#!/usr/bin/env python
# This file 
#     defines schema
#     loads the database from the file system

import sys, os, re, string, glob

from NFL.directory import DATA_DIR
from S2.directory import CLIENT_DIR
import PyQL.columns
import PyQL.inputs
import PyQL.outputs
import PyQL.py_tools
import PyQL.column_types
from PyQL.dt import DT
import cPickle
import NFL.prepare
import S2.query

CURRENT_SEASON = 2013
DB_STRINGS = ['away','home','grass','artificial']  #no need to include team names as Titled Words are strings 

class NFL_DT(DT):

    def __init__(self,data_dirs=[],name="games"):
        DT.__init__(self, name=name,update_cache_on_change_offset=0)  # set to date offset below
        if type(data_dirs) is str: data_dirs = [data_dirs]        
        self.nice_date = PyQL.py_tools.nice_date        
        self.same_season_P = 0        # what the prefixes P and N mean
        self.same_season_p = 1        # what the prefixes p and n mean 
        self.join_letters = "pPnNto0123456789"         # allowed game references
        self.letter_number_pat = re.compile("([a-z])([0-9]+)?",re.I)         # expand s3P2:runs
        self.join_pat = re.compile("[%s]+$"%self.join_letters)         # do all the compiling on init
        self.parameter_prefix = "(?:(?:[%s]+):)?"%self.join_letters  # team:player:join: 
        self.reference_pat = re.compile(self.parameter_prefix.replace("(?:(","((") + "(.*)")   # used to parse the lex-found references to parameters
        self.joins = []
        self.owners = []
        self.read_owners = []
        for data_dir,owner in data_dirs:
            print "inputing from:", data_dir
            if owner and owner not in self.owners: self.owners.append(owner)
            PyQL.inputs.append_from_pickled_columns(self,data_dir,owner=owner,verbose=0)
        self.owner_prefix = "(?:(?:%s)\.)?"%'|'.join(self.owners)
        self.read_owners = self.owners[:]
        print "ownerprefix:",self.owner_prefix

    def prepare(self, joined_headers=[]):
        self.header_aliases = {}
        
        if  self.offset_from_header("site") is None:
            self.add_object(PyQL.columns.Column(name='site',format='%s',data=['home','away']*(len(self[0])/2)))            
        if  self.offset_from_header("season") is None:
            self.add_object(PyQL.columns.Column(name='season',format='%d',
			   data=map(lambda x,s=NFL.prepare.season_from_date:s(x),
				    self.value_from_header('date').value())))

        NFL.prepare.add_join_fields(self)
        NFL.prepare.add_std_fields(self)
        lex_headers = map(lambda x:x.split('.')[-1],joined_headers + self.headers)        # make owner prefix optional 
        lex_headers = dict.fromkeys(lex_headers).keys()  # remove duplicates 

        self.build_lexer(parameters=map(lambda x,pp=self.parameter_prefix: pp + x, lex_headers))
        NFL.prepare.combine_fields(self)
        self.season_offset = self.offset_from_header("season")
        self.site_offset = self.offset_from_header("site")
        self.date_offset = self.offset_from_header("date")
        #print "site offset",self.site_offset
        self.reference_dictionary = {
            'p':self.offset_from_header("_previous game"),
            'P':self.offset_from_header("_previous match up"),
            'n':self.offset_from_header("_next game"),
            'N':self.offset_from_header("_next match up")}
        #return
        NFL.prepare.add_nice_fields(self)
        #NFL.prepare.add_game_dates(self)
        #NFL.prepare.add_formats(self)
        #NFL.prepare.add_ytd_fields(self)
        self.db_strings = DB_STRINGS
        self.update_cache_on_change_offset = self.date_offset        
        #print "selr.headers:",self.headers
        # build lexer down here after adding nice fields
        # include new nice headers and remove duplicates
        lex_headers = map(lambda x:x.split('.')[-1],joined_headers + self.headers + self.header_aliases.keys())
        lex_headers = dict.fromkeys(lex_headers).keys()  # remove duplicates
        parameters=map(lambda x,pp=self.parameter_prefix,op=self.owner_prefix: pp + op + x, lex_headers)
        self.build_lexer(parameters=parameters)
        self.ownerless_headers = dict.fromkeys(map(lambda x:x.split(".")[-1],self.headers)).keys()

    def value_from_header(self,header,default=None,owners=[]):
        offset = self.offset_from_header(header,owners)
        if offset is None: return default
        return self.data[offset] #.value()
    
    def offset_from_header(self, header,owners=[]):
        #print "ofh request",header
        #print "ofh owners",owners
        # first owner defaults to '' (naked parameter) then self.owners ordered as passed in to  __init__        
        if not owners:
            #print "nfl_dt:",self.read_owners,self.owners,type(self.read_owners),type(self.owners)
            owners = [''] + (self.read_owners or self.owners) # read_owners retricts only if it exists
            #print "set owners to",owners
        for owner in owners: 
            if owner: oheader = "%s.%s"%(owner,header)
            else: oheader = header
            #print "looking for",oheader
            if self.header_dict.get(oheader) is not None:
                #print "found at offset",self.header_dict[oheader]
                return self.header_dict[oheader]
        #print "no header matched",header
        return None

        
    def sdb_query(self,sdql,default_fields='_i',indices=None):
        self.joins = []
        self.top_metacode_lines = []
        return self.query(sdql, default_fields=default_fields, indices=indices)

    def code_access_from_parameter(self,reference):
        debug = 0
        if debug: print "referece:",reference
        table = "games"
        terms = []
        groups = self.reference_pat.match(reference).groups()
        if groups[-1] in self.header_aliases.keys():
            expanded_reference = ''.join(filter(lambda x:x is not None,groups[:-1])) + self.header_aliases[groups[-1]]
            if debug: print "expanded_ref:",expanded_reference
            return self.code_access_from_parameter(expanded_reference) 
        if debug: print "groups:",groups
        for term in groups:
            if term: term = term.replace(":",'').strip()
            if term: terms.append(term)
        if debug: print "terms:",terms
        parameter = terms[-1]
        n_terms = len(terms)
        
        join = 't'; player = None; team = None
        if n_terms == 1:
            pass # just the parameter
        elif n_terms == 2: # could be join, team, or player
            join = terms[0]
        if debug: print "join:parameter",join,":",parameter
        
        join = ''.join(map(lambda x:x[0]*int(x[1] or 1),self.letter_number_pat.findall(join))    ) # expand out p3 => ppp
        join = 't' +  filter(lambda x:x!='t',join) # lose any internal `t`s and prepend one for conformity.
        join = string.replace(join,'oo','')          # oo = t
        if join not in self.joins: self.joins.append(join)
        
        # a games table parameter
        offset = self.offset_from_header(parameter)
        if offset is None:
            raise S2.query.UnknownParameterError(parameter)
        #return "_d[%d][%s]"%(offset,join)
        return "_d[%d][_%s]"%(offset,join)  

    def build_top_metacode_lines(self):
        aliases = ["_t=_i"]
        defined = ["t"]
        #print "self.joins:",self.joins
        for join in self.joins:
            current_join = last_join = 't'
            for j in range(1,len(join)):
                current_join += join[j]
                if current_join in defined:
                    last_join = current_join
                    continue
                if join[j] == 'o':
                    aliases.append("if _%s is not None: _%s = _%s+1-2*(_%s%%2)"%(last_join,current_join,
                                                                       last_join,last_join))
                else:
                    aliases.append("if _%s is not None: _%s = self.data[%d][_%s]"%(last_join,current_join,
                                           self.reference_dictionary[join[j]],last_join))
                defined.append(current_join)    
                aliases.append("else: _%s = None"%current_join)         
                last_join = current_join

                same_season = 0

                if self.same_season_P and join[j] in ['P','N']: same_season = 1
                if self.same_season_p and join[j] in ['p','n']: same_season = 1
                if same_season:
                    aliases.append("if _%s is not None and self.data[%d][_t]!=self.data[%d][_%s]:_%s=None"%(current_join,
                                                                                                        self.season_offset,self.season_offset,
                                                                                                        current_join,current_join))
        #print "NFL.join_aliases.aliases:",aliases
        self.top_metacode_lines = aliases


def loader(cid=''):
    data_dirs=[(os.path.join(DATA_DIR,"Schedule/_Column%s"%cid),"Schedule"),
               (os.path.join(DATA_DIR,"NFL/Gamebook/_Column%s"%cid),"NFL"),
               (os.path.join(CLIENT_DIR,"SDB","NFL","Data","_Column"),"SDB"),           
              ]
    owners = ['Schedule','NFL','SDB']    # don't let a client called `Schedule` overwrite! 
    for d in glob.glob(os.path.join(CLIENT_DIR,"*","NFL","Data","_Column")):
        print "inspecting",d
        parts = d.split(os.path.sep)
        print "p:",parts
        client = parts[parts.index("_Column")-3]
        if client in owners: continue
        print "for client",client
        if glob.glob(os.path.join(d,"*.pkl")):
            data_dirs.append((d,client))
              
    print "dd:",data_dirs
    nfl = NFL_DT(data_dirs=data_dirs)
    nfl.prepare() 
    return nfl


########## tests ###########

def test_suite():
    sdql = "date@Cubs:hits=23"
    print "sdql",sdql
    res = mlb.query(sdql)[0][0].data
    print res[0]
    assert res[0] == 20050404
    
    
def test_query(nfl):
    nfl.show_metacode  = 1
    sdql = "(date,self.nice_date(date),points,o:points,overtime)@ team=Bears and season=2010 as 'x'"
    res = nfl.sdb_query(sdql)
    print res
    #print PyQL.outputs.html(res)

def dump_for_S1(nfl,f='/tmp/nfl.py'):
    import time
    text = ["# dumped by dt.py on %s"%time.ctime()]
    text.append("import sys")
    text.append("sys.path += ['/home/jameyer/PyQL/Source']")
    text.append("from dt import DT")
    text.append("from columns import Column")        
    text.append("")
    text.append("dt = DT()")
    for i in range(len(nfl.data)):
        #XXX need to add: if format is a lambda than warn and don't save
        header =  nfl.headers[i].split('.')[-1]
        if header[0] == '_': header = header[1:] 
        text.append("dt.add_object(Column(name=r'''%s''',format=r'''%s'''))"%(
                          header,nfl.data[i].str_format))
    for j in range(len(nfl.data[0])):
        text.append("dt.append((")
        #print "j:",j
        for i in range(len(nfl.data)):
            #print "i:",i                
            text.append(`nfl.data[i][j]` + ',')
        text.append("))")                

    text.append("")
    open(f,'w').write(string.join(text,"\n"))


def dump_for_ar(nfl):
    sdql = "season, date, week,  surface,  _temperature as temperature, _wind as 'wind speed',line, total,team, o:team, rushing yards, o:rushing yards, passing yards, o:passing yards, rushes, o:rushes, passes, o:passes, conference, o:conference, division, o:division, turnovers, o:turnovers, quarter scores[0] + quarter scores[1] as 'first half points', o:quarter scores[0] + o:quarter scores[1] as 'o:first half points',points,o:points"
    res = nfl.query(sdql + "@site='home' and season=2002")[0]
    lout = ['\t'.join(res.headers)]
    for i in range(len(res[0])):
        l = []
        for j in range(len(res.headers)):
            l.append(str(res[j][i]))
        lout.append('\t'.join(l))
    print '\n'.join(lout)
    open("/tmp/nfl_ar.csv",'w').write('\n'.join(lout))
    
if __name__ == "__main__":
    nfl = loader()
    #test_query(nfl)
    dump_for_S1(nfl)
    #dump_for_ar(nfl)

#!/usr/bin/env python
# This file 
#     defines schema
#     loads the database from the file system
#     uses prepare to get reference fields, nice fields

import sys, os, re, string, cPickle

import PyQL.columns
import PyQL.inputs
import PyQL.outputs 
import PyQL.column_types
import PyQL.py_tools
from PyQL.dt import DT

from S2.directory import DATA_DIR
import S2.inputs
import S2.prepare
import S2.common_short_cuts


def normalize_team_name(name):
    return name.lower().replace(' ','')

class UnknownParameterError(Exception):
    def __init__(self,parameter):
        self.parameter = parameter
    def __str__(self):
        return "Error: the requested parameter `%s` does not exist"%self.parameter

class DB(DT):
    def __init__(self,data_dirs=[],
                 name="sport", #eg name=mlb has special shortcuts.
                 ):
        DT.__init__(self, name=name,update_cache_on_change_offset=0)  # will need to set this to date offset
        self.nice_date = PyQL.py_tools.nice_date
        self.day_from_date = PyQL.py_tools.day_from_date
        if type(data_dirs) is str: data_dirs = [data_dirs]
        self.same_season_P = 0        # what the prefixes P and N mean
        self.same_season_p = 1        # what the prefixes p and n mean 
        self.join_letters = "sSpPnNto0123456789"         # allowed game references
        self.letter_number_pat = re.compile("([a-z])([0-9]+)?",re.I)         # expand s3P2:runs
        self.join_pat = re.compile("[%s]+$"%self.join_letters)         # do all the compiling on init
        #self.parameter_prefix = "(?:(?:[A-Z][a-zA-Z]*[\s]*)+:)?(?:(?:[A-Z][a-zA-Z]*[\s]*)+:)?(?:(?:[%s]+):)?"%self.join_letters  # team:player:join:
        self.parameter_prefix = "(?:(?:[A-Z][a-zA-Z]*[\s]*)+:)?(?:(?:(?:[A-Z][a-zA-Z]*[\s]*)|max|min|list|sum|team)+:)?(?:(?:[%s]+):)?"%self.join_letters  # team:player:join: 
        self.reference_pat = re.compile(self.parameter_prefix.replace("(?:(","((") + "(.*)")   # used to parse the lex-found references to parameters
        self.normalize_team_name = normalize_team_name
        self.joins = []
        self.header_aliases = {} # need to take care of these in code_access_from_parameters
        for data_dir in data_dirs:
            print "inputing from:", data_dir
            #PyQL.inputs.append_from_pickled_columns(self,data_dir,0)
            S2.inputs.append_from_flat_file(self,data_dir,verbose=0) # need to write this to import flat files or pickles
            #print "self.headers:",self.headers
            
    def prepare(self, joined_headers=[], db_strings = []):
        #print "prepare: header:",self.headers
        if  self.offset_from_header("site") is None:
            self.add_object(PyQL.columns.Column(name='site',format='%s',data=['home','away']*(len(self[0])/2)))            
        if  self.offset_from_header("season") is None:
            if  self.offset_from_header("date") is not None and hasattr(S2.prepare,"season_from_date"):
                self.add_object(PyQL.columns.Column(name='season',format='%d',
			   data=map(lambda d,sfd=S2.prepare.season_from_date:sfd(d),
				    self.value_from_header('date').value())
					  ))        
        lex_headers = dict.fromkeys(joined_headers + self.headers).keys()  # remove duplicates
        S2.prepare.add_join_fields(self)
        S2.prepare.add_std_fields(self)
        self.build_lexer(parameters=map(lambda x,pp=self.parameter_prefix: pp + x, lex_headers))
        self.season_offset = self.offset_from_header("season")

        self.reference_dictionary = {
            'p':self.offset_from_header("_previous game"),
            'P':self.offset_from_header("_previous match up"),
            's':self.offset_from_header("_starters previous game"),
            'S':self.offset_from_header("_starters previous match up"),
            'n':self.offset_from_header("_next game"),
            'N':self.offset_from_header("_next match up")}

        if hasattr(S2.prepare,"add_nice_fields"):
                         S2.prepare.add_nice_fields(self)
            
        self.db_strings = db_strings # not used much. Possible of value for ALA to mean Alabmaa and not away loss away.
        # include new nice headers and remove duplicates                
        lex_headers = dict.fromkeys(joined_headers + self.headers + self.header_aliases.keys()).keys()  
        self.build_lexer(parameters=map(lambda x,pp=self.parameter_prefix: pp + x, lex_headers))

    def sdb_query(self,sdql,default_fields='_i',indices=None):
        self.joins = []
        self.top_metacode_lines = []
        #sdql = clients.expand(sdql,client=None) # cliet specific short cuts (may use common short cuts so do first)
        sdql = S2.common_short_cuts.expand(sdql,sport=self.name)
        default_fields = S2.common_short_cuts.expand(default_fields,sport=self.name)
        #print "expanded:",sdql
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
            if self.join_pat.match(terms[0]) and terms[0][0].isalpha():  # joins start with a letter,player ref with a number
                join = terms[0]
            elif self.normalize_team_name(terms[0]) in self.normalized_team_names: team = terms[0]
            else: player = terms[0]

        elif n_terms == 3: # could be  team:player, team:join, or player:join
            if self.join_pat.match(terms[1]):     # a join: could be team:join and player:join
                join = terms[1]
                if   self.normalize_team_name(terms[0]) in self.normalized_team_names: team = terms[0]
                else: player = terms[0]
            else:  # team:player
                team, player = terms[0],terms[1]
                
        else: #  must be  team:player:join
            team,player,join = terms[0],terms[1],terms[2]
        if debug: print "tpj:",team,player,join
        
        join = ''.join(map(lambda x:x[0]*int(x[1] or 1),self.letter_number_pat.findall(join))    ) # expand out p3 => ppp
        join = 't' +  filter(lambda x:x!='t',join) # lose any internal `t`s and prepend one for conformity.
        join = string.replace(join,'oo','')          # oo = t
        if join not in self.joins: self.joins.append(join)
        
        # if a team is specified than set access to fail except for the requested team.
        if team: team_condition = "(self.normalize_team_name(%s)=='%s' or None)*"%(self.code_access_from_parameter("%s:team"%join),
                                                                                              self.normalize_team_name(team))
        else: team_condition = ""

        # a games table parameter
        offset = self.offset_from_header(parameter)
        if offset is None:
            raise UnknownParameterError(parameter)

        return "%s_g[%d][_%s]"%(team_condition,offset,join)     # 20110729 allow Cubs:hits=3

    def build_top_metacode_lines(self):
        aliases = ["_t=_i","_g=_d"]
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
                if same_season and self.season_offset is not None:
                    aliases.append("if _%s is not None and self.data[%d][_t]!=self.data[%d][_%s]:_%s=None"%(current_join,
                                        self.season_offset,self.season_offset, current_join,current_join))
        self.top_metacode_lines = aliases

def loader(cid=''):
    dbmap = {}
    print "looking in:",os.path.join(DATA_DIR,"Active")
    for filename in os.listdir(os.path.join(DATA_DIR, 'Active')):
        fullpath = os.path.join(DATA_DIR, "Active", filename)
        if filename.endswith('.tab') and os.path.isfile(fullpath):
            sport = filename[:-4]
            sdb = DB([fullpath])
            if "team" in sdb.headers:
                sdb.prepare()
            dbmap[sport] = sdb
    print "Loaded files: %s" % dbmap.keys()                           
    return dbmap

def test_query(sdb):
    sdql = "date@points>20"
    print "sdql",sdql
    res = sdb.query(sdql)[0][0].data
    print res[0]

def test_formats(sdb):
    import S2.formats
    print "test game fields"
    QO = S2.formats.Query_Summary(headers=sdb.headers)
    sdql = QO.select() + "@site=home"
    print "sdql:",sdql
    res = sdb.sdb_query(sdql)[0]
    print QO.output(res)
    
    
if __name__ == "__main__":
    sdb = loader()
    #test_query(sdb)
    #sdb.show_metacode = 1
    #sdb.print_exceptions =1
    #test_query(sdb)
    #test_formats(sdb)


import sys, os, re, string, glob
import PyQL.columns
from S2.directory import CLIENT_DIR, TOP_DIR
from S2.query import AmbiguousPlayerError, UnknownParameterError
import PyQL.inputs
import PyQL.py_tools
from PyQL.dt import DT
import S2.query

def log(txt):
    open('/tmp/sdb.out','a').write(txt+'\n\n')

sport_offseason = {'nfl':801,'nba':901,'mlb':201,'nhl':801,'ncaafb':701,'ncaabb':801,'cfl':201,'wnba':101}
def load_joins(sport,sdt,globber,expand_season_start_date=1,verbose=1,owner=None):
    print "looking for join with",globber
    joins = glob.glob(globber)
    for join in joins:
        jdt = PyQL.inputs.dt_from_file(join,delim_column=',')
        parts = join.split(os.path.sep)
        if verbose: print "p:",parts
        client = owner or parts[parts.index("_Raw")-3]

        if jdt.headers[0] == 'start date': # use a look back approach to set values in sdt
            if expand_season_start_date:
                for i in range(len(jdt[0])):
                    if jdt[0][i] < 2100: #  a season
                        jdt[0][i] = jdt[0][i]*10000 + sport_offseason[sport]
        #sdt.jdt = jdt
        value = jdt.headers[-1].split('.')[0] # rank.2016
        #nice = sdt.query("self.jdt.query('%s@team=%%s and start date<%%s'%%(team,date)@1)[0][0][-1] as %s.%s@1"%(value,client,value))[0]

        #for col in nice:
        #    offset = sdt.offset_from_header(col.name)
        #    if offset is None:
        #        if verbose: print "adding nice column",col.name
        #        sdt.add_object(col)
        #    else:
        #        if verbose: print col.name," is already a column: overwrite"
        #        sdt.data[offset] = col
        jdt.sort_by_column(0)

        jteam = {} # jtd[team] = [(start,value),...]
        for j in range(len(jdt[0])):
            jteam.setdefault(jdt[1][j],[]).append((jdt[0][j],jdt[-1][j]))
        #print 'jteam',jteam
        new = [] # the new data column
        ti = sdt.offset_from_header('team')
        di = sdt.offset_from_header('date')
        for r in range(len(sdt[0])):
            team = sdt[ti][r]
            date = sdt[di][r]
            jval = filter(lambda x,d=date:x[0]<=d,jteam.get(team,[]))
            if jval:  jval=jval[-1][-1]
            else: jval = None
            new.append(jval)
        col_name = '%s.%s'%(client,value)
        new = PyQL.columns.Column(name=col_name,data=new)
        offset = sdt.offset_from_header(col_name)
        if offset is None:
            if verbose: print "adding nice column",col_name
            sdt.add_object(new)
        else:
            if verbose: print col_name," is already a column: overwrite"
            sdt.data[offset] = new

    return sdt


def load_icons(sport,ext='.png'):
    try:
        from matplotlib._png import read_png
    except:
        print "Cannot load matplotlib"
        return {}
    d = {}
    for f in glob.glob(os.path.join(TOP_DIR,"public_html","Images",sport.upper(),ext)):
        im = read_png(f)
        team = os.path.basename(f)[:-4]
        #print "loading icon for",team
        d[team] = im
        #print "loading icon for",team,im.size
    return d

class Game_DT(DT):

    def __init__(self,data_dirs=[],name="games",update_cache_on_change_offset=0,team_names=[],join_letters = "pPnNto0123456789", verbose=False):
        self.ateam = 'Team'
        #print "sdb_dt.Game_DT.__init__.data_dirs:",data_dirs
        DT.__init__(self, name=name,update_cache_on_change_offset=0)  # set to date offset below
        self.team_names = team_names
        if type(data_dirs) is str: data_dirs = [data_dirs]
        self.nice_date = PyQL.py_tools.nice_date
        self.same_season_P = 0        # what the prefixes P and N mean
        self.same_season_p = 1        # what the prefixes p and n mean
        self.join_letters = join_letters        # allowed game references
        self.letter_number_pat = re.compile("([a-z])([0-9]+)?",re.I)         # expand s3P2:runs
        self.join_pat = re.compile("[%s]+$"%self.join_letters)         # do all the compiling on init
        self.parameter_prefix = "(?:(?:[A-Z][a-zA-Z]*[\s]*)+:)?(?:(?:(?:[A-Z][a-zA-Z]*[\s]*)|max|min|list|sum|%s)+:)?(?:(?:[%s]+):)?"%(self.ateam,self.join_letters)  # team:player:join:
        self.reference_pat = re.compile(self.parameter_prefix.replace("(?:(","((") + "(.*)")   # used to parse the lex-found references to parameters
        #self.parameter_prefix = "(?:(?:[%s]+):)?"%self.join_letters  # team:player:join:
        self.joins = []
        self.owners = []
        self.read_owners = []
        for data_dir,owner in data_dirs:
            if verbose: print "inputing from:", data_dir
            if owner and owner not in self.owners: self.owners.append(owner)
            PyQL.inputs.append_from_pickled_columns(self,data_dir,owner=owner,dict_to_dt=1,verbose=1)
        self.owner_prefix = "(?:(?:%s)\.)?"%'|'.join(self.owners)
        self.read_owners = self.owners[:]
        if verbose: print "sdb_dt.Games_DT.__init__.ownerprefix:",self.owner_prefix


    def find_player(self,name,team,table):
        #print "sdb.find_player",name,team,table
        if hasattr(self,'games'):ndt = self.games.player_dts[table].name_dt
        else: ndt = self.player_dts[table].name_dt
        return S2.query.find_player(ndt,name,team)

    def value_from_header(self,header,default=None,owners=[]):
        offset = self.offset_from_header(header,owners)
        if offset is None: return default
        return self.data[offset] #.value()

    def offset_from_header(self, header,owners=[]):
        if not owners:
            owners = [''] + (self.read_owners or self.owners) # read_owners retricts only if it exists
        for owner in owners:
            if owner: oheader = "%s.%s"%(owner,header)
            else: oheader = header
            if self.header_dict.get(oheader) is not None:
                return self.header_dict[oheader]
        return None

    def offsets_from_header(self, header,owners=[]):
        # first owner defaults to '' (naked parameter) then self.owners ordered as passed in to  __init__
        ret = [] # list of offsets to be checked for first non-Null.
        if not owners:
            owners = [''] + (self.read_owners or self.owners) # read_owners retricts only if it exists
        for owner in owners:
            if owner: oheader = "%s.%s"%(owner,header)
            else: oheader = header
            if self.header_dict.get(oheader) is not None:
                ret.append(self.header_dict[oheader])
        return ret or None

    def mc_reference(self,table,offsets,row):
        # row is something like `_tp` for games table and something like `_d[pdt_off][_tp]` for player
        #print "mc offsts:",offsets
        r_offsets = []
        for offset in offsets:
            if offset not in r_offsets:
                r_offsets.append(offset)
        if len(r_offsets) == 1:
            return "%s[%d][%s]"%(table,r_offsets[0],row)
        ret = '('
        for offset in r_offsets[:-1]:
            ret += "%s[%d][%s] if %s[%d][%s] is not None else "%(table,offset,row,table,offset,row)
        ret += "%s[%d][%s]"%(table,r_offsets[-1],row)
        return ret + ')'


    def sdb_query(self,sdql,default_fields='_i',indices=None):
        self.joins = []
        self.top_metacode_lines = []
        return self.query(sdql, default_fields=default_fields, indices=indices)

    def code_access_from_parameter(self,reference):
        debug = 0
        #if debug: print "referece:",reference
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
            elif terms[0] in self.team_names + [self.ateam]: team = terms[0]
            else: player = terms[0]

        elif n_terms == 3: # could be  team:player, team:join, or player:join
            if self.join_pat.match(terms[1]):     # a join: could be team:join and player:join
                join = terms[1]
                if terms[0] in self.team_names + [self.ateam]: team = terms[0]
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
        if team == self.ateam: team = None
        # if a team is specified than set access to fail except for the requested team.
        if team:
            team_condition = "(%s=='%s' or None)*"%(self.code_access_from_parameter("%s:team"%join), team)
        else: team_condition = ""
        #print "TC:",team_condition
        # if a game-referenced parameter is not in the games table and is in a player table then return the sum over all players.
        if not player and self.offset_from_header(parameter) is None:
            if "longest" in parameter: player = "max"
            elif "average" in parameter: raise UnknownParameterError(parameter)
            else: player = "sum"

        # sub tables may not share parameter names: they can share with the games table
        if player:
            table = None
            for ptn in self.player_table_names:
                parameter_offset = self.player_dts[ptn].offset_from_header(parameter)
                if parameter_offset is not None:
                    # 20170706 will have to make a dict for player_table_offsets or otherwise look up by owner.
                    players_offset = self.player_table_offsets[ptn]
                    table = ptn
                    break
            if not table:
                raise UnknownParameterError(parameter)

            if player in ['sum','max','min','list']:
                # this method with arg :  splice of all player rows for this game.
                return  "(%s%s( filter( lambda x:x is not None,_%s[%d].data[min(_d[%d][_%s].values()):1+max(_d[%d][_%s].values())] )))"%(
                                                              team_condition,player,table,parameter_offset, players_offset, join, players_offset, join)

            names = self.find_player(name=player,team=team,table=table) # if player is unnique in the parameter's table then be done!
            if len(names) == 0:                                 # if there are no matches then search all siblings
                names_s = set()
                for ptn in self.player_table_names:
                    if ptn == table: continue # already have this one.
                    names_s = names_s.union(self.find_player(name=player,team=team,table=ptn))
                    #log("found total of %s in %s"%(names_s,ptn))
                names = list(names_s)
                names.sort()
            if len(names) != 1: raise AmbiguousPlayerError(player,names)
            else: name = names[0]
            return "(%s(_%s[%d][_d[%d][_%s]['%s']] if _d[%d][_%s].has_key('%s') else 0))"%(team_condition,table,
                                                                                       parameter_offset,
                                                                                       players_offset,join,name,
                                                                                       players_offset,join,name)
        # a games table parameter
        offsets = self.offsets_from_header(parameter)
        if offsets is None:
            raise UnknownParameterError(parameter)
        mc_ref = self.mc_reference(table='_d',offsets=offsets,row='_%s'%join)
        #return "(%s_d[%d][_%s])"%(team_condition,offset,join)
        #print "mc_ref:",mc_ref
        return "(%s%s)"%(team_condition,mc_ref)

    def build_top_metacode_lines(self):
        self.alias_metacode_lines = []
        #aliases = ["_t=_i"]
        aliases = ["_g=_d","_t=_i"]
        for ptn in self.player_table_names:
            self.alias_metacode_lines.append("_%s = self.player_dts['%s']"%(ptn,ptn))
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
                    aliases.append("if _%s is not None: _%s = _d[%d][_%s]"%(last_join,current_join,
                                           self.reference_dictionary[join[j]],last_join))
                defined.append(current_join)
                aliases.append("else: _%s = None"%current_join)
                last_join = current_join

                same_season = 0
                if self.same_season_P and join[j] in 'PNS': same_season = 1
                if self.same_season_p and join[j] in 'pns': same_season = 1
                if same_season:
                    aliases.append("if _%s is not None and _d[%d][_t]!=_d[%d][_%s]:_%s=None"%(current_join,
                                                                            self.season_offset,self.season_offset,
                                                                            current_join,current_join))
        self.top_metacode_lines = aliases

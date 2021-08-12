# code access from parameter and query are half cooked.
import sys, os, re, string

import NHL.nhl_dt
import S2.short_cuts
from S2.query import AmbiguousPlayerError
import S2.query
NHL_DT = NHL.nhl_dt.NHL_DT

UnknownParameterError = NHL.nhl_dt.UnknownParameterError

class Players(NHL_DT):
    ateam = "team" # anonymous team
    def __init__(self,data_dirs=[]):
        NHL_DT.__init__(self, data_dirs=data_dirs,name="players")
        self.name_offset = self.offset_from_header('name')

    # this is questionable...    
    def normalize_player_name(self,name):
        name = name.replace('.','')
        name = name.title()
        if name[:3] in ["Aj ","Cj ","Dj ","Jj ","Jr ","Oj ","Pj ","Tj "]:
            name = name[:2].upper() + name[2:]
        if name[:4] in ["Tmp"]: name = name[4:]            
        if name == "Shareef Abdur": name = "Shareef Abdur Rahim"
        return name

    def build_name_dt(self):
        print "building player name dt"
        res = self.player_query("Unique((team,name)) as utn@1")[0]
        res.build_lexer()
        self.name_dt = res.query("utn[0] as team,utn[1] as name@1")[0]
        self.name_dt.build_lexer()
        print "found %d unique team,names"%len(self.name_dt[0])
        #print "test query on team@name=Kobe Bryant.  Headers:",self.name_dt.headers
        #print self.name_dt.query("team@name='Kobe Bryant'")

    def find_player(self,name, team=None):
        if team: team = NHL.nhl_dt.normalize_team_name(team)
        return S2.query.find_player(ndt=self.name_dt,name=name,team=team)
        
    def prepare(self, joined_headers=[]):
        self.data[self.name_offset].data = map(self.normalize_player_name,self.data[self.name_offset].data)

        #print "prepare: header:",self.headers
        self.header_aliases = {} # need to take care of these in code_access_from_parameters
        lex_headers = dict.fromkeys(joined_headers + self.headers).keys()  # remove duplicates
        self._games_offset = self.offset_from_header("_game")
        self.name_offset = self.offset_from_header("name")
        self.db_strings = NHL.nhl_dt.DB_STRINGS

        lex_headers = map(lambda x:x.split('.')[-1],joined_headers + self.headers )
        lex_headers = dict.fromkeys(lex_headers).keys()
        print "building player lexer with heaeders:",lex_headers
        self.build_lexer(parameters=map(lambda x,pp=self.parameter_prefix,op=self.owner_prefix: pp + op + x, lex_headers))

        self.build_name_dt()

    def player_query(self,sdql,default_fields='_i',indices=None):
        self.joins = []
        self.top_metacode_lines = []
        sdql = S2.short_cuts.expand(sdql)
        default_fields = S2.short_cuts.expand(default_fields)
        #print "expanded:",sdql
        return self.query(sdql, default_fields=default_fields, indices=indices)

    def code_access_from_parameter(self,reference):
        debug = 1
        if debug: print "referece:",reference
        terms = []
        groups = self.reference_pat.match(reference).groups()
        if groups[-1] in self.header_aliases.keys():
            expanded_reference = ''.join(filter(lambda x:x is not None,groups[:-1])) + self.header_aliases[groups[-1]]
            if debug: print "players.expanded_ref:",expanded_reference
            return self.code_access_from_parameter(expanded_reference) 
        if debug: print "players.groups:",groups
        for term in groups:
            if term: term = term.replace(":",'').strip()
            if term: terms.append(term)
        if debug: print "players.terms:",terms
        parameter = terms[-1]
        n_terms = len(terms)
        
        join = 't'; player = None; team = None
        if n_terms == 1:
            pass # just the parameter
        elif n_terms == 2: # could be join, team, or player
            if self.join_pat.match(terms[0]) and terms[0][0].isalpha():  # joins start with a letter,player ref with a number
                join = terms[0]
            elif self.games.normalize_team_name(terms[0]) in self.games.normalized_team_names + [self.ateam]: team = terms[0]
            else: player = terms[0]

        elif n_terms == 3: # could be  team:player, team:join, or player:join
            if self.join_pat.match(terms[1]):     # a join: could be team:join and player:join
                join = terms[1]
                if   self.normalize_team_name(terms[0]) in self.games.normalized_team_names+[self.ateam]: team = terms[0]
                else: player = terms[0]
            else:  # team:player
                team, player = terms[0],terms[1]
                
        else: #  must be  team:player:join
            team,player,join = terms[0],terms[1],terms[2]
        if debug: print "players.tpj:",team,player,join
        
        
        join = ''.join(map(lambda x:x[0]*int(x[1] or 1),self.letter_number_pat.findall(join))    ) # expand out p3 => ppp
        join = 't' +  filter(lambda x:x!='t',join) # lose any internal `t`s and prepend one for conformity.
        join = string.replace(join,'oo','')          # oo = t
        if join not in self.joins: self.joins.append(join)
        
        # if a team is specified than set access to fail except for the requested team.
        if team and team != self.ateam:
            team_condition = "(self.games.normalize_team_name(%s)=='%s' or None)*"%(
                                                                     self.games.code_access_from_parameter("%s:team"%join),
                                                                     self.games.normalize_team_name(team))
        else: team_condition = ""
        #print "team_conditink",team_condition
        player_condition = ''
        if player and player not in  ['sum','max','min','list']:
            if team and team == self.ateam: player_team = None
            else: player_team = team
            player_names = self.find_player(name=player,team=player_team)
            if len(player_names) != 1: raise AmbiguousPlayerError(player,player_names)
            else:
                if join == 't':
                    player_condition = "(_p[%d][_i] == '%s' or None)*"%(self.name_offset,player_names[0])
        
        parameter_offset = self.offset_from_header(parameter)
        if parameter_offset is not None:
            print "parameter", parameter,"is  a players field"
            table = "players"

            if player in ['sum','max','min','list']:
                return  "%s%s( filter( lambda x:x is not None,_%s[%d].data[min(_g[%d][_%s].values()):1+max(_g[%d][_%s].values())] ))"%(
                               team_condition,player, table[0], parameter_offset, self._games_offset, join, self._games_offset, join)

            #print "player_con:",player_condition
            if join == 't': return "%s%s_p[%d][_i]"%(team_condition,player_condition,parameter_offset,)
            return "%s%s_p[%d][_g[%d][_%s][str(_p[%d][_i])]]"%(team_condition,player_condition,parameter_offset,
                                                              self.games._players_offset,join,self.player_id_offset,)
        
        # assume a game reference
        offset = self.games.offset_from_header(parameter)
        if offset is None: raise UnknownParameterError(parameter)
        return "%s_g[%d][_%s]"%(team_condition, offset, join)
 

    def build_top_metacode_lines(self):
        # players is the main datatable (_d) and games is the joined in datatable
        aliases = ["_p=_d","_g=self.games","_t=_p[%s][_i]"%self._games_offset]
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
                    aliases.append("if %s is not None: %s = %s+1-2*(%s%%2)"%(last_join,current_join,
                                                                       last_join,last_join))
                else:
                    aliases.append("if %s is not None: %s = self.games.data[%d][%s]"%(last_join,current_join,
                                           self.games.reference_dictionary[join[j]],last_join))
                defined.append(current_join)    
                aliases.append("else: %s = None"%current_join)         
                last_join = current_join

                same_season = 0

                if self.same_season_P and join[j] in ['P','N']: same_season = 1
                if self.same_season_p and join[j] in ['p','n']: same_season = 1
                if same_season:
                    aliases.append("if %s is not None and _g[%d][t]!=_g[%d][%s]:%s=None"%(current_join,
                                                                                                        self.games.season_offset,self.games.season_offset,
                                                                                                        current_join,current_join))
        self.top_metacode_lines = aliases


if __name__ == "__main__":
    players = Players([("/home/jameyer/S2/NHL/Data/Covers/Box/_Column/Player","Covers.Box")])



import sys, os, re, string
import S2.short_cuts
from S2.query import AmbiguousPlayerError, UnknownParameterError
import S2.query
import S2.common_methods
import PyQL.columns
import PyQL.dt
import PyQL.py_tools

SPACE_UPPER_PAT = re.compile("([a-zA-Z])([A-Z])") # check for no space before a cap letter

# what can I get from parent sport_dt?
verbose = False

class Player:
    ateam = "Team" # anonymous team
    #def __init__(self):
    #    pass

    def build_name_dt(self):
        if verbose: print "building player name dt"
        self.show_metacode=1
        data = list(set(self.sdb_query("(team,name)@1")[0].data[0]))
        teams = []
        names = []
        for t,n in data:
            if n.startswith('Yoen'):
                print "adding Yoen for",t
            teams.append(t)
            names.append(n)
        c1 = PyQL.columns.Column(name="team",data=teams)
        c2 = PyQL.columns.Column(name="name",data=names)
        self.name_dt = PyQL.dt.DT(name="name_dt",data=[c1,c2])
        #self.name_dt.build_lexer()
        if verbose: print "found %d unique team,names"%len(self.name_dt[0])


    def prepare(self, joined_headers=[]):
        self.name_offset = self.offset_from_header("name")
        #self.data[self.name_offset].data = map(self.games_prepare.format_name,self.data[self.name_offset].data)
        #print "prepare: header:",self.headers
        self.header_aliases = {} # need to take care of these in code_access_from_parameters
        lex_headers = map(lambda x:x.split('.')[-1],joined_headers + self.headers)        # make owner prepix optional
        self._games_offset = self.offset_from_header("_game")
        if verbose: print "player_dt.prepare.name_offset for:",self.name,self.name_offset
        #print "normalizing player names"
        #self.data[self.name_offset] = map(S2.common_methods.format_name, self.data[self.name_offset]) XXX can't do this here since games_dt has names also.
        #self.db_strings = NFL.nfl_dt.DB_STRING
        parameters = map(lambda x,pp=self.parameter_prefix,op=self.owner_prefix: pp + op + x, lex_headers)
        self.build_lexer(parameters=parameters)
        #self.build_name_dt()

    def sdb_query(self,sdql,default_fields='_i',indices=None):
        #print "player_querty gets :",sdql
        self.joins = []
        self.top_metacode_lines = []
        sdql = S2.short_cuts.expand(sdql)
        default_fields = S2.short_cuts.expand(default_fields)
        #print "expanded:",sdql
        return self.query(sdql, default_fields=default_fields, indices=indices)

    def value_from_header(self,header,default=None,owners=None):
        offset = self.offset_from_header(header,owners)
        if offset is None: return default
        return self.data[offset] #.value()

    def offset_from_header(self, header,owners=None):
        #print "ofh request",header
        # first owner defaults to '' (naked parameter) then self.owners ordered as passed in to  __init__
        if owners is None: owners = [''] + self.owners
        #print "ofh =owbers",owners
        for owner in owners:
            if owner: oheader = "%s.%s"%(owner,header)
            else: oheader = header
            #print "looking for",oheader
            if self.header_dict.get(oheader) is not None:
                #print "found at offset",self.header_dict[oheader]
                return self.header_dict[oheader]
        #print "no header matched",header
        return None

    def code_access_from_parameter(self,reference):
        terms = []
        groups = self.reference_pat.match(reference).groups()
        if groups[-1] in self.header_aliases.keys():
            expanded_reference = ''.join(filter(lambda x:x is not None,groups[:-1])) + self.header_aliases[groups[-1]]
            return self.code_access_from_parameter(expanded_reference)
        for term in groups:
            if term: term = term.replace(":",'').strip()
            if term: terms.append(term)
        parameter = terms[-1]
        n_terms = len(terms)

        join = 't'; player = None; team = None
        if n_terms == 1:
            pass # just the parameter
        elif n_terms == 2: # could be join, team, or player
            if self.join_pat.match(terms[0]) and terms[0][0].isalpha():  # joins start with a letter,player ref with a number
                join = terms[0]
            elif terms[0] in self.games.team_names + [self.ateam]: team = terms[0]
            else: player = terms[0]

        elif n_terms == 3: # could be  team:player, team:join, or player:join
            if self.join_pat.match(terms[1]):     # a join: could be team:join and player:join
                join = terms[1]
                if terms[0] in self.games.team_names+[self.ateam]: team = terms[0]
                else: player = terms[0]
            else:  # team:player
                team, player = terms[0],terms[1]

        else: #  must be  team:player:join
            team,player,join = terms[0],terms[1],terms[2]

        join = ''.join(map(lambda x:x[0]*int(x[1] or 1),self.letter_number_pat.findall(join))    ) # expand out p3 => ppp
        join = 't' +  filter(lambda x:x!='t',join) # lose any internal `t`s and prepend one for conformity.
        join = string.replace(join,'oo','')          # oo = t
        if join not in self.joins: self.joins.append(join)

        # if a team is specified than set access to fail except for the requested team.
        if team and team != self.ateam:
            team_condition = "('%s'=='%s' or None)*"%(self.games.code_access_from_parameter("%s:team"%join),team)

        else: team_condition = ""

        # need to find table - define handy references
        table_offset = {} # [table] = offset
        offset = self.games.offset_from_header(parameter)
        if offset is not None:
            table_offset["games"] = offset
        for table in self.games.player_table_names:
            offset = self.games.player_dts[table].offset_from_header(parameter)
            if offset is not None:
                table_offset[table] = offset

        if not table_offset:
            raise UnknownParameterError(parameter)

        tables = table_offset.keys()
        # allow Team to be used for sum
        if 'games' not in tables and team==self.ateam and not player:
            player = 'sum'
        #if games is the only choice or a team and no player
        if 'games' in tables and ( (len(tables)==1)  or (team == self.ateam and not player)):
            offset = self.games.offset_from_header(parameter) # XX get this from table_offsets??
            return "_g[%d][_%s]"%(offset, join)

        if self.name in tables:
            ptn = self.name
        else:
            ptn = filter(lambda x,f=['games']: x not in f,tables)[0]
        parameter_offset = table_offset[ptn]
        player_condition = ''
        if player and player not in  ['sum','max','min','list']:
            if team and team == self.ateam: player_team = None
            else: player_team = team
            player_names = self.find_player(name=player,team=player_team,table=ptn)
            if len(player_names) != 1: raise AmbiguousPlayerError(player,player_names)
            else:
                if join == 't':
                    #player_condition = "(_d[%d][_i] == '%s' or None)*"%(self.name_offset,player_names[0])
                    player_condition = "0 if _d[%d][_i] != '%s' else "%(self.name_offset,player_names[0])


        if player in ['sum','max','min','list']:
            return  "%s%s( filter( lambda x:x is not None,_%s[%d].data[min(_g[%d][_%s].values()):1+max(_g[%d][_%s].values())] ))"%(
                          team_condition,player, ptn, parameter_offset, self.games.player_table_offsets[ptn], join,
                                                                   self.games.player_table_offsets[ptn], join)
        if join == 't' and self.name == ptn: # this worked fine excpet doesn't give 0 for None
            return "(%s_d[%d][_i])"%(player_condition,parameter_offset,)

        if not player: # check for this player's name in other player table
            # 20131120 want to be able to query on `passing yards + rushing yards` even when the player is not listed in both tables.
            return "(_%s[%d][ _g[%d][_%s][_d[%d][_i]] ] if  _g[%d][_%s].has_key(_d[%d][_i]) else 0)"%(ptn,parameter_offset,
                                                           self.games.player_table_offsets[ptn],join,
                                                                    self.name_offset,
                                                           self.games.player_table_offsets[ptn],join,
                                                                    self.name_offset)
        # specified player name in other table
        # 20131120 want to be able to query on `passing yards + rushing yards` even when the player is not listed in both tables.
        return "(_%s[%d][ _g[%d][_%s]['%s'] ] if _g[%d][_%s].has_key('%s') else 0)"%(ptn,parameter_offset,
                                                           self.games.player_table_offsets[ptn],join,
                                                                   player_names[0], self.games.player_table_offsets[ptn],join,
                                                                   player_names[0]
                                                                                      )



    def build_top_metacode_lines(self):
        self.alias_metacode_lines = ["_g = self.games"]
        aliases = ["_t=_d[%s][_i]"%self._games_offset] # t is the index of the games tables
        for ptn in self.games.player_dts.keys():
            #aliases.append("_%s = self.games.player_dts['%s']"%(ptn,ptn))
            self.alias_metacode_lines.append("_%s = self.games.player_dts['%s']"%(ptn,ptn))
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
                    aliases.append("if _%s is not None: _%s = self.games.data[%d][_%s]"%(last_join,current_join,
                                           self.games.reference_dictionary[join[j]],last_join))
                defined.append(current_join)
                aliases.append("else: _%s = None"%current_join)
                last_join = current_join

                same_season = 0

                if self.same_season_P and join[j] in ['P','N']: same_season = 1
                if self.same_season_p and join[j] in ['p','n']: same_season = 1
                if same_season:
                    aliases.append("if _%s is not None and _g[%d][_t]!=_g[%d][_%s]:_%s=None"%(current_join,
                                                                self.games.season_offset,self.games.season_offset,
                                                                current_join,current_join))
        self.top_metacode_lines = aliases





if __name__ == "__main__":
    pass

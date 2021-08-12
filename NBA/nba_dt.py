#!/usr/bin/env python
# This file
#     defines schema
#     loads the database from the file system
#     uses prepare to get reference fields, nice fields

# for a new season:
#  update CURRENT_SEASON in this file
#  use ~/NBA/Data/Source/download_nba_schedule.py to make ~/NBA/Data/Schedule/_Raw/20??.tab
#  use http://sportsdatabase.com/nba/update_schedule to rebuild
import sys, os, re, string, glob


import NBA.prepare
import NBA.teams
import PyQL.columns
import PyQL.inputs
import PyQL.outputs
import PyQL.column_types
from PyQL.dt import DT
import cPickle
import PyQL.py_tools
from S2.query import AmbiguousPlayerError, UnknownParameterError
import S2.directory
from S2.sdb_dt import Game_DT
DATA_DIR = S2.directory.DATA_DIR("NBA")
CLIENT_DIR = S2.directory.CLIENT_DIR


CURRENT_SEASON = 2020 # also update aasb_from_date and playoffs_from_date in prepare
DB_STRINGS = ["home","away"]

def box_url(date,team,opp,site):
    season = NBA.prepare.season_from_date(date)
    team = NBA.teams.find_SR_abbreviation_from_nickname_and_season(team,season)
    opp = NBA.teams.find_SR_abbreviation_from_nickname_and_season(opp,season)
    if site=='home': hteam = team;ateam=opp
    else: ateam = team;hteam=opp
    return "http://www.basketball-reference.com/boxscores/%s0%s.html"%(date,hteam)

def box_link(date,team,opp,site):
    url = box_url(date,team,opp,site)
    return "<a href=%s>recap</a>"%url

class NBA_DT(Game_DT):

    def __init__(self,data_dirs=[],name="games",team_names=NBA.teams.teams,box_link=box_link):
        print "NBA.nba_dt.__init__.data_dirs:",data_dirs
        Game_DT.__init__(self, data_dirs=data_dirs,name=name,update_cache_on_change_offset=0,team_names=team_names)
        self.box_link = box_link
        self.ateam = "Team"
    def prepare(self, joined_headers):
        #print "prepare: header:",self.headers
        self.header_aliases = {} # need to take care of these in code_access_from_parameters
        if  self.offset_from_header_with_owners("site") is None:
            self.add_object(PyQL.columns.Column(name='site',format='%s',data=['home','away']*(len(self[0])/2)))
        if  self.offset_from_header_with_owners("season") is None:
            self.add_object(PyQL.columns.Column(name='season',format='%d',
			   data=map(lambda d,sfd=NBA.prepare.season_from_date:sfd(d),
				    self.value_from_header_with_owners('date').value())
					  ))
        lex_headers = map(lambda x:x.split('.')[-1],joined_headers + self.headers)        # make owner prepix optional
        lex_headers = dict.fromkeys(lex_headers).keys()  # remove duplicates
        parameters=map(lambda x,pp=self.parameter_prefix,op=self.owner_prefix: pp + op + x, lex_headers)
        self.build_lexer(parameters=parameters)

        NBA.prepare.set_hierarchy_fields(self)
        NBA.prepare.add_join_fields(self)
        NBA.prepare.add_std_fields(self)
        self.season_offset = self.offset_from_header_with_owners("season")
        self.site_offset = self.offset_from_header_with_owners("site")
        self.date_offset = self.offset_from_header_with_owners("date")
        #print "s.date_off:",self.date_offset
        self.points_offset = self.offset_from_header_with_owners("points")
        self._players_offset = self.offset_from_header_with_owners("_players")

        self.reference_dictionary = {
            'p':self.offset_from_header_with_owners("_previous game"),
            'P':self.offset_from_header_with_owners("_previous match up"),
            'n':self.offset_from_header_with_owners("_next game"),
            'N':self.offset_from_header_with_owners("_next match up")}
        #return
        self.update_cache_on_change_offset = self.date_offset
        NBA.prepare.add_nice_fields(self)
        self.db_strings = DB_STRINGS
        lex_headers = map(lambda x:x.split('.')[-1],joined_headers + self.headers + self.header_aliases.keys())
        lex_headers = dict.fromkeys(lex_headers).keys()  # remove duplicates
        parameters=map(lambda x,pp=self.parameter_prefix,op=self.owner_prefix: pp + op + x, lex_headers)
        self.build_lexer(parameters=parameters)
        self.ownerless_headers = dict.fromkeys(map(lambda x:x.split(".")[-1],self.headers)).keys()

    # needed for Bench and Starters
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
            #elif self.normalize_team_name(terms[0]) in self.normalized_team_names: team = terms[0]
            elif terms[0] in self.team_names+[self.ateam]: team = terms[0]
            else: player = terms[0]

        elif n_terms == 3: # could be  team:player, team:join, or player:join
            if self.join_pat.match(terms[1]):     # a join: could be team:join and player:join
                join = terms[1]
                #if   self.normalize_team_name(terms[0]) in self.normalized_team_names: team = terms[0]
                if   terms[0] in self.team_names+[self.ateam]: team = terms[0]
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
        if team: team_condition = "(%s=='%s' or None)*"%(self.code_access_from_parameter("%s:team"%join),   team)
        else: team_condition = ""


        if player:
            #print "nba player query"
            parameter_offset = self.player_dts['player'].offset_from_header_with_owners(parameter)
            if parameter_offset is None:
                raise UnknownParameterError(parameter)

            players_offset = self.player_table_offsets['player']

            if player in ['sum','max','min','list']:
                # this method with arg :  splice of all player rows for this game.
                return  "(%s%s( filter( lambda x:x is not None,_player[%d].data[min(_g[%d][_%s].values()):1+max(_g[%d][_%s].values())] )))"%(
                                   team_condition,player, parameter_offset, players_offset, join, players_offset, join)

            if player == 'Starters':
                return  "(%ssum( filter( lambda x:x is not None,_player[%d].data[min(_g[%d][_%s].values()):min(_g[%d][_%s].values())+5] )))"%(
                                   team_condition, parameter_offset, players_offset, join, players_offset, join)

            if player == 'Bench':
                return  "(%ssum( filter( lambda x:x is not None,_player[%d].data[min(_g[%d][_%s].values())+5:max(_g[%d][_%s].values())+1] )))"%(
                                   team_condition, parameter_offset, players_offset, join, players_offset, join)
            player_names = S2.query.find_player(self.player_dts['player'].name_dt,name=player,team=team)
            if len(player_names) != 1:
                raise AmbiguousPlayerError(player,player_names)
            else:
                player = player_names[0]
            if parameter == "minutes":
                return "(%s(_player[%d][_g[%d][_%s]['%s']] if _g[%d][_%s].has_key('%s') else 0))"%(team_condition,parameter_offset,
                                                                                       players_offset,join,player,
                                                                                       players_offset,join,player)

            return "(%s_player[%d][_g[%d][_%s]['%s']])"%(team_condition,parameter_offset, players_offset,join,player)

        # a games table parameter
        #offset = self.offset_from_header_with_owners(parameter)
        offsets = self.offsets_from_header(parameter)
        if offsets is None:
            raise UnknownParameterError(parameter)
        mc_ref = self.mc_reference(table='_d',offsets=offsets,row='_%s'%join)
        return "(%s%s)"%(team_condition,mc_ref)
        #return "(%s_g[%d][_%s])"%(team_condition,offset,join)     # 20110729 allow Cubs:hits=3


def schedule_for_date(date):
    f = os.path.join(DATA_DIR,"Covers","Schedule","_Pickle","%s.pkl"%date)
    print "looking for",f
    if os.path.isfile(f):
        return cPickle.load(open(f))

def loader(cid=''):
    # confusingly, this import cannot be up top.
    import NBA.player_dt
    # NB: NBA columns are built from NBA and other pickled boxes
    data_dirs = [(os.path.join(DATA_DIR,"Schedule","_Column"),"Schedule"),
                 (os.path.join(DATA_DIR,"NBA","Box","_Column","Game"),"Box"),
                 (os.path.join(DATA_DIR,"Covers","Schedule","_Column"),"Covers"),
                 (os.path.join(CLIENT_DIR,"SDB","NBA","Data","_Column"),"SDB"),
                ]
    owners = ['Schedule','Box','SDB']   # don't let a client called `Schedule` overwrite!
    for d in glob.glob(os.path.join(CLIENT_DIR,"*","NBA","Data","_Column")):
        print "inspecting",d
        parts = d.split(os.path.sep)
        #print "p:",parts
        client = parts[parts.index("_Column")-3]
        if client in owners: continue
        print "for client",client

        if glob.glob(os.path.join(d,"*.pkl")):
           data_dirs.append((d,client))
    nba = NBA_DT(data_dirs=data_dirs)
    nba.icon_dict = S2.sdb_dt.load_icons('NBA','*.png')
    nba.nice_team = lambda x:{'Seventysixers':'76ers','Trailblazers':'Blazers','Timberwolves':'T-Wolves',
                              'Cavaliers':'Cavs','Mavericks':'Mavs'}.get(x,x)
    nba.player_dts = {}
    nba.player_table_offsets = {}
    nba.player_table_names = ["player"]
    player_headers = []

    for ptn in nba.player_table_names:
        print "loading up player dt",ptn
        nba.player_dts[ptn] = NBA.player_dt.Player(data_dirs=[(os.path.join(DATA_DIR,"NBA","Box","_Column",ptn.title()),"Box")],
                                                   name=ptn)
        #nba.player_dts[ptn].show_metacode = 1
        nba.player_dts[ptn].games = nba
        nba.player_dts[ptn].icon_dict= nba.icon_dict
        nba.player_table_offsets[ptn] = nba.offset_from_header("_%s"%ptn) # prepare needs this
        nba.player_dts[ptn].prepare(nba.headers)
        player_headers += nba.player_dts[ptn].headers

    nba.prepare(player_headers)
    for ptn in nba.player_table_names:
        nba.player_table_offsets[ptn] = nba.offset_from_header("_%s"%ptn) # might have changed with nba.prepare
        nba.player_dts[ptn].prepare(nba.headers+player_headers)
        nba.player_dts[ptn].build_name_dt()
    return nba



def test_query(nba):
    sdql = "date@Bulls:points>110"
    print "sdql",sdql
    res = nba.query(sdql)[0][0].data
    print res[0]

def test_players(nba):
    res = nba.players.query("A(points)@1")
    print res

def test_formats():
    import NBA.formats
    print "test game fields"
    sdql = NBA.formats.summary_fields() + "@team=Bulls and date=20110506"
    print "sdql:",sdql
    res = nba.sdb_query(sdql)
    print NBA.formats.summary_html(res[0])


def dump_s1_schedule(nba):
    res = nba.query("(date,team,o:team,line,total,'')@site='home' and season=2012")[0][0]
    res = map(lambda x:'*'.join(map(str,x)),res)
    out = '\n'.join(res+[''])
    out = out.replace('*None','*')
    open('/tmp/nba_lines_2012.txt','w').write(out)

def dump_s1_lines(nba):
    res = nba.query("(date,team,line,total,'')@site='home' and season=2012")[0][0]
    res = map(lambda x:'*'.join(map(str,x)),res)
    out = '\n'.join(res+[''])
    out = out.replace('*None','*')
    open('/tmp/nba_lines_2012.txt','w').write(out)

def dump_for_tpm(nba,c='season=2014'):
    team_parameters = "(_i+1-2*(_i%2)) as '_opponent',_previous game,_next game,_previous match up,_next match up,assists, biggest lead, blocks, conference, defensive rebounds, division, fast break points, field goals attempted, field goals made, fouls, free throws attempted, free throws made, game number, line, offensive rebounds, points, points in the paint,  rebounds, rest, seed,  site, steals, team, team rebounds, three pointers attempted, three pointers made, turnovers"
    game_parameters = '_i,date,line,total,attendance, lead changes, time of game, times tied, total, overtime, playoffs, round, season, series game, series games'
    tparameters = map(lambda x:x.strip(),team_parameters.split(','))
    gparameters = map(lambda x:x.strip(),game_parameters.split(','))
    oparameters = map(lambda x:'o:'+x,tparameters)
    #tparameters = map(lambda x:'t:'+x,tparameters)
    #select = ','.join(tparameters + oparameters+gparameters)
    select = ','.join(gparameters + tparameters)
    print "select:",select
    res = nba.query("(%s)@%s"%(select,c))[0][0]
    res = map(lambda x:'\t'.join(map(str,x)),res)
    out =  '\t'.join(gparameters + tparameters).replace('o:','away ').replace('t:','home ') + '\n'
    out += '\n'.join(res+[''])
    po = nba.offset_from_header('position')
    open('/tmp/nba_games.tab','w').write(out)


    select = "team,date,assists,blocks,defensive rebounds,field goals attempted,field goals made,fouls,free throws attempted,free throws made,minutes,name,offensive rebounds,plus minus,points,position,rebounds,steals,three pointers attempted,three pointers made,turnovers,position + (' '*(_d[%d][_i].strip() == 'C') or 'B'*(_d[%d][_i].strip() == '') or '2'*(_d[%d][_i]==_d[%d][_i-1]) or '1')"%(po,po,po,po)


    res = nba.player_dts['player'].query("(%s)@%s"%(select,c))[0][0]
    res = map(lambda x:'\t'.join(map(str,x)),res)
    print "lres",len(res)
    out =  select.replace(',','\t') + '\n'
    out += '\n'.join(res+[''])
    open('/tmp/nba_players.tab','w').write(out)

if __name__ == "__main__":
    print "sch:",schedule_for_date(20170106)
    #nba = loader()
    #dump_for_tpm(nba,c='season>=2010')
    #dump_s1_lines(nba)
    #code_access_from_parameter("Bulls:p:points")
    #nba.show_metacode = 1
    #nba.players.show_metacode = 1
    #nba.print_exceptions =1
    #nba.players.print_exceptions = 0
    #test_players(nba)
    #test_query(nba)
    #test_suite()
    #test_formats()

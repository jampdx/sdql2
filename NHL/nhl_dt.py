
#!/usr/bin/env python
# This file
#     defines schema
#     loads the database from the file system
#     uses prepare to get reference fields, nice fields

import sys, os, re, string, glob


import NHL.prepare
#reload(NHL.prepare)
import NHL.teams
import PyQL.columns
import PyQL.inputs
import PyQL.outputs
import PyQL.column_types
from PyQL.dt import DT
import cPickle
from S2.query import AmbiguousPlayerError,UnknownParameterError
import S2.sdb_dt
from S2.directory import CLIENT_DIR,DATA_DIR
DATA_DIR = DATA_DIR('nhl')
from S2.sdb_dt import Game_DT


# stuff that other files need are defined up top
CURRENT_SEASON = 2020
DB_STRINGS = ['home','away']

class NHL_DT(Game_DT):

    def __init__(self,data_dirs=[],name="games"):
        print "NHL.nhl_dt.__init__.data_dirs:",data_dirs
        Game_DT.__init__(self, data_dirs=data_dirs,name=name,update_cache_on_change_offset=0,team_names=NHL.teams.teams)
        #self.box_link = NHL.formats.box_link

    def prepare(self, joined_headers):
        #print "prepare: header:",self.headers
        self.header_aliases = {}
        if  self.offset_from_header("site",owners=['Schedule']) is None:
            self.add_object(PyQL.columns.Column(name='site',format='%s',data=['home','away']*(len(self[0])/2)))
        if  self.offset_from_header("season",owners=['Schedule']) is None:
            self.add_object(PyQL.columns.Column(name='season',format='%d',
			   data=map(lambda d,sfd=NHL.prepare.season_from_date:sfd(d),
				    self.value_from_header('date',owners=['Schedule']).value())
					  ))
        self.season_offset = self.offset_from_header("season",owners=['','Schedule'])
        NHL.prepare.set_hierarchy_fields(self)
        NHL.prepare.add_join_fields(self)

        lex_headers = map(lambda x:x.split('.')[-1],joined_headers + self.headers)        # make owner prepix optional
        lex_headers = dict.fromkeys(joined_headers + lex_headers).keys()  # remove duplicates
        #NHL.prepare.add_std_fields(self)
        parameters=map(lambda x,pp=self.parameter_prefix,op=self.owner_prefix: pp + op + x, lex_headers)
        #print "parametsers",parameters
        self.build_lexer(parameters=parameters)
        self._players_offset = self.offset_from_header("_players")

        self.reference_dictionary = {
            'p':self.offset_from_header("_previous game"),
            'P':self.offset_from_header("_previous match up"),
            'n':self.offset_from_header("_next game"),
            'N':self.offset_from_header("_next match up")}
        #print "self.reference_dictionary:",self.reference_dictionary
        #return
        NHL.prepare.add_nice_fields(self)
        NHL.prepare.add_std_fields(self)
        self.update_cache_on_change_offset = self.offset_from_header('date')
        self.db_strings = DB_STRINGS
        # include new nice headers and remove duplicates
        lex_headers = map(lambda x:x.split('.')[-1],joined_headers + self.headers)        # make owner prepix optional
        lex_headers = dict.fromkeys(joined_headers + lex_headers).keys()  # remove duplicates

        parameters=map(lambda x,pp=self.parameter_prefix,op=self.owner_prefix: pp + op + x, lex_headers)
        self.build_lexer(parameters=parameters)
        self.ownerless_headers = dict.fromkeys(map(lambda x:x.split(".")[-1],self.headers)).keys()

def loader(cid=''):
    # confusingly, this import cannot be up top.
    import NHL.player_dt
    # needed to leave owners here since different sources have the same field
    data_dirs = [("/home/jameyer/S2/NHL/Data/Covers/Schedule/_Column","Schedule"),
                  ("/home/jameyer/S2/NHL/Data/Covers/Box/_Column/Game","Box"),
                  #("/home/jameyer/S2/NHL/Data/Covers/Bets/_Column","Covers.Bets"),
                 (os.path.join(CLIENT_DIR,"SDB","NHL","Data","_Column"),"SDB"),
                ]
    owners = ['Schedule','Box','SDB']
    for d in glob.glob(os.path.join(CLIENT_DIR,"*","NHL","Data","_Column")):
        print "inspecting",d
        parts = d.split(os.path.sep)
        print "p:",parts
        client = parts[parts.index("_Column")-3]
        if client in owners: continue
        print "for client",client
        if glob.glob(os.path.join(d,"*.pkl")):
            data_dirs.append((d,client))
    nhl = NHL_DT(data_dirs)
    nhl.icon_dict = S2.sdb_dt.load_icons('NHL','*.png')
    print "nhl headers:",nhl.headers

    #nhl.players = NHL.players_dt.Players([("/home/jameyer/S2/NHL/Data/Covers/Box/_Column/Player","Covers.Box")])
    nhl.player_table_names = ['skater']

    nhl.player_table_offsets = {}
    nhl.player_dts = {}
    player_headers = []

    for ptn in nhl.player_table_names:
        print "loading up player dt",ptn
        nhl.player_dts[ptn] = NHL.player_dt.Player(data_dirs=[(os.path.join(DATA_DIR,"Covers","Box","_Column",ptn.title()),"Box")],
                                                   name=ptn)
        print "headers:",nhl.player_dts[ptn].headers
        #nhl.player_dts[ptn].show_metacode = 1
        nhl.player_dts[ptn].games = nhl
        nhl.player_table_offsets[ptn] = nhl.offset_from_header("_%s"%ptn) # prepare needs this
        nhl.player_dts[ptn].prepare(nhl.headers)
        player_headers += nhl.player_dts[ptn].headers

    nhl.prepare(player_headers)
    for ptn in nhl.player_table_names:
        nhl.player_table_offsets[ptn] = nhl.offset_from_header("_%s"%ptn) # might have changed with nhl.prepare
        nhl.player_dts[ptn].prepare(nhl.headers+player_headers)
        nhl.player_dts[ptn].build_name_dt()
    return nhl

def test_query(nhl):
    sdql = "date@Blackhawks:goals>5"
    print "sdql",sdql
    res = mlb.query(sdql)[0][0].data
    print res[0]

def test_players(nhl):
    res = nhl.players.query("A(points)@team")
    print res

def test_formats(nhl):
    import NHL.formats
    print "test game fields"
    sdql = NHL.formats.summary_fields() + "@team=Blackhawks and season=2010"
    print "sdql:",sdql
    res = nhl.sdb_query(sdql)
    print NHL.formats.summary_html(res[0])


def dump_city_dict(nhl):
    # nasty little thing for parse schedule
    res = nhl.query("R(full name)@team").reduced(None)
    for fn in res[0]:
        nick = NHL.teams.nickname_from_full_name(fn)
        city = fn.split(nick)[0].strip()
        if city == 'NY': city += " " + nick
        print '"%s":"%s",'%(city,nick)

if __name__ == "__main__":
    nhl = loader()
    #dump_city_dict(nhl)

    #code_access_from_parameter("Bulls:p:points")
    #nhl.show_metacode = 1
    #nhl.players.show_metacode = 1
    #nhl.print_exceptions =1
    #nhl.players.print_exceptions = 0
    test_players(nhl)
    #test_query(nhl)
    #test_suite()
    #test_formats(nhl)

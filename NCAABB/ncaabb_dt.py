#!/usr/bin/env python
# This file
#     defines schema
#     loads the database from the file system
#     uses prepare to get reference fields, nice fields

import sys, os, re, string, glob

import NBA.nba_dt
import NCAABB.prepare
#reload(NCAABB.prepare)
import NCAABB.teams
import PyQL.columns
import PyQL.inputs
import PyQL.outputs
import PyQL.column_types
from PyQL.dt import DT
import cPickle
import PyQL.py_tools
from S2.query import AmbiguousPlayerError, UnknownParameterError
from S2.directory import CLIENT_DIR,DATA_DIR
import S2.sdb_dt
DATA_DIR = DATA_DIR("ncaabb")


# stuff that other files need are defined up top
CURRENT_SEASON = 2019
DB_STRINGS = ["home","away","neutral","NCAA","NIT","Conference"] #+ NCAABB.teams.teams.keys())


def covers_box_link(date,gid):
    if not gid: return ''
    season = NCAABB.prepare.season_from_date(date)
    #return "<a href=http://www.covers.com/pageLoader/pageLoader.aspx?page=/data/ncb/results/%d-%d/boxscore%s.html>box</a>"%(season,int(season)+1,gid)
    return "<a href=https://www.covers.com/sport/basketball/ncaab/boxscore/%s>box</a>" % gid


class NCAABB_DT(NBA.nba_dt.NBA_DT):
    def __init__(self,data_dirs=[],name="games"):
        NBA.nba_dt.NBA_DT.__init__(self,data_dirs=data_dirs,name=name,team_names=NCAABB.teams.teams.keys(),box_link=covers_box_link)
    def prepare(self, joined_headers):
        #print "prepare: header:",self.headers
        self.header_aliases = {} # need to take care of these in code_access_from_parameters
        if  self.offset_from_header("site",owners=['Schedule']) is None:
            self.add_object(PyQL.columns.Column(name='Schedule.site',format='%s',data=['home','away']*(len(self[0])/2)))
        if  self.offset_from_header("season",owners=['Schedule']) is None:
            self.add_object(PyQL.columns.Column(name='Schedule.season',format='%d',
			   data=map(lambda d,sfd=NCAABB.prepare.season_from_date:sfd(d),
				    self.value_from_header('date',owners=['Schedule']).value())
					  ))
        NCAABB.prepare.add_join_fields(self)
        #NCAABB.prepare.add_std_fields(self)
        lex_headers = dict.fromkeys(joined_headers + self.headers).keys()  # remove duplicates
        lex_headers = map(lambda x:x.split('.')[-1],joined_headers + self.headers)
        lex_headers = dict.fromkeys(lex_headers).keys()
        #print "building lexer with heaeders:",lex_headers

        self.build_lexer(parameters=map(lambda x,pp=self.parameter_prefix,op=self.owner_prefix: pp + op + x, lex_headers))
        self.season_offset = self.offset_from_header("season",owners=['Schedule'])
        self.site_offset = self.offset_from_header("site",owners=['Schedule'])
        self.date_offset = self.offset_from_header("date",owners=['Schedule'])
        self.points_offset = self.offset_from_header("points",owners=['Box'])
        self._players_offset = self.offset_from_header("_players")

        self.reference_dictionary = {
            'p':self.offset_from_header("_previous game"),
            'P':self.offset_from_header("_previous match up"),
            'n':self.offset_from_header("_next game"),
            'N':self.offset_from_header("_next match up")}

        NCAABB.prepare.add_nice_fields(self)
        # moved down 20180114
        NCAABB.prepare.add_std_fields(self)

        self.db_strings = DB_STRINGS
        self.update_cache_on_change_offset = self.date_offset
        # include new nice headers and remove duplicates
        lex_headers = map(lambda x:x.split('.')[-1],joined_headers + self.headers + self.header_aliases.keys())
        lex_headers = dict.fromkeys(lex_headers).keys()
        #print "building lexer with heaeders:",lex_headers
        self.build_lexer(parameters=map(lambda x,pp=self.parameter_prefix,op=self.owner_prefix: pp + op + x, lex_headers))
        # tried to share more memory after a fork to no avail.
        #for i in range(len(self.data)):
        #    self.data[i].data = tuple(self.data[i].data)
        #self.data = tuple(self.data)
        self.ownerless_headers = dict.fromkeys(map(lambda x:x.split(".")[-1],self.headers)).keys()





def loader():
    # confusingly, this import cannot be up top.
    import NCAABB.player_dt
    data_dirs = [ # this is the order in which non-owner specified parameters will be searched.
                        ("/home/jameyer/S2/NCAABB/Data/Covers/Box/_Column/Game","Box"),
                        #("/home/jameyer/S2/NCAABB/Data/Covers/Bets/_Column","Covers.Bets"),
                        ("/home/jameyer/S2/NCAABB/Data/Schedule/_Column","Schedule"), # D/Sch/Col/ holds the normalized schedule.
                        #("/home/jameyer/S2/NCAABB/Data/Covers/Schedule/_Column","KSC"),
                        (os.path.join(CLIENT_DIR,"SDB","NCAABB","Data","_Column"),"SDB"),
                       ]
    owners = ['Schedule','Box','SDB']
    for d in glob.glob(os.path.join(CLIENT_DIR,"*","NCAABB","Data","_ColumnXXX")):
        print "inspecting",df
        parts = d.split(os.path.sep)
        print "p:",parts
        client = parts[parts.index("_Column")-3]
        if client in owners: continue
        print "for client",client
        if glob.glob(os.path.join(d,"*.pkl")):
            data_dirs.append((d,client))

    ncaabb = NCAABB_DT(data_dirs)
    ncaabb.show_metacode=0
    ncaabb.player_dts = {}
    ncaabb.player_table_offsets = {}
    ncaabb.player_table_names = ["player"]
    player_headers = []

    for ptn in ncaabb.player_table_names:
        ncaabb.player_dts[ptn] = NCAABB.player_dt.Player(data_dirs=[(os.path.join(DATA_DIR,"Covers","Box","_Column",ptn.title()),"Box")],
                                                   name=ptn)
        #ncaabb.player_dts[ptn].show_metacode = 1
        ncaabb.player_dts[ptn].games = ncaabb
        ncaabb.player_table_offsets[ptn] = ncaabb.offset_from_header("_%s"%ptn) # prepare needs this
        ncaabb.player_dts[ptn].prepare(ncaabb.headers)
        player_headers += ncaabb.player_dts[ptn].headers
        ncaabb.player_dts[ptn].show_metacode = 0
    #print "player_headers:",player_headers
    ncaabb.prepare(player_headers)
    #return ncaabb
    for ptn in ncaabb.player_table_names:
        ncaabb.player_table_offsets[ptn] = ncaabb.offset_from_header("_%s"%ptn) # might have changed with ncaabb.prepare
        ncaabb.player_dts[ptn].prepare(ncaabb.headers+player_headers)
        #print "headers:",ncaabb.player_dts[ptn].headers
        ncaabb.player_dts[ptn].build_name_dt()
    S2.sdb_dt.load_joins('ncaabb',ncaabb,os.path.join(CLIENT_DIR,"SDB.sean","NCAABB","Data","_Raw","*.lbd"),
                                                                                                 owner="SDB")
    return ncaabb


# database on server occasionally failed to load properly. make a simple test query here.
def safe_loader(retries=3):
    for i in range(retries):
        ncaabb = loader()
        try:
            res = ncaabb.query("_i@_i=0")[0][0][0]
            #print res
            assert res == 0
            return ncaabb
        except:
            print "safe loader failed %d / %d"%(i+1,retries)
            pass


def test_query(ncaabb):
    sdql = "date@points>110"
    print "sdql",sdql
    res = mlb.query(sdql)[0][0].data
    print res[0]

def test_players(ncaabb):
    res = ncaabb.players.query("A(points)@team")
    print res

def test_formats():
    import NCAABB.ncaabb_formats
    print "test game fields"
    sdql = NCAABB.ncaabb_formats.summary_fields() + "@date=20110506"
    print "sdql:",sdql
    res = ncaabb.sdb_query(sdql)
    print NCAABB.formats.summary_html(res[0])


if __name__ == "__main__":
    ncaabb = loader()
    #ncaabb.show_metacode = 1
    #ncaabb.players.show_metacode = 1
    #ncaabb.print_exceptions =1
    #ncaabb.players.print_exceptions = 0
    #test_players(ncaabb)
    #test_query(ncaabb)
    #test_suite()
    #test_formats()

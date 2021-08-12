#!/usr/bin/env python
# This file
#     defines schema
#     loads the database from the file system

import sys, os, re, string, glob

from S2.directory import CLIENT_DIR
from S2.query import AmbiguousPlayerError, UnknownParameterError
import PyQL.columns
import PyQL.inputs
import PyQL.outputs
import PyQL.py_tools
import PyQL.column_types
from PyQL.dt import DT
import cPickle
#import NCAAFB.teams
import NCAAFB.prepare
import NCAAFB.formats
import S2.query
from S2.directory import DATA_DIR
from S2.sdb_dt import Game_DT


DATA_DIR = DATA_DIR("ncaafb")

CURRENT_SEASON = 2020
DB_STRINGS = ['away','home','neutral','grass','artificial','1A','1AA']  #no need to include team names as Titled Words are strings

class NCAAFB_DT(Game_DT):


    def __init__(self,data_dirs=[],name="games"):
        print "NCAAFB.ncaafb_dt.__init__.data_dirs:",data_dirs
        Game_DT.__init__(self, data_dirs=data_dirs,name=name,update_cache_on_change_offset=None,team_names=[]) #NCAAFB.teams.teams)
        self.box_link = NCAAFB.formats.box_link


    def prepare(self, joined_headers=[]):
        self.header_aliases = {}
        if  self.offset_from_header("site") is None:
            self.add_object(PyQL.columns.Column(name='site',format='%s',data=['home','away']*(len(self[0])/2)))
        if  self.offset_from_header("season") is None:
            self.add_object(PyQL.columns.Column(name='season',format='%d',
			   data=map(lambda x,s=NCAAFB.prepare.season_from_date:s(x),
				    self.value_from_header('date').value())))
        NCAAFB.prepare.set_hierarchy_fields(self)
        NCAAFB.prepare.combine_fields(self) #need this before add std feidls.
        NCAAFB.prepare.add_join_fields(self)
        NCAAFB.prepare.add_std_fields(self)
        lex_headers = map(lambda x:x.split('.')[-1],joined_headers + self.headers)        # make owner prefix optional
        lex_headers = dict.fromkeys(lex_headers).keys()  # remove duplicates##
        parameters=map(lambda x,pp=self.parameter_prefix,op=self.owner_prefix: pp + op + x, lex_headers)
        self.build_lexer(parameters=parameters)
        self.season_offset = self.offset_from_header("season")
        self.site_offset = self.offset_from_header("site")
        self.date_offset = self.offset_from_header("date")
        self.reference_dictionary = {
            'p':self.offset_from_header("_previous game"),
            'P':self.offset_from_header("_previous match up"),
            'n':self.offset_from_header("_next game"),
            'N':self.offset_from_header("_next match up")}
        NCAAFB.prepare.add_nice_fields(self)
        self.db_strings = DB_STRINGS
        self.update_cache_on_change_offset = self.date_offset
        lex_headers = map(lambda x:x.split('.')[-1],joined_headers + self.headers + self.header_aliases.keys())
        lex_headers = dict.fromkeys(lex_headers).keys()  # remove duplicates
        parameters=map(lambda x,pp=self.parameter_prefix,op=self.owner_prefix: pp + op + x, lex_headers)
        self.build_lexer(parameters=parameters)
        self.ownerless_headers = dict.fromkeys(map(lambda x:x.split(".")[-1],self.headers)).keys()


def dump_key_players(ncaafb):
    for pt in ['receiving','rushing']:
        res = ncaafb.player_dts[pt].query("U((name,team))@1")
        print res

def loader():
    import NCAAFB.player_dt
    #reload(NCAAFB.player_dt)
    data_dirs=[(os.path.join(DATA_DIR,"Schedule/_Column"),"Schedule"),
               (os.path.join(DATA_DIR,"Covers/Box/_Column"),"Box"),
               (os.path.join(DATA_DIR,"Covers/Schedule/_Column"),"B2"),
               #(os.path.join(DATA_DIR,"Covers/Bets/_Column"),"Covers.Bets"),
               (os.path.join(CLIENT_DIR,"SDB","NCAAFB","Data","_Column"),"SDB"),
              ]
    owners = ['Schedule','SDB','Box','B2']    # don't let a client called `Schedule` overwrite!
    for d in glob.glob(os.path.join(CLIENT_DIR,"*","NCAAFB","Data","_Column")):
        print "inspecting",d
        parts = d.split(os.path.sep)
        print "p:",parts
        client = parts[parts.index("_Column")-3]
        if client in owners: continue
        print "for client",client
        if glob.glob(os.path.join(d,"*.pkl")):
            data_dirs.append((d,client))

    print "dd:",data_dirs
    ncaafb = NCAAFB_DT(data_dirs=data_dirs)
    print "ncaafb headers:",ncaafb.headers
    ncaafb.player_table_names = ['kickoff_return',"passing","rushing",'interception','punting','punt_return','receiving']
    #ncaafb.player_table_names = ["rushing"]
    ncaafb.player_table_offsets = {}
    ncaafb.player_dts = {}
    player_headers = []

    for ptn in ncaafb.player_table_names:
        print "loading up player dt",ptn
        ncaafb.player_dts[ptn] = NCAAFB.player_dt.Player(data_dirs=[(os.path.join(DATA_DIR,"Covers","Box","_Column",ptn.title()),"Box")],
                                                   name=ptn)
        #ncaafb.player_dts[ptn].show_metacode = 1
        ncaafb.player_dts[ptn].games = ncaafb
        ncaafb.player_table_offsets[ptn] = ncaafb.offset_from_header("_%s"%ptn) # prepare needs this
        ncaafb.player_dts[ptn].prepare(ncaafb.headers)
        player_headers += ncaafb.player_dts[ptn].headers

    ncaafb.prepare(player_headers)
    for ptn in ncaafb.player_table_names:
        ncaafb.player_table_offsets[ptn] = ncaafb.offset_from_header("_%s"%ptn) # might have changed with ncaafb.prepare
        ncaafb.player_dts[ptn].prepare(ncaafb.headers+player_headers)
        print ptn,ncaafb.player_dts[ptn].headers
        ncaafb.player_dts[ptn].build_name_dt()
    print "look for look back dicts to load"
    try:
        S2.sdb_dt.load_joins('ncaafb',ncaafb,os.path.join(CLIENT_DIR,"SDB.ogn","NCAAFB","Data","_Raw","*.lbd"),owner='SDB')
    except:
        print "error in loading SDB.ogn join"
    try:
        S2.sdb_dt.load_joins('ncaafb',ncaafb,os.path.join(CLIENT_DIR,"KS","NCAAFB","Data","_Raw","*.lbd"))
    except:
        print "error in loading KS join"
    print "loader loaded up headers",ncaafb.headers
    return ncaafb


########## tests ###########

def test_suite():

    sdql = "date@Cubs:hits=23"
    print "sdql",sdql
    res = mlb.query(sdql)[0][0].data
    print res[0]
    assert res[0] == 20050404


def test_query():
    import NCAAFB.query
    #ncaafb.show_metacode  = 1
    kwargs = {}
    kwargs["_qt"] = "rushing"
    kwargs["sdql"] = "rushes=10"
    res = NCAAFB.query.query(**kwargs)
    print res
    #print PyQL.outputs.html(res)

def dump_for_S1(ncaafb,f='/tmp/ncaafb.py'):
    import time
    text = ["# dumped by dt.py on %s"%time.ctime()]
    text.append("import sys")
    text.append("sys.path += ['/home/jameyer/PyQL/Source']")
    text.append("from dt import DT")
    text.append("from columns import Column")
    text.append("")
    text.append("dt = DT()")
    for i in range(len(ncaafb.data)):
        #XXX need to add: if format is a lambda than warn and don't save
        header =  ncaafb.headers[i].split('.')[-1]
        if header[0] == '_': header = header[1:]
        text.append("dt.add_object(Column(name=r'''%s''',format=r'''%s'''))"%(
                          header,ncaafb.data[i].str_format))
    for j in range(len(ncaafb.data[0])):
        text.append("dt.append((")
        #print "j:",j
        for i in range(len(ncaafb.data)):
            #print "i:",i
            text.append(`ncaafb.data[i][j]` + ',')
        text.append("))")

    text.append("")
    open(f,'w').write(string.join(text,"\n"))


def dump_for_ar(ncaafb):
    sdql = "season, date, week,  surface,  _temperature as temperature, _wind as 'wind speed',line, total,team, o:team, rushing yards, o:rushing yards, passing yards, o:passing yards, rushes, o:rushes, passes, o:passes, conference, o:conference, division, o:division, turnovers, o:turnovers, quarter scores[0] + quarter scores[1] as 'first half points', o:quarter scores[0] + o:quarter scores[1] as 'o:first half points',points,o:points"
    res = ncaafb.query(sdql + "@site='home' and season=2002")[0]
    lout = ['\t'.join(res.headers)]
    for i in range(len(res[0])):
        l = []
        for j in range(len(res.headers)):
            l.append(str(res[j][i]))
        lout.append('\t'.join(l))
    print '\n'.join(lout)
    open("/tmp/ncaafb_ar.csv",'w').write('\n'.join(lout))


if __name__ == "__main__":
    pass
    ncaafb = loader()
    print ncaafb.query("date,team@Covers.Schedule.line is not None")
    #dump_key_players(ncaafb)
    #test_query()
    #dump_for_S1(ncaafb)
    #dump_for_ar(ncaafb)

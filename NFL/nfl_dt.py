#!/usr/bin/env python
# This file
#     defines schema
#     loads the database from the file system

CURRENT_SEASON = 2020

import sys, os, re, string, glob

from S2.directory import CLIENT_DIR, DATA_DIR, TOP_DIR
from S2.query import AmbiguousPlayerError, UnknownParameterError
import PyQL.columns
import PyQL.inputs
import PyQL.outputs
import PyQL.py_tools
import PyQL.column_types
from PyQL.dt import DT
import cPickle
import NFL.teams
import NFL.prepare
import NFL.formats
import S2.query

from S2.sdb_dt import Game_DT


DATA_DIR = DATA_DIR("nfl")

DB_STRINGS = ['neutral','away','home','grass','artificial']  #no need to include team names as Titled Words are strings

class NFL_DT(Game_DT):

    def __init__(self,data_dirs=[],name="games", verbose=False):
        if verbose: print "NFL.nfl_dt.__init__.data_dirs:",data_dirs
        Game_DT.__init__(self, data_dirs=data_dirs,name=name,update_cache_on_change_offset=0,team_names=NFL.teams.teams)
        self.box_link = NFL.formats.box_link


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
        self.reference_dictionary = {
            'p':self.offset_from_header("_previous game"),
            'P':self.offset_from_header("_previous match up"),
            'n':self.offset_from_header("_next game"),
            'N':self.offset_from_header("_next match up")}
        NFL.prepare.add_nice_fields(self)
        self.db_strings = DB_STRINGS
        self.update_cache_on_change_offset = self.date_offset
        lex_headers = map(lambda x:x.split('.')[-1],joined_headers + self.headers + self.header_aliases.keys())
        lex_headers = dict.fromkeys(lex_headers).keys()  # remove duplicates
        parameters=map(lambda x,pp=self.parameter_prefix,op=self.owner_prefix: pp + op + x, lex_headers)
        self.build_lexer(parameters=parameters)
        self.ownerless_headers = dict.fromkeys(map(lambda x:x.split(".")[-1],self.headers)).keys()


def dump_key_players(nfl):
    for pt in ['receiving','rushing']:
        res = nfl.player_dts[pt].query("U((name,team))@1")
        print res


def loader(cid='', verbose=False):
    import NFL.player_dt
    #reload(NFL.player_dt)
    data_dirs=[(os.path.join(DATA_DIR,"Schedule/_Column%s"%cid),"Schedule"),
               #(os.path.join(DATA_DIR,"NFL/Gamebook/_Column%s"%cid),"NFL"),
               #(os.path.join(DATA_DIR,"NFL/Play/_Column%s"%cid),"Box"),
               (os.path.join(DATA_DIR,"NFL/Box/_Column%s"%cid),"Box"),
               (os.path.join(CLIENT_DIR,"SDB","NFL","Data","_Column"),"SDB"),
              ]
    owners = ['Schedule','Box','SDB']    # don't let a client called `Schedule` overwrite!
    for d in glob.glob(os.path.join(CLIENT_DIR,"*","NFL","Data","_Column")):
        if verbose: print "inspecting",d
        parts = d.split(os.path.sep)
        if verbose: print "p:",parts
        client = parts[parts.index("_Column")-3]
        if client in owners: continue
        if verbose: print "for client",client
        if glob.glob(os.path.join(d,"*.pkl")):
            data_dirs.append((d,client))

    if verbose: print "dd:",data_dirs
    nfl = NFL_DT(data_dirs=data_dirs)
    nfl.icon_dict = S2.sdb_dt.load_icons("NFL","*.png")
    if verbose: print "nfl headers:",nfl.headers
    nfl.player_table_names = ['kickoff_returns','kicking','fumbles',"passing","rushing",'defense','punting','punt_returns','receiving']
    #nfl.player_table_names = ['kicking','fumbles',"passing","rushing",'defense','punting','punt_returns','receiving']
    nfl.player_table_offsets = {}
    nfl.player_dts = {}
    player_headers = []


    for ptn in nfl.player_table_names:
        if verbose: print "loading up player dt",ptn
        nfl.player_dts[ptn] = NFL.player_dt.Player(data_dirs=[(os.path.join(DATA_DIR,"NFL","Box","_Column",ptn.title()),"Box")],
                                                   name=ptn)
        #nfl.player_dts[ptn].show_metacode = 1
        nfl.player_dts[ptn].games = nfl
        nfl.player_table_offsets[ptn] = nfl.offset_from_header("_%s"%ptn) # prepare needs this
        nfl.player_dts[ptn].prepare(nfl.headers)
        nfl.player_dts[ptn].icon_dict = nfl.icon_dict
        player_headers += nfl.player_dts[ptn].headers
    nfl.prepare(player_headers)
    for ptn in nfl.player_table_names:
        nfl.player_table_offsets[ptn] = nfl.offset_from_header("_%s"%ptn) # might have changed with nfl.prepare
        nfl.player_dts[ptn].prepare(nfl.headers+player_headers)
        if verbose: print "ready to build name_dt for", ptn,nfl.player_dts[ptn].headers
        nfl.player_dts[ptn].build_name_dt()
    #nfl.print_exceptions=1
    #nfl.show_metacode=1
    #nfl.lol_data = [col.data for col in nfl.data]
    S2.sdb_dt.load_joins('nfl',nfl,os.path.join(CLIENT_DIR,"SDB.ogn","NFL","Data","_Raw","*.lbd"),owner="SDB")
    S2.sdb_dt.load_joins('nfl',nfl,os.path.join(CLIENT_DIR,"SDB","NFL","Data","_Raw","*.lbd"))
    S2.sdb_dt.load_joins('nfl',nfl,os.path.join(CLIENT_DIR,"KS","NFL","Data","_Raw","*.lbd"))
    return nfl


########## tests ###########

def test_suite():

    sdql = "date@Cubs:hits=23"
    print "sdql",sdql
    res = mlb.query(sdql)[0][0].data
    print res[0]
    assert res[0] == 20050404


def test_query():
    import NFL.query
    #nfl.show_metacode  = 1
    kwargs = {}
    kwargs["_qt"] = "rushing"
    kwargs["sdql"] = "rushes=10"
    res = NFL.query.query(**kwargs)
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

def dump_sdb_for_s3():
    import query
    sdql = "date,t:team,o:team,surface,t:coach,o:coach,t:regular season wins line,o:regular season wins line,t:line,o:line,total@not _i%2"
    kw= {'sdql':sdql,'output':'dt'}
    res = query.query(**kw)[0]
    for i in range(len(res[0])):
        d = {}
        for h,header in enumerate(res.headers):
            if res[h][i] is not None:
                d[header] = res[h][i]
        if d['date'] < 20200900:
            print("don't rewrite",)
            continue

        if d['t:team']=='Redskins':
            d['t:team'] = 'Washington'
        if d['t:team']=='Oilers':
            d['t:team'] = 'Titans'
        if d['o:team']=='Redskins':
            d['o:team'] = 'Washington'
        if d['o:team']=='Oilers':
            d['o:team'] = 'Titans'
        f = open("/home/jameyer/S3/Client/KS/Leagues/NFL/Data/_Pickle/%s_%s.pkl" % (d['date'],d['t:team']),'wb')
        print "dump",d
        cPickle.dump(d,f)


def refile_washington():
    files = ["/home/jameyer/S2/Client/SDB.ogn/NFL/Data/_Raw/coach.lbd", "/home/jameyer/S2/Client/SDB/NFL/Data/_Raw/regular season wins line.lbd"]
    for f in files:
        print "refile",f,"with Washinton"
        txt = open(f).read()
        txt = txt.replace('Redskins','Washington').replace('Oilers','Titans')
        open(f,'w').write(txt)

if ( __name__ == "__main__") :
    #refile_washington()
    dump_sdb_for_s3()
    #load_icons()
    #pass
    #nfl = loader()
    #load_joins('nfl',nfl,os.path.join(CLIENT_DIR,"SDB","NFL","Data","_Raw","*.lbd"))
    #dump_key_players(nfl)
    #test_query()
    #dump_for_S1(nfl)
    #dump_for_ar(nfl)

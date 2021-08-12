# TODO:
#  each client needs a their own default query, default fields, templates and outtputs
#  specify all these in args? build a client dict? make a method for each (ks_query ....) ???
#  this is half baked

from cgi import escape
import urllib
import os
from NBA.nba_dt import AmbiguousPlayerError
from NBA.loader import nba
import NBA.howto_query
import NBA.formats, NBA.player_formats
import PyQL.outputs,PyQL.py_tools
from S2.common_methods import clean_parameters
import S2.query


# methods accessed via S2.tornado_sport need to be defined here
import NBA.update as update
import NBA.tables as tables
import NBA.Sheets.ed # dispatch by client
import NBA.Sheets.wager_talk
import NBA.Sheets.ks_daily
import NBA.Sheets.white_label
import NBA.query_matrix as query_matrix


def sheet(sheet_owner,sheet,**kwargs):
    #print "nba.query.sheet owner:",sheet_owner, sheet
    #print "reloadinng NBA.Sheets.ed"
    #reload(NBA.Sheets.ks_daily)
    if sheet_owner.lower() == 'ks_daily':
        return NBA.Sheets.ks_daily.handler(nba,sheet,**kwargs)
    if sheet_owner.lower() == 'ed':
        return NBA.Sheets.ed.handler(nba,sheet,**kwargs)
    if sheet_owner.lower() == 'wager_talk':
        return NBA.Sheets.wager_talk.handler(nba,sheet,**kwargs)
    if sheet_owner.lower() == 'wl':
        #reload(NBA.Sheets.white_label)
        return NBA.Sheets.white_label.handler(nba,sheet,**kwargs)
    else:
        return "Your requested sheet %s %s was not found"%(sheet_owner,sheet)

DEFAULT_OWNERS = ["","SDB","Box","Schedule","Covers"]

def howto():
    ret = NBA.howto_query.html
    return ret

def XXXparameters(owners=[]):
    ret = "<a href=query>Game Parameters:</a> %s<p>"%clean_parameters(nba.headers,owners)
    ret += "<a href=player_query>Player Parameters:</a> %s<p>"%clean_parameters(nba.players.headers,owners)

    return ret

def remove_Qi(s):
    parts = s.split(',')
    parts = filter(lambda x:x[0]!='Q' and x[1] not in '1234',parts)
    print "filtered to",parts
    return ','.join(parts)

def about(**kwargs):
    html = ''
    show_owners = kwargs.get('read owners',DEFAULT_OWNERS)
    if kwargs.get("show_parameters",1):
        kwargs['filter_show_parameters'] = lambda x: not x.startswith('Box.Q')
        html += '<HR>' +  S2.query.parameters(nba,kwargs.get('read_owners',DEFAULT_OWNERS),**kwargs)
    if kwargs.get("show_howto",1): html += '<HR>' + howto()
    return html

def query(**kwargs):
    #reload(NBA.formats); print "reloaded NBA.query reloading formats"
    if kwargs.get("_qt") == 'player':
        db = nba.player_dts['player']
        singleton = NBA.player_formats.Query_Summary
        group = NBA.player_formats.Query_Records
    else:
        db = nba
        singleton = NBA.formats.Query_Summary
        group = NBA.formats.Query_Records

    if kwargs.get("table_input") or kwargs.get("query_table_submit"):
        kwargs["input_form"] = tables.tables_get(**kwargs)
    if kwargs.get("query_table_submit"):
        kwargs["sdql"] = tables.sdql_from_tables_post(**kwargs)
    #print "nba.q.sdql:",kwargs.get('sdql','')
    #client = kwargs.get("client","sdb")  ##pick up custom outputs and defaults for clients.
    kwargs['read_owners'] = DEFAULT_OWNERS + [kwargs.get('client','guest')] + kwargs.get('nba parameter groups',[])
    kwargs.setdefault('about',about(**kwargs))
    return S2.query.query(sdb=db,
                    Query_Records=group,
                    Query_Summary=singleton,
                    **kwargs)


# return a json ready or html ready dict
def matchup_d(**kwargs):
    dout = {}
    date =  int(kwargs.get('date',PyQL.py_tools.today()))
    if date<20131029: date = 20131029
    dout['date'] = date
    try:
        mups = nba.sdb_query("(team,o:team) @ _i%%2=0 and date=%s"%date)[0][0].data
    except:
        mups = []
    dout['result'] = mups
    return dout

def matchups_html(**kwargs):
    context = kwargs.get('context','html')
    link_page = kwargs.get('link_page','matchups')
    query_page = kwargs.get('query_page','query')
    ret = ''
    mud = matchup_d(**kwargs)
    date = PyQL.py_tools.Date8( mud['date'])
    left_arrow = "<a href=%s?date=%s&sport=nba> <-- </a>"%(link_page,date-1,)
    right_arrow = "<a href=%s?date=%s&sport=nba> --> </a>"%(link_page,date+1,)
    ret += left_arrow + PyQL.py_tools.nice_date(date) + right_arrow
    ret += "<p>"
    for home,away in mud['result']:
        ret += "<a href=%s?sport=nba&sdql=%s>%s at %s</a><BR>\n"%(query_page,
                           urllib.quote("team=%s and o:team=%s"%(home,away)),away,home)
    return S2.query.wrap_return(ret,context=context)
########## tests and demos
def test_query(nba):
    sdql =  "points>40"
    print "sdql:",sdql
    res = query(sdql=sdql,**{'output':'summary','_qt':'player'})
    print "res:",res

def test_table(nba):
    kw = {'query_table_submit': 'S D Q L !','table':'SU','sdql':'HD and season=2013'}
    res = query(**kw)
    print "res:",res



if __name__ == "__main__":
    import sys
    from NBA.loader import nba
    #test_query(nba)
    #test_table(nba)

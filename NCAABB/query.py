# TODO:
#  each client needs a their own default query, default fields, templates and outputs
#  specify all these in args? build a client dict? make a method for each (ks_query ....) ???
#  this is half baked

from cgi import escape
from urllib import quote
import os
import NCAABB.update as update
from NCAABB.ncaabb_dt import AmbiguousPlayerError
from NCAABB.loader import ncaabb
import NCAABB.howto_query
import NCAABB.formats
import NCAABB.player_formats
import PyQL.outputs
from S2.common_methods import clean_parameters
import S2.query
import PyQL.py_tools
import urllib
import NCAABB.Sheets.white_label

def sheet(sheet_owner,sheet,**kwargs):
    if sheet_owner.lower() == 'wl':
        reload(NCAABB.Sheets.white_label)
        return NCAABB.Sheets.white_label.handler(ncaabb,sheet,**kwargs)
    else:
        return "Your requested sheet %s %s was not found"%(sheet_owner,sheet)



DEFAULT_OWNERS = ["","SDB","Box","Schedule"]

def howto():
    ret = NCAABB.howto_query.html
    return ret


def about(**kwargs):
    html = ''
    if kwargs.get("show_parameters",1): html += '<HR>' +  S2.query.parameters(ncaabb,kwargs.get('read_owners',DEFAULT_OWNERS),**kwargs)
    if kwargs.get("show_howto",1): html += '<HR>' + howto()
    return html

def query(**kwargs):
    #client = kwargs.get("client","sdb")  ##pick up custom outputs and defaults for clients.
    if kwargs.get("_qt") == 'player':
        db = ncaabb.player_dts['player']
        singleton = NCAABB.player_formats.Query_Summary
        group = NCAABB.player_formats.Query_Records
    else:
        db = ncaabb
        singleton = NCAABB.formats.Query_Summary
        group = NCAABB.formats.Query_Records
    kwargs['read_owners'] = kwargs.get('read_owners',[]) + DEFAULT_OWNERS
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
        mups = ncaabb.sdb_query("(team,o:team) @ _i%%2=0 and date=%s"%date)[0][0].data
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
    left_arrow = "<a href=%s?date=%s&sport=ncaabb> <-- </a>"%(link_page,date-1,)
    right_arrow = "<a href=%s?date=%s&sport=ncaabb> --> </a>"%(link_page,date+1,)
    ret += left_arrow + PyQL.py_tools.nice_date(date) + right_arrow
    ret += "<p>"
    for home,away in mud['result']:
        ret += "<a href=%s?sport=ncaabb&sdql=%s>%s at %s</a><BR>\n"%(query_page,
                           urllib.quote("team=%s and o:team=%s"%(home,away)),away,home)
    return S2.query.wrap_return(ret,context=context)




########## tests and demos
def test_query(ncaabb):
    sdql =  "(team,date)@date=today"
    print "sdql:",sdql
    res = query(sdql=sdql,output='python',context='raw',ro=1)
    print "res:",res

if __name__ == "__main__":
    import sys
    from NCAABB.loader import ncaabb
    test_query(ncaabb)


from cgi import escape
import urllib
import os
from WNBA.loader import wnba
import WNBA.howto_query
import WNBA.formats, WNBA.player_formats
import PyQL.outputs,PyQL.py_tools
from S2.common_methods import clean_parameters
import S2.query

# methods accessed via S2.tornado_sport need to be defined here
import WNBA.update as update
#import WNBA.tables as tables
#import WNBA.Sheets.ed # dispatch by client
#import WNBA.query_matrix as query_matrix

def sheet(sheet_owner,sheet,**kwargs):
    #print "wnba.query.sheet owner:",sheet_owner, sheet
    #print "reloadinng WNBA.Sheets.ed"
    #reload(WNBA.Sheets.ed)

    if sheet_owner.lower() == 'ed':
        return WNBA.Sheets.ed.handler(wnba,sheet,**kwargs)
    else:
        return "Your requested sheet %s %s was not found"%(sheet_owner,sheet)

DEFAULT_OWNERS = ["","SDB","Box","Schedule"]
#DEFAULT_OWNERS = ["","Schedule"]

def howto():
    ret = WNBA.howto_query.html
    return ret

def about(**kwargs):
    html = ''
    show_owners = DEFAULT_OWNERS
    read_owners = kwargs.get('read owners')
    if read_owners:
        if type(read_owners) is str: read_owners = [read_owners]
        show_owners += read_owners
    if kwargs.get("show_parameters",1): html += '<HR>' +  S2.query.parameters(wnba,read_owners,**kwargs) #parameters(show_owners)
    if kwargs.get("show_howto",1): html += '<HR>' + howto()
    return html

def query(**kwargs):
    #reload(WNBA.formats); print "reloaded WNBA.query"
    #reload(S2.query); print "reloaded eloadinng S2.query"
    if kwargs.get("_qt") == 'player':
        db = wnba.player_dts['player']
        singleton = WNBA.player_formats.Query_Summary
        group = WNBA.player_formats.Query_Records
    else:
        db = wnba
        singleton = WNBA.formats.Query_Summary
        group = WNBA.formats.Query_Records

    if kwargs.get("table_input") or kwargs.get("query_table_submit"):
        kwargs["input_form"] = tables.tables_get(**kwargs)
    if kwargs.get("query_table_submit"):
        kwargs["sdql"] = tables.sdql_from_tables_post(**kwargs)
    #print "wnba.q.sdql:",kwargs.get('sdql','')
    #client = kwargs.get("client","sdb")  ##pick up custom outputs and defaults for clients.
    kwargs['read_owners'] = DEFAULT_OWNERS + kwargs.get('read_owners',[])
    kwargs.setdefault('about',about(**kwargs))
    print "readpwners:",kwargs['read_owners']
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
        mups = wnba.sdb_query("(team,o:team) @ _i%%2=0 and date=%s"%date)[0][0].data
    except:
        mups = []
    dout['result'] = mups
    return dout

def matchups_html(**kwargs):
    context = kwargs.get('context','html')
    link_page = kwargs.get('link_page','matchups')
    ret = ''
    mud = matchup_d(**kwargs)
    date = PyQL.py_tools.Date8( mud['date'])
    left_arrow = "<a href=%s?date=%s> <-- </a>"%(link_page,date-1,)
    right_arrow = "<a href=%s?date=%s> --> </a>"%(link_page,date+1,)
    ret += left_arrow + PyQL.py_tools.nice_date(date) + right_arrow
    ret += "<p>"
    for home,away in mud['result']:
        ret += "<a href=query?sdql=%s>%s at %s</a><BR>\n"%(
                           urllib.quote("team=%s and o:team=%s"%(home,away)),away,home)
    return S2.query.wrap_return(ret,context=context)
########## tests and demos
def test_query(wnba):
    sdql =  "points>40"
    print "sdql:",sdql
    res = query(sdql=sdql,**{'output':'summary','_qt':'player'})
    print "res:",res

def test_table(wnba):
    kw = {'query_table_submit': 'S D Q L !','table':'SU','sdql':'HD and season=2013'}
    res = query(**kw)
    print "res:",res



if __name__ == "__main__":
    import sys
    from WNBA.loader import wnba
    #test_query(wnba)
    #test_table(wnba)

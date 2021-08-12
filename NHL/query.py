from NHL.loader import nhl
import NHL.update as update
import NHL.howto_query
import NHL.formats
import NHL.player_formats
import NHL.Sheets.white_label
import PyQL.py_tools
import urllib
from S2.common_methods import clean_parameters
import S2.query


def sheet(sheet_owner,sheet,**kwargs):
    if sheet_owner.lower() == 'wl':
        reload(NHL.Sheets.white_label)
        return NHL.Sheets.white_label.handler(nhl,sheet,**kwargs)
    else:
        return "Your requested sheet %s %s was not found"%(sheet_owner,sheet)


DEFAULT_OWNERS = ["","SDB","Box","Schedule"]

def howto():
    ret = NHL.howto_query.html
    return ret

def about(**kwargs):
    html = ''
    if kwargs.get("show_parameters",1): html += '<HR>' + S2.query.parameters(nhl,kwargs.get('read_owners',DEFAULT_OWNERS),**kwargs)
    if kwargs.get("show_howto",1): html += '<HR>' + howto()
    return html

def query(**kwargs):
    #client = kwargs.get("client","sdb")  ##pick up custom outputs and defaults for clients.
    #print "reload S2.query"
    #reload(S2.query)
    qt = kwargs.get('_qt','games')
    if qt != 'games':
        db = nhl.player_dts[qt]
        #kwargs['form_action'] = '%s_query'%qt # move to tornado_sport
        singleton = NHL.player_formats.Query_Summary[qt]
        group = NHL.player_formats.Query_Records[qt]
    else:
        db = nhl
        singleton = NHL.formats.Query_Summary
        group = NHL.formats.Query_Records

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
        mups = nhl.sdb_query("(team,o:team) @ _i%%2=0 and date=%s"%date)[0][0].data
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
    left_arrow = "<a href=%s?date=%s&sport=nhl> <-- </a>"%(link_page,date-1,)
    right_arrow = "<a href=%s?date=%s&sport=nhl> --> </a>"%(link_page,date+1,)
    ret += left_arrow + PyQL.py_tools.nice_date(date) + right_arrow
    ret += "<p>"
    for home,away in mud['result']:
        ret += "<a href=%s?sport=nhl&sdql=%s>%s at %s</a><BR>\n"%(query_page,
                           urllib.quote("team=%s and o:team=%s"%(home,away)),away,home)
    return S2.query.wrap_return(ret,context=context)

########## tests and demos
def test_query(nhl):
    sdql =  "goals=3"
    print "sdql:",sdql
    res = query(sdql=sdql,**{'_qt':'skater'})
    print "res:",res

if __name__ == "__main__":
    import sys
    sys.path[:0] = ["/home/jameyer/S2/NHL/Source"]
    test_query(nhl)

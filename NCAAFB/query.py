
import sys,string,re,urllib

import PyQL.outputs
import S2.query
import S2.common_methods
from NCAAFB.loader import ncaafb
from NCAAFB.ncaafb_dt import CURRENT_SEASON
import NCAAFB.formats
import NCAAFB.howto_query
import NCAAFB.date_tools
import NCAAFB.Sheets.california
import NCAAFB.Sheets.pregame
import NCAAFB.Sheets.wagertalk
import NCAAFB.Sheets.white_label
#import NCAAFB.Sheets.jallen
import NCAAFB.player_formats

# methods accessed via S2.tornado_sport need to be defined here
import NCAAFB.update as update
#import NCAAFB.tables as tables
#import NCAAFB.query_matrix as query_matrix

DEFAULT_OWNERS = ["","SDB","Schedule","Box"]
#DEFAULT_OWNERS = ["","SDB","Schedule"]

def sheet(sheet_owner,sheet,**kwargs):
    #print "ncaafb.query.sheet owner:",sheet_owner, sheet
    #print "reloadinng NCAAFB.Sheets.pregame"
    reload(NCAAFB.Sheets.pregame);    reload(NCAAFB.Sheets.california);
    #if sheet_owner.lower() == 'ed':
    #    return NCAAFB.Sheets.ed.handler(ncaafb,sheet,**kwargs)
    if sheet_owner.lower() == 'pregame':
        return NCAAFB.Sheets.pregame.handler(ncaafb,sheet,**kwargs)
    if sheet_owner.lower() == 'california':
        return NCAAFB.Sheets.california.handler(ncaafb,sheet,**kwargs)
    if sheet_owner.lower() == 'wagertalk':
        reload(NCAAFB.Sheets.wagertalk)
        return NCAAFB.Sheets.wagertalk.handler(ncaafb,sheet,**kwargs)
    if sheet_owner.lower() == 'jallen':
        return NCAAFB.Sheets.jallen.handler(ncaafb,sheet,**kwargs)
    if sheet_owner.lower() == 'wl':
        reload(NCAAFB.Sheets.white_label)
        return NCAAFB.Sheets.white_label.handler(ncaafb,sheet,**kwargs)

    else:
        try:
            exec("import NCAAFB.Sheets.%s)"%(sheet_owner,))
            exec("reload(NCAAFB.Sheets.%s)"%(sheet_owner,))
            return eval("NCAAFB.Sheets.%s.handler(ncaafb,sheet,**kwargs)"%(sheet_owner,))
        except:
            print "live import failed"
    return "Your requested sheet %s %s was not found"%(sheet_owner,sheet)

def howto(**kwargs):
    ret = NCAAFB.howto_query.html(**kwargs)
    return ret

def about(**kwargs):
    html = ''
    if kwargs.get("show_parameters",1): html += '<HR>' + S2.query.parameters(ncaafb,kwargs.get('read_owners',DEFAULT_OWNERS),**kwargs)
    if kwargs.get("show_howto",1): html += '<HR>' + howto(**kwargs)
    return html

def query(**kwargs):
    #print "reloading turn off for prod."
    #reload(NCAAFB.howto_query)
    #print "reload formats"
    #reload(NCAAFB.formats)
    #print "NCAAFB.query.kwargs:",kwargs
    qt = kwargs.get('_qt','games')
    if qt != 'games':
        db = ncaafb.player_dts[qt]
        #kwargs['form_action'] = '%s_query'%qt # move to tornado_sport
        singleton = NCAAFB.player_formats.Query_Summary.get(qt)
        group = NCAAFB.player_formats.Query_Records.get(qt)
    else:
        db = ncaafb
        singleton = kwargs.get('format_singleton',NCAAFB.formats.Query_Summary)
        group = kwargs.get('format_group',NCAAFB.formats.Query_Records)

    if kwargs.get("table_input") or kwargs.get("query_table_submit"):
        kwargs["input_form"] = tables.tables_get(**kwargs)
    if kwargs.get("query_table_submit"):
        kwargs["sdql"] = tables.sdql_from_tables_post(**kwargs)
    kwargs['read_owners'] = kwargs.get('read_owners',[]) + DEFAULT_OWNERS
    kwargs.setdefault('about',about(**kwargs))
    #print "headers",ncaafb.headers
    #print "readownder",kwargs['read_owners']
    return S2.query.query(sdb=db,
                          Query_Records=group,
                          Query_Summary=singleton,
                          **kwargs)

# return a json ready or html ready dict
def matchup_d(**kwargs):
    dout = {}
    if kwargs.get('date'):
        date = int(kwargs['date'])
        dout['date'] = date
        where = 'date=%s'%kwargs['date']
    else:
        week = kwargs.get('week')
        season = kwargs.get('season',CURRENT_SEASON)
        if not week:
            season, week, day = NCAAFB.date_tools.find_season_week_day_from_date()
        week = int(week)
        if week > 23: week = 1
        where =  "week=%s and season=%s"%(week,season)
        dout['week'] = week; dout['season'] = season
    #print "where:",where
    try:
        mups = ncaafb.sdb_query("(team,o:team) @ _i%%2=0 and %s"%where )[0][0].data
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
    if mud.get('date'):
        date = PyQL.py_tools.Date8( mud['date'])
        left_arrow = "<a href=%s?date=%s&sport=ncaafb> <-- </a>"%(link_page,date-1,)
        right_arrow = "<a href=%s?date=%s&sport=ncaafb> --> </a>"%(link_page,date+1,)
        ret += left_arrow + PyQL.py_tools.nice_date(date) + right_arrow
    else:
        week = mud['week']
        season = mud['season']
        if week > 1:
            left_arrow = "<a href=%s?week=%s&season=%s&sport=ncaafb> <-- </a>"%(link_page,
                week-1,season)
        else: left_arrow = ''
        if week < 22:
            right_arrow = "<a href=%s?week=%s&season=%s&sport=ncaafb> --> </a>"%(link_page,
                week+1,season)
        else: right_arrow = ''
        ret += left_arrow + " Week %s, %s "%(week,season) + right_arrow
    ret += "<p>"
    for home,away in mud['result']:
        ret += "<a href=%s?sdql=%s&sport=ncaafb>%s at %s</a><BR>\n"%(query_page,
                           urllib.quote("team=%s and o:team=%s"%(home,away)),away,home)
    return S2.query.wrap_return(ret,context=context)
############# tests and demos ##############

def test_mups():
    print matchups_html(**{'date':'20120909','output':'html'})
    print matchup_d(**{'date':'20120909','output':'html'})

def test_query():
    sdql = "team=Bears and season>=2010 and FD+1>10"
    sdql = "team and tA(p:PY)+100>200"
    print query(sdql=sdql,output='summary',short_cuts=['KS'],sport='ncaafb')

if __name__ == "__main__":
    #sdql = "points,o:points @ team='Bears'  and  season=2004"

    for arg in sys.argv[1:]:
        if '=' not in arg:
            arg = arg+"=1"
        var, val = string.split(arg,'=',1)
        try:              #first ask: Is this in my name space?
            eval(var)
        except:
            print "Can't set", var
            sys.exit(-1)
        try:
            exec(arg)  #numbers
        except:
            exec('%s="%s"' % tuple(string.split(arg,'=',1))) #strings
    #open("/tmp/ncaafb_query.html",'w').write(query(text=text,output="summary") )
    test_query()
    #test_mups()

import sys,string,re,urllib

import PyQL.outputs
import S2.query
import S2.common_methods
from NFL.loader import nfl
from NFL.nfl_dt import CURRENT_SEASON
import NFL.formats
import NFL.howto_query
import NFL.date_tools
import NFL.Sheets.ed, NFL.Sheets.deyong, NFL.Sheets.dz, NFL.Sheets.ks_weekly, NFL.Sheets.wagertalk
import NFL.Sheets.white_label
import NFL.player_formats

# methods accessed via S2.tornado_sport need to be defined here
import NFL.update as update
import NFL.tables as tables

import NFL.query_matrix as query_matrix

DEFAULT_OWNERS = ["","SDB","Box","Schedule"]
FILTER_PAT = re.compile("(ats |ou |line|total|dps|dpa)") # want to hide these ??

def sheet(sheet_owner,sheet,**kwargs):
    #print "nfl.query.sheet owner:",sheet_owner, sheet

    if sheet_owner.lower() == 'ed':
        return NFL.Sheets.ed.handler(nfl,sheet,**kwargs)
    if sheet_owner.lower() == 'deyong':
        return NFL.Sheets.deyong.handler(nfl,sheet,**kwargs)
    if sheet_owner.lower() == 'dz':
        return NFL.Sheets.dz.handler(nfl,sheet,**kwargs)
    if sheet_owner.lower() == 'ks_weekly':
        return NFL.Sheets.ks_weekly.handler(nfl,sheet,**kwargs)
    if sheet_owner.lower() == 'wagertalk':
        #print "reloading wager talk"
        #reload(NFL.Sheets.wagertalk)
        return NFL.Sheets.wagertalk.handler(nfl,sheet,**kwargs)
    if sheet_owner.lower() == 'wl':
        print "reloadinng NFL.Sheets"
        reload(NFL.Sheets.white_label)
        return NFL.Sheets.white_label.handler(nfl,sheet,**kwargs)

    else:
        return "Your requested sheet %s %s was not found"%(sheet_owner,sheet)

def howto(**kwargs):
    ret = NFL.howto_query.html(**kwargs)
    return ret

def about(**kwargs):
    html = ''
    if kwargs.get("show_parameters",1): html += '<HR>' + S2.query.parameters(nfl,kwargs.get('read_owners',DEFAULT_OWNERS),**kwargs)
    if kwargs.get("show_howto",1): html += '<HR>' + howto(**kwargs)
    return html

def query(**kwargs):
    #print "reloading turn off for prod."
    #reload(S2.query)
    #reload(tables)
    #print "NFL.query.kwargs.sdql:",kwargs.get('sdql')
    qt = kwargs.get('_qt','games')
    if qt != 'games':
        db = nfl.player_dts[qt]
        #kwargs['form_action'] = '%s_query'%qt # move to tornado_sport
        singleton = NFL.player_formats.Query_Summary.get(qt)
        group = NFL.player_formats.Query_Records.get(qt)
    else:
        db = nfl
        singleton = NFL.formats.Query_Summary
        group = NFL.formats.Query_Records

    if kwargs.get("table_input") or kwargs.get("query_table_submit"):
        kwargs["input_form"] = tables.tables_get(**kwargs)
    if kwargs.get("query_table_submit"):
        kwargs["sdql"] = tables.sdql_from_tables_post(**kwargs)
        #print "table sdql:",kwargs["sdql"]
    kwargs['read_owners'] = kwargs.get('read_owners',[]) + DEFAULT_OWNERS
    kwargs.setdefault('about',about(**kwargs))
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
            season, week, day = NFL.date_tools.find_season_week_day_from_date()
        week = int(week)
        if week > 23 or week<1: week = 1
        where =  "week=%s and season=%s"%(week,season)
        dout['week'] = week; dout['season'] = season
    #print "where:",where
    try:
        mups = nfl.sdb_query("(team,o:team) @ _i%%2=0 and %s"%where )[0][0].data
    except:
        mups = []
    dout['result'] = mups
    return dout

def matchups_html(**kwargs):
    context = kwargs.get('context','html')
    link_page = kwargs.get('link_page','matchups')
    query_page =kwargs.get('query_page','query')
    ret = ''
    mud = matchup_d(**kwargs)
    sid_poop = kwargs.get('sid','')
    if sid_poop:
        sid_poop = '&sid=%s'%sid_poop
    if mud.get('date'):
        date = PyQL.py_tools.Date8( mud['date'])
        left_arrow = "<a href=%s?sport=nfl&date=%s%s> <-- </a>"%(link_page,date-1,sid_poop)
        right_arrow = "<a href=%s?sport=nfl&date=%s%s> --> </a>"%(link_page,date+1,sid_poop)
        ret += left_arrow + PyQL.py_tools.nice_date(date) + right_arrow
    else:
        week = mud['week']
        season = mud['season']
        if week > 1:
            left_arrow = "<a href=%s?sport=nfl&week=%s&season=%s%s> <-- </a>"%(link_page,
                week-1,season,sid_poop)
        else: left_arrow = ''
        if week < 22:
            right_arrow = "<a href=%s?sport=nfl&week=%s&season=%s%s> --> </a>"%(link_page,
                week+1,season,sid_poop)
        else: right_arrow = ''
        ret += left_arrow + " Week %s, %s "%(week,season) + right_arrow
    ret += "<p>"
    for home,away in mud['result']:
        ret += "<a href=%s?sport=nfl&sdql=%s%s&week=%s>%s at %s</a><BR>\n"%(query_page,
                             urllib.quote("team=%s and o:team=%s"%(home,away)),sid_poop,week,away,home)
    return S2.query.wrap_return(ret,context=context)
############# tests and demos ##############

def test_mups():
    print matchups_html(**{'date':'20120909','output':'html','clientsclient':'foo'})
    #print matchup_d(**{'date':'20120909','output':'html'})

def test_query():
    sdql = "int(points),round(p:points)@team=Bears"
    print query(sdql=sdql,output='Xmatplotlib.scatter',short_cuts=['KS'],sport='nfl',show_metacode=1)


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
    #open("/tmp/nfl_query.html",'w').write(query(text=text,output="summary") )
    test_query()
    #test_mups()
    #time_nfl()

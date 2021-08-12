import PyQL.outputs
import urllib,cgi
from S2.common_methods import key_to_query_link

STR_NONE = "--"
def safe_d_d_format(sigfig=0):
    return "lambda x:(None in x and '%s') or '%%0.%df-%%0.%df'%%x"%(STR_NONE,sigfig,sigfig)

# these 'as-defined headers go straight through  
def game_fields(**kwargs):
    # summary output looks for `Date` header and so must be first
    return  ("date as Date," +
                  "site as Site," +
                  "team as Team,  " +
                  "o:team as Opp,"+
                  "Column((points,o:points),format='''%s''') as Score,"%safe_d_d_format() + # `Score` is used below - careful with changes!
                  "Column((date-p:date-1,date-op:date-1),format='''lambda x:('-'*(x[0] is None or 100<x[0]) or str(x[0]))+'&'+('-'*(x[1] is None or 100<x[1]) or str(x[1]))''') as Rest,"
                  # "Column((date-p:date,date-op:date)) as Rest,"
                  "Column((1.*field goals made/field goals attempted,1.*o:field goals made/o:field goals attempted),format='''%s''') as FG%%,"%safe_d_d_format() +
                  "line as Line," +
                  "total as Total," +
                  "points-o:points as SUm," +
                  "points+line-o:points as ATSm," +
                  "points+o:points-total as OUm," +             
                  "Column(points-(total-line)/2.,format='%0.1f') as DPS,"+
                   "Column(o:points-(total+line)/2.,format='%0.1f') as DPA,"
                  "(points>o:points)*'W' or 'L' as SUr,"
                   "(points+line>o:points)*'W' or (points+line<o:points)*'L'or 'P' as ATSr,"
                  "(points+o:points>total)*'O' or (points+o:points<total)*'U' or 'P' as OUr,"             
                  "(len(quarter scores) - 4) or '' as OT") 


def stat_fields(t='t',**kwargs):
     return   (
             "Average(%s:quarter scores[0],format='%%0.1f') as __%s_q1__,"%(t,t) +
             "Average(%s:quarter scores[1],format='%%0.1f') as __%s_q2__,"%(t,t) +
             "Average(%s:quarter scores[2],format='%%0.1f') as __%s_q3__,"%(t,t) +
             "Average(%s:quarter scores[3],format='%%0.1f') as __%s_q4__,"%(t,t) +
             "Average(%s:points,format='%%0.1f') as __%s_total_points__,"%(t,t) +
             "Average(%s:field goals made,format='%%0.1f') as __%s_fgm__,"%(t,t) +
             "Average(%s:field goals attempted,format='%%0.1f') as __%s_fga__,"%(t,t) +
             "Average(%s:three pointers made,format='%%0.1f') as __%s_tpm__,"%(t,t) +
             "Average(%s:three pointers attempted,format='%%0.1f') as __%s_tpa__,"%(t,t) +
             "Average(%s:free throws made,format='%%0.1f') as __%s_ftm__,"%(t,t) +
             "Average(%s:free throws attempted,format='%%0.1f') as __%s_fta__,"%(t,t) +
             "Average(%s:blocks,format='%%0.1f') as __%s_blocks__,"%(t,t) +
             "Average(%s:offensive rebounds,format='%%0.1f') as __%s_orebounds__,"%(t,t) +
             "Average(%s:rebounds,format='%%0.1f') as __%s_rebounds__,"%(t,t) +
             "Average(%s:fouls,format='%%0.1f') as __%s_fouls__,"%(t,t) +
             "Average(%s:assists,format='%%0.1f') as __%s_assists__,"%(t,t) +
             "Average(%s:turnovers,format='%%0.1f') as __%s_turnovers__"%(t,t) 
         )                          
    
def average_line_fields(**kwargs):
    ou = kwargs.get("ou",1)
    ats = kwargs.get("ats",0)
    select = ''
    if ats:
        select += "Average(t:line,format='%0.1f') as __t_average_line__,"
    if ou:
        select += "Average(t:total,format='%0.1f') as __t_average_total__,"
    if select and select[-1] == ',': select = select[:-1]
    return select

# the as-headers here are for lookup in the output methods below
def record_fields(**kwargs):
    ngames = kwargs.get("ngames",1)
    ats = kwargs.get("ats",1)
    ou = kwargs.get("ou",1)
    su = kwargs.get("su",1)
    select = ''
    if ngames:
        select = "Count(points) as __N__,"
    if su:
        select += "Record_WLPM(points-o:points,format='''lambda x:'%s-%s (%0.2f, %0.1f)'%(x[0],x[1],x[3],100.*x[0]/((x[0]+x[1]) or 1))''') as '__su__',"
    if ats:    
        select += "Record_WLPM(points+line-o:points,format='''lambda x:'%s-%s-%s (%0.2f, %0.1f)'%(x[0],x[1],x[2],x[3],100.*x[0]/((x[0]+x[1]) or 1))''') as '__ats__',"
    if ou:    
        select += "Record_WLPM(points+o:points-total,format='''lambda x:'%s-%s-%s (%0.2f, %0.1f)'%(x[0],x[1],x[2],x[3],100.*x[0]/((x[0]+x[1]) or 1))''') as '__ou__',"

    if select[-1] == ',': select = select[:-1]
    return select 

def summary_fields(**kwargs):
    # game_fields needs to be last
    su = kwargs.get("su",1)
    ats = kwargs.get("ats",1)
    ou = kwargs.get("ou",1)
    ret = record_fields(su=su,ats=ats,ou=ou) + ','
    ret += average_line_fields(su=su,ats=ats,ou=ou) +','
    ret += stat_fields('t') + ','
    ret += stat_fields('o') + ','
    ret += game_fields() # this need to be last since headers from Date on are taken as-is
    return ret

def summary_records_table(res,**kwargs):
    su = kwargs.get("su",1)
    ou = kwargs.get("ou",1)
    ats = kwargs.get("ats",1)
    average_line = kwargs.get("average_line",1)    
    ret = []
    ret.append("<table>")
    if su:
        ret.append("<tr><th>SU:</th>")
        ret.append("<td>%s</td>"%(res.value_from_header("__su__"),))
        if average_line: ret.append("<td></td>")
        ret.append("</tr>")        
    if ats:
        ret.append("<tr><th>ATS:</th>")
        ret.append("<td>%s</td>"%(res.value_from_header("__ats__"),))
        if average_line:
            ret.append("<td>&nbsp;&nbsp;avg line: %s </td>"%(
                res.value_from_header("__t_average_line__",''),))
        ret.append("</tr>")                       
    if ou:
        
        ret.append("<tr><th>OU:</th>")
        ret.append("<td>%s</td>"%(res.value_from_header("__ou__"),))
        if average_line:
            ret.append("<td>&nbsp;&nbsp;avg total: %s</td>"%(
                 res.value_from_header("__t_average_total__",''))    )
        ret.append("</tr>")


    ret.append("</table>")
    return '\n'.join(ret)

def values_and_percent(v1,v2):
    return "%s-%s (%0.1f%%)"%(v1,v2,100.*v1.value()/v2.value())

def summary_stats_table(res,**kwargs):

    ret = []
    # NBA handles quarter scores in a separate table
    ret.append("<table>")
    ret.append("<tr><td align=center></td><th>Q1</th><th>Q2</th><th>Q3</th><th>Q4</th><th>Final</th></tr>")
    for side in 'to':
        ret.append("<tr><th>%s:</th>"%({'t':'Team','o':'Opp'}[side]))
        for q in range(4):
            ret.append("<td align=center>%s</td>"%(res.value_from_header('__%s_q%d__'%(side,q+1)),))
        ret.append("<td align=center>%s</td>"%(res.value_from_header('__%s_total_points__'%(side,)),))
    ret.append("</table>")
    ret.append("<table>")
    ret.append("<tr><td align=center></td><th>Field Goals</th><th>Threes</th><th>Free Throws</th>")
    ret.append("<th>Blocks</th><th>O Rbnds</th><th>Rbnds</th><th>Fouls</th><th>Assts</th><th>TrnOvrs</th></tr>")
    for side in 'to':
        ret.append("<tr><th>%s:</th>"%({'t':'Team','o':'Opp'}[side]))
        ret.append("<td align=center>%s</td>"%(values_and_percent(
                       res.value_from_header('__%s_fgm__'%side),res.value_from_header('__%s_fga__'%side))))
        ret.append("<td align=center>%s</td>"%(values_and_percent(
                       res.value_from_header('__%s_tpm__'%side),res.value_from_header('__%s_tpa__'%side))))
        ret.append("<td align=center>%s</td>"%(values_and_percent(
                       res.value_from_header('__%s_ftm__'%side),res.value_from_header('__%s_fta__'%side))))
        ret.append("<td align=center>%s</td>"%(res.value_from_header('__%s_blocks__'%side),))
        ret.append("<td align=center>%s</td>"%(res.value_from_header('__%s_orebounds__'%side),))
        ret.append("<td align=center>%s</td>"%(res.value_from_header('__%s_rebounds__'%side),))
        ret.append("<td align=center>%s</td>"%(res.value_from_header('__%s_fouls__'%side),))
        ret.append("<td align=center>%s</td>"%(res.value_from_header('__%s_assists__'%side),))
        ret.append("<td align=center>%s</td>"%(res.value_from_header('__%s_turnovers__'%side),))
        ret.append("</tr>")    

    ret.append("</tr></table>")
    return '\n'.join(ret)

def summary_games_table(res,**kwargs):
    show_games = kwargs.get("n_games",20)
    show_unplayed = kwargs.get("n_unplayed",4)
    # need to find the range of rows to display
    score_offset = res.offset_from_header("Score")  
    len_res = len(res[score_offset].data)
    #len_played = len(filter(lambda x:x[0] is not None,res[score_offset].data)) XXX picks up missing past games
    scores = res[score_offset].data
    #scores.reverse()
    i = 0
    for i in range(len_res-1,0,-1):
        if scores[i][0] is not None: break
    len_played = i + 1
    #print "n_platyed:",len_played
    #print "n_res:",len_res
    stop = min(len_res, len_played + show_unplayed)
    start = max(0,stop-show_games)
    #print "stop, start:",stop,start
    ret = []
    ret.append("<table id='DT_Table'><thead><tr>")
    day_offset = res.offset_from_header("Date")
    game_headers = res.headers[day_offset:]
    for header in game_headers:
        ret.append("<th>%s</th>"%header)
    ret.append("</tr></thead>")        
    len_game_headers = len(game_headers)
    len_res = len(res[day_offset])
    #for g in range(len(res[day_offset])):
    for g in range(start,stop):
        ret.append("<tr>")
        for h in range(len_game_headers):
            val = res[day_offset+h][g]
            #print "val:",val,"%s"%(val,)
            if val is None or val == (None,None): str_val = STR_NONE  # XXX need eigen handling of None
            else: str_val = res[day_offset+h].format(val)
            ret.append("<td align=center>%s</td>"%str_val)
        ret.append("</tr>")
    ret.append("</tr>")
    ret.append("</table>")
    return "\n".join(ret)

def summary_html(res,**kwargs):
    query_title = kwargs.get("query_title",'')   
    ret = []
    ret.append("<!--Start Summary-->")
    ret.append("<TABLE border=0 bgcolor=FFFFFF>")
    if query_title:
        ret.append("<!--Start Key Row--><TR bgcolor=DDDDDD><TH>%s</TH></TR><!--End Key Row-->"%query_title)
    ret.append("<!--Start Records Row--><TR><TD>")
    #print "building summary records"
    ret.append(summary_records_table(res,**kwargs))
    #print "built summary records"    
    ret.append("</TD></TR><!--End Records Row-->")

    ret.append("<!--Start Stats Row--><TR><TD>")               
    ret.append(summary_stats_table(res,**kwargs))
    ret.append("</TD></TR><!--End Stats Row-->")
    #print "building game table"
    ret.append("<!--Start Games Row--><TR><TD>")               
    ret.append(summary_games_table(res,**kwargs))
    ret.append("</TD></TR><!--End Games Row-->")
    #print "built"        
    ret.append("</TABLE>")
    return "\n".join(ret)


def records_html(res,**kwargs):
    su = kwargs.get("su",1)
    ngames = kwargs.get("ngames",1)        
    ats = kwargs.get("ats",1)
    ou = kwargs.get("ou",1)
    n_rows = kwargs.get("n_rows",100)    
    res = res.reduced(key_to_query_link)    
    ret = []
    ret.append("<TABLE border=0 bgcolor=FFFFFF><tr>")
    if ngames:
        Nr = res.value_from_header("__N__")    
        ret.append("<th valign=bottom># games</th>")
    if su:
        su_offset = res.offset_from_header("__su__")
        sur = res[su_offset].value()
        su_format = res[su_offset].format 
        ret.append("<th valign=bottom>SU<BR>W-L (marg, %win)</th>")
    if ats:
        ats_offset = res.offset_from_header("__ats__")
        atsr = res[ats_offset].value()
        ats_format = res[ats_offset].format 
        ret.append("<th valign=bottom>ATS<BR>W-L-P (marg, %win)</th>")
    if ou:
        ou_offset = res.offset_from_header("__ou__")
        our = res[ou_offset].value()
        ou_format = res[ou_offset].format 
        ret.append("<th valign=bottom>Over / Under<BR>W-L (marg, %win)</th>")
    ret.append("<th valign=bottom>%s</th>"%res.headers[-1])        
    ret.append("</tr>")
    for r in range(min(len(res[0]),n_rows)):
        ret.append("<tr>")
        if ngames:
            ret.append("<td align=center>%s</td>"%Nr[r])
        if su:
            ret.append("<td align=center>%s</td>"%su_format(sur[r]))            
        if ats:
            ret.append("<td align=center>%s</td>"%ats_format(atsr[r]))            
        if ou:
            ret.append("<td align=center>%s</td>"%ou_format(our[r]))
        ret.append("<td align=center>%s</td>"%res[-1][r])
            
        ret.append("</tr>")
    ret.append("</table>")
    return "\n".join(ret)


### tests and demos ####

def test_query(nba):
    print nba.query("(date,points,o:team)@team=Bulls and season=2009")

def test_game_fields(nba):
    res = nba.query("%s@team=Bulls and season=2010"%game_fields())[0]
    print res
    print summary_games_table(res)
    

def test_summary(nba):
    res = nba.nba_query("%s@team=Hawks and overtime>0"%summary_fields())
    #print res
    #return 
    html = ''
    for r in res:
            html += summary_html(r,query_name=' '.join(r.name[-1]),n_games=30,n_unplayed=20)
    open("/tmp/nba.html",'w').write(html)
    #print html

def test_records(nba):
    res = nba.nba_query("%s@team and site=home"%record_fields())
    #print res
    #return 
    html = records_html(res,query_name=' '.join(res.name[-1]))
    open("/tmp/nba.html",'w').write(html)
    print html


if __name__ == "__main__":
    import sys
    from NBA.nba_loader import nba
    #test_query(nba)
    #test_game_fields(nba)
    #test_summary(nba)
    test_records(nba)


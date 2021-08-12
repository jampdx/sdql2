import PyQL.outputs
import urllib,cgi
from S2.common_methods import key_to_query_link

STR_NONE = " "
safe_d_d_format = "lambda x:(None in x and '%s') or '%%d-%%d'%%x"%STR_NONE

# these 'as-defined headers go straight through  
def game_fields(**kwargs):
    # summary output looks for `Date` header and so must be first

    return ("self.nice_date(date,abbreviate_month=1,abbreviate_year=0) as 'Date'," + 
            "day[:3].upper() as 'Day',"+
            "game number as '#',"+                         
            "season as 'Season',"+
            "Column(team,format='%s') as 'Team',"+
            "Column(o:team,format='%s') as 'Opp',"+
            "Column({'home':'H','away':'A','neutral':'N'}.get(site,site)) as 'Site',"+
            "Column((points,o:points),format='''%s''') as 'Score',"%safe_d_d_format +
            "Column(rest,format=lambda r:'%s'*(r is None or 100<r) or str(r)) as 'Rest',"%STR_NONE+
            "line as 'Line',"+
            "total as 'Total',"+
            "margin as 'SUm',"+
            "ats margin as 'ATSm',"+
            "Column({0:'W',1:'L',2:'P'}[(0+points<o:points)+2*(0+points==o:points)],format='%s') as 'SUr',"+
            "Column({0:'W',1:'L',2:'P'}[(points+line<o:points)+2*(points+line==o:points)],format='%s') as 'ATSr',"+
            "Column({0:'O',1:'U',2:'P'}[(points+o:points<total)+2*(points+o:points==total)], format='%s') as 'OUr',"+
            "Column('%d'%(conference==o:conference)) as Conf,"+
            "Column(game type,format='%s') as 'Type',"+
            "Column(conference,format='%s') as 'Conf.',"+
            "overtime as OT")   
    

# the as-headers here are for lookup in the output methods below
def record_fields(**kwargs):
    ngames = kwargs.get("ngames",1)
    su = kwargs.get("su",1)
    ats = kwargs.get("ats",1)
    ou = kwargs.get("ou",1)
    select = ''
    if ngames:
        select = "Count(points) as __N__,"
    if su:
        select += "Record_WLPM(points-o:points,format='''lambda x:'%s-%s (%0.2f, %0.1f&#37;)'%(x[0],x[1],x[3],100.*x[0]/((x[0]+x[1]) or 1))''') as '__su__',"
    if ats:
        select += "Record_WLPM(points+line-o:points,format='''lambda x:'%s-%s-%s (%0.2f, %0.1f&#37;)'%(x[0],x[1],x[2],x[3],100.*x[0]/((x[0]+x[1]) or 1))''') as '__ats__',"
        select += "Average(t:line,format='%0.1f') as __t_average_line__,"
    if ou:    
        select += "Record_WLPM(points+o:points-total,format='''lambda x:'%s-%s-%s (%0.2f, %0.1f&#37;)'%(x[0],x[1],x[2],x[3],100.*x[0]/((x[0]+x[1]) or 1))''') as '__ou__',"
        select += "Average(t:total,format='%0.1f') as __t_average_total__,"
    if select[-1] == ',': select = select[:-1]
    return select 

def summary_fields(**kwargs):
    # game_fields needs to be last
    su = kwargs.get("su",1)
    ou = kwargs.get("ou",1)
    ret = record_fields(su=su,ou=ou)
    if ret: ret += ','
    ret += game_fields() # this need to be last since headers from Date on are taken as-is
    return ret

def summary_records_table(res,**kwargs):
    su = kwargs.get("su",1)
    ats = kwargs.get("ats",1)
    ou = kwargs.get("ou",1)
    average_line = kwargs.get("average_line",1)    
    ret = []
    ret.append("<table>")

    if su:
        ret.append("<tr><th>SU:</th>")
        ret.append("<td>%s</td>"%(res.value_from_header("__su__"),))
        #if average_line:
        #    ret.append("<td>&nbsp;&nbsp;avg line: %s </td>"%(
        #        res.value_from_header("__t_average_line__",''))    )
        ret.append("</tr>")
    
    if ats:
        ret.append("<tr><th>ATS:</th>")
        ret.append("<td>%s</td>"%(res.value_from_header("__ats__"),))
        if average_line:
            ret.append("<td>&nbsp;&nbsp;avg line: %s </td>"%(
                res.value_from_header("__t_average_line__",''))    )
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

def summary_games_table(res,**kwargs):
    show_games = kwargs.get("n_games",20)
    show_unplayed = kwargs.get("n_unplayed",4)
    # need to find the range of rows to display
    score_offset = res.offset_from_header("Score")  # if this were is class I could do this just once...
    len_res = len(res[score_offset].data)
    #len_played = len(filter(lambda x:x[0] is not None,res[score_offset].data)) XXX picks up missing past games
    scores = res[score_offset].data
    i = 0
    for i in range(len_res-1,0,-1):
        if scores[i][0] is not None: break
    len_played = i + 1
    stop = min(len_res, len_played + show_unplayed)
    start = max(0,stop-show_games)
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
            if h == score_offset: str_val = "<b>%s</b>"%str_val
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

    #ret.append("<!--Start Stats Row--><TR><TD>")               
    #ret.append(summary_stats_table(res,**kwargs))
    #ret.append("</TD></TR><!--End Stats Row-->")
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
    ou = kwargs.get("ou",1)
    n_rows = kwargs.get("n_rows",100)    
    res = res.reduced(key_to_query_link)    
    ret = []
    ret.append("<TABLE border=0 bgcolor=FFFFFF><tr>")
    if ngames:
        Nr = res.value_from_header("__N__")    
        ret.append("<th valign=bottom># games</th>")
    if su:
        sur = res.value_from_header("__su__")
    if ou:
        our = res.value_from_header("__ou__")
    ret.append("<th valign=bottom>%s</th>"%res.headers[-1])        
    ret.append("</tr>")
    for r in range(min(len(res[0]),n_rows)):
        ret.append("<tr>")
        if ngames:
            ret.append("<td align=center>%s</td>"%Nr[r])
        if su:
            sur_r = sur[r]
            ret.append("<td align=center>%s-%s (%0.1f, %0.1f)</td>"%(sur_r[0],sur_r[1],sur_r[3],sur_r[4]))
        if ou:
            ret.append("<td align=center>%s-%s-%s (%0.1f, %0.1f)</td>"%our[r])

        ret.append("<td align=center>%s</td>"%res[-1][r])
            
        ret.append("</tr>")
    ret.append("</table>")
    return "\n".join(ret)



### tests and demos ####

def test_query(ncaafb):
    print ncaafb.ncaafb_query("(date,points,team,o:team)@team=ALA and season=2009")

def test_game_fields(ncaafb):
    res = ncaafb.ncaafb_query("%s@team=ALA and season=2010"%game_fields())[0]
    print res
    #print summary_games_table(res)
    

def test_summary(ncaafb):
    res = ncaafb.ncaafb_query("%s@team=ALA"%summary_fields())
    print res
    #return 
    html = ''
    for r in res:
            html += summary_html(r,query_name=' '.join(r.name[-1]),n_games=30,n_unplayed=20)
    open("/tmp/ncaafb.html",'w').write(html)
    #print html

def test_records(ncaafb):
    res = ncaafb.ncaafb_query("%s@team=ALA"%record_fields())
    #print res
    #return 
    html = records_html(res,query_name=' '.join(res.name[-1]))
    open("/tmp/ncaafb.html",'w').write(html)
    print html



if __name__ == "__main__":
    import sys
    #from NCAAFB.ncaafb_loader import ncaafb
    ncaafb.show_metacode = 1
    #test_query(ncaafb)
    #test_game_fields(ncaafb)
    test_summary(ncaafb)
    #test_records(ncaafb)



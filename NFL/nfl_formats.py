# NB cannot have any extra spaces at the end of the *_field definitions


import PyQL.outputs as outputs
import urllib
from S2.common_methods import key_to_query_link

STR_NONE = " "
safe_d_d_format = "lambda x:(None in x and '%s') or '%%d-%%d'%%x"%STR_NONE

def game_fields(**kwargs):
    return ("day as Day," +
    "week as Week," +
    "season as Season," +
    "team as Team," +
    "o:team as Opp," +
    "site as Site," +
    "Column((quarter scores[0],o:quarter scores[0]),format='''lambda x:' '*(x is None) or '%s-%s'%(x[0],x[1])''') as Q1," +
    "Column((quarter scores[1],o:quarter scores[1]),format='''lambda x:' '*(x is None) or '%s-%s'%(x[0],x[1])''') as Q2," +
    "Column((quarter scores[2],o:quarter scores[2]),format='''lambda x:' '*(x is None) or '%s-%s'%(x[0],x[1])''') as Q3," +
    "Column((quarter scores[3],o:quarter scores[3]),format='''lambda x:' '*(x is None) or '%s-%s'%(x[0],x[1])''') as Q4," +
    "Column((points,o:points),format='''lambda x:' '*(x is None) or '%s-%s'%(x[0],x[1])''') as Final," +
    "line as Line," +
    "total as Total," +
    "margin as SUm," +
    "ats margin as ATSm," +
    "ou margin as OUm," +
    "Column(points + line/2. - total/2.,format='%0.1f') as DPS," +
    "Column(o:points - line/2. - total/2.,format='%0.1f') as DPA," +
    "{0:'W',1:'L',2:'P',3:' '}[(points<o:points)+2*(points==o:points)+(points is None)] as 'SUr' ," +
    "{0:'W',1:'L',2:'P'}[(points+line<o:points)+2*(points+line==o:points)] as 'ATSr'," +
    "{0:'O',1:'U',2:'P'}[(o:points+points<total)+2*(total==points+o:points)] as 'OUr'," +
    "overtime as ot")


def stat_fields(**kwargs):
    return  r"""Average(line@points is not None,format='%0.1f') as 'a_line',Average(total@points is not None,format='%0.1f') as 'a_total',
Average(rushes,format='%0.1f') as 'a_rushes', Average(o:rushes,format='%0.1f') as 'a_o_rushes',
Average(rushing yards,format='%0.1f') as 'a_rushing_yards', Average(o:rushing yards,format='%0.1f') as 'a_o_rushing_yards',
Average(passes,format='%0.1f') as 'a_passes', Average(o:passes,format='%0.1f') as 'a_o_passes',
Average(passing yards,format='%0.1f') as 'a_passing_yards',   Average(o:passing yards,format='%0.1f') as 'a_o_passing_yards',
Average(completions,format='%0.1f') as 'a_completions',  Average(o:completions,format='%0.1f') as 'a_o_completions',
Average(turnovers,format='%0.1f') as 'a_turnovers',  Average(o:turnovers,format='%0.1f') as 'a_o_turnovers',
Average(quarter scores[0],format='%0.1f') as 'a_q1', Average(quarter scores[1],format='%0.1f') as 'a_q2',
Average(quarter scores[2],format='%0.1f') as 'a_q3', Average(quarter scores[3],format='%0.1f') as 'a_q4',
Average(o:quarter scores[0],format='%0.1f') as 'a_o_q1', Average(o:quarter scores[1],format='%0.1f') as 'a_o_q2',
Average(o:quarter scores[2],format='%0.1f') as 'a_o_q3', Average(o:quarter scores[3],format='%0.1f') as 'a_o_q4',
Average(points,format='%0.1f') as 'a_points',  Average(o:points,format='%0.1f') as 'a_o_points'"""

def record_fields(**kwargs):
    return r"""Record_WLPM(points-o:points+line) as 'ATS',
Record_WLPM(points+o:points-total) as 'OU',
Record_WLPM(points-o:points,format=r'''lambda x:r'%s-%s-%s (%0.1f)'%(x[0],x[1],x[2],x[3])''') as 'SU'"""  

def summary_fields(**kwargs):
    return record_fields(**kwargs)+ ',' + stat_fields(**kwargs) + ',' + game_fields(**kwargs)

def summary_records_table(res,**kwargs):
    ret = []
    ret.append("<table>")
    ret.append("<tr><th>SU:</th>")
    ret.append("<td>%s</td>"%(res.value_from_header("SU"),))
    ret.append("<td></td></tr>")
    ret.append("<tr><th>ATS:</th>")
    ret.append("<td>%s</td>"%(res.value_from_header("ATS"),))
    ret.append("<td>&nbsp;&nbsp;avg line: %s</td></tr>"%res.value_from_header("a_line",''))
    ret.append("<tr><th>OU:</th>")
    ret.append("<td>%s</td>"%(res.value_from_header("OU"),))
    ret.append("<td>&nbsp;&nbsp;avg total: %s</td></tr>"%res.value_from_header("a_total",''))
    ret.append("</table>")
    return '\n'.join(ret)

def summary_stats_table(res,**kwargs):
    ret = []
    ret.append("<table>")
    ret.append("<tr><td align=center></td><th>Rushes</th><th>Rush Yds</th><th>Passes</th><th>Comp</th><th>Pass Yds</th><th>TrnOvrs</th>")
    ret.append("<th>&nbsp;Q1&nbsp;</th><th>&nbsp;Q2&nbsp;</th><th>&nbsp;Q3&nbsp;</th><th>&nbsp;Q4&nbsp;</th><th>Final</th></tr>")
    ret.append("<tr><th>Team:</th>")
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_rushes',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_rushing_yards',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_passes',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_completions',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_passing_yards',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_turnovers',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_q1',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_q2',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_q3',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_q4',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_points',''))
    ret.append("</tr><tr><th>Opp:</th>")    
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_o_rushes',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_o_rushing_yards',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_o_passes',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_o_completions',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_o_passing_yards',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_o_turnovers',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_o_q1',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_o_q2',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_o_q3',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_o_q4',''))
    ret.append("<td align=center>%s</td>"%res.value_from_header('a_o_points',''))
    ret.append("</tr></table>")
    return '\n'.join(ret)

def summary_games_table(res,**kwargs):
    show_games = kwargs.get("n_games",20)
    show_unplayed = kwargs.get("n_unplayed",4)
    # need to find the range of rows to display
    score_offset = res.offset_from_header("Final") 
    len_res = len(res[score_offset].data)
    scores = res[score_offset].data
    i = 0
    for i in range(len_res-1,0,-1):
        if scores[i][0] is not None: break
    len_played = i + 1
    stop = min(len_res, len_played + show_unplayed)
    start = max(0,stop-show_games)
    ret = []
    ret.append("<table id='DT_Table'><thead><tr>")
    day_offset = res.offset_from_header("Day")
    game_headers = res.headers[day_offset:]
    for header in game_headers:
        ret.append("<th>%s</th>"%header)
    ret.append("</tr></thead>")        
    len_game_headers = len(game_headers)
    for g in range(start,stop): #range(len(res[day_offset])):
        ret.append("<tr>")
        for h in range(len_game_headers):
            #print game_headers[h]
            val = res[day_offset+h][g]
            if val is None or val == (None,None): str_val = STR_NONE 
            else: str_val = res[day_offset+h].format(val)
            ret.append("<td align=center>%s</td>"%str_val)
            #ret.append("<td align=center>%s</td>"%res[day_offset+h].format(res[day_offset+h][g]))
        ret.append("</tr>")
    ret.append("</tr>")
    ret.append("</table>")
    return "\n".join(ret)

def summary_html(res,**kwargs):
    query_title = kwargs.get("query_title",'SDQL Results')
    max_games = kwargs.get('n_games',20)
    max_unplayed = kwargs.get("n_unplayed",10)
    ret = []
    ret.append("<!--Start Summary-->")
    ret.append("<TABLE border=0 bgcolor=FFFFFF>")
    if query_title:
        ret.append("<!--Start Key Row--><TR bgcolor=DDDDDD><TH>%s</TH></TR><!--End Key Row-->"%query_title)
    ret.append("<!--Start Records Row--><TR><TD>")               
    ret.append(summary_records_table(res,**kwargs))
    ret.append("</TD></TR><!--End Records Row-->")

    ret.append("<!--Start Stats Row--><TR><TD>")               
    ret.append(summary_stats_table(res,**kwargs))
    ret.append("</TD></TR><!--End Stats Row-->")

    ret.append("<!--Start Games Row--><TR><TD>")               
    ret.append(summary_games_table(res,**kwargs))
    ret.append("</TD></TR><!--End Games Row-->")
        
    ret.append("</TABLE>")
    return "\n".join(ret)


def records_html(res,**kwargs):
    return outputs.html(res.reduced(key_to_query_link))


### tests and demos ####

def test_query(nfl):
    print nfl.nfl_query("%s@team=Bears and season=2009"%summary_fields())

if __name__ == "__main__":
    import sys
    sys.path[:0] = ["/home/jameyer/S2/NFL/Source"]
    from nfl_loader import nfl
    test_query(nfl)

    

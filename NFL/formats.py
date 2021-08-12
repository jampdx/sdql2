import PyQL.dt
import PyQL.outputs
import urllib,cgi
from S2.common_methods import key_to_query_link
import S2.formats

TEAM_MAP = {'Fortyniners':'49ers'}
#http://www.nfl.com/gamecenter/2001090901/2001/REG1/panthers@vikings
#attach to dt in nfl_dt
def box_link(gid,season,week,team,opp,site):
    if not gid: return ''
    team = TEAM_MAP.get(team,team);    opp = TEAM_MAP.get(opp,opp)
    if site=='home': hteam = team;ateam=opp
    else: ateam = team;hteam=opp
    if week>17: week="POST%s"%week
    else: week="REG%s"%week
    return "<a href=http://www.nfl.com/gamecenter/%s/%s/%s/%s@%s>view</a>"%(gid,season,week,ateam.lower(),hteam.lower())

class Query:

    def __init__(self,headers,**kwargs):
        self.headers = headers
        self.score = "points"  # just for ease of use across sports.
        self.line = kwargs.get('line',1)
        self.total = kwargs.get('total',1)
        self.kwargs = kwargs

    def key_to_query_link(self,key,**kwargs):
        kwargs.setdefault("page",self.kwargs.get("form_action","query"))
        return S2.common_methods.key_to_query_link(key,**kwargs)

    def output_html(self,res):
        return PyQL.outputs.html(res,border=0)
    output = output_html

class Query_Records(Query):
    def __init__(self,headers,**kwargs):
        Query.__init__(self,headers,**kwargs)
        st = kwargs.get('show_teasers',1*(kwargs.get('output') == 'summary')) # default show teasers only for summary output.
        self.ngames = kwargs.get("ngames",1)
        self.ats = kwargs.get("ats",1)
        self.atsp6 = kwargs.get("atsp6",st)
        self.atsp10 = kwargs.get("atsp10",st)
        self.atsm6 = kwargs.get("atsm6",st)
        self.atsm10 = kwargs.get("atsm10",st)
        self.line = kwargs.get("line",1)
        self.ou = kwargs.get("ou",1)
        self.oup6 = kwargs.get("oup6",st)
        self.oup10 = kwargs.get("oup10",st)
        self.oum6 = kwargs.get("oum6",st)
        self.oum10 = kwargs.get("oum10",st)
        self.total = kwargs.get("total",1)
        self.su = kwargs.get("su",1)
        self.n_rows = kwargs.get("n_rows",100)

    def select(self):
        select = ''
        if self.ngames:
            select = "Count(%s) as 'games',"%self.score
        if self.ats:
            select += "Record_WLPM(%s-o:%s+line,format='''lambda x:'%%s-%%s-%%s (%%0.2f, %%0.1f&#37;)'%%(x[0],x[1],x[2],x[3],(100.*x[0])/((x[0]+x[1]) or 1))''') as 'ATS',"%(self.score,self.score)
            if self.line:
                select += "Average(t:line+0*t:points,format='%0.1f') as 'Avg Line',"
        if self.ou:
            select += "Record_WLPM(%s+o:%s-total,format='''lambda x:'%%s-%%s-%%s (%%0.2f, %%0.1f&#37;)'%%(x[0],x[1],x[2],x[3],(100.*x[0])/((x[0]+x[1]) or 1))''') as 'O/U',"%(self.score,self.score)
            if self.total:
                select += "Average(t:total+0*points,format='%0.1f') as 'Avg Total',"
        if self.su:
            select += "Record_WLPM(%s-o:%s,format='''lambda x:'%%s-%%s-%%s (%%0.2f, %%0.1f&#37;)'%%(x[0],x[1],x[2],x[3],(100.*x[0])/((x[0]+x[1]) or 1))''') as 'SU',"%(self.score,self.score)
        if self.atsp6:
            select += "Record_WLPM(%s-o:%s+line+6,format='''lambda x:'%%s-%%s-%%s (%%0.1f&#37;)'%%(x[0],x[1],x[2],(100.*x[0])/((x[0]+x[1]) or 1))''') as 'ATSp6',"%(self.score,self.score)
        if self.atsm6:
            select += "Record_WLPM(%s-o:%s+line-6,format='''lambda x:'%%s-%%s-%%s (%%0.1f&#37;)'%%(x[0],x[1],x[2],(100.*x[0])/((x[0]+x[1]) or 1))''') as 'ATSm6',"%(self.score,self.score)
        if self.atsp10:
            select += "Record_WLPM(%s-o:%s+line+10,format='''lambda x:'%%s-%%s-%%s (%%0.1f&#37;)'%%(x[0],x[1],x[2],(100.*x[0])/((x[0]+x[1]) or 1))''') as 'ATSp10',"%(self.score,self.score)
        if self.atsm10:
            select += "Record_WLPM(%s-o:%s+line-10,format='''lambda x:'%%s-%%s-%%s (%%0.1f&#37;)'%%(x[0],x[1],x[2],(100.*x[0])/((x[0]+x[1]) or 1))''') as 'ATSm10',"%(self.score,self.score)
        if self.oup6:
            select += "Record_WLPM(%s+o:%s-total-6,format='''lambda x:'%%s-%%s-%%s (%%0.1f&#37;)'%%(x[0],x[1],x[2],(100.*x[0])/((x[0]+x[1]) or 1))''') as 'O/Up6',"%(self.score,self.score)
        if self.oum6:
            select += "Record_WLPM(%s+o:%s-total+6,format='''lambda x:'%%s-%%s-%%s (%%0.1f&#37;)'%%(x[0],x[1],x[2],(100.*x[0])/((x[0]+x[1]) or 1))''') as 'O/Um6',"%(self.score,self.score)
        if self.oup10:
            select += "Record_WLPM(%s+o:%s-total-10,format='''lambda x:'%%s-%%s-%%s (%%0.1f&#37;)'%%(x[0],x[1],x[2],(100.*x[0])/((x[0]+x[1]) or 1))''') as 'O/Up10',"%(self.score,self.score)
        if self.oum10:
            select += "Record_WLPM(%s+o:%s-total+10,format='''lambda x:'%%s-%%s-%%s (%%0.1f&#37;)'%%(x[0],x[1],x[2],(100.*x[0])/((x[0]+x[1]) or 1))''') as 'O/Um10',"%(self.score,self.score)


        if select[-1] == ',': select = select[:-1]
        return select

    def output(self,res,**kwargs):
        self.kwargs['key_to_query_link'] = self.key_to_query_link
        return S2.formats.records_output(res,**self.kwargs)

class Query_Summary(Query_Records):

    records_select = Query_Records.select
    def __init__(self,headers,**kwargs):
        Query_Records.__init__(self,headers,**kwargs)
        self.show_unplayed = int(kwargs.get("show_unplayed",16))
        self.show_games = int(kwargs.get("show_games",40))
        self.first_summary_select = kwargs.get("first_summary_select","t:Rushes")

    def stats_select(self,prefix):
        ret = ''
        ret += "A(%s:rushes,format='%%0.1f') as '%s:Rushes',"%(prefix,prefix)
        ret += "A(%s:rushing yards,format='%%0.1f') as '%s:Rush Yds',"%(prefix,prefix)
        ret += "A(%s:passes,format='%%0.1f') as '%s:Passes',"%(prefix,prefix)
        ret += "A(%s:passing yards,format='%%0.1f') as '%s:Pass Yds',"%(prefix,prefix)
        ret += "A(%s:completions,format='%%0.1f') as '%s:Comp',"%(prefix,prefix)
        ret += "A(%s:turnovers,format='%%0.1f') as '%s:TOs',"%(prefix,prefix)
        ret += "A(%s:quarter scores[0],format='%%0.1f') as '%s:Q1',"%(prefix,prefix)
        ret += "A(%s:quarter scores[1],format='%%0.1f') as '%s:Q2',"%(prefix,prefix)
        ret += "A(%s:quarter scores[2],format='%%0.1f') as '%s:Q3',"%(prefix,prefix)
        ret += "A(%s:quarter scores[3],format='%%0.1f') as '%s:Q4',"%(prefix,prefix)
        ret += "A(%s:points,format='%%0.1f') as '%s:Final',"%(prefix,prefix)
        return ret[:-1]

    def select(self):
        ret = self.records_select() + ","
        ret += self.stats_select('t') + ","
        ret += self.stats_select('o') + ","
        self.first_games_select = "Date"
        self.score_offset = "Final"
        ret += ("self.nice_date(date,abbreviate_month=1,abbreviate_year=0) as 'Date'," +
                "self.box_link(_gid,season,week,team,o:team,site) as 'Link',"
                "day as Day," +
                "week as Week," +
                "season as Season," +
                "team as Team," +
                "o:team as Opp," +
                "site as Site," +
                "Column((quarter scores[0],o:quarter scores[0]),format='''lambda x:' '*(x is None) or '%s-%s'%(x[0],x[1])''') as Q1," +
                "Column((quarter scores[1],o:quarter scores[1]),format='''lambda x:' '*(x is None) or '%s-%s'%(x[0],x[1])''') as Q2," +
                "Column((quarter scores[2],o:quarter scores[2]),format='''lambda x:' '*(x is None) or '%s-%s'%(x[0],x[1])''') as Q3," +
                "Column((quarter scores[3],o:quarter scores[3]),format='''lambda x:' '*(x is None) or '%s-%s'%(x[0],x[1])''') as Q4," +
                "Column((points,o:points),format='''lambda x:' '*(x[0] is None) or '<b>%s-%s</b>'%(x[0],x[1])''') as Final," )
        if self.line:  ret += "line as Line,"
        if self.total: ret += "total as Total,"
        ret += "margin as SUm,"
        if self.ats: ret += "ats margin as ATSm,"
        if self.ou:  ret += "ou margin as OUm,"
        if self.ats and self.ou:
            ret += "Column(points + line/2. - total/2.,format='%0.1f') as DPS,"
            ret += "Column(o:points - line/2. - total/2.,format='%0.1f') as DPA,"

        ret += "{0:'W',1:'L',2:'P',3:' '}[(points<o:points)+2*(points==o:points)+(points is None)] as 'SUr' ,"
        if self.ats:
            ret += "{0:'W',1:'L',2:'P'}[(points+line<o:points)+2*(points+line==o:points)] as 'ATSr',"
        if self.ou:
            ret +=  "{0:'O',1:'U',2:'P'}[(o:points+points<total+0)+2*(total==points+o:points)] as 'OUr',"
        ret += "overtime as ot"
        return ret

    def records_table(self,res):
        ret = []
        ret.append("<table>")
        if self.kwargs.get('caption'):
            ret.append("<caption>%s</caption>"%self.kwargs["caption"])
        if self.su:
            ret.append("<tr><th>SU:</th>")
            ret.append("<td>%s</td>"%(res.value_from_header("SU"),))
        if self.atsp6 or self.atsm6 or self.atsp10 or self.atsm10 or self.oup6 or self.oum6 or self.oup10 or self.oum10:
            ret.append("<td></td><th colspan=4 bgcolor=F8F8F8>Teaser Records</tr>")
        else:
            ret.append("<td></td><th colspan=4></tr>")

        if self.ats:
            ret.append("<tr><th>ATS:</th>")
            ret.append("<td>%s</td>"%(res.value_from_header("ATS"),))

            if self.line: ret.append("<td>&nbsp;&nbsp;avg line: %s</td>"%(res.value_from_header("Avg Line",'')))
            else: ret.append("<td></td>")

            if self.atsp6: ret.append("<td bgcolor=F8F8F8> <b>+6:</b>&nbsp; %s &nbsp; </td>"%(res.value_from_header("ATSp6"),))
            else: ret.append("<td></td>")
            if self.atsm6: ret.append("<td bgcolor=F8F8F8> <b>-6:</b>&nbsp;  %s &nbsp; </td>"%(res.value_from_header("ATSm6"),))
            else: ret.append("<td></td>")
            if self.atsp10: ret.append("<td bgcolor=F8F8F8> <b>+10:</b>&nbsp;  %s &nbsp; </td>"%(res.value_from_header("ATSp10"),))
            else: ret.append("<td></td>")
            if self.atsm10: ret.append("<td bgcolor=F8F8F8> <b>-10:</b>&nbsp;  %s &nbsp; </td>"%(res.value_from_header("ATSm10"),))
            else: ret.append("<td></td>")
            ret.append("</tr>")

        if self.ou:
            ret.append("<tr><th>O/U:</th>")
            ret.append("<td>%s</td>"%(res.value_from_header("O/U"),))
            if self.total:
                ret.append("<td>&nbsp;&nbsp;avg total: %s</td>"%res.value_from_header("Avg Total",''))
            else: ret.append("<td></td>")
            if self.oup6: ret.append("<td bgcolor=F8F8F8><b>+6:</b> &nbsp; %s &nbsp;</td>"%(res.value_from_header("O/Up6"),))
            else: ret.append("<td></td>")
            if self.oum6: ret.append("<td bgcolor=F8F8F8><b>-6:</b> &nbsp; %s &nbsp;</td>"%(res.value_from_header("O/Um6"),))
            else: ret.append("<td></td>")
            if self.oup10: ret.append("<td bgcolor=F8F8F8><b>+10:</b> &nbsp; %s &nbsp;</td>"%(res.value_from_header("O/Up10"),))
            else: ret.append("<td></td>")
            if self.oum10: ret.append("<td bgcolor=F8F8F8><b>-10:</b> &nbsp; %s  &nbsp;</td>"%(res.value_from_header("O/Um10"),))
            else: ret.append("<td></td>")
            ret.append("</tr>")


        ret.append("</table>")
        return '\n'.join(ret)

    def stats_table(self,res):
        ret = []
        ret.append("<table><tr><th></th>") # space for team/opp
        start_column = res.offset_from_header(self.first_summary_select)
        stop_column = res.offset_from_header(self.first_games_select)
        fields = (stop_column-start_column)/2
        team = ["<tr><th>Team</th>"]
        opp = ["<tr><th>Opp</th>"]
        for i in range(start_column,start_column+fields):
            ret.append("<th>%s</th>"%(res.headers[i].split(':',1)[1],))
            team.append("<td>%s</td>"%(res[i],))
            opp.append("<td>%s</td>"%(res[i+fields],))
        ret.append("</tr>")
        team.append("</tr>")
        opp.append("</tr>")
        ret += team + opp
        ret.append("</table>")
        return "\n".join(ret)

    def games_table(self,res):
        start_column = res.offset_from_header(self.first_games_select)
        stop_column = len(res.headers)
        gdt = PyQL.dt.DT()
        for i in range(start_column,stop_column):  gdt.add_object(res[i])

        score_offset = gdt.offset_from_header("Final")
        len_res = len(gdt[score_offset].data)
        scores = gdt[score_offset].data
        i = 0
        for i in range(len_res-1,0,-1):
            if scores[i][0] is not None: break
        len_played = i + 1
        stop = min(len_res, len_played + self.show_unplayed)
        start = max(0,stop-self.show_games)

        for h in range(len(gdt)):
            gdt[h].data = gdt[h].data[start:stop]
        return PyQL.outputs.html(gdt,null=' ',border=0,row_stripe="F2F2F2",error_as_null=1)

    def output(self,res,**kwargs):
        ret = []
        ret.append("<!--Start Summary-->")
        ret.append("<TABLE border=0 bgcolor=FFFFFF>")
        if kwargs.get('query_title') and kwargs.get('show_key',1):
            ret.append("<!--Start Key Row--><TR bgcolor=DDDDDD><TH>%s</TH></TR><!--End Key Row-->"%(
                           cgi.escape(kwargs.get('query_title','')),))
        if self.kwargs.get('show_records',1):
            ret.append("<!--Start Records Row--><TR><TD>")
            ret.append(self.records_table(res))
            ret.append("</TD></TR><!--End Records Row-->")
        if self.kwargs.get('show_stats',1):
            ret.append("<!--Start Stats Row--><TR><TD>")
            ret.append(self.stats_table(res))
            ret.append("</TD></TR><!--End Stats Row-->")
        if self.show_games:
            ret.append("<!--Start Games Row--><TR><TD>")
            ret.append(self.games_table(res))
            ret.append("</TD></TR><!--End Games Row-->")

        ret.append("</TABLE>")
        return "\n".join(ret)



### tests and demos ####
def test_records(sdb):
    Q = Query_Records(sdb.headers,ou=1)
    res = sdb.sdb_query(Q.select() + '@site and team[0]=B')
    print res
    #return
    html =  Q.output(res)
    open("/tmp/sdb.html",'w').write(html)
    print Q.select()
    #print html

### tests and demos ####
def test_summary(sdb):
    Q = Query_Summary(sdb.headers)
    res = sdb.sdb_query(Q.select() + '@site and team[0]=B and season=2012')
    print res
    #return
    html = ''
    for r in res:
        html += Q.output(r,**{'query_title':' '.join(r.name[-1])})
    open("/tmp/sdb.html",'w').write(html)
    #print html

def test_query(nfl):
    print nfl.sdb_query("%s@team=Bears and season=2009"%summary_fields())

if __name__ == "__main__":
    from NFL.loader import nfl
    #test_query(nfl)
    test_records(nfl)
    #test_summary(nfl)
    #Q = Query_Summary(nfl.headers)

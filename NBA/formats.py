import PyQL.outputs
import urllib,cgi
from S2.common_methods import key_to_query_link
import S2.formats
import NBA.teams

class Query:
    key_to_query_link = key_to_query_link
    def __init__(self,headers,**kwargs):
        self.headers = headers
        self.kwargs = kwargs
        
    def output_html(self,res):
        return PyQL.outputs.html(res,border=0)
    output = output_html

class Query_Records(Query):
    def __init__(self,headers,**kwargs):
        Query.__init__(self,headers,**kwargs)
        self.ngames = kwargs.get("ngames",1)
        self.ats = kwargs.get("ats",1)
        self.line = kwargs.get("line",1)
        self.ou = kwargs.get("ou",1)
        self.total = kwargs.get("total",1)        
        self.su = kwargs.get("su",1)
        self.n_rows = kwargs.get("n_rows",100) 

    def select(self):
        select = ''
        if self.ngames:
            select = "Count(points) as 'games',"
        if self.ats:
            select += "Record_WLPM(points-o:points+line,format='''lambda x:'%s-%s-%s (%0.2f, %0.1f&#37;)'%(x[0],x[1],x[2],x[3],(100.*x[0])/((x[0]+x[1]) or 1))''') as 'ATS',"
            if self.line:
                select += "Average(t:line+0*t:points,format='%0.1f') as 'Avg Line',"
        if self.ou:    
            select += "Record_WLPM(points+o:points-total,format='''lambda x:'%s-%s-%s (%0.2f, %0.1f&#37;)'%(x[0],x[1],x[2],x[3],(100.*x[0])/((x[0]+x[1]) or 1))''') as 'O/U',"
            if self.total:
                select += "Average(t:total+0*points,format='%0.1f') as 'Avg Total',"
        if self.su:
            select += "Record_WLPM(points-o:points,format='''lambda x:'%s-%s (%0.2f, %0.1f&#37;)'%(x[0],x[1],x[3],(100.*x[0])/((x[0]+x[1]) or 1))''') as 'SU',"

        return select[:-1] 

    def output(self,res):
        return S2.formats.records_output(res,**self.kwargs)
        



class Query_Summary(Query_Records):
    
    records_select = Query_Records.select
    def __init__(self,headers,**kwargs):
        Query_Records.__init__(self,headers,**kwargs)
        self.show_unplayed = int(kwargs.get("show_unplayed",15))
        self.show_games = int(kwargs.get("show_games",50))
        self.level = kwargs.get("level","pro")
        
    def stats_select(self,prefix):
        select = ''
        select += "A(%s:field goals made) as '%s:FG',"%(prefix,prefix)
        #select += "A(%s:field goals attempted) as '%s:FGA',"%(prefix,prefix)
        select += "R((S(%s:field goals made), S(%s:field goals attempted)),format='''lambda x:'%%0.1f'%%(100.*x[0]/x[1])''' ) as '%s:Pct',"%(prefix,prefix,prefix)

        select += "A(%s:free throws made) as '%s:FT',"%(prefix,prefix)
        #select += "A(%s:free throws attempted) as '%s:FTA',"%(prefix,prefix)
        select += "R((S(%s:free throws made), S(%s:free throws attempted)),format='''lambda x:'%%0.1f'%%(100.*x[0]/x[1])''' ) as '%s:Pct',"%(prefix,prefix,prefix)
        
        select += "A(%s:three pointers made) as '%s:3s',"%(prefix,prefix)
        #select += "A(%s:three pointers attempted) as '%s:TPA',"%(prefix,prefix)
        select += "R((S(%s:three pointers made), S(%s:three pointers attempted)),format='''lambda x:'%%0.1f'%%(100.*x[0]/x[1])''' ) as '%s:Pct',"%(prefix,prefix,prefix)


        select += "A(%s:blocks) as '%s:BLKS',"%(prefix,prefix)
        select += "A(%s:offensive rebounds) as '%s:O-RBND',"%(prefix,prefix)
        select += "A(%s:rebounds) as '%s:RBND',"%(prefix,prefix)
        select += "A(%s:fouls) as '%s:Fouls',"%(prefix,prefix)
        select += "A(%s:assists) as '%s:AST',"%(prefix,prefix)
        select += "A(%s:turnovers) as '%s:TOvers',"%(prefix,prefix)
        if self.level == 'pro':
            select += "A(%s:quarter scores[0],format='%%0.1f') as '%s:Q1',"%(prefix,prefix)
            select += "A(%s:quarter scores[1],format='%%0.1f') as '%s:Q2',"%(prefix,prefix)
            select += "A(%s:quarter scores[2],format='%%0.1f') as '%s:Q3',"%(prefix,prefix)
            select += "A(%s:quarter scores[3],format='%%0.1f') as '%s:Q4',"%(prefix,prefix)
            select += "A(%s:points,format='%%0.1f') as '%s:Final',"%(prefix,prefix)
        
        else:
            select += "A(%s:half scores[0],format='%%0.1f') as '%s:H1',"%(prefix,prefix)
            select += "A(%s:half scores[1],format='%%0.1f') as '%s:H2',"%(prefix,prefix)
            select += "A(%s:points,format='%%0.1f') as '%s:Final',"%(prefix,prefix)
        
        return select[:-1]
    
    def select(self):
        select = self.records_select() + ","
        self.first_summary_select = "t:FG"          
        select += self.stats_select('t') + ","
        select += self.stats_select('o') + ","
        self.first_games_select = "Date"
        self.score_offset = "Final"
        if self.level == 'pro': box_link = "self.box_link(date,team,o:team,site) as 'Link',"
        else: box_link = "self.box_link(date,gid) as 'Link',"                   
        select += ("self.nice_date(date,abbreviate_month=1,abbreviate_year=0) as 'Date'," +
                   box_link +
                "self.day_from_date(date)[:3] as Day," +
                "season as Season," +
                "team as Team," +
                "o:team as Opp," +
                "site as Site," +
                "Column((points,o:points),format='''lambda x:(' '*(x[0] is None) or '<b>%s-%s</b>'%(x[0],x[1])) ''') as Final," +
                "Column((rest,o:rest),format='''lambda x:(' '*(x[0] is None) or str(x[0])) + '&' + (' '*(x[1] is None) or str(x[1]))  ''') as Rest," )
        if self.line: select += "line as Line," 
        if self.total: select += "total as Total," 
        select += "margin as SUm," 
        if self.ats: select += "ats margin as ATSm," 
        if self.ou: select += "ou margin as OUm," 
        if self.line and self.total:
            select += "Column(points + line/2. - total/2.,format='%0.1f') as DPS," 
            select += "Column(o:points - line/2. - total/2.,format='%0.1f') as DPA,"
        select += "{0:'W',1:'L',2:'P',3:' '}[(points<o:points)+2*(points==o:points)+(points is None)] as 'SUr' ," 
        if self.ats: select += "{0:'W',1:'L',2:'P'}[(points+line<o:points)+2*(points+line==o:points)] as 'ATSr'," 
        if self.ou: select += "{0:'O',1:'U',2:'P'}[(o:points+points<total+0)+2*(total==points+o:points)] as 'OUr'," 
        select += "overtime as ot"
        return select

    def records_table(self,res):
        select = []
        select.append("<table>")
        if self.su:
            select.append("<tr><th>SU:</th>")
            select.append("<td>%s</td>"%(res.value_from_header("SU"),))
            select.append("<td></td></tr>")
        if self.ats:
            select.append("<tr><th>ATS:</th>")
            select.append("<td>%s</td>"%(res.value_from_header("ATS"),))
        if self.line:
            select.append("<td>&nbsp;&nbsp;avg line: %s</td></tr>"%(res.value_from_header("Avg Line",'')))
        else:
            select.append("<td></td></tr>")            
        if self.ou:
            select.append("<tr><th>O/U:</th>")
            select.append("<td>%s</td>"%(res.value_from_header("O/U"),))
        if self.total:
            select.append("<td>&nbsp;&nbsp;avg total: %s</td></tr>"%res.value_from_header("Avg Total",''))
        else:
            select.append("<td></td></tr>")            
        select.append("</table>")
        return '\n'.join(select)

    def quarter_scores_table(self,res):

        if self.level == 'pro':
            cols = 5
            symbol = 'Q'
        else:
            cols = 3
            symbol = 'H'

        select = []
        select.append("<table><tr><td></td>")
        for i in range(1,5):
            select.append("<th>%s%d</th>"%(symbol,i))
        select.append("<th>Final</th></tr>")
        
                    
        for team in 'to':
            select.append("<tr><th>%s</th>"%{'t':'Team','o':'Opp'}[team])
            for i in range(1,5):
                select.append("<td>%s</td>"%res.value_from_header("%s:%s%d"%(team,symbol,i)))
            select.append("<td>%s</td></tr>"%res.value_from_header("%s:Final"%(team,)))
        select.append("</table>")
        return '\n'.join(select)
        
    def stats_table(self,res): 
        select = []
        select.append("<table><tr><th></th>") # space for team/opp
        start_column = res.offset_from_header(self.first_summary_select)
        stop_column = res.offset_from_header(self.first_games_select)
        fields = (stop_column-start_column)/2
        team = ["<tr><th>Team</th>"]
        opp = ["<tr><th>Opp</th>"]
        for i in range(start_column,start_column+fields):
            select.append("<th>%s</th>"%(res.headers[i].split(':',1)[1],))
            team.append("<td>%s</td>"%(res[i],))
            opp.append("<td>%s</td>"%(res[i+fields],))
        select.append("</tr>")
        select += team + opp
        select.append("</table>")
        return "\n".join(select)
        
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
        if kwargs.get('query_title'):
            ret.append("<!--Start Key Row--><TR bgcolor=DDDDDD><TH>%s</TH></TR><!--End Key Row-->"%(
                           cgi.escape(kwargs.get('query_title','')),))
        ret.append("<!--Start Records Row--><TR><TD>")               
        ret.append(self.records_table(res))
        ret.append("</TD></TR><!--End Records Row-->")

        #ret.append("<!--Start Quarter Scores Row--><TR><TD>")               
        #ret.append(self.quarter_scores_table(res))
        #ret.append("</TD></TR><!--End Stats Row-->")

        ret.append("<!--Start Stats Row--><TR><TD>")               
        ret.append(self.stats_table(res))
        ret.append("</TD></TR><!--End Stats Row-->")

        ret.append("<!--Start Games Row--><TR><TD>")               
        ret.append(self.games_table(res))
        ret.append("</TD></TR><!--End Games Row-->")

        ret.append("</TABLE>")
        return "\n".join(ret)



### tests and demos ####

def test_query(nba):
    print nba.query("(date,points,o:team)@team=Bulls and season=2009")

def test_game_fields(nba):
    res = nba.query("%s@team=Bulls and season=2010"%game_fields())[0]
    print res
    print summary_games_table(res)
    
### tests and demos ####
def test_records(sdb):
    Q = Query_Records(headers=sdb.headers,ou=1)
    res = sdb.sdb_query(Q.select() + '@site and team[0]=B')
    print res
    #return 
    html =  Q.output(res)
    open("/tmp/sdb.html",'w').write(html)
    #print html

def test_summary(sdb):
    Q = Query_Summary(headers=sdb.headers,ou=1)
    res = sdb.sdb_query(Q.select() + '@H and season=2009')
    print res
    #return 
    html = ''
    for r in res:
        html += Q.output(r,**{'query_title':' '.join(r.name[-1])})
    open("/tmp/sdb.html",'w').write(html)
    #print html




if __name__ == "__main__":
    import sys
    #from NBA.loader import nba
    #test_summary(nba)
    test_records(nba)


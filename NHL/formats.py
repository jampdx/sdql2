import PyQL.outputs
import urllib,cgi
from S2.common_methods import key_to_query_link
import S2.formats 

class Query:

    def __init__(self,headers,**kwargs):
        self.kwargs = kwargs
        self.headers = headers
    def key_to_query_link(self,key,**kwargs):
        kwargs.setdefault("page",self.kwargs.get("form_action","query"))
        return S2.common_methods.key_to_query_link(key,**kwargs)        
    def output_html(self,res):
        return PyQL.outputs.html(res)
    output = output_html

class Query_Records(Query):
    def __init__(self,headers,**kwargs):
        Query.__init__(self,headers,**kwargs)
        self.ngames = kwargs.get("ngames",1)
        self.su = kwargs.get("su",1)
        self.ou = kwargs.get("ou",1)
        self.invested = kwargs.get("invested",1)
        self.PL = kwargs.get("PL",1)
        self.n_rows = kwargs.get("n_rows",100)
        self.line = kwargs.get("line",1)
        self.total = kwargs.get("total",1)

    def select(self):
        select = ''
        if self.ngames:
            select = "Count(t:goals) as games,"
        if self.su:
            select += "Record_WLPM(t:goals-o:goals,format='''lambda x:'%s-%s (%0.2f, %0.1f&#37;)'%(x[0],x[1],x[3],100.*x[0]/((x[0]+x[1]) or 1))''') as 'SU',"
            if self.line:
                select += "Average_Line(t:line,format='%0.1f') as 'Avg Line',Average_Line(o:line,format='%0.1f') as 'o:Avg Line',"                
            if self.PL:
                select += "Sum(( line+0<0 and (t:goals>o:goals) )*100 or ( 0<0+line and (t:goals<o:goals) )*(-100) or ( t:goals is not None )*(line+0),format='''lambda x,df=PyQL.outputs.dollar_format:df(x)''') as '$ On',"
                select += "Sum(( 0+o:line<0 and (o:goals>t:goals) )*100 or ( 0<0+o:line and (o:goals<t:goals) )*(-100) or ( t:goals is not None )*(o:line+0),format='''lambda x,df=PyQL.outputs.dollar_format:df(x)''') as '$ Against',"            
            if self.invested:
                select += "Sum(( 0<0+line and (t:goals is not None))*100 or (-1*line)*(t:goals is not None) or 0)  as 'On Invested',"
                select += "Sum(( 0<0+o:line and (t:goals is not None))*100 or (-1*o:line)*(t:goals is not None) or 0) as 'Against Invested',"         


        if self.ou:    
            select += "Record_WLPM(t:goals+o:goals-total,format='''lambda x:'%s-%s-%s (%0.2f, %0.1f&#37;)'%(x[0],x[1],x[2],x[3],100.*x[0]/((x[0]+x[1]) or 1))''') as 'O/U',"
            if self.total:
                select += "Average(t:total+0*t:goals,format='%0.1f') as Avg Total,"
            if 0 and self.PL: # do not have over / under price
                select += "Sum(( 0+over<0 and 0+total<(t:goals+o:goals) )*100 or ( 0<over and (t:goals+o:goals)<total)*(-100) or ((t:goals+o:goals)!=total)*over,format='''lambda x,df=PyQL.outputs.dollar_format:df(x)''') as '$ Over',"
                select += "Sum(( 0+under<0 and (t:goals+o:goals)<total )*100 or ( 0<under and total<(t:goals+o:goals))*(-100) or ((t:goals+o:goals)!=total)*under,format='''lambda x,df=PyQL.outputs.dollar_format:df(x)''') as '$ Under',"
            if 0 and self.invested:
                select += "Sum(( 0<0+over and (t:goals is not None))*100 or (-1*over)*(t:goals is not None) or 0)  as 'Over Invested',"
                select += "Sum(( 0<0+under and (t:goals is not None))*100 or (-1*under)*(t:goals is not None) or 0)  as 'Under Invested',"        
            
        if select[-1] == ',': select = select[:-1]
        return select 

    def output(self,res):
        self.kwargs['key_to_query_link'] = self.key_to_query_link        
        return S2.formats.records_output(res,**self.kwargs)

class Query_Summary(Query_Records):
    
    records_select = Query_Records.select
    def __init__(self,headers,**kwargs):
        Query_Records.__init__(self,headers,**kwargs)
        self.show_unplayed = int(kwargs.get("show_unplayed",10))
        self.show_games = int(kwargs.get("show_games",20))
        
    def stats_select(self,prefix):
        ret = ''            # first `as` must match  self.first_summary_select
        ret += "A(%s:shots on goal,format='%%0.1f') as '%s:SoG',"%(prefix,prefix)
        ret += "A(%s:penalties,format='%%0.1f') as '%s:Pens',"%(prefix,prefix)
        ret += "A(%s:penalty minutes,format='%%0.1f') as '%s:P-Mins',"%(prefix,prefix)
        ret += "A(%s:period scores[0],format='%%0.1f') as '%s:P1',"%(prefix,prefix)
        ret += "A(%s:period scores[1],format='%%0.1f') as '%s:P2',"%(prefix,prefix)
        ret += "A(%s:period scores[2],format='%%0.1f') as '%s:P3',"%(prefix,prefix)
        ret += "A(%s:goals,format='%%0.1f') as '%s:Final',"%(prefix,prefix)
        return ret[:-1]
    
    def select(self):
        ret = self.records_select() + ","
        self.first_summary_select = "t:SoG"          
        ret += self.stats_select('t') + ","
        ret += self.stats_select('o') + ","
        self.first_games_select = "Date"
        self.score_offset = "Final"
        ret += ("self.nice_date(date,abbreviate_month=1,abbreviate_year=0) as 'Date'," +
                "day as Day," +
                "season as Season," +
                "team as Team," +
                "o:team as Opp," +
                "site as Site," +
                "Column((period scores[0],o:period scores[0]),format='''lambda x:' '*(x is None) or '%s-%s'%(x[0],x[1])''') as P1," +
                "Column((period scores[1],o:period scores[1]),format='''lambda x:' '*(x is None) or '%s-%s'%(x[0],x[1])''') as P2," +
                "Column((period scores[2],o:period scores[2]),format='''lambda x:' '*(x is None) or '%s-%s'%(x[0],x[1])''') as P3," +
                "Column((t:goals,o:goals),format='''lambda x:' '*(x[0] is None) or '<b>%s-%s</b>'%(x[0],x[1])''') as Final," )
        if self.line: ret += "line as Line,"
        if self.total: ret += "total as Total,"
        ret += "t:goals-o:goals as SUm," 
        if self.total: ret + "t:goals+o:goals-t:total as OUm,"
        ret += "{0:'W',1:'L',2:'P',3:' '}[(t:goals<o:goals)+2*(t:goals==o:goals)+(t:goals is None)] as 'SUr' ," 
        if self.total: ret += "{0:'O',1:'U',2:'P'}[(o:goals+t:goals<total+0)+2*(total==t:goals+o:goals)] as 'OUr'," 
        ret += "overtime as ot"
        return ret

    def XXrecords_table(self,res):
        ret = []
        ret.append("<table>")
        if self.su:
            ret.append("<tr><th>SU:</th>")
            ret.append("<td>%s</td>"%(res.value_from_header("SU"),))
        if self.line:
            ret.append("<td>&nbsp;&nbsp;avg line: %s</td></tr>"%(res.value_from_header("Avg Line",'')))
        else:
            ret.append("<td></td></tr>")            
        if self.ou:
            ret.append("<tr><th>O/U:</th>")
            ret.append("<td>%s</td>"%(res.value_from_header("O/U"),))
        if self.total:
            ret.append("<td>&nbsp;&nbsp;avg total: %s</td></tr>"%res.value_from_header("Avg Total",''))
        else:
            ret.append("<td></td></tr>")            
        ret.append("</table>")
        return '\n'.join(ret)


    def records_table(self,res):
        ret = []
        ret.append("<table>")
        if self.su:
            ret.append("<tr><th>SU:</th>")
            ret.append("<td>%s</td>"%(res.value_from_header("SU"),))
            if self.line:
                ret.append("<td>&nbsp;&nbsp;avg line: %s / %s</td>"%(res.value_from_header("Avg Line",''),res.value_from_header("o:Avg Line",'')))
            else:
                ret.append("<td></td>")
            if self.PL:
                on_made = res.value_from_header("$ On").value() or 0
                against_made = res.value_from_header("$ Against").value() or 0
                on_invested = res.value_from_header("On Invested").value() or 0
                against_invested = res.value_from_header("Against Invested").value() or 0
                on_roi = S2.formats.percent_format(on_invested,on_made)
                against_roi = S2.formats.percent_format(against_invested,against_made)
                ret.append("<td>&nbsp;&nbsp;on / against: %s  / %s</td>"%(S2.formats.dollar_format(on_made),S2.formats.dollar_format(against_made)))
                ret.append("<td>&nbsp;&nbsp;ROI:  %s / %s</td></tr>"%(on_roi,against_roi))

            else:
                ret.append("<td></td><td></td>")
            ret.append("</tr>")

        if 0 : # place holder for goal line
            ret.append("<tr><th>RL:</th>")
            ret.append("<td>%s</td>"%(res.value_from_header("RL"),))
            if self.line:
                ret.append("<td>&nbsp;&nbsp;avg line: %s / %s</td>"%(res.value_from_header("Avg Run Line",''),res.value_from_header("o:Avg Run Line",'')))
            else:
                ret.append("<td></td>")
            if self.PL:
                on_made = res.value_from_header("$ RL On").value() or 0
                against_made = res.value_from_header("$ RL Against").value() or 0
                on_invested = res.value_from_header("RL On Invested").value() or 0
                against_invested = res.value_from_header("RL Against Invested").value() or 0
                on_roi = S2.formats.percent_format(on_invested,on_made)
                against_roi = S2.formats.percent_format(against_invested,against_made)
                ret.append("<td>&nbsp;&nbsp;on / against: %s  / %s</td>"%(S2.formats.dollar_format(on_made),S2.formats.dollar_format(against_made)))
                ret.append("<td>&nbsp;&nbsp;ROI:  %s / %s</td></tr>"%(on_roi,against_roi))

            else:
                ret.append("<td></td><td></td>")
            ret.append("</tr>")

        if self.total:
            ret.append("<tr><th>OU:</th>")
            ret.append("<td>%s</td>"%(res.value_from_header("O/U"),))
            if self.line:
                ret.append("<td>&nbsp;&nbsp;avg total: %s </td>"%(res.value_from_header("Avg Total",'')))
            else:
                ret.append("<td></td>")
            if 0 and self.PL: # do not have over / under price
                on_made = res.value_from_header("$ Over").value() or 0
                against_made = res.value_from_header("$ Under").value() or 0
                on_invested = res.value_from_header("Over Invested").value() or 0
                against_invested = res.value_from_header("Under Invested").value() or 0
                on_roi = S2.formats.percent_format(on_invested,on_made)
                against_roi = S2.formats.percent_format(against_invested,against_made)
                ret.append("<td>&nbsp;&nbsp;over / under: %s  / %s</td>"%(S2.formats.dollar_format(on_made),S2.formats.dollar_format(against_made)))
                ret.append("<td>&nbsp;&nbsp;ROI:  %s / %s</td></tr>"%(on_roi,against_roi))
            else:
                ret.append("<td></td><td></td>")
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
        if kwargs.get('query_title'):
            ret.append("<!--Start Key Row--><TR bgcolor=DDDDDD><TH>%s</TH></TR><!--End Key Row-->"%(
                           cgi.escape(kwargs.get('query_title','')),))
        ret.append("<!--Start Records Row--><TR><TD>")               
        ret.append(self.records_table(res))
        ret.append("</TD></TR><!--End Records Row-->")

        ret.append("<!--Start Stats Row--><TR><TD>")               
        ret.append(self.stats_table(res))
        ret.append("</TD></TR><!--End Stats Row-->")

        ret.append("<!--Start Games Row--><TR><TD>")               
        ret.append(self.games_table(res))
        ret.append("</TD></TR><!--End Games Row-->")

        ret.append("</TABLE>")
        return "\n".join(ret)


### tests and demos ####

def test_query(sdb):
    print sdb.sdb_query("(date,t:goals,team,o:team)@season=2009")


def test_summary(sdb):
    Q = Query_Summary(headers=sdb.headers)
    print "Q.s:",Q.select()
    res = sdb.sdb_query(Q.select()+'@'+"team[0]=C and overtime")
    print res
    #return 
    html = ''
    for r in res:
            html += Q.output(r,**{'query_title':' '.join(r.name[-1])})
    open("/tmp/sdb.html",'w').write(html)
    #print html

def test_records(sdb):
    Q = Query_Records(headers=sdb.headers,ou=1)
    res = sdb.sdb_query(Q.select() + '@team[0]=A and site')
    print res
    #return 
    html =  Q.output(res)
    open("/tmp/sdb.html",'w').write(html)
    #print html





if __name__ == "__main__":
    #from nhl_dt import loader
    #sdb = loader()
    test_summary(sdb)
    #test_records(sdb)



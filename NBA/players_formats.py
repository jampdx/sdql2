import PyQL.outputs
import urllib,cgi
import S2.common_methods
import S2.short_cuts


 
class Query:

    def __init__(self,headers,**kwargs):
        self.headers = headers
        self.line = kwargs.get('line',1)
        self.total = kwargs.get('total',1)
        
    def key_to_query_link(self,key,**kwargs):
        kwargs["page"] = "players_query"
        return S2.common_methods.key_to_query_link(key,**kwargs)
    
    def output_html(self,res):
        return PyQL.outputs.html(res,border=0)
    output = output_html

class Query_Records(Query):
    def __init__(self,headers,**kwargs):
        Query.__init__(self,headers,**kwargs)
        self.n_rows = kwargs.get("n_rows",100) 

    def select(self):
        select = ''
        select = "Count(minutes>0) as 'Games',"
        select += "A(minutes,format='%0.1f') as 'Minutes',"
        select += "A(points,format='%0.1f') as 'Points',"
        select += "A(field goals made,format='%0.1f') as 'FGs',"
        #select += "S(100.*field goals made)/S(field goals attempted,format='%0.1f') as 'FG%',"
        select += "A(three pointers made,format='%0.1f') as 'Threes',"        
        #select += "S(100.*three pointers made)/S(three pointers attempted,format='%0.1f') as '3s%',"
        #select += "A(free throws made,format='%0.1f') as '&nbsp;Free<BR>Throws',"        
        #select += "S(100.*free throws made)/S(free throws attempted,format='%0.1f') as 'FT%',"
        select += "A(blocks,format='%0.1f') as 'Blocks',"
        select += "A(rebounds,format='%0.1f') as 'Rbnds',"
        #select += "A(fouls,format='%0.1f') as 'Fouls',"
        select += "A(assists,format='%0.1f') as 'Assists',"
        select += "A(steals,format='%0.1f') as 'Steals',"
        select += "A(turnovers,format='%0.1f') as 'TrnOvrs',"
        select +=  S2.short_cuts.expand('A(FP)',sport='nba') + " as 'FP',"
        select +=  "'%0.1f'%(Sum("+S2.short_cuts.expand('A(FP)',sport='nba') + ")/Sum(minutes),) as 'FP&#47;Min',"
        return select[:-1]

    def output(self,res):
        res = PyQL.outputs.auto_reduce(res, self.key_to_query_link) 
        return PyQL.outputs.html(res,border=0)


class Query_Summary(Query_Records):

    records_select = Query_Records.select
    def __init__(self,headers,**kwargs):
        Query_Records.__init__(self,headers,**kwargs)
        self.show_unplayed = int(kwargs.get("show_unplayed",10))
        self.show_games = int(kwargs.get("show_games",20))
        
    def stats_select(self):
        select = ("self.nice_date(date,abbreviate_month=1,abbreviate_year=0) as 'Date'," +
                "self.games.day_from_date(date)[:3] as Day," +
                "season as Season," +
                "site as Site," +
                "team as Team," +
                "o:team as Opp," +
                "'%s-%s'%(team:points,team:o:points) as Final," +
                "name as Name," +
                "'%0.1f'%(minutes,) as Minutes," +
                "points as Points," +
                #"field goals made as FGs,"
                "three pointers made as 'Threes',"
                #"free throws made as FTs,"
                 "blocks as 'Blocks',"
                 "rebounds as 'Rbnds',"
                 # "fouls as 'Fouls',"
                  "assists as 'Assists',"
                  "steals as 'Steals',"
                  "turnovers as 'TrnOvrs',"+
                  S2.short_cuts.expand('FP',sport='nba') + ","
                  )
        if self.line: select += "line as Line," 
        if self.total: select += "total as Total," 
        select += "overtime as ot"
        return select
    
    def select(self):
        self.first_games_select = "Date"
        self.score_offset = "Final"
        select =  self.records_select() + "," + self.stats_select()
        #print "select:",select
        return select


    def stats_table(self,res): 
        select = [] # select is the header row
        select.append("<table><tr><th></th>") # upper left column is blank
        start_column = 0 # res.offset_from_header(self.first_summary_select)
        stop_column = res.offset_from_header(self.first_games_select)
        player = ["<tr><th>Summary</th>"]
        for i in range(start_column,stop_column):
            #print "i,head",i,res.headers[i]
            select.append("<th>%s</th>"%(res.headers[i],)) #.split(':',1)[1],))
            player.append("<td align=center>%s</td>"%(res[i],))
        select.append("</tr>")
        select += player 
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
        print "scores:",scores
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
        #ret.append("<!--Start Records Row--><TR><TD>")               
        #ret.append(self.records_table(res))
        #ret.append("</TD></TR><!--End Records Row-->")

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

        
    #def output(self,res,**kwargs):
        #return PyQL.outputs.html(res,border=0)

        


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
    res = sdb.sdb_query(Q.select() + '@name and team=Heat')
    print res
    #return
    Q.sort = 0
    html =  Q.output(res)
    open("/tmp/sdb.html",'w').write(html)
    #print html

def test_summary(sdb):
    Q = Query_Summary(headers=sdb.headers,ou=1)
    res = sdb.sdb_query(Q.select() + '@H and season=2011 and team=Bulls and name=Carlos Boozer')
    print res
    #return 
    html = ''
    for r in res:
        html += Q.output(r,**{'query_title':' '.join(r.name[-1])})
    open("/tmp/sdb.html",'w').write(html)
    #print html




if __name__ == "__main__":
    import sys
    from NBA.loader import nba
    test_summary(nba.players)
    #test_records(nba.players)

    #1.*S(points),date,name@name and team=Bulls and season=2011|Max($1),R($2),R($3)@$2[-1]

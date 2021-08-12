import PyQL.outputs
import urllib,cgi
import S2.common_methods
import NHL.formats


Query_Records = {} # for easy of access from query.py
Query_Summary = {}
DATE = "Date"  # used as a delimitor so better to define it once.
GAMES = "Games"  # used as a delimitor so better to define it once.


class Query_Records_Player(NHL.formats.Query_Records):
    def __init__(self,headers,**kwargs):
        self.show_unplayed = int(kwargs.get("show_unplayed",10))
        self.show_games = int(kwargs.get("show_games",20))

        kwargs.setdefault('show_teasers',0)
        NHL.formats.Query_Records.__init__(self,headers,**kwargs)
        self.records_select = NHL.formats.Query_Records.select(self)
        self.games_select = ("self.nice_date(date,abbreviate_month=1,abbreviate_year=0) as '%s',"%DATE +
                "self.games.box_link(date,gid) as 'Link',"      +            
                "day as 'Day'," +
                "season as 'Season'," +
                "team as 'Team'," +
                "name as 'Name'," +
                "o:team as 'Opp'," +
                "site as 'Site'") # mind your commas
  
class Query_Summary_Player(Query_Records_Player,NHL.formats.Query_Summary):
    def __init__(self,headers,**kwargs):
        Query_Records_Player.__init__(self,headers,**kwargs)
    def output(self,res,**kwargs):
        # a custom output built by splitting the result along known names
        doffset = res.offset_from_header(DATE)
        goffset = res.offset_from_header(GAMES)
        head = val = ''
        #print "player_formats.offsets:",goffset,doffset
        for s in range(goffset,doffset):
            head += "<th>%s</th>"%res.headers[s]
            val += "<td align='center'>%s</td>"%res.data[s]
        summary = "<table><caption>Player Averages</caption><tr>%s</tr><tr>%s</tr></table>"%(head,val)
        records = NHL.formats.Query_Summary.records_table(self,res)
        # shorten the res and take advantage of a default output method.
        res.data = res.data[doffset:]
        res.headers = res.headers[doffset:]
        games =  PyQL.outputs.html(res,border=0,show=self.show_games,caption='Games')
        return records + '<p>' + summary + '<p>' + games 


class Query_Records_Skaters(Query_Records_Player):
    
    def __init__(self,headers,**kwargs):
        Query_Records_Player.__init__(self,headers,**kwargs)
        #self.n_rows = kwargs.get("n_rows",100) 
      
    def select(self):
        select = "S(1,format='%%d') as '%s',"%GAMES
        select += "A(minutes,format='%0.1f') as 'Min',"
        select += "A(goals,format='%0.1f') as Goals,"
        select += "A(penalty minutes,format='%0.1f') as Pen Mins,"
        select += "A(points,format='%0.1f') as Points,"
        select += "A(shots on goal,format='%0.1f') as Shots,"
        return select[:-1]
Query_Records["skater"] = Query_Records_Skaters

class Query_Summary_Skaters(Query_Summary_Player,Query_Records_Skaters):
    
    def __init__(self,headers,**kwargs):
        Query_Records_Skaters.__init__(self,headers,**kwargs)
        self.records_select = self.records_select.replace("o:goals","Team:o:goals").replace("t:goals","Team:t:goals")
        
    def select(self):
        select = ( self.records_select + ',' + Query_Records_Skaters.select(self) + "," + self.games_select + ',' +
        #select = ( Query_Records_Skaters.select(self) + "," + self.games_select + ',' +
                "Column(minutes,format='%0.1f') as 'Minutes'," +
                "goals as 'Goals',"
                "assists as 'Assists',"
                   "points as 'Points'," 
                  )
        select = select[:-1]
        #print "QRS.select:",select
        return select
    

Query_Summary["skater"] = Query_Summary_Skaters




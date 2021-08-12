import PyQL.outputs
import urllib,cgi
import S2.common_methods
import NFL.player_formats


Query_Records = {} # for easy of access from query.py
Query_Summary = {}


Query_Records = NFL.player_formats.Query_Records
Query_Summary = NFL.player_formats.Query_Summary


class Query_Records_Defense(NFL.player_formats.Query_Records_Player):
    def __init__(self,headers,**kwargs):
        NFL.player_formats.Query_Records_Player.__init__(self,headers,**kwargs)
        self.parameters = ["deflections", "interceptions", "sacks", "tackles"]
        self.niced = {}

    def select(self):
        select = ''
        select = "S(1,format='%d') as 'Games',"
        for p in self.parameters:
            select += "A(%s,format='%%0.1f') as '%s',"%(p,self.niced.get(p,p.title()))
        return select[:-1]
Query_Records["defense"] = Query_Records_Defense

class Query_Summary_Defense(NFL.player_formats.Query_Summary_Player,Query_Records_Defense):
    def __init__(self,headers,**kwargs):
        Query_Records_Defense.__init__(self,headers,**kwargs)
        NFL.player_formats.Query_Summary_Player.__init__(self,headers,**kwargs)
        
    def select(self):
        select = self.records_select + ',' + Query_Records_Defense.select(self) + "," + self.games_select + ','
        for p in self.parameters:
            select += "%s as '%s',"%(p,self.niced.get(p,p.title()))
        select = select[:-1]
        return select
Query_Summary["defense"] = Query_Summary_Defense        


















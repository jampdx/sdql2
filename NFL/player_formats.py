import PyQL.outputs
import urllib,cgi
import S2.common_methods
import NFL.formats


Query_Records = {} # for easy of access from query.py
Query_Summary = {}
DATE = "Date"  # used as a delimitor so better to define it once.
GAMES = "Games"  # used as a delimitor so better to define it once.


class Query_Records_Player(NFL.formats.Query_Records):
    def __init__(self,headers,**kwargs):
        kwargs.setdefault('show_teasers',0)
        self.show_unplayed = int(kwargs.get("show_unplayed",10))
        self.show_games = int(kwargs.get("show_games",20))

        NFL.formats.Query_Records.__init__(self,headers,**kwargs)
        self.records_select = NFL.formats.Query_Records.select(self)
        self.games_select = ("self.nice_date(date,abbreviate_month=1,abbreviate_year=0) as '%s',"%DATE +
                "self.games.box_link(_gid,season,week,team,o:team,site) as 'Link',"      +
                "day as 'Day'," +
                "season as 'Season'," +
                "team as 'Team'," +
                "name as 'Name'," +
                "o:team as 'Opp'," +
                "site as 'Site'") # mind your commas

class Query_Summary_Player(Query_Records_Player,NFL.formats.Query_Summary):
    def __init__(self,headers,**kwargs):
        Query_Records_Player.__init__(self,headers,**kwargs)
    def output(self,res,**kwargs):
        # a custom output built by splitting the result along known names
        doffset = res.offset_from_header(DATE)
        goffset = res.offset_from_header(GAMES)
        head = val = ''
        for s in range(goffset,doffset):
            head += "<th>%s</th>"%res.headers[s]
            val += "<td align='center'>%s</td>"%res.data[s]
        summary = "<table><caption>Player Averages</caption><tr>%s</tr><tr>%s</tr></table>"%(head,val)
        records = NFL.formats.Query_Summary.records_table(self,res)
        # shorten the res and take advantage of a default output method.
        res.data = res.data[doffset:]
        res.headers = res.headers[doffset:]
        games =  PyQL.outputs.html(res,border=0,show=self.show_games,caption='Games')
        return records + '<p>' + summary + '<p>' + games

class Query_Records_Rushing(Query_Records_Player):

    def __init__(self,headers,**kwargs):
        Query_Records_Player.__init__(self,headers,**kwargs)
        #self.n_rows = kwargs.get("n_rows",100)

    def select(self):# longest rush, name, rushes, rushing touchdowns, rushing yards
        select = ''
        select = "S(1,format='%%d') as '%s',"%GAMES
        select += "A(rushes,format='%0.1f') as 'Rushes',"
        select += "A(rushing yards,format='%0.1f') as 'Rushing Yards',"
        select += "S(rushing yards)/S(rushes,format='%0.1f') as 'Yards per Rush',"
        select += "A(rushing touchdowns,format='%0.1f') as 'Rushing TDs',"
        select += "A(longest rush,format='%0.1f') as 'Longest',"
        return select[:-1]
Query_Records["rushing"] = Query_Records_Rushing

class Query_Summary_Rushing(Query_Summary_Player,Query_Records_Rushing):

    def __init__(self,headers,**kwargs):
        Query_Records_Rushing.__init__(self,headers,**kwargs)

    def select(self):
        select = ( self.records_select + ',' + Query_Records_Rushing.select(self) + "," + self.games_select + ',' +
                "rushes as 'Rushes'," +
                "rushing yards as 'Rush Yds'," +
                "Column(1.*rushing yards/rushes,format='%0.1f') as 'Yds/Rush'," +
                "rushing touchdowns as 'Rush TDs'," +
                  "longest rush as 'Longest',"
                  )
        select = select[:-1]
        return select
Query_Summary["rushing"] = Query_Summary_Rushing


class Query_Records_Receiving(Query_Records_Player):

    def __init__(self,headers,**kwargs):
        Query_Records_Player.__init__(self,headers,**kwargs)
        #self.n_rows = kwargs.get("n_rows",100)

    def select(self):# longest receiv, name, receives, receiving touchdowns, receiving yards
        select = ''
        select = "S(1,format='%%d') as '%s',"%GAMES
        select += "A(receptions,format='%0.1f') as 'Receptions',"
        select += "A(receiving yards,format='%0.1f') as 'Receiving Yards',"
        select += "S(receiving yards)/S(receptions,format='%0.1f') as 'Yards per Recep',"
        select += "A(receiving touchdowns,format='%0.1f') as 'Receiving TDs',"
        select += "A(longest reception,format='%0.1f') as 'Longest',"
        return select[:-1]
Query_Records["receiving"] = Query_Records_Receiving

class Query_Summary_Receiving(Query_Summary_Player,Query_Records_Receiving):

    def __init__(self,headers,**kwargs):
        Query_Records_Receiving.__init__(self,headers,**kwargs)
        Query_Summary_Player.__init__(self,headers,**kwargs)

    def select(self):
        select = ( self.records_select + ',' + Query_Records_Receiving.select(self) + "," + self.games_select + ',' +
                "receptions as 'Receptions'," +
                "receiving yards as 'Receiving Yds'," +
                "Column(1.*receiving yards/receptions,format='%0.1f') as 'Yds/Reception'," +
                "receiving touchdowns as 'Receiving TDs'," +
                  "longest reception as 'Longest',"
                  )
        select = select[:-1]
        return select
Query_Summary["receiving"] = Query_Summary_Receiving


# completions, interceptions, interceptions thrown, name, passes, passing touchdowns, passing yards
class Query_Records_Passing(Query_Records_Player):
    def __init__(self,headers,**kwargs):
        Query_Records_Player.__init__(self,headers,**kwargs)

    def select(self):
        select = ''
        select = "S(1,format='%%d') as '%s',"%GAMES
        select += "A(passes,format='%0.1f') as 'Passes',"
        select += "A(passing yards,format='%0.1f') as 'Passing Yards',"
        select += "S(passing yards)/S(passes,format='%0.1f') as 'Yards per Pass',"
        select += "A(passing touchdowns,format='%0.1f') as 'Passing TDs',"
        select += "A(interceptions thrown,format='%0.1f') as 'Ints',"
        return select[:-1]
Query_Records["passing"] = Query_Records_Passing

class Query_Summary_Passing(Query_Summary_Player,Query_Records_Passing):

    def __init__(self,headers,**kwargs):
        Query_Records_Passing.__init__(self,headers,**kwargs)
        Query_Summary_Player.__init__(self,headers,**kwargs)

    def select(self):
        select = ( self.records_select + ',' + Query_Records_Passing.select(self) + "," + self.games_select + ',' +
                "passes as 'Passes'," +
                "passing yards as 'Pass Yds'," +
                "Column(1.*passing yards/passes,format='%0.1f') as 'Yds/Pass'," +
                "passing touchdowns as 'Pass TDs'," +
                "interceptions thrown as 'Ints',"
                  )
        select = select[:-1]
        return select
Query_Summary["passing"] = Query_Summary_Passing

class Query_Records_Kickoff_Returns(Query_Records_Player):
    def __init__(self,headers,**kwargs):
        Query_Records_Player.__init__(self,headers,**kwargs)

    def select(self):
        select = ''
        select = "S(1,format='%d') as 'Games',"
        select += "A(kickoff returns,format='%0.1f') as 'KO Returns',"
        select += "S(average kickoff return*kickoff returns)/S(kickoff returns,format='%0.1f') as 'KO Ret Yds',"
        select += "A(kickoff return touchdowns,format='%0.1f') as 'KO Ret TDs',"
        select += "A(longest kickoff return,format='%0.1f') as 'Longest',"
        return select[:-1]
Query_Records["kickoff_returns"] = Query_Records_Kickoff_Returns

class Query_Summary_Kickoff_Returns(Query_Summary_Player,Query_Records_Kickoff_Returns):

    def __init__(self,headers,**kwargs):
        Query_Records_Kickoff_Returns.__init__(self,headers,**kwargs)
        Query_Summary_Player.__init__(self,headers,**kwargs)

    def select(self):
        select = ( self.records_select + ',' + Query_Records_Kickoff_Returns.select(self) + "," + self.games_select + ',' +
                "kickoff returns as 'KO Rets'," +
                "average kickoff return as 'KO Ret Yds'," +
                "kickoff return touchdowns as 'KO Ret TDs'," +
                "longest kickoff return as 'Longest',"
                  )
        select = select[:-1]
        return select
Query_Summary["kickoff_returns"] = Query_Summary_Kickoff_Returns

# field goals, field goals attempted, kicking extra points, kicking extra points attempted, longest field goal
class Query_Records_Kicking(Query_Records_Player):
    def __init__(self,headers,**kwargs):
        Query_Records_Player.__init__(self,headers,**kwargs)

    def select(self):
        select = ''
        select = "S(1,format='%d') as 'Games',"
        select += "A(field goals,format='%0.1f') as 'FieldGoals',"
        select += "S(100*field goals)/S(field goals attempted,format='%0.1f') as 'FG %',"
        select += "A(kicking extra points,format='%0.1f') as 'PATs',"
        select += "S(100*kicking extra points)/S(kicking extra points attempted,format='%0.1f') as 'PAT %',"
        select += "A(longest field goal,format='%0.1f') as 'Longest',"
        return select[:-1]
Query_Records["kicking"] = Query_Records_Kicking

class Query_Summary_Kicking(Query_Summary_Player,Query_Records_Kicking):

    def __init__(self,headers,**kwargs):
        Query_Records_Kicking.__init__(self,headers,**kwargs)
        Query_Summary_Player.__init__(self,headers,**kwargs)

    def select(self):
        select = ( self.records_select + ',' + Query_Records_Kicking.select(self) + "," + self.games_select + ',' +
                "field goals as 'FGs'," +
                "field goals attempted - field goals as 'Missed FGs'," +
                "kicking extra points as 'PATs'," +
                "kicking extra points attempted - kicking extra points as 'Missed PATs'," +
                "longest field goal as 'Longest',"
                  )
        select = select[:-1]
        return select
Query_Summary["kicking"] = Query_Summary_Kicking


class Query_Records_Punt_Returns(Query_Records_Player):
    def __init__(self,headers,**kwargs):
        Query_Records_Player.__init__(self,headers,**kwargs)

    def select(self):
        select = ''
        select = "S(1,format='%d') as 'Games',"
        select += "A(punt returns,format='%0.1f') as 'KO Returns',"
        select += "S(average punt return*punt returns)/S(punt returns,format='%0.1f') as 'KO Ret Yds',"
        select += "A(punt return touchdowns,format='%0.1f') as 'KO Ret TDs',"
        select += "A(longest punt return,format='%0.1f') as 'Longest',"
        return select[:-1]
Query_Records["punt_returns"] = Query_Records_Punt_Returns

class Query_Summary_Punt_Returns(Query_Summary_Player,Query_Records_Punt_Returns):

    def __init__(self,headers,**kwargs):
        Query_Records_Punt_Returns.__init__(self,headers,**kwargs)
        Query_Summary_Player.__init__(self,headers,**kwargs)

    def select(self):
        select = ( self.records_select + ',' + Query_Records_Punt_Returns.select(self) + "," + self.games_select + ',' +
                "punt returns as 'KO Rets'," +
                "average punt return as 'KO Ret Yds'," +
                "punt return touchdowns as 'KO Ret TDs'," +
                "longest punt return as 'Longest',"
                  )
        select = select[:-1]
        return select
Query_Summary["punt_returns"] = Query_Summary_Punt_Returns

# average punt yards, longest punt, name, punts, punts inside the twenty
class Query_Records_Punting(Query_Records_Player):
    def __init__(self,headers,**kwargs):
        Query_Records_Player.__init__(self,headers,**kwargs)

    def select(self):
        select = ''
        select = "S(1,format='%d') as 'Games',"
        select += "A(punts,format='%0.1f') as 'Punts',"
        select += "S(average punt yards*punts)/S(punts,format='%0.1f') as 'PuntYds',"
        select += "A(punts inside the twenty,format='%0.1f') as 'InsideThe20',"
        return select[:-1]
Query_Records["punting"] = Query_Records_Punting

class Query_Summary_Punting(Query_Summary_Player,Query_Records_Punting):

    def __init__(self,headers,**kwargs):
        Query_Records_Punting.__init__(self,headers,**kwargs)
        Query_Summary_Player.__init__(self,headers,**kwargs)

    def select(self):
        select = ( self.records_select + ',' + Query_Records_Punting.select(self) + "," + self.games_select + ',' +
                "punts as 'Punts'," +
                "average punt yards as 'AvgYds'," +
                "punts inside the twenty as 'InsideThe20'," +
                "longest punt as 'Longest',"
                  )
        select = select[:-1]
        return select
Query_Summary["punting"] = Query_Summary_Punting

class Query_Records_Fumbles(Query_Records_Player):
    def __init__(self,headers,**kwargs):
        Query_Records_Player.__init__(self,headers,**kwargs)

    def select(self):
        select = ''
        select = "S(1,format='%d') as 'Games',"
        select += "A(fumbles,format='%0.1f') as 'Fumbles',"
        select += "A(fumbles lost,format='%0.1f') as 'Lost',"
        select += "A(fumbles recovered,format='%0.1f') as 'Recoverd',"
        select += "A(fumble yards,format='%0.1f') as 'Yards',"
        return select[:-1]
Query_Records["fumbles"] = Query_Records_Fumbles

class Query_Summary_Fumbles(Query_Summary_Player,Query_Records_Fumbles):

    def __init__(self,headers,**kwargs):
        Query_Records_Fumbles.__init__(self,headers,**kwargs)
        Query_Summary_Player.__init__(self,headers,**kwargs)

    def select(self):
        select = ( self.records_select + ',' + Query_Records_Fumbles.select(self) + "," + self.games_select + ',' +
                "fumbles as 'Fumbles'," +
                  "fumbles lost as 'Lost'," +
                "fumbles recovered as 'Recovered'," +
                  "fumble yards as 'Yards',"
                  )
        select = select[:-1]
        return select
Query_Summary["fumbles"] = Query_Summary_Fumbles

class Query_Records_Defense(Query_Records_Player):
    def __init__(self,headers,**kwargs):
        Query_Records_Player.__init__(self,headers,**kwargs)
        self.parameters = "tackles","tackle assists","sacks","forced fumbles","interceptions"
        self.niced = {"tackle assists":"Assists"}

    def select(self):
        select = ''
        select = "S(1,format='%d') as 'Games',"
        for p in self.parameters:
            select += "A(%s,format='%%0.1f') as '%s',"%(p,self.niced.get(p,p.title()))
        return select[:-1]
Query_Records["defense"] = Query_Records_Defense

class Query_Summary_Defense(Query_Summary_Player,Query_Records_Defense):
    def __init__(self,headers,**kwargs):
        Query_Records_Defense.__init__(self,headers,**kwargs)
        Query_Summary_Player.__init__(self,headers,**kwargs)

    def select(self):
        select = self.records_select + ',' + Query_Records_Defense.select(self) + "," + self.games_select + ','
        for p in self.parameters:
            select += "%s as '%s',"%(p,self.niced.get(p,p.title()))
        select = select[:-1]
        return select
Query_Summary["defense"] = Query_Summary_Defense

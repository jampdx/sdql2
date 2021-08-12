import PyQL.columns
import PyQL.py_tools
import string
import os, sys, imp

from NCAAFB.directory import DATA_DIR

def main_is_frozen():
    return (hasattr(sys, "frozen") or # new py2exe
        hasattr(sys, "importers") # old py2exe
            or imp.is_frozen("__main__")) # tools/freeze

def get_main_dir():
    if main_is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.realpath(__file__))



import UserDict
class look_back_dict(UserDict.UserDict):
    def __init__(self,d={}):
        UserDict.UserDict.__init__(self,d)
    def look_back_get(self,key,default=None):
        #print "look_back_dict.key:",key,type(key)
        if key in self.keys(): return self[key]
        elif 1979<key: return self.look_back_get(key-1,default)  
        else: return default
    

def conference_dict():
    d = {} # d[team][season]=conf
    for line in map(string.strip,open(os.path.join(DATA_DIR,"team_conference")).readlines()[1:]):
        if not string.strip(line): continue
        #print line
        abbr,season,conf = map(string.strip,string.split(line,'\t'))
        if not d.has_key(abbr): 
            d[abbr] = look_back_dict()
        d[abbr][int(season)] = conf
    return d

def team_dict():
    d = {}
    division = "1A"
    for line in map(string.strip,open(os.path.join(DATA_DIR,"team_abbreviations")).readlines()):
        if not '-' in line: continue
        if line == 'Here are the 1-AA "TEAM" and "OPP" codes:':
            division = "1AA"
        abbr,name = map(string.strip,string.split(line,'-',1))
        #print line,division,abbr,name
        if d.has_key(abbr): raise "%s is already an abbr"%abbr
        d[abbr] = (name,division)
    return d

def season_from_date(date):
    sdate = str(date)
    season = int(sdate[:4])
    if sdate[4]=='0' and sdate[5] in "123": season = season - 1
    return season

def add_season(dt):
    dt.season_from_date = season_from_date
    nice = dt.query("self.season_from_date(date) as season@1")[0]
    for col in nice:
        print "adding nice column:",col.name
        dt.add_object(col)        
    del dt.season_from_date

def add_nice_fields(dt):
    dt.day_from_date = PyQL.py_tools.day_from_date
    dt.conference_d = conference_dict()
    dt.team_d = team_dict()
    dt.look_back_dict = look_back_dict
    nice = dt.query("points-o:points as margin,points+line-o:points as ats margin,points-total+o:points as ou margin,self.day_from_date(date) as day,self.team_d.get(team,('',''))[0] as 'full name',self.team_d.get(team,('',''))[1] as 'division',self.conference_d.get(team,self.look_back_dict()).look_back_get(season,'') as conference@1")[0]
    for col in nice:
        print "adding nice column:",col.name
        if col.name in ["ats margin","ou margin"]:
            col.str_format = """lambda line:"%s%d%s"%('+'*(0<line) + '-'*(line<0),int(abs(line)),"'"*(line!=int(line)))"""
            # """ '''
        dt.add_object(col)        
    del dt.day_from_date
    #del dt.conference_d
    del dt.team_d
    
def add_game_dates(dt):  ## looks into key to get season - needs update for 2.0

    res = dt.query("date@season and team and site and game type='RS'")
    for i in range(len(res)):
        header = res.headers[i]
        #print header
        season = int(header[0][-4:])
        team = string.strip(string.replace(header[2][5:-1],"'",''))
        site = string.strip(string.replace(header[4][5:-1],"'",''))
        #print season,team,site
        #print res[i].data
        dt.game_dates[(season,team,site)] = res.data[i][0]
        

def add_ytd_fields(dt):

    if "wins" in dt.headers:
        print "ytd fields aleady built"
        return
    dt.game_dates = {} #[(season,team,site)] = [dates]    
    len_data = len(dt.data[0])
    dt.game_dates = {}
    dt.add_object(PyQL.columns.Column(name='game number',format="%d",data=[None]*len_data))
    dt.add_object(PyQL.columns.Column(name='wins',format="%d",data=[None]*len_data))
    dt.add_object(PyQL.columns.Column(name='losses',format="%d",data=[None]*len_data))
    dt.add_object(PyQL.columns.Column(name='opponents',format="%s",data=[None]*len_data)) # list of ytd opps

    record = {} #record[team]=[w,l,p]
    games = {}   #games[team] = count
    opponents = {} #opponents[team] = [list of ytd opponents]
    p = dt.offset_from_header("previous game")        
    season_offset = dt.offset_from_header("season")
    games_offset = dt.offset_from_header("game number")
    wins_offset = dt.offset_from_header("wins")
    losses_offset = dt.offset_from_header("losses")
    opponents_offset = dt.offset_from_header("opponents")
    team_offset = dt.offset_from_header("team")
    site_offset = dt.offset_from_header("site")
    date_offset = dt.offset_from_header("date")
    points_offset = dt.offset_from_header("points")         
    for row in range(len_data):
        date = dt.data[date_offset][row]
        season = season_from_date(date)
        site = dt.data[site_offset][row]
        team_name = dt.data[team_offset][row]
        dt.game_dates.setdefault((season,team_name,site),[])
        dt.game_dates[(season,team_name,site)].append(date)        
        p_row = dt.data[p][row]
        if p_row is not None and dt.data[season_offset][row] != dt.data[season_offset][p_row]:
            record[team_name] = [0,0,0]
            games[team_name] = 0
            opponents[team_name] = []
        #if p_row is not None and dt.data[dt.games.stats_offset][p_row] is None:
        #    continue # 2nd not played - leave the wins/losses as None
        record.setdefault(team_name,[0,0,0])
        games.setdefault(team_name,0)
        opponents.setdefault(team_name,[])
        games[team_name] += 1
        dt.data[games_offset][row] = games[team_name] 
        dt.data[wins_offset][row] = record[team_name][0]
        dt.data[losses_offset][row] = record[team_name][1] 
        dt.data[opponents_offset][row] = opponents[team_name][:] 
        #print "setting wins, losses for ",team_name,record[team_name]
        o_row = row + 1 - 2*(row%2)
        opp_name = dt.data[team_offset][o_row]
        opponents[team_name].append(opp_name)            

        points = dt.data[points_offset][row]
        o_points = dt.data[points_offset][o_row]
        if None in [points,o_points]: continue # not played        
        #print "points,o:p;oint",points,o_points
        #print "record:",record[team_name]
        record[team_name][points<o_points + 2*(points==o_points)] += 1

def set_types(dt):
    date_offset = dt.offset_from_header("date")
    if isinstance(dt.data[date_offset].data[0],PyQL.py_tools.Date8):
        print "date is already a Date8"
        return        
    dt.data[date_offset].data = map(lambda x,convert=PyQL.py_tools.Date8:convert(x),dt.data[date_offset].data)
    for offset in range(len(dt.data)):
        if dt.data[offset].str_format == '%dXXX':
            print "converting",dt.headers[offset]
            for i in range(len(dt.data[offset].data)):
                if dt.data[offset].data[i] is not None:
                    dt.data[offset].data[i] = PyQL.py_tools.Int_fdiv(dt.data[offset].data[i])

  
def add_reference_fields(dt):
    reference_fields =  [("previous game","%s"),("previous match up","%s"),
                       ("next game","%s"),("next match up","%s"),
                       ("rest","%s")]
    n_games = len(dt[0])    
    for field in reference_fields:
        dt.add_object(PyQL.columns.Column(name=field[0],format=field[1],data=[None]*n_games))

    team = {} #team[team] = [game1,game2,...]
    team_opp = {} #team[team][opp number] = [game1,game2,...]        
    team_offset = dt.offset_from_header("team")

    #go through games to build team and team_opp dictionaries
    for row in range(len(dt[0])):
        team_name = dt[team_offset][row]
        opp_name = dt[team_offset][row + 1 - 2*(row%2)]            
        team.setdefault(team_name,[]).append(row)
        team_opp.setdefault(team_name,{})
        team_opp[team_name].setdefault(opp_name,[]).append(row)
        #print "row,team,opp:",row,team_number,opp_number
    # through games to set previous game and previous match up
    p = dt.offset_from_header("previous game")
    P = dt.offset_from_header("previous match up")
    rest = dt.offset_from_header("rest")        
    date = dt.offset_from_header("date") # for reading in                    
    team_pointer = {}
    mup_pointer = {}
    for row in range(len(dt[0])):
        # previous game
        team_name = dt[team_offset][row]
        opp_name = dt[team_offset][row + 1 - 2*(row%2)]            
        pointer = team_pointer.setdefault(team_name,0) - 1
        #print "row,pointer:",row,pointer
        if 0<=pointer:
            p_row = team[team_name][pointer]
            dt.data[p][row] = p_row
            #print "date,row,p_row:",dt[date][row],date,row,p_row            
            dt.data[rest][row] = PyQL.py_tools.delta_days(dt[date][row],dt[date][p_row]) - 1
        team_pointer[team_name] += 1 
        # previous match up
        mup_pointer.setdefault(team_name,{})            
        pointer = mup_pointer[team_name].setdefault(opp_name,0) - 1
        if 0<=pointer:
            P_row = team_opp[team_name][opp_name][pointer]
            dt.data[P][row] = P_row
        mup_pointer[team_name][opp_name] += 1

    # through games to set next game and next match up
    n = dt.offset_from_header("next game")

    N = dt.offset_from_header("next match up")        
    team_pointer = {}
    mup_pointer = {}
    for row in range(n_games-1,-1,-1):
        # next game
        team_name = dt[team_offset][row]
        pointer = team_pointer.setdefault(team_name,len(team[team_name])) 
        #print "row,pointer:",row,pointer
        if pointer<len(team[team_name]):
            dt.data[n][row] = team[team_name][pointer]
        team_pointer[team_name] -= 1
        # next match up
        opp_name = dt[team_offset][row + 1 - 2*(row%2)]            
        mup_pointer.setdefault(team_name,{})            
        pointer = mup_pointer[team_name].setdefault(opp_name,
                                                      len(team_opp[team_name][opp_name])) 
        if pointer<len(team_opp[team_name][opp_name]):
            dt.data[N][row] = team_opp[team_name][opp_name][pointer]
        mup_pointer[team_name][opp_name] -= 1

 


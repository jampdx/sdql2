# This file:
#     builds reference and nice fields
# Goals:
#     Handle custom client data 

import sys, os, re, string
sys.path[:0] = ["/home/jameyer/S2/NFL/Source"] #for emacs testing
import nfl_date_tools
from snf import d as SNF
from grass import d as GRASS
from time_zones import time_zones as TIME_ZONES
from teams import division as DIVISION
import PyQL.py_tools
import PyQL.columns

def add_season_site(dt):
    dt.season_from_date = season_from_date
    nice = dt.query("self.season_from_date(date) as season,{0:'home',1:'away'}[_i%2] as site@1")[0]
    for col in nice:
        print "adding nice column:",col.name
        dt.add_object(col)        
    del dt.season_from_date



def season_from_date(date):
    sdate = str(date)
    season = int(sdate[:4])
    if sdate[4]=='0' and sdate[5] in "123": season = season - 1
    return season

def add_reference_fields(nfl):
    reference_fields =  [("previous game","%s"),("previous match up","%s"),
                       ("next game","%s"),("next match up","%s"),
                       ("rest","%s"),("opponents","%s")]
    n_games = len(nfl[0])    
    for field in reference_fields:
        nfl.add_object(PyQL.columns.Column(name=field[0],format=field[1],data=[None]*n_games))

    
    n_games = len(nfl.data[0])
    team = {} #team[team] = [game1,game2,...]
    team_opp = {} #team[team][opp number] = [game1,game2,...]        
    team_offset = nfl.offset_from_header("team")
    opponents = {} # opponents[team] = [list of year-to-date opponents]
    season_offset = nfl.offset_from_header("season")     
    opps = nfl.offset_from_header("opponents")
    #go through games to build team and team_opp dictionaries
    last_season = 0
    for row in range(len(nfl[0])):
        current_season = nfl[season_offset][row]
        if last_season != current_season:
            last_season=current_season
            opponents = {}
        team_name = nfl[team_offset][row]
        opp_name = nfl[team_offset][row + 1 - 2*(row%2)]            
        team.setdefault(team_name,[]).append(row)
        team_opp.setdefault(team_name,{})
        team_opp[team_name].setdefault(opp_name,[]).append(row)
        nfl.data[opps][row] = opponents.get(team_name,[])[:]
        opponents.setdefault(team_name,[]).append(opp_name)
    # through games to set previous game and previous match up
    p = nfl.offset_from_header("previous game")
    P = nfl.offset_from_header("previous match up")
    opponents = nfl.offset_from_header("opponents")        
    week = nfl.offset_from_header("week") # for reading in
    season = nfl.offset_from_header("season") # for reading in
    date = nfl.offset_from_header("date") # for reading in                    
    team_pointer = {}
    mup_pointer = {}
    for row in range(len(nfl[0])):
        # previous game
        team_name = nfl[team_offset][row]
        opp_name = nfl[team_offset][row + 1 - 2*(row%2)]            
        pointer = team_pointer.setdefault(team_name,0) - 1
        if 0<=pointer:
            p_row = team[team_name][pointer]
            nfl.data[p][row] = p_row
        team_pointer[team_name] += 1 
        # previous match up
        mup_pointer.setdefault(team_name,{})            
        pointer = mup_pointer[team_name].setdefault(opp_name,0) - 1
        if 0<=pointer:
            P_row = team_opp[team_name][opp_name][pointer]
            nfl.data[P][row] = P_row
        mup_pointer[team_name][opp_name] += 1

    # through games to set next game and next match up
    n = nfl.offset_from_header("next game")

    N = nfl.offset_from_header("next match up")        
    team_pointer = {}
    mup_pointer = {}
    for row in range(n_games-1,-1,-1):
        # next game
        team_name = nfl[team_offset][row]
        pointer = team_pointer.setdefault(team_name,len(team[team_name])) 
        #print "row,pointer:",row,pointer
        if pointer<len(team[team_name]):
            nfl.data[n][row] = team[team_name][pointer]
        team_pointer[team_name] -= 1
        # next match up
        opp_name = nfl[team_offset][row + 1 - 2*(row%2)]            
        mup_pointer.setdefault(team_name,{})            
        pointer = mup_pointer[team_name].setdefault(opp_name,
                                                      len(team_opp[team_name][opp_name])) 
        if pointer<len(team_opp[team_name][opp_name]):
            nfl.data[N][row] = team_opp[team_name][opp_name][pointer]
        mup_pointer[team_name][opp_name] -= 1
    return nfl

def add_nice_fields(nfl):
    #print "adding nice headers"
    #nfl.game_dates = PyQL.py_tools.remove_duplicates(
    #      nfl.query("date@date>20100800")[0][0].data)
    #nfl.game_dates.sort()            
    nfl.SNF = SNF
    nfl.week_from_date = nfl_date_tools.find_week_from_date
    nfl.season_week_day_from_date = nfl_date_tools.find_season_week_day_from_date
    nfl.GRASS = GRASS
    nfl.TIME_ZONES = TIME_ZONES
    nfl.DIVISION = DIVISION
    nfl.streak = streak
    #nfl.show_metacode=1
    nice = nfl.query(
      "self.streak(self,_i,'su') as 'streak',"
      "self.streak(self,_i,'site') as 'site streak',"
      "self.streak(self,_i,'ats') as 'ats streak',"
      "self.streak(self,_i,'ou') as 'ou streak',"
      "points-(total-line)/2. as 'dps',"
      "o:points-(total+line)/2. as 'dpa',"
      "points-o:points as 'margin',"
      "points+line-o:points as 'ats margin',"
      "points+o:points-total as 'ou margin',"
      "interceptions+fumbles lost as 'turnovers',"
      "passes + rushes + o:sacks as 'plays',"        
      "quarter scores[0]-o:quarter scores[0] as 'margin after the first',"
      "quarter scores[0]+quarter scores[1]-o:quarter scores[0]-o:quarter scores[1] as 'margin at the half',"
      "quarter scores[0]+quarter scores[1]+quarter scores[2]-o:quarter scores[0]-o:quarter scores[1]-o:quarter scores[2] as 'margin after the third',"
      "interceptions+fumbles lost-o:interceptions-o:fumbles lost as 'turnover margin',"      
      "self.week_from_date(date) as 'week',"
      "self.season_week_day_from_date(date)[-1] as 'day',"
      "(team in self.SNF[season].get(self.week_from_date(date),[]))*1 as 'snf',"
      "{1:'grass',0:'artificial'}.get(self.GRASS.get(team*(site=='home') or o:team,{}).get(season)) as 'surface',"
      "self.DIVISION(team,season) as 'division',"
      "self.DIVISION(team,season)[:3] as 'conference',"
      "((self.week_from_date(date)>17 and season>2001) or (self.week_from_date(date)>18 and season==2001))*1 as 'playoffs',"                
      "Column(self.TIME_ZONES[team*(site=='home') or o:team],format=lambda x:`str(x)`) as 'time zone'"
      "@1")[0]

    for col in nice:
        if col.name in nfl.headers:
            print col.name,"is already a header"
            continue
        print "adding nice column:",col.name
        if col.name in ["ats margin","ou margin"]:
            col.str_format = """lambda line:"%s%d%s"%('+'*(0<line) + '-'*(line<0),int(abs(line)),"'"*(line!=int(line)))"""
            # '   this single quote helps emacs keep the syntax highlighting correct
            col.set_format(col.str_format)
        nfl.add_object(col)
    return nfl


def streak(nfl,index,flavor='su'): # for a given index in games table return the number of games won (lost) in a row
    #print "streak gets:",index,flavor
    pi = nfl.reference_dictionary['p']; Pi = nfl.reference_dictionary['P']        
    ni = nfl.reference_dictionary['n']; Ni = nfl.reference_dictionary['N']
    si = nfl.offset_from_header("site")
    points_i = nfl.offset_from_header("points")
    season_i = nfl.offset_from_header("season")
    total_i = nfl.offset_from_header("total")
    line_i = nfl.offset_from_header("line")
    i = index
    streak = 0
    while 1:
        #print "streak.i:",i
        ti = nfl.data[pi][i]  # team index
        if not ti or nfl.data[season_i][ti]!=nfl.data[season_i][i]:
            return streak # no more previous same season games
        if flavor == 'site':
            margin = 1*(nfl.data[si][ti]=='home') or -1
        elif flavor == 'su':
            margin = nfl.data[points_i][ti]-nfl.data[points_i][ti+1-2*(ti%2)]
        elif flavor == 'ou':
            margin = nfl.data[points_i][ti]+nfl.data[points_i][ti+1-2*(ti%2)]-nfl.data[total_i][ti]
        elif flavor == 'ats':
            margin = nfl.data[points_i][ti]-nfl.data[points_i][ti+1-2*(ti%2)]+nfl.data[line_i][ti]
        if margin == 0: return streak
        if  0<margin: 
            if streak<0: return streak
            streak += 1
            #print "winning streak.streak:",streak

        else: # a loss
            if 0<streak: return streak
            streak -= 1
            #print "losing streak.streak:",streak                
        i = nfl.data[pi][i]
    raise "can't get here"
 

def add_ytd_fields(dt):

    if "wins" in dt.headers:
        print "ytd fields aleady built"
        return
    len_data = len(dt.data[0])

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
    points_offset = dt.offset_from_header("points")         
    for row in range(len_data):
        team_name = dt.data[team_offset][row]            
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
        if dt.data[points_offset][row] is None: continue # not played
        points = dt.data[points_offset][row]
        o_points = dt.data[points_offset][o_row]
        record[team_name][points<o_points + 2*(points==o_points)] += 1

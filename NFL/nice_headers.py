# This file:
#     defines schema
#     load the database from the file system
#     builds reference and nice fields
# Goals:
#     Separate out trends (don't always need and they can be slow to load)
#     Update methods: pickles, gamebooks, by hand
#     Clear separation between data fields and synthetics.
#     Handle custom client data 
# TODO:
#     Don't have season in schema: use self.season_from_date(date) 

import sys, os, re, string
sys.path[:0] = ["/home/jameyer/S2/NFL/Source"] #for emacs testing
import nfl_date_tools
from snf import d as SNF
from grass import d as GRASS
from time_zones import time_zones as TIME_ZONES


def add_reference_fields(nfl):
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

def add_nice_headers(nfl):
    #print "adding nice headers"
    #nfl.game_dates = py_tools.remove_duplicates(
    #      nfl.query("date@date>20100800")[0][0].data)
    #nfl.game_dates.sort()            
    nfl.SNF = SNF
    nfl.week_from_date = nfl_date_tools.find_week_from_date
    nfl.GRASS = GRASS
    nfl.TIME_ZONES = TIME_ZONES
    nfl.show_metacode=1
    nice = nfl.query(
      "points-(total-line)/2. as dps,"
      "o:points-(total+line)/2. as dpa,"
      "points-o:points as margin,"
      "self.week_from_date(date) as week,"
      "(team in self.SNF[season].get(self.week_from_date(date),[]))*1 as snf,"
      "{1:'grass',0:'artificial'}.get(self.GRASS.get(team*(site=='home') or o:team,{}).get(season)) as surface,"
      "Column(self.TIME_ZONES[team*(site=='home') or o:team],format=lambda x:`str(x)`) as time zone"
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

nfl = NFL()
nfl = inputs.append_from_pickled(nfl,
               "/home/jameyer/S2/NFL/Data/Pickled/1989_2009",0)
nfl = add_reference_fields(nfl)
nfl.build_lexer(parameters=map(lambda x:'([pPnNto]+[.:])?'+x,nfl.headers))
nfl = add_nice_headers(nfl)
nfl.db_strings = ["Bears","Packers","Giants"]
nfl.build_lexer(parameters=map(lambda x:'([pPnNto]+[.:])?'+x,nfl.headers))
nfl.set_types()



if __name__ == "__main__":
    nfl.show_metacode  = 1 
    res = nfl.nfl_query("date,week,team,points,touchdowns,drives,dps@team='Bears' and  season=2007")
    print res
    print outputs.html(res)

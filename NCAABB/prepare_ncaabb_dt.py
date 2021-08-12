# This file:
#     builds reference and nice fields

import sys, os, re, string
import PyQL.py_tools 
import PyQL.columns

#import NCAABB.ncaabb_time_zones
#import NCAABB.ncaabb_seed
#import NCAABB.teams

def season_from_date(date): 
    date = str(date) 
    season = int(date[:4])
    if date[4] == '0': season -= 1
    return season

def XXXplayoffs_from_date(date):
	season = season_from_date(date)
	if season==2010 and 20110415<date: return 1
	if season==2009 and 20100415<date: return 1
	if season==2008 and 20090415<date: return 1
	if season==2007 and 20080418<date: return 1
	if season==2006 and 20070419<date: return 1
	if season==2005 and 20060419<date: return 1
	if season==2004 and 20050420<date: return 1
	if season==2003 and 20040414<date: return 1
	if season==2002 and 20030416<date: return 1
	return 0
   

def add_reference_fields(ncaabb):
        len_cols = len(ncaabb[0])
        reference_fields =  [
                                  ("previous game","%s"),
                                  ("previous match up","%s"),
                                  ("next game","%s"),
                                  ("next match up","%s"),
                                  ("opponents","%s")
		           ]
        ytd_fields =  [
                                 ("wins","%d"),
                                 ("losses","%d"),
                                 ("matchup wins","%d"),
                                 ("matchup losses","%d"),
		      ]             

        for field in  reference_fields + ytd_fields:
            ncaabb.add_object(PyQL.columns.Column(name=field[0],format=field[1],data=[None]*len_cols))

        team = {} #team[team] = [game1,game2,...]
        team_opp = {} #team_opp[team][opp] = [game1,game2,...]                
        
        team_offset = ncaabb.offset_from_header("team")
        points_offset = ncaabb.offset_from_header("points")

        #go through games to build team and team_opp dictionaries
        for row in range(len(ncaabb[0])):
            team_name = ncaabb[team_offset][row]
            opp_name = ncaabb[team_offset][row + 1 - 2*(row%2)]
            team.setdefault(team_name,[]).append(row)
            team_opp.setdefault(team_name,{})
            team_opp[team_name].setdefault(opp_name,[]).append(row)
	    
        # go through games to set previous game and previous match up
        p = ncaabb.offset_from_header("previous game")
        P = ncaabb.offset_from_header("previous match up")
        
        w = ncaabb.offset_from_header("wins");
        l = ncaabb.offset_from_header("losses")        
        mw = ncaabb.offset_from_header("matchup wins")
        ml = ncaabb.offset_from_header("matchup losses")
        site = ncaabb.offset_from_header("site")
        season = ncaabb.offset_from_header("season")
        date = ncaabb.offset_from_header("date") # for reading in
        #print "adding YTD averages. Offset of wins=",w
        record = {} #record[team]=[w,l] (TYD)
        mup_record = {} #mup_record[team][opp]=[w,l] (TYD)
        team_pointer = {}
        mup_pointer = {}
        current_season = None
        for row in range(len(ncaabb[0])):
            row_season = ncaabb[season][row]
            if row_season != current_season:
                current_season = row_season
                #print "new season",season,"\nsmup_record:\n",starter_mup_record,"\nstarter_record\n",starter_record
                record = {}; starter_record = {}; mup_record = {}; starter_mup_record = {};
                
            # previous game
            team_name = ncaabb[team_offset][row]
            opp_name = ncaabb[team_offset][row + 1 - 2*(row%2)]
            points,o_points = ncaabb[points_offset][row] ,ncaabb[points_offset][row + 1 - 2*(row%2)]
            record.setdefault(team_name,[0,0])
            mup_record.setdefault(team_name,{}).setdefault(opp_name,[0,0])
            ncaabb.data[w][row] =  record[team_name][0] 
            ncaabb.data[l][row] =   record[team_name][1] 
            ncaabb.data[mw][row] =  mup_record[team_name][opp_name][0] 
            ncaabb.data[ml][row] =  mup_record[team_name][opp_name][1]    
                    
            if points is not None:
                record[team_name][points<o_points] += 1
                mup_record[team_name][opp_name][points<o_points] += 1

	    # handle previous
            pointer = team_pointer.setdefault(team_name,0) - 1
            #print "row,pointer:",row,pointer
            if 0<=pointer:
                p_row = team[team_name][pointer]
                ncaabb.data[p][row] = p_row
            else:                 ncaabb.data[p][row] = None
            team_pointer[team_name] += 1

            # handle previous match up
            mup_pointer.setdefault(team_name,{})            
            pointer = mup_pointer[team_name].setdefault(opp_name,0) - 1
            if 0<=pointer:
                P_row = team_opp[team_name][opp_name][pointer]
                ncaabb.data[P][row] = P_row
            else:                 ncaabb.data[P][row] = None                
            mup_pointer[team_name][opp_name] += 1

        # go through games to set next game and next match up
        n = ncaabb.offset_from_header("next game")
        N = ncaabb.offset_from_header("next match up")        
        team_pointer = {}
        mup_pointer = {}
        for row in range(len(ncaabb[0])-1,-1,-1):
            # next game
            team_name = ncaabb[team_offset][row]
            pointer = team_pointer.setdefault(team_name,len(team[team_name])) 
            if pointer<len(team[team_name]):
                ncaabb.data[n][row] = team[team_name][pointer]
            else: ncaabb.data[n][row] = None
            team_pointer[team_name] -= 1
            # next match up
            opp_name = ncaabb[team_offset][row + 1 - 2*(row%2)]            
            mup_pointer.setdefault(team_name,{})            
            pointer = mup_pointer[team_name].setdefault(opp_name,
                                                          len(team_opp[team_name][opp_name])) 
            if pointer<len(team_opp[team_name][opp_name]):
                ncaabb.data[N][row] = team_opp[team_name][opp_name][pointer]
            else: ncaabb.data[N][row] = None                
            mup_pointer[team_name][opp_name] -= 1
        return ncaabb

     
def add_nice_fields(ncaabb):
        ncaabb.streak = streak
        ncaabb.day_from_date = PyQL.py_tools.day_from_date
        #ncaabb.division_from_nickname_season = NCAABB.teams.division_from_nickname_season
        #ncaabb.conference_from_nickname_season = NCAABB.teams.conference_from_nickname_season
        #ncaabb.playoffs_from_date = playoffs_from_date 
        nice = ncaabb.query("points-(total-line)/2. as dps,"
                          "o:points-(total+line)/2. as dpa,"
                          "points-o:points as margin,"
                          "points+line-o:points as ats margin,"
                          "points+o:points-total as ou margin,"
                          "half scores[0]-o:half scores[0] as margin at the half,"
#                          "self.playoffs_from_date(date) as playoffs,"
                          "len(half scores)-2 as overtime,"
                          "self.day_from_date(date) as day,"
#                          "self.division_from_nickname_season(team,season) as division,"
#                          "self.conference_from_nickname_season(team,season) as conference,"
                          "self.streak(_index_,'su') as streak,"
                          "self.streak(_index_,'ats') as ats streak,"
                          "self.streak(_index_,'ou') as ou streak,"
                          "self.streak(_index_,'site') as site streak,"
                          "int(str(date)[4:6]) as month@1")[0]
        for col in nice:
            if col.name in ncaabb.headers:
                print col.name," is already a column"
                continue
            #print "adding nice column",col.name    
            ncaabb.add_object(col)

def rest(ncaabb,index):
        tp = ncaabb.data[ncaabb.reference_dictionary['p']][index]
        if tp is None: return None
        di = ncaabb.offset_from_header("date")
        if str(ncaabb.data[di][index])[:4] != str(ncaabb.data[di][tp])[:4]: return None
        return PyQL.py_tools.delta_days(ncaabb.data[di][index],ncaabb.data[di][tp]) - 1
        
def streak(ncaabb,index,flavor='su'): # for a given index in games table return the number of games won (lost) in a row
        #print "streak sgtart,"
        pi = ncaabb.reference_dictionary['p']; Pi = ncaabb.reference_dictionary['P']        
        ni = ncaabb.reference_dictionary['n']; Ni = ncaabb.reference_dictionary['N']
        si = ncaabb.site_offset
        #print "streak.si:",si	
        #rli = ncaabb.point_line_offset
        #rlri = ncaabb.point_line_points_offset
        #print "rlri:",rlri
        ri = ncaabb.points_offset
        #li = ncaabb.line_offset
        di = ncaabb.date_offset
        #toti = ncaabb.offset_from_header("total")
        i = index
        streak = 0
        while 1:
            #print "streak.i:",i
            ti = ncaabb.data[pi][i]  # team index
            if not ti or str(ncaabb.data[di][ti])[:4]!=str(ncaabb.data[di][index])[:4]:
                return streak # no more previous same season games
            if flavor == 'site':
                margin = 1*(ncaabb.data[si][ti]=='home') or -1
            elif flavor == 'su':
                margin = ncaabb.data[ri][ti]-ncaabb.data[ri][ti+1-2*(ti%2)]
            elif flavor == 'ou':
                margin = ncaabb.data[ri][ti]+ncaabb.data[ri][ti+1-2*(ti%2)]-ncaabb.data[toti][ti]
            elif flavor == 'rl':
                #(point line+0<0+line)*1.5 or -1.5
                margin = ncaabb.data[ri][ti]+((ncaabb.data[rli][ti]<ncaabb.data[li][ti])*1.5 or -1.5) -ncaabb.data[ri][ti+1-2*(ti%2)]

            if margin == 0: return streak
            if  0<margin: 
                if streak<0: return streak
                streak += 1
                #print "winning streak.streak:",streak
                
            else: # a loss
                if 0<streak: return streak
                streak -= 1
                #print "losing streak.streak:",streak                
            i = ncaabb.data[pi][i]
        raise "can't get here"




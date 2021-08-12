# This file:
#     builds reference and nice fields
# Goals:
#     Handle custom client data

import sys, os, re, string
import PyQL.py_tools as py_tools
import PyQL.columns as columns


def add_join_fields(sdb):

	starter_offset = sdb.offset_from_header("starter")

        n_rows = len(sdb[0])
        join_fields =  [
                                  ("_previous game","%s"),
                                  ("_previous match up","%s"),
                                  ("_next game","%s"),
                                  ("_next match up","%s"),
    	               ]
	if starter_offset is not None: join_fields += [
	                                  ("_starters previous game","%s"),
		                          ("_starters previous match up","%s")
		                                      ]

        for field in join_fields:
            sdb.add_object(columns.Column(name=field[0],format=field[1],data=[None]*n_rows))

        team = {} #team[team] = [game1,game2,...]
        team_opp = {} #team_opp[team][opp] = [game1,game2,...]
        starter = {} # starter[name] = [game1,game2,..] of this starter
        starter_opp = {} # starter[name][opp number] = [game1,game2,..] of this starter

        team_offset = sdb.offset_from_header("team")
	if team_offset is None: raise Exception("Database needs a column named 'team'.")
        date_offset = sdb.offset_from_header("date")
	if date_offset is None: raise Exception("Database needs a column named 'date'.")

        #go through games to build team and team_opp dictionaries (and for starter, too)
        for row in range(n_rows):
	    #print "row:",row
            team_name = sdb[team_offset][row]
            opp_name = sdb[team_offset][row + 1 - 2*(row%2)]
	    if starter_offset is not None: starter_name = sdb[starter_offset][row]
	    else: starter_name = None
            team.setdefault(team_name,[]).append(row)
            team_opp.setdefault(team_name,{}).setdefault(opp_name,[]).append(row)
            # repeat for starter
            if starter_name: # Even with a starter offset there could be a missing starter name.
                starter.setdefault(starter_name,[]).append(row)
                starter_opp.setdefault(starter_name,{}).setdefault(opp_name,[]).append(row)

        # go through games to set previous game and previous match up
        p = sdb.offset_from_header("_previous game")
        P = sdb.offset_from_header("_previous match up")
        s = sdb.offset_from_header("_starters previous game")
        S = sdb.offset_from_header("_starters previous match up")
        team_pointer = {}
        mup_pointer = {}
        starter_pointer = {}
        starter_mup_pointer = {}
        for row in range(n_rows):
            team_name = sdb[team_offset][row]
	    if starter_offset is not None: starter_name = sdb[starter_offset][row]
	    else: starter_name = None
            opp_name = sdb[team_offset][row + 1 - 2*(row%2)]
            pointer = team_pointer.setdefault(team_name,0) - 1
            #print "row,pointer:",row,pointer
            if 0<=pointer:
                p_row = team[team_name][pointer]
                sdb.data[p][row] = p_row
            else: sdb.data[p][row] = None
            team_pointer[team_name] += 1
            # handle previous start
	    if starter_name and starter_offset is not None:
	        pointer = starter_pointer.setdefault(starter_name,0) - 1
		if 0<=pointer and starter_name:
		    s_row = starter[starter_name][pointer]
		    sdb.data[s][row] = s_row
		else: sdb.data[s][row] = None
		starter_pointer[starter_name] += 1
            # handle previous match up
            mup_pointer.setdefault(team_name,{})
            pointer = mup_pointer[team_name].setdefault(opp_name,0) - 1
            if 0<=pointer:
                P_row = team_opp[team_name][opp_name][pointer]
                sdb.data[P][row] = P_row
            else:                 sdb.data[P][row] = None
            mup_pointer[team_name][opp_name] += 1
             # handle starters previous match up
	    if starter_name and starter_offset is not None:
                starter_mup_pointer.setdefault(starter_name,{})
		pointer = starter_mup_pointer[starter_name].setdefault(opp_name,0) - 1
		if 0<=pointer and starter_name:
                    S_row = starter_opp[starter_name][opp_name][pointer]
		    sdb.data[S][row] = S_row
	        else:      sdb.data[S][row] = None
		starter_mup_pointer[starter_name][opp_name] += 1

        # go through games to set next game and next match up
        n = sdb.offset_from_header("_next game")
        N = sdb.offset_from_header("_next match up")
        team_pointer = {}
        mup_pointer = {}
        for row in range(len(sdb[0])-1,-1,-1):
            # next game
            team_name = sdb[team_offset][row]
            pointer = team_pointer.setdefault(team_name,len(team[team_name]))
            if pointer<len(team[team_name]):
                sdb.data[n][row] = team[team_name][pointer]
            else: sdb.data[n][row] = None
            team_pointer[team_name] -= 1
            # next match up
            opp_name = sdb[team_offset][row + 1 - 2*(row%2)]
            mup_pointer.setdefault(team_name,{})
            pointer = mup_pointer[team_name].setdefault(opp_name,
                                                          len(team_opp[team_name][opp_name]))
            if pointer<len(team_opp[team_name][opp_name]):
                sdb.data[N][row] = team_opp[team_name][opp_name][pointer]
            else: sdb.data[N][row] = None
            mup_pointer[team_name][opp_name] -= 1
        return sdb

def add_std_fields(sdb):

	starter_offset = sdb.offset_from_header("starter")
        n_rows = len(sdb[0])

        std_fields =  [
                         ("wins","%d"),
                         ("losses","%d"),
		         ("game number","%d"),
                         ("matchup wins","%d"),
                         ("matchup losses","%d"),
		         ("opponents","%s")
		     ]
	if starter_offset is not None:
	    std_fields +=  [
                         ("starter wins","%d"),
                         ("starter losses","%d"),
                         ("starter matchup wins","%d"),
                         ("starter matchup losses","%d")
		     ]
        for field in std_fields:
	    if field[0] in sdb.headers: raise Exception("%s is already a field"%field[0])
            sdb.add_object(columns.Column(name=field[0],format=field[1],data=[None]*n_rows))


        team_offset = sdb.offset_from_header("team")
	opponents = {} # opponents[team] = [list of year-to-date opponents]
	opponents_offset = sdb.offset_from_header("opponents")
        points_offset = sdb.offset_from_header("goals")
        date_offset = sdb.offset_from_header("date")
	#print "goals.offset:",points_offset
	if points_offset is None: points_offset = sdb.offset_from_header("runs")
	if points_offset is None:
                #print "points offset on ponits"
                points_offset = sdb.offset_from_header("points")
	if points_offset is None: raise "SportsDataBase expects a header of goals, points, or runs"

        gn = sdb.offset_from_header("game number");
        w = sdb.offset_from_header("wins");
        l = sdb.offset_from_header("losses")
        sw = sdb.offset_from_header("starter wins")
        sl = sdb.offset_from_header("starter losses")
        mw = sdb.offset_from_header("matchup wins")
        ml = sdb.offset_from_header("matchup losses")
        smw = sdb.offset_from_header("starter matchup wins")
        sml = sdb.offset_from_header("starter matchup losses")
        season_offset = sdb.offset_from_header("season")
	if season_offset is None: raise Exception("STD needs a 'season' column")
        print "adding STD averages. Offset of wins=",w
        record = {} #record[team]=[w,l] (TYD)
        starter_record = {} #starter_record[starter]=[w,l] (TYD)
        mup_record = {} #mup_record[team][opp]=[w,l] (TYD)
        starter_mup_record = {} #starter_mup_record[starter][opp]=[w,l] (TYD)
        current_season = None
        for row in range(len(sdb[0])):
	    #print "row::",row
            row_season = sdb[season_offset][row]
            if row_season != current_season:
                current_season = row_season
                record = {}; starter_record = {}; mup_record = {}; starter_mup_record = {};
                opponents = {}; game_number = {}

            team_name = sdb[team_offset][row]
            opp_name = sdb[team_offset][row + 1 - 2*(row%2)]
	    if starter_offset is not None: starter_name = sdb[starter_offset][row]
	    else: starter_name = None
	    sdb.data[opponents_offset][row] = opponents.get(team_name,[])[:]
	    opponents.setdefault(team_name,[]).append(opp_name)
            points,o_points = sdb[points_offset][row] ,sdb[points_offset][row + 1 - 2*(row%2)]
            game_number[team_name] = game_number.setdefault(team_name,0) + 1 # this field is updated before the game happens
            record.setdefault(team_name,[0,0])
            mup_record.setdefault(team_name,{}).setdefault(opp_name,[0,0])

            sdb.data[gn][row] =  game_number[team_name]
            sdb.data[w][row] =  record[team_name][0]
            sdb.data[l][row] =   record[team_name][1]
            sdb.data[mw][row] =  mup_record[team_name][opp_name][0]
            sdb.data[ml][row] =  mup_record[team_name][opp_name][1]
	    if starter_name:
		    starter_record.setdefault(starter_name,[0,0])
		    starter_mup_record.setdefault(starter_name,{}).setdefault(opp_name,[0,0])
		    sdb.data[sw][row] =  starter_record[starter_name][0]
		    sdb.data[sl][row] =  starter_record[starter_name][1]
		    sdb.data[smw][row] =  starter_mup_record[starter_name][opp_name][0]
		    sdb.data[sml][row] =  starter_mup_record[starter_name][opp_name][1]

            if points is not None and points!=o_points:
                record[team_name][points<o_points] += 1
                mup_record[team_name][opp_name][points<o_points] += 1
                if starter_name is not None:
			starter_record[starter_name][points<o_points] += 1
			starter_mup_record[starter_name][opp_name][points<o_points] += 1

        return sdb



def add_nice_fields(sdb):
    sdb.streak = streak
    has_total = (sdb.offset_from_header("total") is not None)
    #print "S2.prepare ht:",has_total
    if sdb.offset_from_header("runs") is not None:
	    margins = "runs-o:runs as margin,(runs+o:runss-total) as 'ou margin',"
    if sdb.offset_from_header("goals") is not None:
	    margins = "goals-o:goals as margin,(goals+o:goals-total) as 'ou margin',"
    else:
	    margins = "points-o:points as margin,(points+o:points-total) as 'ou margin',(points+line-o:points) as 'ats margin',"
    #print "prepare margins:",margins
    nice = sdb.query(
                          margins + "int(str(date)[4:6]) as month,"
	                  "date-p:date as rest,"
                          "self.streak(self,_i,'su') as streak,"
                          "self.streak(self,_i,'ou') as ou streak,"*(has_total) +
                          "self.streak(self,_i,'site') as site streak"
                          "@1")[0]
    for col in nice:
        offset = sdb.offset_from_header(col.name)
        if offset is None:
            #print "S2.prepare adding nice column:",col.name ,"eg:",col.data[1000]
            sdb.add_object(col)
        else:
            #print col.name," is already a column: overwrite"
            sdb.data[offset] = col




def streak(sdb,index,flavor='su'): # for a given index in games table return the number of games won (lost) in a row
        #print "streak sgtart,"
        pi = sdb.offset_from_header("_previous game")
	Pi = sdb.offset_from_header("_previous match up")
        ni = sdb.offset_from_header("_next game")
	Ni = sdb.offset_from_header("_next match up")
        si = sdb.offset_from_header("site")
        #print "streak.si:",si
        rli = sdb.offset_from_header("run line")
        #rlri = sdb.run_line_runs_offset
        #print "rlri:",rlri
        pti = sdb.offset_from_header("goals")
	if pti is None: pti = sdb.offset_from_header("runs")
	if pti is None: pti = sdb.offset_from_header("points")
        li = sdb.offset_from_header("line")
        di = sdb.offset_from_header("date")
        seai = sdb.offset_from_header("season")
        toti = sdb.offset_from_header("total")
        #print "toti:",toti
        #print "di:",di
        i = index
        streak = 0
        while 1:
            #print "streak.i:",i
            ti = sdb.data[pi][i]  # team index
	    if not ti or sdb.data[seai][ti]!=sdb.data[seai][index]:
                return streak # no more previous same season games
	    oi = ti+1-2*(ti%2)
            if flavor == 'site':
                margin = 1*(sdb.data[si][ti]=='home') or -1*(sdb.data[si][ti]=='away')
            elif flavor == 'su':
                margin = sdb.data[pti][ti]-sdb.data[pti][oi]
            elif flavor == 'ats':
                margin = sdb.data[pti][ti]+sdb.data[li][ti]-sdb.data[pti][oi]
            elif flavor == 'ou':
                margin = sdb.data[pti][ti]+sdb.data[pti][oi]-sdb.data[toti][ti]
            elif flavor == 'rl':
		#print "try setting rl margin"
                #(run line+0<0+line)*1.5 or -1.5
                margin = sdb.data[pti][ti]+((sdb.data[rli][ti]<sdb.data[li][ti])*1.5 or -1.5) -sdb.data[pti][oi]
		#print "rl margin",margin

            if margin == 0: return streak
            if  0<margin:
                if streak<0: return streak
                streak += 1
                #print "winning streak.streak:",streak

            else: # a loss
                if 0<streak: return streak
                streak -= 1
                #print "losing streak.streak:",streak
            i = sdb.data[pi][i]
        raise "can't get here"

if __name__ == "__main__":
	import S2.db
	#sdb = S2.db.DB("/home/jameyer/S2/Data/Available/mlb.tab")
	add_join_fields(sdb)
	#add_nice_fields(sdb)
	sdb.build_lexer()
	#print sdb.query("opponents@team=Cubs and season=2010")

# This file:
#     builds reference and nice fields

import sys, os, re, string
import PyQL.py_tools
import PyQL.columns

import NBA.time_zones
import NBA.seed
import NBA.teams

import S2.prepare
add_join_fields = S2.prepare.add_join_fields
add_std_fields = S2.prepare.add_std_fields

def pover_str(delta=0):
    b = -0.03529002
    cs = [ 0.01288742,  0.00802667,  0.00567704,  0.01755217]
    b = -0.022556
    cs = [ 0.01422447,  0.01045663,  0.00895397,  0.01138185] # 20180308
    b = -0.0360984
    cs = [ 0.01260923,  0.00977983,  0.00776667,  0.01699431]
    if delta:
        params = ['total+%s-p:total'%delta,'total+%s-op:total'%delta,
                  'total+%s-p2:total'%delta,'total+%s-op2:total'%delta]
    else:
        params = ['total-p:total','total-op:total', 'total-p2:total','total-op2:total']
    model = "%0.5f"%b
    for p,param in enumerate(params):
        model += "+%0.5f*(%s)"%(cs[p],param)
    #return "int(round(100./(1+math.pow(math.e,-1*(%s)))))"%model
    return "(.1*int(round(1000./(1+math.pow(math.e,-1*(%s))))))"%model
POVER_STR = pover_str() # short_cuts needs this
KELLY_STR = "(((%s<50)*(1-%s/100.) or %s/100.)*1.95-1)/0.95"%(POVER_STR,POVER_STR,POVER_STR)
#KELLY_STR =  "(1/(1+math.pow(math.e,-0.8*%s))-0.5)"%(KELLY_STR,) # joe sigmoid

def season_from_date(date):
    sdate = str(date)
    season = int(sdate[:4])
    if season == 2020:
        if date<20201100:
            season -= 1
    elif sdate[4] == '0':
        season -= 1
    return season

def playoffs_from_date(date):
	season = season_from_date(date)
	if season==2020 and 20210516<date: return 1
	if season==2019 and 20200816<date: return 1
	if season==2018 and 20190411<date: return 1
	if season==2017 and 20180411<date: return 1
        if season==2016 and 20170413<date: return 1
	if season==2015 and 20160413<date: return 1
	if season==2014 and 20150415<date: return 1
	if season==2013 and 20140417<date: return 1
	if season==2012 and 20130417<date: return 1
	if season==2011 and 20120427<date: return 1
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

def aasb_from_date(date):
	season = season_from_date(date)
        if season==1994 and date> 19950212: return 1
        if season==1995 and date> 19960211: return 1
        if season==1996 and date> 19970209: return 1
        if season==1997 and date> 19980208: return 1
        if season==1998: return
        if season==1999 and date> 20000213: return 1
        if season==2000 and date> 20010211: return 1
        if season==2001 and date> 20020210: return 1
        if season==2002 and date> 20030209: return 1
        if season==2003 and date> 20040215: return 1
        if season==2004 and date> 20050220: return 1
        if season==2005 and date> 20060219: return 1
        if season==2006 and date> 20070218: return 1
        if season==2007 and date> 20080217: return 1
        if season==2008 and date> 20090215: return 1
        if season==2009 and date> 20100214: return 1
        if season==2010 and date> 20110220: return 1
        if season==2011 and date> 20120226: return 1
        if season==2012 and date> 20130217: return 1
        if season==2013 and date> 20140216: return 1
        if season==2014 and date> 20150215: return 1
        if season==2015 and date> 20160214: return 1
        if season==2016 and date> 20170219: return 1
        if season==2017 and date> 20180220: return 1
        if season==2018 and date> 20190220: return 1
        if season==2019 and date> 20200216: return 1
        if season==2020 and date> 20210305: return 1
        return 0

def set_hierarchy_fields(nba):
    print 'set hierarchy fields'
    # set a top level (no owner) parameter based on one or more owner-parameters.
    # this needs to be done before streak in add_nice so that 'points' is well defined
    nice = nba.sdb_query(
        "filter(lambda x:x is not None,[Covers.points,Box.points,SDB.points])[-1] as 'points',"
        "filter(lambda x:x is not None,[Covers.total,SDB.total])[-1] as 'total',"
        "filter(lambda x:x is not None,[Covers.line,SDB.line])[-1] as 'line',"
        "filter(lambda x:x is not None,[Covers.quarter scores,Box.quarter scores,SDB.quarter scores])[-1] as 'quarter scores'"
                                 "@1")[0] # watch your commas!

    for col in nice:
        offset = nba.offset_from_header(col.name,owners=[''])
        if offset is None:
            print "adding hierarchy column",col.name
            nba.add_object(col)
        else:
            print col.name,"is already a column: overwrite hierachically"
            nba.data[offset] = col
    # done with B2.parameter, clean up.
    #del_these = []
    #for h,head in enumerate(ncaafb.headers):
    #    if head.startswith("B2.") or head.startswith('SDB'): # and head not in ['SDB.line','SDB.total']):
    #        del_these.append(h)
    #del_these.reverse()
    #for d in del_these:
    #    print "deleting used hierarchy feild",d,ncaafb.headers[d]
    #    ncaafb.del_column(d)



def update_nice(nba,nice):

        for col in nice:
            offset = nba.offset_from_header(col.name)
            if offset is None:
                print "adding nice column",col.name
                nba.add_object(col)
            else:
                print col.name," is already a column: overwrite"
                nba.data[offset] = col


def add_nice_fields(nba):
        nba.time_zones = NBA.time_zones.time_zones
        nba.seed_dict = NBA.seed.d
        nba.round = NBA.seed.round
        nba.streak = S2.prepare.streak
        nba.series = series
        nba.aasb_from_date = aasb_from_date
        nba.day_from_date = PyQL.py_tools.day_from_date
        nba.division_from_nickname_season = NBA.teams.division_from_nickname_season
        nba.conference_from_nickname_season = NBA.teams.conference_from_nickname_season
        nba.abbreviation_from_nickname = NBA.teams.abbreviation_from_nickname
        nba.playoffs_from_date = playoffs_from_date
        # It is handy to make two runs at nice: round and seed depend on the team name already being changed
        nice = nba.sdb_query("'Pelicans'*(season<2014 and team=='Hornets') or team as team@1")[0]
        update_nice(nba,nice)
        nice = nba.query("'Hornets'*(team=='Bobcats') or team as team@1")[0]
        update_nice(nba,nice)
        nice = nba.query("((t:date-p:date)*(season==p:season) or None)-1 as rest,"
                          "float(line) as 'line',"
                          "float(total) as 'total',"
                          "float(points-(total-line)/2.) as dps,"
                          "float(o:points-(total+line)/2.) as dpa,"
                          "points-o:points as margin,"
                          "float(points+line-o:points) as ats margin,"
                          "float(points+o:points-total) as ou margin,"
                          "quarter scores[0]-o:quarter scores[0] as margin after the first,"
                          "quarter scores[0]+quarter scores[1]-o:quarter scores[0]-o:quarter scores[1] as margin at the half,"
                          "quarter scores[0]+quarter scores[1]+quarter scores[2]-o:quarter scores[0]-o:quarter scores[1]-o:quarter scores[2] as margin after the third,"
                          "self.playoffs_from_date(date) as playoffs,"
                          "self.aasb_from_date(date) as 'after all star break',"
                          "2002<=season and len(quarter scores)-4 as overtime,"
                          "self.day_from_date(date) as day,"
                          "self.division_from_nickname_season(team,season) as division,"
                          "self.conference_from_nickname_season(team,season) as conference,"
                          "self.streak(self,_i,'su') as streak,"
                          "self.streak(self,_i,'ats') as ats streak,"
                          "self.streak(self,_i,'ou') as ou streak,"
                          "self.streak(self,_i,'site') as site streak,"
                          "self.seed_dict.get((season,team)) as seed,"
                          "self.series(self,_i)[0] as series game,"
                          "self.series(self,_i)[1] as series games,"
                          "self.series(self,_i)[2] as series wins,"
                          "self.series(self,_i)[3] as series losses,"
#                          "Column(self.time_zones[team*(site==home) or o:team],format=lambda x:`str(x)`) as time zone,"
                          "Column(self.time_zones[team]) as time zone,"
                          "(self.playoffs_from_date(date) or None) and self.round(self.seed_dict.get((season,team)),self.seed_dict.get((season,o:team)),self.conference_from_nickname_season(team,season),self.conference_from_nickname_season(o:team,season)) as round,"
                          "int(str(date)[4:6]) as month@1")[0]
        update_nice(nba,nice)
        #cast(nba)

def cast(nba):
    import numpy as np
    for p in 'fouls,assists,blocks,three pointers made,three pointers attemped,field goals made,field goals attemped,free throws made,free throws attemped,blocks,rebounds,offensive rebounds,minutes,steals,time tied,lead changes,turnovers,overtime,team rebounds'.split(','):
        o = nba.offset_from_header(p)
        if o is None: print "oops, cant cast %s: it is not a parameter!"%p
        print "casting %s as int8 at %d"% (p,o)
        nba.data[o] = np.int8(     nba.data[o])


def series(nba,index): # for a given index in games table return a tuple of (game number in series, number of games in series)
    # unlike MLB, ignore site
    #print "nba.series.index: %s"%index
    pi = nba.reference_dictionary['p']; Pi = nba.reference_dictionary['P']
    ni = nba.reference_dictionary['n']; Ni = nba.reference_dictionary['N']
    #print "nba.series.nindex: %s"%ni
    si = nba.season_offset
    di = nba.date_offset
    opponents_offset = nba.offset_from_header("opponents")
    team_offset = nba.offset_from_header("team")
    points_offset = nba.offset_from_header("points")
    date = nba.data[di][index]
    season = nba.data[si][index]
    playoffs = playoffs_from_date(date)
    #print "s,d,p",season,date,playoffs
    prev_games = next_games = wins = losses = 0
    same_series = True; i = index # look back
    #print "nba.series.date: %s"%date

    if not playoffs: return None
    while same_series:
        #print "i,p,P:",i,nba.data[pi][i],nba.data[Pi][i]
        if nba.data[pi][i] == nba.data[Pi][i] and nba.data[pi][i] is not None  and date - 30 < nba.data[di][nba.data[pi][i]] and nba.playoffs_from_date(nba.data[di][nba.data[pi][i]]): # kludge same-season
            i = nba.data[pi][i]
            oi = i + (1 - 2 * (i%2))
            try:
                points = nba.data[points_offset][i]
                o_points = nba.data[points_offset][oi]
                #print points,o_points
                if points > o_points: wins += 1
                elif points < o_points: losses += 1
            except: pass
            prev_games += 1
        else: same_series = False
    same_series = True; i = index # look forward
    while playoffs and same_series:
        #print "i,n,N:",i,nba.data[ni][i],nba.data[Ni][i]
          if nba.data[ni][i] == nba.data[Ni][i] and nba.data[ni][i] is not None  and date + 30 > nba.data[di][nba.data[ni][i]]: # kludge same-season:
            i = nba.data[ni][i]
            next_games += 1
          else: same_series = False
    #print "ret:",(prev_games+1,prev_games+next_games+1,wins,losses)
    return (prev_games+1,prev_games+next_games+1,wins,losses)

def XXseries(nba,index): # for a given index in games table return a tuple of (game number in series, number of games in series)
	# adapt from MLB : here don't care about site and is only non None during playoffs
        pi = nba.reference_dictionary['p']; Pi = nba.reference_dictionary['P']
        ni = nba.reference_dictionary['n']; Ni = nba.reference_dictionary['N']
        si = nba.site_offset
        di = nba.date_offset
        site = nba.data[si][index]
        date = nba.data[di][index]
        print "date:",date
	if not playoffs_from_date(date): return None
        print "po"
        prev_games = 0; next_games = 0;
        same_series = 1; i = index # look back
        while same_series:
            #print "i,p,P:",i,nba.data[pi][i],nba.data[Pi][i]
            if nba.data[pi][i] == nba.data[Pi][i] and nba.data[pi][i] is not None and site == nba.data[si][nba.data[pi][i]] and date - 30 < nba.data[di][nba.data[pi][i]]: # kludge same-season
                i = nba.data[pi][i]
                prev_games += 1
            else: same_series = 0
        same_series = 1; i = index # look forward
        while same_series:
            #print "i,n,N:",i,nba.data[ni][i],nba.data[Ni][i]
            if nba.data[ni][i] == nba.data[Ni][i] and nba.data[ni][i] is not None and date + 30 > nba.data[di][nba.data[ni][i]]:
                i = nba.data[ni][i]
                next_games += 1
            else: same_series = 0
        return (prev_games+1,prev_games+next_games+1)

def XXXrest(nba,index):
        tp = nba.data[nba.reference_dictionary['p']][index]
        if tp is None: return None
        di = nba.offset_from_header("date")
        if str(nba.data[di][index])[:4] != str(nba.data[di][tp])[:4]: return None
        return PyQL.py_tools.delta_days(nba.data[di][index],nba.data[di][tp]) - 1

def XXXstreak(nba,index,flavor='su'): # for a given index in games table return the number of games won (lost) in a row
        #print "streak sgtart,"
        pi = nba.reference_dictionary['p']; Pi = nba.reference_dictionary['P']
        ni = nba.reference_dictionary['n']; Ni = nba.reference_dictionary['N']
        si = nba.site_offset
        #print "streak.si:",si
        #rli = nba.point_line_offset
        #rlri = nba.point_line_points_offset
        #print "rlri:",rlri
        ri = nba.points_offset
        #li = nba.line_offset
        di = nba.date_offset
        #toti = nba.offset_from_header("total")
        i = index
        streak = 0
        while 1:
            #print "streak.i:",i
            ti = nba.data[pi][i]  # team index
            if not ti or str(nba.data[di][ti])[:4]!=str(nba.data[di][index])[:4]:
                return streak # no more previous same season games
            if flavor == 'site':
                margin = 1*(nba.data[si][ti]=='home') or -1
            elif flavor == 'su':
                margin = nba.data[ri][ti]-nba.data[ri][ti+1-2*(ti%2)]
            elif flavor == 'ou':
                margin = nba.data[ri][ti]+nba.data[ri][ti+1-2*(ti%2)]-nba.data[toti][ti]
            elif flavor == 'rl':
                #(point line+0<0+line)*1.5 or -1.5
                margin = nba.data[ri][ti]+((nba.data[rli][ti]<nba.data[li][ti])*1.5 or -1.5) -nba.data[ri][ti+1-2*(ti%2)]

            if margin == 0: return streak
            if  0<margin:
                if streak<0: return streak
                streak += 1
                #print "winning streak.streak:",streak

            else: # a loss
                if 0<streak: return streak
                streak -= 1
                #print "losing streak.streak:",streak
            i = nba.data[pi][i]
        raise "can't get here"

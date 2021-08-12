# This file:
#     builds reference and nice fields
# Goals:
#     Handle custom client data

import sys, os, re, string
import NFL.date_tools
from NFL.snf import d as SNF
#from NFL.grass import d as SURFACE
import NFL.grass
#from NFL.time_zones import time_zones as TIME_ZONES
from NFL.teams import division as DIVISION
import PyQL.py_tools
import PyQL.columns

import S2.prepare
add_join_fields = S2.prepare.add_join_fields
add_std_fields = S2.prepare.add_std_fields

verbose = False


def season_from_date(date):
    sdate = str(date)
    season = int(sdate[:4])
    if sdate[4]=='0' and sdate[5] in "123": season = season - 1
    return season


def combine_fields(nfl):
    """use some canned logic to unify columns and remove extras"""
    #print "combine_fields"
    extra_columns = [] # list of offsets to remove

    for h in range(len(nfl.headers)):
        header = nfl.headers[h]
        #print "header",header
        if not header.startswith('Box.'): continue
        owner,field = header.split('.',1)
        h2 = nfl.offset_from_header("%s.%s"%('SDB',field)) or nfl.offset_from_header("%s.%s"%('Schedule',field))
        if h2 is None: continue
        #print "extra column at",field
        extra_columns.append(h2)
        #print "checking for possible update of:",header,"from:",nfl.headers[h2]
        for i in range(len(nfl[0])):
            #print "i:",i
            if nfl[h][i] is None and nfl[h2][i] is not None:
                #print "updating",header,"with",nfl[h2][i]
                nfl[h][i] =  nfl[h2][i]

    extra_columns.sort()
    extra_columns.reverse()
    for h in extra_columns:
        if verbose: print "del column:",h,nfl.headers[h]
        nfl.del_column(h,rebuild_header_dict=0)

    nfl.build_header_dict()
    return nfl

def add_prenice_fields(nfl): # needs to get done before nice_fields site_streak
    nfl.N_SITES = NFL.date_tools.N_SITES
    nice = nfl.sdb_query(
        "self.N_SITES.get((str(date),team),site) as 'site'@1")[0]

    for col in nice:
        offset = nfl.offset_from_header(col.name)
        if offset is None:
            if verbose: print "adding prenice column",col.name
            nfl.add_object(col)
        else:
            if verbose: print col.name," is already a column: prenice overwrites"
            nfl.data[offset] = col
    return nfl

def add_nice_fields(nfl):
    nfl = add_prenice_fields(nfl)
    #print "adding nice headers"
    #nfl.game_dates = PyQL.py_tools.remove_duplicates(
    #      nfl.query("date@date>20100800")[0][0].data)
    #nfl.game_dates.sort()
    nfl.SNF = SNF
    nfl.week_from_date = NFL.date_tools.find_week_from_date
    nfl.season_week_day_from_date = NFL.date_tools.find_season_week_day_from_date
    nfl.SURFACE = NFL.grass.d
    nfl.SURFACE_PATCH = NFL.grass.PATCH
    #nfl.TIME_ZONES = TIME_ZONES
    nfl.DIVISION = DIVISION
    nfl.streak = S2.prepare.streak
    #nfl.show_metacode=1
    nice = nfl.sdb_query(
      "((date-p:date)*(season==p:season) or None)-1 as rest,"
        "{'Redskins':'Washington'}.get(team,team) as 'team',"
      "self.streak(self,_i,'su') as 'streak',"
      "float(line) as 'line',"
      "int(start time) as 'start time',"
      "float(total) as 'total',"
      "overtime or (len(quarter scores)>4)*1 as 'overtime',"   # prior to 2001 overtime is a parameter and len(quarter scores)==4
      "return yards or punt return yards + kickoff return yards as 'return yards',"   # prior to 2001 return yards was not broken down
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
        "self.SURFACE_PATCH.get((date,team)) or self.SURFACE.get(team*(site=='home') or o:team,{}).get(season) as 'surface',"
      "self.DIVISION(team,season) as 'division',"
      "self.DIVISION(team,season)[:3] as 'conference',"
      "((self.week_from_date(date)>17 and season>2001) or (self.week_from_date(date)>18 and season==2001))*1 as 'playoffs',"
      #"Column(self.TIME_ZONES[team*(site=='home') or o:team],format=lambda x:`str(x)`) as 'time zone',"
      "int(str(date)[4:6]) as month@1")[0]

    for col in nice:

        if col.name in ["ats margin","ou margin"]:
            col.str_format = """lambda line:"%s%d%s"%('+'*(0<line) + '-'*(line<0),int(abs(line)),"'"*(line!=int(line)))"""
            # '   this single quote helps emacs keep the syntax highlighting correct
            col.set_format(col.str_format)

        offset = nfl.offset_from_header(col.name)
        if offset is None:
            if verbose: print "adding nice column",col.name
            nfl.add_object(col)
        else:
            if verbose: print col.name," is already a column: nice overwrites"
            nfl.data[offset] = col


    return nfl

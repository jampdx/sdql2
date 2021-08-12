
# This file:
#     builds reference and nice fields
# Goals:
#     Handle custom client data

import sys, os, re, string
import NCAAFB.date_tools
import NCAAFB.teams
import PyQL.py_tools
import PyQL.columns
from S2.directory import data_dir
DATA_DIR = data_dir("ncaafb")

import S2.prepare
add_join_fields = S2.prepare.add_join_fields
add_std_fields = S2.prepare.add_std_fields


import UserDict
class look_back_dict(UserDict.UserDict):
    def __init__(self,d={}):
        UserDict.UserDict.__init__(self,d)
    def look_back_get(self,key,default=None):
        #print "look_back_dict.key:",key,type(key)
        if key in self.keys(): return self[key]
        elif 1979<key: return self.look_back_get(key-1,default)
        else: return default

def team_dict():
    d = {} # d[team][season]=(full,div,conf,cdiv)
    for line in map(string.strip,open(os.path.join(DATA_DIR,"Join","_Raw","teams.bar")).readlines()):
        if not line: continue
        #print line
        if 1: #try: # user might mess format
            abbr,fn,div,conf,cdiv,season = map(string.strip,string.split(line,'|'))
        #except:
        #    continue
        if not d.has_key(abbr):
            d[abbr] = look_back_dict()
        d[abbr][int(season)] = (fn,div,conf,cdiv)
    return d

def coach_dict():
    d = {}
    # file has abbr coach date and we can only deal with season.
    for line in map(string.strip,open(os.path.join(DATA_DIR,"Join","_Raw","head_coaches.tab")).readlines()[1:]):
        if not string.strip(line): continue
        #print line
        abbr,coach,date = map(string.strip,string.split(line,'\t'))
        season = season_from_date(date)
        if not d.has_key(abbr):
            d[abbr] = look_back_dict()
        d[abbr][season] = coach
    return d


def season_from_date(date):
    sdate = str(date)
    season = int(sdate[:4])
    if sdate[4]=='0' and sdate[5] in "123": season = season - 1
    return season


def set_hierarchy_fields(ncaafb):
    print 'set hierarchy fields'
    # set a top level (no owner) parameter based on one or more owner-parameters.
    # this needs to be done before add_join_fields to get the s, S prefixes for SDB.starter
    nice = ncaafb.sdb_query(
        "B2.school as Schedule.school,"
        "B2.rank as Schedule.rank,"
        "B2.start time as Schedule.start time,"
        "B2._gid as Schedule._gid,"
        "filter(lambda x:x is not None,[B2.line,Box.line,SDB.line])[-1] as 'line',"
        "filter(lambda x:x is not None,[B2._ROT])[-1] as 'rot',"
        "filter(lambda x:x is not None,[B2.points,Box.points,SDB.points])[-1] as 'points',"
        "filter(lambda x:x is not None,[B2.quarter scores,Box.quarter scores,SDB.quarter scores])[-1] as 'quarter scores',"
        "len(filter(lambda x:x is not None,[ [1]*((SDB.overtime or 0)+4),B2.quarter scores,Box.quarter scores])[-1])-4 as 'overtime',"
        "filter(lambda x:x is not None,[B2.total,Box.total,SDB.total])[-1] as 'total'"
                                 "@1")[0] # watch your commas!

    for col in nice:
        offset = ncaafb.offset_from_header(col.name,owners=[''])
        if offset is None:
            print "adding hierarchy column",col.name
            ncaafb.add_object(col)
        else:
            print col.name,"is already a column: overwrite hierachically"
            ncaafb.data[offset] = col
    # done with B2.parameter, clean up.
    del_these = []
    for h,head in enumerate(ncaafb.headers):
        if head.startswith("B2.") or (head.startswith('SDB') and head not in ['SDB.line','SDB.total']):
            del_these.append(h)
    del_these.reverse()
    for d in del_these:
        print "deleting used hierarchy feild",d,ncaafb.headers[d]
        ncaafb.del_column(d)

def combine_fields(ncaafb):
    """use some canned logic to unify columns and remove extras"""
    #print "combine_fields"
    extra_columns = [] # list of offsets to remove

    for h in range(len(ncaafb.headers)):
        header = ncaafb.headers[h]
        #print "header",header
        if not header.startswith('SDB.'): continue
        owner,field = header.split('.',1)
        #if field in ['line','total','points','quarter scores']: continue
        if field in ['line','total']: continue
        h2 = ncaafb.offset_from_header("Box.%s"%(field,))
        if h2 is None: continue
        #print "extra column at",field
        extra_columns.append(h)
        #print "checking for possible override of:",header
        for i in range(len(ncaafb[0])):
            if ncaafb[h][i] is not None:
                ncaafb[h2][i] =  ncaafb[h][i]
                #if field == 'points': print 'combine:.points', ncaafb[h2][i],'i:',i
    extra_columns.sort()
    extra_columns.reverse()
    for h in extra_columns:
        #print "deleting column:",h,ncaafb.headers[h]
        ncaafb.del_column(h,rebuild_header_dict=0)
    ncaafb.build_header_dict()
    return ncaafb


def add_nice_fields(ncaafb):
    ncaafb.team_d = team_dict()
    ncaafb.look_back_dict = look_back_dict
    #ncaafb = add_first_nice_fields(ncaafb) #got to do these first
    ncaafb.week_from_date = NCAAFB.date_tools.find_week_from_date
    ncaafb.season_week_day_from_date = NCAAFB.date_tools.find_season_week_day_from_date
    ncaafb.abbr_to_full = NCAAFB.teams.abbr_to_full
    #ncaafb.GRASS = GRASS
    #ncaafb.TIME_ZONES = TIME_ZONESovero
    #ncaafb.DIVISION = DIVISION
    ncaafb.streak = S2.prepare.streak
    #ncaafb.show_metacode=1
    nice = ncaafb.sdb_query(
      "((date-p:date)*(season==p:season) or None)-1 as rest,"
      "self.streak(self,_i,'su') as 'streak',"
      "full name or self.abbr_to_full.get(team) as 'full name',"
      "float(line) as 'line',"
      "(total>27)*float(total) or None as 'total',"
     "(quarter scores is not None and len(quarter scores)-4) or overtime as 'overtime',"
      "1*(game type == 'PO') as 'playoffs',"
      "self.streak(self,_i,'site') as 'site streak',"
      "self.streak(self,_i,'ats') as 'ats streak',"
      "self.streak(self,_i,'ou') as 'ou streak',"
      "points-(total-line)/2. as 'dps',"
      "o:points-(total+line)/2. as 'dpa',"
      "points-o:points as 'margin',"
      "points+line-o:points as 'ats margin',"
      "points+o:points-total as 'ou margin',"
      "interceptions+fumbles lost as 'turnovers',"
#      "passes + rushes + o:sacks as 'plays',"
      "quarter scores[0]-o:quarter scores[0] as 'margin after the first',"
      "quarter scores[0]+quarter scores[1]-o:quarter scores[0]-o:quarter scores[1] as 'margin at the half',"
      "quarter scores[0]+quarter scores[1]+quarter scores[2]-o:quarter scores[0]-o:quarter scores[1]-o:quarter scores[2] as 'margin after the third',"
      "interceptions+fumbles lost-o:interceptions-o:fumbles lost as 'turnover margin',"
      "self.week_from_date(date) as 'week',"
      "self.season_week_day_from_date(date)[-1] as 'day',"
  "self.team_d.get(team,self.look_back_dict()).look_back_get(season,'')[1] as 'division',"
                    "self.team_d.get(team,self.look_back_dict()).look_back_get(season,'')[2] as 'conference',"
                    "self.team_d.get(team,self.look_back_dict()).look_back_get(season,'')[3] as 'cdivision',"
#                    "self.coach_d.get(team,self.look_back_dict()).look_back_get(season,'') as coach,"
      "int(str(date)[4:6]) as month@1")[0]

    for col in nice:

        if col.name in ["ats margin","ou margin"]:
            col.str_format = """lambda line:"%s%d%s"%('+'*(0<line) + '-'*(line<0),int(abs(line)),"'"*(line!=int(line)))"""
            # '   this single quote helps emacs keep the syntax highlighting correct
            col.set_format(col.str_format)

        offset = ncaafb.offset_from_header(col.name,owners=[''])
        if offset is None:
            print "adding nice column",col.name
            ncaafb.add_object(col)
        else:
            print col.name," is already a column: overwrite"
            ncaafb.data[offset] = col

    return ncaafb

# This file:
#     builds reference and nice fields

import sys, os, re, string
import PyQL.py_tools
import PyQL.columns

import NCAABB.teams
import S2.prepare
add_join_fields = S2.prepare.add_join_fields
add_std_fields = S2.prepare.add_std_fields
from S2.directory import DATA_DIR
DATA_DIR = DATA_DIR("ncaabb")

def clean_name(name):
    ret = name.strip().replace('.','').replace("'",'').replace("-",' ').replace("(",'').replace(")",'')
    return re.sub("[\s]+",' ',ret)

def clean_team(name):
    return name.replace('-','').strip()

def season_from_date(date):
    date = str(date)
    season = int(date[:4])
    if date[4] == '0': season -= 1
    return season


import UserDict

def set_hierarchy_fields(ncaabb):
        #ncaabb.playoffs_from_date = playoffs_from_date
        nice = ncaabb.sdb_query("filter(lambda x:x is not None,[Schedule.points,Box.points])[-1] as 'points',"
                                "filter(lambda x:x is not None,[Schedule.half scores,Box.half scores])[-1] as 'half scores',"
             "filter(lambda x:x is not None,[Schedule.line,Box.line,SDB.line])[-1] as 'line',"
             "filter(lambda x:x is not None,[Schedule.total,Box.total,SDB.total])[-1] as 'total'"
                                 "@1")[0]
        for col in nice:
            if col.name in ncaabb.headers:
                print col.name,"is already a column"
                continue
            print "adding hierarchy column",col.name
            ncaabb.add_object(col)
        del_these = []
        for h,header in enumerate(ncaabb.headers):
            if header in ['Schedule.total','Box.total','SDB.total','Schedule.line','Box.line','SDB.line']:
                del_these.append(h)
                pass
        del_these.sort()
        del_these.reverse()
        for h in del_these:
            print "NOT del extra column",h,ncaabb.headers[h]
            #ncaabb.del_column(h,rebuild_header_dict=0)
        ncaabb.build_header_dict()


def add_nice_fields(ncaabb):
        set_hierarchy_fields(ncaabb)
        ncaabb.streak = S2.prepare.streak
        ncaabb.day_from_date = PyQL.py_tools.day_from_date
        #ncaabb.division_from_nickname_season = NCAABB.teams.division_from_nickname_season
        #ncaabb.conference_d = conference_dict()
        #ncaabb.team_d = team_dict()
        #ncaabb.look_back_dict = look_back_dict
        #ncaabb.find_conference = NCAABB.teams.find_conference
        #ncaabb.playoffs_from_date = playoffs_from_date
        nice = ncaabb.sdb_query("((date-p:date)*(season==p:season) or None)-1 as rest,"
                                "float(line) as 'line',"
                                "float(total) as 'total',"
                                "float(points-(total-line)/2.) as dps,"
                                "float(o:points-(total+line)/2.) as dpa,"
                                "points-o:points as margin,"
                                "float(points+line-o:points) as ats margin,"
                                "float(points+o:points-total) as ou margin,"
                                "half scores[0]-o:half scores[0] as margin at the half,"
                                "len(half scores)-2 as overtime,"
                                "self.day_from_date(date) as day,"
                                #"self.find_conference(team,season) as conference,"
                                #"self.conference_d.get(self.team_d.get(team,self.look_back_dict()).look_back_get(season,team),self.look_back_dict()).look_back_get(season,'') as conference,"
                          #"self.team_d.get(team,self.look_back_dict()).look_back_get(season,team) as team,"
                          "self.streak(self,_i,'su') as streak,"
                          "self.streak(self,_i,'ats') as ats streak,"
                          "self.streak(self,_i,'ou') as ou streak,"
                          "self.streak(self,_i,'site') as site streak,"
                          "int(str(date)[4:6]) as month@1")[0]
        for col in nice:
            offset = ncaabb.offset_from_header(col.name)
            if offset is None:
                print "adding nice column",col.name
                ncaabb.add_object(col)
            else:
                print col.name," is already a column: overwrite"
                ncaabb.data[offset] = col

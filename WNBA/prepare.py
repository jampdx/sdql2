# This file:
#     builds reference and nice fields

import sys, os, re, string
import PyQL.py_tools
import PyQL.columns

import WNBA.teams
import S2.prepare
add_join_fields = S2.prepare.add_join_fields
add_std_fields = S2.prepare.add_std_fields
from S2.directory import DATA_DIR
DATA_DIR = DATA_DIR("wnba")

def clean_name(name):
    ret = name.strip().replace('.','').replace("'",'').replace("-",' ').replace("(",'').replace(")",'')
    return re.sub("[\s]+",' ',ret)

def clean_team(name):
    return name.replace('-','').strip()

def season_from_date(date):
    date = str(date)
    season = int(date[:4])
    return season

def playoffs_from_date(date):
	season = season_from_date(date)
	if season==2011 and 20110911<date: return 1
	if season==2012 and 20120923<date: return 1
	if season==2013 and 20130915<date: return 1
	if season==2014 and 20140817<date: return 1
	if season==2015 and 20150913<date: return 1
	if season==2016 and 20160918<date: return 1
	if season==2017 and 20170905<date: return 1
	if season==2018 and 20180820<date: return 1
	if season==2019 and 20190908<date: return 1
	if season==2020 and 20200914<date: return 1

	return 0

def set_hierarchy_fields(wnba):
        print "wnba.heaersd:",wnba.headers
        #wnba.playoffs_from_date = playoffs_from_date
        nice = wnba.sdb_query("filter(lambda x:x is not None,[Schedule.points,Box.points])[-1] as 'points',"
                                "filter(lambda x:x is not None,[Schedule.quarter scores,Box.quarter scores])[-1] as 'quarter scores',"
                                "filter(lambda x:x is not None,[Schedule.line,Box.line,SDB.line])[-1] as 'line',"
                                "filter(lambda x:x is not None,[Schedule.total,Box.total,SDB.total])[-1] as 'total'"
                                 "@1")[0]
        for col in nice:
            if col.name in wnba.headers:
                print col.name,"is already a column"
                continue
            print "adding hierarchy column",col.name
            wnba.add_object(col)

def add_nice_fields(wnba):
        set_hierarchy_fields(wnba)
        wnba.streak = S2.prepare.streak
        wnba.day_from_date = PyQL.py_tools.day_from_date
        #wnba.division_from_nickname_season = WNBA.teams.division_from_nickname_season
        #wnba.conference_d = conference_dict()
        #wnba.team_d = team_dict()
        #wnba.look_back_dict = look_back_dict
        wnba.find_conference = WNBA.teams.conference_from_nickname_season
        wnba.playoffs_from_date = playoffs_from_date
        nice = wnba.sdb_query("((date-p:date)*(season==p:season) or None)-1 as rest,"
                                "float(line) as 'line',"
                                "float(total) as 'total',"
                                "float(points-(total-line)/2.) as dps,"
                                "float(o:points-(total+line)/2.) as dpa,"
                                "points-o:points as margin,"
                                "float(points+line-o:points) as ats margin,"
                                "float(points+o:points-total) as ou margin,"
                                "self.day_from_date(date) as day,"
                                "self.playoffs_from_date(date) as playoffs,"
                                "self.find_conference(team,season) as conference,"
                                "self.streak(self,_i,'su') as streak,"
                                "self.streak(self,_i,'ats') as ats streak,"
                                "self.streak(self,_i,'ou') as ou streak,"
                                "self.streak(self,_i,'site') as site streak,"
                                "int(str(date)[4:6]) as month@1")[0]
        for col in nice:
            offset = wnba.offset_from_header(col.name)
            if offset is None:
                print "adding nice column",col.name
                wnba.add_object(col)
            else:
                print col.name," is already a column: overwrite"
                wnba.data[offset] = col

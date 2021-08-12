import NHL.teams
import sys, os, re, string
import PyQL.py_tools
import PyQL.columns
import PyQL.column_types
import NHL.lines

import S2.prepare
add_join_fields = S2.prepare.add_join_fields
add_std_fields = S2.prepare.add_std_fields

# use NHL.lines
def XXXother_line(line):
    if line>420: return -80-line
    if line>400: return -70-line
    if line>360: return -50-line
    if line>300: return -30-line
    if line>170: return -20-line
    if line>140: return -15-line
    if line>=100: return -10-line
    if line>=-110: return -210-line
    if line>=-170: return -10-line
    if line>=140: return -15-line
    if line>=-200: return -20-line
    if line>=-300: return -30-line
    if line>=-360: return -50-line
    if line>=-400: return -70-line
    return -80-line

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
    if season == 2020: # covid times
        if sdate[4]=='0' and sdate[5] in "123456789":
            season = season - 1
    elif sdate[4]=='0' and sdate[5] in "1234567":
        season = season - 1
    return season

def clean_name(name):
    ret = name.strip().replace('.','').replace("'",'').replace("-",' ').replace("(",'').replace(")",'')
    return re.sub("[\s]+",' ',ret)

def clean_team(name):
    return name.replace('-','').strip()


def playoffs_from_date(date):
    if 20070410 < date < 20070800: return 1
    if 20080408 < date < 20080800: return 1
    if 20090414 < date < 20090800: return 1
    if 20100413 < date < 20100800: return 1
    if 20110412 < date < 20110800: return 1
    if 20120410 < date < 20120800: return 1
    if 20130429 < date < 20130800: return 1
    if 20140415 < date < 20140800: return 1
    if 20150414 < date < 20150800: return 1
    if 20160412 < date < 20160800: return 1
    if 20170411 < date < 20170800: return 1
    if 20180410 < date < 20180800: return 1
    if 20190409 < date < 20190800: return 1
    if 20200731 < date < 20201000: return 1
    if 20210514 < date < 20211000: return 1
    return 0


# need to do this, at least for streak in nice
def set_hierarchy_fields(nhl):
        #nhl.playoffs_from_date = playoffs_from_date
        nice = nhl.sdb_query("filter(lambda x:x is not None,[Schedule.goals,Box.goals])[-1] as 'goals',"
  "filter(lambda x:x is not None,[Schedule.period scores,Box.period scores])[-1] as 'period scores',"
 "int(filter(lambda x:x is not None,[Schedule.line,Box.line,SDB.line])[-1]) as 'line',"
 "filter(lambda x:x is not None,[Schedule.total,Box.total,SDB.total])[-1] as 'total'"
                                 "@1")[0]
        for col in nice:
            if col.name in nhl.headers:
                print col.name,"is already a column overwrite"
                nhl.data[offset] = col
                continue
            print "adding hierarchy column",col.name
            nhl.add_object(col)


# made these SDB shortcuts??
def add_nice_fields(nhl):
    #print "nhl.goals",nhl.offset_from_header("goals")
    #set_hierarchy_fields(nhl)
    #print "nhl.goals",nhl.offset_from_header("goals") # note that `goals` move to the default set in hierarchy_fields
    nhl.division_conference_from_nickname_season = NHL.teams.division_conference_from_nickname_season
    nhl.streak = S2.prepare.streak
    nhl.other_line = NHL.lines.other_line
    nhl.playoffs_from_date = playoffs_from_date
    nhl.day_from_date = PyQL.py_tools.day_from_date
    nice = nhl.sdb_query("int(str(date)[4:6]) as month,"
                         "self.division_conference_from_nickname_season(team,season)[0] as division,"
                         "self.division_conference_from_nickname_season(team,season)[1] as conference,"
                         "(goals-o:goals) as 'margin',"
                         "(goals+o:goals-total) as 'ou margin',"
                         "PyQL.column_types.MLB_Line(self.other_line(o:line) if (line is None) else line) as 'line',"
                         "1*(len(period scores)>3) as 'overtime',"
                         "self.streak(self,_i,'su') as 'streak',"
                         "self.day_from_date(date) as day,"
                         "self.streak(self,_i,'ou') as 'ou streak',"
                         "self.streak(self,_i,'site') as 'site streak',"
                         "((date-p:date)*(season==p:season) or None)-1 as 'rest',"
                         "self.playoffs_from_date(date) as 'playoffs'"
                         "@1")[0]

    for col in nice:
        offset = nhl.offset_from_header(col.name)
        if offset is None:
            print "adding nice column:",col.name ,"eg:",col.data[100],len(col.data)
            nhl.add_object(col)
        else:
            print col.name," is already a column: overwrite"
            print "now had Nones:",len(filter(lambda x:x is None,nhl.data[offset].data))
            nhl.data[offset].data = col.data
            print "nmice col had Nones:",len(filter(lambda x:x is None,col.data)),len(col.data)

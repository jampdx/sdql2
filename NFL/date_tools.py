import sys,time
import PyQL.py_tools

delta_day = {}
delta_day["Sunday"] = 0
delta_day["Monday"] = 1
delta_day["Tuesday"] = 2
delta_day["Wednesday"] = 3
delta_day["Thursday"] = -3
delta_day["Friday"] = -2
delta_day["Saturday"] = -1
first_sunday = {}
first_sunday[1989] = 19890910
first_sunday[1990] = 19900909
first_sunday[1991] = 19910901
first_sunday[1992] = 19920906
first_sunday[1993] = 19930905
first_sunday[1994] = 19940904
first_sunday[1995] = 19950903
first_sunday[1996] = 19960901
first_sunday[1997] = 19970831
first_sunday[1998] = 19980906
first_sunday[1999] = 19990912
first_sunday[2000] = 20000903
first_sunday[2001] = 20010909
first_sunday[2002] = 20020908
first_sunday[2003] = 20030907
first_sunday[2004] = 20040912
first_sunday[2005] = 20050911
first_sunday[2006] = 20060910
first_sunday[2007] = 20070909
first_sunday[2008] = 20080907
first_sunday[2009] = 20090913
first_sunday[2010] = 20100912
first_sunday[2011] = 20110911
first_sunday[2012] = 20120909
first_sunday[2013] = 20130908
first_sunday[2014] = 20140907
first_sunday[2015] = 20150913
first_sunday[2016] = 20160911
first_sunday[2017] = 20170910
first_sunday[2018] = 20180909
first_sunday[2019] = 20190908
first_sunday[2020] = 20200913

for s in  first_sunday.keys():
    first_sunday[s] = PyQL.py_tools.Date8(first_sunday[s])

def find_week_from_date(date=None):
    if not date: date = PyQL.py_tools.today()
    season,week,day = find_season_week_day_from_date(date)
    if type(day) is type(123): week+=1
    return week or 1

def find_season_week_day_from_date(date=None):
    if not date: date = PyQL.py_tools.today()
    seasons = first_sunday.keys()
    seasons.sort(lambda x,y:cmp(y,x))
    for season in seasons:
        if first_sunday[season]-7 <= date: break

    day_of_season = PyQL.py_tools.delta_days(date,first_sunday[season])

    week = day_of_season/7 + 1
    print "dos:",day_of_season,week
    if day_of_season < 0:
        day = (day_of_season+7)%7
    else:
        day = day_of_season%7

    if day == 0:
        day = "Sunday"
    elif day == 1:
        day = "Monday"
    elif day == 2:
        day = "Tuesday"
        #week += 1
    elif day == 3:
        day = "Wednesday"
        #week += 1
    elif day == 4:
        week += 1
        day = "Thursday"
    elif day == 5:
        week += 1
        day = "Friday"
    elif day == 6:
        week += 1
        day = "Saturday"
    if week > 22: # offseason
        if first_sunday.get(season+1): # next season is loaded
            return find_season_week_day_from_date(first_sunday.get(season+1))
        else:
            return season,22,'Sunday'
    return  season,week,day

def find_date(season,week,day):
    #print "find_date:",season,week,day
    fs_date = "%s"%first_sunday[season]
    fs_seconds = time.mktime((int(fs_date[:4]),int(fs_date[4:6]),int(fs_date[6:8]),0,0,0,0,0,0))
    delta_seconds = (7*(week - 1) + delta_day[day]) * 86400
    game_seconds = fs_seconds + delta_seconds
    #print game_seconds
    return int(time.strftime("%Y%m%d",time.localtime(game_seconds)) )

def dates_from_week_season(week,season):
    fs = first_sunday[season]
    ws = fs + 7*(week-1)
    ret = []
    for i in range(-4,2):
        ret.append(ws+i)
    return ret


neutral_sites = """19900128,Broncos,Fortyniners
19910127,Giants,Bills
19920126,Bills,Redskins
19930131,Cowboys,Bills
19940130,Bills,Cowboys
19950129,Fortyniners,Chargers
19960128,Steelers,Cowboys
19970126,Packers,Patriots
19980125,Broncos,Packers
19990131,Falcons,Broncos
20000130,Titans,Rams
20010128,Giants,Ravens
20020203,Patriots,Rams
20030126,Buccaneers,Raiders
20031027,Chargers,Dolphins
20040201,Patriots,Panthers
20050206,Eagles,Patriots
20051002,Cardinals,Fortyniners
20060205,Steelers,Seahawks
20070204,Bears,Colts
20071028,Dolphins,Giants
20080203,Patriots,Giants
20081207,Bills,Dolphins
20081026,Saints,Chargers
20090201,Cardinals,Steelers
20091203,Bills,Jets
20091025,Buccaneers,Patriots
20100207,Colts,Saints
20101107,Bills,Bears
20101031,Fortyniners,Broncos
20101213,Vikings,Giants
20110206,Packers,Steelers
20111023,Buccaneers,Bears
20111130,Bills,Redskins
20120205,Patriots,Giants
20121028,Rams,Patriots
20121216,Bills,Seahawks
20130203,Fortyniners,Ravens
20130929,Vikings,Steelers
20131027,Jaguars,Fortyniners
20140202,Broncos,Seahawks
20140928,Raiders,Dolphins
20141026,Falcons,Lions
20141109,Jaguars,Cowboys
20150201,Seahawks,Patriots
20151004,Dolphins,Jets
20151025,Jaguars,Bills
20151101,Chiefs,Lions
20160207,Broncos,Panthers
20161002,Jaguars,Colts
20161023,Rams,Giants
20161030,Bengals,Redskins
20161121,Raiders,Texans
20170205,Falcons,Patriots
20170924,Jaguars,Ravens
20171001,Dolphins,Saints
20171022,Rams,Cardinals
20171029,Browns,Vikings
20171119,Raiders,Patriots
20180204,Patriots,Eagles
20181014,Seahawks,Raiders
20181021,Titans,Chargers
20181028,Eagles,Jaguars
20190203,Rams,Patriots
20191006,Raiders,Bears
20191013,Buccaneers,Panthers
20191027,Rams,Bengals
20191103,Jaguars,Texans
20191118,Chargers,Chiefs
20200202,Chiefs,Fortyniners
20201207,Fortyniners,Bills
20201213,Fortyniners,Redskins
20210103,Fortyniners,Seahawks"""

N_SITES = {}
for line in neutral_sites.split('\n'):
    date,h,a = line.split(',')
    N_SITES[(date,h)] = N_SITES[(date,a)] = 'neutral'
#print N_SITES

if __name__ == "__main__":
    date = 20201202
    print find_season_week_day_from_date(date)
    #print find_week_from_date(date)
    #print dates_from_week_season(week=9,season=2013)

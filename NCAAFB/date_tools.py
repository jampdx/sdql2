import sys,time
import PyQL.py_tools

# this is for the NFL: update

delta_day = {}
delta_day["Sunday"] = 0
delta_day["Monday"] = 1
delta_day["Tuesday"] = 2
delta_day["Wednesday"] = -4
delta_day["Thursday"] = -3
delta_day["Friday"] = -2
delta_day["Saturday"] = -1
first_sunday = {}
first_sunday[1980] = 19800831
first_sunday[1981] = 19810906
first_sunday[1982] = 19820905
first_sunday[1983] = 19830828
first_sunday[1984] = 19840826
first_sunday[1985] = 19850901
first_sunday[1986] = 19860831
first_sunday[1987] = 19870830
first_sunday[1988] = 19880828
first_sunday[1989] = 19890903
first_sunday[1990] = 19900826
first_sunday[1991] = 19910901
first_sunday[1992] = 19920830
first_sunday[1993] = 19930829
first_sunday[1994] = 19940828
first_sunday[1995] = 19950827
first_sunday[1996] = 19960825
first_sunday[1997] = 19970824
first_sunday[1998] = 19980830
first_sunday[1999] = 19990829
first_sunday[2000] = 20000827
first_sunday[2001] = 20010826
first_sunday[2002] = 20020825
first_sunday[2003] = 20030824
first_sunday[2004] = 20040829
first_sunday[2005] = 20050904
first_sunday[2006] = 20060903
first_sunday[2007] = 20070902
first_sunday[2008] = 20080831
first_sunday[2009] = 20090906
first_sunday[2010] = 20100905
first_sunday[2011] = 20110904
first_sunday[2012] = 20120902
first_sunday[2013] = 20130901
first_sunday[2014] = 20140831
first_sunday[2015] = 20150906
first_sunday[2016] = 20160904
first_sunday[2017] = 20170903
first_sunday[2018] = 20180902
first_sunday[2019] = 20190901
first_sunday[2020] = 20200906

for s in  first_sunday.keys():
    first_sunday[s] = PyQL.py_tools.Date8(first_sunday[s])

def find_week_from_date(date=None):
    if not date: date = PyQL.py_tools.today()
    season,week,day = find_season_week_day_from_date(date)
    if type(day) is type(123): return week+1
    return week

def find_season_week_day_from_date(date=None):
    if not date: date = PyQL.py_tools.today()
    seasons = first_sunday.keys()
    seasons.sort(lambda x,y:cmp(y,x))
    for season in seasons:
        if first_sunday[season]-14 <= date: break

    day_of_season = PyQL.py_tools.delta_days(date,first_sunday[season])
    #print "dos:",day_of_season
    week = day_of_season/7 + 1
    if day_of_season < -7:
        day = (day_of_season+14)%7
    elif day_of_season < 0:
        day = (day_of_season+7)%7
    else:
        day = day_of_season%7
    #print "week:",week
    if day == 0:
        day = "Sunday"
    elif day == 1:
        day = "Monday"
    elif day == 2:
        day = "Tuesday"
        week += 1
    elif day == 3:
        day = "Wednesday"
        week += 1
    elif day == 4:
        week += 1
        day = "Thursday"
    elif day == 5:
        week += 1
        day = "Friday"
    elif day == 6:
        week += 1
        day = "Saturday"
    if day_of_season<0:
        week=1
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
    #print "w,s",week,season
    #print 'fss:',first_sunday[season],type(first_sunday[season]),len(str(first_sunday[season]))
    fs =  PyQL.py_tools.Date8(first_sunday[season])
    ws = fs + 7*(week-1)
    ret = []
    for i in range(-4,2):
        ret.append(ws+i)
    return ret

if __name__ == "__main__":
    date = PyQL.py_tools.Date8(20170826)
    print find_season_week_day_from_date(date)
    #print find_week_from_date(date)
    #print dates_from_week_season(week=9,season=2013)

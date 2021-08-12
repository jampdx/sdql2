# a dictionary of d[team_key][season] = (surface==grass)
from NFL.nfl_dt import CURRENT_SEASON

PATCH = {}
PATCH[(20180204,'Patriots')] = 'artificial'
PATCH[(20180204,'Eagles')] =  'artificial'
PATCH[(20150913,'Texans')] = 'grass'
PATCH[(20150913,'Chiefs')] = 'grass'
# from Ogn google group
PTXT = """
20031027,Chargers,Dolphins,grass
20051002,Cardinals,Fortyniners,grass
20071028,Dolphins,Giants,grass
20081026,Saints,Chargers,grass
20081207,Bills,Dolphins,grass
20091025,Buccaneers,Patriots,grass
20091203,Bills,Jets,grass
20101031,Fortyniners,Broncos,grass
20101107,Bills,Bears,grass
20101213,Vikings,Giants,grass
20111023,Buccaneers,Bears,grass
20121028,Rams,Patriots,grass
20121216,Bills,Seahawks,grass
20130929,Vikings,Steelers,grass
20131027,Jaguars,Fortyniners,grass
20140928,Raiders,Dolphins,grass
20141026,Falcons,Lions,grass
20141109,Jaguars,Cowboys,grass
20151004,Dolphins,Jets,grass
20151025,Jaguars,Bills,grass
20151101,Chiefs,Lions,grass
20161002,Jaguars,Colts,grass
20161023,Rams,Giants,grass
20161030,Bengals,Redskins,grass
20161121,Raiders,Texans,grass
20170924,Jaguars,Ravens,grass
20171001,Dolphins,Saints,grass
20171022,Rams,Cardinals,grass
20171029,Browns,Vikings,grass
20171119,Raiders,Patriots,grass
20150201,Seahawks,Patriots,grass
20110206,Packers,Steelers,artificial
20100207,Colts,Saints,grass
20080203,Patriots,Giants,grass
20070204,Bears,Colts,grass
20040201,Patriots,Panthers,artificial"""
for line in PTXT.split('\n'):
    if not line: continue
    parts = line.split(',')
    PATCH[(int(parts[0]),parts[1])] = parts[3]
    PATCH[(int(parts[0]),parts[2])] = parts[3]
#print "PATCH  ",PATCH
lbd = """
1989,Bears,grass
1989,Bengals,artificial
2000,Bengals,grass
2004,Bengals,artificial
1989,Bills,artificial
1989,Broncos,grass
1989,Browns,grass
1989,Buccaneers,grass
1989,Cardinals,grass
1989,Chargers,grass
2020,Chargers,artificial
1989,Chiefs,artificial
1994,Chiefs,grass
1989,Colts,artificial
1989,Cowboys,artificial
1989,Dolphins,grass
1989,Eagles,artificial
2003,Eagles,grass
1989,Falcons,grass
1992,Falcons,artificial
1989,Fortyniners,grass
1989,Giants,artificial
2000,Giants,grass
2002,Giants,artificial
1995,Jaguars,grass
1989,Jets,artificial
2000,Jets,grass
2002,Jets,artificial
1989,Lions,artificial
1989,Oilers,artificial
1989,Packers,grass
1995,Panthers,grass
1989,Patriots,artificial
1991,Patriots,grass
2006,Patriots,artificial
1989,Raiders,grass
1989,Rams,grass
1995,Rams,artificial
2016,Rams,grass
2020,Rams,artificial
1996,Ravens,grass
2003,Ravens,artificial
2016,Ravens,grass
1989,Redskins,grass
1989,Saints,artificial
1989,Seahawks,artificial
1989,Steelers,artificial
2001,Steelers,grass
2002,Texans,grass
2015,Texans,artificial
1989,Titans,artificial
1997,Titans,grass
1998,Titans,artificial
1999,Titans,grass
1989,Vikings,artificial"""
# the Texans played week 1, 2015 on grass and this is handled in prepare.py

d = {}
for line in map(lambda x:x.strip(),lbd.split()):
    if not line: continue
    y,t,s = line.split(',')
    y = int(y)
    d.setdefault(t,{})
    for i in range(y,CURRENT_SEASON+1):
        d[t][i] = s
        #print 'setting:',i,t,s

if __name__ == "__main__":
    print d["Rams"]
    #dump_for_lbd()

""" util for NFL/Source/ level code player lookup.
    the box scores have a master list of players.
    game book has `F. Last` name the the H/A team is often not clear
"""
from parse_NFL_box import ROSTER_DIR
import cPickle
from NFL.nfl_dt import CURRENT_SEASON
import os
import glob

def load_roster(season=CURRENT_SEASON):
    d = {}
    for f in glob.glob(os.path.join(ROSTER_DIR,"*_%s.pkl"%(season,))):
        team = os.path.basename(f).split('_',1)[0]
        d[team] = cPickle.load(open(f))
    return d
roster = load_roster()
#print 'Ravens roster:',roster['Ravens']

def find_player_on_team(player,team):
    #print "roster looking for",player,"on",team,roster[team]
    player = player.replace("-"," ")
    pparts = player.split(".")
    lenf = len(pparts[0])
    if len(pparts)!=2:
        print("surprising player",player)
        raise Exception

    m = []
    for first,last in roster[{'49ers':'Fortyniners'}.get(team,team)]:
        if first[0].lower() == pparts[0].lower() and last.lower() == pparts[-1].lower():
            m.append('%s %s'%(first,last))
        elif first[:lenf].lower() == pparts[0].lower() and last.lower().split(' ')[-1] == pparts[-1].lower():
            m.append('%s %s'%(first,last))
        elif first[:lenf].lower() == pparts[0].lower() and last.lower() == pparts[-1].lower().split(' ')[0]:
            m.append('%s %s'%(first,last))
        elif first[:lenf].lower() == pparts[0].lower() and last.lower().split(' ')[-1] == pparts[-1].lower().split(' ')[-1]:
            m.append('%s %s'%(first,last))
    #print "returning",m
    return m

#print find_player_on_team(player="J. Wynn",team='Vikings')

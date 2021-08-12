# a dictionary of d([season,team key)] = seed


round_1 = ([1,8],[4,5],[3,6],[2,7])
round_2 = ([1,4],[1,5],[4,8],[5,8],[2,3],[2,6],[3,7],[6,7])
round_3 = ([1,3],[1,6],[1,2],[1,7],[3,8],[6,8],[2,8],[7,8],
           [3,4],[4,6],[2,4],[4,7],[3,5],[5,6],[2,5],[5,7])
#returns the round of the playoffs , need conference for finals
def round(team_seed,opp_seed,conference,opp_conference):
    if conference != opp_conference: return 4
    teams = [team_seed,opp_seed]
    teams.sort()
    if teams in round_1: return 1
    if teams in round_2: return 2
    if teams in round_3: return 3    
    
d = {}
d[(1998, 'Seventysixers')] = 6
d[(1998, 'Bucks')] = 7
d[(1998, 'Hawks')] = 4
d[(1998, 'Heat')] = 1
d[(1998, 'Jazz')] = 3
d[(1998, 'Kings')] = 6
d[(1998, 'Knicks')] = 8
d[(1998, 'Lakers')] = 4
d[(1998, 'Magic')] = 3
d[(1998, 'Pacers')] = 2
d[(1998, 'Pistons')] = 5
d[(1998, 'Rockets')] = 5
d[(1998, 'Spurs')] = 1
d[(1998, 'Suns')] = 7
d[(1998, 'Timberwolves')] = 8
d[(1998, 'Trailblazers')] = 2
d[(1999, 'Seventysixers')] = 5
d[(1999, 'Bucks')] = 8
d[(1999, 'Heat')] = 2
d[(1999, 'Hornets')] = 4
d[(1999, 'Jazz')] = 2
d[(1999, 'Kings')] = 8
d[(1999, 'Knicks')] = 3
d[(1999, 'Lakers')] = 1
d[(1999, 'Pacers')] = 1
d[(1999, 'Pistons')] = 7
d[(1999, 'Raptors')] = 6
d[(1999, 'Spurs')] = 4
d[(1999, 'Suns')] = 5
d[(1999, 'Supersonics')] = 7
d[(1999, 'Timberwolves')] = 6
d[(1999, 'Trailblazers')] = 3
d[(2000, 'Seventysixers')] = 1
d[(2000, 'Bucks')] = 2
d[(2000, 'Heat')] = 3
d[(2000, 'Hornets')] = 6
d[(2000, 'Jazz')] = 4
d[(2000, 'Kings')] = 3
d[(2000, 'Knicks')] = 4
d[(2000, 'Lakers')] = 2
d[(2000, 'Magic')] = 7
d[(2000, 'Mavericks')] = 5
d[(2000, 'Pacers')] = 8
d[(2000, 'Raptors')] = 5
d[(2000, 'Spurs')] = 1
d[(2000, 'Suns')] = 6
d[(2000, 'Timberwolves')] = 8
d[(2000, 'Trailblazers')] = 7
d[(2001, 'Seventysixers')] = 6
d[(2001, 'Celtics')] = 3
d[(2001, 'Hornets')] = 4
d[(2001, 'Jazz')] = 8
d[(2001, 'Kings')] = 1
d[(2001, 'Lakers')] = 3
d[(2001, 'Magic')] = 5
d[(2001, 'Mavericks')] = 4
d[(2001, 'Nets')] = 1
d[(2001, 'Pacers')] = 8
d[(2001, 'Pistons')] = 2
d[(2001, 'Raptors')] = 7
d[(2001, 'Spurs')] = 2
d[(2001, 'Supersonics')] = 7
d[(2001, 'Timberwolves')] = 5
d[(2001, 'Trailblazers')] = 6
d[(2002, 'Seventysixers')] = 4
d[(2002, 'Bucks')] = 7
d[(2002, 'Celtics')] = 6
d[(2002, 'Hornets')] = 5
d[(2002, 'Jazz')] = 7
d[(2002, 'Kings')] = 2
d[(2002, 'Lakers')] = 5
d[(2002, 'Magic')] = 8
d[(2002, 'Mavericks')] = 3
d[(2002, 'Nets')] = 2
d[(2002, 'Pacers')] = 3
d[(2002, 'Pistons')] = 1
d[(2002, 'Spurs')] = 1
d[(2002, 'Suns')] = 8
d[(2002, 'Timberwolves')] = 4
d[(2002, 'Trailblazers')] = 6
d[(2003, 'Bucks')] = 6
d[(2003, 'Celtics')] = 8
d[(2003, 'Grizzlies')] = 6
d[(2003, 'Heat')] = 4
d[(2003, 'Hornets')] = 5
d[(2003, 'Kings')] = 4
d[(2003, 'Knicks')] = 7
d[(2003, 'Lakers')] = 2
d[(2003, 'Mavericks')] = 5
d[(2003, 'Nets')] = 2
d[(2003, 'Nuggets')] = 8
d[(2003, 'Pacers')] = 1
d[(2003, 'Pistons')] = 3
d[(2003, 'Rockets')] = 7
d[(2003, 'Spurs')] = 3
d[(2003, 'Timberwolves')] = 1
d[(2004, 'Seventysixers')] = 7
d[(2004, 'Bulls')] = 4
d[(2004, 'Celtics')] = 3
d[(2004, 'Grizzlies')] = 8
d[(2004, 'Heat')] = 1
d[(2004, 'Kings')] = 6
d[(2004, 'Mavericks')] = 4
d[(2004, 'Nets')] = 8
d[(2004, 'Nuggets')] = 7
d[(2004, 'Pacers')] = 6
d[(2004, 'Pistons')] = 2
d[(2004, 'Rockets')] = 5
d[(2004, 'Spurs')] = 2
d[(2004, 'Suns')] = 1
d[(2004, 'Supersonics')] = 3
d[(2004, 'Wizards')] = 5
d[(2005, 'Bucks')] = 8
d[(2005, 'Bulls')] = 7
d[(2005, 'Cavaliers')] = 4
d[(2005, 'Clippers')] = 6
d[(2005, 'Grizzlies')] = 5
d[(2005, 'Heat')] = 2
d[(2005, 'Kings')] = 8
d[(2005, 'Lakers')] = 7
d[(2005, 'Mavericks')] = 4
d[(2005, 'Nets')] = 3
d[(2005, 'Nuggets')] = 3
d[(2005, 'Pacers')] = 6
d[(2005, 'Pistons')] = 1
d[(2005, 'Spurs')] = 1
d[(2005, 'Suns')] = 2
d[(2005, 'Wizards')] = 5

d[(2006,"Pistons")] = 1
d[(2006,"Cavaliers")] = 2
d[(2006,"Raptors")] = 3
d[(2006,"Heat")] = 4
d[(2006,"Bulls")] = 5
d[(2006,"Nets")] = 6
d[(2006,"Wizards")] = 7
d[(2006,"Magic")] = 8

d[(2006,"Mavericks")] = 1
d[(2006,"Suns")] = 2
d[(2006,"Spurs")] = 3
d[(2006,"Jazz")] = 4
d[(2006,"Rockets")] = 5
d[(2006,"Nuggets")] = 6
d[(2006,"Lakers")] = 7
d[(2006,"Warriors")] = 8

d[(2007,"Celtics")] = 1
d[(2007,"Pistons")] = 2
d[(2007,"Magic")] = 3
d[(2007,"Cavaliers")] = 4
d[(2007,"Wizards")] = 5
d[(2007,"Raptors")] = 6
d[(2007,"Seventysixers")] = 7
d[(2007,"Hawks")] = 8

d[(2007,"Lakers")] = 1
d[(2007,"Hornets")] = 2
d[(2007,"Spurs")] = 3
d[(2007,"Jazz")] = 4
d[(2007,"Rockets")] = 5
d[(2007,"Suns")] = 6
d[(2007,"Mavericks")] = 7
d[(2007,"Nuggets")] = 8

d[(2008,"Cavaliers")] = 1
d[(2008,"Celtics")] = 2
d[(2008,"Magic")] = 3
d[(2008,"Hawks")] = 4
d[(2008,"Heat")] = 5
d[(2008,"Seventysixers")] = 6
d[(2008,"Bulls")] = 7
d[(2008,"Pistons")] = 8

d[(2008,"Lakers")] = 1
d[(2008,"Nuggets")] = 2
d[(2008,"Spurs")] = 3
d[(2008,"Trailblazers")] = 4
d[(2008,"Rockets")] = 5
d[(2008,"Mavericks")] = 6
d[(2008,"Hornets")] = 7
d[(2008,"Jazz")] = 8

d[(2009,"Cavaliers")] = 1
d[(2009,"Magic")] = 2
d[(2009,"Hawks")] = 3
d[(2009,"Celtics")] = 4
d[(2009,"Heat")] = 5
d[(2009,"Bucks")] = 6
d[(2009,"Bobcats")] = 7
d[(2009,"Bulls")] = 8

d[(2009,"Lakers")] = 1
d[(2009,"Mavericks")] = 2
d[(2009,"Suns")] = 3
d[(2009,"Nuggets")] = 4
d[(2009,"Jazz")] = 5
d[(2009,"Trailblazers")] = 6
d[(2009,"Spurs")] = 7
d[(2009,"Thunder")] = 8

d[(2010,"Bulls")] = 1
d[(2010,"Heat")] = 2
d[(2010,"Celtics")] = 3
d[(2010,"Magic")] = 4
d[(2010,"Hawks")] = 5
d[(2010,"Knicks")] = 6
d[(2010,"Seventysixers")] = 7
d[(2010,"Pacers")] = 8

d[(2010,"Spurs")] = 1
d[(2010,"Lakers")] = 2
d[(2010,"Mavericks")] = 3
d[(2010,"Thunder")] = 4
d[(2010,"Nuggets")] = 5
d[(2010,"Trailblazers")] = 6
d[(2010,"Hornets")] = 7
d[(2010,"Grizzlies")] = 8


if __name__ == "__main__":
    for i in range(1,9):
        for j in range(1,9):
            print i,j,round(i,j,1,1)

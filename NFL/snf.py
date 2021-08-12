import string

txt = """
1989	9	Redskins	Cowboys
1989	10	Chargers	Raiders
1989	11	Colts	Jets
1989	12	Saints	Rams
1989	13	Vikings	Bears
1989	14	Dolphins	Patriots
1989	15	Seahawks	Raiders
1990	1	Giants	Eagles
1990	2	Steelers	Oilers
1990	3	Buccaneers	Lions
1990	4	Cardinals	Redskins
1990	5	Bills	Raiders
1990	6	Bears	Rams
1990	8	Falcons	Bengals
1990	9	Vikings	Broncos
1990	10	Cowboys	Fortyniners
1990	11	Bengals	Steelers
1990	12	Chargers	Seahawks
1990	13	Vikings	Packers
1990	14	Dolphins	Eagles
1990	15	Lions	Bears
1990	17	Oilers	Steelers
1991	1	Redskins	Lions
1991	2	Bengals	Oilers
1991	3	Saints	Rams
1991	4	Cardinals	Cowboys
1991	5	Vikings	Broncos
1991	6	Colts	Steelers
1991	7	Seahawks	Raiders
1991	9	Giants	Redskins
1991	10	Broncos	Steelers
1991	11	Dolphins	Patriots
1991	12	Oilers	Browns
1991	13	Saints	Falcons
1991	14	Chargers	Raiders
1991	15	Buccaneers	Vikings
1991	16	Colts	Bills
1991	17	Seahawks	Rams
1992	1	Broncos	Raiders
1992	2	Cardinals	Eagles
1992	3	Bills	Colts
1992	4	Saints	Fortyniners
1992	5	Jets	Patriots
1992	6	Saints	Rams
1992	8	Chiefs	Steelers
1992	9	Redskins	Giants
1992	10	Bears	Bengals
1992	11	Broncos	Giants
1992	12	Seahawks	Chiefs
1992	13	Chargers	Raiders
1992	14	Buccaneers	Rams
1992	15	Oilers	Packers
1992	16	Dolphins	Jets
1992	17	Oilers	Bills
1993	1	Saints	Oilers
1993	2	Seahawks	Raiders
1993	3	Cardinals	Cowboys
1993	5	Bills	Giants
1993	6	Packers	Broncos
1993	8	Dolphins	Colts
1993	9	Vikings	Lions
1993	10	Redskins	Colts
1993	11	Chargers	Bears
1993	12	Buccaneers	Vikings
1993	13	Oilers	Steelers
1993	14	Fortyniners	Bengals
1993	15	Chargers	Packers
1993	16	Colts	Eagles
1993	17	Vikings	Chiefs
1993	18	Oilers	Jets
1994	1	Broncos	Chargers
1994	2	Cardinals	Giants
1994	3	Falcons	Chiefs
1994	4	Jets	Bears
1994	5	Bengals	Dolphins
1994	6	Eagles	Redskins
1994	9	Cardinals	Steelers
1994	10	Chiefs	Raiders
1994	11	Lions	Buccaneers
1994	12	Fortyniners	Rams
1994	13	Colts	Patriots
1994	14	Dolphins	Bills
1994	15	Falcons	Saints
1994	16	Seahawks	Raiders
1995	1	Broncos	Bills
1995	2	Cardinals	Eagles
1995	3	Vikings	Cowboys
1995	4	Jaguars	Packers
1995	5	Jets	Raiders
1995	6	Patriots	Broncos
1995	9	Redskins	Giants
1995	10	Chargers	Dolphins
1995	11	Eagles	Broncos
1995	12	Chiefs	Oilers
1995	13	Saints	Panthers
1995	14	Fortyniners	Bills
1995	15	Buccaneers	Packers
1995	16	Seahawks	Raiders
1996	1	Giants	Bills
1996	2	Cardinals	Dolphins
1996	3	Broncos	Buccaneers
1996	4	Falcons	Eagles
1996	5	Redskins	Jets
1996	6	Bengals	Oilers
1996	7	Colts	Ravens
1996	9	Patriots	Bills
1996	10	Saints	Fortyniners
1996	11	Panthers	Giants
1996	12	Raiders	Vikings
1996	13	Rams	Packers
1996	14	Chargers	Patriots
1996	15	Lions	Vikings
1996	16	Jaguars	Seahawks
1996	17	Chargers	Broncos
1997	1	Panthers	Redskins
1997	2	Cardinals	Cowboys
1997	3	Patriots	Jets
1997	4	Buccaneers	Dolphins
1997	5	Vikings	Eagles
1997	6	Bears	Saints
1997	7	Steelers	Colts
1997	9	Panthers	Falcons
1997	10	Packers	Lions
1997	11	Steelers	Ravens
1997	12	Chargers	Raiders
1997	13	Redskins	Giants
1997	14	Chargers	Broncos
1997	15	Dolphins	Lions
1997	16	Rams	Bears
1997	17	Seahawks	Fortyniners
1998	1	Chiefs	Raiders
1998	2	Patriots	Colts
1998	3	Cardinals	Eagles
1998	4	Ravens	Bengals
1998	5	Chiefs	Seahawks
1998	6	Giants	Falcons
1998	8	Panthers	Bills
1998	9	Seahawks	Raiders
1998	10	Buccaneers	Titans
1998	11	Lions	Bears
1998	12	Fortyniners	Saints
1998	13	Chargers	Broncos
1998	14	Vikings	Bears
1998	15	Dolphins	Jets
1998	16	Vikings	Jaguars
1998	17	Cowboys	Redskins
1999	1	Browns	Steelers
1999	2	Bills	Jets
1999	3	Patriots	Giants
1999	4	Seahawks	Raiders
1999	5	Packers	Buccaneers
1999	6	Cardinals	Redskins
1999	8	Lions	Buccaneers
1999	9	Dolphins	Titans
1999	10	Seahawks	Broncos
1999	11	Jaguars	Saints
1999	12	Panthers	Falcons
1999	13	Patriots	Cowboys
1999	14	Chiefs	Vikings
1999	15	Cardinals	Bills
1999	16	Fortyniners	Redskins
2000	1	Bills	Titans
2000	2	Cardinals	Cowboys
2000	3	Dolphins	Ravens
2000	4	Giants	Redskins
2000	5	Eagles	Falcons
2000	6	Jaguars	Ravens
2000	7	Bears	Vikings
2000	9	Chargers	Raiders
2000	10	Rams	Panthers
2000	11	Colts	Jets
2000	12	Steelers	Jaguars
2000	13	Cardinals	Giants
2000	14	Bears	Packers
2000	15	Raiders	Jets
2000	16	Cowboys	Giants
2001	1	Titans	Dolphins
2001	3	Cardinals	Broncos
2001	4	Eagles	Cowboys
2001	5	Fortyniners	Panthers
2001	6	Colts	Raiders
2001	9	Saints	Jets
2001	10	Seahawks	Raiders
2001	11	Patriots	Rams
2001	12	Vikings	Bears
2001	13	Fortyniners	Bills
2001	14	Broncos	Seahawks
2001	15	Ravens	Steelers
2001	16	Colts	Jets
2001	17	Saints	Redskins
2001	18	Buccaneers	Eagles
2002	1	Texans	Cowboys
2002	2	Steelers	Raiders
2002	3	Falcons	Bengals
2002	4	Seahawks	Vikings
2002	5	Browns	Ravens
2002	6	Broncos	Dolphins
2002	8	Redskins	Colts
2002	9	Giants	Jaguars
2002	10	Jets	Dolphins
2002	11	Raiders	Patriots
2002	12	Broncos	Colts
2002	13	Saints	Buccaneers
2002	14	Packers	Vikings
2002	15	Rams	Cardinals
2002	16	Patriots	Jets
2002	17	Bears	Buccaneers
2003	1	Titans	Raiders
2003	2	Vikings	Bears
2003	3	Dolphins	Bills
2003	4	Saints	Colts
2003	5	Steelers	Browns
2003	6	Seahawks	Fortyniners
2003	8	Chiefs	Bills
2003	9	Vikings	Packers
2003	10	Rams	Ravens
2003	11	Patriots	Cowboys
2003	12	Dolphins	Redskins
2003	13	Jaguars	Buccaneers
2003	14	Falcons	Panthers
2003	15	Saints	Giants
2003	16	Colts	Broncos
2003	17	Ravens	Steelers
2004	1	Broncos	Chiefs
2004	2	Bengals	Dolphins
2004	3	Dolphins	Steelers
2004	3	Raiders	Buccaneers
2004	4	Fortyniners	Rams
2004	5	Redskins	Ravens
2004	6	Saints	Vikings
2004	8	Bears	Fortyniners
2004	9	Ravens	Browns
2004	10	Patriots	Bills
2004	11	Texans	Packers
2004	12	Broncos	Raiders
2004	13	Jaguars	Steelers
2004	14	Redskins	Eagles
2004	15	Colts	Ravens
2004	16	Dolphins	Browns
2004	17	Giants	Cowboys
2005	1	Ravens	Colts
2005	2	Raiders	Chiefs
2005	3	Chargers	Giants
2005	4	Cardinals	Fortyniners
2005	5	Jaguars	Bengals
2005	6	Seahawks	Texans
2005	8	Patriots	Bills
2005	9	Redskins	Eagles
2005	10	Steelers	Browns
2005	11	Texans	Chiefs
2005	12	Jets	Saints
2005	13	Chargers	Raiders
2005	14	Packers	Lions
2005	15	Bears	Falcons
2005	16	Ravens	Vikings
2005	17	Cowboys	Rams
2006	1	Giants	Colts
2006	2	Cowboys	Redskins
2006	3	Patriots	Broncos
2006	4	Bears	Seahawks
2006	5	Chargers	Steelers
2006	6	Broncos	Raiders
2006	8	Panthers	Cowboys
2006	9	Patriots	Colts
2006	10	Giants	Bears
2006	11	Broncos\tChargers
2006	12	Eagles\tColts
2006	13	Seahawks\tBroncos
2006	14	Cowboys\tSaints
2006	15	Chargers\tChiefs
2006	17	Bears\tPackers
2007	1	Cowboys\tGiants
2007	2	Patriots\tChargers
2007	3	Bears\tCowboys
2007	4	Giants\tEagles
2007	5	Packers\tBears
2007	6	Seahawks\tSaints
2007	7	Broncos\tSteelers
2007	9	Eagles\tCowboys
2007	10	Chargers\tColts
2007	11	Bills\tPatriots
2007	12	Patriots\tEagles
2007	13	Steelers\tBengals
2007	14	Ravens\tColts
2007	15	Giants\tRedskins
2007	16	Vikings\tRedskins
2007	17	Colts\tTitans
2008	1	Colts\tBears
2008	2	Browns\tSteelers
2008	3	Packers\tCowboys
2008	4	Bears\tEagles
2008	5	Jaguars\tSteelers
2008	6	Chargers\tPatriots
2008	7	Buccaneers\tSeahawks
2008	9	Colts\tPatriots
2008	10	Eagles\tGiants
2008	11	Redskins\tCowboys
2008	12	Chargers\tColts
2008	13	Vikings\tBears
2008	14	Ravens\tRedskins
2008	15	Cowboys\tGiants
2008	16	Buccaneers\tChargers
2009\t1\tPackers\tBears
2009\t2\tCowboys\tGiants
2009\t3\tCardinals\tColts
2009\t4\tSteelers\tChargers
2009\t5\tTitans\tColts
2009\t6\tFalcons\tBears
2009\t7\tGiants\tCardinals
2009\t9\tEagles\tCowboys
2009\t10\tColts\tPatriots
2009\t11\tBears\tEagles
2009\t12\tRavens\tSteelers
2009\t13\tCardinals\tVikings
2009\t14\tGiants\tEagles
2009\t15\tPanthers\tVikings
2009\t16\tRedskins\tCowboys
2010\t1\tSaints\tVikings
2010\t1\tRedskins\tCowboys
2010\t2\tColts\tGiants
2010\t3\tDolphins\tJets
2010\t4\tGiants\tBears
2010\t5\tFortyniners\tEagles
2010\t6\tRedskins\tColts
2010\t7\tPackers\tVikings
2010\t8\tSaints\tSteelers
2010\t9\tPackers\tCowboys
2010\t10\tSteelers\tPatriots
2010\t11\tEagles\tGiants
2010\t12\tColts\tChargers
2010\t13\tRavens\tSteelers
2010\t14\tCowboys\tEagles
2010\t15\tPatriots\tPackers
2010\t16\tBengals\tChargers
2011\t1\tJets\tCowboys
2011\t2\tFalcons\tEagles
2011\t3\tColts\tSteelers
2011\t4\tRavens\tJets
2011\t5\tFalcons\tPackers
2011\t6\tBears\tVikings
2011\t7\tSaints\tColts
2011\t8\tEagles\tCowboys
2011\t9\tSteelers\tRavens
2011\t10\tJets\tPatriots
2011\t11\tGiants\tEagles
2011\t12\tChiefs\tSteelers
2011\t13\tPatriots\tColts
2011\t14\tCowboys\tGiants
2011\t15\tChargers\tRavens
2011\t16\tPackers\tBears
2012\t1\tBroncos\tSteelers
2012\t2\tFortyniners\tLions
2012\t3\tRavens\tPatriots
2012\t4\tEagles\tGiants
2012\t5\tSaints\tChargers
2012\t6\tTexans\tPackers
2012\t7\tBengals\tSteelers
2012\t8\tBroncos\tSaints
2012\t9\tFalcons\tCowboys
2012\t10\tBears\tTexans
2012\t11\tSteelers\tRavens
2012\t12\tGiants\tPackers
2012\t13\tCowboys\tEagles
2012\t14\tPackers\tLions
2012\t15\tPatriots\tFortyniners
2012\t16\tJets\tChargers
2013\t1\tCowboys\tGiants
2013\t2\tSeahawks\tFortyniners
2013\t3\tSteelers\tBears
2013\t4\tFalcons\tPatriots
2013\t5\tFortyniners\tTexans
2013\t6\tCowboys\tRedskins
2013\t7\tColts\tBroncos
2013\t8\tVikings\tPackers
2013\t9\tTexans\tColts
2013\t10\tSaints\tCowboys
2013\t11\tGiants\tPackers
2013\t12\tPatriots\tBroncos
2013\t13\tGiants\tRedskins
2013\t14\tPackers\tFalcons
2013\t15\tSteelers\tBengals
2013\t16\tRavens\tPatriots
2014\t1\tBroncos\tColts
2014\t2\tFortyniners\tBears
2014\t3\tPanthers\tSteelers
2014\t4\tCowboys\tSaints
2014\t5\tPatriots\tBengals
2014\t6\tEagles\tGiants
2014\t7\tBroncos\tFortyniners
2014\t8\tSaints\tPackers
2014\t9\tSteelers\tRavens
2014\t10\tPackers\tBears
2014\t11\tColts\tPatriots
2014\t12\tGiants\tCowboys
2014\t13\tChiefs\tBroncos
2014\t14\tChargers\tPatriots
2014\t15\tEagles\tCowboys
2014\t16\tCardinals\tSeahawks
2015\t1\tCowboys\tGiants
2015\t2\tPackers\tSeahawks
2015\t3\tLions\tBroncos
2015\t4\tSaints\tCowboys
2015\t5\tGiants\tFortyniners
2015\t6\tColts\tPatriots
2015\t7\tPanthers\tEagles
2015\t8\tBroncos\tPackers
2015\t9\tCowboys\tEagles
2015\t10\tSeahawks\tCardinals
2015\t11\tCardinals\tBengals
2015\t12\tBroncos\tPatriots
2015\t13\tSteelers\tColts
2015\t14\tTexans\tPatriots
2015\t15\tEagles\tCardinals
2015\t16\tVikings\tGiants
2016\t1\tCardinals\tPatriots
2016\t2\tVikings\tPackers
2016\t3\tCowboys\tBears
2016\t4\tSteelers\tChiefs
2016\t5\tPackers\tGiants
2016\t6\tTexans\tColts
2016\t7\tCardinals\tSeahawks
2016\t8\tCowboys\tEagles
2016\t9\tRaiders\tBroncos
2016\t10\tPatriots\tSeahawks
2016\t11\tRedskins\tPackers
2016\t12\tBroncos\tChiefs
2016\t13\tSeahawks\tPanthers
2016\t14\tGiants\tCowboys
2016\t15\tCowboys\tBuccaneers
2016\t16\tChiefs\tBroncos
2016\t17\tLions\tPackers
2017\t1\tCowboys\tGiants
2017\t2\tFalcons\tPackers
2017\t3\tRedskins\tRaiders
2017\t4\tSeahawks\tColts
2017\t5\tTexans\tChiefs
2017\t6\tBroncos\tGiants
2017\t7\tPatriots\tFalcons
2017\t8\tLions\tSteelers
2017\t9\tDolphins\tRaiders
2017\t10\tBroncos\tPatriots
2017\t11\tCowboys\tEagles
2017\t12\tSteelers\tPackers
2017\t13\tSeahawks\tEagles
2017\t14\tSteelers\tRavens
2017\t15\tRaiders\tCowboys


2018\t1\tPackers\tBears
2018\t2\tCowboys\tGiants
2018\t3\tLions\tPatriots
2018\t4\tSteelers\tRavens
2018\t5\tTexans\tCowboys
2018\t6\tPatriots\tChiefs
2018\t7\tChiefs\tBengals
2018\t8\tVikings\tSaints
2018\t9\tPatriots\tPackers
2018\t10\tEagles\tCowboys
2018\t11\tBears\tVikings
2018\t12\tVikings\tPackers
2018\t13\tSteelers\tChargers
2018\t14\tBears\tRams
2018\t15\tRams\tEagles
2018\t16\tSeahawks\tChiefs
2018\t17\tTitans\tColts

2019\t1\tPatriots\tSteelers
2019\t2\tFalcons\tEagles
2019\t3\tBrowns\tRams
2019\t4\tSaints\tCowboys
2019\t5\tChiefs\tColts
2019\t6\tChargers\tSteelers
2019\t7\tCowboys\tEagles
2019\t8\tChiefs\tPackers
2019\t9\tRavens\tPatriots
2019\t10\tCowboys\tVikings
2019\t11\tRams\tBears
2019\t12\tFortyniners\tPackers
2019\t13\tTexans\tPatriots
2019\t14\tRams\tSeahawks
2019\t15\tSteelers\tBills
2019\t16\tBears\tChiefs
2019\t17\tSeahawks\tFortyniners

2020\t1\tRams\tCowboys
2020\t2\tSeahawks\tPatriots
2020\t3\tSaints\tPackers
2020\t4\tFortyniners\tEagles
2020\t5\tSeahawks\tVikings
2020\t6\tFortyniners\tRams
2020\t7\tRaiders\tBuccaneers
2020\t8\tCowboys\tEagles
2020\t9\tBuccaneers\tSaints
2020\t10\tPatriots\tRavens
2020\t11\tRaiders\tChiefs
2020\t12\tPackers\tBears
2020\t13\tChiefs\tBroncos
2020\t14\tBills\tSteelers
2020\t15\tCowboys\tFortyniners
2020\t16\tPackers\tTitans


"""

d = {} # d[season][week] = [team,opp]
for line in map(string.strip,string.split(txt,"\n")):
    if not line: continue
    #print "snf:",line
    season,week,home,away = string.split(line,"\t")
    season,week = map(int,[season,week])
    #print week,home
    d.setdefault(season,{})
    d[season].setdefault(week,{})
    d[season][week] = [home,away]

import re

nicknames = ['Bobcats', 'Bucks', 'Bulls', 'Cavaliers', 'Celtics', 'Clippers', 'Grizzlies', 'Hawks', 'Heat',  'Hornets','Jazz', 'Kings', 'Knicks', 'Lakers', 'Magic', 'Mavericks', 'Nets', 'Nuggets', 'Pacers', 'Pelicans','Pistons', 'Raptors', 'Rockets', 'Seventysixers', 'Spurs', 'Suns', 'Supersonics', 'Thunder', 'Timberwolves', 'Trailblazers', 'Warriors', 'Wizards']

teams = nicknames

division_pre_2004 = {'Knicks': 'Atlantic', 'Warriors': 'Pacific', 'Hawks': 'Central', 'Wizards': 'Atlantic', 'Seventysixers': 'Atlantic', 'Nuggets': 'Midwest', 'Cavaliers': 'Central', 'Jazz': 'Midwest', 'Timberwolves': 'Pacific', 'Clippers': 'Pacific', 'Bulls': 'Central', 'Heat': 'Atlantic', 'Celtics': 'Atlantic', 'Magic': 'Atlantic', 'Mavericks': 'Midwest', 'Bobcats': 'Central', 'Trailblazers': 'Pacific', 'Lakers': 'Pacific', 'Pacers': 'Central', 'Rockets': 'Midwest', 'Bucks': 'Central', 'Supersonics': 'Pacific', 'Raptors': 'Central', 'Spurs': 'Midwest', 'Pistons': 'Central', 'Grizzlies': 'Midwest', 'Suns': 'Pacific', 'Kings': 'Pacific', 'Nets': 'Atlantic'}

division = {'Knicks': 'Atlantic', 'Thunder': 'Northwest', 'Hawks': 'Southeast', 'Wizards': 'Southeast', 'Seventysixers': 'Atlantic', 'Nuggets': 'Northwest', 'Pelicans': 'Southwest','Cavaliers': 'Central', 'Jazz': 'Northwest', 'Timberwolves': 'Northwest', 'Clippers': 'Pacific', 'Bulls': 'Central', 'Heat': 'Southeast', 'Warriors': 'Pacific', 'Celtics': 'Atlantic', 'Magic': 'Southeast', 'Mavericks': 'Southwest', 'Bobcats': 'Southeast', 'Trailblazers': 'Northwest', 'Lakers': 'Pacific', 'Pacers': 'Central', 'Rockets': 'Southwest', 'Bucks': 'Central', 'Supersonics': 'Southwest', 'Raptors': 'Atlantic', 'Spurs': 'Southwest', 'Pistons': 'Central', 'Grizzlies': 'Southwest', 'Suns': 'Pacific', 'Kings': 'Pacific', 'Nets': 'Atlantic','Hornets':'Southeast'}



nickname_from_abbreviation = {}
nickname_from_abbreviation["ATL"] = "Hawks"
nickname_from_abbreviation["BOS"] = "Celtics"
nickname_from_abbreviation["CHI"] = "Bulls"
nickname_from_abbreviation["CLE"] = "Cavaliers"
nickname_from_abbreviation["DAL"] = "Mavericks"
nickname_from_abbreviation["DEN"] = "Nuggets"
nickname_from_abbreviation["DET"] = "Pistons"
nickname_from_abbreviation["GST"] = "Warriors"
nickname_from_abbreviation["GSW"] = "Warriors"
nickname_from_abbreviation["GS"] = "Warriors"
nickname_from_abbreviation["HOU"] = "Rockets"
nickname_from_abbreviation["IND"] = "Pacers"
nickname_from_abbreviation["LAC"] = "Clippers"
nickname_from_abbreviation["LAL"] = "Lakers"
nickname_from_abbreviation["MIA"] = "Heat"
nickname_from_abbreviation["MIL"] = "Bucks"
nickname_from_abbreviation["MIN"] = "Timberwolves"
nickname_from_abbreviation["BKN"] = "Nets"
nickname_from_abbreviation["BK"] = "Nets"
nickname_from_abbreviation["Nets"] = "Nets"
nickname_from_abbreviation["NOP"] = "Pelicans"
nickname_from_abbreviation["NO"] = "Pelicans"
nickname_from_abbreviation["NYK"] = "Knicks"
nickname_from_abbreviation["NY"] = "Knicks"
nickname_from_abbreviation["ORL"] = "Magic"
nickname_from_abbreviation["PHI"] = "Seventysixers"
nickname_from_abbreviation["PHX"] = "Suns"
nickname_from_abbreviation["PHO"] = "Suns"
nickname_from_abbreviation["POR"] = "Trailblazers"
nickname_from_abbreviation["SAC"] = "Kings"
nickname_from_abbreviation["SAS"] = "Spurs"
nickname_from_abbreviation["SA"] = "Spurs"
nickname_from_abbreviation["SEA"] = "Supersonics"
nickname_from_abbreviation["TOR"] = "Raptors"
nickname_from_abbreviation["UTA"] = "Jazz"
nickname_from_abbreviation["MEM"] = "Grizzlies"
nickname_from_abbreviation["WAS"] = "Wizards"
nickname_from_abbreviation["CHA"] = "Hornets"
nickname_from_abbreviation["OKC"] = "Thunder"

nickname_from_abbreviation["WST"] = "Western Conference"
nickname_from_abbreviation["EST"] = "Eastern Conference"
#nickname_from_abbreviation["CHA"] = "Bobcats"


abbreviation_from_nickname = {}
for abbreviation,nickname in nickname_from_abbreviation.items():
    if len(abbreviation)==3:
        abbreviation_from_nickname[nickname] = abbreviation
abbreviation_from_nickname['Warriors'] = 'GSW'
abbreviation_from_nickname['Jazz'] = 'UTH'
SR_abbreviation_from_nickname =  abbreviation_from_nickname.copy()
SR_abbreviation_from_nickname['Suns'] = 'PHO'
SR_abbreviation_from_nickname['Nets'] = 'NJN'
SR_abbreviation_from_nickname['Warriors'] = 'GSW'
SR_abbreviation_from_nickname['Pelicans'] = 'NOP'
SR_abbreviation_from_nickname['Spurs'] = 'SAS'
SR_abbreviation_from_nickname['Knicks'] = 'NYK'
SR_abbreviation_from_nickname['Hornets'] = 'CHO'
nba_nickname_to_abbr = abbreviation_from_nickname
nba_nickname_to_abbr['Jazz'] = 'UTA'

def find_SR_abbreviation_from_nickname_and_season(nickname, season):
    if nickname == 'Hornets' and season<2014: return 'CHA'
    if nickname == 'Nets' and season>2011: return 'BRK'
    if nickname == 'Pelicans' and season<2002: return 'CHH'
    if nickname == 'Pelicans' and season<2013: return 'NOH'
    if nickname == 'Grizzlies' and season<2001: return 'VAN'
    return SR_abbreviation_from_nickname.get(nickname,nickname)


city_from_nickname = {'Bobcats':'Charlotte', 'Bucks':'Milwaukee', 'Bulls':'Chicago', 'Cavaliers':'Cleveland', 'Celtics':'Boston', 'Clippers':'L.A. Clippers', 'Grizzlies':'Memphis', 'Hawks':'Atlanta', 'Heat':'Miami', 'Pelicans':'New Orleans', 'Jazz':'Utah','Kings':'Sacramento', 'Knicks':'New York', 'Lakers':'L.A. Lakers', 'Magic':'Orlando', 'Mavericks':'Dallas', 'Nets':'Brooklyn', 'Nuggets':'Denver', 'Pacers':'Indiana', 'Pistons':'Detroit', 'Raptors':'Toronto', 'Rockets':'Houston', 'Seventysixers':'Philadelphia', 'Spurs':'San Antonio', 'Suns':'Phoenix', 'Supersonics':'Seattle', 'Thunder':'Oklahoma City', 'Timberwolves':'Minnesota', 'Trailblazers':'Portland', 'Warriors':'Golden State', 'Wizards':'Washington','Hornets':'Charlotte'}



def division_from_nickname_season(nickname,season):
    #print "division_from_nickname_season:",nickname,season
    if nickname in ['Pelicans','Hornets']:
        if season<=2003: return 'Central'
    if 2004<=season: return division[nickname]
    return division_pre_2004[nickname]

def conference_from_division(division):
    if division in ["Atlantic","Central","Southeast"]: return "Eastern"
    return "Western"

def conference_from_nickname_season(nickname,season):
    division = division_from_nickname_season(nickname,season)
    return conference_from_division(division)

conferences =  ["Eastern","Western"]
divisions = sorted(list(set(division.values())))

def get_images():
    import urllib,re,Image
    #page = urllib.urlopen('http://www.logoeps.net/nba-team-logos').read()
    pat =  'src="(http://www.logoeps.*[_-]([a-z]+)[_-]logo.*thumb.jpg)'
    mos = re.findall(pat, page,re.I)
    print len(mos)
    for url,team in mos:
        f = "/home/jameyer/S2/public_html/Images/NBA/%s.jpg"%team.title()
        print "retrieve",url
        jpg = urllib.urlretrieve(url,f)

_colors = """tr>
<td>Atlanta Hawks</td>
<td style="background:#E03A3E"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#C1D32F"></td>
<td style="background:#26282A"></td>
<td>4.34</td>
<td>8.9</td>
</tr>
<tr>
<td>Boston Celtics</td>
<td style="background:#008348"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#BB9753"></td>
<td style="background:#000000"></td>
<td>4.84</td>
<td>7.66</td>
</tr>
<tr>
<td>Brooklyn Nets</td>
<td style="background:#000000"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#000000"></td>
<td style="background:#FFFFFF"></td>
<td>21</td>
<td>21</td>
</tr>
<tr>
<td>Charlotte Hornets</td>
<td style="background:#1D1160"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#00788C"></td>
<td style="background:#FFFFFF"></td>
<td>16.14</td>
<td>5.17</td>
</tr>
<tr>
<td>Chicago Bulls</td>
<td style="background:#CE1141"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#000000"></td>
<td style="background:#FFFFFF"></td>
<td>5.55</td>
<td>21</td>
</tr>
<tr>
<td>Cleveland Cavaliers</td>
<td style="background:#6F263D"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#FFB81C"></td>
<td style="background:#000000"></td>
<td>10.39</td>
<td>12.12</td>
</tr>
<tr>
<td>Dallas Mavericks</td>
<td style="background:#0053BC"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#BBC4CA"></td>
<td style="background:#000000"></td>
<td>7.09</td>
<td>11.86</td>
</tr>
<tr>
<td>Denver Nuggets</td>
<td style="background:#00285E"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#FDB927"></td>
<td style="background:#00285E"></td>
<td>14.33</td>
<td>8.29</td>
</tr>
<tr>
<td>Detroit Pistons</td>
<td style="background:#006BB6"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#ED174C"></td>
<td style="background:#FFFFFF"></td>
<td>5.56</td>
<td>4.35</td>
</tr>
<tr>
<td>Golden State Warriors</td>
<td style="background:#006BB6"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#FDB927"></td>
<td style="background:#26282A"></td>
<td>5.56</td>
<td>8.56</td>
</tr>
<tr>
<td>Houston Rockets</td>
<td style="background:#CE1141"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#C4CED4"></td>
<td style="background:#000000"></td>
<td>5.55</td>
<td>13.13</td>
</tr>
<tr>
<td>Indiana Pacers</td>
<td style="background:#002D62"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#FDBB30"></td>
<td style="background:#002D62"></td>
<td>13.53</td>
<td>7.94</td>
</tr>
<tr>
<td>Los Angeles Clippers</td>
<td style="background:#ED174C"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#006BB6"></td>
<td style="background:#FFFFFF"></td>
<td>4.35</td>
<td>5.56</td>
</tr>
<tr>
<td>Los Angeles Lakers</td>
<td style="background:#552583"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#FDB927"></td>
<td style="background:#000000"></td>
<td>10.61</td>
<td>12.15</td>
</tr>
<tr>
<td>Memphis Grizzlies</td>
<td style="background:#00285E"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#6189B9"></td>
<td style="background:#000000"></td>
<td>14.33</td>
<td>5.79</td>
</tr>
<tr>
<td>Miami Heat</td>
<td style="background:#000000"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#98002E"></td>
<td style="background:#FFFFFF"></td>
<td>21</td>
<td>8.84</td>
</tr>
<tr>
<td>Milwaukee Bucks</td>
<td style="background:#00471B"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#EEE1C6"></td>
<td style="background:#00471B"></td>
<td>10.95</td>
<td>8.46</td>
</tr>
<tr>
<td>Minnesota Timberwolves</td>
<td style="background:#0C2340"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#78BE20"></td>
<td style="background:#000000"></td>
<td>15.79</td>
<td>9.18</td>
</tr>
<tr>
<td>New Orleans Pelicans</td>
<td style="background:#002B5C"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#B4975A"></td>
<td style="background:#000000"></td>
<td>14</td>
<td>7.51</td>
</tr>
<tr>
<td>New York Knicks</td>
<td style="background:#006BB6"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#F58426"></td>
<td style="background:#000000"></td>
<td>5.56</td>
<td>8.21</td>
</tr>
<tr>
<td>Oklahoma City Thunder</td>
<td style="background:#007AC1"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#EF3B24"></td>
<td style="background:#FFFFFF"></td>
<td>4.61</td>
<td>3.95</td>
</tr>
<tr>
<td>Orlando Magic</td>
<td style="background:#0077C0"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#000000"></td>
<td style="background:#FFFFFF"></td>
<td>4.77</td>
<td>21</td>
</tr>
<tr>
<td>Philadelphia Seventysixers</td>
<td style="background:#006BB6"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#ED174C"></td>
<td style="background:#FFFFFF"></td>
<td>5.56</td>
<td>4.35</td>
</tr>
<tr>
<td>Phoenix Suns</td>
<td style="background:#1D1160"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#E56020"></td>
<td style="background:#000000"></td>
<td>16.14</td>
<td>6.03</td>
</tr>
<tr>
<td>Portland Trailblazers</td>
<td style="background:#E03A3E"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#000000"></td>
<td style="background:#FFFFFF"></td>
<td>4.34</td>
<td>21</td>
</tr>
<tr>
<td>Sacramento Kings</td>
<td style="background:#5A2D81"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#63727A"></td>
<td style="background:#FFFFFF"></td>
<td>9.87</td>
<td>4.98</td>
</tr>
<tr>
<td>San Antonio Spurs</td>
<td style="background:#000000"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#C4CED4"></td>
<td style="background:#000000"></td>
<td>21</td>
<td>13.13</td>
</tr>
<tr>
<td>Toronto Raptors</td>
<td style="background:#CE1141"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#000000"></td>
<td style="background:#FFFFFF"></td>
<td>5.55</td>
<td>21</td>
</tr>
<tr>
<td>Utah Jazz</td>
<td style="background:#002B5C"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#F9A01B"></td>
<td style="background:#002B5C"></td>
<td>14</td>
<td>6.71</td>
</tr>
<tr>
<td>Washington Wizards</td>
<td style="background:#E31837"></td>
<td style="background:#FFFFFF"></td>
<td style="background:#002B5C"></td>
<td style="background:#FFFFFF"></td>
<td>4.72</td>
<td>14</td>
</tr>"""

colors_from_nickname = {}
for line in _colors.split('<tr>'):
    team = re.findall('<td>([a-z ]+)</td>',line,re.I)[0].split()[-1]
    #print "team",team
    colors = re.findall('background:(#[0-9a-z]+)',line,re.I)
    colors_from_nickname[team] = colors


if __name__ == "__main__":
    #print division_from_nickname_season("Bulls",2005)
    #print division_from_nickname_season("Bulls",2003)
    #print division_from_nickname_season("Hawks",2005)
    #print division_from_nickname_season("Hawks",2003)
    #print conference_from_nickname_season("Hawks",2003)
    #print ("%s"%(map(lambda x:"<a href=schedule_log?team=%s>%s</a>"%(x,x),nicknames),)).replace("'",'').replace(",",'')
    #print '), (t:team='.join(nicknames)
    #import urllib,re;    page = urllib.urlopen('http://www.logoeps.net/nba-team-logos').read()
    #get_images()
    pass

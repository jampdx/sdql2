# Notes:
# Atlanta Thrashers became the Winnipeg Jets in 2011
crowd_abbreviation_to_nickname = {
    'COL':'Avalanche',
    'CHI':'Blackhawks',
    'CBJ':'Blue Jackets',
    'STL':'Blues',
    'BOS':'Bruins',
    'MTL':'Canadiens',
    'VAN':'Canucks',
    'WSH':'Capitals',
    'ARI':'Coyotes',
    'NJ':'Devils',
    'ANA':'Ducks',
    'CGY':'Flames',
    'PHI':'Flyers',
    'CAR':'Hurricanes',
    'NYI':'Islanders',
    'WPG':'Jets',
    'LA':'Kings',
    'TB':'Lightning',
    'TOR':'Maple Leafs',
    'EDM':'Oilers',
    'FLA':'Panthers',
    'PIT':'Penguins',
    'NAS':'Predators',
    'NYR':'Rangers',
    'DET':'Red Wings',
    'BUF':'Sabres',
    'OTT':'Senators',
    'SJ':'Sharks',
    'DAL':'Stars',
    'MIN':'Wild',
    'VEG':'Knights'
}
abbreviation_to_nickname = {
'CAR': 'Hurricanes',
'BUF': 'Sabres',
'TOR': 'Maple Leafs',
'OTT': 'Senators',
'COL': 'Avalanche',
'DAL': 'Stars',
'PHO': 'Coyotes',
'ARI': 'Coyotes',
'NYI': 'Islanders',
'NAS': 'Predators',
'CHI': 'Blackhawks',
'NYR': 'Rangers',
'WAS': 'Capitals',
'ATL': 'Thrashers',
'TB': 'Lightning',
'PIT': 'Penguins',
'PHI': 'Flyers',
'DET': 'Red Wings',
'VAN': 'Canucks',
'SJ': 'Sharks',
'STL': 'Blues',
'MIN': 'Wild',
'EDM': 'Oilers',
'CAL': 'Flames',
'NJ': 'Devils',
'CLB': 'Blue Jackets',
'ANA': 'Ducks',
'LA': 'Kings',
'FLA': 'Panthers',
'BOS': 'Bruins',
'MON': 'Canadiens',
'West': 'Western Conference',
'East': 'Eastern Conference',
'WIN': 'Jets',
'STAL': 'Team Staal',
'LIDS': 'Team Lidstrom',
'ALFRD': 'Team Alfredsson',
'CHAR': 'Team Chara',
'VEG':'Knights'
    }

msfd = {'SJ':'SJS','WAS':'WSH','CLB':'CBJ','TB':'TBL','WIN':'WPJ',
        'VEG':'VGK','LA':'LAK','NJ':'NJD','CAL':'CGY',
        'FLA':'FLO','MON':'MTL','NAS':'NSH','SJ':'SJS'}
msf_abbreviation_to_nickname = {}
for abbr in abbreviation_to_nickname.keys():
    msf_abbr = msfd.get(abbr,abbr)
    msf_abbreviation_to_nickname[msf_abbr] = abbreviation_to_nickname[abbr]


nickname_to_abbreviation = {}
for abb,nick in abbreviation_to_nickname.iteritems():
    nickname_to_abbreviation[nick] = abb
def nickname_from_full_name(full_name):
    nickname = full_name.title().split()[-1]
    if nickname == "Leafs": return "Maple Leafs"
    if nickname == "Wings": return "Red Wings"
    if nickname == "Jackets": return "Blue Jackets"
    if nickname == "Knights": return "Knights"
    return nickname


def division_conference_from_nickname_season(team,season):
    if season == 2020:
        if team in ["Bruins","Sabres","Devils","Islanders", "Rangers", "Flyers","Penguins","Capitals"]:
            return "East",None
        if team in ["Hurricanes","Blackhawks","Blue Jackets","Stars","Red Wings","Panthers","Predators","Lightning"]:
            return "Central",None

        if team in ["Ducks","Coyotes","Avalanche","Kings","Wild","Sharks","Blues","Knights"]:
            return "West",None

        if team in ["Flames","Oilers","Canadiens","Senators","Maple Leafs","Canucks","Jets"]:
            return "North",None


    if season < 2013:
        if team in ["Blackhawks","Blue Jackets","Red Wings","Predators","Blues"]: return "Central","Western"
        if team in ["Flames","Avalanche","Oilers","Wild","Canucks"]: return "Northwest","Western"
        if team in ["Bruins","Sabres","Canadiens","Senators","Maple Leafs"]: return "Northeast","Eastern"
        if team in ["Ducks","Stars","Kings","Coyotes","Sharks"]: return "Pacific","Western"
        if team in ["Hurricanes","Panthers","Lightning","Capitals","Thrashers","Jets"]: return "Southeast","Eastern"

    if team in ["Bruins","Sabres", "Red Wings", "Panthers", "Canadiens", "Senators", "Lightning","Maple Leafs"]:
       return "Atlantic","Eastern"
    if team in ["Rangers","Islanders","Devils","Capitals", "Penguins", "Flyers", "Hurricanes","Blue Jackets"]:
       return "Metropolitan","Eastern"

    if team in ["Blackhawks","Blues", "Predators", "Wild","Avalanche","Stars","Jets"]:
       return "Central","Western"

    if team in ["Kings", "Ducks","Coyotes","Sharks","Canucks","Flames","Oilers","Knights"]:
       return "Pacific","Western"



teams = (["Blackhawks","Blue Jackets","Red Wings","Predators","Blues"]+
                 ["Devils","Islanders","Rangers","Flyers","Penguins"]+
                 ["Flames","Avalanche","Oilers","Wild","Canucks"]+
                 ["Bruins","Sabres","Canadiens","Senators","Maple Leafs"]+
                 ["Ducks","Stars","Kings","Coyotes","Sharks","Knights"]+
                 ["Hurricanes","Panthers","Lightning","Capitals","Jets"])

# `city`  excpet NY has two teams
city_to_nickname = {
"Carolina":"Hurricanes",
"Buffalo":"Sabres",
"Toronto":"Maple Leafs",
"Ottawa":"Senators",
"Phoenix":"Coyotes",
"Arizona":"Coyotes",
"NY Islanders":"Islanders",
"Edmonton":"Oilers",
"Calgary":"Flames",
"Pittsburgh":"Penguins",
"Philadelphia":"Flyers",
"Nashville":"Predators",
"Chicago":"Blackhawks",
"NY Rangers":"Rangers",
"Washington":"Capitals",
"Detroit":"Red Wings",
"Vancouver":"Canucks",
"San Jose":"Sharks",
"St Louis":"Blues",
"Atlanta":"Thrashers",
"Tampa Bay":"Lightning",
"Minnesota":"Wild",
"Colorado":"Avalanche",
"Columbus":"Blue Jackets",
"Anaheim":"Ducks",
"Los Angeles":"Kings",
"New Jersey":"Devils",
"Florida":"Panthers",
"Boston":"Bruins",
"Montreal":"Canadiens",
"Dallas":"Stars",
"Winnipeg":"Jets",
"Las Vegas":"Knights"
    }


def get_images():
    import urllib,re,Image

    pat =  '<a  href="logos/.*" title="([a-zA-Z ]+) Logos">[\s]+<img src="(.*gif)">'
    mos = re.findall(pat, page,re.I)
    print len(mos)
    for team,url in mos[:30]:
        team = team.split()[-1]
        f = "/home/jameyer/S2/public_html/Images/NHL/%s.gif"%team.title()
        print "retrieve",url, 'for',team
        jpg = urllib.urlretrieve(url,f)
if __name__ == "__main__":
    #page = urllib.urlopen('http://www.sportslogos.net/teams/list_by_league/1/National_Hockey_League/NHL/logos/').read()
    #print page
    #get_images()
    pass

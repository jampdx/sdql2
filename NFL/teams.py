
teams = ["Bears", "Bengals", "Bills", "Broncos", "Browns", "Buccaneers", "Cardinals", "Chargers", "Chiefs", "Colts", "Cowboys", "Dolphins", "Eagles", "Falcons", "Fortyniners", "Giants", "Jaguars", "Jets", "Lions", "Oilers", "Packers", "Panthers", "Patriots", "Raiders", "Rams", "Ravens", "Redskins", "Saints", "Seahawks", "Steelers", "Texans", "Titans", "Vikings"]

divisions = ["NFC West","NFC Central","AFC Central","AFC West","NFC East","AFC East","NFC South","AFC North","NFC North","AFC South"]

conferences = ["NFC","AFC"]

team_abbr = {'LAC':'Chargers','LA':'Rams','CHI':'Bears','CIN':'Bengals','BUF':'Bills','DEN':'Broncos','CLE':'Browns','TB': "Buccaneers",
             'ARZ':"Cardinals", 'SD':"Chargers", 'KC':"Chiefs", 'IND':"Colts", 'DAL':"Cowboys", 'MIA':"Dolphins",
             'PHI':"Eagles", 'ATL':"Falcons", 'SF':"Fortyniners", 'NYG':"Giants", 'JAC':"Jaguars", 'JAX':"Jaguars", 'NJ':"Jets", 'DET':"Lions",
             'HOU':"Oilers", 'GB':"Packers", 'CAR':"Panthers", 'NE':"Patriots",
             'STL':"Rams", 'BAL':"Ravens", 'WAS':"Washington", 'NO':"Saints", 'SEA':"Seahawks", 'PIT':"Steelers",
             'HOU':"Texans", 'TEN':"Titans", 'MIN':"Vikings",
             'OAK':"Raiders","NYJ":"Jets",'ARI':'Cardinals','LV':'Raiders'}

abbr_from_nickname = {'49ers':'SF'}
abbr_from_nickname['49Ers'] = 'SF'
for abbr in team_abbr:
    abbr_from_nickname[team_abbr[abbr]] = abbr
abbr_from_nickname['Chargers'] = 'LAC'
abbr_from_nickname['Jets'] = 'NYJ'
abbr_from_nickname['Jaguars'] = 'JAX'
abbr_from_nickname['Rams'] = 'LA'


def division(team,season):
    if 1989 <= season < 2002:
        if team in ["Bills","Colts","Dolphins","Jets","Patriots"]: return "AFC East"
        if team in ["Ravens","Jaguars","Titans","Steelers","Browns","Bengals","Oilers"]: return "AFC Central"
        if team in ["Broncos","Raiders","Chargers","Chiefs","Seahawks"]: return "AFC West"
        if team in ["Cowboys","Giants","Eagles","Redskins","Cardinals","Washington"]: return "NFC East"
        if team in ["Lions","Packers","Bears","Vikings","Buccaneers"]: return "NFC Central"
        if team in ["Fortyniners","Rams","Saints","Falcons","Panthers"]: return "NFC West"

    if 2002<=season:
        if team in ["Bills","Dolphins","Jets","Patriots"]: return "AFC East"
        if team in ["Broncos","Raiders","Chargers","Chiefs"]: return "AFC West"
        if team in ["Steelers","Browns","Bengals","Ravens"]: return "AFC North"
        if team in ["Jaguars","Colts","Titans","Texans"]: return "AFC South"
        if team in ["Lions","Packers","Bears","Vikings"]: return "NFC North"
        if team in ["Panthers","Falcons","Saints","Buccaneers"]: return "NFC South"
        if team in ["Cowboys","Giants","Eagles","Redskins","Washington"]: return "NFC East"
        if team in ["Cardinals","Fortyniners","Seahawks","Rams"]: return "NFC West"


colors_from_nickname = {
'Bears':['#03202F', '#DD4814'],
'Bengals':['#000000', '#FB4F14'],
'Bills':['#00338D', '#C60C30'],
'Broncos':['#FB4F14', '#002244'],
'Browns':['#26201E', '#E34912'],
'Buccaneers':['#B20032', '#89765F'],
'Cardinals':['#870619', '#000000'],
'Chargers':['#08214A', '#EEC607'],
'Chiefs':['#B20032', '#FFB612'],
'Colts':['#FFFFFF', '#003B7B'],
'Cowboys':['#8C8B8A', '#002244'],
'Dolphins':['#006666', '#DF6108'],
'Eagles':['#003B48', '#000000'],
'Falcons':['#BD0D18', '#000000'],
'Fortyniners':['#AF1E2C', '#E6BE8A'],
'Giants':['#192F6B', '#CA001A'],
'Jaguars':['#000000', '#007198'],
'Jets':['#0C371D', '#FFFFFF'],
'Lions':['#006DB0', '#C5C7CF'],
'Packers':['#213D30', '#FFCC00'],
'Panthers':['#0088CE', '#000000'],
'Patriots':['#D6D6D6', '#0D254C'],
'Raiders':['#C4C8CB', '#000000'],
'Rams':['#13264B', '#C9AF74'],
'Ravens':['#280353', '#000000'],
'Redskins':['#773141', '#FFB612'],
'Saints':['#D2B887', '#000000'],
'Seahawks':['#4EAE47', '#06192E'],
'Steelers':['#F2C800', '#000000'],
'Texans':['#FFFFFF', '#02253A'],
'Titans':['#648FCC', '#000080'],
'Vikings':['#3B0160', '#F0BF00']}

fullname_from_nickname = {
'Bears':'Chicago Bears',
'Bengals':'Cincinnati Bengals',
'Bills':'Buffalo Bills',
'Broncos':'Denver Broncos',
'Browns':'Cleveland Browns',
'Buccaneers':'Tampa Bay Buccaneers',
'Cardinals':'Arizona Cardinals',
'Chargers':'Los Angeles Chargers',
'Chiefs':'Kansas City Chiefs',
'Colts':'Indianapolis Colts',
'Cowboys':'Dallas Cowboys',
'Dolphins':'Miami Dolphins',
'Eagles':'Philadelphia Eagles',
'Falcons':'Atlanta Falcons',
'Fortyniners':'San Francisco Fortyniners',
'Giants':'New York Giants',
'Jaguars':'Jacksonville Jaguars',
'Jets':'New York Jets',
'Lions':'Detroit Lions',
'Packers':'Green Bay Packers',
'Panthers':'Carolina Panthers',
'Patriots':'New England Patriots',
'Raiders':'Oakland Raiders',
'Rams':'Los Angeles Rams',
'Ravens':'Baltimore Ravens',
'Redskins':'Washington Redskins',
'Saints':'New Orleans Saints',
'Seahawks':'Seattle Seahawks',
'Steelers':'Pittsburgh Steelers',
'Texans':'Houston Texans',
'Titans':'Tennessee Titans',
'Vikings':'Minnesota Vikings'}


nickname_from_abbreviation = {}
nickname_from_abbreviation["ATL"] = "Dream"
nickname_from_abbreviation["CHI"] = "Sky"
nickname_from_abbreviation["CONN"] = "Sun"
nickname_from_abbreviation["IND"] = "Fever"
nickname_from_abbreviation["NY"] = "Liberty"
nickname_from_abbreviation["WAS"] = "Mystics"

nickname_from_abbreviation["DAL"] = "Wings"
nickname_from_abbreviation["LA"] = "Sparks"
nickname_from_abbreviation["MIN"] = "Lynx"
nickname_from_abbreviation["PHO"] = "Mercury"
nickname_from_abbreviation["SA"] = "Stars"
nickname_from_abbreviation["SEA"] = "Storm"

nickname_from_abbreviation["LV"] = "Aces"


abbreviation_from_nickname = {}
for abbreviation,nickname in nickname_from_abbreviation.items():
    abbreviation_from_nickname[nickname] = abbreviation

western_teams = ['Wings','Sparks','Lynx','Mercury','Stars','Storm','Aces']
eastern_teams = ['Dream','Sky','Sun','Fever','Mystics','Liberty']

teams = western_teams + eastern_teams

def conference_from_nickname_season(nickname,season):
    if nickname in western_teams: return 'Western'
    if nickname in eastern_teams: return 'Eastern'

conferences =  ["Eastern","Western"]



if __name__ == "__main__":
    pass

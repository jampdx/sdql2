import re

game_dates_pat = re.compile( "game dates(\([^)]*\))")

def expand(text):
    text = game_dates_pat.sub(lambda g:'''self.game_dates['''+g.group(1)+'''] as "games dates''' + g.group(1)+'"',text)
    return text


if __name__ == "__main__":
    sdql = "game dates(season,o:team,'home')"
    print sdql, "==>", expand(sdql)

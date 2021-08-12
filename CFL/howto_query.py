
from PyQL.py_tools import link

html = "<b>How to Query: </b>"
html += "<p>The syntax for access to the WNBA team data is: <em>game reference:parameter.</em> To see the date, team, and opponent where the team scored +100 points after scoring +100 points in the previous game use the SDQL: "+ link(page='query',sdql="date,team,o:team@points>100 and p:points>100")
html += "<p>The syntax for access to the WNBA player data: <em>[team:]player name:game reference:parameter.</em> To see the date, team, opponent and number of points by Angel McCoughtry in the game after she scored more than 30 use the SDQL: "+ link(page='query',sdql="date,team,o:team,Angel McCoughtry:points@Angel McCoughtry:p:points>30")
#html += "<p>The SDQL strives to be flexible in isolating batters and pitchers and all these formats for setting Arron Hill's previous hits to 4 are acceptable: <em>Aaron Hill:p:hits=4</em>, <em>AaHi:p:hits=4</em>, and <em>AHill:p:hits=4</em>"

if __name__ == "__main__":
    print html

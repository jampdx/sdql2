
from PyQL.py_tools import link

html = "<b>How to Query: </b>"
html += "<p>The syntax for access to the NBA team data is: <em>game reference:parameter.</em> To see the date, team, and opponent where the team scored +120 points after scoring +120 runs in the previous game use the SDQL: "+ link(page='query',sdql="date,team,o:team@points>120 and p:points>120")
html += "<p>The syntax for access to the NBA player data: <em>[team:]player name:game reference:parameter.</em> To see the date, team, opponent and number of points by Kobe Bryant in the game after he scored more than 30 use the SDQL: "+ link(page='query',sdql="date,team,o:team,Kobe Bryant:points@Kobe Bryant:p:points>30")
#html += "<p>The SDQL strives to be flexible in isolating batters and pitchers and all these formats for setting Arron Hill's previous hits to 4 are acceptable: <em>Aaron Hill:p:hits=4</em>, <em>AaHi:p:hits=4</em>, and <em>AHill:p:hits=4</em>"

if __name__ == "__main__":
    print html

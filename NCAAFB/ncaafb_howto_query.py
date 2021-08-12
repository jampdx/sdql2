
from PyQL.py_tools import link

html = "<b>How to Query:</b>"
html += "<p>The syntax for access to the NCAAFB database is: <em>game reference:parameter.</em><p> To see the date, team, point, opponent and opponent's points where the team scored more than 50 points their last four games use the SDQL: "+ link(page='query',sdql="date, team, points, o:team, o:points @ p:points > 50 and p2:points > 50 and p3:points > 50 and p4:points > 50")

html += "<p>To see the total points scored and allowed for team starting with the letter `A` in 2010 use the SDQL: "+ link(page='query',sdql="Sum(points), Sum(o:points) @ team and season = 2010 and team[0] = 'A'")

if __name__ == "__main__":
    print html

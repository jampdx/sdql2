
from PyQL.py_tools import link


def game_level(**kwargs):
    ret = ''
    num_ret = ''
    dv_ret = ''
    dv_ret += "<b>For data visualization queries</b>, you need to specify the parameters to plot as well as the restrictive conditions."
    dv_ret += "<p><b>Scatter Plots</b> require the SDQL syntax: <em>x, y @ conditions</em>. For example:"
    dv_ret += "<BR>To plot the opponent's points vs the team's points for all UCLA games in 2013 use the SDQL: "+ link(page='query_data_viz',sdql="t:points as Points, o:points as Opponent Points @ t:team=UCLA and season=2013",**{'output':'plotly.scatter'})
    dv_ret += "<p><b>Histograms</b> require the SDQL syntax: <em>x @ conditions</em>. For example :"
    dv_ret += "<BR>To plot the distribution of points for all NCAAFB games since 2010 use the SDQL: "+ link(page='query_data_viz',sdql="t:points as Points @ 2010 <= season",**{'output':'plotly.histogram'})
    dv_ret += "<BR>To color this histogram by site, use the SDQL: "+ link(page='query_data_viz',sdql="t:points as Points @ 2010 <= season and site",**{'output':'plotly.histogram'})
    dv_ret += "<p><b>Box Plots</b> require the SDQL syntax: <em>x @ groups </em>. For example :"
    dv_ret += "<BR>See the points scored by NCAAFB teams in 2013 use the SDQL: "+ link(page='query_data_viz',sdql="points @ team and season=2013",**{'output':'plotly.box','show':40})
    

    num_ret += "<b>For access to the NCAAFB game-level database</b> use the syntax: <em>game reference:parameter.</em>"
    num_ret += "<BR>Where game game references are any combination of t, o, p, P, n and N (for team, opponent, previous game, previous matchup, next game and next matchup respectively). Here are a few examples: "
    num_ret += "<BR> To see how teams do when rushing for more than 100 yards while holding their opponent to few than 100 yars use the SDQL: "+ link(page='query',sdql="100 < t:rushing yards and to:rushing yards < 100")
    num_ret += "<BR> To see how teams do after scoring more than 40 points their last four games use the SDQL: "+ link(page='query',sdql="40 < p:points and 40 < p2:points and 40 < p3:points and 40 < p4:points")
    num_ret += "<BR> To see how teams do after their opponent passed for more than 400 yards and lost use the SDQL: "+ link(page='query',sdql="400 < top:passing yards and top:points < topo:points")
    num_ret += "<BR> To see how teams do when they have a season-to-date average of less that 50 rushing yards use the SDQL: "+ link(page='query',sdql="tA(rushing yards) < 50")
    
    num_ret += "<p><b>To access an individual player's performance</b> use the syntax: <em>[Team:]Player Name:game reference:parameter.</em>"
    num_ret += "<BR>Where the specification of the team is optional and the name can be abbreviated."
    num_ret += "<BR> To see how Fresno does when DCarr throws for more than 400 yards use the SDQL: "+ link(page='query',sdql="400 < FRES:DCarr:passing yards")
    num_ret += "<BR> To see how Wisconsin does after M Gorden has more than 100 rushing yards use the SDQL: "+ link(page='query',sdql="100<WIS:MGordon:p:rushing yards")
    if "data_vi" in kwargs.get('form_action',''):
        return dv_ret + "<p>" + num_ret
    return num_ret + "<p>" + dv_ret



def player_level(**kwargs):
    ret = ''
    num_ret = ''
    dv_ret = ''
    dv_ret += "<b>For data visualization queries</b>, you need to specify the parameters to plot as well as the restrictive conditions."
    dv_ret += "<p><b>Scatter Plots</b> require the SDQL syntax: <em>x, y @ conditions</em>. For example:"
    dv_ret += "<BR>To plot receiving yards vs rushing yards for Cowboys players in 2013 use the SDQL: "+ link(page='receiving_query_data_viz',sdql="rushing yards, receiving yards @ team = Cowboys and season = 2013",**{'output':'plotly.scatter'})
    dv_ret += "<BR>Tp break this down by player, just add ` and name` to the SDQL: "+ link(page='receiving_query_data_viz',sdql="rushing yards, receiving yards @ team = Cowboys and season = 2013 and name",**{'output':'plotly.scatter'})
    dv_ret += "<p><b>Histograms</b> require the SDQL syntax: <em>x @ conditions</em>. For example:"
    dv_ret += "<BR>To plot the distribution of individual rushing yards for all NCAAFB players since 2006 use the SDQL: "+ link(page='rushing_query_data_viz',sdql="t:rushing yards as Rushing Yards @ 2006 <= season",**{'output':'plotly.histogram'})
    dv_ret += "<p><b>Box Plots</b> require the SDQL syntax: <em>x @ groups </em>. For example :"
    dv_ret += "<BR>See the distribution of passing yards for each QB in 2013 use the SDQL: "+ link(page='passing_query_data_viz',sdql="passing yards @ name and season = 2013",**{'output':'plotly.box','show':50})
    

    num_ret += "<b>For access to the NCAAFB player-level database</b> use the syntax: <em>game reference:parameter.</em>"
    num_ret += "<BR>Where game game references are any combination of t, o, p, P, n and N (for team, opponent, previous game, previous matchup, next game and next matchup respectively). Here are a few examples: "
    num_ret += "<BR> To see how players do when they have more than 35 rushes use the SDQL: "+ link(page='rushing_query',sdql="35 < t:rushes")
    num_ret += "<BR> To see how players do after rushing for more than 100 yards and 2+ TDs use the SDQL: "+ link(page='rushing_query',sdql="100 < p:rushing yards and 2 <= p:rushing touchdowns")
    
    num_ret += "<p><b>To access the team's performance from the player-level query page</b> use the syntax: <em>Team:game reference:parameter.</em>"
    num_ret += "<BR> To see how players do after accounting for more than 90% of their team's rushes use the SDQL: "+ link(page='rushing_query',sdql="0.9 * Team:p:rushes < p:rushes")
    if "data_vi" in kwargs.get('form_action',''):
        return dv_ret + "<p>" + num_ret
    return num_ret + "<p>" + dv_ret


def html(**kwargs):
    qt = kwargs.get('_qt')
    ret = "<b>How to Query:</b><P>"
    #ret += "%s"%kwargs
    if qt == 'games': ret += game_level(**kwargs)
    else: ret += player_level(**kwargs)
    return ret


if __name__ == "__main__":
    print html()

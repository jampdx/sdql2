import S2.query_server

# trend_matchups and build_key_player uses this

def mups(dates):
    c = "H and date in %s"%dates
    sdql = "(team,o:team,line,total,date)@%s" % (c,)
    #print "sdql:",sdql
    res = S2.query_server.query('nba',timeout=10, client='KS', sdql=sdql,context='json',output='json')
    #print "mups.res:",res
    res = res.replace('json_callback','d=').replace('null','None')
    exec(res)
    return d

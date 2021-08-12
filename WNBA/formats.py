import PyQL.outputs
import urllib,cgi

import NBA.formats

class Query_Records(NBA.formats.Query_Records):
    def __init__(self,headers,**kwargs):
        kwargs.setdefault("show ats",1)
        kwargs.setdefault("show ou",1)
        #kwargs["level"] = "ncaa"
        NBA.formats.Query_Records.__init__(self,headers,**kwargs)

class Query_Summary(NBA.formats.Query_Summary):
    def __init__(self,headers,**kwargs):
        kwargs.setdefault("show ats",1)
        kwargs.setdefault("show ou",1)
        #kwargs["level"] = "ncaa"
        NBA.formats.Query_Summary.__init__(self,headers,**kwargs)



### tests and demos ####

def test_query(ncaabb):
    print ncaabb.query("(date,points,o:team)@team='BROWN' and season=2009")

def test_records(sdb):
    Q = Query_Records(headers=sdb.headers,ou=1)
    res = sdb.sdb_query(Q.select() + '@site and team[0]=B')
    print res
    #return
    html =  Q.output(res)
    open("/tmp/sdb.html",'w').write(html)
    #print html

def test_summary(sdb):
    Q = Query_Summary(headers=sdb.headers,ou=1)
    res = sdb.sdb_query(Q.select() + '@H and season=2009')
    print res
    #return
    html = ''
    for r in res:
        html += Q.output(r,**{'query_title':' '.join(r.name[-1])})
    open("/tmp/sdb.html",'w').write(html)
    #print html





if __name__ == "__main__":
    import sys
    from NCAABB.loader import ncaabb
    #test_query(ncaabb)
    #test_game_fields(ncaabb)
    #test_summary(ncaabb)
    test_records(ncaabb)

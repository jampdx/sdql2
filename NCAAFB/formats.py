import PyQL.dt
import PyQL.outputs
import urllib,cgi
from S2.common_methods import key_to_query_link
import S2.formats

import NFL.formats

#http://www.covers.com/pageLoader/pageLoader.aspx?page=/data/cfl/results/2013/boxscore37381.html
def box_link(gid,season,week,team,o_team,site): # overloading nfl call to link
    if not gid: return ''
    return "<a href=http://www.covers.com/pageLoader/pageLoader.aspx?page=/data/ncf/results/%s-%s/boxscore%s.html>box</a>"%(season,season+1,gid)



class Query_Records(NFL.formats.Query_Records):
    def __init__(self,headers,**kwargs):
        self.ngames = kwargs.get("ngames",1)
        self.ats = kwargs.get("ats",1)
        self.line = kwargs.get("line",1)
        self.ou = kwargs.get("ou",1)
        self.total = kwargs.get("total",1)        
        self.su = kwargs.get("su",1)
        self.n_rows = kwargs.get("n_rows",100)
        NFL.formats.Query_Records.__init__(self,headers,**kwargs)


class Query_Summary(NFL.formats.Query_Summary):
    
    def __init__(self,headers,**kwargs):
        self.show_unplayed = int(kwargs.get("show_unplayed",16))
        self.show_games = int(kwargs.get("show_games",40))
        NFL.formats.Query_Summary.__init__(self,headers,**kwargs)        
        




### tests and demos ####
def test_records(sdb):
    Q = Query_Records(sdb.headers,ou=1)
    res = sdb.sdb_query(Q.select() + '@site and team[0]=B')
    print res
    #return 
    html =  Q.output(res)
    open("/tmp/sdb.html",'w').write(html)
    #print html

### tests and demos ####
def test_summary(sdb):
    Q = Query_Summary(sdb.headers,ou=1)
    res = sdb.sdb_query(Q.select() + '@site and team[0]=B and season=2012')
    print res
    #return 
    html = ''
    for r in res:
        html += Q.output(r,**{'query_title':' '.join(r.name[-1])})
    open("/tmp/sdb.html",'w').write(html)
    #print html

def test_query(ncaafb):
    print ncaafb.sdb_query("%s@team=Bears and season=2009"%summary_fields())

if __name__ == "__main__":
    from NCAAFB.loader import ncaafb
    #test_query(ncaafb)
    #test_records(ncaafb)
    test_summary(ncaafb)
    

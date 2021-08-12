import urllib, urlparse

API_KEY = "plot.ly_137"

class SDB:
    def __init__(self,sport,table=''):
        # we need these to query the server at the right url
        self.sport = sport.lower()  
        self.table = table or ''   # self.query wants a string


    # query the server, convert json to a python dictionary that looks likes this for the sdql 'points@_i<10':
    #  d = {'headers': ['points'], 'groups':
    #          [{'sdql': '_i < 10', 'columns': [[105, 91, 100, 101, 112, 106, 106, 111, 112, 94]]}]}
    def query(self,sdql,**kwargs):
        # take care of some server parameters
        kwargs["sdql"] = sdql
        kwargs["output"] = "json"
        kwargs.setdefault("reduce", "1")
        kwargs["api_key"] = API_KEY
        # build up the url
        page = self.sport + "/%s%squery.json"%(self.table,self.table and '_')
        qs = '&'.join(["%s=%s"%(urllib.quote_plus(str(k)),urllib.quote_plus(str(v))) for (k,v) in kwargs.items()])        
        url = urlparse.urlunparse([ 'http','sportsdatabase.com',page, '',qs, ''])
        #print "url:",url
        result = urllib.urlopen(url).read() # this is a string representing a json callback
        # quick + dirty conversion from json to python
        result = result.replace('json_callback','d=').replace('null','None')
        exec(result) # create a python dictionary called `d`.   
        return d


def tests():
    # NFL games table
    #nfl = SDB("nfl")
    #res = nfl.query("A(points)@team and season=2013")
    #print res

    # nba player table
    nbap = SDB("nba","player")
    res = nbap.query("name, DK.FP @ date=today-1 and minutes>0")
    print res    
    
if __name__ == "__main__":
    tests()

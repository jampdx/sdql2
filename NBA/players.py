# load up the rosters and provide name => id look up and matching
import re, glob, os, cPickle
from PyQL.dt import DT
import PyQL.inputs as inputs


SPACE_UPPER_PAT = re.compile("([a-zA-Z])([A-Z])") # check for no space before a capitol letter

class Players(DT):
    
    def __init__(self,data_dir="/home/jameyer/S2/MLB/Data/Rosters/Columns"):
            DT.__init__(self, name="players")        
            inputs.append_from_pickled_columns(self,data_dir,1)
            self.pid_throws_dict = cPickle.load(open("/home/jameyer/S2/MLB/Data/Clients/SDB/Maps/pid_throws.pkl"))
            
    def build_dict(self):
        ret = {}
        headers = ["bats","dob","height","name","number","throws","weight"]
        q = "(pid,%s)@1"%','.join(headers)
        res = self.query(q)
        for player in res[0][0].data:
            h = 0
            pid = player[0]
            ret[pid] = {}
            for header in headers:
                h+=1  
                ret[pid][header] = player[h]
        # add historic starter throws data
        for pid in self.pid_throws_dict.keys():
            ret.setdefault(pid,{'throws':self.pid_throws_dict[pid]})
        return ret
        
     # a softish get method always returns a list - ideally of length 1       
    def get_pid(self,name,team=None):
        if team: team = team.lower().replace(' ','')   # teams are saved as lower case with collapsed spaces
        
        name = SPACE_UPPER_PAT.sub(lambda g:g.group(1)+' '+g.group(2) , name) # aA => a A        
        # first look for full name. for speed up could check for len > min len
        #print "search full",name         
        q = "(pid,name)@" + (team is not None)*("team='%s' and "%team) + "string.lower(name)='%s'"%name.lower()
        res = self.query(q)
        if res: return res[0][0].data

        # if put [a-z]* after each word.
        initials_name = ' '.join(map(lambda x:x+'[a-z]*',name.lower().split()))
        q = "(pid,name)@" + (team is not None)*("team='%s' and "%team) + "re.match('%s',name,re.I) is not None"%initials_name     
        res = self.query(q)
        if res: return res[0][0].data
            
        # try re.search
        #print "search for",name
        q = "(pid,name)@" + (team is not None)*("team='%s' and "%team) + "re.search('%s',name,re.I) is not None"%name.lower()     
        res = self.query(q)
        if res: return res[0][0].data

        # keep looking ....
        
        return []
 


       
############# test and demos ########
def test_get(p):
    print p.get_pid("AHi","bluejays")
    #print p.get_pid("JJ")
    
def test_build_dict(p):
    d = p.build_dict()
    return d

def test_query(p):
    sdql = "name, pid @ 1"
    r = p.query(sdql)
    print r

if __name__ == "__main__":
    p = Players("/home/jameyer/S2/MLB/Data/Rosters/Columns")
    p.show_metacode  = 1
    #test_get(p)
    #d = test_build_dict(p)
    test_query(p)

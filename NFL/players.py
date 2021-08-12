import re, glob, os, cPickle
from PyQL.dt import DT
from PyQL.columns import Column
import PyQL.inputs as inputs
import NFL.nfl_dt
import S2.query

SPACE_UPPER_PAT = re.compile("([a-zA-Z])([A-Z])") # check for no space before a cap letter



class Players:
    """ query on batters and pitchers to build a dt with header: team,name,pid """
    def __init__(self, nfl):
        self.bdt = self.build_player_dt(nfl.batters,"batter")
        self.pdt = self.build_player_dt(nfl.pitchers,"pitcher")
        #self.bdt.normalize_player_name = NFL.nfl_dt.normalize_player_name
        #self.pdt.normalize_player_name = NFL.nfl_dt.normalize_player_name
        
    def build_player_dt(self,table,flavor):
        tn = [] # [(t,n),...] so we don't use pid=None unless we have to 
        tc=[];nc=[];ic=[]
        table.show_metacode = 1
        res = table.query("U((%s id,%s name,team))@1"%(flavor,flavor))[0][0]
        res.sort(lambda x,y:cmp(y,x)) # put Nones last
        for i,n,t in res:
            n = NFL.nfl_dt.normalize_player_name(n) 
            t = NFL.nfl_dt.normalize_team_name(t)
            print i,n,t
            if i is None and (t,n) in tn:
                #print "have",t,n
                continue
            tn.append((t,n))
            tc.append(t);nc.append(n);ic.append(i)
        del tn
        print "players.Players.build_player_dt ready to ret"
        return DT(name="b",data=[Column(name='team',data=tc),Column(name='name',data=nc),Column(name='pid',data=ic)])
        
     # a softish get method always returns a list - ideally of length 1
    def find_player(self,name,team=None,batter=1,pitcher=1):
        if pitcher: ndt = self.pdt
        else: ndt = self.bdt
        return S2.query.find_player(ndt,name,team)
     
    def XXXget_pid(self,name,team=None,batter=1,pitcher=1):
        if team: team = NFL.nfl_dt.normalize_team_name(team)
        
        name = SPACE_UPPER_PAT.sub(lambda g:g.group(1)+' '+g.group(2) , name) # aA => a A         # OBrian would need to be obrian
        # first look for full name. for speed up could check for len > min len
        #print "search full",name         
        q = "U((pid,name))@" + (team is not None)*("team='%s' and "%team) + "name='%s'"%name.lower()
        if batter:
            res = self.bdt.query(q)
            if res: return res[0][0].data
        if pitcher:
            res = self.pdt.query(q)
            print "q,res:",q,res
            if res: return res[0][0].data

        # if put [a-z]* after each word.
        initials_name = ' '.join(map(lambda x:x+'[a-z]*',name.lower().split()))
        q = "U((pid,name))@" + (team is not None)*("team='%s' and "%team) + "re.match('%s',name,re.I) is not None"%initials_name
        if batter:
            res = self.bdt.query(q)
            if res: return res[0][0].data
        if pitcher:
            res = self.pdt.query(q)
            if res: return res[0][0].data
            
        # try re.search
        #print "search for",name
        q = "U((pid,name))@" + (team is not None)*("team='%s' and "%team) + "re.search('%s',name,re.I) is not None"%name.lower()
        if batter:
            res = self.bdt.query(q)
            if res: return res[0][0].data
        if pitcher:
            res = self.pdt.query(q)
            if res: return res[0][0].data
        # keep looking ....
        
        return []


       
############# test and demos ########
def test_get(p):
    print p.get_pid("AHi","bluejays")
    #print p.get_pid("JJ")
    

def test_query(p):
    sdql = "name, pid @ 1"
    r = p.bdt.query(sdql)
    print r

if __name__ == "__main__":
    #p = NFL_Players("/home/jameyer/S2/NFL/Data/Rosters/Columns")
    nfl = NFL.nfl_dt.loader()
    p = Players(nfl)
    test_get(p)
    #d = test_build_dict(p)
    #test_query(p)

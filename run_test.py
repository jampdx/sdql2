import os,string,time,glob,cPickle,urllib,multiprocessing
import PyQL.py_tools
import PyQL.mail_tools
import S2.query
import S2.query_server
import S2.trend_dt
import S2.trends
from S2.directory import CLIENT_DIR, RESTART

GROUPS = { # some of the usual groups: can override in .trend file
       "SITE":"H,A,1",
       "p:SITE":"p:H,p:A,1",
       "p2:SITE":"p2:H,p2:A,1",
       "op:SITE":"op:H,op:A,1",
       "op2:SITE":"op2:H,op2:A,1",
       "LINE":"F,D,1",
       "p:LINE":"p:F,p:D,1",
       "p2:LINE":"p2:F,p2:D,1",
       "op:LINE":"op:F,op:D,1",
       "op2:LINE":"op2:F,op2:D,1",
       "p:SU":"p:W,p:L,1",
       "p2:SU":"p2:W,p2:L,1",    
       "op:SU":"op:W,op:L,1",
       "op2:SU":"op2:W,op2:L,1",    
       "TEAM":"t:team,1"
    }


# to run in a separate process
def query_and_pickle(**kwargs):
    print "query farm:",kwargs['server']
    url = "http://%s/%s/query?%s"%(kwargs['server'],kwargs['sport'].lower(),urllib.urlencode(kwargs))
    #print "call out to URL:",url
    res = urllib.urlopen(url=url).read()
    #print "slave got: %s"%res
    try:
        cd = cPickle.loads(res)
    except:
        return "the url called returned no pickled object."
    #print "pkliing to ",kwargs['fout']   
    cPickle.dump(cd,open(kwargs['fout'],'w'))

    



class Feeder:
    def __init__(self,f, sport, client, run=1, clean=1, update=0, upload=0,servers=[], **kwargs): 
        """
     Run trends from a `.trend` file containing a list of trends preceded by optional args and group definitions.
     groups are defined in f like this: `.SITE:H,A,1`  and are expanded locally
     args are defined in f like this: `@margin=t:runs-o:runs`. They overwrite passed in kwarg and are eventually passed to the server via urllib's query string
     Trends are feed line by line (with expanded out groups) to the query server with kwargs.
     The special output of `dump_trends` catches the query results, culls and dumps a numbered pkl (containing n>=1 trends) to eg KS/MLB/Trend/annual_ml_on/1.pkl 
    """
        self.servers = servers
        self.ready_servers = servers[:]
        self.running_servers = []
        self.sport = sport
        # these can also be overwritten from the .trend file
        kwargs["client"] = client
        self.client = client
        #kwargs['short_cuts']
        kwargs["output"] = "dump_trends"
        kwargs["context"] = "raw"
        kwargs["show_parameters"] = "0"
        kwargs["show_howto"] = "0"
        kwargs["page"] = "query"
        kwargs["nice"] = "18"

        self.upload = upload
        self.count = 0
        self.errors = []
        self.f = f

        self.kwargs = kwargs
        self.update = update
        self.fread = f 
        if update: self.fread = f.replace(".trend",".update")
        self.dout = os.path.join(f[:-6]) 
        self.pout = os.path.join( self.dout,"_Pickle")
        self.cout = os.path.join( self.dout,"_Column")
        if not os.path.isdir( self.dout):
            print "making trend dir at", self.dout        
            os.system("mkdir %s"% self.dout)
        if not os.path.isdir( self.pout):
            print "making trend _Pickle dir at", self.pout        
            os.system("mkdir %s"% self.pout)
        if not os.path.isdir( self.cout):
            print "making trend _Column dir at", self.cout        
            os.system("mkdir %s"% self.cout)
            
        if update: self.make_update_file()
        if clean:
            print "clearing old pkl from", self.pout
            os.system("rm -f %s"%(os.path.join( self.pout,'*.pkl')))         
        if run: self.run()
        self.build_columns()
        self.log()
        self.notify()

    def make_update_file(self):
        # get the instructions from the original file
        out = map(string.strip,open(self.f).readlines())
        if out and out[0] and out[0][0] == '|': # want to pipe in another trend set to use as a template.
            ofile = os.path.join(os.path.split(self.fread)[0],out[0][1:])
            olines = map(string.strip,open(ofile).readlines())
            out = olines + out
        
        out = filter(lambda x:x and x[0] in '#@',out)
        out.append("@find_best_date=0")
        out.append("@show_record=0")
        out.append("@update_record=1")
        f = os.path.join(self.dout,'_Column','sdql.pkl')
        sdql = cPickle.load(open(f))
        f = os.path.join(self.dout,'_Column','english.pkl')
        english = cPickle.load(open(f))
        len_sdql = len(sdql)
        N = min(len_sdql,self.kwargs.get('N',len_sdql))
        for i in range(N):
            if PyQL.py_tools.in_parens(sdql[i]): out.append('%s as "%s"'%(sdql[i],english[i]))
            else: out.append('(%s) as "%s"'%(sdql[i],english[i]))
        open(self.fread,'w').write('\n'.join(out+['']))
                     
    def run(self):
        # kwargs["client"] = os.path.dirname(dout).split(CLIENT_DIR)[-1]
        #print kwargs
        today = PyQL.py_tools.today()
        self.kwargs.setdefault("column_flavor",'Best_Profit') # the columns.Column class name
        self.kwargs.setdefault("find_best_date",'0')
        self.kwargs.setdefault("margin","t:points-o:points")
        self.kwargs.setdefault("wager","t:line") # MLB style
        self.kwargs.setdefault("p","0.5")     # NFL style
        self.kwargs.setdefault("pval","1")     # NFL style
        self.kwargs.setdefault("give_up","None") # (N,min_profit|max_pval) if after N games still don't have min_profit then abort search.
        self.kwargs.setdefault("perfect","None") # if both a win and a loss then abort search.
        
        cchars = '#@.>'
        groups = self.kwargs.get("groups",GROUPS)
        lines = map(string.strip,open(self.fread).readlines())

        if lines and lines[0] and lines[0][0] == '|': # want to pipe in another trend set to use as a template.
            ofile = os.path.join(os.path.split(self.fread)[0],lines[0][1:])
            olines = map(string.strip,open(ofile).readlines())
            lines = olines + lines

        good_lines = filter(lambda x:len(x.strip()),lines)
        trend_lines = filter(lambda x,cc=cchars:x[0] not in cc,good_lines)
        clines =  filter(lambda x,cc=cchars:x[0] in cc,good_lines)
        for line in clines:
            if line[0] == '#': continue
            if line[0] == '>': continue # pat replace ?
            if line[0] == '.': # defines a mappings .SITE=>H as home, A as away,1
                name,options = line[1:].split('=>',1)
                groups[name] = options 
                continue
            if line[0] == '@': # a parameter: pass to kwargs
                name,value = (line[1:].split('=') + ['1'])[:2] # allow setting flags to '1' with just @best_profit
                self.kwargs[name] = value
                continue

        i = 0
        n_trends = len(trend_lines)
        for line in trend_lines:
            if line[0] == '^': break
            i += 1
            #if not 27 < i < 33: continue
            #if "_tppp" not in line: continue
            # avoid overhead of new query by bundling
            #print "sk[gb]:",        type( self.kwargs.get('groupby'))   
            if self.kwargs.get('groupby') in [0,'0']: # strings here for url args replace groups with 1
                parts =  map( lambda p,g=groups:(g.has_key(p) and '1') or p,line.split('|') )
                #print "runtrneds. no group parts",parts
            else:
                exclude = []
                if 'series'  in line:
                    exclude.append('SERIES')
                if ' win'  in line or ' loss' in line:
                    exclude.append('p:SUR')

                parts = map( lambda p,g=groups,e=exclude:(p in e and '1') or  g.get(p,p),line.split('|') )
            
            cparts = []
            combos = 1
            for part in parts:
                grps = PyQL.py_tools.split_not_protected(part,',')
                combos *= len(grps)
                if combos > 100:
                    cparts.append(grps)
                else:
                    cparts.append([part])
            
            #parts = map(lambda p,s=PyQL.py_tools.split_not_protected:s(p,','), parts)
            #print "cparts:",cparts
            parts = PyQL.py_tools.all_combinations(cparts)
            len_parts = len(parts)
            #print "Ready to run",len_parts,"sub trends. with kwargs:",self.kwargs
            #raise
            j = 0
            for part in parts:
                j += 1
                print "trends set %s: %d/%d %d/%d "%(self.dout,i,n_trends,j,len_parts) 
                self.kwargs["fout"] = os.path.join(self.pout , "%s_%s.pkl"%(i,j))            
                conditions = ' and '.join(  filter( lambda p:p!='1', part) )
                if not conditions.strip(): continue

                if self.kwargs['column_flavor'] in ["Best_Profit","Best_ROI"]:
                    select = "Best_Profit((%s,%s,date,team),give_up=%s,perfect=%s,roi=%s) as record"%(
                                self.kwargs["margin"],self.kwargs["wager"],self.kwargs["give_up"],self.kwargs["perfect"],1*(self.kwargs['column_flavor']=="Best_ROI"))
                elif self.kwargs['column_flavor'] == "Best_Record":
                    select = "Best_Record((%s,date),p=%s,give_up=%s,perfect=%s) as record"%(
                            self.kwargs["margin"],self.kwargs["p"],self.kwargs["give_up"],self.kwargs["perfect"])

                select +=",U((date,team)*(date >= %s)) as future_dateteam"%today  
                self.kwargs["sdql"] = "%s@%s"%(select, conditions)
                print "sdql cond:",conditions
                #self.kwargs["debug"] = "1"
                timeout = 20
                if self.client in ["KS","SDB"]: timeout = 300
                if self.servers:
                    self.kwargs['sport'] = sport
                    self.kwargs["context"] = "pkl"
                    # check for any running processes being done
                    while not self.ready_servers:
                        for p in range(len(self.running_servers)-1,-1,-1):
                            proc,server = self.running_servers[p]
                            #print "chk #",p,proc.ready()
                            
                            if proc.ready():
                                #print "server %d named %s finished"%(p,server)
                                del self.running_servers[p]
                                self.ready_servers.append(server)
                        if not self.ready_servers:
                            #print "no server is ready: sleep for a sec"
                            #print "running:",len(self.running_servers)
                            time.sleep(1)
                    server = self.ready_servers.pop()
                    self.kwargs['server']=server
                    #print "registered as running:", server
                    proc = POOL.apply_async(query_and_pickle,
                                              kwds=self.kwargs)
                    self.running_servers.append((proc,server))
                else:
                    #print "runtrends hitting server with",self.kwargs
                    res = S2.query_server.query(sport,timeout=timeout, **self.kwargs)
                    mo = S2.query.PAT_COUNT.search(res)
                    if mo and int(mo.group('count')):
                        self.count += int(mo.group('count'))
                        print "total N:",self.count
                    elif "error" in res.lower():
                        self.errors.append(conditions)
                #print res.strip()
        print "errors:",self.errors

    def build_columns(self):
        print "run_trends.build_coilumns"
        # move generated files to columns 
        # assume a directory full of pkled trends
        # combine these sort and take top self.kwargs[N]
        pfs = glob.glob(os.path.join(self.pout,"*.pkl"))
        print "run_trends.glob at",self.pout        
        if not pfs:
            print "No results"
            return 
        #print pfs
        cd = {} # column dict
        d = cPickle.load(open(pfs[0]))
        #print "run_trends.d",d
        for k in d.keys():
            cd[k] = []
        for pf in pfs:
            d = cPickle.load(open(pf))
            #print "pf:",pf
            for k in d:
                #print "k,len",k,len(d[k])
                cd[k] += d[k]

        if not len(cd.values()[0]):
            return "no results"

        for k in cd.keys():
            print k,len(cd[k])
            #assert len(cd.values()[0]) == len(cd[k])
            if len(cd.values()[0]) != len(cd[k]):
                print "how odd, the columns are not of the same length"
                return

        sort = self.kwargs.get('sort')
        if not sort and 'pval' in cd.keys(): sort = 'pval'
        if not sort and 'profit' in cd.keys(): sort = 'profit'
        if sort:
            if sort not in cd.keys():
                return "sort not in keys: %s: %s"%(sort,cd.keys())
            temp = []
            for i in range(len(cd[sort])):
                temp.append((cd[sort][i],i))
            temp.sort()
            cdt = {}
            for k in cd.keys():
                cdt[k] = []
                for v,i in temp:
                    cdt[k].append(cd[k][i])
                cd[k] = cdt[k]
                
        if sort == 'profit':
            for k in cd.keys():
                cd[k].reverse()

        N = int(self.kwargs.get('N',0) )
        if N and N < len(cd.values()[0]):
            for k in cd.keys():
                cd[k] = cd[k][:N]

        for k in cd.keys():
            print "writing",k
            f = open(os.path.join(self.cout,"%s.pkl"%k),'w')
            cPickle.dump(cd[k],f)
            f.close()
        if self.upload:
            # 20140912: lay turd in Log/trend.sync' picked up by root via crontab and S2.monitor,py
            open(os.path.join(S2.directory.LOG_DIR,"%s.sync_trend"%self.sport.lower()),'a').write(self.cout+'\n')
            #scp_txt = "scp %s sportsdatabase.com:%s"%(os.path.join(self.cout,'*.pkl'),os.path.join(self.cout,"."))
            #os.system(scp_txt)
            #restart_filename = "/tmp/%s_trends.restart"%self.sport.lower()
            #open(restart_filename,'w').write("remote restart request at %s"%time.ctime())
            #os.system("rsync -r  %s sportsdatabase.com:%s"%(restart_filename,
            #                                                os.path.join(S2.directory.LOG_DIR,"%s_trends.restart"%self.sport.lower())))

    def log(self):
        logd = os.path.join(os.path.split(self.f)[0],"_Count")
        if not os.path.isdir(logd):
            os.system("mkdir %s"%logd)
        logf = os.path.join(logd,"%s.int"%PyQL.py_tools.today())
        start = 0
        if os.path.isfile(logf):
            start = int(open(logf).read().strip())
        open(logf,'w').write("%d"%(start+self.count))

        
    def notify(self):
        message = ''
        message += "Done with %d trends with %d errors<p>"%(self.count,len(self.errors))
        if self.errors: message += '<p>'.join(self.errors)
        email = self.kwargs.get('email')
        email_active_links = self.kwargs.get('email_active_links')
        if email and email_active_links:
            # build a dt and query it
            dt = S2.trend_dt.loader(self.sport,client_glob=self.client,trend_set_glob=self.f.split(".trend")[0])
            kw = {}
            kw["result_only"] = 1 
            kw["sport"] = self.sport
            kw["client"] = self.client
            kw["pyql"] = self.kwargs.get("pyql","1>0")
            host = self.kwargs.get("host","SportsDatabase.com")
            if str(email_active_links) not in ['all','1']:
                kw['active_dates'] = email_active_links # can set to today; tomorrow; date; date1,date2,...
            message += S2.trends.query(dt,**kw).replace("href=query?sdql","href=http://%s/%s/query?sdql"%(
                                                        host,self.sport,))
            
            message += "<p>Update your e-mail notification preferences from the trends page."
        if email:
            print "mailoing to",email
            try:
                PyQL.mail_tools.send_html(sender = "support@SportsDatabase.com",
                                      receiver = email,
                                      subject="%s Trends Ready"%self.sport.upper(),                                      
                                      html="<html>" + message + "</html>")
            except:
                print "trend e-mail notifiction failed" 


        #else:
        #    print "mail message:\n",message
########## utils #######

def preprocess_trends(trends):
    # allow users to enter a more user friendly bar delimited format.
    # first line is !flavor and we only handle !bar and !tab for now.
    out = []
    for trend in trends[1:]:
        if trend[0] == '#': continue
        if trend[0] in '@^':
            out.append(trend)
            continue
        
        trend=trend.strip()
        if not trend: continue
        if trend[-1] == '|': trend = trend[:-1]
        trend = ''.join(map(lambda x:(ord(x)>125)*"'" or x,trend))
        trend = trend.replace("< =","<=") .replace("> =",">=")  # these worked in 1.0 and not 2
        parts = map(lambda x:x.strip(),trend.split('|'))
        if len(parts) == 1:
            parts = map(lambda x:x.strip(),trend.split('\t'))
        if len(parts) == 3:
            tid,eng,sdql = parts
            out.append('(%s) as "%s=>%s: %s"'%(sdql,sdql,tid,eng))
        elif len(parts) == 2:
            eng,sdql = parts
            out.append('(%s) as "%s=>%s"'%(sdql,sdql,eng))
        else:
            #raise Exception("Unexpected line: %s"%trend)
            print "Unexpected line:",trend
    return out    

def post_trends(**kwargs):
    # write to a file, start running and return a link to the impending trends (add time estimate, email option)
    print "runtrends.post_rends.Hi"
    client = kwargs.get("client")
    sport = kwargs.get("sport")
    trend_set = kwargs.get("trend_set","web").replace(" ","_")
    fd = os.path.join(S2.directory.CLIENT_DIR,client,sport.upper(),"Trend")
    trend_lines = map(lambda x:x.strip(),kwargs.get("trends",'').split('\n'))
    if trend_lines and trend_lines[0] and trend_lines[0][0] == '!':
        trend_lines = preprocess_trends(trend_lines)
    params = filter(lambda x:len(x.strip()) and x[0] == '@',trend_lines)
    for param in params:
        name,value = (param[1:].split('=') + ['1'])[:2] 
        kwargs[name] = value
        
    trends = filter(lambda x:len(x.strip()) and x[0] not in '@',trend_lines)
    if not trends:
        tf = os.path.join(fd,trend_set+".trend")
        if os.path.isfile(tf): os.system("rm %s"%tf)
        return "No trends found: removing trend set %s"%trend_set
    if not client: return "Guests cannot use this page."
    if not sport: return  "`sport` is a required kwarg."

    d = {}
    d["show_record"] = kwargs.get("show_record",0)
    d["N"] = kwargs.get("N",2000)
    d["perfect"] = kwargs.get("perfect",0)
    d["p"] = kwargs.get("p",0.5)
    d["pval"] = kwargs.get("pval",1) # pval=1 means don't filter
    d["find_best_date"] = kwargs.get("find_best_date",0)
    if kwargs.get('email'): d['email'] = kwargs['email']
    if kwargs.get('email_active_links'): d['email_active_links'] = kwargs['email_active_links']
    d["margin"] = kwargs.get("margin","points+line-o:points")
    d["column_flavor"] = "Best_Record"
    if sport.lower() in ['mlb','nhl']: 
        d["column_flavor"] = "Best_Profit"
        if sport.lower() == 'mlb': d["margin"] = kwargs.get("margin","runs-o:runs")
        else: d["margin"] = kwargs.get("margin","goals-o:goals")        

    print "post trends to",fd
    if not os.path.isdir(fd):
        os.makedirs(fd)
    f = os.path.join(fd,"%s.trend"%trend_set)
    #print "write trends with\n %s\n\n%s"%(d,trends)
    write_trend_set(f,d,trend_lines) 
    len_trends = len(filter(lambda x:len(x) and x[0]!='@',trends))
    run_trends = os.path.join(S2.directory.SOURCE_DIR,"run_trends.py")
    print "ready to run wiht os.sus"
    os.system("nice -n 19 python %s sport=%s client=%s trend_set=%s restart=1&"%(
                               run_trends,sport,client,trend_set)) 
    return """Your %s trend%s will be viewable <a href=trends?trend_set=%s>here</a> when done. <BR>
                Check back in 5 minutes."""%(len_trends,'s'*(len_trends!=1),trend_set)

def write_trend_set(f,        # write to
                    kwargs,   # see S2.formats.Dump_Trends for key words:
                    trends=["TEAM|SITE|LINE|p:SITE|p:LINE|p:SU"]):     # sample named groups are defined above 
    out = []
    items = kwargs.items()
    items.sort()
    for k,v in items:
        out.append("@%s=%s"%(k,v))
    open(f,'w').write( '\n'.join(out+trends+['']) )

# write a trend set from a larger culled set: don't forget to add the headers manually.
def trend_set_from_pickle():
    f = os.path.join(CLIENT_DIR,'KS','NBA','Trend','ats_kba_raw','_Column','sdql.pkl')
    trends = cPickle.load(open(f))
    print '\n'.join(trends)

def generate_sample_sets():
    d = {}
    client = "SDB"
    d["show_record"] = 1
    d["N"] = 1000
    d["english_as_sdql"] = 1
    d["perfect"] = 1
    # su for all sports
    d["column_flavor"] = "Best_Record"    
    d["margin"] = "points-o:points"
    d["pval"] = "0.01"
    d["p"] = "0.5"
    d["give_up"] = "(10,0.1)" # gets slow if we don't give up.
    d["english_as_sdql"] = 1
    d["find_best_date"] = 1
    #d["bet"] = "SU"    
    su_trends =  ["TEAM|SITE|p:SITE|p:SU"]
    #su_trends =  ["SITE|p:SITE|p:SU"]
    f = os.path.join(S2.directory.CLIENT_DIR,client,'NFL',"Trend","sample_su.trend")
    write_trend_set(f,d,trends=su_trends)
    f = os.path.join(S2.directory.CLIENT_DIR,client,'NCAAFB',"Trend","sample_su.trend")
    write_trend_set(f,d,trends=su_trends)
    f = os.path.join(S2.directory.CLIENT_DIR,client,'NBA',"Trend","sample_su.trend")
    write_trend_set(f,d,trends=su_trends)
    f = os.path.join(S2.directory.CLIENT_DIR,client,'NCAABB',"Trend","sample_su.trend")
    write_trend_set(f,d,trends=su_trends)
    d["margin"] = "goals-o:goals"    
    f = os.path.join(S2.directory.CLIENT_DIR,client,'NHL',"Trend","sample_su.trend")
    write_trend_set(f,d,trends=su_trends)    
    d["margin"] = "runs-o:runs"    
    f = os.path.join(S2.directory.CLIENT_DIR,client,'MLB',"Trend","sample_su.trend")
    write_trend_set(f,d,trends=su_trends)

    del d["p"]
    del d["pval"]
    
    d["perfect"] = "0"    
    # Money Line Sports
    d["column_flavor"] = "Best_Profit"
    d["min_profit"] = 1000
    d["give_up"] = "(10,0)"
    
    sport = "MLB"
    
    d["margin"] = "runs-o:runs"
    d["wager"] = "line"
    d["flip_record"] = "0"
    #d["bet"] = "ML"
    #d["side"] = "ON"    
    f = os.path.join(S2.directory.CLIENT_DIR,client,sport,"Trend","sample_ml_on.trend")
    #print "writing ",d,"to",f
    write_trend_set(f,d)

    d["margin"] = "o:runs-runs"
    d["wager"] = "o:line"
    d["flip_record"] = "1"
    #d["bet"] = "ML"
    #d["side"] = "AGAINST"    
    f = os.path.join(S2.directory.CLIENT_DIR,client,sport,"Trend","sample_ml_against.trend")
    write_trend_set(f,d)

    sport = "NHL"
    
    d["margin"] = "goals-o:goals"
    d["wager"] = "line"
    d["flip_record"] = "0"
    #d["bet"] = "ML"
    #d["side"] = "ON"    
    f = os.path.join(S2.directory.CLIENT_DIR,client,sport,"Trend","sample_ml_on.trend")
    write_trend_set(f,d)

    d["margin"] = "o:goals-goals"
    d["wager"] = "o:line"
    d["flip_record"] = "1"
    #d["bet"] = "ML"
    #d["side"] = "AGAINST"    
    f = os.path.join(S2.directory.CLIENT_DIR,client,sport,"Trend","sample_ml_against.trend")
    write_trend_set(f,d)

    # Line = +/- Points Sports
    del d["wager"] 
    del d["flip_record"] 
    del d["min_profit"]
    #del d["side"]
    d["column_flavor"] = "Best_Record"    
    d["margin"] = "points+line-o:points"
    d["pval"] = "0.01"
    d["p"] = "0.5"
    d["give_up"] = "(10,0.1)" # gets slow if we don't give up.
    d["bet"] = "ATS"    
    for sport in ["NFL","NBA","NCAABB","NCAAFB"]:
        f = os.path.join(S2.directory.CLIENT_DIR,client,sport,"Trend","sample_ats.trend")
        write_trend_set(f,d)
    


def ks_sub(text):
    return text.replace("DPS","dps").replace("DPA","dpa")
def translate_KS_trends(sport='nfl'):
    # quick and dirty patch for NFL and NBA 2012
    fs = glob.glob("/home/jameyer/Sports/NFL/Source/Batch/KS/Client/*")
    fs.sort()
    fs = filter(os.path.isfile,fs)
    print "fs:",fs
    for f in fs:
        print "f:",f
        lout = ["@column_flavor=Best_Record","@find_best_date=0","@p=0.5","@perfect=0","@pval=1","@show_record=0"]            
        lines = filter(len,map(string.strip,open(f).readlines()))
        if lines[0][:5] != '#bet=':
            print lines[0]
            raise "surprise format"
        exec(lines[0][1:].strip())
        lout.append({"ats":"@margin=points+line-o:points","ou":"@margin=points+o:points-total"}[bet])
        for line in lines[1:]:
            print "line:",line
            parts = filter(len,map(string.strip,line.split('|')))
            if len(parts) == 2:
                lout.append("(%s) as '%s'"%(ks_sub(parts[1]),parts[0].replace("'","")))
            else:
                lout.append(ks_sub(parts[0]))

        fout = os.path.join(S2.directory.CLIENT_DIR,'KS',sport.upper(),"Trend",os.path.basename(f)+".trend")
        lout.append('')
        open(fout,'w').write('\n'.join(lout))                

SERVER_FARMS = {}
#SERVER_FARMS = {"td": ["ks.sportsdatabase.com","sportsdatabase.com"],'johp':['s2.johp']}

#SERVER_FARMS["t3"] =  ["ks.sportsdatabase.com","sportsdatabase.com","s2.johp"]

SERVER_FARMS["s2"] = ["s2.johp"]
#SERVER_FARMS["108"] = ["108.sportsdatabase.com"]
#SERVER_FARMS["158"] = ["158.sportsdatabase.com"]
SERVER_FARMS["69"] = ["69.sportsdatabase.com"]

        
if __name__ == "__main__":
    post_trends(client='guest',sport='mlb',trends='HD'); raise
    #trend_set_from_pickle(); raise
    #translate_KS_trends();raise
    sf = None
    sfm = 1 # how many cores per farm server
    generate = 0
    sport = 'ncaafb'
    client = 'cajun'
    trend_set = '*'
    restart = 0
    update = 0
    upload = 0
    run =1
    clean=1
    groupby = 1
    and_then_update = 0 # immediately update. If a large set is generated it could be stale when done.
    N = 0
    import sys, string
    for arg in sys.argv[1:]:
        if '=' not in arg:
            arg = arg+"=1"
        var, val = string.split(arg,'=')
        try:              #first ask: Is this in my name space?
            eval(var)
        except:
            print "Can't set", var
            sys.exit(-1)
        try:
            exec(arg)  #numbers
        except:
            exec('%s="%s"' % tuple(string.split(arg,'='))) #strings
    if generate:
        print "generating sample sets"
        generate_sample_sets()
    if not sport or not client:
        raise Exception, "Need sport and client to be defined on the command line."
    globber = os.path.join(CLIENT_DIR,client,sport.upper(),"Trend",trend_set+'.trend')
    print "globbinhg woith",globber
    fs = glob.glob(globber)
    fs.sort()
    servers = []
    if sf:
        servers = SERVER_FARMS[str(sf)] * sfm
    POOL = multiprocessing.Pool(len(servers) + 2)        
    for f in fs:
        print "running",f," in update mode"*(update==1)
        # upload is not tested
        immediate_upload = upload
        if and_then_update: immediate_upload = 0
        Feeder(f,sport,client=client,run=run,clean=clean,update=update,upload=immediate_upload,servers=servers,groupby=groupby,N=N)
        if not update and and_then_update:
            Feeder(f,sport,client=client,run=run,clean=clean,update=1,upload=upload,servers=servers,groupby=groupby,N=N)            
    if restart:
        print "setting restart flag"        
        RESTART(sport,"trends")
    else:
        print "restart not requested"

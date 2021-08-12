import PyQL.outputs, PyQL.py_tools
import urllib,cgi,re,os
import cPickle
from S2.common_methods import key_to_query_link
import S2.trends
import S2.directory
import scipy.stats
import numpy

TEAM_PLAYER_PAT = S2.directory.TEAM_PLAYER_PAT

class Query:
    key_to_query_link = key_to_query_link
    def __init__(self,headers,**kwargs):
        self.kwargs = kwargs
        self.headers = map(lambda x:x.split('.')[-1],headers)

    def output_html(self,res):
        return PyQL.outputs.html(res)


class Dump_Trends(Query):

    def output(self,res):
        # query is of form: date, metric @ groups and conditions and team=Bulls and name='Bob Jones'$
        # look for the groups most different from the shortest group
        # select based on delta, number of games, and the number of conditions
        #reload(S2.directory); reload(S2.trends)
        #print "RELOADed S2.directory, trends - TURN OFF FOR DEPLOYMNET"
        today = PyQL.py_tools.today()
        print "player_formats.Dump_Trends gets res of len",len(res)
        if not res or not len(res):
            print "formats.Dump_Trends gets NoResults"
            return 'No results'
        date_offset = 0
        metric_offset = 1
        fout = self.kwargs.get('fout','/tmp/nba_player_default.pkl')
        client = self.kwargs.get('client','guest')
        sport = self.kwargs.get('sport','default')
        show_record = self.kwargs.get("show_record")
        translator = self.kwargs.get('translator','default')
        # pick up args with defaults.
        self.english_as_sdql = self.kwargs.get("english_as_sdql",0) # A => A rather than A => site=='away'
        find_best_date = int(self.kwargs.get("find_best_date", 0)) # need also on transform key

        min_delta = float(self.kwargs.get("delta",1))
        min_N = int(self.kwargs.get("min_N",1))
        max_pval = float(self.kwargs.get("pval",0.2))
        # define column
        cd = {}
        for k in "name,team,sdql,english,active,delta,pval".split(','):
            cd[k]=[]

        # need the index of the most populous result
        theaders = map(lambda x:(len(x[0]),x.name),res)
        theaders.sort()
        isk = res.headers.index(theaders[-1][1])
        print "isk:",isk
        print "base trned name:",res[isk].name
        parent_data = filter(lambda x:x is not None,res[isk][metric_offset].data)
        if len(parent_data) < min_N:
            print "too few: resturn"
            return "not enough games for this situation"
        arr_isk = numpy.array(parent_data)
        avg_isk = numpy.average(arr_isk)
        for i in range(len(res)): # this many group bys
            if i == isk: continue
            if '_baseline' in str(res[i].name): continue
            child_data = filter(lambda x:x is not None,res[i][metric_offset].data)
            if len(child_data) < min_N:
                print "didn't make min N cut"
                continue
            arr_i = numpy.array(child_data)
            avg_i = numpy.average(arr_i)
            delta =  avg_i - avg_isk
            #print "pf.delta",delta
            if -min_delta < delta < min_delta:
                print "didn't make delta cut:",avg_i,avg_isk,min_delta
                continue
            # met all simple tests, now look for a 'pval'
            foo, pval = scipy.stats.mannwhitneyu(arr_i,arr_isk)
            pval = pval * 2 # two sided
            print "pval",pval
            if pval>max_pval:
                print "didn't made the pval cut with",pval
                continue
            print "made the pval cut with",pval
            print "name:",res[i].name
            pat_sub_pairs =  S2.trends.PAT_SUB_PAIRS + S2.directory.CLIENT_TRANSLATORS.get(client,{}).get(sport.upper(),{}).get(translator,[])
            query_key , english_key = self.transform_key(res[i].name,
                                                        pat_sub_pairs=pat_sub_pairs,
                                                        show_date=0,
                                                        sport=sport)
            #query_key , english_key = self.transform_key(res[i].name)
            #print  "query_key , english_key:", query_key , english_key
            query_key = S2.trends.clean_as_sdql(query_key)

            mo = TEAM_PLAYER_PAT.findall(query_key)
            if len(mo):
                team,player = mo[0].split(':')
            else:
                team = player = None
            #print "plater_formats:",team,player
            active = [] # [(date,team,player),..]
            for d in range(len(res[i][0])):
                #print "testing for active:",res[i][date_offset][d], today
                if res[i][date_offset][d] >= today:
                    active.append((res[i][date_offset][d],team,player))

            cd["sdql"].append(query_key)
            cd["english"].append(english_key)
            cd["team"].append(team)
            cd["name"].append(player)
            cd["delta"].append(delta)
            cd["pval"].append(pval)
            cd["active"].append(active)


        if self.kwargs.get('winnow'):
            print "winnow not built for players"
        if self.kwargs.get('context','') == 'pkl':
            return cPickle.dumps(cd)

        fname = os.path.join(S2.directory.CLIENT_DIR,(fout))
        #print "write to",fname
        if not len(cd["sdql"]):
            return "no trends"
        f = open(fname, 'w' )
        cPickle.dump(cd,f)
        f.close()

        return "saved %s"%fname


    def transform_key(self,key,record=None,pat_sub_pairs=None,show_record=0,update_record=0,show_date=0,bet=None,side=None,sport='default'):
        sdql,english = S2.trends.split_key(key)
        if "=>" in english:
            #print "fpormat.transxofmr_ket.englogn:",english
            return english.split("=>",1)
        #return sdql,english
        if self.english_as_sdql:
            sdql = english # need to preserve short cuts used in trend generation.
        #open("/tmp/nba.out",'a').write("record:%s\n"%record)
        if record:
            if show_record:
                #english += " have a %s %s record of %s"%(bet or '',side or '',record[:-1],)
                english += " have a %s record of %s"%(bet or '',record[:-1],)
            if update_record:
                english += " UPDATE have a %s %s record of %s and date>=%s"%(bet or '',side or '',record[:-1],record[-1])
                #open("/tmp/nba.out",'a').write("ebg:%s\n"%english)
            if record[-1] and show_date:
                #print "adding to sdql:" + " and date>=%s"%record[-1]
                sdql  += " and date>=%s"%record[-1]
                #english  += " since %s"%record[-1]
                english  += " and date >= %s"%record[-1] # build nice english with pat_sub_pairs
        if pat_sub_pairs: # cleint specific translations.
            #print "english pre sub:",english
            english = S2.trends.translate(english,pat_sub_pairs)
            #print "english post sub:",english
            sdql = S2.trends.translate(sdql)

        if sport.startswith('ncaa') and english.startswith('The '):
            parts = english.split()
            if parts[2] == 'are':
                parts[2] = 'is'
                english = ' '.join(parts[1:])
        return sdql,english

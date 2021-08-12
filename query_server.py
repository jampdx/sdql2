"""
query a running server via python's urllib
use try/except to keep up with possible changing ports.
"""

import urllib,urllib2, urlparse
import httplib  # for error when port is switched during a request.
import socket
import time

from S2.directory import PORTS

def query(sport,timeout=60,**kwargs):
    #print "timeout:",timeout
    page = "%s/%s"%(sport.lower(), kwargs.get("page","query"))
    kwargs['timeout'] = str(timeout)
    kwargs['show_metacode'] = '0'
    server = kwargs.get('server','localhost')
    qs = '&'.join(["%s=%s"%(urllib.quote_plus(str(k)),urllib.quote_plus(str(v))) for (k,v) in kwargs.items()])
    flip = 0
    try:
        url = urlparse.urlunparse([ 'http','%s:%d'%(server,PORTS[0],),page, '',qs, ''])
        #print "s2.qs.url:",url
        content = urllib2.urlopen(url,timeout=timeout).read()
    except urllib2.URLError,e:      # no one home on this port
        print "url error",e,"try other port"
        #if e.code == 408:
        #    print "timed out return error message"
        #    return  "%s"%e
        flip = 1
    except httplib.BadStatusLine,e: # port switched during transaction
        print "bad status error"  ,e
        flip = 1
    except socket.timeout,e:
            return "%s"%e
    if flip:
        PORTS.reverse()
        print "switch to port",PORTS[0]
        url = urlparse.urlunparse([ 'http','%s:%d'%(server,PORTS[0],),page, '',qs, ''])
        try:
            content = urllib2.urlopen(url,timeout=timeout).read()
        except Exception,e:
            #print "can't find a port - sleep for two minutes and continue"
            #time.sleep(120)
            return "%s"%e

    return content

# for AI work
def dump_nba():
    metric = "points+line>o:points"
    metric_name = 'ats'
    cond = '2010<=season<=2016 and %s'%metric.replace('>','!=')
    params = "line,total,rest,p:rest,p:biggest lead,pp:biggest lead,p:assists,p:three pointers made,pp:assists,pp:three pointers made,p:line,p:total,pp:line,pp:total,p:dps,p:dpa,pp:dps,pp:dpa,o:rest,op:rest,op:line,op:total,op:biggest lead,opp:biggest lead,op:assists,op:three pointers made,opp:assists,opp:three pointers made,opp:line,opp:total,op:dps,op:dpa,opp:dps,opp:dpa".split(",")
    sdql = '%s@%s and None not in [%s]'%(select,cond,select)
    print "sdql:",sdql
    res = query(sport='nba',sdql=sdql, output='csv',context='raw',result_only=1,client='KS')
    open('/tmp/nba_6x_atsr_2010-2016_H.csv','w').write(res)

def dump_nfl():
    cond = '2010<=season<=2016 and None not in [line,total]'
    select = "line,total,points,o:points"
    sdql = '%s@%s'%(select,cond)
    print "nfl dump for",sdql
    res = query(sport='nfl',sdql=sdql, output='csv',context='raw',result_only=1,client='KS')
    res = res.replace('xxx',"'")
    open('/tmp/nfl_ltpop_2016.csv','w').write(res)

def dump_spread_sports():
    metric = "points+o:points>total"
    metric_name = 'ou'
    cond = '2010<=season<=2016 and H and %s'%metric.replace('>','!=')
    params = "line,total,p:line,p:total,op:line,op:total,p:dps,p:dpa,op:dps,op:dpa,pp:line,pp:total,opp:line,opp:total,pp:dps,pp:dpa,opp:dps,opp:dpa".split(',')
    for sport in ['NBA','NFL','NCAAFB','NCAABB','WNBA','CFL']:
        for p in [2,6,10,18]:
            select = ",".join(params[:p]+[metric])
            sdql = "%s@%s and None not in [%s]"%(
                            select,cond,select)
            print "sdql:",sdql
            res = query(sport=sport,sdql=sdql, output='csv',context='raw',result_only=1,client='KS',show_metacode=1)
            open('/tmp/qs1217_%s_%sp_%sr_2010-2016_H.csv'%(sport,p,metric_name),'w').write(res)

def dump_bb():
    metric = "points+line>o:points"
    metric_name = 'ats'
    cond = '2010<=season<=2016 and %s and H'%metric.replace('>','!=')
    params = "p:dps,p:dpa,op:dps,op:dpa, pp:dps,pp:dpa,opp:dps,opp:dpa, p3:dps,p3:dpa,op3:dps,op3:dpa, p4:dps,p4:dpa,op4:dps,op4:dpa".split(',')
    for sport in ['NBA','NCAABB','WNBA']:
        for p in [4,8,16,20]:
            select = ",".join(params[:p]+[metric])
            sdql = "%s@%s and None not in [%s]"%(
                            select,cond,select)
            print "sdql:",sdql
            res = query(sport=sport,sdql=sdql, output='csv',context='raw',result_only=1,client='KS',show_metacode=1)
            open('/tmp/bb1217_%s_%sp_%sr_2010-2016.csv'%(sport,p,metric_name),'w').write(res)

if __name__ == "__main__":
    dump_bb()
    #dump_spread_sports()
    #dump_nfl()

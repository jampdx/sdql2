"""
Runs from crontab every few minutes
rsync's freshess stamps and if the local one is updated (and not too recent of the last restart):
   sync and restart
"""
import argparse,os,time

MIN_RESTART_INTERVAL = 1200 # seconds


SPORTS = ["MLB","NFL","NBA","NHL","CFL","NCAAFB","NCAABB"]

TRENDS = [] # run these with each database update sports::client::trend_set

for s in SPORTS:
    TRENDS.append("%s::KSC::*"%(s,))
    TRENDS.append("%s::SDB::*"%(s,))

TOP_DIR = "/home/jameyer/S2"


def float_from_file(f):
    if not os.path.isfile(f):return 0
    return float(open(f).read().strip())

def run_trends_if_fresh(args):
    if not args.sport: sports = SPORTS
    else: sports = [args.sport]
    if not args.trend or args.trend is True: trends = TRENDS
    else: trends = [args.trend]
    if args.user: sudo = ''
    else: sudo =  "sudo -u www-data"     # running as root

    new_trends = []
    fresh_sports = []
    stale_sports = []
    for sport,client,trend_set in map(lambda x:x.split('::'),trends):
        if sport not in sports: continue
        f_query =   os.path.join(TOP_DIR,'Log','%s_query.start_time'%sport.lower()) # the timestamp of the query server start
        f_trend =   os.path.join(TOP_DIR,'Log','%s_trend_query.start_time'%sport.lower()) # the timestamp of the query server start
        if sport in stale_sports:
            print "no update for", sport, client, trend_set
            continue
        if sport not in fresh_sports:
            old_start_time = 0
            if os.path.isfile(f_trend):
                old_start_time = float_from_file(f_trend)
            print "old start time:",old_start_time
            if old_start_time + MIN_RESTART_INTERVAL > time.time():
                print "let's not restart too quick"
                continue

            c = "rsync -a "# local
            c += f_query
            c += ' '
            c += f_trend
            print "get start_time with:",c
            os.system(c)
            new_start_time = float_from_file(f_trend)
            if new_start_time <= old_start_time:
                print "nothing to refresh for",sport
                stale_sports.append(sport)
                continue
            print "run trends for",sport,client,trend_set
            c = "%s python /home/jameyer/S2/Source/run_trends.py sport=%s client=%s trend_set=%s restart > /dev/null 2>&1&"%(sudo,
                sport,client,trend_set)
            print "run with command:",c
            os.system(c)
            #os.system('sudo -u root')

def move_data_if_fresh(args):
    if not args.sport: sports = SPORTS
    else: sports = [args.sport]
    new_sports = []
    for sport in sports:
        f =   os.path.join(TOP_DIR,'Log','%s_query.start_time'%sport.lower())
        old_start_time = 0
        if os.path.isfile(f):
            old_start_time = float_from_file(f)
        print "old start time:",old_start_time

        if old_start_time + MIN_RESTART_INTERVAL > time.time():
            print "let's not restart too quick"
            continue

        c = "rsync -a %s:"%MASTER
        c += f
        c += ' '
        c += f
        print "get start_time with:",c
        os.system(c)
        new_start_time = float_from_file(f)
        if new_start_time <= old_start_time:
            print "nothing to refresh for",sport
            continue
        print "sync all data files and set restart flag. Trends and other downstream friends set data_start_time on start up and decide when to refresh."
        c = "python %s -d --d_column -s=%s -g=%s"%(os.path.join(TOP_DIR,"sync.py"), sport, MASTER)
        print "getting S2 data with",c
        os.system(c)
        c = "python %s --client=%s -g=%s"%(os.path.join(TOP_DIR,"sync.py"), 'SDB', MASTER)
        print "getting SDB data with",c
        os.system(c)
        print "Transfered files.  Set restart flag for",sport
        r = os.path.join(TOP_DIR,"Log","%s_query.restart"%sport.lower())
        open(r,'w').write(time.ctime())
        os.system("chown www-data %s; chgrp www-data %s"%(r,r))

if __name__ == "__main__":
    MASTER = "sportsdatabase.com"

    parser = argparse.ArgumentParser(description="Slave S2 data.")
    parser.add_argument("-s","--sport", help="Thes port to sync.  Don't specify for all.")
    parser.add_argument("-g","--get", help="The machine from which to get the data.")
    parser.add_argument("-t","--trend", help="Run trends if data are fresh.",action="store_true")
    parser.add_argument("-u","--user", help="Set to anything if not called from root .",action="store_true")

    args = parser.parse_args()
    if not args.get and not args.trend:
        raise Exception("need to specify --get=data_master.com or --trend")

    if args.get:
        MASTER = args.get
        move_data_if_fresh(args)
    if args.trend:
        run_trends_if_fresh(args)

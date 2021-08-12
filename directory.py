import platform
import os
import re
import sys
import time
import glob
import PyQL.py_tools

PORTS = range(8201,8203)

STOP_PAGE = "iLoA4LcTiOb"

SUPER_USERS = ["KS","SDB","efm","jam","shess"] # these can update SDB lines and clients are prevented from taking these usernames

UPLOAD_CSV_USERS = ["jam","efm","orhane",'SDB.ogn','SDB.sean']

# one or two word team name, requires full Team:Player:Prefix:parameter format
TEAM_PLAYER_PAT = re.compile("(?:^|[^:])([A-Z][a-z]+(?: [A-Z][a-z]+)?:[^:]+):[a-zA-Z0-9]+:")
GUEST_TIMEOUT = 15; CLIENT_TIMEOUT = 15

SERVICE_PORTS = {
         "mlb_query":[7090,7091],
         "mlb_trends":[8090,8091],
         "nfl_query":[7010,7011],
         "nfl_trends":[8010,8011],
         "cfl_query":[7210,7211],
         "cfl_trends":[8210,8211],
         "nba_query":[7050,7051],
         "nba_trends":[8050,8051],
         "wnba_query":[7250,7251],
         "wnba_trends":[8250,8251],
         "nhl_query":[7060,7061],
         "nhl_trends":[8060,8061],
         "ncaafb_query":[7110,7111],
         "ncaafb_trends":[8110,8111],
         "ncaabb_query":[7150,7151],
         "ncaabb_trends":[8150,8151]
         }

#SERVICE_PORTS = { "ncaafb_query":[7110,7111] } #handy for testing
SOURCE_DIR = os.path.dirname(os.path.realpath( __file__ ) )
TOP_DIR = os.path.dirname(SOURCE_DIR)
TEMPLATE_DIR = os.path.join(TOP_DIR,"TT")
TPY_DIR = os.path.join(TOP_DIR,"Tpy")
LOG_DIR = os.path.join(TOP_DIR,"Log")
CLIENT_DIR = os.path.join(TOP_DIR,"Client")
SESSIONS_DIR = os.path.join(TOP_DIR,"Sessions")
CLIENT_IMAGE_DIR = os.path.join(TOP_DIR,"public_html","Images","Client")
WEB_IMAGE_DIR = '/static/Images/Client'

N_FORKS = {} # "mlb_query":4,"nfl_query":4}

def data_dir(sport):
    return os.path.join(TOP_DIR,sport.upper(),"Data")
DATA_DIR = data_dir

def RESTART(sport,flavor="query"):
    open(os.path.join(LOG_DIR,"%s_%s.restart"%(sport.lower(),flavor)),'w').write(time.ctime())

def load_translators():
    td = {}
    files = glob.glob(os.path.join(TOP_DIR,"Client",'*','*','Source','*_translator.py'))
    files.sort()
    for f in files:
        #print "dir.load trans.f:",f
        parts = f.split(os.path.sep)
        sport = parts[-3]
        client = parts[-4]
        # first there was one translator called KS_NFL_translator.py
        #  then I needed KS_NFL_rushing_translator.py
        #    thus 'default' is defined as below.
        name_parts = parts[-1][:-3].split('_')
        if len(name_parts) == 3: name = "default"
        elif len(name_parts) == 4: name = name_parts[2]
        else: raise Exception("Unknown trend translator file name format")

        td.setdefault(client,{}).setdefault(sport,{})[name] = PyQL.py_tools.importer(f,refresh=1).pat_sub_pairs
    return td
CLIENT_TRANSLATORS = load_translators() # {"KS":{NFL:trans,NBA:trans...},{TH:{..}...}
#print "S2.dir reloaded trans",CLIENT_TRANSLATORS["KS"]["MLB"].keys()
# if a sport doesn't have a custom translator for SDB client then assign the generic one.
f = os.path.join(SOURCE_DIR,'trend_translator.py')
sdb_translator = PyQL.py_tools.importer(f).pat_sub_pairs
for service in SERVICE_PORTS:
    sport,flavor = service.split('_',1)
    if flavor == 'query':
        CLIENT_TRANSLATORS.setdefault("SDB",{}).setdefault(sport.upper(),{}).setdefault("default",sdb_translator)
        CLIENT_TRANSLATORS.setdefault("KS",{}).setdefault(sport.upper(),{}).setdefault("default",sdb_translator)
CLIENT_TRANSLATORS['KS']['NFL']['default'] = sdb_translator # force new paradigm
#print "dirtecoprfrt.CT.mlb:",CLIENT_TRANSLATORS['KS']['MLB']['default']
#print "dirtecoprfrt.CT:.nfl",CLIENT_TRANSLATORS['KS']['NFL']['default']
#raise

def data_columns(client,sport):
    return map(lambda x:os.path.split(x)[-1][:-4],
               glob.glob(os.path.join(CLIENT_DIR,client,sport.upper(),"Data","_Column","*.pkl")))



if __name__ == "__main__":
    print data_columns("jam","nfl")

#!/usr/bin/env python
  
"""
Run from the command line for a stand-alone server or use factory_app on a reloading server
"""

# XXX when running as a factroy_app the database is loaded twice!
from wsgiref.simple_server import make_server
import sys,cgi,os,urlparse

import PyQL.tpy_tools
import PyQL.py_tools

from S2.loader import sdb  
import S2.query # needed to be preloaded here
from S2.directory import TOP_DIR, TPY_DIR

# check for running server needs the PORT
PORT = 7002
# data update methods need to trip the restart filename
RESTART_FILENAME = os.path.join(TOP_DIR,"Data","Active","db.tab")

def page(environ,start_response):
    # XXX only server from local (and trusted) hosts
    status = '200 OK'
    output = ''
    path_info = environ.get('PATH_INFO',"/")
    if path_info and path_info[0]=='/': path_info = path_info[1:]    
    sport_page = path_info.split('/')
    #print "sp:",sport_page
    if len(sport_page) > 1:
        sport = sport_page[0]
        tpy_page = sport_page[1]
    else:
        tpy_page = sport_page[0]
        sport = None

    #output += "<p>os.environ['remote_user']=%s<BR>"%(os.environ.get('REMOTE_USER') ,)

    if tpy_page == '': tpy_page = "home"
    if tpy_page[-4:] != ".tpy": tpy_page += ".tpy"

    webvars = urlparse.parse_qs(environ.get("QUERY_STRING",""))

    for k in webvars:
        if len(webvars[k]) == 1: webvars[k] = webvars[k][0]
        #output += "wv[%s] = %s<BR>"%(k,webvars[k])
          
    webvar = PyQL.py_tools.guess_types(webvars)
    if sport: webvars["sport"] = sport
    #print "Loading %s from %s" % (tpy_page, TPY_DIR)
    output += "%s"%PyQL.tpy_tools.build_page( os.path.join(TPY_DIR,'top.tpy') , webvars) 
    output += "%s"%PyQL.tpy_tools.build_page( os.path.join(TPY_DIR,tpy_page) , webvars)
    output += "%s"%PyQL.tpy_tools.build_page( os.path.join(TPY_DIR,'bottom.tpy') , webvars)     

    response_headers = [('Content-type', 'text/html'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]


# for paste.deploy-based reloading wsgi server
def app_factory(global_config, **local_conf):
    return page

if __name__ == "__main__":
    import string
    stand_alone = 1
    port = PORT
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
    if stand_alone:
        httpd = make_server('', port, page)
        print "Serving HTTP on port",port
        httpd.serve_forever()
    else:
        ncaafb_ini = "# dumped by start.py\n\n[app:main]\n\npaste.app_factory = S2.start:app_factory\n"
        open("sdb.ini",'w').write(ncaafb_ini)
        print "start.py is starting reloading_wsgi_server on port",port,"\nwith restart filename:",RESTART_FILENAME
        os.system("python reloading_wsgi_server.py sdb.ini -p %s -c %s"%(port,RESTART_FILENAME))


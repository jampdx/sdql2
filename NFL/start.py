#!/usr/bin/env python

"""
Run from the command line for a stand-alone server or use factory_app on a reloading server
"""


import sys,cgi,os
import PyQL.tpy_tools
import PyQL.py_tools
import urlparse

from wsgiref.simple_server import make_server

from NFL.directory import TOP_DIR, TPY_DIR, TOP_TPY_DIR, PORT, RESTART_FILENAME, LOG_FILENAME, ERROR_FILENAME


# check for running server needs the PORT
# data update methods need to trip the restart filename
RESTART_FILENAME = os.path.join(TOP_DIR,"Log","restart.flag")

def page(environ,start_response):
    # XXX only server from local (and trusted) hosts
    status = '200 OK'
    output = ''
    tpy_page = environ.get('PATH_INFO',"/")
    if tpy_page and tpy_page[0]=='/': tpy_page = tpy_page[1:]
    #output += "<p>os.environ['remote_user']=%s<BR>"%(os.environ.get('REMOTE_USER') ,)

    if tpy_page == '': tpy_page = "query"
    if tpy_page[-4:] != ".tpy": tpy_page += ".tpy"

    webvars = urlparse.parse_qs(environ.get("QUERY_STRING",""))

    for k in webvars:
        if len(webvars[k]) == 1: webvars[k] = webvars[k][0]
        #output += "wv[%s] = %s<BR>"%(k,webvars[k])
        
    webvar = PyQL.py_tools.guess_types(webvars)
    if 'sleep' in webvars:  # for non-blocking test
        import time
        time.sleep(webvars['sleep'])
    print "Loading %s from %s" % (tpy_page, TPY_DIR)
    output += "%s"%PyQL.tpy_tools.build_page( os.path.join(TPY_DIR,tpy_page) , webvars)

    response_headers = [('Content-type', 'text/html'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]


# for paste.deploy-based reloading wsgi server
def app_factory(global_config, **local_conf):
    from NFL.loader import nfl
    import NFL.query # needed to be preloaded here
    import NFL.tables # needed to be preloaded here    
    
    return page

if __name__ == "__main__":
    
    import string
    stand_alone = 0
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
        from NFL.loader import nfl
        import NFL.query # needed to be preloaded here
        import NFL.tables # needed to be preloaded here
        
        httpd = make_server('', port, page)
        print "Serving HTTP on port",port
        httpd.serve_forever()
    else:
        nfl_ini = "# dumped by start.py\n\n[app:main]\n\npaste.app_factory = NFL.start:app_factory\n"
        open("nfl.ini",'w').write(nfl_ini)
        print "start.py is starting reloading_wsgi_server on port",port,"\nwith restart filename:",RESTART_FILENAME
        #os.system("python reloading_wsgi_server.py nfl.ini -p %s -c %s>%s&"%(port,RESTART_FILENAME,LOG_FILENAME))
        os.system("python reloading_wsgi_server.py nfl.ini -p %s -c %s 1> %s 2>%s &"%(port,RESTART_FILENAME,LOG_FILENAME,ERROR_FILENAME))

#!/usr/bin/env python

"""
Run from the command line for a stand-alone server or use factory_app on a reloading server
"""

import  NCAAFB.ncaafb_loader 
import NCAAFB.query
import os
ncaafb = NCAAFB.ncaafb_loader.ncaafb    
 
import socket

if __name__ != "__main__":
    TOP_DIR = os.path.dirname(os.path.realpath( __file__ ) )
else: TOP_DIR = "/home/jameyer/S2/NCAAFB/Source"

TPY_DIR = os.path.join(os.path.dirname(TOP_DIR),"Tpy")

import wsgiref
import sys,cgi,os
import PyQL.tpy_tools
import PyQL.py_tools
import urlparse
import urllib


from wsgiref.simple_server import make_server

PORT = 7101
RESTART_FILENAME = "/home/jameyer/S2/NCAAFB/Log/restart.flag"


# TODO
#   Separate data server from web server
#   AUTH
#   move head.html and foot.html to tpy
#   other flavors of respose headers: json, xml

def page(environ,start_response):
    # XXX only server from local (and trusted) hosts
    output = ''
    status = '200 OK'
    webvars = urlparse.parse_qs(environ.get("QUERY_STRING",""))
    for k in webvars:
        if len(webvars[k]) == 1: webvars[k] = webvars[k][0]
    webvar = PyQL.py_tools.guess_types(webvars)
    if 'sleep' in webvars:
        import time
        time.sleep(webvars['sleep'])
    page = webvars.get("TPY_PAGE",environ.get('PATH_INFO',"/"))
    if page == '/': page = "/query"
    if page[-4:] != ".tpy": page += ".tpy"
    # XXX it is not possible that os.path.join doesn't work here!
    #page = os.path.join(TOP_DIR,"NCAAFB/Tpy",page)
    page = TPY_DIR + page
    
    #output += open(TOP_DIR + "../HTML/head.html").read()    
    output += "%s"%(PyQL.tpy_tools.build_page(page,webvars),)
    #output += open(TOP_DIR + "../HTML/foot.html").read()        
    #output += "Hi"

    response_headers = [('Content-type', 'text/html'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]



# pass through for paste.deploy-based reloading wsgi server
def app_factory(global_config, **local_conf):
    return page


if __name__ == "__main__":
    import string
    stand_alone = 0
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
      print "deploy.py is starting reloading_wsgi_server on port",PORT,"\nwith restart filename:",RESTART_FILENAME
      os.system("python reloading_wsgi_server.py ncaafb.ini -p %s -c %s"%(PORT,RESTART_FILENAME))
  

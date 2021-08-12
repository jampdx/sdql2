#!/usr/bin/env python

import sys,os,cgi,urllib

#    for S1 style cgi_script
sys.path[:0] = ["/home/jameyer/Sports/Source"]
import sdb
import S2.sdb

from S2.top import TOP_DIR 
from NCAAFB.start import PORT
import PyQL.py_tools
import PyQL.tpy_tools

# called for apache AddHandler cgi_script 
def cgi_script(webvars={}):
    #webvars = PyQL.py_tools.guess_types(webvars)
    #webvars['su']=0
    #return  "Content-type: text/html\n\n%s"%(webvars,)
    return sdb.cgi_script(webvars,tpy_dir="/home/jameyer/S2/NCAAFB/Tpy",port=PORT)

# use wsgi to get required environ variable
def application_simple(environ,start_response):
    status = '200 OK'
    wv = {}
    wv["REMOTE_USER"] = environ.get("REMOTE_USER","guest")
    wv["__next_page__"] = os.environ.get('PATH_INFO',"home")    
    output += "<table>"
    keys = environ.keys()
    keys.sort()
    for key in keys:
        output += "<tr><td>%s</td><td> %s</td></tr>"%(key,cgi.escape(str(environ[key])))
    output += "</table>"
    response_headers = [('Content-type', 'text/html'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]

# call a local wsgi server for content
def application_wsgi_server(environ,start_response):
    status = '200 OK'
    qs = environ.get("QUERY_STRING","?")
    wv = {} # collect special web vars to pass through
    wv["REMOTE_USER"] = environ.get("REMOTE_USER","guest")
    wv["TPY_PAGE"] = environ.get('PATH_INFO',"home")    
    qs += '&%s'%urllib.urlencode(wv)
    
    output = ""
    url = "http://localhost:7012?%s"%(qs,)
    output += urllib.urlopen(url).read()
    response_headers = [('Content-type', 'text/html'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]

# call a local wsgi server for content
def application_joe_server(environ,start_response):
    status = '200 OK'
    wv = {} # collect special web vars to pass through
    
    wv["QUERY_STRING"] = environ.get("QUERY_STRING","?")
    wv["REMOTE_USER"] = environ.get("REMOTE_USER","guest")
    wv["TPY_PAGE"] = environ.get('PATH_INFO',"home")    
    output = "PATH_INFO: "+environ.get('PATH_INFO',"None")  
    output += S2.sdb.build_tpy(wv,tpy_dir="/home/jameyer/S2/NCAAFB/Tpy",port=PORT)
    response_headers = [('Content-type', 'text/html'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]
                

application = application_wsgi_server
     
if __name__=="__main__":
    print cgi_script()

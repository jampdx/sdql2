#!/usr/bin/env python

import sys,os,cgi,urllib

from NCAAFB.start import PORT
from NCAAFB.directory import TPY_DIR, TOP_TPY_DIR
import PyQL.py_tools
import PyQL.tpy_tools
from urllib import quote

def data_url(environ):
    url = "http://localhost:%d"%(PORT,)
    #url += quote(environ.get('SCRIPT_NAME', ''))
    url += quote(environ.get('PATH_INFO', ''))
    qs = environ.get('QUERY_STRING')
    if qs:
        qs = qs.replace('__client',"NOTALLOWED") + '&'
    qs += "__client_name=%s"%environ.get("REMOTE_USER","guest")    
    url += '?' + qs
    return url

# grab needed info from environ and then call a local wsgi server for content
def application(environ,start_response):
    output = ''    
    status = '200 OK'
    
    #keys = environ.keys()
    #keys.sort()
    #for key in keys:
    #    output += "%s: %s<BR>"%(key,environ[key]) 

    url = data_url(environ)
    #output += "data_url: %s<p>"%url
    
    output += "%s"%PyQL.tpy_tools.build_page( os.path.join(TOP_TPY_DIR,'top.tpy') , environ) 
    output += urllib.urlopen(url).read()
    output += "%s"%PyQL.tpy_tools.build_page( os.path.join(TOP_TPY_DIR,'bottom.tpy') , environ)
    
    response_headers = [('Content-type', 'text/html'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    
    return [output]

     

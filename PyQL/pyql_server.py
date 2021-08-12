#!/usr/bin/env python

import sys,cgi,os
import tpy_tools
import py_tools
import inputs
import urlparse

from wsgiref.simple_server import make_server

TOP_DIR = os.path.dirname(os.path.realpath( __file__ ) )

TPY_DIR = os.path.join(os.path.dirname(TOP_DIR),"Tpy")

PORT = 7101

def page(environ,start_response):
    # XXX only server from local (and trusted) hosts
    output = ''

    tpy_page = environ.get('PATH_INFO',"/")

    if tpy_page and tpy_page[0]=='/': tpy_page = tpy_page[1:]
    #keys = environ.keys()
    #keys.sort()
    #for key in keys:
        #output += "DS.%s: %s<BR>"%(key,environ[key])
    #output += "<p>os.environ['remote_user']=%s<BR>"%(os.environ.get('REMOTE_USER') ,)

    if tpy_page == '': tpy_page = "query"
    if tpy_page[-4:] != ".tpy": tpy_page += ".tpy"

    status = '200 OK'
    webvars = urlparse.parse_qs(environ.get("QUERY_STRING",""))

    for k in webvars:
        if len(webvars[k]) == 1: webvars[k] = webvars[k][0]
        #output += "wv[%s] = %s<BR>"%(k,webvars[k])

    webvar = py_tools.guess_types(webvars)
    if 'sleep' in webvars:  # for non-blocking test
        import time
        time.sleep(webvars['sleep'])
    webvars['dt'] = data_table
    output += "%s"%tpy_tools.build_page( os.path.join(TPY_DIR,tpy_page) , webvars)

    response_headers = [('Content-type', 'text/html'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]



if __name__ == "__main__":

    import string
    port = PORT
    datafile = "/home/jameyer/PyQL2/Data/health.tab"
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
    data_table = inputs.dt_from_file(datafile)
    httpd = make_server('', port, page)
    print "Serving HTTP on port",port
    httpd.serve_forever()

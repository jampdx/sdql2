#!/usr/bin/env python
import os,cgi
import PyQL.py_tools, PyQL.tpy_tools
import sys
import urllib
import urllib2
import urlparse
import base64
import Cookie
import cPickle

from S2.directory import TPY_DIR, SESSIONS_DIR

NHL_TPY_DIR = "/home/jameyer/S2/NHL/Tpy"; NHL_PORT = 20060
#from NHL.directory import TPY_DIR as NHL_TPY_DIR
from NCAAFB.directory import TPY_DIR as NCAAFB_TPY_DIR
from NCAAFB.directory import PORT as NCAAFB_PORT
from NCAABB.directory import TPY_DIR as NCAABB_TPY_DIR
from NCAABB.directory import PORT as NCAABB_PORT
from NFL.directory import TPY_DIR as NFL_TPY_DIR
from NFL.directory import PORT as NFL_PORT
from MLB.directory import TPY_DIR as MLB_TPY_DIR
from MLB.directory import PORT as MLB_PORT
from MLB.directory import TREND_PORT as MLB_TREND_PORT
from NBA.directory import TPY_DIR as NBA_TPY_DIR
from NBA.directory import PORT as NBA_PORT


PORTS = {"ncaafb":NCAAFB_PORT,
         "ncaabb":NCAABB_PORT,
         "nfl":NFL_PORT,
         "mlb":MLB_PORT, "mlb.trend":MLB_TREND_PORT,
         "nba":NBA_PORT,
         "nhl":NHL_PORT,
         'sdb':None,'':None}

TPY_DIRS = {"ncaafb":NCAAFB_TPY_DIR,
            "ncaabb":NCAABB_TPY_DIR,
            "nfl":NFL_TPY_DIR,
            "mlb":MLB_TPY_DIR,
            "nba":NBA_TPY_DIR,
            "nhl":NHL_TPY_DIR,
            'sdb':TPY_DIR,'':TPY_DIR}



def get_session(session_id):
    """Look up the given session_id in the database

    Return the session object, or a new empty object
    """
    session_file = os.path.join(SESSIONS_DIR, session_id)
    try:
        session = cPickle.load(open(session_file, 'r'))
    except IOError:
        session = {'id': session_id}
    return session

def set_session(session_d):
    """save the value of the session to the database."""

    # don't write unused sessions to the filesystem
    #if session_d.keys() == ['id']:
    #    return

    session_id = session_d['id']
    session_file = os.path.join(SESSIONS_DIR, session_id)
    cPickle.dump(session_d, open(session_file, 'w'))

# get environ info
def application(environ,start_response):
    status = '200 OK'
    script = os.path.basename(environ["SCRIPT_NAME"])
    # probably want to pass along a message if an unknown script is called

    webvars = {}  # the dict to send to tpy-land
    tpy_file = environ.get("PATH_INFO") or "home"
    if tpy_file[0] == "/": tpy_file = tpy_file[1:]
    script_server = script # look on trend server for tpy file that start with `trend`
    if tpy_file[:5] == "trend":
        script_server += ".trend"
    port = PORTS.get(script_server,'')
    tpy_dir = TPY_DIRS.get(script,'')
    webvars["NEXT_PAGE"] = os.path.join(tpy_dir,tpy_file)
    webvars["SERVER_NAME"] = environ["SERVER_NAME"]

    # need to inform conent_type and possible web vars based on optional script extentions.
    parts = tpy_file.split('.')
    if len(parts)>1 and parts[-1] == "json":  content_type = "text/javascript"
    else: content_type = "text/html"

    user = environ.get("REMOTE_USER","guest")

    if user == "guest":
        os.nice(19)
        timeout = 900
    else:
        timeout = 900


    # get a session id, either loaded from a cookie or a new one
    session_cookie = Cookie.SimpleCookie(environ.get('HTTP_COOKIE'))
    if session_cookie.get('session_id'):
        session_id = session_cookie['session_id'].value
    else:
        session_id = base64.urlsafe_b64encode(os.urandom(30))

    top = bottom = ''
    if content_type == "text/html":
        top = PyQL.tpy_tools.build_page(os.path.join(TPY_DIR,"top.tpy") ,webvars)
        bottom = PyQL.tpy_tools.build_page(os.path.join(TPY_DIR,"bottom.tpy")  ,webvars)

    if not port:
        webvars["session_id"] = session_id
        content = PyQL.tpy_tools.build_page(webvars["NEXT_PAGE"],webvars)
    else:
        qs = environ.get('QUERY_STRING', '')
        qd = urlparse.parse_qs(qs)
        qd['session_id'] = [session_id]
        qs = '&'.join(["%s=%s"%(urllib.quote_plus(k),urllib.quote_plus(v[0])) for (k,v) in qd.items()])
        url = urlparse.urlunparse([ 'http',
                                  'localhost:%d'%port,
                                  environ.get('PATH_INFO',''),
                                   '',
                                  qs,
                                  ''])
        try:
            content = urllib2.urlopen(url,timeout=timeout).read()
        except urllib2.URLError, e:
            content = "Your request to %s had and error: %s"%(url,cgi.escape("%s"%e))
        except:
            content = "An error occured."

    ret = top + content + bottom
    #ret = "%s"%environ + ret
    response_headers = [('Content-type', content_type),
                        ('Content-Length', str(len(ret))),
                        ('Set-Cookie', 'session_id=%s'%session_id)]
    start_response(status, response_headers)
    return [ret]

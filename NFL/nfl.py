#!/usr/bin/env python

import sys,os

sys.path[:0] = ["/home/jameyer/Sports/Source"]
import sdb
sys.path[:0] = ["/home/jameyer/S2/NFL/Source"]
from start import PORT
import PyQL.py_tools

def cgi_script(webvars={}):
    #webvars = PyQL.py_tools.guess_types(webvars)
    #webvars['su']=0
    return sdb.cgi_script(webvars,tpy_dir="/home/jameyer/S2/NFL/Tpy",port=PORT)
     
if __name__=="__main__":
    print cgi_script()

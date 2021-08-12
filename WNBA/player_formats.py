import PyQL.outputs
import urllib,cgi

import NBA.player_formats

class Query_Records(NBA.player_formats.Query_Records):
    def __init__(self,headers,**kwargs):
        kwargs.setdefault("show ats",1)
        kwargs.setdefault("show ou",1)
        #kwargs["level"] = "ncaa"
        NBA.player_formats.Query_Records.__init__(self,headers,**kwargs)

class Query_Summary(NBA.player_formats.Query_Summary):
    def __init__(self,headers,**kwargs):
        kwargs.setdefault("show ats",1)
        kwargs.setdefault("show ou",1)
        #kwargs["level"] = "ncaa"
        NBA.player_formats.Query_Summary.__init__(self,headers,**kwargs)

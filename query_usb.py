
import sys,string,re,urllib

import PyQL.outputs 
import S2.loader
dbmap = S2.loader.sdb

import S2.formats
import S2.howto_query
import S2.new_features

def about_SDQL2():
    return S2.new_features.html

def getDB(kwargs):
    sport = kwargs.get("sport", "")
    return dbmap.get(sport, dbmap.values()[0])
    

def clean_parameters(**kwargs):
    sdb = getDB(kwargs)
    parameters = sdb.headers
    parameters.sort()
    p_str = str(filter(lambda x:x[0]!='_' and "." not in x,parameters))[1:-1]
    return p_str.replace("'","").replace('"','')

def examples():
    ret = S2.howto_query.html 
    return ret

def query(**kwargs):

    sdql = kwargs.get("sdql")
    if not sdql: return ''

    sdb = getDB(kwargs)
    #pick up parameters via kwargs
    
    debug = kwargs.get("debug",0)
    show_metacode = kwargs.get("show_metacode",0)
    debug_message = kwargs.get("debug_message","")
    error_message = kwargs.get("error_message","")
    client = kwargs.get("client","sdb")
    output = kwargs.get("output",None)
    indices = kwargs.get("indices",[])
    sdb.same_season_p = kwargs.get("same_season_p",0)
    sdb.same_season_P = kwargs.get("same_season_P",1)
    default_fields = kwargs.get("default_fields","_i")
    # what to return if the sdql contains no known output and a select clause.
    formatter = PyQL.outputs.html # a simple html table.

    # top level message
    debug_message += "debug is on:<p>"
    debug_message += "output: %s<p>"%output
    debug_message += "sdql: %s<p>"%sdql

    if output == "summary":
        Q = S2.formats.Query_Summary(headers=sdb.headers,**kwargs)
        debug_message += "summary output requested<p>"        
        default_fields = Q.select()
        debug_message += "default fields:%s<p>"%default_fields
        #return debug_message              
        try: res = sdb.sdb_query(sdql,default_fields=default_fields,indices=indices)
        except:  
            if debug: return "debug message:%s<p>\nerror message:%s<p><pre>\n%s\n</pre>"%(
                                                                              debug_message,error_message ,sdb.metacode)
            else: return "An error occured.  Please check your SDQL and try again."
        html = ''
        for r in res:
            html += Q.output(r, query_title=' '.join(r.name[-1]))

    elif output == "records":
        debug_message += "records output requested<p>"
        Q = S2.formats.Query_Records(headers=sdb.headers,**kwargs)
        default_fields = Q.select()
        debug_message += "default fields:%s<p>"%default_fields
        try: res = sdb.sdb_query(sdql,default_fields=default_fields,indices=indices)
        except:  
            if debug: return "debug message:%s<p>\nerror message:%s<p><pre>\n%s\n</pre>"%(debug_message,error_message ,sdb.metacode)
            else: return "An error occured.  Please check your SDQL and try again."

        html = Q.output(res)        

    else:
        debug_message += "no output flavor requeste<p>"
        # do the query and have a look
        try: res = sdb.sdb_query(sdql,default_fields=default_fields,indices=indices)
        except   AmbiguousPlayerError, s:
            error_message += "%s"%s
            res = []
            
        #return debug_message
        # if no results 
        if not res or not len(res[0]):
            html = "Your SDQL <em>%s</em> returned no results"%sdql

        # if sdql has a select clause return a simple html table
        elif len(res[0].headers)>1 or res[0].headers[0] != '_i':
            res = PyQL.outputs.auto_reduce(res,S2.formats.key_to_query_link)
            html = formatter(res) 

        # sdql had no select clause use defaults   
        else:
            if len(res) == 1: # no group by
                kwargs["output"] = "summary"
                kwargs["indices"] = res[0][0]
                kwargs["debug_message"] = debug_message
                kwargs["sdql"] = '1 as "%s"'%sdql
                # sdql=new sdql  # XXX do not pass conditions here: since incides are passed in use: fields @ 1                 
                return query(**kwargs)

            else: # group by
                kwargs["output"] = "records"
                #kwargs["indices"] = res[0][0] # extend to dt of indices?
                kwargs["debug_message"] = debug_message
                return query(**kwargs)
            
    if show_metacode: html = "<pre>%s</pre>"%sdb.metacode + html
    if debug: html = debug_message + html    
    return error_message + "<p>" + html



############# tests and demos ##############

    
if __name__ == "__main__":
    sdql = "team=ALA  and  season"
    for arg in sys.argv[1:]:
        if '=' not in arg:
            arg = arg+"=1"
        var, val = string.split(arg,'=',1)
        try:              #first ask: Is this in my name space?
            eval(var)
        except:
            print "Can't set", var
            sys.exit(-1)
        try:
            exec(arg)  #numbers
        except:
            exec('%s="%s"' % tuple(string.split(arg,'=',1))) #strings
    #open("/tmp/query.html",'w').write(query(text=text,output="summary") )
    print query(sdql=sdql,output="records")

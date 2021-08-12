import sys,string,re,urllib,cgi
import PyQL.py_tools
import PyQL.outputs
try:
    import PyQL.plotly_tools
    PLOTLY = 1
except:
    print "can't import plotly"
    PLOTLY= 0
try:
    import PyQL.matplotlib_tools
    MATPLOTLIB = 1
except:
    print "can't import matplotlib"
    MATPLOTLIB = 0

import S2.directory

import S2.formats, S2.player_formats
import S2.trends
import S2.howto_query
import S2.new_features
from S2.common_methods import clean_parameters
import S2.short_cuts
import S2.js_tools
import traceback

# needed in run_trends
PAT_COUNT = re.compile("(?P<count>[0-9]+)\strend")



def bugs():
    b = []
    b.append("can't use short cuts in square bracket queries: A(W@D and date)[D and date] fails")
    b.append("can't use None in a list: tS(W) in [0,None] fails.")
    b.append("list comprehension is not understood")
    b.append("group by rest return a key of rest=None, which is not valid SDQL")

def examples():
    ret = S2.howto_query.html
    return ret


class AmbiguousPlayerError(Exception):
    def __init__(self,name,players):
        #print "caught APE:",name,players
        self.players = players
        self.name = name

    def __str__(self):
        if not self.players:
            return "Error: the requested name `%s` returned no players"%self.name
        return "Error: the requested name `%s` returned the following players: %s"%(self.name, ', '.join(self.players))

class UnknownParameterError(Exception): # accessed for prefix:parameter format
    def __init__(self,parameter):
        self.parameter = parameter
    def __str__(self): # could add `did you mean...`
        return "Error: unknown parameter: `%s`"%self.parameter
# filter on owners, lose owner prefix and  parameters starting with an _
def available_headers(headers,owners):
    return filter(lambda x,p=re.compile('('+'|'.join(owners)+')\.'):'.' not in x or p.search(x),headers)

def parameters(sdb,owners,**kwargs):
    # show parameters want to be different from read parameters for special case.
    page = "query"
    if 'data_v' in kwargs.get('form_action',''):
        page += "_data_viz"
    show_headers = sdb.headers
    if kwargs.get('filter_show_parameters'):
        #print "filtering show parames from",show_headers
        show_headers = filter(kwargs['filter_show_parameters'],show_headers)
        #print "filtering show parames to",show_headers
    ret = "<a href=%s>Game Parameters:</a> %s<p>"%(page,S2.common_methods.clean_parameters(show_headers,owners))
    for ptn in sdb.player_table_names:
        params = sdb.player_dts[ptn].headers
        #print "filtering show p parames from",params
        if kwargs.get('filter_show_parameters'):   params = filter(kwargs['filter_show_parameters'],params)
        #print "filtering show p parames from",params
        params = S2.common_methods.clean_parameters(params,owners)
        if params:
            ret += "<a href=%s_%s>%s Parameters:</a> %s<p>"%(ptn,page,ptn.title().replace("_"," "),params)
    return ret


def input_form(**kwargs):
    #print "if:",kwargs
    font_size=kwargs.get("input_font_size","1em")
    format_options = kwargs.get('format_options','') # html inputs for run line, OU, invested, ....
    if kwargs.get('graphic_options',1):
        output = kwargs.get("output","default")
        output_select = "<select name='output'>"
        opts = [("default","Numerical")]
        if MATPLOTLIB:
            opts+=[("matplotlib.scatter","Scatter.png: x,y@c"),("matplotlib.histogram","Histogram.png: x@c"),("matplotlib.box","Box.png: x@g")]
        if PLOTLY:
            opts+=[("plotly.scatter","Scatter.js: x,y@c"),("plotly.histogram","Histogram.js: x@c"),("plotly.box","Box.js: x@g")]
        for opt in opts:
            s = " selected"*(opt[0] == output)
            output_select += "<option value='%s'%s>%s</option>"%(opt[0],s,opt[1])
        output_select += "</select>"
    else: output_select = ''
    sdql = PyQL.py_tools.force_ascii(kwargs.get('no_as_sdql',kwargs.get('sdql','')))
    return '''<div style="background-color: #F0F0F8;">          %s
                       <form action="%s">
                      %s %s<BR>
                 <input style="font-size:%s" type="text" name="%s" id="sdql" size=%s value="%s"> <BR>
                 <input type="submit" name="submit" size=60 value="  S D Q L !  ">
                      %s
                       </form></div>'''%(kwargs.get('form_message',''),
                       kwargs.get('form_action','query'),
                       output_select, format_options,
                       font_size,
                       kwargs.get('input_name','sdql'),
                       kwargs.get('input_size','120'),
                       sdql,kwargs.get('hidden',''))

def wrap_return(ret,context="html",output='null',sdql=''):
    # json needs sdql for subsequent refinement of query_matrix generated sdql
    #    and for parsing out the (sdql) as "english"
    if context == "json":
        return '{"output":"%s","html":"%s","sdql":"%s"}'%(output,ret.replace('"','\\"'),sdql.replace('"',"'"),)
    return ret

def readable(parameter,owners):
    parts = parameter.split(".")
    if len(parts) == 1 or ".".join(parts[:-1]) in owners: return True

def read_headers(sdb,owners):
    if hasattr(sdb,"games"):
        return read_headers(sdb.games,owners)
    rh = set()
    rh.update(filter(lambda x,o=owners,r=readable:r(x,o),sdb.headers))
    if hasattr(sdb,'player_dts'):
        for table in sdb.player_dts.keys():
            rh.update(filter(lambda x,o=owners,r=readable:r(x,o),sdb.player_dts[table].headers))
    if hasattr(sdb,"header_aliases"):
        rh.update( sdb.header_aliases.keys())
    return list(rh)

def query(sdb,Query_Records,Query_Summary,**kwargs):

    #print "reloading dt trn off for deploy"
    #reload(PyQL.dt)
    #print "S2.query reloading S2.direcctory for translator"
    #reload(S2.directory);    reload(S2.trends)
    #print "S2.query reloading S2.formats and player_formats"
    #reload(S2.formats);    reload(S2.player_formats);  reload(S2.common_methods)
    #print "s2.quert gets:",kwargs.get('ou')

    # return a string. format as per the specified `output` parameter
    #print "S2.query gets sdql:", kwargs.get("sdql")
    #print "S2.query gets outut:", kwargs.get("output")
    read_owners = kwargs.get('read_owners')
    #print "S2.read owners:",read_owners
    if read_owners:
        #print "S2.query setting readowners to",read_owners
        sdb.read_owners = read_owners # can this be right? how else to let dt internal offset_from_header know?
        # 20130724 rebuild lexer
        owner_prefix = "(?:(?:%s)\.)?"%'|'.join(read_owners)
        headers = read_headers(sdb,read_owners)
        lex_headers = map(lambda x:x.split('.')[-1], headers )
        lex_headers = dict.fromkeys(lex_headers).keys()  # remove duplicates
        #print "lex headers:",lex_headers
        parameters=map(lambda x,pp=sdb.parameter_prefix,op=owner_prefix: pp + op + x, lex_headers)
        sdb.build_lexer(parameters=parameters)


    sdql = kwargs.get("sdql",'') #or "Replace(team),Average(points)@team"
    #print "S2.query.sdql:",sdql
    kwargs.setdefault("no_as_sdql", sdql)
    args = PyQL.py_tools.split_not_protected(sdql,'?',1)
    if len(args)>1:
        kwargs.update(PyQL.py_tools.parse_qs(args[1]))
        sdql = kwargs['sdql'] = args[0]
    if ') as "' in sdql: # this loses ? args format
        kwargs["no_as_sdql"] = S2.trends.condense_sdql(sdql) # from trend generation
    #print "S2.query.nosassdql:",   kwargs["no_as_sdql"]
    ro =  kwargs.get('result_only')
    if (not ro and kwargs.get('show_form',1)) or kwargs.get("show_form") == 9: # silly magic for table forms
        form = kwargs.get("input_form",input_form(**kwargs)) # set this for (eg) tables in SPORT/query.py
    else: form = ''
    #if ro or not kwargs.get('show_about',1): about = ''
    #else: about = kwargs.get('about','')
    about = kwargs.get('about','')     # turn off with show_parameters=0; show_howto=0
    if not ro and kwargs.get("new_features",0): about = S2.new_features.html + "<p>" + about

    context = kwargs.get('context','html')
    #print "S2.context:",context

    if not sdql: return wrap_return(form + about,context)
    #print "s2.q.sc:",kwargs.get('short_cuts',[])
    #print "S2.query gets sdql:",sdql,'ready to expand with:',kwargs.get('short_cuts',[])
    #reload(S2.short_cuts)
    sdql = S2.short_cuts.expand(sdql,clients=kwargs.get('short_cuts',[]),sport=kwargs.get('sport','default'))
    debug = kwargs.get("debug",0)
    show_metacode = kwargs.get("show_metacode",0)
    debug_message = kwargs.get("debug_message","")
    error_message = kwargs.get("error_message","")
    # 20150415 set these in SPORT.query
    #kwargs.setdefault("line",1)
    #kwargs.setdefault("total",1)
    #kwargs.setdefault("ats",1)
    #kwargs.setdefault("ou",1)
    output = kwargs.get("output",None)
    #print "=-===================q.out",output
    indices = kwargs.get("indicies",[])
    sdb.same_season_p = kwargs.get("same_season_p",1)
    sdb.same_season_P = kwargs.get("same_season_P",0)
    sdb.read_owners = kwargs.get("read_owners",[])
    # show_headers are used in the output methods
    show_headers = available_headers(sdb.headers,sdb.read_owners)
    #print "S2.query sdb.headers:",sdb.headers
    #print "S2.query set read_ownsers:",sdb.read_owners
    #print "S2.query set show_headers:",show_headers
    default_fields = kwargs.get("default_fields","_i")
    # what to return if the sdql contains no known output and a select clause.
    formatter = PyQL.outputs.html # a simple html table.

    # top level message
    debug_message += "debug is on:<p>"
    debug_message += "output: %s<p>"%output
    debug_message += "sdql: %s<p>"%sdql
    debug_message += "kwargs: %s<p>"%kwargs

    html = ''
    #print "S2.q.outp[ut",output
    if output == "dt":
        res = sdb.sdb_query(sdql,indices=indices)
        return res
    elif output == "python":
        res = sdb.sdb_query(sdql,indices=indices).as_dict()
        return res
    elif output in ["dump_trends","dump_player_trends"]:
        debug_message += "dump_trends output requested<p>"
        if output == "dump_trends":
            Q = S2.formats.Dump_Trends(show_headers,**kwargs)
        else:
            Q = S2.player_formats.Dump_Trends(show_headers,**kwargs)
        try:
            res = sdb.sdb_query(sdql,indices=indices)
        except:
            if debug: return "debug message:%s<p><pre>\n%s\n</pre>"%(
                                          debug_message,sdb.metacode)
            else: return "An error occurred (101).  Please check your SDQL and try again."

        r = Q.output(res)
        if kwargs.get('context','')=='pkl': return r
        # this is tard-parsed by run_trends.py: edit PAT_COUNT with this
        return "%d trends were handled"%len(res)
    elif str(output).startswith("matplotlib"):
        kwargs.setdefault('dsql','sdql') # the name of the domain specific query language for drill down links
        res = sdb.sdb_query(sdql,default_fields=default_fields,indices=indices)

        if len(res[0]) > 2 and hasattr(sdb,'icon_dict'):  kwargs['icon_dict'] = sdb.icon_dict
        if kwargs.get("reduce"):
            res = res.reduced()
        #web_image_dir = kwargs.get("image_dir",S2.directory.WEB_IMAGE_DIR)  # api servers want to point the image_dir back to the server.
        web_image_dir = S2.directory.WEB_IMAGE_DIR # that seemed dangerous
        html = PyQL.matplotlib_tools.Plotter(res,S2.directory.CLIENT_IMAGE_DIR,web_image_dir,**kwargs).plot()

    elif str(output).startswith("plotly"): # plotly.scatter ...
        res = sdb.sdb_query(sdql,default_fields=default_fields,indices=indices)
        if kwargs.get("reduce"):
            res = res.reduced()
        html = PyQL.plotly_tools.Plotter(res,**kwargs).plot()

    elif output == "scatter":
        Q = S2.formats.Flot_Scatter(show_headers,**kwargs)
        debug_message += "scatter output requested<p>"
        try: res = sdb.sdb_query(sdql,indices=indices)
        except:
            if debug: return "debug message:%s<p><pre>\n%s\n</pre>"%(
                                          debug_message,sdb.metacode)
            else: return "An error occurred (101).  Please check your SDQL and try again."

        if not res or not len(res[0]):
            if not ro: html += "Your SDQL <em>%s</em> returned no results"%cgi.escape(sdql)
        else:
            for r in res:
                kwargs['query_title'] = query_title=' '.join(r.name[-1])
                html += Q.output(r,**kwargs)

    elif output == "json":
        res = sdb.sdb_query(sdql,default_fields=default_fields,indices=indices)
        if kwargs.get("reduce"):
            res = res.reduced()
        return PyQL.outputs.json(res,query_name=kwargs.get('query_name','sdql'),sigfig=kwargs.get('sigfig',3))

    elif output == "csv":
        #print "S2.query.csv relaoding oututs"
        #reload(PyQL.outputs)
        res = sdb.sdb_query(sdql,default_fields=default_fields,indices=indices)
        if kwargs.get("reduce"):
            res = res.reduced()
        else: res = res[0]
        return PyQL.outputs.csv(res,query_name=kwargs.get('query_name','sdql'),sigfig=kwargs.get('sigfig',3))


    elif output == "summary":
        Q = Query_Summary(show_headers,**kwargs)
        debug_message += "summary output requested<p>"
        default_fields = Q.select()
        debug_message += "default fields:%s<p>"%default_fields
        #return debug_message
        res = None
        try: res = sdb.sdb_query(sdql,default_fields=default_fields,indices=indices)
        except   AmbiguousPlayerError, s:
            html += "%s"%s

        #except:
        #    if debug: html += "debug message:%s<p>\nerror message:%s<p><pre>\n%s\n</pre>"%(
        #                                                                      debug_message,error_message ,sdb.metacode)

        #    else: html += "An error occurred (102).  Please check your SDQL and try again."
        if not res or not len(res[0]):
            if not ro: html += "Your SDQL <em>%s</em> returned no results"%cgi.escape(sdql)
        else:
            headers = res.headers[:]
            headers.sort()
            for h in headers:
                r = res.value_from_header(h)
                kwargs['query_title'] = query_title=' '.join(r.name[-1])
                html += Q.output(r,**kwargs)

    elif output == "records":
        debug_message += "records output requested<p>"
        Q = Query_Records(show_headers,**kwargs)
        default_fields = Q.select()
        debug_message += "default fields:%s<p>"%default_fields
        res = None
        try: res = sdb.sdb_query(sdql,default_fields=default_fields,indices=indices)
        except   AmbiguousPlayerError, s:
            html += "%s"%s
        #except:
        #    if debug: html += "debug message:%s<p>\nerror message:%s<p><pre>\n%s\n</pre>"%(debug_message,error_message ,sdb.metacode)
        #    else: html += "An error occurred (103).  Please check your SDQL and try again."
        else:
            if not res or not len(res[0]):
                if not ro: html += "Your SDQL <em>%s</em> returned no results"%cgi.escape(sdql)
            else: html += Q.output(res)

    else:
        debug_message += "no output flavor requested<p>"
        # do the query and have a look
        res = None
        #res = sdb.sdb_query(sdql,default_fields=default_fields,indices=indices)
        try: res = sdb.sdb_query(sdql,default_fields=default_fields,indices=indices)
        except   AmbiguousPlayerError, s:
            html += "%s"%s
        except   UnknownParameterError, s:
            html += "%s"%s
        except:
            #traceback.print_exc()
            if debug:
                error_message += traceback.format_exc()
                html += "debug message:%s<p>\nerror message:%s<p><pre>\n%s\n</pre>"%(debug_message,error_message ,sdb.metacode)
            else: html += "An error occurred (104).  Please check your SDQL and try again."
            #print html
            #return html
        else:
            if not res or not len(res[0]):
                if not ro: html += "Your SDQL <em>%s</em> returned no results"%cgi.escape(sdql)
            # if sdql has a select clause return a simple html table
            elif len(res[0].headers)>1 or res[0].headers[0] != '_i':
                if kwargs.get("reduce"): res = res.reduced()
                else: res = PyQL.outputs.auto_reduce(res,lambda k,k2q=S2.common_methods.key_to_query_link,kw=kwargs:k2q(k,**kw))
                html += formatter(res,show=kwargs.get('show'),sort=kwargs.get('sort'),
                                  border=kwargs.get('border',0),
                                  repeat_header_every=kwargs.get('repeat_header_every',0),
                                  column_stripe=kwargs.get('column_stripe','FFFFFF'),
                                  row_stripe=kwargs.get('row_stripe','FFFFFF'))

            # sdql had no select clause use defaults
            else:
                if len(res) == 1: # no group by
                    kwargs["output"] = "summary"
                    kwargs["indices"] = res[0][0]
                    kwargs["debug_message"] = debug_message
                    # sdql=new sdql  # XXX do not pass conditions here: since incides are passed in use: fields @ 1
                    return query(sdb,Query_Records,Query_Summary,**kwargs)

                else: # group by
                    kwargs["output"] = "records"
                    #kwargs["indices"] = res[0][0] # extend to dt of indices?
                    kwargs["debug_message"] = debug_message
                    return query(sdb,Query_Records,Query_Summary,**kwargs)
    html = form + html + about
    if show_metacode: html = "<pre>%s</pre>"%sdb.metacode + html
    if debug: html = debug_message + html
    if error_message: html =  error_message + "<p>" + html
    html = S2.js_tools.document_ready(html,**kwargs)
    return wrap_return(html,context,output=output,sdql=kwargs["no_as_sdql"])

# util for find_player
def name_pats(name):
    len_name = len(name)
    name_space = ''
    name_pat = ''
    i = -1
    for i in range(len_name):
        c = name[i]
        name_space += c
        name_pat += c
        if i+1 < len_name:
            nc = name[i+1]
        else:
            nc = None
        if nc and nc.isupper() and c.strip():
            name_space += ' '
            name_pat += '[a-z ]*'
        elif nc == ' ': name_pat += '[a-z]*' # finish up the first word with small letters
    name_pat += '[a-z ]*'
    return name_space, name_pat

def find_player(ndt,name,team):
    #print "S2.find player gets",name,team
    name_space,name_pat = name_pats(name)
    c = (team is not None)*("team='%s' and "%team)
    c += "((string.lower(name) in ['%s','%s']) as '_m1')"%(name.lower(),name_space.lower()) # exact insensitive match
    c += ",((re.match('%s',name) is not None) as '_m2')"%name                               # exact starts with
    c += ",((re.match('%s$',name) is not None) as '_m3')"%name_pat                          # allow any lowercase after word
    c += ",((re.match('%s$',name,re.I) is not None) as '_m4')"%name_pat                     # allow any anycase after word
    #c += ",((re.search('%s',name,re.I) is not None) as '_m5)"%name_pat                         # anywhere in name
    #print "fpc:",c
    q = "Unique(name)@" + c
    res = ndt.query(q)
    if not res: return []
    hs = res.headers
    hs.sort(key=lambda t:t[-1]) # sort by 'as keys'
    return res.value_from_header(hs[0])[0].data


############# tests and demos ##############

def test_find_player():
    import PyQL.columns
    import PyQL.dt

    c1 = PyQL.columns.Column(name="team")
    c2 = PyQL.columns.Column(name="name")
    ndt = PyQL.dt.DT(data=(c1,c2))
    c1.append('Bulls');c2.append('Mike McSmith')
    c1.append('Bulls');c2.append('MJ Smith')
    #print ndt
    return find_player(ndt,'MMS',None)

if __name__ == "__main__":
    #sdql = 'team=ALA as "ALABAMVA" and  season'
    #print input_form(sdql = sdql)
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
    #print query(sdql=sdql,output="records")
    print test_find_player()

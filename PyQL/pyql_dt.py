import PyQL.inputs, PyQL.outputs, PyQL.dt, PyQL.py_tools,PyQL.outputs,PyQL.columns
import traceback
import cgi
import re
import math
import datetime

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


def input_form(**kwargs):
    font_size=kwargs.get("input_font_size","1em")
    if kwargs.get('graphic_options',1):
        output = kwargs.get("output","default")
        output_select = "<select name='output'>"
        opts = [("default","DataTable")]
        if MATPLOTLIB:
            opts+=[("matplotlib.scatter","Scatter.png: x,y@c"),("matplotlib.histogram","Histogram.png: x@c"),("matplotlib.box","Box.png: x@g")]
        if PLOTLY:
            opts+=[("plotly.scatter","Scatter.js: x,y@c"),("plotly.histogram","Histogram.js: x@c"),("plotly.box","Box.js: x@g")]
        for opt in opts:
            s = " selected"*(opt[0] == output)
            output_select += "<option value='%s'%s>%s</option>"%(opt[0],s,opt[1])
        output_select += "</select>"
        #if kwargs.get('has_icons'):
        #    output_select += "%s<input type='checkbox' name='use_icons'%s>"%( kwargs['has_icons'],
        #                                                                      ' CHECKED'*(kwargs.get('use_icons') is not None),)
    else: output_select = ''
    pyql = kwargs.get('no_as_pyql',kwargs.get('pyql',''))
    return '''         %s
                       <form action="%s">
                       %s  <BR>
                 <input style="font-size:%s" type="text" name="%s" id="pyql" size=%s value="%s"> <BR>
                 <input type="submit" name="submit" size=60 value="::: P y Q L !">
                      %s
                       </form>'''%(kwargs.get('form_message',''),
                       kwargs.get('form_action','query'),
                       output_select,
                       font_size,
                       kwargs.get('input_name','pyql'),
                       kwargs.get('input_size','120'),
                       pyql,kwargs.get('hidden',''))



def wrap_return(ret,context="html",output='null',pyql=''):
    # json needs pyql for subsequent refinement of query_matrix generated pyql
    #    and for parsing out the (pyql) as "english"
    if context == "json":
        return '{"output":"%s","html":"%s","pyql":"%s"}'%(output,ret.replace('"','\\"'),pyql.replace('"',"'"),)
    return ret

def init_autocomplete(id,words):
    return """<script>
function split( val ) {
      //return val.split( /,\s*/ );
      return val.split( /([^a-zA-Z ])/ );
}
function extractLast( term ) {
      return $.trim(split( term ).pop());
}

    $( "\#%s" )
      .bind( "keydown", function( event ) {
        if ( event.keyCode === $.ui.keyCode.TAB &&
            $( this ).autocomplete( "instance" ).menu.active ) {
          event.preventDefault();
        }
      })
      .autocomplete({
      minLength: 1,
        source: function( request, response ) {
          var matcher = new RegExp( "^" + $.ui.autocomplete.escapeRegex(  extractLast(request.term )), "i" );
          response( $.grep( %s, function( item ){
          last = extractLast( item )
              return matcher.test(last);
          }) );
},


        focus: function() {
          // prevent value inserted on focus
          return false;
        },
        select: function( event, ui ) {
          var terms = split( this.value );
          // remove the current input
          terms.pop();
          // add the selected item
          terms.push( ui.item.value );
          // add placeholder to get the comma-and-space at the end
          terms.push( "" );
          //this.value = terms.join( ", " );
          this.value = terms.join('');
          return false;
        }
      });</script>
      """%(id,words)


class UnknownParameterError(Exception):
    def __init__(self,reference,parameters):
        self.reference = reference
        self.parameters = parameters
    def __str__(self):
        return """<font color='#FF0000' size=+1>Ambiguous Parameter Error:<b> `%s`</b></font>.
                  These parameters were matched: %s<BR>
                  Please add letters to uniquely identify the parameter you want.<p>
<b>Usage Hints</b><ul><li>references are case sensitive<li>if the first few letters specify a parameter uniquely, then use them<li>use the capitals of the CamelCase parameters and fill in lowercase letters for degenerates.</ul>
"""%(
                                   self.reference,self.parameters)

def reduce_key_preserve_group(k):
    return ' '.join(k[-1])

class DT(PyQL.dt.DT):
    def __init__(self,data_dir,name,alias_d={},camel_case=0,reduce_key_transform=None):
        PyQL.dt.DT.__init__(self,alias_d=alias_d)
        PyQL.inputs.append_from_pickled_columns(self,data_dir)
        print "pyql_dt has cc:",camel_case
        if camel_case == 'auto':
            if filter(lambda x:x.title()==x,self.headers):
                camel_case = 1
                print "auto chooses camel case query access"
            else:
                camel_case = 0
        print "pyql_dt has cc:",camel_case
        if camel_case:
            self.code_access_from_parameter = self.camel_case_code_access_from_parameter
            self.headers_lower = map(lambda x:x.lower(),self.headers)
            self.build_lexer(parameters=['([A-Za-z][A-Za-z0-9]*)(?!\()']) # look for parameters in all strings
        self.reduce_key_transform = reduce_key_transform

        #print "init headers:", self.headers

    def query(self,**kwargs):

        print "reloading matplotlib"
        reload(PyQL.matplotlib_tools)
        if hasattr(self,'icon_dict'): kwargs.setdefault("icon_dict",self.icon_dict)
        if hasattr(self,'watermark'): kwargs.setdefault("watermark",self.watermark)
        pyql = kwargs.get("pyql",'')
        kwargs.setdefault("no_as_pyql",pyql)
        args = PyQL.py_tools.split_not_protected(pyql,'?',1)
        if len(args)>1:
            kwargs.update(PyQL.py_tools.parse_qs(args[1]))
            pyql = kwargs['pyql'] = args[0]

        #if ') as "' in sdql: # this loses ? args format
        #    kwargs["no_as_pyql"] = S2.trends.condense_sdql(sdql) # from trend generation
        #    print "S2.query.nosassdql:",   kwargs["no_as_sdql"]

        ro =  kwargs.get('result_only')
        if (not ro and kwargs.get('show_form',1)) or kwargs.get("show_form") == 9: # silly magic for table forms
            form = kwargs.get("input_form",input_form(**kwargs)) # set this for (eg) tables in SPORT/query.py
            parameters = self.headers[:]
            parameters.sort()
            if kwargs.get('autocomplete',0):
                form += init_autocomplete(id='pyql',words=parameters)
            display_parameters = kwargs.get('display_parameters',parameters)
            about = '<p><b>Parameters:</b><BR><!--start_parameters-->%s<!--stop_parameters-->\n'%(', '.join(display_parameters),)
        else:
            form = ''
            about = ''

        context = kwargs.get('context','html')
        output = kwargs.get('output','default')

        if not pyql: return wrap_return(form + about,context)
        debug = kwargs.get("debug",0)
        show_metacode = kwargs.get("show_metacode",0)
        debug_message = kwargs.get("debug_message","")
        error_message = kwargs.get("error_message","")
        default_fields = kwargs.get("default_fields","_i")
        # what to return if the pyql contains no known output and a select clause.
        formatter = PyQL.outputs.html # a simple html table.

        # top level message
        debug_message += "debug is on:<p>"
        debug_message += "output: %s<p>"%output
        debug_message += "pyql: %s<p>"%pyql
        debug_message += "kwargs: %s<p>"%kwargs

        html = ''
        # try except this with a class.owned error. Handy for UnknownParameterError, AmbiguousPlayerError...
        try:
            res = PyQL.dt.DT.query(self,pyql)
        except UnknownParameterError as e:
            return "%s"%e
        #print "res:",res[0][0]
        #print "type:",type(res[0][0].value()),type(res[0][0].data)
        if str(output).startswith("matplotlib"):
            if kwargs.get("reduce"):
                #print "reduce resul"
                res = res.reduced()
            web_image_dir = kwargs.get("web_image_dir")
            client_image_dir = kwargs.get("client_image_dir")
            if not web_image_dir or not client_image_dir:
                raise Exception("If you want to make an image, you need to say where")
            html = PyQL.matplotlib_tools.Plotter(res,client_image_dir,web_image_dir,**kwargs).plot()

        elif str(output).startswith("plotly"): # plotly.scatter ...
            if kwargs.get("reduce"):
                res = res.reduced()
            html = PyQL.plotly_tools.Plotter(res,**kwargs).plot()

        elif output == "scatter":
            Q = S2.formats.Flot_Scatter(show_headers,**kwargs)
            debug_message += "scatter output requested<p>"

            if not res or not len(res[0]):
                html += "Your PYQL <em>%s</em> returned no results"%cgi.escape(pyql)
            else:
                for r in res:
                    kwargs['query_title'] = query_title=' '.join(r.name[-1])
                    html += Q.output(r,**kwargs)

        elif output in ["json","python"]:
            if kwargs.get("reduce"):
                res = res.reduced()
            if output == "python": return res
            return PyQL.outputs.json(res,query_name=kwargs.get('query_name','pyql'),sigfig=kwargs.get('sigfig',3))

        else:
            debug_message += "no output flavor requested<p>"
            # do the query and have a look

            if not res or not len(res[0]): html += "Your PYQL <em>%s</em> returned no results"%cgi.escape(pyql)
            elif len(res[0].headers)>1 or res[0].headers[0] != '_i':
                    if kwargs.get("reduce"): res = res.reduced()
                    else:
                        res = PyQL.outputs.auto_reduce(res,self.reduce_key_transform)
                    html += formatter(res,show=kwargs.get('show'),sort=kwargs.get('sort'),
                                      border=kwargs.get('border',0),
                                      repeat_header_every=kwargs.get('repeat_header_every',0),
                                      column_stripe=kwargs.get('column_stripe','FFFFFF'),
                                      row_stripe=kwargs.get('row_stripe','FFFFFF'))


        html = form + html + about + """<script>$(document).ready(function() {
                                         $('#DT_Table').DataTable(    { 'bFilter': false,    'bPaginate': false,  'aLengthMenu': false});
                                          } );
                                        </script>"""
        if show_metacode: html = "<pre>%s</pre>"%self.metacode + html
        if debug: html = debug_message + html
        if error_message: html =  error_message + "<p>" + html
        return wrap_return(html,context,output=output,pyql=pyql)

    # optional overload of code_access_from_parameter ease of data access to CamelCase parameters.
    def camel_case_code_access_from_parameter(self,reference):
        if reference in self.alias_d.keys(): return self.alias_d[reference]
        parameter = None
        if reference in self.headers:
            return PyQL.pyql_dt.DT.code_access_from_parameter(self,reference)
        if reference.lower() in self.headers_lower:
            parameter = self.headers[self.headers_lower.index(reference.lower())]
            return PyQL.pyql_dt.DT.code_access_from_parameter(self,parameter)
        pats = []
        pats.append(re.sub('([A-Z][a-z0-9]*)',lambda g:g.group(1)+'[a-z0-9]*',reference)+'$') # complete with lowercase
        pats.append(re.sub('([A-Z][a-z0-9]*)',lambda g:g.group(1)+'[A-za-z0-9]*',reference)+'$') # complete with any case
        pats.append(re.sub('([A-Z][a-z0-9]*)',lambda g:'[a-z0-9]*'.join(g.group(1))+'[a-z0-9]*',reference)+'$') # regex between all letters
        pats.append(re.sub('([A-Z][a-z0-9]*)',lambda g:'[A-Za-z0-9]*'.join(g.group(1)),reference)+'$') # regex between all letters
        possible = [] # a list of lists of matches
        for pat in pats:
            parameters = filter(lambda x,p=pat:re.match(p,x), self.headers)
            if len(parameters) == 1:
                return PyQL.pyql_dt.DT.code_access_from_parameter(self,parameters[0])
            alpha_parameters = filter(lambda x:x.isalpha(),parameters)
            if len(alpha_parameters) == 1:
                return PyQL.pyql_dt.DT.code_access_from_parameter(self,alpha_parameters[0])
            #print "poss matches",parameters
            if parameters: possible.append((len(parameters),parameters)) # just for easy sort
        if len(possible):
            possible.sort()
            raise UnknownParameterError(reference,possible[0][1])
        #print "no match: just let it through"
        return "%s"%reference

def loader(d,name='name'):
    return dt(d,name)


def repeating_fractions():
    import PyQL.pyql_dt
    db = DT("/home/jameyer/PyDB/Apps/Math/Data/_Column",name='rf')
    #print db.headers
    res = db.query(**{'pyql':'x,r2/x@1','output':"matplotlib.scatter","client_image_dir":"/tmp","web_image_dir":'/tmp'})

if __name__ == "__main__":
    repeating_fractions()
    #dt = DT("/home/jameyer/PyDB/Apps/OECD/Data/_Column","OECD")
    #print dt.query(**{'pyql':"year,country@_i<10"})

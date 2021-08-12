"""
Generic formatters for dt objects.
"""
#THIS_DIR = "/home/jameyer/PyQL2/Source"
import sys,time,string,os,cPickle
#sys.path[:0] = [THIS_DIR]
#import py_tools,columns
import cPickle
import PyQL.columns
import PyQL.py_tools


def pickle_columns(dt,pdir,verbose=1):
    for h in range(len(dt.headers)):
        header = dt.headers[h]
        if verbose: print 'pkl',header
        f = os.path.join(pdir,header+'.pkl')
        cPickle.dump(dt.data[h].data,open(f,'w'))

def percent_format(total,win,plus_sign=1,str_none='--'):
    if total is None or win is None: return str_none
    if type(total) is type("Abc") or type(win) is type("Abc"): return " "
    val = win*100./(total or 1)
    return "+"*(plus_sign and 0<val) + "%0.1f"%val + "%"

def line_format(val,plus_sign=1,sigfig=0):
    return '+'*(plus_sign>0 and val>0) + ('%%0.%sf'%sigfig)%val

def dollar_format(val,plus_sign=1,str_none='--'):
    if val is None: return str_none
    if type(val) is type("Abc"): return val
    str_val = "%0.0f"%abs(val)
    digits = -1
    new_str = ""
    for c in range(len(str_val)-1,-1,-1):
        digits += 1
        #print "new_str,digits:",new_str,digits
        if new_str and not digits%3: new_str = "," + new_str
        new_str = str_val[c] + new_str
    return "%s$%s"%("+"*(plus_sign and 0<val) or "-"*(val<0) or "",new_str)

def log(message="",file="/tmp/output.log"):
    if not message: return
    open(file,'a').write(message+"\n")
    try: open(file,'a').write(message+"\n")
    except: pass

def html(dt,sort=None,sort_button='',show=None,
         repeat_header_every=0,column_stripe="FFFFFF",
         row_stripe="FFFFFF",id="DT_Table",null='-',
         caption='',border=0, error_as_null=0):
    #return "<b>No results</b>"
    if not dt.data:
        return "<b>No results</b>"
    #print "html: ",dt
    if not isinstance(dt.data[0],PyQL.columns.Column): # columns are themselves data tables
        nested = 1
    else:
        nested = 0
    if nested :  outer_id = "outer"
    else: outer_id = id
    ret = ["\n<table border=%s id='%s'>\n"%(border,outer_id) + "<caption>%s</caption>"%(caption)]
    ret.append("<thead><tr>")
    header_row = "<tr>" # cache a copy of the header row (sans sort links) for possible repeat
    #log("headers:%s"%(dt.headers,))
    for header in dt.headers:
        #log("header:%s"%(header,))
        if type(header) is type((1,2,3)):
            if type(header[-1]) is tuple:
                str_header = string.join(header[-1],' ')
            else:
                str_header = string.join(header,' ')
        else: str_header = str(header)
        #log("dt.data[0]:%s"%(dt.data[0],))
        if not isinstance(dt.data[0],PyQL.columns.Column) or not sort_button:
            ret.append("<th>%s</th>"%str_header)
        elif sort_button and type(sort_button) is type("abc"):
            ret.append("<th>%s</th>"%sort_button%str_header)
        elif type(sort_button) is type(lambda x:x):
            ret.append("<th>%s</th>"%sort_button(str_header))
        else:
            ret.append("<th>%s</th>"%str_header)
        header_row += "<th>%s</th>"%str_header
    ret.append("</tr></thead>")
    header_row += "</tr>"
    if not dt.data:
        ret.append("</table>")
        return string.join(ret,"\n") + "\n"
    #log( "type(dt.data[0]):%s"%type(dt.data[0]))
    #assert False,  "type(dt.data[0]):%s"%type(dt.data[0])
    if nested: # columns are themselves data tables
        ret.append("<tr>")
        for item in dt.data:
            ret.append("<td valign=top align=center>%s</td>"%html(item,sort=sort,sort_button=sort_button,show=show,repeat_header_every=repeat_header_every,column_stripe=column_stripe,row_stripe=row_stripe))
        ret.append("</tr>")
        ret.append("</table>")
        return string.join(ret,"\n")
    #print "dt.html: not a dt"
    # if dt.data element values are lists then format each item in the list
    data = []
    if sort is not None: dt.sort_by_column(offset=sort)
    #print "dt.data:",dt.data
    for item in dt.data:
        #print "item.value():",item.value()
        if type(item.value()) is list: # py_tools.py_types.sequences:
            data.append(item.value())
        else:
            #print "listify"
            data.append([item.value()])
    if not data:
        ret.append("</table>")
        return string.join(ret,"\n") + "\n"
    #print "DT.html.data:",data
    len_data = max(map(len,data))
    n_rows = show or len_data
    if show and show<0: # take the last n_rows, watch out for None<0 (fixed in python3)
        rng = range(max([0,n_rows+show]),n_rows)
    else:
        rng = range(n_rows)  # take the first n_rows
    for r in range(n_rows):
        if len_data == r: break
        #print "dt.html.r:",r
        ret.append("<tr%s>"%((r%2)*' ' or " bgcolor=%s"%row_stripe))
        row_bgcolor = (r%2)*"FFFFFF" or  row_stripe
        for c in range(len(dt.headers)):
            column_bgcolor = ((c+1)%2)*"FFFFFF" or  column_stripe
            bgcolor = PyQL.py_tools.add_colors(column_bgcolor,row_bgcolor)
            ret.append("<td valign=top bgcolor=%s>"%bgcolor)
            #print "header:",dt.headers[c]
            #print "data[%d][%d]"%(c,r)," --- "*(len(data[c])<=r) or data[c][r]
            #print "dt.data[%d].fomat:"%c,dt.data[c].format
            #print "dt.data[%d]"%c,dt.data[c]
            if error_as_null:
                try: ret.append(null*(len(data[c])<=r or data[c][r] is None) or dt.data[c].format(data[c][r]))
                except: ret.append(null)
            else:
                #print "outputs: formatting",data[c][r],"with",dt.data[c].str_format
                ret.append(null*(len(data[c])<=r or data[c][r] is None) or dt.data[c].format(data[c][r]))
            ret.append("</td>")
        ret.append("</tr>")
        #print "r:",r
        if repeat_header_every and r and not (r+1)%repeat_header_every and 0 < n_rows - r - repeat_header_every:
            ret.append(header_row)
    ret.append("</table>")
    #print "html returnint:",ret
    return string.join(ret,"\n") + "\n"


def add_reduced_as_key(dt):
    # query result key is ( (pyql terms), (as terms))
    # if there are common elements in the as term make the keys (pyql, as terms, reduced as terms)
    len_headers = len(dt.headers)
    if not len_headers: return
    #print 'outputs:heasders',dt.headers
    #if len(dt.headers[0])<2: return dt.headers[0]
    len_as = len(dt.headers[0][1])
    i = 0
    common = 1
    while common and i < len_as:
        val = dt.headers[0][1][i]
        #print 'outputs:val,i',val,i
        for h in range(1,len_headers):
            if dt.headers[h][1][i] != val:
                common = 0
                break
        i += 1
    cl = i - 1  # common left

    i = 0
    common = 1
    while common and i < len_as:
        val = dt.headers[0][1][len_as-1-i]
        for h in range(1,len_headers) :
            if dt.headers[h][1][len_as-1-i] != val:
                common = 0
                break
        i += 1
    cr = i - 1
    #print "cr,cl:",cr,cl
    common = ''
    if cl or cr:
        common = ' '.join(dt.headers[0][1][:cl])
        if common: common += ' '
        common += ' '.join(dt.headers[0][1][len_as-cr:])
        common = common.replace("and and","and")
        if common.startswith('and '): common = common[4:]
        #print "slice:",cl,len_as-cr
        for i in range(len_headers):
            dt.headers[i] =  (dt.headers[i][0],dt.headers[i][1] , dt.headers[i][1][cl:len_as-cr] )
            dt[i].name =  dt.headers[i]
            #print "dt.headers[i]",dt.headers[i]
    #print "common:",common
    return common.strip()

def auto_reduce(dt,key_transform=None,name='query',format='%s'):
    # if all columns are summatives then reduce
    len_dt = len(dt)
    if not len_dt: return dt
    for i in range(len_dt):
        #log("auto_reduce.i=%d; name: %s"%(i,dt[i].name),)
        for col in dt[i]:
            if type(col.value()) is list: return dt
    #log("auto reducing")
    return dt.reduced(key_transform,name=name,format=format)


# a single dt with columns for elements
def csv(dt,pyql='',pyql_as='',
            show_headers=True,
            str_none='',
            sigfig=3,
            query_name="pyql",
            delim=',',
            sort=None,
            ):
    lout = []
    if sort is not None:
        dt.sort_by_column(sort)
    if show_headers:
        lout.append(delim.join(dt.headers))


    for r in range(len(dt[0])):
        rout = []
        for c in range(len(dt.headers)):
            val = dt[c][r]
            if val is None:
                rout.append(str_none)
            elif type(val) is float:
                rout.append( ("%%0.%sf"%sigfig)%val )
            else:
                rout.append("%s"%(val,))
        lout.append(delim.join(rout))
    return '\n'.join(lout)

# a single dt with columns for elements
def json_single(dt,pyql='',pyql_as='',
            show_headers=True,
            str_none='null',
            sigfig=3,
            query_name="pyql",
            ):
    out = '{ \n\t"%s": "%s" ' % (query_name,pyql,)
    if pyql_as: out += ',\n\t"as": "%s"'%(pyql_as,)
    if show_headers:
        out += ',\n\t"headers": %s'%(list(dt.headers),)
    out += ',\n\t"columns" : [\n'
    #print "out:",out
    #dt.sort()
    i = -1
    for col in dt:
        i += 1
        cols = "["
        #print "cname:",col.name,col.data,col.value()
        data = col.data or [col.value()]
        for val in data:
            #print "val:",val,type(val)
            if val is None:
                cols +="%s"% str_none
            elif type(val) is float:
                cols += ("%%0.%sf"%sigfig)%val
            elif type(val) is str:
                cols += "'%s'"%string.replace(val,"'","\'")
            elif type(val) is list:
                cols += '['
                for item in val:
                  if type(item) is float:
                      cols += ("%%0.%sf,"%sigfig)%item
                  if type(item) is str:
                      cols += '"%s",'%(item,)
                  elif item is None:
                      cols += "%s,"%(str_none,)
                  else:
                      cols += "%s,"%(item,)
                if cols[-1] == ',': cols = cols[:-1]
                cols += ']'
            elif isinstance(val,PyQL.columns.Column):
                raise
            else:
                cols += "%s"%(val,)
            cols +=","
        cols = string.strip(cols)
        #cols = string.replace('None',str_null)
        if cols[-1] == ',': cols = cols[:-1]
        cols += "],\n"
        out += "\t\t"+cols
    out = out[:-2] + '\n\t]}'
    return out

def json(dt,str_none='null',
            sigfig=3,
            query_name="pyql",
        ):
    # a single dt or a dt of dts?
    if not dt or not len(dt): return "null"
    if not isinstance(dt[0],PyQL.dt.DT):
        #print dt
        pyql = ' '.join((dt.name,))
        pyql_as = ' '.join((dt.name,))
        return json_single(dt=dt,pyql=pyql_as,show_headers=1,str_none=str_none,sigfig=sigfig,query_name=query_name)

    out = '{ \n"headers": %s'%(list(dt[0].headers),)
    out += ',\n"groups": [\n'
    for d in dt:
        pyql = ' '.join(d.name[0])
        pyql_as = ' '.join(d.name[1])
        out += json_single(dt=d,pyql=pyql_as,show_headers=0,str_none=str_none,sigfig=sigfig,query_name=query_name)
        out += ",\n"
    out = out[:-2] + "\n\t]\n}"
    return out



def pickle_column(col,fout):
    cPickle.dump({"name":col.name,"data":col.data,"format":col.str_format},open(fout,'w'))

def pickler(dt,directory='/tmp',name='test.py',create_dir=0):
    if not os.path.isdir(directory) and create_dir:
        os.system("mkdir %s"%directory)
    out = ["# dumped by ~PyQL2/Source/outputs.py on %s"%time.ctime()]
    out.append("import cPickle")
    out.append("from PyQL.dt import DT")
    out.append("from PyQL.columns import Column")
    out.append("")
    out.append("dt = DT()")
    for i in range(len(dt.data)):
        fout = os.path.join(directory,"%s.pkl"%dt.headers[i])
        cPickle.dump(dt.data[i].data,open(fout,'w'))
        out.append("f=open('%s','r')"%fout)
        out.append("dt.add_object(Column(data=cPickle.load(f),name=r'''%s''',format=r'''%s'''))"%(dt.headers[i],dt.data[i].str_format))
    out.append('')
    open(os.path.join(directory,name),'w').write('\n'.join(out))



### test and demos############
def test_pickle():
    import column_types
    c = PyQL.columns.Column("total")
    c.append(column_types.Total('6.5'))
    print "prepickle:",c[0],c[0]+1
    cPickle.dump(c,open('/tmp/total.pkl','w'))
    c2 = cPickle.load(open('/tmp/total.pkl'))
    print "postpickle:",c2[0],c2[0]+1

def test_html(test_dt):
    print html(test_dt)
    res = test_dt.query("age,weight@1")
    print html(res)
    res = test_dt.query("age,weight@height")
    print html(res)

def test_json(test_dt):
    #print json(test_dt)
    sdql = "Replace(age),Replace(weight)@first name[0] and age as Age>0"
    sdql = "(age,weight,height)@1"
    res = test_dt.query(sdql)#.reduced(None)

    print json(res)
    #res = test_dt.query("S(age),age,weight@1")[0]
    #print json(res)

def test_formats(test_dt):
    test_dt.show_metacode=1
    res = test_dt.query(r"Sum(age,format='''lambda x,df=PyQL.outputs.dollar_format:df(x)''')@1").reduced(None)
    #res = test_dt.query("Sum(age)@1").reduced(None)
    print res

def test_reduce_as_key(test_dt):
    res = test_dt.query("first name@1 and 2 and age and (weight>0 and age>0) and 4>2")
    print res
    common = reduce_as_key(res)
    print 'common',common
    print res

if __name__ == "__main__":
    #test_pickle()
    #import PyQL.dt as dt
    #test_dt = dt.test_dt()
    #test_formats(test_dt)
    #test_dt.build_lexer()
    #test_html(test_dt)
    #test_json(test_dt)
    #pickler(test_dt)
    #test_reduce_as_key(test_dt)
    print 'line format',line_format(120.7,sigfig=3)

#!/usr/bin/env python
# cython: profile=True

import string,random,re,time,math,sys,os,glob,cgi,urllib
import datetime
from itertools import product

MONTH_NUMBERS = {"January":1,"February":2,"March":3,"April":4,"May":5,"June":6,"July":7,"August":8,"September":9,"October":10,"November":11,"December":12}

MTH_NUMBERS = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}

# move down from Source dir and up to Tpy
def tpy_dir_from_file(f,tpy='Tpy'):
    return os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(f))),tpy)

def data_formats_from_html(out):
    data = [] # a list of rows (sideways from a dt.)
    formats = []  # pdf table formats. Build from html colspan
    #print 'out:',out
    out = re.sub('[\s]+',' ',out,0,re.I) # normalize to single space - which matters in pdf
    out = re.sub('<br>','\n',out,0,re.I)
    out = re.sub('&nbsp;',' ',out,0,re.I)
    #out = re.sub('<t([h|d]) [^>]*colspan[\s]*=[\s]*=([0-9]+)',lambda x,f=formats:handle_colspan(x,f),out,0,re.I)
    rows = re.split('<tr',out,0,re.I)[1:]
    for r,row in enumerate(rows):
        row = re.split('</tr>',row,0,re.I)[0]
        #print "row:",row
        parts = []
        tds = re.split('<t[d|h][^>]*?(?:colspan=([0-9]+))?>',row,0,re.I)
        s = 0 # the match index
        c = 0 # the column index
        while s<len(tds)-1:
            s += 1;col_span = tds[s]
            s += 1
            # do not have  < > inside a td! use &lt; &gt; for html
            td = re.sub('<[^>]+>','',tds[s].strip()).replace('&lt;','<').replace('&gt;','>')
            parts.append(td)
            if col_span:
                ics = int(col_span)
                for i in range(1,ics):
                    parts.append('')
                formats.append(('LINEAFTER',(c+ics-1,r),(c+ics-1,r-1),1,GRID_COLOR))
                formats.append(('LINEBEFORE',(c,r),(c,r-1),1,GRID_COLOR))
                if ics>1: formats.append(('SPAN',(c,r),(c+ics-1,r)))
                c += ics
            else:
                c += 1
            #print 'col_span:',r,s/2,col_span
        #print "parts:",parts
        data.append(parts[:])
    return data,formats


def log(m):
    open("/tmp/pt.out",'a').write("%s\n\n"%m)

def in_parens(t): # return True if the whole text is enclosed in parens. (1) and (2) is False (1 and 2) is True
    t = t.strip()
    if t[0] != '(' or t[-1] != ')': return False
    start = stop = 0
    for c in t[1:-1]:
        if c == '(': start += 1
        elif c == ')': stop += 1
        if stop > start: return False
    return True


def query_link(pyql='',english=None,page='query',name='sdql'):
    return "<a href=%s?%s=%s>%s</a>"%(page,name,urllib.quote(pyql),cgi.escape(english or pyql))

# this is used by S2/*/howto and ought to be replaced by above
def link(page='query',sdql='',english=None,**kwargs):
    args = ''
    for k,v in kwargs.iteritems():
        args += "&%s=%s"%(urllib.quote(str(k)),urllib.quote(str(v)))
    return "<a href=%s?sdql=%s%s>%s</a>"%(page,urllib.quote(sdql),args,cgi.escape(english or sdql))

# used by cgi scripts for setting types of webvars
def guess_types(d,remove_blank=1):
    #print "gt:",d
    for var in d.keys():
        val = d[var]
        if val in ['',['']]: # and remove_blank:
            del d[var]
            continue
        if type(val) is list and len(val) == 1:
            val = val[0]
            d[var] = val
        if type(val) is str:
            if val.isdigit() or (len(val)>1 and val[0]=='-' and val[1:].isdigit()):
                #print "int",var,val
                d[var] = int(val)
            else:
                try: d[var] = float(val)
                except: pass
        elif type(val) is list:
            try:
                d[var] = map(int,val)
            except:
                try:
                    d[var] = map(float,val)
                except:
                    pass
    #open("/tmp/py_tools.guest_type.out",'w').write("ret:%s"%d)
    return d

def parse_qs(qs):
    # pyql wants to allow points@team=Cubs&show_games=10&show_unplayed=5
    ret = {}
    parts =qs.split('&')
    for part in parts:
        name,val = (part.split('=') + ["1"])[ :2] # just mention to set to 1
        ret[name] = val
    return guess_types(ret)

# metacode tests inequalites for None by multipling by 1. This will not be needed in Python 3.
class DictWithMul(dict):
    def __init__(self, *args):
        dict.__init__(self, args)
    def __mul__(self,other):
        other == None and 1*other
        return self
    def __rmul__(self,other):
        return self.__mul__(other)

def time_from_string(s):
    mo = re.search("(^|[^0-9])(?P<hh>[0-9]{2,2}):(?P<mm>[0-9]{2,2}):(?P<ss>[0-9]{2,2})",s)
    if mo:
        return float("%s%s.%s"%(mo.group('hh'),mo.group('mm'),mo.group('ss'),))

def date_from_string(s):
    # look through some known formats and return Date8
    mo = re.search("(?P<month>[0-9]{1,2})/(?P<day>[0-9]{1,2})/(?P<year>[0-9]{4,4})",s)
    if mo:
        d = mo.group('year') + mo.group('month').zfill(2) + mo.group('day').zfill(2)
        return Date8(int(d))
    mo = re.search("(?P<day>[0-9]{1,2})/(?P<month>%s)/(?P<year>[0-9]{4,4})"%'|'.join(MTH_NUMBERS),s)
    if mo:
        d = mo.group('year') + '%0.2d'%MTH_NUMBERS[mo.group('month')] + mo.group('day').zfill(2)
        return Date8(int(d))

# use column_types.Date
class Date8(int):
    def __init__(self,value):
        assert len(str(value)) == 8
        self.value = value
    def __radd__(self,other):
        return Date8(add_days_to_date(self.value,other))
    def __add__(self,other):
        return Date8(add_days_to_date(self.value,other))
    def __mul__(self,other):
        return Date8(self.value*other)
    def __rmul__(self,other):
        return Date8(self.value*other)
    def __sub__(self,other):
        if isinstance(other,Date8):
            return delta_days(self.value,other)
        return Date8(add_days_to_date(self.value,-other))
    def nice_str(self):
        if not self.value: return self.value
        str_val = str(self.value)
        return "%s-%s-%s"%(str_val[4:6],str_val[6:],str_val[:4])


def html_select(options,name,selected,size=1):
    if type(selected) is str: selected = [selected]
    ret = "<select name='%s' size=%s>"%(name,size)
    for option in options:
        ret += "<option%s>%s\n"%(' SELECTED'*(option in selected),option)
    ret += "</select>"
    return ret

def nice_int(num):
    # put commas for thousands
    ret = []
    snum = "%d"%num
    len_snum = len(snum)

    for i in range(len_snum-1,-1,-1):
        ret.append(snum[i])
        if i and not (len_snum-i)%3:
            ret.append(",")
    ret.reverse()
    return ''.join(ret)


# via http://mappinghacks.com/code/dp.py.txt
def simplify_points (pts, tolerance):
    anchor  = 0
    floater = len(pts) - 1
    stack   = []
    keep    = set()

    stack.append((anchor, floater))
    while stack:
        anchor, floater = stack.pop()

        # initialize line segment
        if pts[floater] != pts[anchor]:
            anchorX = float(pts[floater][0] - pts[anchor][0])
            anchorY = float(pts[floater][1] - pts[anchor][1])
            seg_len = math.sqrt(anchorX ** 2 + anchorY ** 2)
            # get the unit vector
            anchorX /= seg_len
            anchorY /= seg_len
        else:
            anchorX = anchorY = seg_len = 0.0

        # inner loop:
        max_dist = 0.0
        farthest = anchor + 1
        for i in range(anchor + 1, floater):
            dist_to_seg = 0.0
            # compare to anchor
            vecX = float(pts[i][0] - pts[anchor][0])
            vecY = float(pts[i][1] - pts[anchor][1])
            seg_len = math.sqrt( vecX ** 2 + vecY ** 2 )
            # dot product:
            proj = vecX * anchorX + vecY * anchorY
            if proj < 0.0:
                dist_to_seg = seg_len
            else:
                # compare to floater
                vecX = float(pts[i][0] - pts[floater][0])
                vecY = float(pts[i][1] - pts[floater][1])
                seg_len = math.sqrt( vecX ** 2 + vecY ** 2 )
                # dot product:
                proj = vecX * (-anchorX) + vecY * (-anchorY)
                if proj < 0.0:
                    dist_to_seg = seg_len
                else:  # calculate perpendicular distance to line (pythagorean theorem):
                    dist_to_seg = math.sqrt(abs(seg_len ** 2 - proj ** 2))
                if max_dist < dist_to_seg:
                    max_dist = dist_to_seg
                    farthest = i

        if max_dist <= tolerance: # use line segment
            keep.add(anchor)
            keep.add(floater)
        else:
            stack.append((anchor, farthest))
            stack.append((farthest, floater))

    keep = list(keep)
    keep.sort()
    return [pts[i] for i in keep]


def remove_jameyer(globber,down_dirs=2):
    def sub(g):
        print "sub g",g
        ret = "sys.path[:0] = [os.path.join(" + ("%s"%(['..']*down_dirs))[1:-1] + ','
        for d in string.split(g.group(1),os.path.sep):
            ret += '"%s",'%d
        return ret + ")]"
    jam_pat = re.compile(r'''sys.path\[:0\][\s]*=[\s]*\["/home/jameyer/([^\]]+)"\]''')
    for file in glob.glob(globber):
        txt =  open(file).read()
        txt = jam_pat.sub(sub,txt)
        open(file,'w').write(txt)

def offset_dict(lst):
    d = {}
    i = -1
    for item in lst:
        i += 1
        d[item] = i
    return d

# auto download partially fails
def clear_small_files(globber,size):
    files = glob.glob(globber)
    files.sort()
    for f in files:
        print "testing",f,"for too small"
        if os.stat(f).st_size < size:
            print f,"too small: removing"
            os.system("rm %s"%f)

def clear_old_files(dir,too_old_time):
    files = glob.glob(os.path.join(dir,'*'))
    files.sort()
    for file in files:
        mtime = os.path.getmtime(file)
        print file,mtime
        if mtime < too_old_time:
            print "too old: removing"
            os.system("rm %s"%file)

class Int_fdiv(int):
    def __init__(self,value):
        self.value = value
    def __div__(self,other):
        return 1.*self.value/other
    #def __rdiv__(self,other):
    #    return 1.*other/self.value
    def __mul__(self,other):
        return Int_fdiv(self.value*other)
    def __rmul__(self,other):
        return Int_fdiv(self.value*other)
    #def __add__(self,other):
    #    return Int_fdiv(self.value+other)
    #def __radd__(self,other):
    #    return Int_fdiv(self.value+other)
    #def __sub__(self,other):
    #    return Int_fdiv(self.value-other)
    #def __rsub__(self,other):
    #    return Int_fdiv(other - self.value)


class Float(float):
    def __init__(self,value):
        self.value = value
        self.sigfig = 2
    def __radd__(self,other):
        f = Float(self.value+other)
        f.sigfig = self.sigfig
        return f
    def __add__(self,other):
        f = Float(self.value+other)
        f.sigfig = self.sigfig
        return f
    def __mul__(self,other):
        f = Float(self.value*other)
        f.sigfig = self.sigfig
        return f
    def __rmul__(self,other):
        f = Float(self.value*other)
        f.sigfig = self.sigfig
        return f
    def __div__(self,other):
        f = Float(self.value/other)
        f.sigfig = self.sigfig
        return f
    def __rdiv__(self,other):
        f = Float(other/self.value)
        f.sigfig = self.sigfig
        return f
    def __sub__(self,other):
        f = Float(self.value-other)
        f.sigfig = self.sigfig
        return f
    def __rsub__(self,other):
        f = Float(other - self.value)
        f.sigfig = self.sigfig
        return f

    def __str__(self):
        if self.value is None: return self.value
        return ("%%0.%df"%self.sigfig)%self.value


# return an imported file name, don't pollute sys.path
def importer(file,refresh=0):
    sys.path[:0] = [os.path.dirname(file)]
    python_page = __import__(os.path.basename(file)[:-3])
    if refresh:
        reload(python_page)
    del(sys.path[0])
    return python_page

def nice_date(date,abbreviate_month=0,abbreviate_year=0,show_year=1):
    if date is None:
        return date
    date = "%s"%date
    #print "PyQL.pytool.nicedate:",date
    #return time.strftime("%B %d, %Y",(int(date[:4]),int(date[4:6]),int(date[6:]),0,0,0,0,0,0))
    nice_date =  time.strftime("%B %d %Y",(int(date[:4]),int(date[4:6]),int(date[6:]),1,1,1,1,1,1))
    m,d,y = string.split(nice_date," ")
    if abbreviate_month:
        m = m[:3]
    if not show_year:
        return "%s %s"%(m,d)
    if abbreviate_year:
        y =  y[-2:]
    return "%s %s, %s"%(m,d,y)

def today(delta_days=0):
    now_tuple = time.localtime(time.time()+delta_days*3600*24)
    return Date8(int("%4d%0.2d%0.2d"%(now_tuple[0],now_tuple[1],now_tuple[2])))
def yyyymmddhhmm(delta_days=0):
    now = time.localtime(time.time()+delta_days*3600*24)
    return 100000000*now[0]+1000000*now[1]+10000*now[2]+100*now[3]+now[4]

def add_days_to_date(start,days):
    str_start = str(start)
    d = datetime.date(int(str_start[:4]),int(str_start[4:6]),int(str_start[6:]))
    t = datetime.timedelta(days)
    r = d + t
    return r.year*10000+r.month*100+r.day

def day_from_date(date):
    date = "%s"%date
    t = time.localtime(time.mktime((int(date[:4]),int(date[4:6]),int(date[6:8]),0,0,0,0,0,0)))
    return time.strftime("%A",t)

def delta_days(date1,date2): #date1 and date2 are 8 digit dates YYYYMMDD: return d1-d2
     date1 = "%s"%date1
     date2 = "%s"%date2
     d2 = time.mktime((int(date2[:4]),int(date2[4:6]),int(date2[6:8]),0,0,0,0,0,0))
     d1 = time.mktime((int(date1[:4]),int(date1[4:6]),int(date1[6:8]),0,0,0,0,0,0))
     return int((d1 - d2)/86400)

def date_range(start,days):
    """ enter a start date in YYYYMMDD and an interger number of days: return a list of integer dates """
    str_start = str(start)
    d = datetime.date(int(str_start[:4]),int(str_start[4:6]),int(str_start[6:]))
    one_day = datetime.timedelta(days=1)
    if days < 0:
        one_day = -1*one_day
        days = -1*days
    ret = []
    for i in range(days):
        ret += [int(d.strftime("%Y%m%d"))]
        d += one_day
    return ret

class Timer:
    def __init__(self): self.start = time.time()
    def time(self): return time.time()-self.start

#usage:  if type(my_object) in py_tools.py_types.sequences: then my_object is either a list or tuple
class Py_types:
    import types
    string = types.StringType
    integer = types.IntType
    float = types.FloatType
    long = types.LongType
    list = types.ListType
    tuple = types.TupleType
    dictionary = types.DictionaryType
    instance = types.InstanceType
    numbers = [integer,float,long]
    sequences = [list,tuple]
    int = integer
py_types = Py_types()

def factorial(N,use_stirling=None):
    if use_stirling and use_stirling<N:
        return math.pow(2*math.pi,0.5)*math.pow(N,0.5)*math.pow(N/math.e,N)
    return math.factorial(N)

def ln_factorial(N,use_stirling=None):
    if use_stirling and use_stirling<N:
        return 0.5*math.log(2*math.pi*N) + N*math.log(N) - N
    ret = 1
    for i in range(1,N+1): ret *= i
    return math.log(ret)

def combinatoric(N,M,use_stirling=None,ret_ln=0):
    if M>N: raise "N flips, M heads"
    T = N - M
    ln_ret = ln_factorial(N,use_stirling) - ln_factorial(T,use_stirling) - ln_factorial(M,use_stirling)
    if ret_ln: return ln_ret
    return math.exp(ln_ret)

def probability(N,M,p=0.5,use_stirling=30):
    change_direction = 0
    if p < 0:
        p = abs(p)
        change_direction = 1
    q = 1 - p
    #if D_PROBABILITY.has_key((N,M,p)): return D_PROBABILITY[(N,M,p)]
    ret = 0
    if (p==0.5 and M>N*p) or (p>0.5 and change_direction==0) or (p<0.5 and change_direction==1):
        for m in range(M,N+1):
            ret += math.exp(m*math.log(p) + (N-m)*math.log(1-p) + combinatoric(N,m,use_stirling,ret_ln=1))
    else:
        for m in range(M+1):
            ret += math.exp(m*math.log(p) + (N-m)*math.log(1-p) + combinatoric(N,m,use_stirling,ret_ln=1))
    #D_PROBABILITY[(N,M,p)] = ret
    #print "N,M,prob:",N,M,ret
    return ret

def add_colors(col1,col2): #overlay two colors (substract components)
    ret = []
    for i in [0,2,4]:
        c1_10 = 255 - string.atoi("0x%s"%col1[i:i+2],0)
        c2_10 = 255 - string.atoi("0x%s"%col2[i:i+2],0)
        #c2_10 = 255 - 16*d10[col2[i]] - d10[col2[1+i]]
        sum = 255 - (c1_10 + c2_10)
        if sum < 0:
            ret.append("00")
        else:
            ret.append(hex(sum)[2:])
    return string.join(ret,"")


# return [list1[0],list2[0],list1[1],list2[1],....]
def entwine(list1,list2):
    ret = []
    while list1 + list2:
        if list1: ret.append(list1.pop(0))
        if list2: ret.append(list2.pop(0))
    return ret

#return a list of subtexts split on delims which are not in quotes or braces
#as per the regex split rules, the list of subtexts include the delimitors if they are captured with parens (eg delim='(\t)' )
def split_not_protected(text,              #the string to split
                        delim=' ',         # regex
                        n_splits=None, # the maximum number of splits to take
                        protect_in_braces=1,
                        protect_single_quotes=1,
                        protect_double_quotes=1,
                        protect_braces=1):

    if not text: return [""]
    try:
        if delim == '|':
            pat = re.compile('\|')
        else:
            pat = re.compile(delim)
        items = pat.split(text)
        delims = pat.findall(text)        # the actual delimitor for possible reinsertion

    except:
        items = string.split(text,delim)
        delims = (delim,)*(len(items) - 1)
    #print "items:",items
    #print "delims:",delims
    return_delims = 0
    if len(items) > len(delims) + 1:  # the regex captured the delimitors
        return_delims = 1
        for i in range(1,(len(items)+1)/2):del(items[i])
        #print "items:",items
        #print "delims=%s"%delims

    len_items = len(items)
    len_delims = len(delims)
    if len(items) < 2:
        if return_delims>0: return entwine(items,delims)
        return items
    open_quotes = {}
    if protect_single_quotes:
        open_quotes["'"]=0
    if protect_double_quotes:
        open_quotes['"']=0
    open_braces = {}
    close_braces = {}
    if protect_braces:
        open_braces = {'{':0,'[':0,'(':0}
        close_braces = {'}':'{',']':'[',')':'('}

    #first run through and record all protected offsets in protected_offsets
    protected_offsets = []          # a list of offsets which are quoted or in braces
    offset = -1
    for c in text:
        offset += 1
        #print "text[%d]:"%offset,c
        #print "open_quotes:",open_quotes
        #print "open_braces:",open_braces
        if c in open_quotes.keys():
            if not sum(open_quotes.values()): # there are no open quotes
                open_quotes[c] = 1                # set this flavor to open
                protected_offsets.append(offset)  # protect this offset
            elif open_quotes[c] == 1:         # this flavor was open
                open_quotes[c] = 0                # close this flavor
                protected_offsets.append(offset)  # protect this offset
            else:                             # a different flavor is open
                pass                              # no change in open quote status

        elif not protect_in_braces:
            if sum(open_quotes.values()): protected_offsets.append(offset)  # protect this offset
            continue

        elif c in open_braces.keys() and 1 not in open_quotes.values():
            open_braces[c] += 1
            protected_offsets.append(offset)  # protect this offset
        elif c in close_braces.keys() and open_braces[close_braces[c]] \
                                                     and 1 not in open_quotes.values():
            open_braces[close_braces[c]] -= 1
            protected_offsets.append(offset)  # protect this offset
        elif sum(open_quotes.values() + open_braces.values()): #some non special character with protection
            protected_offsets.append(offset)
    #print "protected:",protected_offsets
    ret_items = [items[0]]
    delim_items = []
    text = items[0] # rebuild text from items to keep track of overall offset
    #print "protected:",protected_offsets
    for i in range(1,len_items):
        item = items[i]
        delim = delims[i-1]
        #print "i,text,len(text),ret_items:",i,text,len(text),ret_items
        if len(text) in protected_offsets: # this one is protected
            #print "protected"
            ret_items[-1] = string.join([ret_items[-1],item],delim)
        else:
            ret_items.append(item)
            delim_items.append(delim)
            if n_splits and i + 1 < len_items and n_splits < len(ret_items): # join the rest and return
                last_item = ret_items[-1]
                while i < len_delims:
                    last_item += delims[i] + items[i+1]
                    i += 1
                ret_items[-1] = last_item
                if return_delims>0: return entwine(ret_items,delim_items)
                return ret_items
        text += delims[i-1] + item
    if return_delims>0: return entwine(ret_items,delim_items)
    return ret_items

#set a common type among simple elements in a list.
#elements are not cast to higher order object (eg dict and list)
def common_type(lst):
    #print "py_tools.common_type: lst[0] = %s"%lst[0]
    types_found = {}
    for item in lst:
        if item is not None: types_found[type(item)] = None
    if len(types_found) < 2: return lst # already of a single type (or all None)
    if py_types.tuple in types_found or py_types.list in types_found or \
       py_types.dictionary in types_found: return lst

    if py_types.string in types_found:
        return map(lambda x: str(x)*(x is not None) or None,lst)

    def float_if_not_None(val):
        if val == None: return None
        return float(val)
    def str_if_not_None(val):
        if val == None: return None
        return str(val)

    if py_types.float in types_found and py_types.integer in types_found:return map(float_if_not_None,lst)

    return map(str_if_not_None,lst)

def remove_duplicates(lst):
    return dict.fromkeys(lst).keys()

def random_cohort_from_dicts(child,parent):
    """child and parent are of the form {'key 1':(v11,v12...), 'key 2': (v21,v22,...),...}
               A dictionary of randomly selected parent values is returned with len(ret[key i]) == len(child[key i])
               """
    ret = {}
    for key in child.keys():
        if not parent.has_key(key): raise "all child keys must exist in the parent."
        parent_values = list(parent[key]) #make copy so as to use del
        len_child_values = len(child[key])
        len_parent_values = len(parent[key])
        if len_parent_values < len_child_values:
            raise "there must be a least as many parent as child values as each and every child key."
        if len_parent_values == len_child_values:
            ret[key] = parent_values[:]  #do I need these [:] copies???
            continue   #no entropy here
        if len_child_values < len_parent_values/2.0:
            ret[key] = []
            while len(ret[key]) < len_child_values:
                i = random.randint(0,len(parent_values)-1)
                ret[key].append(parent_values[i])
                del(parent_values[i])
        else:  #randomly select the ones not returned
            while len(parent_values) > len_child_values:
                i = random.randint(0,len(parent_values)-1)
                del(parent_values[i])
            ret[key] = parent_values[:]
    return ret

#return a random subset from parent which matches the structure of child
def random_cohort(child,parent):
    if type(child) is not type(parent): raise "child and parent must be the same type."
    if type(child) is type({'a':"a letter"}): return random_cohort_from_dicts(child,parent)
    if type(child) in py_types.sequences:
        cd = {}
        pd = {}
        for item in child: cd[item[0]] = item[1]
        for item in parent: pd[item[0]] = item[1]
        cohort = random_cohort_from_dicts(cd,pd)
        ret = []
        for item in child: ret += [[item[0],cohort[item[0]]]]
        return ret

    raise "%s not supported"%type(child)

# could, as above, check for N>len(lst/2) and handle separately
def random_subset(N,lst):
    len_lst = len(lst)
    if len_lst == N: return lst
    if len_lst < N: raise "the number of items requested cannot be larger than the length of the list."
    ret = []
    temp = lst[:]
    while len(ret) < N:
        i = random.randint(0,len(temp)-1)
        ret.append(temp[i])
        del(temp[i])
    return ret

def transpose_table(l):
    #log("tt gets:\n\n%s"%(l,))
    return map (lambda column, l=l: map(lambda x, n=column: x[n],l), range(len(l[0])))

def value_from_string(s):
    """return as tuple, list, dict, int, long, float, or string"""
    s = string.strip(s)
    if len(s)>1 and s[0] == '0' and s[1]!='.':
        return s #numeric strings starting with a zero are strings- not numbers.
    if s and s[0] in "[({":
        try: return eval(s)
        except: return s    #some odd string. e.g.: "(foo) and moo"
    if s.lower() == 'nan': return s # float(NAN) doesn't fail!
    try: as_float = float(s.replace(',',''))
    except: return s
    try:
        if as_float == int(as_float):
            return int(as_float)
    except:
        if as_float == long(as_float):
            return long(as_float)
    return as_float

def all_combinations(list_of_lists):
    return product(*list_of_lists) if list_of_lists else []

def tuple_of_tuples_from_txt(txt,
                 delim_row='\n',
                 delim_column="\t",
                 null='',               # the symbol of null in the input txt
                 has_header=1,           # true=>yes, false=>no
                 verbose=1,
                 protect_single_quotes=0, # often O'Brian
                             protect_double_quotes=1,
                             protect_braces=1
                 ):
    """ Enter txt and parameters: return headers[column], data[column][row]"""
    #print "tuple_of_tuples_from_text.has_header:",has_header
    txt_null = null
    lines = string.split(txt,delim_row)
    while not string.strip(lines[0]): lines = lines[1:] # remove any blank lines
    if has_header:
        columns = map(str,string.split(string.strip(lines[0]),delim_column))
        lines = lines[1:]
    else:  #JAM custom naming of columns
        num_columns = len(string.split(lines[0],delim_column))
        columns = tuple(map(lambda i:"column_%d"%i,range(num_columns)))
    data = []
    if verbose: print "headers:",columns
    for column in columns: data.append([])
    #filter empty lines, set user defined null to None, and set the column types
    num_lines = -1
    for line in lines:
        #print 'line:','c'.join(line.split())
        if not string.strip(line):  #ignore empty lines
            continue
        num_lines+=1
        if verbose: print "read_rows: line (%d) = %s"%(num_lines,line)
        fields = map(string.strip,split_not_protected(line,
                   delim_column,
                   protect_single_quotes=protect_single_quotes,
                                                      protect_double_quotes=protect_double_quotes,
                                                      protect_braces=protect_braces))
        if verbose: print "read_rows: fields = %s"%(fields,)
        if len(fields) != len(columns):
            print "len(fields)!=len(columns)",len(fields),len(columns)
            print fields,columns
            raise Exception("read_rows: Mismatch in line #%d\n\tcolumns = %s\n\tline = %s\n\tfields = %s"%(
                                             num_lines,columns,line,fields))
        #print "len is ok for", fields
        for i in range(len(fields)):
            if fields[i] == txt_null: field = None  #set user defined null to python's None
            else: field = value_from_string(fields[i])
            data[i].append(field)
    #print "data[15]:",data[15]
    return columns, tuple(map(tuple,map(common_type,data)))



## Turn iso-8859-1 and Windows 1252 encoded strings into universal ASCII
###  This means that curved quotes turn into straight quotes and some other
###  characters turn into spaces

## The following char table was derived by staring at
## http://en.wikipedia.org/wiki/Windows-1252
##  16 characters per line
##  the fraction 1/2 (dec 189) is mapped to '

replacement= '''\
e ,f".  ^%S"O Z \
 ''""o--~ s"o zY\
 icL Y|S"c "   "\
       .,  " ' ?\
AAAAAAACEEEEIIII\
DNOOOOOx0UUUUYPs\
aaaaaaaceeeeiiii\
dnooooo 0uuuuypy\
'''

# '''

#If the above string is the wrong
# length, this will raise an exception
#z=1/(128-len(replacement))

def force_ascii(s):
    r = ''
    for c in s:
        if ord(c) < 128:
            r += c
        else:
            r += replacement[ord(c)-128]
    return r

######### tests and demos #########
def __test_all_combinations():
    l = [[1,2,3],"ABC"]
    #l = [[]]
    print "all combinations of %s = %s"%(l,all_combinations(l))

def __test_value_from_string():
    s = "47"
    v = value_from_string(s)
    print s," => ",v, type(v)
    s = "0.7"
    v = value_from_string(s)
    print s," => ",v, type(v)
    s = "(4.7,4)"
    v = value_from_string(s)
    print s," => ",v, type(v)
    s = "[4.7,('a',4)]"
    v = value_from_string(s)
    print s," => ",v, type(v)
    s = "{'a':4532}"
    v = value_from_string(s)
    print s," => ",v, type(v)
    s = "1234567890123"
    v = value_from_string(s)
    print s," => ",v, type(v)
    s = "0234567890123"
    v = value_from_string(s)
    print s," => ",v, type(v)

def __test_common_type():
    lst = [1,2,3]
    print lst,common_type(lst)
    lst = [1,2,'3']
    print lst,common_type(lst)
    lst = [1,2.0,3]
    print lst,common_type(lst)
    lst = [[1],2.0,3]
    print lst,common_type(lst)

def __test_random_cohort():
    c = {"a":(1,2,),"b":(5,),"c":(1,2,3,4,45)}
    p = {"a":(10,20,30,40,50),"b":(52,56,1,134),"c":(1,2,3,4,45,54,2,1,5,6,7,8,9,2)}
    print "child = %s\nparent=%s\nrandom_cohort=%s"%(c,p,random_cohort(c,p))
    c = ((1,(1,2)),(2,(45,32,54)),(3,(3,)))
    p = ((1,(1,2,56,787,432)),(2,(45,32,324,1,2,43,4,2)),(3,(3,87,0,2,3)))
    print "child = %s\nparent=%s\nrandom_cohort=%s"%(c,p,random_cohort(c,p))

def __test_random_subset():
    p = range(100,151)
    N = 10
    print "%d randomly selected from %s: %s"%(N,p,random_subset(N,p))

def __test_split():
    delim = ";"
    text = """Average(field,kwd=foo),Sum(f2,kwd)@col"""
    #print text,"\n","split on %s:\n%s"%(delim,split_not_protected(text,delim,0))
    delim = ","
    text = """Average(field,format=lambda x:'%s-%s'%(x[1],x[2])),Average(bob)"""
    #print text,"\n","split on %s:\n%s"%(delim,split_not_protected(text,delim))
    #delim = re.compile("(and|>)")
    #text = """f@s1  and  c2>4"""
    delim = 'Average('
    text = "foo.query('Average(goo)@1')<10 and bob"
    print text,"\n","split on %s:\n%s"%(delim,split_not_protected(text,delim=delim,n_splits=0,
                                                                  protect_in_braces=0))

def __test_tuple_of_tuples_from_txt():
    txt = "age\theight\tweight\n"
    txt += "8\t\t60.4\n"
    txt += "43\t\t160\n"
    print "tuple_of_tuples_from_txt:",tuple_of_tuples_from_txt(txt)

def __test_add_colors():
    c1 = "88FDFF"
    c2 = "AA8188"
    print "%s + %s => %s"%(c1,c2,add_colors(c1,c2))

def __test_probability():
    M = 2986 #1766
    N = 1766+2986
    #N = 8; M =0;
    print "P(%d,%d) = %0.7e"%(N,M,probability(N,M,use_stirling=1),)
    #N=60
    #for M in range(60):
    #    print "P(%d,%d) = "%(N,M),probability(N,M,use_stirling=None),
    #    print "P(%d,%d,stirling approx.) = "%(N,M),probability(N,M,use_stirling=2)

def __test_date_range():
    start = 20031219
    days = 14
    print "%d days from %s: %s"%(days,start,date_range(start,days))

def __test_day_from_date():
    print day_from_date(20050809)

def __test_nice_date():
    print nice_date(20071030,0,0)

def __test_importer():
    open("/tmp/test_importer.py",'w').write("d={'a':1}")
    f = importer("/tmp/test_importer.py")
    print f
    print f.d

def __test_remove_duplicates():
    lst = [1,2,3,4,5,4]
    lst= remove_duplicates(lst)
    lst.append(5)
    print lst

def __test_date8():
    d = Date8(20070910)
    print d -39
    print "%d"%(d -39)
    print 39 - d

def __test_Float():
    f = Float(23)
    print f + 39
    print 39 + f
    print 43.234 - f
    print f - 43.234
    print f * 43.234
    print 3.14*f
    print f / 43.234
    print 3.14/f

def __test_fdiv():
    b = Int_fdiv(5)
    print b
    print b - 4
    print 4 - b
    print (1+1*b)/7
    print 7/(1*b)

def __test_simplify_points():
    line = [(0,0),(1,0),(2,0),(2,1),(2,2),(1,2),(0,2),(0,1),(0,0)]
    print simplify_points(line, 1.0)

def __test_nice_int():
    for i in range(998,1001):
        print nice_int(i)
    for i in range(999999,1000002):
        print nice_int(i)

def __test_guess():
    d = {'sdql':['AD'],'line':'-7.5','total':'54.','line':''}
    print "guess: %s"%guess_types(d)

def __test_in_parens():
    t = "(This is (all of it) in parens)"
    print t, in_parens(t)

    t = "(This is) (all of it) not (in parens)"
    print t, in_parens(t)

def __test_clear_small_files():
    clear_small_files("/home/jameyer/S2/MLB/Data/Covers/Schedule/_Raw/2014*",30000)

if __name__ == "__main__":
    pass
    #__test_clear_small_files()
    #__test_in_parens()
    #__test_guess()
    #__test_nice_int()
    #__test_simplify_points()
    #__test_fdiv()
    #__test_date8()
    #__test_Float()
    #__test_probability()
    #__test_date_range()
    #__test_all_combinations()
    #__test_value_from_string()
    #__test_common_type()
    #__test_random_cohort()
    #__test_random_subset()
    #__test_split()
    #__test_tuple_of_tuples_from_txt()
    #__test_add_colors()
    #__test_probability()
    #__test_day_from_date()
    #__test_importer()
    #__test_remove_duplicates()
    #print link(sdql='HD',**{'ouput':'my'})
    #print yyyymmddhhmm()
    #print date_from_string(" [21/Feb/2016:13:08:52 -0500])")
    #print time_from_string(" [21/Feb/2016:13:08:52 -0500])")
    print 'nd',nice_date(20170922,abbreviate_month=0,abbreviate_year=0)
    print 'nd',nice_date(20170922,abbreviate_month=1,show_year=0)

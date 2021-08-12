from sys import path as sys_path # imports go to the namespace of the query
from sys import exc_info as sys_exec_info
import string
import math
import re
import time

sys_path[:0] = ["/home/jameyer/PyQL2/Source"]
#import columns, py_tools, outputs
import PyQL.py_tools as py_tools
import PyQL.outputs as outputs
import PyQL.columns as columns

import ply.lex as lex
from dt_yaccer import parser
import dt_ply_lexer
import columns


class Field:
    def __init__(self):
        pass

class DT:

    def __init__(self,
                  data=None,
                  name=None,
                  top_metacode_lines=[],
                  verbose=0,
                  update_cache_on_change_offset = None,
                  build_lexer = True, #don't want to do this for result DT
                  db_strings = []
                  ):
        self.update_cache_on_change_offset = update_cache_on_change_offset
        self.db_strings = db_strings # eg ['Cubs','White Sox']
        self.timer = 0 # set timer on the query loop
        self.print_exceptions = 0 # print exception in query loop
        self.has_squarebracket = 0 # an internal summative has square bracket
        self.has_squarebracket_in_condition = 0 # triggers update on change
        self.verbose = verbose
        self.name = name
        self.data = data or []
        self.headers = []
        self.header_dict = {}
        self.show_metacode = False
        self.top_metacode_lines = top_metacode_lines #  aliases and joins
        for col in self.data: self.headers.append(col.name)
        if self.data and build_lexer:
            self.build_lexer()
        if self.data:
            self.build_header_dict()

    def build_header_dict(self):
        self.header_dict = {}
        for h in range(len(self.headers)):
            self.header_dict[self.headers[h]] = h

    def build_lexer(self,filename=None,parameters=None):
        parameters = (parameters or self.headers[:])
        lex_txt = open('/home/jameyer/PyQL2/Source/dt_ply_lexer.py').read()
        parameters.sort(lambda x,y:cmp(len(y),len(x)))
        parameters = '|'.join(parameters)
        if self.verbose: print "parameter :",parameters
        parameters = string.replace(parameters,' ','\ ')
        db_strings = "|".join(self.db_strings) # words we don't want to bother quoting
        db_strings = string.replace(db_strings," ","\ ")
        if parameters:
            lex_txt = string.replace(lex_txt,
                                 "__YOUR PARAMETERS HERE__",parameters)
        if db_strings:
            lex_txt = string.replace(lex_txt,
                                 "__YOUR STRINGS HERE__",db_strings)
        filename = filename or "lexer_%s.py"%abs(hash(
                                              parameters + db_strings))
        open('/home/jameyer/PyQL2/Source/Lexers/%s'%filename,'w').write(lex_txt)
        sys_path[:0] = ["/home/jameyer/PyQL2/Source/Lexers"]
        lex_file = __import__(filename[:-3])
        self.lexer = lex_file.lexer

    def __str__(self):
        ret = "DT Instance Named `%s` with %d Columns\n\n"%(
            self.name,len(self.data))
        for d in self.data:
            ret += "%s\n%s\n%s\n"%(d.name,'-'*len(d.name),str(d),)
        return ret
    __repr__ = __str__
    def __getitem__(self, idx):
        return self.data.__getitem__(idx)

    def __len__(self):
        return self.data.__len__()

    def append(self, obj):
        #print "append.obj:",obj,type(obj)
        #assert len(obj) == len(self.data)
        for i  in range(len(self.data)):
            self.data[i].append(obj[i])

    def append_on_change(self,on_change_value,values):
        if self.verbose:
            print "appending (on change of %s) %s with %s"%(on_change_value,`self.name`,values)
        for i in range(len(values)):
            # each column object has an append_on_change method
            self.data[i].append_on_change(on_change_value,values[i])

    def append_pending(self,on_change_value):
        for i in range(len(self.data)):
            # each column object has an append_pending method
            self.data[i].append_pending(on_change_value)

    def value_from_header(self,header,default=None):
        offset = self.offset_from_header(header)
        if offset is None: return default
        #print "vfh: self.name:",self.name
        #print "vfh: data[offset]",self.data[offset]
        return self.data[offset] #.value()

    def code_access_from_word(self,word):
        """ subclass this for short cuts etc.
             Python's None and methods (string.upper) are handled here also
        """
        #print "sef.name:","parm:",parameter,"headers:",self.headers
        #print "quoting word:",word
        #return "'%s'"%word
        return word

    def code_access_from_parameter(self,parameter):
        """ subclass this to build (eg) top_metacode from joins
            and use join indices such as tp, PPo,
            and other tables such as player stats, district, ...
        """
        #print "sef.name:","parm:",parameter,"headers:",self.headers
        return "_d[%d][_i]"%self.offset_from_header(parameter)

    def parse_fields(self,fields):
        f = 0
        for field in fields:
            f += 1
            print "field_%d"%f,field
            term,term_type = field
            print "term:",term

    def query(self, pyql, default_fields = None, indices=None):
        parsed = parser.parse(pyql,lexer=self.lexer,debug=1)
        print "pyql:",pyql
        self.parse_fields(parsed.fields)
        #print "fields:"
        #for item in parsed.fields: print item
        #print "condition_terms:"
        #for item in parsed.condition_terms: print item

def test_ply(txt,lexer):
    result = parser.parse(txt,lexer=lexer,debug=1)
    print "text:",txt
    print "fields:"
    for item in result.fields:
        print item
    print "condition_terms:"
    for item in result.condition_terms:
        print item

# build and return a sample dt
def test_dt():
    c1 = columns.Column(name="height",format="""lambda h:"%0.0f'%0.0f''"%(int(h)/12,int(h)-12*(int(h)/12))""")
    c2 = columns.Column(name="weight",format="""lambda w:'%d\#'%w""")
    c3 = columns.Column(name="first name",format="%s")
    c4 = columns.Column(name="age",format="%s")
    c5 = columns.Column(name="children",format="%s")
    dt = DT(data = (c1,c2,c3,c4,c5),name="test table",db_strings=['mike'])
    c1.append(65);c2.append(180);c3.append(None);c4.append(23);c5.append(['al'])
    c1.append(69);c2.append(150);c3.append("mike");c4.append(43);c5.append(['mary','ed'])
    c1.append(70);c2.append(190);c3.append("ike");c4.append(72);c5.append(['marty','ned','john']) # '''
    dt.verbose = 0
    return dt

def test_query(dt):
    dt.show_metacode = 1
    dt.verbose = 0
    dt.update_cache_on_change_offset = None
    pyql = "Sum(age as Age@weight>0,N=2),Sum(age as Age+height) / Average(weight as 'Heft'@age as Age>2 and weight>0) @ Sum(age@1>0)[1>0]"
    #pyql = "age @Sum(age as Age@height>0,N=1) > 0"
    #pyql = "Average(weight as W)[age and height>0] @age and height>0"
    #pyql = "1*Sum(height,format='%f')-Sum(weight,N=2,format='%s,')@weight>0"
    #pyql = "age@(weight>100),(weight>160)"
    #pyql = "age@weight>100,160 and Average(height)>0 and first name.upper()"
    #pyql = "hits as H/runs as 'R'@(team=Bears),math.foo(site=home),1"
    print "pyql:",pyql
    dt.query(pyql)





if __name__ == "__main__":
    dt = test_dt()
    test_query(dt)

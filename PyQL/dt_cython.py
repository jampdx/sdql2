#!/usr/bin/env python
from __future__ import division

from iterools import izip, chain

import traceback
import time
#import cython
import sys
sys.path.append('/usr/lib64/python2.7/site-packages')

import re
DATA_DIR = '/home/cgw/Work/SDB/Data'
exc_count = 0 # global

# imports go to the namespace of the query.  To get into the namespace of column.value lambda functions need to import from columns.py
from sys import path as sys_path
from sys import exc_info as sys_exec_info
import string
import math
import random
import re
import time
import os
import sys
from ply import lex

use_cython = os.environ.get("USE_CYTHON") is not None

#sys_path[:0] = ["/home/jameyer/PyQL2/Source"]
#import columns,dt py_tools, outputs

sys.path.insert(0, "/home/cgw/Work/SDB/")

import PyQL.columns
import PyQL.outputs
import PyQL.py_tools
import PyQL.dt_lexer
import PyQL.safe_ast_query
#import PyQL.dt

from PyQL.py_tools import all_combinations

from PyQL.dt_lexer import COMMA_TOK, ONE_TOK, AT_TOK,L_PAREN_TOK,R_PAREN_TOK

if __name__ != "__main__":
    TOP_DIR = os.path.dirname(os.path.realpath( __file__ ) )
else: TOP_DIR = "/home/jameyer/PyQL2/Source"

NUMBER_TYPES = [int,float]

SPACE_PAT = re.compile("[\s]+")
SPACE_DOT_PAT = re.compile("[\s]+\.")
AS_CONDITION_PAT = re.compile("[\s]*=[\s]*%s\"\"\"%\([^,]+,\)")
AS_CONDITION_SPLIT = re.compile("[\s]*=[\s]*%s")

def common_conditions(conditions):
    if len(conditions) < 2:  # "I don't have anything in common with myself" - Kafka
        return []
    conditions = map(lambda x:x[0],conditions)
    len_conditions = len(conditions)
    parts = map(lambda x:x.split(' and '),conditions)
    same_parts = []
    for (p,part) in enumerate(parts[0]):
        all_same = 1
        for c in range(1,len(conditions)):
            if part != parts[c][p]:
                all_same = 0
        if all_same:
            same_parts.append(part)
    return same_parts



def as_condition_from_metacode(mc):
    # parsing the parse: an ugly wart
    # 'r"""weight = %s"""%(_d[1][_i],)'  for group by
    # 'r"""weight>0"""' for conditional
    #print "acfm gets:",mc
    parts = mc.split('"""')
    r = []
    for p in range(len(parts)):
        if not p%2: continue
        r.append(AS_CONDITION_SPLIT.split(parts[p])[0])
    #print "acfm retruys:",' '.join(r)
    return ' '.join(r)

def XXas_condition_from_metacode(mc):
    #print "mcin:",mc
    # 'r"""weight = %s"""%(_d[1][_i],)'  for group by. or even:
    # 'r"""[65 + age , 69] = %s"""%([ 65 + ((_d[3][_i] is not None or None)*_d[3][_i]) , 69],),r"""and""",r"""[23 , 43] = %s"""%([ 23 , 43],)'
    # 'r"""weight>0"""' for conditional
    mc = re.sub(AS_CONDITION_PAT,'"""',mc)
    print "mcsubed:",mc
    return ' '.join(eval("(%s,)"%mc))

def nice_header(header):
    ret = header
    ret =  SPACE_PAT.sub(' ',ret)
    ret =  SPACE_DOT_PAT.sub('.',ret)
    return ret

def split_args(guts):
    # take the inside of an aggregator an find the args
    # egs: Sum(points,N=3),Maximum((points,fouls),N=4)
    fields = args = ""
    lp = 0
    lc = 0 # watch out for {
    after_comma = False
    for c in guts:
        if not after_comma and lp == lc == 0 and c == ',':
            after_comma = True
            continue
        if c == '(': lp += 1
        if c == ')': lp -= 1
        if c == '{': lc += 1
        if c == '}': lc -= 1
        if after_comma: args += c
        else: fields += c
    return fields,args

class DT_Error(Exception):
    """Raised when lex has parsing failure.
    """

class Condition(tuple):
    list_vals = []
    def __init__(self,data):
        tuple.__init__(data)
        self.code = self[0]
        self.pyql = self[1]
        self.as_term = self[2]

class Field(object):
    def __init__(self,as_terms, code_terms, pyql_terms,
                 has_non_summative,n_field_caches,
                 has_squarebracket,has_comparator):
        #print "Field.init with as, code, nfc, hns:",as_terms,code_terms,n_field_caches, has_non_summative
        self.has_squarebracket = has_squarebracket
        self.has_comparator = has_comparator
        self.args = ''
        self.alias = nice_header(' '.join(as_terms))   # used in init result
        self.code_terms = code_terms  # code/aggregator to pass update result
        self.pyql_terms = pyql_terms
        self.as_terms = as_terms
        self.aggregators = filter(lambda ct:type(ct) is not str,code_terms)
        self.len_aggs = len(self.aggregators)
        #print "Fields.len_aggs:",self.len_aggs
        self.n_field_caches = n_field_caches # start val for numbering cache
        self.has_non_summative = has_non_summative #this + a summative triggers a running sum and the use of field_cache
        self.parse_code()

    def parse_code(self):
        self.use_has_non_summative = self.has_non_summative
        # 20110728 comment following one line out for 10% speed up of query loop at the cost of not allowing mixed summative and non in methods.
        # eg: (Average(age),weight)@1 works fine with this line in. without this line would need to use (Average(age), Replace(weight))
        # the quicker way builds compound values in column.value lambda function and thus also requires any methods used to be imported in columns.py
        # the slower way gets rid of a lot of code in this method
        if len(filter(lambda x:type(x) is not str or x.strip()!='',self.code_terms)) > 1: # a space is not really another term
            self.use_has_non_summative = 1  # ie if there is more than one term (and a summative is used) always use the field_cache
        # determine the meta code for update and init
        # deal with field_cache
        self.value_terms = [] # how to build value from Tuple((Sum(A)/Sum(B)))
        self.flavor = 'Column'
        update_terms = []  # metacode to update the result
        field_caches = 0 # self.n_field_caches # globa number of field caches
        #print "F.pc: staring field_caches:",self.n_field_caches
        self.tuple_index = 0
        #print "F.parse_code.code_terms (%d)"%len(self.code_terms),self.code_terms
        for term in self.code_terms :
            #print "parse_code.code_term",term
            if type(term) is str:      # not a summative
                if self.len_aggs > 1 and not self.use_has_non_summative:
                    # use to build Tuple value
                    self.value_terms.append(term)
                else:
                    update_terms.append(term)
                continue
            # for multiple summatives set global args to last summative args
            self.args = term.fields[0].args
            #print "self.args:",self.args
            # current term is a summative
            if self.len_aggs == 1 and not self.use_has_non_summative and not self.has_squarebracket: # this is the only aggregator
                self.flavor = term.fields[0].flavor
            if  self.use_has_non_summative and term.fields[0].flavor == 'Column':
                term.fields[0].flavor = 'Replace'
            if (self.len_aggs>0 and self.use_has_non_summative) or self.has_squarebracket:    # running sum
                update_terms.append('self.field_values[%d].get(_key)'%(field_caches+self.n_field_caches))
                #print "update_ters:",update_terms
                field_caches += 1
                #if not self.has_non_summative: self.flavor = 'Replace'
                if not self.has_non_summative: self.flavor = 'Replace'
                continue

            if self.len_aggs > 1 or self.has_squarebracket:
                self.value_terms.append('s.data[%d].value()'%self.tuple_index)
                self.tuple_index += 1
                self.flavor = 'Tuple'
                #print "flavor is Tuple"
            #print "term.conditions:",term.conditions
            if term.conditions[0][0] != "True":
                update_terms.append("((%s) or None) and %s"%(
                    term.conditions[0][0],term.fields[0].update))
            else:
                update_terms.append(term.fields[0].update)

        if self.tuple_index > 0:
            self.update = '('
            for i in range(len(update_terms)):
                self.update += "_safe_update_term_%d,"%i
                self.safe_update_terms = update_terms
            self.update += ')'
        else:
            self.safe_update_terms = []
            self.update = ' '.join(update_terms)

        #print "Fields.field_caches:",field_caches
        #print "Fields.aggregators:",self.aggregators
        if field_caches:
            self.cache = []
            for agg in self.aggregators:
                #agg.fields[0].flavor = agg.flavor
                #print "appending Field.cache with agg:",agg
                self.cache.append(agg)

        else: self.cache = []

    def init_code(self):
        data = ''
        tuple_value = ''
        if self.tuple_index:
            if self.value_terms:
                tuple_value = ",value='''lambda s=self:%s'''"%' '.join(self.value_terms)
            else: tuple_value = ''
            data = 'data=('
            for agg in self.aggregators:
                args = ''
                if agg.fields[0].args: args = "," + agg.fields[0].args
                data += r'PyQL.columns.%s(name="""%s"""%s),'%(
                    agg.fields[0].flavor,'foo',args)
            data += r'),'

        outer_args = "," + self.args
        # for these synthetics pass through only format to outer args
        if self.args and self.flavor in ["XReplace","XTuple","XColumn"]:
            largs = []
            for arg in string.split(self.args,","):
                if string.strip(string.split(arg,"=")[0]) != "format":
                    continue
                largs.append(arg)
            outer_args = "," + ",".join(largs)
        if string.strip(outer_args) == ",": outer_args = ''
        #print "outer_args:",outer_args
        #print "tuple_value",tuple_value
        return r'PyQL.columns.%s(%sname="""%s"""%s%s),'%(self.flavor,data,
                                       self.alias,outer_args,tuple_value)
    def __repr__(self):
        return ("Field.flavor:%s\n"%self.flavor +
         "Field.alias:%s\n"%self.alias +
         "Field.update:%s\n"%self.update +
         "Field.cache:%s\n"%self.cache +
         "Field.aggregarore:%s\n"%self.aggregators +
         "Field.init_code:%s"%self.init_code() )

class ConditionList(list):
    has_comparator = 0

class DT(object):

    def __init__(self,
                 data=None,
                 name=None,
                 top_metacode_lines=[],
                 verbose=0,
                 update_cache_on_change_offset = None,
                 build_lexer = True, #don't want to do this for result DT
                 db_strings = [], # quote these in metacode
                 alias_d = {},     # search for keys like parameters and shortcut to these aliases in code_from_parameter (often of form: Europe: self.Europe)
                 #preallocate = 0
    ):
        self.alias_d = alias_d
        self.is_function = 0
        self.update_cache_on_change_offset = update_cache_on_change_offset
        self.db_strings = db_strings # eg ['Cubs','White Sox']
        self.timer = 0 # set timer on the query loop
        self.print_exceptions = 0 # print exception in query loop
        self.has_squarebracket = 0 # an internal summative has square bracket
        self.has_squarebracket_in_condition = 0 # triggers update on change
        self.verbose = verbose
        self.name = name
        self.data = data or []
        #if preallocate:
        #    self.data = np.empty(preallocate, dtype=object) # experimental!
        self.headers = []
        self.header_dict = {}
        self.show_metacode = False
        self.top_metacode_lines = top_metacode_lines #  aliases and joins
        for col in self.data: self.headers.append(col.name)
        if self.data and build_lexer:
            self.build_lexer()
        if self.data:
            self.build_header_dict()

    def del_column(self,index,rebuild_header_dict=1):
        if index>len(self.data)-1: raise Exception("Index out of range for DT.__del__")
        del self.data[index]
        del self.headers[index]
        if rebuild_header_dict: self.rebuild_header_dict()

    def build_header_dict(self):
        self.header_dict = {}
        for h in range(len(self.headers)):
            self.header_dict[self.headers[h]] = h

    def XXbuild_lexer(self,filename='',parameters=[],db_string_pat=''):
        #,alias_condition_pat='',alias_reference_pat=''):
        parameters = (parameters or self.headers[:])
        lex_txt = open(os.path.join(TOP_DIR,'dt_lexer.py')).read()
        parameters.sort(lambda x,y:cmp(len(y),len(x)))
        parameters = '|'.join(parameters)
        if self.verbose: print "parameter :",parameters
        parameters = string.replace(parameters,' ','\ ')
        db_strings = db_string_pat or "|".join(self.db_strings) # words we don't want to bother quoting
        db_strings = string.replace(db_strings," ","\ ")
        #if alias_condition_pat:
        #    lex_txt = string.replace(lex_txt,
        #                         "__YOUR_ALIAS_CONDITIONS HERE__",alias_condition_pat)
        #if alias_reference_pat:
        #    lex_txt = string.replace(lex_txt,
        #                         "__YOUR_ALIAS_REFERENCES HERE__",alias_reference_pat)
        if parameters:
            lex_txt = string.replace(lex_txt,
                                 "__YOUR PARAMETERS HERE__",parameters)
        if db_strings:
            lex_txt = string.replace(lex_txt,
                                 "__YOUR STRINGS HERE__",db_strings)
        filename = filename or "lexer_%s.py"%abs(hash(
                                              parameters + db_strings))
        if not os.path.isfile(filename):
            open(os.path.join(TOP_DIR,"Lexers",filename),'w').write(lex_txt)
        sys_path[:0] = [os.path.join(TOP_DIR,"Lexers")]
        lex_file = __import__(filename[:-3])
        self.lexer = lex_file.lexer

    def build_lexer(self,parameters=[],db_string_pat=''):
        #,alias_condition_pat='',alias_reference_pat=''):
        parameters = (parameters or self.headers[:]) + self.alias_d.keys() # alias_d added 20141025
        parameters.sort(lambda x,y:cmp(len(y),len(x)))

        parameters = map(lambda x:x+"(?![a-zA-Z_])",parameters) # 20130806: add negative look ahead so parameters don't match part of a string.
        parameters = '|'.join(parameters)
        if self.verbose: print "parameter :",parameters
        parameters = string.replace(parameters,' ','\ ')
        db_strings = db_string_pat or "|".join(self.db_strings) # words we don't want to bother quoting
        db_strings = string.replace(db_strings," ","\ ")
        if parameters:
            PyQL.dt_lexer.t_PARAMETER.__doc__ = parameters
        if db_strings:
            PyQL.dt_lexer.t_DB_STRING.__doc__ = db_strings

        self.lexer = lex.lex(module=PyQL.dt_lexer)

    def as_dict(self):
        ret = {}
        for dt in self:
            #print 'dt',dt
            ret[dt.name] = dt.data
        return ret

    def __str__(self):
        ret = "DT Instance Named `%s` with %d Columns\n\n"%(
            self.name,len(self.data))
        for d in self.data:
            ret += "%s\n%s\n%s\n"%(d.name,'-'*len(d.name),str(d),)
        MAXLEN = 10000
        if len(ret) > MAXLEN:
            ret = ret[:MAXLEN] + ("...(%d more bytes)" % (len(ret)-MAXLEN))
        return ret
    __repr__ = __str__

    def __getitem__(self, idx):
        return self.data[idx]

    def __len__(self):
        return len(self.data)

    def append_dt(self,other):
        for sd, od in izip(self.data, other.data):
            sd.data += od.data
        #for i in range(len(self.data)):
        #    #print "append",self.data[i].data
        #    self.data[i].data += other.data[i].data

    def append(self, row):
        for sd, r in izip(self.data, row):
            sd.append(r)

        #for i in xrange(len(self.data)):"
        #    self.data[i].append(row[i])


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

    def value_from_header_with_owners(self,header,default=None,owners=None):
        offset = self.offset_from_header_with_owners(header,owners)
        if offset is None: return default
        return self.data[offset] #.value()

    def offset_from_header_with_owners(self, header,owners=None):
        #print "ofh request",header
        # first owner defaults to '' (naked parameter) then self.owners ordered as passed in to  __init__
        if owners is None:
            owners = [''] + self.owners
        for owner in owners:
            if owner: oheader = "%s.%s"%(owner,header)
            else: oheader = header
            if self.header_dict.get(oheader) is not None:
                return self.header_dict[oheader]
        return None

    def value_from_header(self,header,default=None):
        offset = self.offset_from_header(header)
        if offset is None: return default
        return self.data[offset] #.value()

    #def code_access_from_alias_condition(self,alias):
    #    """ subclass this for references to a conditional term made up of parameters or combinations of parameters
    #    """
    #    return alias

    #def code_access_from_alias_reference(self,alias):
    #    """ subclass this for references to parameters or combinations of parameters
    #    """
    #    return alias

    def XXXcode_access_from_word(self,word): # 20110804: inside functions leave alone else quote
        """ subclass this for short cuts etc.
             Python's None and methods (string.upper) and lambda x:x are handled here also
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
        if self.alias_d.has_key(parameter): return self.alias_d[parameter]
        return "_d[%d][_i]"%self.offset_from_header(parameter)

    def parse_aggregator(self,t_val,has_squarebracket=0,
                         is_function=0,name='aggregator',n_field_caches=0):
        # append self.aggregators so we know how to update cache
        # and return the aggregator dt
        #print "parse_aggre gets:",t_val," and is_function:",is_function
        ag_dt = DT(name=name,build_lexer=False)
        ag_dt.is_function = is_function
        ag_dt.has_squarebracket = has_squarebracket
        ag_dt.headers = self.headers
        ag_dt.condition_cache = self.condition_cache #? for nested ??
        ag_dt.header_dict = self.header_dict
        ag_dt.lexer = self.lexer.clone()
        ag_dt.code_access_from_parameter = self.code_access_from_parameter # need subclass
        flavor,guts = string.split(t_val,'(',1)
        guts = guts[:-1] # last ')'
        if not is_function and "," in guts:
            guts,args = split_args(guts)
        else: args = ''
        #print "parse_aggregator: flavor,guts,args:",flavor,'|',guts,'|',args
        ag_dt.parse(guts,n_field_caches=n_field_caches)
        ag_dt.flavor = flavor           # for is_function
        ag_dt.fields[0].flavor = flavor # for aggregator
        ag_dt.args = args
        ag_dt.fields[0].args = args
        #print "parse_aggregator: flavor,guts,args,fields:",flavor,'|',guts,'|',args,'|',ag_dt.fields
        #print "ag_dt.fields[0].args:",args
        return ag_dt

    def parse_fields(self,toks,n_field_caches=0):
        """ PF: use field toks to find fields:
                need to know how to init and with what to update
        """
        fields = [] # [Field,... ]
        code_terms = []
        pyql_terms = []
        as_terms = []
        has_non_summative = False
        after_as = False
        #n_field_caches = 0  # total number of field caches: needed for indexing in Field
        field_has_squarebracket = 0
        field_has_comparator = 0
        as_is = 1   # copy pyql to as
        seen_as = 0 # clear as from pyql upon seeing the first as
        open_paren = 0 # when closed handle possible AS
        len_toks = len(toks)
        children_cache = []
        t = -1
        while True: # break on '@'
            t += 1
            tok = toks[t]
            #print "field tok",tok
            if t+1<len_toks: next_tok = toks[t+1]
            else: next_tok = None
            if self.verbose: print "field t - tok:%d - %s"%(t,tok)
            t_val = tok.value
            if not open_paren and t_val in ['@',','] and tok.type != 'STRING':
                #print "time to build Field for",pyql_terms, code_terms
                #print "pre n_field_caches:",n_field_caches
                field = Field(as_terms,code_terms,pyql_terms,
                              has_non_summative and not self.is_function,
                              n_field_caches,
                              field_has_squarebracket,
                              field_has_comparator)
                #print "fc:",field.cache
                field.cache = children_cache + field.cache
                fields.append(field)
                n_field_caches += len(field.cache)
                #print "post n_field_caches:",n_field_caches
                if t_val == '@': break
                children_cache = []
                code_terms = [];pyql_terms = [];as_terms = [];
                has_non_summative = False
                field_has_square_bracket = 0; field_has_comparator = 0
                seen_as = 0; as_is = 1; after_as = False;

            elif after_as:
                if t_val == 'is':
                    as_is = 1
                    as_terms += [pyql_terms[-1]]
                else:
                    # need to gobble tokens upto next `,` or `@`
                    if not seen_as: as_terms = [t_val]
                    elif as_is: as_terms[-1] = t_val
                    else: as_terms.append(t_val)
                    if tok.type == "STRING":
                        after_as = 0 # 20110730 allow age as 'A' + weight as 'W
                        as_is = 1
                    else:
                        as_is = 0
                seen_as = 1
                continue
            elif tok.type == 'PARAMETER':
                code_terms.append(self.code_access_from_parameter(t_val))
                pyql_terms.append(t_val)
                if as_is: as_terms.append(t_val)
            elif tok.type == 'WORD':
                # eg: for `map(lambda x:x[0],foo)` don't want to quote lambda or x
                #print "n,v:",self.name,t_val
                #if self.name == "python_function": # or t_val != t_val.title():
                if self.name in ["python_function","python_tuple"]: # 20130325: added python_tuple to fix lambda x:(x>0) ==> lambda x:('x'>0)
                    code_terms.append(t_val)
                else:  code_terms.append("'%s'"%t_val)
                pyql_terms.append(t_val)
                if as_is: as_terms.append(t_val)
            elif tok.type in ['PYTHON_FUNCTION','SQUARE_BRACKET']:
                if tok.type == 'PYTHON_FUNCTION':
                    open_symbol,close_symbol = '(',')'
                    temp_val = t_val
                    if t_val.strip()[0] == '(':
                        name = "python_tuple"
                    else: name = "python_function"
                    #print "tval:",t_val,"name:",name
                else:
                    open_symbol,close_symbol = '[',']'
                    temp_val = '(' + t_val[1:-1] + ')'
                    name = "square_bracket"
                temp_ag = self.parse_aggregator(temp_val,is_function=1,name=name,n_field_caches=n_field_caches)
                code_terms.append( temp_ag.flavor + open_symbol)
                as_terms.append( temp_ag.flavor + open_symbol)
                pyql_terms.append( temp_ag.flavor + open_symbol)
                for field in temp_ag.fields:
                    if field.has_non_summative:
                        has_non_summative=True
                    if field.has_comparator:
                        field_has_comparator=field.has_comparator #True
                    code_terms += field.code_terms + [',']
                    as_terms += field.as_terms + [',']
                    pyql_terms += field.pyql_terms + [',']
                code_terms[-1] = code_terms[-1][:-1]
                code_terms.append(close_symbol)
                as_terms[-1] = as_terms[-1][:-1]
                as_terms.append(close_symbol)
            elif tok.type == 'AGGREGATOR':
                #print "found field agg"
                if next_tok and next_tok.type == "SQUARE_BRACKET":
                    t += 1 # skip this square bracket
                    field_has_squarebracket = 1
                    ag_has_squarebracket = 1
                    read_ag =  self.parse_aggregator("Sum(1@%s)"%(
                        next_tok.value[1:-1]),has_squarebracket=1,n_field_caches=n_field_caches)
                    read_key = read_ag.conditions[0].pyql
                else:
                    ag_has_squarebracket = 0
                    read_key = ''
                #print "parse_fields parsing agg for tval:",t_val
                code = self.parse_aggregator(t_val,ag_has_squarebracket,n_field_caches=n_field_caches)
                for field in code.fields:
                    children_cache += field.cache
                #print "parse fiels agg for code.field[0]:",code.fields[0]
                code_terms.append(code)
                pyql_terms.append(t_val)
                if as_is:
                    square_as = ''
                    if ag_has_squarebracket:
                        square_as = "[%s]"%as_condition_from_metacode(read_ag.conditions[0][-1])
                    arg_as = ''
                    if code.args:
                        arg_as = ",%s"%code.args
                    c_as_term = ''
                    if str(code.conditions[0][0]) != 'True':
                        c_as_term += "@%s"%(as_condition_from_metacode(code.conditions[0][-1]))
                    as_terms.append("%s(%s%s%s)%s"%(code.fields[0].flavor,code.fields[0].alias,c_as_term,arg_as,square_as))
                code.fields[0].read_key = read_key
            elif tok.type in ['STRING','DB_STRING']:
                code_terms.append(r"'%s'"%t_val)
                pyql_terms.append(t_val)
                if as_is: as_terms.append(t_val)
            elif tok.type in ['COMPARATOR'] and self.name not in ["python_function"]:
                field_has_comparator = t_val #1
                if t_val == '=': code_terms.append("==")
                else: code_terms.append(t_val)
                pyql_terms.append(t_val)
                if as_is: as_terms.append(t_val)
            elif tok.type == 'AS':
                after_as = True
            else:
                code_terms.append(t_val)
                pyql_terms.append(t_val)
                if as_is: as_terms.append(t_val)
            if tok.type in ["PARAMETER","INTEGER","FLOAT"]:
                has_non_summative = True  # field flavor => Column
            elif tok.type == '(':
                #raise "is paren paradigm usurped by funciton?"
                open_paren += 1
            elif tok.type == ')':
                open_paren -= 1
        return fields

    def parse_conditions(self,toks):
        """ After the @.
        first loop:
           break up into conjunction delimited terms,
           handle comma groups, and
           flag as statements (implicit groups) or conditionals.
        """
        self.verbose = 0
        condition_tok_terms = [] # eg [ [[points],[>],[20]],[[and]],[[50,60,..],[<],[yards]],...]]
        tok_terms = ConditionList()
        after_comma = False; after_as = False
        open_paren = 0
        open_paren_tok_terms_offset = {}  # {number of open parens:off set of tok_terms}
        len_toks = len(toks)
        t = -1
        while t < len_toks-1:
            t += 1
            tok = toks[t]
            #print "pc.tok:",tok
            #print "after_as:",after_as
            if t+1<len_toks: next_tok = toks[t+1]
            else: next_tok = None
            t_val = tok.value; t_type = tok.type
            tok.as_term = ''
            if self.verbose: print "condition tok: %s"%(tok,)
            if after_comma and t_type == "SPACE": continue
            if after_as:
                if not tok_terms: # as on a conjunction
                    condition_tok_terms[-1][-1][-1].as_term = t_val
                elif tok_terms[-1][-1].value == ')':
                    tok_terms[-1][-1].as_term = t_val
                    for c_tok_terms in condition_tok_terms[open_paren_tok_terms_offset[open_paren+1]:] + [tok_terms[:-1]]:
                      for tterm in c_tok_terms:
                        for tt in tterm:
                            tt.as_term = ' '
                else:
                    tok_terms[-1][-1].as_term = t_val
                    # 20120918: following 3 lines removed since: `age as goo + age as foo` only captured `as foo`
                    #for tterm in tok_terms[:-1]:
                    #    for tt in tterm:
                    #        tt.as_term = ' '
                after_as = False
                continue
            if tok.type == '(':
                #raise "is paren ever used or usurped by PYTHON_FUNCTION?"
                open_paren += 1
                open_paren_tok_terms_offset[open_paren] = len(condition_tok_terms)
                #print "setting open_paren_tok_terms_offset[open_paren] to",condition_tok_terms,len(condition_tok_terms)
                #continue
            elif tok.type == ')':
                open_paren -= 1
            elif t_val == ',' and not open_paren and not self.is_function:
                after_comma = True
                continue
            elif t_type == 'AS':
                after_as = True
                continue
            elif t_type == "CONJUNCTION":
                condition_tok_terms.append(tok_terms)
                temp = ConditionList()
                temp.has_comparator = 1 # 'and' is not an implicit group by
                tok.as_term = t_val
                temp.append([tok])
                condition_tok_terms.append(temp)
                tok_terms = ConditionList()
                continue
            elif t_type in ["COMPARATOR"]:
                #print "ttpye is comp"
                if t_val == '='  and (not self.is_function or self.name == 'python_tuple'):
                    t_val = '=='
                    tok.as_term = '='
                    #print "ttpye is comp and tal .."

                tok_terms.has_comparator = t_val
            if after_comma:
                #print "after comma. tok terms were:",tok_terms
                tok_terms[-1].append(tok)
                #print "                and now are:",tok_terms
            else:
                tok_terms.append([tok])
            if not open_paren:
                after_comma = False
        condition_tok_terms.append(tok_terms)
        #print "ctokterms:",condition_tok_terms
        tuple_conditions = []
        for tok_terms in condition_tok_terms: # and|or delimted
            #print "tterms:",tok_terms
            #print "toktermns (%d)"%len(tok_terms),tok_terms,"first one as_term:",tok_terms[0][0].as_term
            code_val_as_terms = [] # [(code,val,as_term)] or  [(code,val,as_term),(code,val,as_term), ..]
            skip_squarebracket = 0
            for t in range(len(tok_terms)):
                toks = tok_terms[t]
                #print "toks:",toks
                cva = []
                for tok in toks:
                    #print "tok:",tok,"tok.as_term:",tok.as_term or "NO AS TERM","type:",tok.type
                    t_type = tok.type; t_val = tok.value; t_as_term = tok.as_term
                    if t_type == 'COMPARATOR' and t_val == '=' and (not self.is_function or self.name=='python_tuple'):t_val = '=='
                    if t_type == "SQUARE_BRACKET" and skip_squarebracket:
                        skip_squarebracket = 0
                        continue

                    elif tok.type in ['PYTHON_FUNCTION','SQUARE_BRACKET']:
                        if tok.type == 'PYTHON_FUNCTION':
                            open_symbol,close_symbol = '(',')'
                            if string.replace(t_val,' ','')[-2] == ",": close_symbol = ",)" # ',)' is referenced below so look out!
                            temp_val = t_val
                            if t_val.strip()[0] == '(': name="python_tuple"
                            else: name="python_function"
                        else:
                            name = "square_bracket"
                            open_symbol,close_symbol = '[',']'
                            temp_val = '(' + t_val[1:-1] + ')'
                        temp_ag = self.parse_aggregator(string.replace(temp_val,'(',"(1@_foo as ' '== as ' '",1) , is_function=1,name=name)
                        code = temp_ag.flavor + open_symbol
                        cond = temp_ag.conditions[0]
                        #print "cond",cond
                        #print "cond_as",cond.as_term
                        #print "tasterm:",t_as_term
                        if not t_as_term:
                            eval_as = eval(cond.as_term)
                            if type(eval_as) is str: str_as = eval_as
                            else: str_as = ' '.join(eval_as)
                            t_as_term = temp_ag.flavor+"%s%s%s"%(open_symbol,str_as,close_symbol)
                        # want to make (age>23) a comparison and leave (age,), (age+height), (age>23,weight) all as group-by
                        if name == 'python_tuple' and close_symbol != ',)':  # this would always be an implicit group by
                            test_code =  " (%s@1) "%temp_val.strip()[1:-1]
                            test_ag = self.parse_aggregator(test_code,name="test for simple paren",is_function=1)
                            if len(test_ag.fields) == 1 and test_ag.fields[0].has_comparator:
                                tok_terms.has_comparator = 1
                        code += cond[0].split('==',1)[1]  + close_symbol

                    elif t_type == "WORD":                   #20120714: pointz=>pointz; Bears=>'Bears'
                        if self.name == "python_function" or t_val[0]!=t_val[0].upper():
                            code = t_val
                        else:  code = "'%s'"%t_val

                    elif t_type == "PARAMETER":
                        code = self.code_access_from_parameter(t_val)
                        if tok_terms.has_comparator:
                            if any(op in tok_terms.has_comparator for op in '<>'):
                                code = "(1*%s)" % code # avoid e.g. "None < 3"
                                # (not needed for python 3.0)


                    elif t_type == "AGGREGATOR":
                        #print "t_tpye is agg"
                        next_tok = (t+1<len(tok_terms)) and tok_terms[t+1][0]
                        if next_tok and next_tok.type == "SQUARE_BRACKET":
                            self.has_squarebracket_in_condition = 1
                            #print "agg has sb so parse with:  Sum(1@%s)"%(next_tok.value[1:-1])
                            read_ag =  self.parse_aggregator("Sum(1@%s)"%(
                                next_tok.value[1:-1]),has_squarebracket=1,is_function=1) # 20120412 is_function=1 added to avoid treating comma in eg [season-1,season-2] as args
                            read_key = read_ag.conditions[0].pyql
                            skip_squarebracket = 1
                            square_t_val = next_tok.value
                        else:
                            square_t_val = ''
                            skip_squarebracket = 0
                            read_key = ''

                        ag_dt = self.parse_aggregator(t_val,self.has_squarebracket)
                        t_val = t_val + square_t_val
                        if not t_as_term: # no outside as. eg: Sum(weight) as Total
                            square_as = ''
                            if skip_squarebracket:
                                square_as = "[%s]"%as_condition_from_metacode(read_ag.conditions[0][-1])
                            arg_as = ''
                            if ag_dt.args:
                                 arg_as = ",%s"%ag_dt.args
                            agg_as_term = ''
                            #if str(ag_dt.conditions[0][0]) != 'True':
                            #    agg_as_term += "@%s"%(as_condition_from_metacode(ag_dt.conditions[0][-1]))
                            agg_as_cond = as_condition_from_metacode(ag_dt.conditions[0][-1])
                            if agg_as_cond != "1":
                                agg_as_term += "@%s"%(agg_as_cond)
                            t_as_term = "%s(%s%s%s)%s"%(ag_dt.fields[0].flavor,ag_dt.fields[0].alias,agg_as_term,arg_as,square_as)

                        offset = len(self.condition_cache)
                        self.condition_cache.append(ag_dt)
                        pvs = ''
                        for pv in ag_dt.conditions[0].list_vals: #20120411 - this failed for different number of terms in cond and key. eg: S(age@1+1)[2]
                            #print "pv:",pv,read_key
                            if pv != 'and':
                                pvs += pv + ' ' # 20120612: added space to match ' '.join(keys)
                            else:
                                #print "setting read_key",read_key," for",pvs
                                read_key = string.replace(read_key,'_replace_parent_val_',pvs.strip(),1)
                                pvs = ''
                        if pvs:
                            read_key = string.replace(read_key,'_replace_parent_val_',pvs.strip(),1)
                            #print "finally setting read_key",read_key," for",pvs

                        #read_key = string.replace(read_key,'_replace_parent_val_',' '.join(ag_dt.conditions[0].list_vals))
                        force_none_to_fail = ''
                        if tok_terms.has_comparator and tok_terms.has_comparator != 'is':  # 'is' in tok_terms.has_comparators??
                            force_none_to_fail = '1*'
                        code = "(%s_condition_cache[%d].value((%s,)))"%(force_none_to_fail,offset,read_key or ag_dt.conditions[0].pyql)

                    elif t_type in ["STRING"]:
                        code = "'%s'"%(t_val,)
                        t_as_term = code # what if a string has an as?
                    elif t_type in ["DB_STRING"]:
                        code = "'%s'"%(t_val,)
                    else: code = t_val
                    #print "cva.append:", (code,t_val,t_as_term)
                    cva.append((code,t_val,t_as_term))
                    #print "cva:",cva
                if cva: code_val_as_terms.append(cva)

            text_code_val_as_terms = []
            for cva in all_combinations(code_val_as_terms):
                #print "cva:",cva
                # build these up as lists for easy concatination.
                text_code_terms = [];text_val_terms = [];text_as_term_terms = []; list_val_terms = []
                for code,val,as_term in cva:
                    #print "val in cva:",val,"as in cva:",as_term
                    text_code_terms.append(code)
                    list_val_terms.append(val)
                    if self.has_squarebracket and val != 'and':  #20120411 - new paradigm: cache on _replace_parent_val_ for each 'and' delimited term
                        # this silliness since parent is parsed last
                        if not text_val_terms or text_val_terms[-1] != '_replace_parent_val_':
                            #print "appending _replace_parent_val_ for",val
                            text_val_terms.append('_replace_parent_val_')
                    else:
                        text_val_terms.append(val)
                    #print "text_val_terms:",                        text_val_terms
                    #print "append text_code_terms with:",code
                    #print "as_trm:",`as_term`,type(as_term)
                    text_as_term_terms.append(as_term or val)
                #print  "text_as_term_terms ",text_as_term_terms
                #text_as_term_terms = filter(lambda x:string.strip(x),text_as_term_terms)
                #print  "filtered: text_as_term_terms ",text_as_term_terms
                #print "c_terms:",text_code_terms
                #print "val_terms:",text_val_terms
                # don't bother grouping by these: 1,0,True,False and strings that are not all upper.
                if len(text_code_terms) == 1 and (text_code_terms[0] in ["1","True","0","False"] or (text_code_terms[0][0] == "'" and not text_code_terms[0][1:-1].isupper())):
                #if text_code_terms == text_val_terms: # a constant
                    #print "tct:",text_code_terms
                    tok_terms.has_comparator = 1
                if tok_terms.has_comparator:
                    text_code_val_as_terms.append(
                        (' '.join(text_code_terms),
                         'r"""%s"""'%(' '.join(text_val_terms),),
                         'r"""%s"""'%(' '.join(text_as_term_terms).strip()),
                                  list_val_terms))
                else:
                    if self.has_squarebracket:
                        # eg: Sum(points@team)[opponents]
                        #     need keys of (team=%s,opponents)
                        #     so that Cache_DT can sum over opponents.
                        v_terms = '(r"""%s = %%s""",%s)'%(
                            ' '.join(text_val_terms).strip(),
                            ' '.join(text_code_terms).strip(),)
                    else:
                        v_terms = '(r"""%s = %%s"""%%(%s,))'%(
                            ' '.join(text_val_terms).strip(),
                            ' '.join(text_code_terms).strip(),)
                    #print "text_as_term_terms::",text_as_term_terms

                    text_code_val_as_terms.append(('True',v_terms,
       'r"""%s = %%s"""%%(%s,)'%(' '.join(text_as_term_terms).strip(),
                                                       ' '.join(text_code_terms).strip(),),
                                                          list_val_terms))
            tuple_conditions.append(text_code_val_as_terms)
            #print  "text_code_val_as_terms:",text_code_val_as_terms
        #print "tcond:",tuple_conditions
        tuple_conditions = all_combinations(tuple_conditions)

        # now flatten
        conditions = []
        for tuple_condition in tuple_conditions:
            codes = []; vals = []; as_terms = [];list_vals = []
            for code,val,as_term,list_val in tuple_condition:
                codes.append(code);vals.append(val);as_terms.append(as_term)
                list_vals += list_val
            # join vals by `,` for tuples
            condition = Condition((' '.join(codes),
                                                 ','.join(vals),
                                                SPACE_PAT.sub(' ',','.join(as_terms).strip())))
            condition.list_vals = list_vals
            #print "condition.list_vals:",condition.list_vals
            conditions.append(condition)
            #print "condition:vals:",vals

        return conditions

    def aggregator_groups(self,tok,after_at):
        #print "agg_groups gets tok:",tok
        #why a member of dt? No ref to self.
        flavor,guts = string.split(tok.value,'(',1)
        guts = guts[:-1] # last ')'
        # move up top
        N_group_pat = re.compile("(N[\s]*=[\s]*[0-9]+,[0-9]+[0-9,]*)")
        mo = N_group_pat.findall(guts)

        if not mo: return [tok]

        N_match = mo[0]
        #print "mo:",N_match
        temp_pyql = ""
        for N in string.split(string.split(N_match,'=')[1],","):
            temp_pyql += flavor + '(' + string.replace(guts,N_match,'N=%s'%N)+')'
            if after_at: temp_pyql += ','
        if after_at: temp_pyql = temp_pyql[:-1] # last comma
        temp_lexer = self.lexer.clone()
        temp_lexer.input(temp_pyql)
        ret = []
        while True:
            tok = temp_lexer.token()
            if not tok:break
            ret.append(tok)
        return ret

    def parse(self,pyql,default_fields=None,n_field_caches=0):
        # parse pyql into tokens, pass to parse_fields, parse_conditions
        #      Handle subsequent queries.
        #print "parse get pyql:",pyql
        self.subsequent_query = None
        self.lexer.input(pyql)
        # need to learn up top if has at since expand agg group is different for fields and conditions.
        # also, can a subsequent query have agg group?
        toks = []
        has_at = False
        while True:
            tok = self.lexer.token()
            if not tok: break
            # want to allow coach = Bob Jones
            if tok.type == "WORD" and len(toks) > 1 and toks[-2].type == "WORD" and toks[-1].type == "SPACE":
                tok.value = ' ' + tok.value
            toks.append(tok)
            if tok.value == '@': has_at = True
        if not has_at:# no @ given - handle default
            if not default_fields: # assuse that the pyql was fields and set the condition to `@1`
                toks += [AT_TOK, ONE_TOK]
            else:
                default_toks = []
                self.lexer.input('%s'%default_fields)
                while True:
                    tok = self.lexer.token()
                    #print "default field tok:",tok
                    if not tok: break
                    default_toks.append(tok)
                toks = default_toks + [AT_TOK] + toks
        condition_toks = []
        field_toks = []
        pending = [] #list of lists of toks used to expand aggregator groups for fields: Sum(runs,N=2,3) + Sum(hits,N=4,5),...
        after_at = False
        for tok in toks:
            if not tok or tok.type == "CONJUCTION" or tok.value in [',','@']:
                dump_pending = True
            else: dump_pending = False
            append_toks = [] # a tok might `AGGREGATOR group by` into more
            if tok and tok.type == "DOLLAR_INDEX":
                tok.value = self.headers[int(tok.value[1:])-1]
                tok.type = "PARAMETER"
                append_toks = [tok]
            elif tok and tok.type == "AGGREGATOR":
                append_toks = self.aggregator_groups(tok,after_at)
                #print "aggrp: appendtoks:",append_toks
            elif tok and tok.type == "BAR":
                self.subsequent_query = tok.value[1:]
                dump_pending = True
                tok = None
                #append_toks = [tok]
                #break
            elif tok and tok.value != '@':
                append_toks = [tok]
            if append_toks:
                if after_at:
                    condition_toks += append_toks
                else:
                    pending.append(append_toks)
            dump_toks = []
            if dump_pending and not after_at:
                #print "dump_pend.pending:",pending
                for p_toks in all_combinations(pending):
                    #print "lens:",len(p_toks),len(pending)
                    #print "p_toks:",p_toks
                    for p_tok in p_toks:
                        dump_toks.append(p_tok)
                    if p_tok.value != ',': dump_toks.append(COMMA_TOK)
                #if dump_toks[-1].value == ',': dump_toks = dump_toks[:-1]
                pending = []
            #if dump_toks and after_at:
            #    condition_toks += dump_toks
            if dump_toks:
                field_toks += dump_toks
            if tok and tok.value == '@':
                #field_toks.append(tok)
                after_at = True
            if not tok: break  # hit BAR

        if field_toks and field_toks[-1].value == ',':
            field_toks = field_toks[:-1]
        if condition_toks and condition_toks[-1].value == ',':
            condition_toks = condition_toks[:-1]


        if len(field_toks) and field_toks[-1].type == 'SPACE': field_toks = field_toks[:-1]
        if len(condition_toks) and condition_toks[0].type == 'SPACE': condition_toks = condition_toks[1:]

        # put a terminal @ on fields for historic parsing of fields.
        field_toks.append(AT_TOK)

        #print "field_toks:",field_toks
        #print "condition_toks:",condition_toks
        fields = self.parse_fields(field_toks,n_field_caches=n_field_caches)
        conditions = self.parse_conditions(condition_toks)
        #print "conds:",conditions
        if self.verbose:
            print "fields:\n%s\n\n%d condition%s:\n%s\n"%(
                fields, len(conditions),
                (len(conditions)!=1)*'s' or '',conditions)
        self.fields = fields
        self.conditions = conditions

    def build_top_metacode_lines(self):
        # for joins in subclass:  done after all parsing
        pass

    def build_metacode(self,fields,conditions,
                       field_cache,condition_cache,top_metacode_lines): #bmc
        if use_cython:
            mc = r'cimport cython\n'
            mc += r'from cython cimport *\n'
            mc += r'@cython.boundscheck(False)\n'
            mc += r'def update(self, list _d, int _i, _result, _field_cache, _condition_cache):\n'
        else:
            mc = r'def update(self, _d, _i, _result, _field_cache, _condition_cache):\n'
        #mc += r'\tglobal exc_count\n' # disabled :(  cgw
        #mc += "\tprint _condition_cache\n"
        if self.update_cache_on_change_offset is not None and self.has_squarebracket_in_condition:
             mc += "\t_on_change_value = _d[%d][_i];\n"%self.update_cache_on_change_offset
             mc += "\tif _on_change_value != self.on_change_value:\n"
             mc += "\t\tself.on_change_value = _on_change_value\n"
             #mc += "\t\tprint 'updating cache on',self.on_change_value\n"
             mc += "\t\tfor _cache in _condition_cache:\n"
             mc += "\t\t\tfor _col in _cache: _col.append_pending(_on_change_value)\n"

        # a good place for joins and ad hoc aliases
        for tmc in top_metacode_lines:
            mc += r'\t%s\n'%tmc

        mc += r'\t_c_keys = [] # define condition keys\n'
        mc += r'\t_c_true_offsets = [] # define offsets for true conditions\n'

        # Find common conditions
        c_conds = common_conditions(conditions)
        if c_conds:
            mc += r'\ttry:\n\t\tif %s: #query on common elements once\n'%(' and '.join(c_conds),)
        else:
            mc += r'\tif 1: # no common query elements found means no pre-query\n'

        # combinatorics of comma delimited conditions
        for (c,condition) in enumerate(conditions):
            c_code = condition.code
            for c_cond in c_conds:
                c_code = c_code.replace(c_cond+' and ','').replace(' and '+c_cond,'')
            mc += r'\t\t\ttry:\n\t\t\t\tif %s:\n\t\t\t\t\t_c_keys += [((%s,),(%s,))]\n'%(
                        #condition.code,
                        c_code,
                        condition.pyql,
                        condition.as_term)
            mc += r'\t\t\t\t\t_c_true_offsets.append(%s)\n'%c

            if self.print_exceptions:
                #mc += r'\t\ttexcept:\n\t\t\texc_count += 1\n'
                mc += r'\t\t\texcept:\n'
                mc += r'\t\t\t\texc_info=sys.exc_info()\n'
                mc += r'\t\t\t\terrmsg=traceback.format_exception(*exc_info, limit=1)[-1].strip()\n'
                mc += r'\t\t\t\tlineno=exc_info[2].tb_lineno\n'
                mc += r'\t\t\t\tprint "EXCEPTION %s @ %d"%(errmsg, lineno)\n'
            else:
                #mc += r'\texcept: exc_count += 1\n'
                mc += r'\t\t\texcept: pass\n'

        if c_conds: # Close the "try" block
            mc += "\texcept: pass\n"


        #Each running summative defined to the left of the @ sign
        #   gets its own fc.
        #There are no groups allowed in the possible conditional of these
        if field_cache:
            mc += r'\t# field cache loop\n'
            mc += r'\tizip=itertools.izip\n'
            mc += r'\tif _c_keys:\n'
        for (i, fc) in enumerate(field_cache):
            # The condition is checked with the generation of the value
            #print "fc loop i",i
            mc += r'\t\ttry: _update_value = ((%s) or None)*%s\n'%(
                          fc.conditions[0].code,fc.fields[0].update)
            mc += r'\t\texcept: _update_value = None\n'
            mc += r'\t\tfor _c_true_offset,_key in izip(_c_true_offsets,_c_keys):\n'
            mc += r'\t\t\t_offset = _field_cache[%d].offset_from_header(_key[0])\n'%i

            mc += r'\t\t\tif _offset is None:\n'
            mc += r'\t\t\t\t_field_cache[%s].add_object(Cache_DT(data=(%s),name=_key[0]))\n'%(i,fc.fields[0].init_code())
            mc += r'\t\t\t\t_offset = -1\n'
            mc += r'\t\t\t_field_cache[%d][_offset].append((_update_value,))\n'%i
            if not fc.fields[0].read_key:
                mc += r'\t\t\tself.field_values[%d][_key] = _field_cache[%d][_offset][0].value() # no square bracket\n'%(i,i)

            if fc.fields[0].read_key:
                #print "mc foudn read_key"
                for (c, condition) in enumerate(conditions):
                    rk = fc.fields[0].read_key
                    #print "read key:",rk
                    rpv = [] # 20120413: new pv paradigm: delimit by and
                    for pv in condition.list_vals:
                        if pv == 'and':
                            #print "mc replacing _replace_parent_val_ with pv: ",' '.join(rpv)
                            rk = string.replace(rk,"_replace_parent_val_",' '.join(rpv),1)
                            rpv = []
                        else:
                            rpv.append(pv)
                    #print "finally: mc replacing _replace_parent_val_ with pv: ",' '.join(rpv)
                    rk = string.replace(rk,"_replace_parent_val_",' '.join(rpv),1)

                    #print "read key:",rk
                    mc += r'\t\t\tif _c_true_offset == %s:\n'%c
                    #mc += r'\t\t\t\tprint "field_cahce:",_field_cache[%d]\n'%i
                    mc += r'\t\t\t\tself.field_values[%d][_key] = _field_cache[%d].value((%s,),) # lhs square bracket notation.\n'%(i,i,rk)

        if not field_cache:
            mc += r'\t_update_tuple = ()\n'
            mc += r'\tif _c_keys:\n'

        update_mc = r'\t\ttry: _update_tuple += (%s,)\n' % ','.join(field.update for field in fields)


        if len(fields)  <2:
            update_mc += r'\t\texcept: _update_tuple += (None,)\n'
        else: # Try individually, if there were multiple fields
            update_mc += r'\t\texcept:\n'
            for field in fields:
                update_mc += r'\t\t\ttry: _update_tuple += (%s,)\n'%field.update
                update_mc += r'\t\t\texcept: _update_tuple += (None,)\n'

        for (s, sut) in enumerate(chain(field.safe_update_terms for field in fields)):
            update_mc += r'\t\ttry: _safe_update_term_%d = %s\n'%(s,sut)
            update_mc += r'\t\texcept: _safe_update_term_%d = None\n'%s

        if not field_cache:
            mc += update_mc
        mc += r'\tfor _key in _c_keys:\n'
        if field_cache:
            mc += r'\t\t_update_tuple = ()\n' # Create empty tuple to append to - cgw
            mc += update_mc

        mc += r'\t\t_offset = _result.offset_from_header(_key)\n'
        mc += r'\t\tif _offset is None:\n' # First time through
        mc += r'\t\t\t_result.add_object(DT(data=('
        for field in fields:
            mc += field.init_code()
        mc += r'),name=_key,build_lexer=False))\n'
        mc += r'\t\t\t_offset = -1\n'
        #mc += r'\t\tprint "MC._field_cache:",_field_cache\n'
        #mc += r'\t\tprint "MC.self.field_values:",self.field_values\n'
        #mc += r'\t\tprint "MC:",_i,_offset,_update_tuple\n'
        mc += r'\t\t_result[_offset].append(_update_tuple)\n'

        for (i,cc) in enumerate(condition_cache):
            #print "cc.fields:",cc.fields
            #print "cc.conditions:",cc.conditions
            mc += r'\t# update the cache for the condition fields\n'
            mc += r'\t_keys = []\n'
            for condition in cc.conditions:
                #print "cond:",condition.code,condition.pyql
                mc += r'\ttry:\n\t\tif %s:\n\t\t\t_keys += [(%s,)]\n'%(
                    condition.code,
                    #string.replace(condition.pyql,'%s""",','%s"""%'))
                    condition.pyql)
                mc += r'\texcept: pass\n'

            mc += r'\tif _keys:\n\t\t_update_tuple = ()\n'
            for field in cc.fields:

                mc += r'\t\ttry: _update_tuple += (%s,)\n'%field.update
                mc += r'\t\texcept: _update_tuple += (None,)\n'
            #mc += r'\tfor _key in map(self._nk,_keys):\n'
            mc += r'\tfor _key in _keys:\n'
            mc += r'\t\t_offset = _condition_cache[%d].offset_from_header(_key)\n'%i
            mc += r'\t\tif _offset is None:\n'
            mc += r'\t\t\t_condition_cache[%d].add_object(DT(data=('%i
            for field in cc.fields:
                mc += field.init_code()
            mc += r'),name=_key,build_lexer=False))\n'
            mc += r'\t\t\t_offset = -1\n'
            if self.update_cache_on_change_offset is not None and self.has_squarebracket_in_condition:
                mc += r'\t\t_condition_cache[%d][_offset].append_on_change(_on_change_value,_update_tuple)\n'%i
            else:
                mc += r'\t\t_condition_cache[%d][_offset].append(_update_tuple)\n'%i

        mc = string.replace(mc,r'\n','\n')
        mc = string.replace(mc,r'\t','\t')  # Why?
        self.metacode = mc #'\n'.join(lines)

    def query(self, pyql, default_fields = None, indices=None):
        global exc_count
        self.has_squarebraket_in_condition = 0
        self.has_squarebraket = 0
        self.subsequent_query = False
        self.field_cache = []
        self.condition_cache = []
        self.parse(pyql,default_fields=default_fields)
               # builds self.fields, self.conditions and
               #   potentially appends self.field_cache,self.condition_cache

        # one dictionary each summative refered to in the fields
        # this holds the current value of the field cache
        self.field_values = []
        field_cache = []
        i = -1
        for field in self.fields:
            #print "query::field",field
            for fc in field.cache:
                #print "query::field.cache",fc
                self.field_cache.append(fc)
                field_cache.append(Cache_DT(name="field_cache_%d"%i))
                self.field_values.append({})

        # one for each summative refered to in the conditions
        condition_cache = []
        for i in range(len(self.condition_cache)):
            condition_cache.append(Cache_DT(name="conditon_cache_%d"%i))

        # the one result DT
        result = DT(name=pyql,build_lexer=False)

        self.build_top_metacode_lines()
        self.build_metacode(self.fields,self.conditions,
                            self.field_cache,self.condition_cache,
                            self.top_metacode_lines)
        if self.show_metacode: # Show me da code!
            print "METACODE"
            for i, line in enumerate(self.metacode.split('\n'),1):
                print "%4d  %s" % (i, line)

        # raises an error if someone includes unspecified python code.
        #PyQL.safe_ast_query.filter(self.metacode)

        # create the 'update' function in the local scope

        if use_cython:
            import Cython.Build.Inline
            self.metacode = self.metacode.replace("(DT", "(PyQL.dt.DT") #? TEMP HACK
            self.metacode = self.metacode.replace("(Cache_DT", "(PyQL.dt.Cache_DT") #? TEMP HACK
            # IF THIS CODE IS STILL HERE IN 2016 PLEASE SHOOT ME
            print "DATA TYPE:", type(self.data)
            #oh man this is pure evil
            if type(self.data) is not list: # 2d optimized pointer array!
                # Boilerplate.
                #bp = 'import numpy as np\n'
                #bp += 'import numpy as np\n'
                #bp += 'DTYPE = np.int64\n'
                #bp += 'ctypedef np.int64_t DTYPE_t\n'
                bp = 'cimport cython\n'
                bp += 'from cython import *\n'
                bp += 'from cython.ref cimport *\n'
                #bp += 'import PyQL.dt\n'
                #bp += 'import PyQL.columns\n'
                #self.metacode = bp + self.metacode

                # I can't believe I'm doing this.  Children avert your eyes.
                base_addr = self.data.__array_interface__['data'][0]
                HOURS_PER_DAY = 24
                col_stride = HOURS_PER_DAY * len(self.data[0])

                # Looking for patterns like _d[X][Y], avoiding condition_cache
                #pat = re.compile(r'([^a-z])(_[a-z]+)\[([^]]+)]\[([^]]+)]')
                #self.metacode = pat.sub(r'\1 \2[\3,\4]',
                #                        self.metacode)

                self.metacode = self.metacode.replace("_d[",
                                                      "<object><PyObject*>(%d+%d*"%(base_addr, col_stride))

                self.metacode = self.metacode.replace("][_i]", "+24*_i)")
                lines = self.metacode.split('\n')
                newlines = []
                for line in lines:
                    if "def update" in line:
                        line = line.replace("list _d", "_d")
                    if "PyObject" in line:
                        line += " #  I told you not to look!"
                        print line, "(HA HA)"
                    newlines.append(line)
                self.metacode = '\n'.join(newlines)

            t0 = time.time()
            if self.show_metacode:
                print "modified metacode"
                for i, line in enumerate(self.metacode.split('\n'),1):
                    print "%4d  %s" % (i, line)

            co = Cython.Build.Inline.cython_inline(self.metacode, locals=locals(), globals=globals())
            update = co['update']

            t1 = time.time()
            print "CYTHON BUILD TIME: %.2f ms" % (1000*(t1-t0))

        else:

            co = compile(self.metacode, "metacode", "exec")
            exec(co)



        self.timer = False
        if self.timer: start = time.time()
        self.on_change_value = None
        exc_count = 0
        for i in indices or xrange(len(self.data[0])):
            update(self, self.data, i, result, field_cache, condition_cache)
        if exc_count:
            print "%d EXCEPTIONS OCCURRED DURING QUERY" % exc_count

        if self.timer:
            print "query loop took %0.2f ms"%(1000*(time.time()-start))
        if self.subsequent_query:
            # not too sure what I want here...
            if len(result) == 1:
                result = result[0]
            else:
                result = result.reduced()
            result.db_strings = self.db_strings # probably we want this.
            #result.verbose = 1
            result.build_lexer()
            result.show_metacode = self.show_metacode
            result.print_exceptions = self.print_exceptions
            result = result.query(self.subsequent_query,
                                  default_fields=','.join(result.headers))

        return result


    def offset_from_header(self, header):
        return self.header_dict.get(header)

    def add_object(self, object):
        #print "to self:",self
        # removed these two lines for production
        #if object.name in self.headers:
        #    raise KeyError(object.name)
        self.header_dict[object.name] = len(self.headers)
        self.headers.append(object.name)
        self.data.append(object)

    # return a new dt made by combine sibling tables
    #  created by a query with multiple keys,optionally moving keys to a column
    # buggy in that a str_format is required to pass on to reduced dt
    def reduced(self,key_transform=None,position='last',name='query',format='%s'):
        data = []
        if key_transform:
            data.append(PyQL.columns.Column(name=name,format=format))
            for sibling in self.data:
                #print "sibling.name:",sibling.name
                data[-1].append(key_transform(sibling.name))
                #print "sibling.name appened:",key_transform(sibling.name)
        if not len(self.data): n_columns = 0
        else: n_columns = len(self.data[0])
        # 20140818: if all columns are lists then add them, else append values to a single list.
        all_lists = 1
        for c in range(n_columns):
            if type(self.data[0][c].value()) is not list:
                all_lists = 0
                break
        for c in range(n_columns):
            data.append(PyQL.columns.Column(name=self.data[0][c].name,
                                       format=self.data[0][c].str_format))
            for sibling in self.data:
                # 20130107 is a non-summative add values, else append them
                if all_lists:
                    data[-1] += sibling[c].value()
                else:
                    data[-1].append(sibling[c].value())
        if key_transform and position != 'first': # must be last
            data = data[1:] + [data[0]]
        ret = DT(data=data,name=self.name,build_lexer=False)
        return ret

    def append_row(self,d,none_value=None):
        for header in self.headers:
            self.data[self.offset_from_header(header)].append(d.get(header,none_value))

    def replace_row(self,i,d,none_value=None):
        for header in self.headers:
            print "header:",header
            self.data[self.offset_from_header(header)][i] = d.get(header,none_value)

    def update_row(self,i,d):
        for k in d:
            self.data[self.offset_from_header(k)][i] = d[k]

    def sort_by_column(self,offset=0,compare=cmp):
        if self.verbose: print "dt.sort_by_column:offset:",offset
        if type(offset) is not int:
            offset = self.offset_from_header(offset)
            print "sort.off:", offset
            if type(offset) is not type(123):
                return
        tr = PyQL.py_tools.transpose_table(self.data)
        # sort strings and (string, ...) smallest to largest else largest to smallest
        if type(tr[0][offset]) is type('abc') or (
                 type(tr[0][offset]) in [type((1,2)),type([1,2])] and 0<len(tr[0][offset]) and type(tr[0][offset][0]) is type('abc')):
            tr.sort(lambda x,y,offset=offset,compare=compare:compare(x[offset],y[offset]))
        else:
            tr.sort(lambda x,y,offset=offset,compare=compare:compare(y[offset],x[offset]))

        tr = PyQL.py_tools.transpose_table(tr)
        for c in range(len(self.data)):
            self.data[c].data = tr[c]

    def html(self):
        return PyQL.outputs.html(self)

    def _nk(self,key):
        # normalize_key: an ugle patch to account for the mishandling of spaces
        # A(age@1>0)[1>0] would stores values in Cache_DT under ("1 > 0") and look at ("1>0")
        print "_nk gets:",key
        ret = key
        ret = map(lambda x:''.join(x).replace(' ',''),ret)
        ret = tuple(ret)
        print "and returns:",ret
        return ret

class Cache_DT(DT):
    """ used inside the query loop to maintain and reference running summatives.  Allows sum over list of keys: Sum(points@team)[opponents] """
    def __init__(self,data=[],verbose=0,name=None,top_metacode_lines=[]):
        DT.__init__(self,data=data,verbose=verbose,name=name,
                    top_metacode_lines=top_metacode_lines,build_lexer=False)
        #print "Cache_DT.headers:",self.headers
        #for h in range(len(self.headers)):
        #    if type(self.headers[h]) is str: self.headers[h].replace(' ','')
        #    else: self.headers = map(lambda x:(''.join(x).replace(' ',''),),self.headers)

    def value(self,header,default=None):
        """ expect header to be a tuple with string or list values: take the cartestian product of keys and return the expressed summative of all corresponding values """
        if not len(self) or not len(self[0]):
            return default
        #print "self.headers:",self.headers
        #print "self:",self
        # eg pyql: Sum(points@team and season)[opponents and 2007]
        #          value request: header= (('team = %s', ['Lions', 'Seahawks']), 'and', ('season = %s', 2007))
        headers = []
        for term in header:
            if type(term) is str:
                headers.append([term])
                continue
            # must be a two-ple (format string,value) or (format string,[value1,value2,..])
            if type(term[1]) is not list:
                headers.append([term[0]%(term[1],)])
                continue
            # must be a two-ple  (format string,[value1,value2,..])
            keys = []
            for ref in term[1]:
                keys.append(term[0]%(ref,))
            headers.append(keys)
        summ = None
        count = 0
        #print "Cache_DT.headers:",headers #,"allcombs:"%str(all_combinations(headers))
        if not headers or not headers[0]:
            print "no headers: returning None"
            return None
        for head in all_combinations(headers):
            #head = head[0]
            #print "Cache_DT.lookup_head:",head

            v = self.value_from_header(head)
            if v is None: continue
            #print "value,typre:",v[0].value(),type(v[0].value())
            if type(v[0].value()) in NUMBER_TYPES:
                summ = (summ or 0) + v[0].value()
            else:
                summ =  v[0].value()
            count += 1
        #print "Cache_DT.sum:",sum
        if summ is not None and isinstance(self[0][0],PyQL.columns.Average):
            summ =  1. * summ / count
        return summ

    def append(self, row):
        # Instead of calling append in the parent class, we just copy the code here,
        # since it's tiny
        for sd, r in izip(self.data, row):
            sd.append(r)

def type_of_tuple_items(t):
    for item in t:
        if item is not None:
            return type(item)
    return type(None)


def dt_from_file(file,
                 name="DT",
                 headers=None,   # if not headers than take from file
                 delim_row='\n',delim_column='\t',null='',verbose=0  # fields for parsing text file
                 ):
    txt = open(file).read()
    file_headers,data = PyQL.py_tools.tuple_of_tuples_from_txt(txt,
                                                          delim_column=delim_column,
                                                          delim_row=delim_row,
                                                          null=null,
                                                          verbose=verbose,
                                                          has_header=not headers)
    if not headers: headers = map(lambda x:string.strip(re.sub("[\s]+",' ',x)),file_headers)
    dt = DT(name=name)
    for i in range(len(headers)):
        #print i,headers[i],type(data[i])
        #if i == 15: print data[i]
        data_type = type_of_tuple_items(data[i])
        #print "data_type",data_type
        format = { int: "%d", float: "%0.2f"}.get(data_type, " '%s' ")
        #print "format:",format
        dt.add_object(PyQL.columns.Column(name=headers[i],data=data[i],format=format))
    dt.build_lexer()
    return dt

######################  tests and demos ################
# build and return a sample dt
def test_dt():
    c1 = PyQL.columns.Column(name="height",format="""lambda h:"%0.0f'%0.0f''"%(int(h)/12,int(h)-12*(int(h)/12))""")
    c2 = PyQL.columns.Column(name="weight",format="""lambda w:'%d\#'%w""")
    c3 = PyQL.columns.Column(name="first name",format="%s")
    c4 = PyQL.columns.Column(name="age",format="%s")
    c5 = PyQL.columns.Column(name="children",format="%s")
    dt = DT(data = [c1,c2,c3,c4,c5],name="test table",db_strings=['mike'])
    c1.append(65);c2.append(180);c3.append(None);c4.append(23);c5.append(['al'])
    c1.append(69);c2.append(150);c3.append("mike");c4.append(43);c5.append(['mary','ed'])
    c1.append(70);c2.append(190);c3.append("ike");c4.append(72);c5.append(['marty','ned','john']) # '''
    dt.verbose = 0
    #col_data = map(to_np, col.data)
    #dt.build_lexer()
    return dt

def test_query(dt):
    import time
    dt.show_metacode = 1
    dt.verbose = 0
    dt.update_cache_on_change_offset = None
    pyql = "Sum(age as Age@weight>0,N=2),Sum(age as Age+height) / Average(weight as 'Heft'@age as Age>2 and weight>0) @ Sum(age@1>0)[1>0]"

    #pyql = "Average(weight as W)[age and height>0] @age and height>0"
    #pyql = " 1*Sum(height,format='%f') - Sum(weight,N=2,format='%s,') @ weight     >      0"
    pyql = " (max(Sum(age as Age,N=1),Sum(age))) @ 1"
    pyql = " age as Age@ Sum(first name is None or age==43) as bob"
    #pyql = "(height,Sum(weight),Sum(age)) as foo bar@1"
    #pyql = "map(string.upper,map(lambda x:x[0],filter(lambda x:x[1]>'b',children)))[0:] @ 1"
    #pyql = "Sum(age@Replace(age@Sum(age@'foo')==66)==43)@weight>0"
    #pyql = "Sum(age@Replace(age@height>30)[height>30]==23) @ 1"
    #pyql = " age @ (weight>100),(weight>160) "
    #pyql = " age @ weight>100,160 and height>0"
    #pyql = "age%3@age"
    #pyql = "first name.lower()@1"
    dt.my_method_2 = lambda x,y:2*x+y
    dt.my_method = lambda x:2*x
    #pyql = "self.my_method(Sum(age),5)@self.my_method(Sum(age@1 and age>0),3)>60"
    #pyql = "(Sum(weight),height)@Sum(age@1)+Sum(age@4)"
    #pyql = "1@(Sum(age@age>20)[age>20]>50 and Sum(height)) is True"
    #pyql = "1@len(filter(lambda x,y='b':x[0]=='j',children))"
    #pyql = "Sum(1)@len(map(string.upper,map(lambda x:x[0],filter(lambda x,y='b':x[1]>=y,children)[0:-1])))==1"
    #pyql = "1*Sum(height@Sum(age)+2>5)+Sum(age)@1"
    #pyql = "height,age@(Sum(height)+Sum(age)+Replace(56))=256"
    #pyql = "1@(Sum(age@1)[1]+Sum(height),234)>(2*age,weight)" # this works in parse function as condition mode
    #pyql = "(Sum(age)+Sum(height) > Replace(2*age)+Replace(weight))@1"
    #pyql = "string.zfill((Sum(age)+Sum(height)),10),(1*Average(weight),Replace(3)) as W3@1"
    #pyql = "1*max([Average(weight),170])@1"
    pyql = "first name@(Sum(age@1)[1]+Sum(height),234)>(2*max([34,age]),Replace(weight)) and 2*Sum(weight)/Sum(height@age>23)[age>23]"
    pyql = "(first name,children)@len ( map ( lambda x:x[0] , filter ( lambda z,y='a':z[0]==y,children)))"
    #pyql = "1@filter ( lambda z,y='a':z[0]==y,children)"
    #pyql = "Sum(1)@(age=23,)" # this groups by T/F\
    pyql = "Sum(1)@(age)" # this groups by age
    pyql = "Sum(1)@(age>23)" # simple condition
    pyql = "(age as A)@(age<50,weight)"  # groups by (T/F,weight)
    #pyql = "(age as A)@(age<50,weight>100)"  # groups by (T/F,T/F)
    #pyql = r'''Sum(1)+Column(1), Column((2,2),format="lambda x:'%d-%d'%x") @ 1'''
    #pyql = "(age as A)@(age<50,weight)"  # XXX probably this ought to group. NB (age<50,weight,)  does group.
    #pyql = "(age as A),weight as W@self.my_method(Sum(age@1,N=1))"
    #pyql = "1@self.my_method(Sum(age,N=1))"
    #pyql = "1@format(Sum(age,N=1),'0.5f')"
    #pyql = "age as 'A' + weight as 'W'@1"
    #pyql = "1@None is not first name"
    #pyql = "Sum(age@weight<200 and age>0,N=2,3)+Sum(height,N=1,2,3)@1"
    #pyql = "1,first name[:2],math.e,(bob)@Sum(age@2)[2]=66 and first name[:1] in 'ijk' and first name in [mike,ike,mike] and 1"
    #pyql = "Column({'a':'A','b':'B'}['a']),mike,'ike' as 'G'@first name[0] =   i"
    #pyql = "age as A,first name@(age=23)"
    #pyql = "age as A,first name@(age=23 and age>0)"
    #pyql = "first name@-age < (-25*1), -46"
    #pyql = "age@S(age@height)[height+1]"
    pyql = "height@Average(age@height and age)[[65+age,69] and [23,43]]<98"
    pyql = "4@Sum(age@Sum(weight@2)[4]>10)[Sum(weight@7)[9]>10]>60"   #XXX this fails
    #pyql = "Average(height)@Sum(age@Sum(weight@2)[2]>10)>60 and height"
    #pyql = "age@Sum(1@[1,1])"
    pyql = "( (Sum(weight),S(height)) )@1" #this works
    #pyql = "Tuple( (Sum(weight),S(height)),format=lambda x:'%s-%s'%x )@1" XXX Fails
    pyql = "1+R((Sum(age),Sum(weight))),R((A(age),A(weight))) @ 1"  #
    pyql = "age@S(age@1<2 and 2<3)[1<2 and 2<3]"
    pyql = "age@S(age@1>0) is None"
    start = time.time()
    pyql = "_i@age as goo  + age as foo>10 and Age"
    pyql = "1*Sum(age)/Sum(height),0+Sum(age),Sum(height)+0@1"
    pyql = "age,height@1,2|$2@$1=23"
    pyql = "$4 as Age,weight@1,2|$1,$2@23 = $1"
    pyql = "age@Average(age@1 and Average(weight@2 and 3)>1)>1"
    pyql = "1*(0<cmp(map(lambda x:0 or 2 and  x>0,[1,2,3]),map(lambda x:((0) or 2)*(x>0),[0,0,1]))) as scored_first@1"
    pyql = "round(weight)@Sum(weight)>0"
    #pyql = "age@(Average(100*((height-weight) as 'W')@1)) as 'WP'"
    #pyql = "age,height@weight"
    res = dt.query(pyql,default_fields='_i')
    print "query took %f seconds"%(time.time() - start)
    print "result",res
    #test_suite(dt)
    #print PyQL.outputs.html(res[0])
    return res

def test_suite(dt):
    print "start test suite"
    pyql ="S(age)@age>0 and weight>10,100,200 and height<400"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][0].value()==138

    pyql = "(age as A)@(len(string.split(str(age),'3'))<2)"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][-1][0]==72

    pyql = "age@S(age@1>0)[1>0]"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[-1][-1][0]==72

    pyql = r'''Sum(1)+Column(1), Column((2,2),format="lambda x:'%d-%d'%x") @ 1'''
    print "pyql:",pyql
    res = dt.query(pyql)
    print res[0][0].value()
    assert res[0][0].value()==4

    pyql = r'''R((Sum(age),Sum(weight))),R((A(age),A(weight))) @ 1'''
    print "pyql:",pyql
    res = dt.query(pyql)
    print res[0][0].value()
    assert res[0][0].value()==(138,520)

    pyql = "1 * (Sum(age),Sum(age)+4,math.pow(Sum(age)+4,2)) @ 1"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res[0]
    assert res[0][-1][-1][-1] == 20164


    pyql = "string.zfill(int((Sum(age)+Sum(height))),5) as 'test zfil',(1*Average(weight),Replace(3)) as W3@1"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res[0][0].value()
    assert res[0][0].value() == '00342'


    pyql = "age@first name is None and height>0"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][0].value()[0] == 23

    pyql = "Sum(age)@weight=180"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][0].value() == 23

    pyql = " max(Sum(age as Age,N=1),Sum(age)) @ 1"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][0].value() == 138


    pyql = "Sum(age)@(weight=180 and age>0)"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][0].value() == 23

    pyql = "(height,weight,age) as foo bar@(height,weight,age) as HWA = (69,150,43)"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res[0][0]
    assert res[0][0].value()[0] == (69, 150, 43)

    pyql = "Sum(age)@(weight=180 and age>0,) "
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][0].value() == 23 # 138 # (False,) is True XXX 138 if parse condition functon as field XXX

    pyql = "Average(weight)[age and height>0]@age and height>0"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][0].value() == 180

    pyql = "age,Sum(age@weight>150)[weight>150],Sum(age@Replace(age@height>30)[height>30]=23),Sum(age@Replace(age@Sum(age@'foo')['foo']=66)=43)@weight>0"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][0].data == [23,43,72]
    assert res[0][-1].value() == 72

    pyql = "Average(height)@Sum(age@Sum(weight@2)[2]>10)[Sum(weight@7)[7]>10]>60 and height"   #XXX this fails
    pyql = "Average(height)@Sum(age@Sum(weight@2)[2]>10)>60 and height"    # this works
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][0].value() == 70

    pyql = "age as Age,first name or 'John Doe' as Name,height as 'Height@Sum(age)' is None"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][0][0] == 23

    pyql = "tuple((height,weight,age,))@1"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][0][1] == (69,150,43)

    pyql = "first name,age@(height,weight,age,) = (69,150,43)"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][1][0] == 43

    pyql = "map(string.upper,map(lambda x:x[0],filter(lambda x:x[1]>'b',children)))[0:]@len(map(string.upper,map(lambda x:x[0],filter(lambda x,y='b':x[1]>y,children)[0:-1])))=1"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][0][-1] == ['N','J']

    dt.test = lambda x:x[0]+x[1]
    pyql = "self.test((age,weight))@1"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][0][-1] == 262

    pyql = "age,','.join(children)@self.test((age,weight))=262"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][0][-1] == 72

    pyql = "first name.upper()@max([height,weight,age])>150"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][0][-1] == 'IKE'

    pyql = "$4 as Age,weight@1|$1,$2@23 = $1"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert res[0][1].data[0] == 180

    pyql = "age,Sum(age,N=1,2,3),Sum(age,N=1)/Sum(age,N=3,2)@1"
    print "pyql:",pyql
    res = dt.query(pyql)
    print res
    assert "%0.3f"%res[0][-2].value() == "0.522"

def nfl_suite(nfl):
    import time
    #nfl.show_metacode = 1
    #nfl.update_cache_on_change_offset = nfl.offset_from_header('date')

    pyql = "Sum(points,N=4)/Sum(points,N=6,format='%0.3f')@Sum(points@team,N=5,format='%0.6f')>50 and team='Bears'"
    res = nfl.query(pyql)
    print "res:",res
    assert "%s"%res[0][0] == '0.599'

    pyql = "Average(points)@team=='Bears'"
    res = nfl.query(pyql)
    print "res:",res
    assert "%0.2f"%res[0][0].value() == '19.76'

    pyql = "Average(points@team=='Chargers')@1"
    res = nfl.query(pyql)
    print "res:",res
    assert "%0.2f"%res[0][0].value() == '21.95'

    nfl.show_metacode = 1

    pyql = "week,Replace(team),Sum(points)@team|($2,$3)@17 in $1"
    res = nfl.query(pyql)
    print "res:",res

    print res[0][0].value()[0][-1]
    assert res[0][0].value()[0][-1] == 4401

    pyql = "Sum(points)@(team='Bears'),(site='home') and season=2009 and playoffs=0"
    res = nfl.query(pyql)
    print "res:",res[0][0].value()
    assert res[0][0].value() in [5778,327] # which one is first?

    # some weird weighted average of opponent's points....
    pyql = "Replace(team),Average(points)[opponents and playoffs=0 and season==2007]@team and playoffs=0 and season=2007"
    res = nfl.query(pyql)
    print "res:",res
    assert "%0.2f"%res.value_from_header((('team = Falcons', 'and', 'playoffs == 0', 'and', 'season == 2007'), ('team = Falcons', 'and', 'playoffs = 0', 'and', 'season = 2007')))[1].value() == "21.26"
    start = time.time()
    res = nfl.query(pyql)
    print "query took %0.3f seconds"%(time.time()-start)
    print "res:",res

def time_nfl(nfl):
    #nfl.show_metacode = True
    t0 = time.time()
    # Lots of grouping
    #pyql = "date,team@A(points@team and passing yards and rushing yards)>30 and S(points@team and passing yards and rushing yards)>30"
    #res = nfl.query(pyql)

    # Lots of request columns, simple "where" clause
    pyql = 'R($1),R($2),R($3),R($4),R($5),R($6),R($7),R($8),R($9),R($10),R($11),R($12),R($13),R($14),R($15),R($16),R($17),R($18),R($19),R($20),R($21),R($22),R($23),R($24),R($25),R($26),R($27),R($28),R($29),R($30),R($31),R($32),R($33),R($34),R($35),R($36),R($37),R($38),R($39),R($40),R($41),R($42),R($43),R($44),R($45),R($46),R($47),R($48),R($49),R($50),R($51),R($52),R($53),R($54),R($55),R($56),R($57),R($58),R($59)@1'

    res = nfl.query(pyql)
    #print res
    t1 = time.time()
    print "%.2f" % (1000*(t1-t0))


def test_maintain():
    dt = test_dt()
    print dt
    dt.replace_row(0,{'age':89,"weight":153,"first name":'grace'})
    dt.append_row({'age':999,"weight":177,"first name":'bob'})
    dt.update_row(-1,{'height':122})
    dt.update_row(-1,{'children':['mike','ike']})
    print dt

def testit():
    dt = test_dt()
    dt.show_metacode = True
    test_suite(dt)

def timeit():
    import PyQL.inputs
    nfl = PyQL.inputs.dt_from_pickled_columns(DATA_DIR + '/_Column',name='DT',verbose=0)
    nfl.show_metacode = True
    for x in xrange(10):
        time_nfl(nfl)

if (__name__ == "__main__"):
    import PyQL.inputs # brings 'dt' into namespace, but why?
    timeit()
    testit()

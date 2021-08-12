#!/usr/bin/env python

"""
Columns making up data tables.
"""
import math,re # for use inside value = lambda
import string,sys
import PyQL.column_types
import PyQL.outputs
import PyQL.py_tools
from PyQL.cache import format_cache

import array
import gc

#import numpy as np

#masked = np.ma.masked

#def to_np(data):
#    return np.ma.masked_equal(data, None)

############# column classes ##############
# each has __init__, append, value, str methods
# append takes exactly one argument and ought to handle None cleanly

#TODO: require str_format (or otherwise inherit (often lambda) methods.)


def diff(lst):
    #return "%s"%(lst[0][0],)
    sum1 = sum(filter(lambda item:item is not None,lst[0]))
    n1 = len(filter(lambda item:item is not None,lst[0]))
    if not sum1 and not n1: return None
    sum2 = sum(filter(lambda item:item is not None,lst[1]))
    n2 = len(filter(lambda item:item is not None,lst[1]))
    if not sum2 and not n2:  return None
    return 1.*sum1/n1 - 1.*sum2/n2


class Column(object):

    __slots__ = ['unique_vals', 'data',
                 '__getitem__', '__setitem__',
                 'name', 'none_repr', 'pending_append',
                 'format', 'str_format']

    def message(self,str):
        # print in a generally inoffensive format with "Message from file.Class:" header
        print "<pre>\nMessage from %s.Column:\n%s\n</pre>\n"%(__name__,str)

    def __init__(self,
                 value='',
                 name=None,    # used for named access can be anything that a dictionary key can be
                 format=None, #format is for the elements
                 data = [],
                 none_repr = "None",
                 use_array=1, # experimental RAM saver
                 **kwargs):  # **kwargs added to Column,Tuple and Replace to allow dt to pass in N without failure (N is ignored)
        #print "columns.Column: format:",format
        if not data: data = []
        #print "columns.Column: str_format:",format
        #print 'DATA IS', type(data)
        self.data = data # "internal use only"
        self.name = name
        self.none_repr = none_repr
        self.set_format(format)
        self.pending_append = [] #[(on_change_value,value_to_append),..]

        # Delegate!  (faster than subclass)
        # NB:  this makes it impossible to override these methods in subclass!! - cgw
        self.__getitem__ = self.data.__getitem__
        self.__setitem__ = self.data.__setitem__
    # added for S2 loading of columns from a list of directories.
    #def update(self,other):
    #    for i in range(len(self.data)):
    #        self.data[i] = self.data[i] if self.data[i] is not None else other[i]

    def append(self, value):
        self.data.append(value)

    def __len__(self):
        return len(self.data)


    def append_pending(self,change_value):
        #print "columns.append_pending: change_value:",change_value
        for i in range(len(self.pending_append)-1,-1,-1):
            on_change_value, value = self.pending_append[i]
            #print "columns.append_pending: on_change_value:",on_change_value
            if change_value != on_change_value:
                self.append(value)
                del(self.pending_append[i])

    def append_on_change(self,on_change_value,value):
        #print "append_on_change.saving:",on_change_value,value
        self.pending_append.append((on_change_value,value))

    def python_repr(self): # dump to python code: assume columns in name space
        return '''columns.Column(name=%s,
                                format=%s,
                                data=%s,
                                none_repr=%s)'''%(
                                    `self.name`,`self.str_format`,self.data,`self.none_repr`)

    def set_format(self,format):
        haveit = format_cache.get(format)
        if haveit:
            self.str_format, self.format = haveit
            return

        # Set self.str_format
        if format == str:
            self.str_format = "str"
        elif type(format) is str:
            self.str_format = format
        else:
            self.str_format = str(format)

        # Set self.format
        #open('/tmp/mlb.out','w').write("readt to set self.format wth :%s"%(format,))
        if not format or format == str or format == 'None':
            self.format = str
        elif type(format) is str:
            if format.startswith("lambda"):
                self.format = eval(format) #passed in string  lambda
            else:
                self.format = lambda x,f=format: f%x # string format (eg: '%0.4f')
        else: self.format = format
        # Remember for next time!
        format_cache[format] = (self.str_format, self.format)

    def value(self):
        return self.data #[:]   # 20110729 [:] added to allow running columns. eg: 1*Column(age). but this was expensive!

    def __repr__(self):
        ret = "" #"Column instance: value = \n"
        for item in self.value():
            #print "Column: name, item:",item,self.name
            if item is None: ret += "%s\n"%self.none_repr
            else: ret += "%s\n"%(self.format(item),)
        return ret

class Unique(Column):

    def __init__(self,
                 value='',
                 name=None,    # used for named access can be anything that a dictionary key can be
                 format=None, #format is for the elements
                 data = [],
                 none_repr = "None",
                 ):
        Column.__init__(self,name=name,format=format,
                        data=[],none_repr =none_repr)
        self.unique_vals = set()
        for d in data:
            self.append(d)

    def append(self,value):
        if value in self.unique_vals:
            return
        self.unique_vals.add(value)
        self.data.append(value)

    def sort(self,c=lambda x:x[0]>x[1]): # should be "sorted"
        return sorted(self.data, c)

    def __repr__(self):
        value = self.value()
        if value is None: return self.none_repr
        return self.format(value)

# a Tuple of Column instances
class Tuple(Column):
    def __init__(self,
             name=None,
             format=None,
             data=[],
             value=None,
              **kwargs
             ):
        Column.__init__(self,name=name,format=format,data=data)
        self.value = eval(value) if value else self.default_value


    def safe_summative_diff(self): # Tuple((Sum,Sum))
        return (None if None in [self.data[0].value(), self.data[1].value()]
                else self.data[0].value() - self.data[1].value())

    def safe_summative_ratio(self): # Tuple((Sum,Sum))
        if None in [self.data[0].value(), self.data[1].value()]: return None
        if self.data[1].value() == 0: return None
        return 1.*self.data[0].value()/self.data[1].value()

    def diff(self):
        sum1 = sum(filter(lambda item:item is not None,self.data[0]))
        n1 = len(filter(lambda item:item is not None,self.data[0]))
        if not sum1 and not n1: return None
        sum2 = sum(filter(lambda item:item is not None,self.data[1]))
        n2 = len(filter(lambda item:item is not None,self.data[1]))
        if not sum2 and not n2:  return None
        return 1.*sum1/n1 - 1.*sum2/n2

    def append(self,value):
        #print "columns.Tuple.append: value:",value
        #print "columns.Tuple.append: self.data:",self.data
        if value == (None,):
            for i in range(len(self.data)):  self.data[i].append(value)
            return
        assert len(value) == len(self.data),"Cannot update column.Tuple with a value of different length:\n\tvalue=%s\n\tlen(self.data)=%d"%(
                                                 value,len(self.data))
        for i in range(len(value)):  self.data[i].append(value[i])

    def default_value(self):
        return tuple(self.data)

    def __repr__(self):
        try: value = self.value()
        except: value = None
        if value is None: return self.none_repr
        return self.format(value)

class Record_WLPM(Column):
    def __init__(self,
                 name=None,
                 format=None,
                 N = None,
                 ):
        Column.__init__(self,name=name,format=format or '''lambda x:"%d-%d-%d (%0.1f)"%(x[0],x[1],x[2],x[3])''')
        self.record = [0,0,0]
        self.count = 0
        self.total_margin = 0.0
        self.N = N
        self.data = [] # a list of margins

    def append(self,value): #value is (margin)
        if value is None: return
        self.data.append(value)
        self.record[(value<0) + 2*(0==value)] += 1
        self.count += 1
        self.total_margin += value
        if self.N and self.N<len(self.data):
            old_value = self.data.pop(0)
            self.record[(old_value<0) + 2*(0==old_value)] -= 1
            self.count -= 1
            self.total_margin -= old_value

    def value(self):
        if self.N and len(self.data)<self.N: return
        return tuple(self.record) + (self.total_margin/(self.count or 1),self.pval())
    def net_units(self,vig=0.1):
        if self.N and len(self.data)<self.N: return
        if self.record[1]<self.record[0]: return self.record[0]-(1+vig)*self.record[1]
        return self.record[1]-(1+vig)*self.record[0]
    def pval(self):
        return PyQL.py_tools.probability(self.record[0]+self.record[1],self.record[0],0.5)

    def __repr__(self):
        if self.N and len(self.data)<self.N: return
        value = self.value()
        if value is None: return self.none_repr
        return self.format(value)

#find the optimal starting date
class Best_Record(Column):
    def __init__(self,
                 name=None,
                 format=None,
                 p=0.5,               #the probability of 'heads'
                 give_up = (20,0.25),   #give up at (game, pval)
                 perfect = 0,
                 ):
        Column.__init__(self,name=name,format=format or '''lambda x:"%d-%d-%d (%0.1f)"%(x[0],x[1],x[2],x[3])''')
        self.perfect = perfect
        self.give_up = give_up
        self.record = [0,0,0]
        self.count = 0
        self.total_margin = 0.0
        self.results = [] # (margin,date)
        self.p = p
        self.date = None

    def append(self,value): #value is (margin,date)
        if value is None or value[0] is None or value[1] is None: return
        #self.record[(value<0) + 2*(0==value)] += 1
        #self.count += 1
        #self.total_margin += value
        self.results.append(value)

    def value(self):
        record = [0,0,0]
        total_margin = 0
        self.pval = 2
        count = 0
        results = self.results[:]
        results.reverse()
        for result in results: #( margin,date)
            record[(result[0]<0) + 2*(0==result[0])] += 1
            total_margin += result[0]
            count += 1
            pval = PyQL.py_tools.probability(record[0]+record[1],record[0],self.p)
            #print "columns.record, pval:",record,pval
            if pval < self.pval and not (self.perfect and record[0]*record[1]):
                #print "     columns.new best"
                self.date = result[1]
                self.record = record[:]
                self.total_margin = total_margin
                self.pval = pval
                self.count = count
            if self.give_up and self.give_up[0]<count and self.give_up[1]<pval:
                break
            if self.perfect and self.record[0]*self.record[1]!=0:
                break
        return tuple(self.record) + (self.total_margin/(self.count or 1),self.pval,self.date)

    def value_all(self,pval=None):
        self.record = [0,0,0]
        self.total_margin = 0
        self.count = 0
        if not self.results: return tuple(self.record) + (self.total_margin/(self.count or 1),0,None)
        self.date = self.results[0][1]
        for result in self.results: #( margin,date)
            self.record[(result[0]<0) + 2*(0==result[0])] += 1
            self.total_margin += result[0]
            self.count += 1
        self.pval = pval or PyQL.py_tools.probability(self.record[0]+self.record[1],self.record[0],self.p)
        return tuple(self.record) + (self.total_margin/(self.count or 1),self.pval,self.date)

    def net_units(self,vig=0.1):
        if self.record[1]<self.record[0]: return self.record[0]-(1+vig)*self.record[1]
        return self.record[1]-(1+vig)*self.record[0]

    def __repr__(self):
        value = self.value()
        if value is None: return self.none_repr
        return self.format(value)

#find the optimal starting date
# added 20060102 for MLB
class Best_Profit(Column):

    def __init__(self,
                 name=None,
                 format=None,
                 give_up = (10,0),   #give up at (N games, $won) or (N games, roi)
                 perfect = 0, # =1 means give up if ever negative; =0.9 for 90%
                 roi=0,
                 ):

        Column.__init__(self,name=name,format=format or '''lambda x:"%d-%d ($%0.0f)"%(x[0],x[1],x[4])''')
        self.roi = roi # default is to test on profit: set roi upon init.
        self.give_up = give_up
        self.record = [0,0,0]
        self.perfect = perfect
        self.count = 0
        self.total_margin = 0.0
        self.results = [] # (margin,line,date,team)
        self.date = None

    def append(self,value): #value is (margin,line,date)
        if value is None or value[0] is None or value[1] is None: return
        self.results.append(value)

    def value(self):
        record = [0,0,0]
        total_margin = 0.0
        self.profit = -9999
        self.invested = 0
        running_profit = 0
        running_invested = 0
        count = 0
        results = self.results[:]
        results.reverse()
        for result in results: #( margin,line,date,team)
            #print "result:",result,running_profit
            record[(result[0]<0) + 2*(0==result[0])] += 1
            total_margin += result[0]
            count += 1
            running_profit += ((result[1]<0)*(0<result[0]))*100 or ((0<result[1])*(result[0]<0))*(-100) or (result[0]!=0)*result[1]
            if result[1]<0: running_invested -= result[1]
            else: running_invested += 100

            #print "profit:",running_profit,"record:",record
            if self.perfect>0 and (record[0]+record[1])>0:
                #print "Best_Profit has perfect=",self.perfect
                if record[0]>=record[1] and 1.*record[0]/(record[0]+record[1]) < self.perfect:
                    break
                if record[1]>record[0] and 1.*record[1]/(record[0]+record[1]) < self.perfect:
                    break
            if self.roi and running_invested:
                give_up_value = 1.*running_profit/running_invested
            else: give_up_value = running_profit
            if self.give_up and self.give_up[0]<count and give_up_value < self.give_up[1]:
                #print "Columns.give_up"
                break
            # adhoc min of 1000 before roi kicks in
            if (self.roi and running_profit>1000 and (1.*self.profit/(self.invested or 1)  <= 1.*running_profit/running_invested) ) or  (not self.roi and self.profit < running_profit):
                self.date = result[2]
                self.record = record[:]
                self.total_margin = total_margin
                self.profit = running_profit
                self.invested = running_invested
                self.count = count
                #print "best profit:",self.profit,"best record:",self.record
        return tuple(self.record) + (1.*self.total_margin/(self.count or 1),self.profit,self.invested,self.date)

    def value_all(self):
        self.record = [0,0,0]
        self.total_margin = 0
        self.count = 0
        self.profit = 0
        self.running_invested = 0
        if not self.results: return tuple(self.record) + (self.total_margin/(self.count or 1),0,None)
        self.date = self.results[0][2]
        for result in self.results: #( margin,line,date)
            self.record[(result[0]<0) + 2*(0==result[0])] += 1
            self.total_margin += result[0]
            self.count += 1
            self.profit += ((result[1]<0)*(0<result[0]))*100 or ((0<result[1])*(result[0]<0))*(-100) or (result[0]!=0)*result[1]
            if result[1]<0: self.running_invested -= result[1]
            else: self.running_invested += 100

        return tuple(self.record) + (1.*self.total_margin/(self.count or 1),self.profit,self.running_invested,self.date)

    def __repr__(self):
        value = self.value()
        if value is None: return self.none_repr
        return self.format(value)


class Best_ROI(Best_Profit):
    # not tested. adding invested to the Best_Profit value tuple is enough.

    def __init__(self,
                 name=None,
                 format=None,
                 give_up = (10,0),   #give up at (game, $won)
                 perfect = 0, # give up if ever negative
                 ):

       Best_Profit.__init__(self,name=name,format=format,give_up=give_up,prefect=perfect,roi=1)


class Record_WLPMN(Record_WLPM): #add Netunits
    def __init__(self,
                 name=None,
                 format=None,
                 ):
        Record_WLPM.__init__(self,name=name,
                                  format=format or '''lambda x:"%d-%d-%d (%0.1f) %0.1f"%x''')

    def value(self):
        return tuple(self.record) + (self.total_margin/(self.count or 1),self.net_units())



# the number of not-None values  NB: Sum(1) might be prefered.
class Count(Column):
    def __init__(self,
                 name=None,
                 format=None,
                 ):
        Column.__init__(self,name=name,format=format or '''lambda x:"%d"%x''')
        self.name = name
        self.count = 0

    def append(self,value):
        if value is not None:
            self.count += 1

    def value(self): return self.count

    def __repr__(self):
        value = self.value()
        if value is None: return self.none_repr
        return self.format(value)

class Replace(Column):
    def __init__(self,
                 name=None,
                 format=None,
                 **kwargs
                 ):
        Column.__init__(self,name,format=format or "%s")
        self.name = name
        self.last_value = None

    def append(self,value):
        if value is not None:
            self.last_value = value

    def value(self): return self.last_value

    def __repr__(self):
        value = self.value()
        if value is None: return self.none_repr
        #print "col.repr.value:",value
        try: return self.format(value)
        except: return self.none_repr

class Max_Min(Column):
    def __init__(self,
                 name=None,
                 format=None,
                 N=None,          # the number to average over (None => all)
                 method=max
                 ):
        Column.__init__(self,name=name,format=format)
        self.N = N
        self.method = method

    def append(self,value):
        if value is not None:
            self.data.append(value)
            if self.N and self.N<len(self.data): self.data.pop(0)
    def value(self):
        len_data = len(self.data)
        if not len_data: return
        if self.N and self.N > len_data: return
        return self.method(self.data)

    def __repr__(self):
        if not self.data: return self.none_repr
        return self.format(self.value())

class Minimum(Max_Min):
    def __init__(self,
                 name=None,
                 format=None,
                 N=None,          # the number to average over (None => all)
                 ):
        Max_Min.__init__(self,name=name,format=format,N=N,method=min)
class Maximum(Max_Min):
    def __init__(self,
                 name=None,
                 format=None,
                 N=None,          # the number to average over (None => all)
                 ):
        Max_Min.__init__(self,name=name,format=format,N=N,method=max)

class Summative(Column):
    def __init__(self,
                 name=None,
                 format=None,
                 N=None,          # the number to average over (None => all)
                 value=None,       # eg "lambda s=self:(s.average,s.sum_weight)"
                 ):
        #Column.__init__(self,name=name,format=format)
        # Copy constructor stuff here for speed - cgw - is this really helpful?
        self.unique = False
        self.none_repr = "None"
        self.data = []
        self.name = name
        self.pending_append = []
        self.set_format(format)

        self.average = None
        self.sum = 0.
        self.sum_weight = 0.
        self.count = 0
        self.N = N
        if value and type(value) is str:
            self.value = eval(value)
        elif value:
            self.value = value
        else:
            self.value = lambda s=self: s.sum


    def append(self,val_weight): #val_weight can be a value, or a (val[,weight]) tuple
        #print "columns.py.Summative.append.val_weight:",val_weight
        #print "columns.py.Summative.append.value():",self.value()
        weight = 1
        val = val_weight
        #print "columns.Summative.append.val:",val
        if type(val_weight) in [type(()),type([])]:
            if len(val_weight) == 0: raise "empty list passed to Summative.append"
            elif len(val_weight) == 1: val,weight = val_weight[0],1
            else: val,weight = val_weight[0],val_weight[1]
        if val == None or weight == None: return
        # build up data only if Summative is over a range of past N values
        if self.N: self.data.append((val,weight))
        if len(self.data) < self.N:         # building up data
            self.count = self.count + 1
            return
        if self.count < self.N:             # start calculating summative values
            self.count = self.count + 1
            for v,w in self.data:
                self.sum += v * w
                self.sum_weight += w
            self.average = 1.*self.sum/self.sum_weight
            return
        self.count = self.count + 1
        self.sum += val * weight
        self.sum_weight += weight
        if self.N and self.N < len(self.data):
            v,w = self.data.pop(0)
            self.sum -= v * w
            self.sum_weight -= w
        if not self.sum_weight: return None
        self.average = 1.*self.sum/self.sum_weight

    def __repr__(self):
        ret = "Summative instance:\n"
        ret += "sum = %s\n"%self.sum
        ret += "count = %s\n"%self.count
        ret += "average = %s\n"%self.average
        ret += "sum_weight = %s\n"%self.sum_weight
        return ret

def average_line(line):
    #print "al.line:",line
    if line is None: return None
    if line>0: return line + 100
    return line - 100

class Average_Line(Summative):

    def __init__(self,
                 name=None,
                 format='%0.2f',
                 N=None,          # the number to average over (None => all)
                 ):
        Summative.__init__(self,name=name,format=format,N=N,
                                         value=lambda s=self,al=average_line:al(s.average))
    def append(self,val_weight):
        #print "A_L.append:",val_weight
        val = val_weight; weight=1
        if type(val_weight) in [type(()),type([])]:
            if len(val_weight) == 0: raise "empty list passed to Summative.append"
            elif len(val_weight) == 1: val,weight = val_weight[0],1
            else: val,weight = val_weight[0],val_weight[1]
        if val == None or weight == None: return
        val = float(val)
        if val<0:
            val = val + 100
        else: val = val - 100
        #print "A_L.float_val:",val
        Summative.append(self,(val,weight))
    def __repr__(self):
        if self.value() is None: return self.none_repr
        return self.format(self.value())

class Average(Summative):
    def __init__(self,
                 name=None,
                 format='%0.2f',
                 N=None,          # the number to average over (None => all)
                 ):
        Summative.__init__(self,name=name,format=format,N=N,value=lambda s=self:s.average)
    def __repr__(self):
        #open("/tmp/col.print",'a').write("%s"%self.average)
        if self.average is None: return self.none_repr
        return self.format(self.average)


class Sum(Summative):
    def __init__(self,
                 name=None,
                 format=None,
                 N=None,          # the number to average over (None => all)
                 ):
        Summative.__init__(self,name=name,format=format,N=N,value=lambda s=self:{(self.N<=self.count and 0<self.count):s.sum}.get(1))
    def __repr__(self):
        if self.value() is None: return self.none_repr
        return self.format(self.value())

# put these in the namespace of the parser allowing short cut access from pyql

S = Sum
A = Average
R = Replace
Min = Minimum
Max = Maximum
U = Unique
C = Column

########################################
#############  Tests and demos #############
########################################



def _test_column():
    print "_test_column"
    col = Column("bob",format="""lambda x:"value of bob is  %s"%x""")
    col.append('fred')
    print "col.str_format:",col.str_format
    print "col.format:",col.format
    print "col:",col
    print "col.value():",col.value()
    print "col.data",col.data
    print "__repr__(col):\n",col
    print "col.python_repr()",col.python_repr()


def _test_total_column():
    print "_test_column"
    col = Column("total")
    col.append(PyQL.column_types.Total(8.5))
    print "col:",(col[0]+1).nice_str()


def _test_unique():
    print "_test_unique"
    col = Unique("bob",data=[1,2,3,3],format="""lambda x:"value of unique is  %s"%(x,)""")
    col.append(('fred',4))
    col.append(('red',6))
    col.append(('red',6))
    assert (col.data == [1,2,3,('fred',4),('red',6)])
    print "col.str_format:",col.str_format
    print "col.format:",col.format
    print "col:",col
    print "col.value():",col.value()
    print "col.data",col.data
    print "__repr__(col):\n",col
    print "col.python_repr(0)",col.python_repr()

def _test_sum():
    print "_test_sum"
    col = Sum(name="height",format="%0.6f",N=2)
    col = Sum(name="height",format="lambda x,d=PyQL.outputs.dollar_format:d(x)",N=2)
    #col = Summative(name="height",value="lambda s=self:(s.average,s.sum_weight)",format="%0.2f (%0.3f)",N=3)
    col.append((4,2))
    col.append(6)
    col.append(10)
    print "col:%s"%col
    print "col.value():",col.value()
    print "col.data",col.data
    print "col.format:",col.format
    print "formatted:%s"%col

def _test_average_line():
    print "_test_average_line"
    col = Average_Line(name="mlb_line")
    col.append(-140)
    col.append(115)
    col.append(115)
    col.append(115)
    print "col.value():",col.value()
    print "formatted:%s"%col

def _test_average():
    print "_test_average"
    col = Average(name="height",N=3)
    col.append((4,2))
    col.append(6)
    col.append(10)
    print "col:",col
    print "col.value():",col.value()
    print "col.data",col.data
    print "col.format:",col.format
    print "formatted:%s"%col

def _test_count():
    print "_test_count"
    col = Count("bob")
    col.append('a')
    col.append('b')
    print "col:",col
    print "col.value():",col.value()
    print "col.data",col.data
    print "__repr__(col):\n",col

def _test_replace():
    print "_test_replace"
    col = Replace()
    col.append('a')
    col.append('b')
    print "col:",col
    print "col.value():",col.value()
    print "col.data",col.data
    print "__repr__(col):\n",col

def _test_maximum():
    print "_test_maximum"
    #col = Maximum(N=3)
    col = Minimum(N=5)
    col.append(100)
    col.append(110)
    #col.append(None)
    col.append(15)
    col.append(25)
    col.append(15)
    print "col:",col
    print "col.value():",col.value()
    print "col.data",col.data
    print "__repr__(col):\n",col

def _test_record_wlpmn():
    print "_test_record_wlpm"
    col = Record_WLPMN()
    col.append(2)
    col.append(2.5)
    col.append(1.5)
    print "col:",col
    print "col.value():",col.value()
    print "col.data",col.data
    print "col.pval",col.pval()
    print "__repr__(col):\n",col

def _test_record_wlpm():
    print "_test_record_wlpm"
    col = Record_WLPM(format='''lambda x:'%s-%s (%0.1f%%)'%(x[0],x[1],100.*x[0]/(x[0]+x[1]))''')
    t = PyQL.column_types.Total(4)
    col.append(2+t)
    col.append(-5+t)
    print "col:",col
    print "col.value():",col.value()
    print "col.data",col.data
    print "col.pval",col.pval()
    print "__repr__(col):\n",col

def _test_best_record():
    print "_test_best_record"
    col = Best_Record()
    col.append((-2,20031101))
    col.append((2.5,20031108))
    col.append((1.5,20031115))
    col.append((1.5,20031116))
    print "col:",col
    print "col.value():",col.value()
    print "col.data",col.data
    print "col.pval",col.pval
    print "__repr__(col):\n",col

def _test_best_profit():
    print "_test_best_record"
    col = Best_Profit(perfect=1)
    col.append((-1,-200,20030401,'Cubs'))
    col.append((-2.,-140,20030402,'Cubs'))
    col.append((2,200,20030403,'Reds'))
    col.append((1,-150,20030410,'Braves'))
    col.append((-2,140,20030522,'Cubs'))
    col.append((1,-105,20030530,'Cubs'))
    print "col:",col
    print "col.value():",col.value()
    print "col.data",col.data
    print "col.profit",col.profit
    #print "__repr__(col):\n",col

def _test_tuple():
    print "_test_tuple"
    #col = Tuple(data=(Sum(),Average()),format="Sum:%s and Avg:%s")
    col = Tuple(data=(Sum(),Average()),value="lambda s=self,math=math:math.pow(s.data[0].value()/s.data[1].value(),2)")
    #col = Tuple(data=(Sum(),Average()),value="self.safe_summative_diff")
    col.append((3,3))
    col.append((6,6))
    col.append((None,4.5))
    #col.append((5,None))
    print col

def _test_weighted_average():
    print "_test_weighted_average"
    col = Average(format='%0.1f')
    #col = Summative(name="height",value="lambda s=self:(s.average,s.sum_weight)",format="%0.2f (%0.3f)",N=3)
    col.append((4,2))
    col.append((6,1))
    col.append((10,2))
    print col

def _test_misc():
    print "_test_misc"
    col = Column(name='bob',format='%0.1f-%0.1f')
    #col = Summative(name="height",value="lambda s=self:(s.average,s.sum_weight)",format="%0.2f (%0.3f)",N=3)
    col.append((4,2))
    col.append((6,1))
    col.append((10,2))
    print col


if ( __name__ == "__main__" ):
    #_test_misc()
    #_test_column()
    #_test_sum()
    #_test_average()
    #_test_average_line()
    #_test_count()
    #_test_replace()

    _test_unique()
    #_test_record_wlpmn()
    #_test_record_wlpm()
    #_test_tuple()
    #_test_weighted_average()
    #_test_best_record()
    # _test_best_profit()
    #_test_maximum()
    #_test_set()

from PyQL.py_tools import add_days_to_date,delta_days

class Date(int):
    def __init__(self,value):
        assert type(value) in [Date,int] and len(str(value)) == 8
        self.value = value
    def __radd__(self,other):
        return Date(add_days_to_date(self.value,other))
    def __add__(self,other):
        return Date(add_days_to_date(self.value,other))
    def __mul__(self,other):
        return Date(self.value*other)
    def __rmul__(self,other):
        return Date(self.value*other)
    def __sub__(self,other):
        if isinstance(other,Date):
            return delta_days(self.value,other)
        return Date(add_days_to_date(self.value,-other))
    def nice_str(self):
        if not self.value: return self.value
        str_val = str(self.value)
        return "%s-%s-%s"%(str_val[4:6],str_val[6:],str_val[:4])

class MLB_Line(int):
    def __init__(self,value):
        #print "__init__ Line with `%s` type `%s`"%(value,type(value))
        self.value = value

    def math_value(self,v):
        if not v: return v
        if v <= -100: return int(v) + 100
        if v >= 100: return int(v) - 100

    def mlb_value(self,math_value):
        if math_value >= 0: return int(math_value) + 100
        if math_value < 0: return int(math_value) - 100

    def __add__(self,other):
        if isinstance(other,MLB_Line):
            return self.math_value(self.value)+self.math_value(other.value)
        return MLB_Line(self.mlb_value(self.math_value(self.value)+other))
    def __radd__(self,other):
        return self.__add__(other)
    #def __mul__(self,other):
    #    return MLB_Line(self.value*other)
    #def __rmul__(self,other):
    #    return MLB_Line(self.value*other)
    def __sub__(self,other):
        if isinstance(other,MLB_Line):
            return self.math_value(self.value)-self.math_value(other.value)
        return MLB_Line(self.mlb_value(self.math_value(self.value)-other ))

class Total(float):
    def __init__(self,value):
        self.value = value
    def __radd__(self,other):
        return Total(self.value+float(other))
    def __add__(self,other):
        return Total(self.value+float(other))
    def __mul__(self,other):
        return Total(self.value*float(other))
    def __rmul__(self,other):
        return Total(self.value*float(other))
    def __sub__(self,other):
        return Total(self.value-float(other))
    def __rsub__(self,other):
        return Total(float(other)-self.value)
    def nice_str(self):
        ret = "%0.1f"%self.value
        if ret[-2:] == '.0': return ret[:-2]
        if ret[-2:] == '.5': return ret[:-2]+"'"
        return ret
    def __str__(self):
        return self.nice_str()

############# tests and demos ######

if __name__ == "__main__":
    t = Total(7.5)
    t = 3-t
    print "%s"%t
    print t.nice_str()

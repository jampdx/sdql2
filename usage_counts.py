import glob,os
import PyQL.py_tools

def show_counts(start=None,stop=None):
    cipd = {} # [ip]=count
    date = start
    while date<=stop:
        print "looking in",date
        for f in glob.glob(os.path.join("/home/jameyer/S2/Log/Count",str(date),'*')):
            c = int(open(f).read())
            ip = os.path.basename(f)
            cipd.setdefault(ip,0)
            cipd[ip] += c
        date += 1
    cips = []
    for ip in cipd.keys():
        cips.append((cipd[ip],ip))
    cips.sort()
    for cip in cips:
        print cip


if __name__ == "__main__":
    import sys,string
    start = stop = 0
    for arg in sys.argv[1:]:
        if '=' not in arg:
            arg = arg+"=1"
        var, val = string.split(arg,'=')
        try:              #first ask: Is this in my name space?
            eval(var)
        except:
            print "Can't set", var
            sys.exit(-1)
        try:
            exec(arg)  #numbers
        except:
            exec('%s="%s"' % tuple(string.split(arg,'='))) #strings
    if not start:
        start = PyQL.py_tools.today()
    else:
        start = PyQL.py_tools.Date8(start)
    if stop: stop = PyQL.py_tools.Date8(stop)
    else:stop = start
    show_counts(start=start,stop=stop)

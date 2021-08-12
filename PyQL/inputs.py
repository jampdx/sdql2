import string, re, os
from PyQL.dt import  DT
import py_tools, columns
import cPickle
import glob
import PyQL.column_types

def type_of_tuple_items(t):
    for item in t:
        if item is not None:
            return type(item)
    return type(None)

def typed_or_none(x,x_type):
    if x is None: return None
    try: return x_type(x)
    except: return None

ht_pat = re.compile("(.*)<(.*)>")
def  headers_types_from_headers(headers):
    ret_h = []
    ret_t = []
    for header in headers:
        found = ht_pat.findall(header)
        if found:
            ret_h.append(found[0][0])
            ret_t.append(eval(found[0][1]))
        elif header == 'date':
            ret_h.append(header)
            ret_t.append(eval('PyQL.column_types.Date'))
        else:
            ret_h.append(header)
            ret_t.append(None)
    return ret_h, ret_t


def dt_from_file(file,
                 name="DT",
                 headers=None,   # if not headers than take from file
                 column_types=None,   # if not types, look in header for eg <type: str> then guess
                 delim_row='\n',delim_column='\t',null='',verbose=0,  # fields for parsing text file
                 build_lexer=True,
                 dt=None,
                 protect_braces=1,
                 protect_single_quotes=1,
                 protect_double_quotes=1,
                 file_is_data=0,
                 nrows=None, # None is all
                 ):
    if file_is_data:
        txt = file
    else:
        txt = open(file).read()
    file_headers,data = py_tools.tuple_of_tuples_from_txt(txt,
                                                          delim_column=delim_column,
                                                          delim_row=delim_row,
                                                          null=null,
                                                          verbose=verbose,
                                                          has_header=not headers,
                                                          protect_single_quotes=protect_single_quotes,
                                                          protect_double_quotes=protect_double_quotes,
                                                          protect_braces=protect_braces)
    #print "inputs got data:",data
    if not headers: headers = map(lambda x:string.strip(re.sub("[\s]+",' ',x)),file_headers)
    if not column_types:
        headers,column_types = headers_types_from_headers(headers)
    if dt is None: dt = DT(name=name)
    for i in range(nrows or len(headers)):
        #print i,headers[i],type(data[i])
        #if i == 15: print data[i]
        if not column_types[i]:
            column_type = type_of_tuple_items(data[i])
        else:
            column_type = column_types[i]
        if verbose: print "loading %s as type %s"%(headers[i],column_type)
        #data_column = tuple(map(lambda x,dt=column_type:typed_or_none(x,dt),data[i]))
        data_column = map(lambda x,dt=column_type:typed_or_none(x,dt),data[i])
        #print "column_type",column_type
        format = { int: "%d", float: "%0.2f"}.get(column_type, " '%s' ")
        #print "format:",format
        dt.add_object(columns.Column(name=headers[i],data=data_column,format=format))
    if build_lexer:
        dt.build_lexer()
    #print "inputs returning:",str(dt.data).replace('\n',' ')
    return dt

# look to column names for files
def append_from_pickled(dt,directory,
                        verbose=0):
    # make sure all fields are of the same length.
    # add [None]*len for missing fields
    if verbose: print "adding pickled data from",directory
    len_cols = None

    for column in dt.data:
        name = column.name
        if verbose: print "adding pickled data for",name
        filename = os.path.join(directory,name)
        print "looking for file",filename
        if not os.path.isfile(filename):
            if verbose: print "No pickle found for %s. Adding Nones"%name
            column.append([None]*len_cols) # first column needs to exist
            continue
        f = open(filename,'r')
        col = cPickle.load(f)
        len_col = len(col)
        if len_cols is None: len_cols = len_col
        elif len_cols != len_col: raise "Mismatch"
        column.data += col
    return dt

def auto_format(lst):
    lst = filter(lambda x: x is not None,lst)
    if not lst: return "%s"
    if type(lst[0]) is int: return "%d"
    if type(lst[0]) is float: return "%0.2f"  # WTQ this is kind of random
    return "%s"

# look to file system for columns
# 20130622 overwrite existing
def append_from_pickled_columns(dt,directory,
                                owner=None, # if owner prepend `owner.` to each parameter name
                                dict_to_dt=0,
                                verbose=False):
    # make sure all fields are of the same length.
    # add [None]*len for missing fields
    if verbose: print "adding pickled data from",directory
    len_cols = None
    for filename in glob.glob(os.path.join(directory,"*")):
        basename = os.path.basename(filename)
        name = basename
        if name[-4:] == ".pkl": name = name[:-4]
        #name = name.split(".")[0]
        if owner: name = "%s.%s"%(owner,name)
        if not os.path.isfile(filename):
            continue # directory
        if verbose: print "adding pickled data for",name
        f = open(filename,'r')
        upick = cPickle.load(f)
        f.close()
        if type(upick) is list:
            if 0 and dict_to_dt and len(upick) and type_of_tuple_items(upick) is dict and not basename.startswith('_'):
                upick = dt_from_list_of_dicts(upick)
                cformat = '%s'
                if verbose: print "moved from list of dicts to dt in inputs"
            else:
                cformat = auto_format(upick)
            column = columns.Column(data=upick,name=name,format=cformat)
        elif type(upick) is dict:
            upick.setdefault("name",name) # name is defined in pickled columns haben fortfahrt
            column = columns.Column(**upick) # this is a good way to bring a predefined array into the database
        else:
            raise Exception("Error in inputs.py: column type for %s (%s) is not allowed"%(name,type(upick)))
        if len_cols is not None and len_cols != len(column.data): raise
        offset = dt.offset_from_header(name)
        if offset is not None:
            if verbose: print "replacing column for",name
            dt.data[offset] = column
        else:
            dt.add_object(column)
        #dt.headers.append(column.name)
    dt.build_lexer()
    return dt

def dt_from_pickled_columns(directory,name='DT',verbose=0):
    dt = DT(name=name)
    append_from_pickled_columns(dt,directory,verbose=verbose)
    return dt

def columnize_pickled_dicts(dict_glob,column_dir):
    #print "inpouts.cpd glob at:",dict_glob
    cd = {}
    len_data = -1
    for f in glob.glob(dict_glob):
        #print "inpouts.f:",f
        f = open(f)
        d = cPickle.load(f)
        f.close()
        if not d: continue
        len_data += 1
        keys = dict.fromkeys(cd.keys() + d.keys()).keys()
        for key in keys:
            cd.setdefault( key, [None]*len_data ).append( d.get(key, None) )

    for key in cd.keys():
        fout = open(os.path.join( column_dir, "%s.pkl"%key ),'w')
        cPickle.dump(cd[key],fout)
        fout.close()


def csv_to_pickle(fname,delim_column=',',sort=None,protect_braces=1,protect_single_quotes=1,
                  protect_double_quotes=1,nrows=None,verbose=0):
    dt = dt_from_file(fname,delim_column=delim_column,protect_braces=protect_braces,protect_single_quotes=protect_single_quotes,
                      protect_double_quotes=protect_double_quotes,verbose=verbose)
    #print 'dtoo',dt[0][0]
    if sort:
        #print "csv_to_p sorting"
        dt.sort_by_column(dt.offset_from_header(sort),compare=lambda x,y:cmp(y,x))
        #print 'oo',dt[0][0]
    pdir = os.path.split(fname)[0].replace("_Raw","_Column")
    for col in dt:
        name = col.name
        print "pickling",name
        fout = open(os.path.join( pdir, "%s.pkl"%name ),'w')
        cPickle.dump(col.data,fout)
        fout.close()

def dt_from_dict_of_lists(dols,name='DT'):
    dt = DT(name=name)
    for k in dols.keys():
        dt.add_object(columns.Column(name=k,data=dols[k]))
    return dt

def dt_from_list_of_dicts(lods):
    cd = {}
    nd = -1
    for d in lods:
        #print "d:",d
        nd += 1
        for key in set(d.keys()+cd.keys()):
            cd.setdefault(key,nd*[None])
            cd[key].append(d.get(key))
    dt = dt_from_dict_of_lists(cd)
    #dt.build_lexer() # need to figure out how to do this once per column - not per cell.
    return dt




###### tests and demos ####
def test_from_file():
    dt = dt_from_file("/home/jameyer/PyDB/Apps/Paypal/Data/_Raw/Paypal.csv")
    print "loaded dt with headers:",dt.headers
    return dt

def test_from_dir():
    dt = DT()
    dt = append_from_pickled_columns(dt,"/home/jameyer/S2/MLB/Data/Schedule/Columns")
    print "loaded dt with headers:",dt.headers
    return dt

def test_dt_from_lod():
    l = []
    l.append({'name':'Bob','height':66,'weight':165})
    l.append({'name':'Fred','height':68,'weight':159})
    dt = dt_from_list_of_dicts(l)
    dt.build_lexer()
    print "got dt",dt
    print "q",dt.query('name@height')

if __name__ == "__main__":
    #dt = test_from_file()
    #dt = test_from_dir()
    #csv_to_pickle("/home/jameyer/PyDB/Apps/Paypal/Data/_Raw/Paypal.csv",sort="Date")
    #test_dt_from_lod()
    import argparse
    parser = argparse.ArgumentParser(description="Build Columns")
    parser.add_argument("-g","--globber", help="glob of raw file(s)")
    args = parser.parse_args()
    if not args.globber:
        print "need to pass in a globber for file(s) to parse with -g=my_globb*"
    else:
        csv_to_pickle(args.globber)

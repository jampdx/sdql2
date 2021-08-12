# towards generic database tools
# MLB doesn't work because of double header in key
# MLB and NHL do not work beause of line
import os, cPickle
import PyQL.py_tools as py_tools
import  PyQL.inputs

# keys are eg: home points, temperature (or t:points, temperature)
# apply [home |t:] parameter to one side and a naked parameter to both sides
def fold_dict_by_site(data):
    ret_dict = {}
    for dk in data.keys():
        nk = dk.replace("t:","home ").replace("o:","away ")
        site_parameter = nk.split(' ',1)
        if len(site_parameter) == 2 and site_parameter[0] in ['home','away']:
            site,parameter = site_parameter
            ret_dict.setdefault(parameter,[None,None])
            ret_dict[parameter][{'home':0,'away':1}[site]] = data[dk]
        else:
            ret_dict[dk] = [ data[dk], data[dk] ] # apply (eg temperature) to both sides
    return ret_dict


# generic dataloader : get headers from dict keys.
# expect keys of form: (home|away)? parameter.  If no site is given (eg temperature) apply to both sides
# writes _Column/key.pkl files
# 20130622 if key[0] == '/' this is a sub table
#          pass in a list of dirs to find a pickle: save to the _Column dir of pkl_dir[0]
# 20140905 above takes first available pkl_file. Now update each one after the other: the last now has priority. Use `take_first` to recover from this.
def columnize(sdb,pkl_dirs,verbose=0,
              take_first=0, # take the first available file
              overwrite=0,   # overwrite each file in turn (0 to update from each file in turn
              keys = []     # only save these keys (!keys for all)
              ):
    #print 's2.columize at keys:',keys,"with",pkl_dirs
    if type(pkl_dirs) is str: pkl_dirs = [pkl_dirs]
    cd = {}
    len_data = len(sdb[0])
    if verbose: print "loading data into sdb with %d `rows`."%len_data
    res = sdb.query("(date,team,_i)@1")[0][0]
    missing = []
    today = py_tools.today()
    for date,team,gi in res:
        if gi%2: continue  # data are saved by home team

        if verbose: print "loading data for :",date,team,gi

        bname = "%s_%s.pkl"%(date,team)
        if take_first:
            for pkl_dir in pkl_dirs:
                fname = os.path.join(pkl_dir,bname)
                if os.path.isfile(fname):
                    pkl_dirs = [pkl_dir]
                    break
        if verbose: print "from",pkl_dirs,bname
        if not filter(lambda x,b=bname:os.path.isfile(os.path.join(x,b)),pkl_dirs):
            d = {} # still need to append Nones
            if date<today:
                missing.append(bname)
                #print "s2.build missing",bname
        else:
            d = {}
            for pkl_dir in pkl_dirs:
                fname = os.path.join(pkl_dir,bname)
                #print "s2.build loading from",fname
                if os.path.isfile(fname):
                    f = open(fname,'r')
                    if overwrite:
                        d = cPickle.load(f)
                    else:
                        if verbose: print "S2.build.pkl_dir: updating from", fname
                        d.update(cPickle.load(f))
                if verbose: print "S2.bild. wtih:",d

        for key in d.keys():
            #print "s2.build raw key",key
            if key.startswith('t:'):
                sites = [0]
                header = key[2:]
            elif key.startswith('o:'):
                sites = [1]
                header = key[2:]
            elif key.split()[0] in ['home','away']  : # look for home|away header
                parts = key.split()
                if parts[0] == 'home':
                    sites = [0]
                    header = key[5:]
                elif parts[0] == 'away':
                    sites = [1]
                    header = key[5:]
            else:
                sites = [0,1]
                header = key
            if not header:
                if verbose: print "Blank header: continue"
                continue
            if header in ["team","date"]:
                if verbose: print "Can't update primary key:",header
                continue
            if header[0] == "/": # player level data
                if sites != [0]: continue
                cd.setdefault(header,{})
                cd[header].setdefault('_game',[]) # so this player table can find the games table
                table_idx = {'home':{},'away':{}} # {site:{p:batter dt index,..}}  so games dt can find players in this table
                for site in 'home','away':
                    for pd in d.get("%s %s"%(site,header),[]): # a list of dictionaries.
                        table_idx[site][pd['name']] = len(cd[header].get('name',[]))
                        known_keys = set(pd.keys() + cd[header].keys())
                        for ph in known_keys:
                            if ph == "_game": continue
                            cd[header].setdefault(ph,[None]*len(cd[header]['_game']))
                            cd[header][ph].append(pd.get(ph))
                        cd[header]['_game'].append(gi+ (site=='away') ) # so that this table can find the game
                    table_idx_header = '_'+header[1:].lower()
                    cd.setdefault(table_idx_header,[None]*len_data)
                    cd[table_idx_header][gi + (site=='away')*1] = table_idx[site]
            else:
                cd.setdefault(header,[None]*len_data)
                for site in sites:
                    #print "setting %s at %d to %s"%(header,start_i+site,d[key])
                    cd[header][gi + site] = d[key]
    if verbose: print "ready to pickle keys:",cd.keys()
    for key in cd.keys():
        #print "S2.build.key:",key
        if keys and key not in keys: continue
        dout = pkl_dirs[0].replace("_Pickle","_Column")
        if not os.path.isdir(dout):
            os.mkdir(dout)

        if key[0] == '/':
            dout = os.path.join(dout,key[1:])
            #print "S2.build ready to pickle to directory dout:",dout
            if not os.path.isdir(dout):
                os.makedirs(dout)
            for pkey in cd[key]:
                if verbose: print "pickling",key,pkey,"len:",len(cd[key][pkey])
                fout = os.path.join( dout, "%s.pkl"%pkey)
                #print "saving to",fout
                cPickle.dump(cd[key][pkey],open(fout,'w'))

        else:
            if verbose: print "pickling",key,"len:",len(cd[key])
            fout = os.path.join( dout, "%s.pkl"%key)
            cPickle.dump(cd[key],open(fout,'w'))

    if verbose: print "missing:", len(missing), missing[:100]

# create columns from picked dictionaries: dictionbary keys map to column names (folded by site)
# pickled files are expected to be date_team.pkl (MLB will need DH as well)
# expect keys of form: (home|away|t:|o:)? parameter.  If no site is given (eg temperature) apply to both sides
# TODO: handle special headers for sub tables (eg players)
def XXXcolumnize(sdb,pkl_dir,overwrite_with_None=1,verbose=0):
    cd = {}
    len_data = len(sdb[0])
    print "writing data columns from %s."%pkl_dir
    col_dir = pkl_dir.replace("_Pickle","_Column")
    if not os.path.isdir(col_dir):
        os.mkdir(col_dir)
    # assuming the database has keys from the schedule_columns
    sdql_c = '1'
    res = sdb.query("(date,team,_i)@%s"%sdql_c)[0][0]
    #print "res:",res
    missing = []
    today = PyQL.py_tools.today()
    for date,team,i in res:
        if i%2: continue  # data are saved by home team
        if verbose: print "loading data for:",date,team
        fname = os.path.join(pkl_dir,"%s_%s.pkl"%(date,team))
        #print "looking for",fname
        if not os.path.isfile(fname):
            updict = {} # still need to append Nones
            if today and date<today:
                missing.append(fname)
                if verbose: print "missing",fname
        else:
            f = open(fname,'r')
            data = cPickle.load(f)
            updict = fold_dict_by_site(data)

        for key in updict.keys():
            cd.setdefault(key,len_data*[None])
            for s in 0,1:
                val = updict[key][s]
                if val is not None or overwrite_with_None:
                    cd[key][i+s] = val

    print "missing:", len(missing),missing

    for key in cd.keys():
        print "pickling",key,"len:",len(cd[key])
        cPickle.dump(cd[key],open(os.path.join(pkl_dir,"..","_Column","%s.pkl"%(key,)),'w'))

# f is in a ../_Raw directory an fout has the same name in ../_Pickle
# special treatment for `line` header
def pickles_from_flat_file(f,delim='\t'):
    din = PyQL.inputs.dt_from_file(f,delim_column=delim,build_lexer=False)
    #print f,din
    date_offset = din.offset_from_header("date")
    home_team_offset = din.offset_from_header("home team")
    for i in range(len(din[0].data)):
        h = -1
        d = {} # data dict
        for header in din.headers:
            h += 1
            val = din[h][i]
            #parts = header.split()
            #if parts[0] not in ["home","away"]:
            #    if parts[0] == 'line':
            if header == "line":
                if val is not None: a_val = -1*val
                else:  a_val = val
                d["home %s"%header] = val
                d["away %s"%header] = a_val
            elif header not in ['date','home team']: # don't save key in file
                d[header] = val
        date = din[date_offset][i]
        home_team = din[home_team_offset][i]
        fout = os.path.join( os.path.dirname(f).replace("_Raw","_Pickle"), "%s_%s.pkl"%(date,home_team))
        cPickle.dump(d,open(fout,'w'))

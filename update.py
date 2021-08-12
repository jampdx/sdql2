"""
Update the database from a client entered form with fields or from text data with headers
"""
import datetime
import traceback
import os,sys,string,re,urllib,cPickle
import S2.common_methods
import PyQL.outputs
import PyQL.inputs
import PyQL.html_tools
import S2.formats

from S2.directory import CLIENT_DIR, LOG_DIR, RESTART

#  allow clients to upload files of several and various formats and have these magic parsers sort them out
# parse returns ('Owner/Flavor',parsed dictionary
import MLB.parser
import CFL.parser
import NCAAFB.parser
import NBA.parser

PARSERS = {'mlb':MLB.parser.parse,
           'cfl':CFL.parser.parse,
           'ncaafb':NCAAFB.parser.parse,
           'nba':NBA.parser.parse
           }
# util for fortail m_fields: give instructions and form to name the fields
def input_field_names(**kwargs):
    html = "Use this page to input custom data fields.<BR>"
    html += "Clients are allowed two fields each - if you need more write us at: <a href=mailto:support@sportsdatabase.com>support@SportsDatabase.com</a><p>"
    html += "Use the form below to enter the names of your custom field(s).<BR>"
    #html += "If your field refers to both sides of the game (like `turf type`) do not use a parameter prefix: just use <em>turf type</em>.<p>"
    #html += "If your field refers to one side of the game (like `blitzes` for the NFL) use the parameter prefixes 't:' and 'o:'.<BR>"
    #html += "For example to enter the team and opponents blitzes you would enter the fields: <em>t:blitzes</em> and <em>o:blitzes</em><p>"
    html += "<form method=get>field names %s %s"%(PyQL.html_tools.input(name='fields'),PyQL.html_tools.input(name='fields'))
    html += "<input type='submit' name='submit value='submit'> </form>"
    return html

# util for form_fields
def input_dates(hide_fields, **kwargs):
    html = "Enter the date you want to start entering data and the number of days forward from that date.<p>"
    html += "The 8 digit date format YYYYMMDD is required.<BR>"
    html += "For example to enter data for games on September 10th, 2012 use: <em>20120910</em>"
    html += "<form method=get>start date: %s number of dates: %s"%(PyQL.html_tools.input(name='date',size=10),PyQL.html_tools.input(name='dates',size=5))
    for field in hide_fields: # need to pass these through
        html += PyQL.html_tools.input(name='fields',value=field,type='hidden')
    html += "<input type='submit' name='submit value='submit'> </form>"
    return html

def form_csv(**kwargs):
    #print "kw:",kwargs
    client = kwargs["client"]
    sport = kwargs["sport"]
    parameter = kwargs.get('parameter')
    default_txt = ''
    if parameter:
        fname = parameter.replace(' ','-')  + '.lbd' # look back dict
        f = os.path.join(CLIENT_DIR,client,sport.upper(),'Data','_Raw',fname)
        if os.path.isfile(f):
            default_txt = open(f).read()
    rewrite = kwargs.get("rewrite",1) # not tested
    html = ''
    html += "<P>Paste your csv data below"
    #html += " or select a file to upload:"
    #html += "<form method=post  ENCTYPE='multipart/form-data'><input TYPE='file' NAME='_csv_%s_%s'>"%(sport,client)
    #html += "<input type='submit' name='submit' value='upload'></form>"
    #html += "In either case," here are the rule:<BR>"
    html += "&nbsp;The first row must have the data headers.<BR>"
    if sport != 'mlb': html += "&nbsp;The first two headers must be date,t:team<BR>"
    else: html += "&nbsp;The first three headers must be date,t:team,double header<BR>"
    html += "&nbsp;Data fields applying to one side need t: or o:<p>"
    html += "For example: to set the home team line to 150, the away team line to -170, and the total to 5.5 for the Maple Leafs on 20151008 use:<BR>"
    html += "<pre>date,t:team,t:line,o:line,total<BR>"
    html += "20151008,Maple Leafs,150,-170,5.5</pre><br>"
    html += "<form method=post>"
    html += "<input type='hidden' name='rewrite' value='%s'>"%rewrite
    html += "<input type='submit' name='submit' value='paste your csv file below and click here to submit'><BR>"
    html += "<textarea name='_csv_%s_%s' cols=120 rows=40>%s</textarea>"%(sport,client,default_txt)
    html += "</form>"
    return html

def post_csv_fields(**kwargs):
    client = kwargs["client"]
    sport = kwargs["sport"]
    rewrite = kwargs.get('rewrite',1) # overwrite any existing file: turn off to update any existing file. NOT TESTED
    delim = kwargs.get('delim',',')
    #print 'post kwargsL',kwargs.keys()
    csvk = filter(lambda x:x.startswith('_csv_'),kwargs.keys())[0]
    #print "csvk",csvk,kwargs[csvk]
    f_sport,f_client = csvk.split('_')[-2:]
    if f_sport != sport or f_client != client: raise Exception('mismatch in sport or client')
    lines = kwargs[csvk].splitlines()
    headers = map(lambda x:x.strip(),lines[0].split(delim))
    #print "headers:",headers
    if headers[0] == 'start date' and headers[1] in ['t:team','team']:  # a look-back dict
        # this just dumps a file in the clients Data/_Raw dict.
        # since the database is needed for a look-back dict, the database loader does the work
        # TODO: add some row/column error checking here.
        fname = "_".join(headers[2:]).replace(' ','-')  + '.lbd' # look back dict
        rdir = os.path.join(CLIENT_DIR,client,sport.upper(),'Data','_Raw')
        if not os.path.isdir(rdir): os.makedirs(rdir)
        csv_text = kwargs[csvk].replace("'",'') # no quotes here

        try:
            ftemp = "/tmp/%s.test"%fname
            open(ftemp,'w').write(csv_text)
            #print "testing format of %s join"%fname
            jdt = PyQL.inputs.dt_from_file(ftemp,delim_column=',')
        except Exception,s:
            return "An error occured<p><font color='FF0000'>%s</font>"%s




        open(os.path.join(rdir,fname),'w').write(csv_text)
        RESTART(sport=sport,flavor="query")

        return 'Your start-date data for <em>%s</em> will be available in a few minutes.'%(
                                                                              fname.replace('_',', '))
    if headers[0] != 'date': return 'Error the first field must be <em>date</em>'
    if headers[1] != 't:team': return 'Error the second field must be <em>t:team</em>'
    if sport == 'MLB' and headers[2] != 'double header': return 'Error the third field for MLB must be <em>double header</em> 0,1, or 2'
    pending = [] # for pending update file
    pdir = os.path.join(CLIENT_DIR,client,sport.upper(),'Data','_Pickle')
    cdir = os.path.join(CLIENT_DIR,client,sport.upper(),'Data','_Column')
    if not os.path.isdir(pdir): os.makedirs(pdir)
    if not os.path.isdir(cdir): os.makedirs(cdir)
    for line in lines[1:]: # dump a dict for each line
        #print "apring line:",line
        fields = line.split(delim)
        #print "fields,len:",fields,len(fields)
        if sport=='mlb':
            fout = os.path.join(pdir,'%s_%s_%s.pkl'%(fields[0],fields[1],fields[2]))
            start = 3
        else:
            fout = os.path.join(pdir,'%s_%s.pkl'%(fields[0],fields[1]))
            start=2
        pout = "%s=%s"%(client,fields[0])
        if pout not in pending:
            pending.append(pout)

        if not rewrite and os.path.isfile(fout): # update any existing dict
            dout = cPickle.load(open(fout))
        else: dout = {}                          # fresh dict
        for f in range(start,len(fields)):
            #print "f,heaers[f]",f,headers[f]
            if headers[f] == 'o:team': continue
            daton = fields[f].strip()
            if not daton: continue
            try:
                if int(float(daton)) == float(daton): daton = int(daton)
                else: daton = float(daton)
            except:  pass # eventually add other types: list, dict?
            dout[headers[f]] = daton
        #print "pickig doiut:",dout
        cPickle.dump(dout,open(fout,'w'))
    open(os.path.join(LOG_DIR,"%s_client_data.pending"%sport.lower()),'a').write('\n'.join(pending)+'\n')
    return "wrote %d fields for %d games.<p>These data will be available from the query page within 5 minutes."%(
        len(fields)-2+1*(sport=='mlb'),len(lines)-1,)


def place_prefix(pre,field):
    # put prefix just before field
    parts = field.split(':')
    if len(parts) == 1:
        return "%s:%s"%(pre,field)
    return ':'.join(parts[:-1] + [field] + parts[-1:])

def fix_side_prefixes(fields):
    # if a field has no prefix, add entries for both t:field and o:field
    pat = "(.*)([to]:)(.*)"
    ret = []
    for field in fields:
        mo = re.findall(pat,field)
        if len(mo) == 0:
            ret.append(place_prefix('t',field))
            ret.append(place_prefix('o',field))
            print "ret0:",ret
        elif len(mo) == 1:
            # need to move possible t:Owner.Sub:field ==> Owner.Sub:t:field
            if '.' not in mo[0][-1]: # not t:Owner.field
                ret.append(field)
            else:
                o,f = mo[0][-1].split(':') # only one : expected
                ret.append(mo[0][0]+o+':'+f)
        else:
            raise Exception("Unexpected number of prefixes in %s."%(field,))
    return ret

def form_fields(sdb,**kwargs):
    client = kwargs.get("client")
    sport = kwargs.get("sport")
    write_as = kwargs.get("write as")
    box = kwargs.get('box') # just give an upload input # each sport should parse these in post
    expand_sides = kwargs.get("expand sides",1) # add t: o: to each field
    rewrite = kwargs.get('rewrite',1) # overwrite any existing file: turn off to update any existing file.
    #defined_fields = S2.directory.data_columns(client,sport)
    #if defined_fields: field_text = ",".join(defined_fields)
    #else:
    #    field_text = kwargs.get("fields") # comma delimted string ready for select clause
    #    if type(field_text) is list: field_text = ",".join(field_text)
    fields = kwargs.get("fields",S2.directory.data_columns(client,sport) )
    if type(fields) is str: fields = fields.split(',')
    date = kwargs.get("date")
    default_dates = 2
    if sport.lower() in ['nfl','ncaafb']: default_dates=7
    dates = kwargs.get("dates",default_dates)
    if not client or client == "guest":
        return "You need to be logged in to use thdis page!"
    if box:
        fields = ["_file_box"]

    if not fields or not [f for f in fields if f]:  # have to define something
        return input_field_names(**kwargs)
    if not date: # special case of update_lines always has a date.
        return input_dates(fields,**kwargs)
    if expand_sides and not box:
        print "fields:",fields
        fields = fix_side_prefixes(fields)
    fields = map(lambda x,c=write_as or client,ic=S2.common_methods.insert_client:ic(x,c),fields)

    key = "(date,team,o:team)"
    if sport == 'mlb': key = "(date,team,double header,o:team)"  # files are saved as date_team_gameNumber and parameter dh=0 for single games
    try: # this will fail if the fields do not yet exist
        res = sdb.query("%s,%s@%s<=date and (date-%s)<=%s and not _i%%2"%(key,','.join(fields),date,dates,date))
    except: # get empty fields for date range
        empty_fields = map(lambda x:"'' as '%s'"%x,fields)
        res = sdb.query("%s,%s@%s<=date and (date-%s)<=%s and not _i%%2"%(key,','.join(empty_fields),date,dates,date))
    if not res:
        return "Nothing to update for your date range."
    html = "<form method=post><input type='hidden' name='rewrite' value='%s'>"%rewrite
    html += "<input type='submit' name='submit' value='Update!'>"
    #print "sdb.ohead replad forads",sdb.ownerless_headers
    #print "kwargs",kwargs
    #reload(S2.formats)
    input_form = S2.formats.Input_Table(sdb.ownerless_headers,**kwargs)
    html += input_form.output(res[0])
    if box: html += "<input type='hidden' name='_post_box_' value=1>" # intercept at the sport level
    html += "<input type='submit' name='submit' value='Update!'>"
    html += "</form>"
    return html


FIELD_PAT = re.compile("([0-9]{8,8}_[^|]+)\|(.*)") # matches S2.formats.Input_Table
def post_fields(**kwargs):
    #print "S2.update.post ges kwarfds:%s"%(kwargs,)
    # expect a bunch of special tard kwargs _d_20120518_t_Bears_n_VARIABLE NAME_v_VALUE_
    # need to confirm that the web client is the same as given in the update keys
    client = kwargs.get("client")
    sport = kwargs.get("sport")
    rewrite = kwargs.get("rewrite",1)
    rebuild_box = kwargs.get("rebuild_box",0) # if user changes game data then we need to rebuild the Box _Columns
    write_as = kwargs.get("write as")    # super users can write to SDB
    f_lower = kwargs.get('f_lower',1)    # force the filename to be lower case.
    if not client: return "This method requires client."
    if not sport: return "This method requires sport."
    #print "update.sports",sport
    upd = {} # upd[(date,team)] = {name:value} fmor writing to a pickled file
    player_dts = {}
    for key in kwargs.keys():
        #print "key:",key,"val:",kwargs[key],type(kwargs[key])
        #if not kwargs[key]: continue
        mo = FIELD_PAT.findall(key)
        if mo:                 #[('20160903_WYO', 't:SDB./Punting:0.punt yards')]
            #return key        #name='20160903_WYO|t:SDB.rushing yards' 20160903_WYO|o:SDB./Passing:1.passes
            #print 'field.mox:',mo
            k,f = mo[0]
            fclient, fname = f.rsplit(".",1)
            #fclient, fname = f.split(".",1)
            #print "k,f,fc,fn:",k,f,fclient, fname
            #if f_lower: fname = fname.lower() # field names are lowercase.
            if "_file_box" in fname: # not a parameter but a file
                #eturn "%s"%kwargs
                # moved under individual sprts.
                if not client in S2.directory.SUPER_USERS: return "%s is not an allowed parameter name"%fname
                if not PARSERS.get(sport.lower()): return "Nothing for %s files."%sport
                #print "kwargs[key] for _file_:",kwargs[key]
                #return "ready to parse:<p>%s"%(kwargs[key],)
                #print "time to parse:",kwargs
                #open("/tmp/update.txt",'w').write(kwargs[key])
                flavor, upd[k] = PARSERS[sport.lower()](kwargs[key])
                try: flavor, upd[k] = PARSERS[sport.lower()](kwargs[key])
                except:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    return  repr(traceback.format_exception(exc_type, exc_value,
                                          exc_traceback)).replace('\\n','<p>')


                #print 'upd',type(upd[k])
                break

            if ':' in fclient:
                pre, fclient = fclient.split(':',1)
                fclient = fclient.split("./")[0]
                fname = pre + ':' + fname
            if (write_as or client) != fclient:
                return "Error: mismatch in client field: %s != %s<p>from (%s)"%(client,fclient,mo)
            if " /" in fname:
                pt, rest = fname.split(':',1)
                i,field = rest.split(".",1)
                player_dts.setdefault(pt,{}).setdefault(i,{})[field] = kwargs[key]
            elif str(kwargs[key]).lower() == 'none':
                upd.setdefault(k,{})[fname] = None
            elif fname == 'line' and sport in ['nfl','nba','ncaafb','ncaabb','cfl','wnba']:
                upd.setdefault(k,{})['home line'] = kwargs[key]
                upd.setdefault(k,{})['away line'] = -1*kwargs[key]
            elif ('quarter scores' in fname or 'period scores' in fname or 'half scores' in fname or 'inning runs' in fname) and type(kwargs[key]) is str:
                    upd.setdefault(k,{})[fname] = eval(kwargs[key])
            else:
                upd.setdefault(k,{})[fname] = kwargs[key]


            for pt in player_dts.keys():
                upd.setdefault(k,{})[pt] = map(lambda x:x[1],sorted(player_dts[pt].items()))

    #print "upd:%s"%(upd,)
    pdir = os.path.join(CLIENT_DIR,write_as or client,sport.upper(),'Data','_Pickle')
    if not os.path.isdir(pdir): os.makedirs(pdir)
    dates = set()
    for k in upd.keys():
        dates.add(k.split('_')[0])
        #upd[k] = PyQL.py_tools.guess_types(upd[k])
        f = os.path.join(pdir,k+'.pkl')
        if not rewrite and os.path.isfile(f): # update any existing dict
            d = cPickle.load(open(f))
        else: d = {}                          # fresh dict
        #print "k,upd[k]:",k,upd[k]
        d.update(upd[k])
        #print "update dumping to:",f
        cPickle.dump(d,open(f,'w'))
    # append the list of pending updates.
    lout = []
    for date in dates:
        lout.append("%s=%s"%(write_as or client,date))
    if rebuild_box:
        lout.append("%s.Box=1"%(write_as or client,))
    text_out = '\n'.join(lout)+'\n'
    open(os.path.join(LOG_DIR,"%s_client_data.pending"%sport.lower()),'a').write(text_out)
    if 'SDB' in [client,write_as]:
        ldir = os.path.join(CLIENT_DIR,client,sport.upper(),'Data','_Log')
        if not os.path.isdir(ldir): os.makedirs(ldir)
        dtime = datetime.datetime.today().strftime('%Y%m%d.%s')
        open(os.path.join(ldir,'%s_%s'%(dtime,fname)),'w').write(text_out)



    len_upd = len(upd)
    return "Updates initiated for %d game"%len_upd + 's'*(len_upd!=1)



def join_get(**kwargs):
    join = kwargs.get('join')
    flavor = kwargs.get('flavor')
    if not join: return "this method expects the join and flavor to be specified"
    if join == "active_starters":
        html = "<form method=post>"
        html += "<input type='submit' name='submit' value='Update!'><BR>"
        team_starters = active_starters()
        teams = team_starters.keys()
        teams.sort()
        for team in teams:
            starters = team_starters[team]
            starters.sort()
            html += "<b>%s</b><BR><textarea rows='12' cols='40' name='%s'>%s</textarea><p>"%(team,team,'\n'.join(starters))
        html += "<BR><input type='submit' name='submit' value='Update!'>"
        #html += "<BR><input type='hidden' name='join' value='%s'>"%join
        html += "</form>"
        return html

    if join == "pitcher_throws":
        d = pitcher_throws()
        pitchers = d.keys()
        pitchers.sort()
        vals = []
        for p in pitchers:
            vals.append("%s:%s"%(p,d[p]))
        html = "<form method=post>"
        html += "<input type='submit' name='submit' value='Update!'><BR>"
        html += "<textarea rows='40' cols='60' name='pitcher_throws_data'>%s</textarea>"%('\n'.join(vals),)
        html += "<BR><input type='submit' name='submit' value='Update!'>"
        #html += "<BR><input type='hidden' name='join' value='%s'>"%join
        html += "</form>"
        return html

def join_post(**kwargs):
    join = kwargs.get('join')
    sport = kwargs.get('sport')
    if not join: return "this method expects the join to be specified"
    if not sport: return "this method expects the sport to be specified"
    if join == "active_starters":
        d = {}
        for team in active_starters().keys():
            d[team] = map(lambda x:x.strip(),kwargs[team].split('\n'))
        #f = open("/tmp/active_starters.pkl",'w')
        f = open(os.path.join(DATA_DIR,"Join","_Raw","active_starters.pkl"),'w')
        cPickle.dump(d,f)
        return "active starters have been updated"
    elif join == "pitcher_throws":
        d = {}
        for line in kwargs['pitcher_throws_data'].split('\n'):
            p,t = line.split(':')
            d[p.strip()] = t.strip()
        f = open(os.path.join(DATA_DIR,"Join","_Raw","pitcher_throws.pkl"),'w')
        cPickle.dump(d,f)
        RESTART(sport="mlb",flavor="query")
        return "pitcher_throws has been updated and changes will take effect in about 5 minutes"
    else: # generic joined in file. dump it and hope prepare.py or manage.py or something knows about it.
        return "don't know what to do with: %s"%join





############# tests and demos ##############
def parse_cherry():
    kwargs = {}
    kwargs["client"] = "Cherry"
    kwargs["sport"] = "NHL"
    kwargs['_csv_NHL_Cherry'] = open('/tmp/PuckLineList.csv').read()
    post_csv_fields(**kwargs)


if __name__ == "__main__":
    #parse_cherry();raise
    #sdql = "points,o:points @ team='Bears'  and  season=2004"
    sdql = "team=Bears and season>=2010"
    for arg in sys.argv[1:]:
        if '=' not in arg:
            arg = arg+"=1"
        var, val = string.split(arg,'=',1)
        try:              #first ask: Is this in my name space?
            eval(var)
        except:
            print "Can't set", var
            sys.exit(-1)
        try:
            exec(arg)  #numbers
        except:
            exec('%s="%s"' % tuple(string.split(arg,'=',1))) #strings
    #open("/tmp/nba_query.html",'w').write(query(text=text,output="summary") )
    kwargs = {'client':'hess','fields':'line,total','date':'20120909'}
    print form_fields('foo',**kwargs)
    kwargs = {'client':'hess','sport':'nfl','20120910_Raiders|hess.line':'100','20120910_Raiders|hess.total':'48'}
    #print post_fields(**kwargs)

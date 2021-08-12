import PyQL.outputs,PyQL.dt
import urllib,cgi,re,os
import cPickle
from S2.common_methods import key_to_query_link
import S2.trends
import S2.directory

STR_NONE = " "
safe_d_d_format = "lambda x:(None in x and '%s') or '%%d-%%d'%%x"%STR_NONE

TEAM_PAT = re.compile("([^:]team|t:team)[\s]*[=]{1,2}[\s]*([A-Z][a-z]+(?:[\s]*[A-Z][a-z]+)?)") # no capitol words can follow a team name!


def fprint(txt):
    open('/tmp/dump.out','a').write(txt + '\n%s\n'%'-'*20)

def percent_format(total,win,plus_sign=1,str_none="---"):
    if total is None or win is None: return str_none
    val = win*100./(total or 1)
    return "+"*(plus_sign and 0<val) + "%0.1f"%val + "%"

def dollar_format(val,plus_sign=1):
    if val is None: return STR_NONE
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


class Query:
    clients = {} # for subclass customizations
    key_to_query_link = key_to_query_link
    def __init__(self,headers,**kwargs):
        self.kwargs = kwargs
        self.headers = map(lambda x:x.split('.')[-1],headers)
        #print self.headers

        self.score = None
        for score in ["goals","runs","points"]:
            if score in self.headers:
                self.score = score
                break
        if not self.score:
                raise Exception("Query excpects a header of 'goals', 'runs', or 'points'")

    def output_html(self,res):
        return PyQL.outputs.html(res)

    output = output_html

class Flot_Scatter(Query):
    # just a quick sketch here:
    # todo: small multiples on same graph or separate, icons, icon size, pass in the usual parameters.
    def output(self,res,**kwargs):
        # expect sdql of form (x,y)@cond
        width = kwargs.get("width",800)
        height = kwargs.get("height",600)
        out = "<script type='text/javascript'>function draw_ts(canvas,data){$.plot($('#'+canvas),[{data:data,color:'#888888',yaxis: {autoscale:true},xaxis: {autoscale:true}, points:{show:true,radius:2,fill:true,fillcolor:'#000000'}}])}"
        str_data = str(res[0].data).replace('(','[').replace(')',']') # tuple to list
        #print "str_data:",str_data
        out += "$(document).ready(function(){draw_ts(canvas='canvas',data=%s);});</script>"%str_data
        out += "<div id='canvas' style='width:%spx;height:%spx;background-color:#FFFFFF';></div>"%(
                          width,height)
        return out

class Input_Table(Query):
    #20130330 klugded in drop down menus for MLB starters.
    def output(self,res):
        # first field is the key (date, team) or (date,team,dh): the others are presented in text input boxes.
        ret = ["<table border=1><th>Game</th>"]
        size = self.kwargs.get('size',5)
        n_fields = len(res)
        for f in range(1,n_fields):
            ret.append("<th>%s</th>"%(res.headers[f],))
        if 'starter' in ''.join(ret): #cheap flag that we need active_starters
            from MLB.joins import active_starters
            team_starters = active_starters()
        for i in range(len(res[0])):
            game = "_".join(map(str,res[0][i])) # date_team[_dh]_o:team
            game = game.replace("'",'')
            key = "_".join(map(str,res[0][i][:-1])) # date_team[_dh] ; peal off o:team
            key = key.replace("'",'')
            ret.append("<tr><th align='right'>%s</th>"%(game.replace('_',' '),))

            for f in range(1,n_fields):
                val = res[f].data[i]
                if val is None: val=''
                if '_file_' in res.headers[f]:
                    ret.append("<td><input type='file' name='%s|%s'></td>"%(key,res.headers[f]))
                elif 'starter' in res.headers[f]:
                    select = "<td><select name='%s|%s'>"%(key,res.headers[f])
                    options = team_starters[res[0][i][1*(res.headers[f][0]=='t') or -1]] # team is at 1; o:team is at -1
                    options.sort()
                    if not val: selected = " SELECTED"
                    else: selected = ''
                    select += "<option value='None'%s>---\n"%selected
                    for option in options:
                        if val == option: selected = " SELECTED"
                        else: selected = ''
                        select += "<option value='%s'%s>%s\n"%(option,selected,option)
                    select += "</select></td>"
                    ret.append(select)
                else:
                    ret.append("<td><input type='text' name='%s|%s' value='%s' size=%s></td>"%(key,res.headers[f],val,size))
            ret.append("</tr>")
        ret += ["</table>"]
        return "\n".join(ret)


class Dump_Trends(Query):
    #pat_ats_record
    def output(self,res):
        #reload(S2.directory); reload(S2.trends)
        #print "RELOADed S2.directory, trends - TURN OFF FOR DEPLOYMNET"
        #print "Dtrends gets",self.kwargs,res
        if not self.kwargs.has_key('fout'):
            raise Exception, "dump_trends needs a **kwargs key at 'fout'"
        if not res or not len(res):
            print "formats.Dump_Trends gets NoResults"
            return 'No results'
        client = self.kwargs.get('client','SDB')
        sport = self.kwargs.get('sport','default')
        column_flavor = self.kwargs['column_flavor']
        bet = self.kwargs.get('bet')
        side = self.kwargs.get('side')
        check_record = self.kwargs.get("check_record")
        show_record = self.kwargs.get("show_record")
        update_record = self.kwargs.get("update_record")
        translator = self.kwargs.get('translator','default')
        #print "translator:",translator
        #open("/tmp/nba.out",'a').write("Dump.translatir:%s"%translator)
        flip_record = int(self.kwargs.get("flip_record",0))
        #print "fr:",flip_record
        record_offset = res[0].offset_from_header("record")
        assert record_offset is not None
        fdt_offset = res[0].offset_from_header("future_dateteam")
        assert fdt_offset is not None
        # pick up args with defaults.
        self.english_as_sdql = self.kwargs.get("english_as_sdql",0) # A => A rather than A => site=='away'
        find_best_date = int(self.kwargs.get("find_best_date", 0)) # need also on transform key
        #print "formt.find best date",find_best_date
        min_profit = float(self.kwargs.get("min_profit",0))
        min_roi = float(self.kwargs.get("min_roi",0))
        pval = self.kwargs.get('pval',1)
        perfect = self.kwargs.get('pperfect',0) # post perfect for SDQG: 'perfect' is passed to Column and handled there
        #print "dump trends.perfect",perfect
        min_games = int(self.kwargs.get('min_games',0))
        min_percent = float(self.kwargs.get('min_percent',0))
        #print "DumpTrends.perfet",perfect
        #print min_profit,type(min_profit); raise
        max_groups = self.kwargs.get("max_groups")
        # define column
        cd = {}
        # "record" is W,L,P,marg, profit,start_date
        cd["team"] = [];    cd["sdql"] = [] ;   cd["english"] = [];    cd["active"] = []
        if column_flavor in ["Best_Profit","Best_ROI"]:
            record_fields = ["wins","losses","pushes","margin","profit","invested","start"]
        elif column_flavor == "Best_Record":
            record_fields = ["wins","losses","pushes","margin","pval","start"]
        else:
            raise Exception, "Unknown column_flavor: %s"%column_flavor
        #print "formats sets record fields to",record_fields
        i = -1
        for rf in record_fields:
            i += 1
            cd[rf] = []
        if max_groups: res = res[:max_groups]
        #print "max_groups,lenres;",max_groups,len(res)
        for item in res: # this many group bys
            #print( "formats.item:%s"%item[0])
            if not find_best_date:
                record = item[record_offset].value_all()
            else:
                record = item[record_offset].value() # search for the best profit
            #print "rec:",record
            if flip_record and record:
                record = (record[1],record[0],record[2],-record[3]) + record[4:]

            #print "possibly flipped rec:",record
            # KS likes 6-0 (except for teasers)
            #print "formats.record:",record
            if record[-1] is None:
                #fprint("%s: didn't made the start date cut"%(record,))
                continue

            #if client in ['SDQG'] and ( 1<record[1]<record[2] or 1<record[2]<record[1]):
                #print record,"didn't made the special SDQG cut"
            #    continue
            ngames = 1.*record[0]+record[1]
            if min_games and min_games > ngames:
                print "didn't make the min games cut",min_games,ngames
                continue
            if min_percent and min_percent/100.>max(record[0]/ngames,record[1]/ngames):
                print "didn't make the min percent cut",ngames,record[0],record[1]
                continue
            if perfect and record[0]*record[1]:
                print "didn't make the post perfect cut"
                continue
            if column_flavor == "Best_Profit" and (min_profit and record[4] < min_profit) or ( min_roi and 1.*record[4]/(record[5] or 1) < min_roi):
                #print record,"didn't made the min_profit cut"
                continue
            if column_flavor == "Best_ROI" and (min_profit and record[4] < min_profit) or ( min_roi and 1.*record[4]/(record[5] or 1)< min_roi):
                #print record,"didn't made the roi cut"
                continue
            if pval<1 and ((column_flavor == "Best_Record" and pval and record[-2] > pval) or (record[0]+record[1]==0)) and not (client=='KS' and bet.isalpha() and record[0]*record[1]==0 and (record[0]+record[1])>5):
                #print record,"didn't made the pval cut"
                continue
            #print "made the pval cut"
            active = filter(lambda x:len(x),item[fdt_offset].value())
            #print "name:",item.name
            #print "len ctrans:",len(S2.directory.CLIENT_TRANSLATORS.get(client,{}).get(sport.upper(),{}).get(translator,[]) )
            if not self.kwargs.get('update'):
                #pat_sub_pairs = S2.directory.CLIENT_TRANSLATORS.get(client,{}).get(sport.upper(),{}).get(translator,[]) + S2.trends.PAT_SUB_PAIRS
                pat_sub_pairs =  S2.trends.PAT_SUB_PAIRS + S2.directory.CLIENT_TRANSLATORS.get(client,{}).get(sport.upper(),{}).get(translator,[])
            else:  pat_sub_pairs = S2.trends.PAT_SUB_PAIRS
            if bet and bet.lower() in ['ml','su']: show_bet = 'su' # 'Straight up win' is just 'Win '
            else: show_bet = bet
            #print "ready to transform_key with len(psp)",len(pat_sub_pairs)
            query_key , english_key = self.transform_key(item.name,record=record,
                                                         pat_sub_pairs=pat_sub_pairs,
                                                         show_record=show_record,
                                                         update_record=update_record,
                                                         show_date=find_best_date,
                                                         bet=show_bet,side=side,sport=sport)
            #print  "query_key , english_key:", query_key , english_key
            #print;   print;
            if client in ['KS','SDB']:
                query_key = S2.trends.clean_as_sdql(query_key)
            #print  "cealn as.query_key:", query_key
            mo = TEAM_PAT.findall(' ' + query_key)
            #print "query_key , english_key, no",query_key , english_key, mo
            if len(mo): team = mo[0][-1]
            else: team = None
            #print "name:",item.name
            #print "qk,ek",query_key,english_key
            if check_record:
                mo = re.findall("([0-9]+)[\s]*-[\s]*([0-9]+)",english_key)
                #print "rec from eng:",mo
                if mo and (int(mo[0][0]) != int(record[0])) or (int(mo[0][1]) != int(record[1])):
                    #print "mismatch:",english_key, record
                    english_key = "ERROR: " + english_key
                else:
                    english_key = "OK: " + english_key
            else:
                pass
                #print "formats hs no check_record"
            cd["sdql"].append(query_key)
            cd["english"].append(english_key)
            cd["team"].append(team)
            cd["active"].append(active)
            for i in range(len(record)):
                #print("rec[i]%s"%(record[i],))
                cd[record_fields[i]].append(record[i])

        if self.kwargs.get('winnow'):
            #print "winnowing trends with group-by  ['wins','losses','team'] query for the shortest SDQL text"
            data = []
            for k in cd.keys(): data.append(PyQL.columns.Column(name=k,data=cd[k]))
            tdt = PyQL.dt.DT(data=data)
            #print "%d original trends"%len(tdt[0])
            pyql = 'Minimum((len(sdql),'+','.join(tdt.headers) + '))@'
            for rf in ['wins','losses','team']:
                pyql += "%s and "%rf
            pyql = pyql[:-5]
            #print "winnowing with",pyql
            res = tdt.query(pyql)
            res = res.reduced()
            #print "winnowed to %d trends"%len(res[0])
            for h,header in enumerate(tdt.headers):
                cd[header] = map(lambda x:x[1+h],res[0].data)

        if self.kwargs.get('context','') == 'pkl':
            return cPickle.dumps(cd)

        fname = os.path.join(S2.directory.CLIENT_DIR,(self.kwargs['fout']))
        #print "write to",fname
        if not len(cd["wins"]):
            return "no trends"
        f = open(fname, 'w' )
        cPickle.dump(cd,f)
        f.close()

        return "saved %s"%fname


    def transform_key(self,key,record=None,pat_sub_pairs=None,show_record=0,update_record=0,show_date=0,bet=None,side=None,sport='default'):
        sdql,english = S2.trends.split_key(key)
        #print "formats.tkey sdql,eng",sdql,english
        if "=>" in english:
            #print "fpormat.transxofmr_ket.englogn:",english
            return english.split("=>",1)
        #return sdql,english
        if self.english_as_sdql:
            sdql = english # need to preserve short cuts used in trend generation.
            print "eng as sdql:",sdql
        #open("/tmp/nba.out",'a').write("record:%s\n"%record)
        if record:
            if show_record:
                #english += " have a %s %s record of %s"%(bet or '',side or '',record[:-1],)
                english += " have a %s record of %s"%(bet or '',record[:-1],)
            if update_record:
                english += " UPDATE have a %s %s record of %s and date>=%s"%(bet or '',side or '',record[:-1],record[-1])
                #open("/tmp/nba.out",'a').write("ebg:%s\n"%english)
            if record[-1] and show_date:
                #print "adding to sdql:" + " and date>=%s"%record[-1]
                sdql  += " and date>=%s"%record[-1]
                #english  += " since %s"%record[-1]
                english  += " and date >= %s"%record[-1] # build nice english with pat_sub_pairs
        if pat_sub_pairs: # cleint specific translations.
            #print "english pre sub:",english
            english = S2.trends.translate(english,pat_sub_pairs)
            #print "english post sub:",english
            #print "sdql pre sub:",sdql
            sdql = S2.trends.translate(sdql)
            #print "sdql post sub:",sdql
        if sport.startswith('ncaa') and english.startswith('The '):
            parts = english.split()
            if parts[2] == 'are':
                parts[2] = 'is'
                english = ' '.join(parts[1:])
        #print "formats.tranlate returning sdql",sdql
        english  = english.strip()
        if len(english) and english[-1] != '.':
            english += '.'
        return sdql,english


def records_output(res,**kwargs):
    ktql = kwargs.get('key_to_query_link',key_to_query_link)
    html = PyQL.outputs.add_reduced_as_key(res)
    res = PyQL.outputs.auto_reduce(res, ktql)
    if html:
        #print 'html:',html
        if not html.endswith(' and'): html += " and"
        html += " ... "
    html += PyQL.outputs.html(res)
    # kludged in to keep KS1.0 clients logged in.  Remove with KS2 and cookies.
    if kwargs.has_key('sid'):
        #print "subbingh on sid"
        html = html.replace('query?','query?sid=%s&'%kwargs['sid'])
    return html


class Query_Records(Query):
    def __init__(self,headers,**kwargs):
        Query.__init__(self,headers,**kwargs)
        self.ngames = kwargs.get("ngames",1)
        self.su = kwargs.get("su",1)
        self.ats = kwargs.get("ats",1)
        self.ou = kwargs.get("ou",1)
        self.n_rows = kwargs.get("n_rows",100)
        self.average_line = kwargs.get("average_line",1)
        self.average_total = kwargs.get("average_total",1)

    def select(self):
        select = ''
        if self.ngames:
            select = "Count(%s) as __N__,"%self.score
        if self.su:
            select += "Record_WLPM(%s-o:%s,format='''lambda x:'%%s-%%s (%%0.2f, %%0.1f&#37;)'%%(x[0],x[1],x[3],100.*x[0]/((x[0]+x[1]) or 1))''') as '__su__',"%(self.score,self.score)
        if self.ats:
            select += "Record_WLPM(%s+line-o:%s,format='''lambda x:'%%s-%%s-%%s (%%0.2f, %%0.1f&#37;)'%%(x[0],x[1],x[2],x[3],100.*x[0]/((x[0]+x[1]) or 1))''') as '__ats__',"%(self.score,self.score)
            if self.average_line: select += "Average(t:line,format='%0.1f') as __t_average_line__,"
        if self.ou:
            select += "Record_WLPM(%s+o:%s-total,format='''lambda x:'%%s-%%s-%%s (%%0.2f, %%0.1f&#37;)'%%(x[0],x[1],x[2],x[3],100.*x[0]/((x[0]+x[1]) or 1))''') as '__ou__',"%(self.score,self.score)
            if self.average_total: select += "Average(t:total,format='%0.1f') as __t_average_total__,"
        if select[-1] == ',': select = select[:-1]
        return select


    def output(self,res):
        res = PyQL.outputs.auto_reduce(res, self.key_to_query_link)
        ret = []
        ret.append("<TABLE border=0 bgcolor=FFFFFF><tr>")
        if self.ngames:
            Nr = res.value_from_header("__N__")
            ret.append("<th valign=bottom># games</th>")
        if self.su:
            sur = res.value_from_header("__su__")
            ret.append("<th valign=bottom>SU</th>")
        if self.ats:
            atsr = res.value_from_header("__ats__")
            ret.append("<th valign=bottom>ATS</th>")
        if self.ou:
            our = res.value_from_header("__ou__")
            ret.append("<th valign=bottom>O/U</th>")
        ret.append("<th valign=bottom>%s</th>"%res.headers[-1])
        ret.append("</tr>")
        for r in range(min(len(res[0]),self.n_rows)):
            ret.append("<tr>")
            if self.ngames:
                ret.append("<td align=center>%s</td>"%Nr[r])
            if self.su:
                sur_r = sur[r]
                ret.append("<td align=center>%s-%s (%0.1f, %0.1f)</td>"%(sur_r[0],sur_r[1],sur_r[3],sur_r[4]))
            if self.ats:
                atsr_r = atsr[r]
                ret.append("<td align=center>%s-%s (%0.1f, %0.1f)</td>"%(atsr_r[0],atsr_r[1],atsr_r[3],atsr_r[4]))
            if self.ou:
                ret.append("<td align=center>%s-%s-%s (%0.1f, %0.1f)</td>"%our[r])

            ret.append("<td align=center>%s</td>"%res[-1][r])

            ret.append("</tr>")
        ret.append("</table>")
        return "\n".join(ret)


# idea of generic methods below is not cooked = half baked.
class Query_Summary(Query_Records):

    records_select = Query_Records.select
    def __init__(self,headers,**kwargs):
        Query_Records.__init__(self,headers,**kwargs)
        self.show_unplayed = int(kwargs.get("show_unplayed",10))
        self.show_games = int(kwargs.get("show_games",20))

    # name headers here in select for output headers
    def select(self):
        ret = self.records_select() + ","
        # game select keep their query assigned headers, do not start with `__`, and need to be last in the select clause
        if 'date' in self.headers:
            ret += "self.nice_date(date,abbreviate_month=1,abbreviate_year=0) as 'Date',"
            ret += "self.day_from_date(date)[:3] as 'Day',"
        if 'game number' in self.headers:
            ret += "game number as '#',"
        if 'season' in self.headers:
            ret += "season as 'Season',"
        if 'team' in self.headers:
            ret += "Column(team,format='%s') as 'Team',"
            ret += "Column(o:team,format='%s') as 'Opp',"
        if 'site' in self.headers:
            ret += "Column({'home':'H','away':'A','neutral':'N'}.get(site,site)) as 'Site',"
        ret += "Column((%s,o:%s),format='''%s''') as 'Score',"%(self.score,self.score,safe_d_d_format)  # `Score` is used below for unplayed games
        if 'date' in self.headers:
            ret += "Column(date-p:date+1,format=lambda r:'%s'*(r is None or 100<r) or str(r)) as 'Rest',"%STR_NONE
        if 'line' in self.headers: ret += "line as 'Line',"
        if 'total' in self.headers: ret += "total as 'Total',"
        ret += "%s-o:%s as 'SUm',"%(self.score,self.score)
        if 'line' in self.headers: ret += "%s+line-o:%s as 'ATSm',"%(self.score,self.score)
        if 'total' in self.headers:
            ret += "Column({0:'W',1:'L',2:'P'}[(0+%s<o:%s)+2*(0+%s==o:%s)],format='%%s') as 'SUr',"%(self.score,self.score,self.score,self.score)
        if 'line' in self.headers:
            ret += "Column({0:'W',1:'L',2:'P'}[(%s+line<o:%s)+2*(%s+line==o:%s)],format='%%s') as 'ATSr',"%(self.score,self.score,self.score,self.score)
        if 'total' in self.headers:
            ret += "Column({0:'O',1:'U',2:'P'}[(%s+o:%s<total)+2*(%s+o:%s==total)], format='%%s') as 'OUr',"%(self.score,self.score,self.score,self.score)
        if 'conference' in self.headers: ret += "Column('%d'%(conference==o:conference)) as Conf,"
        if "game type" in self.headers: ret += "Column(game type,format='%s') as 'Type',"
        if "overtime" in self.headers: ret += "overtime as OT,"
        if ret[-1] == ",": ret = ret[:-1]

        return ret

    def output_records(self,res):
        # record fields start with __
        ret = []
        ret.append("<table>")

        if self.su:
            ret.append("<tr><th>SU:</th>")
            ret.append("<td>%s</td>"%(res.value_from_header("__su__"),))
            ret.append("</tr>")

        if self.ats:
            ret.append("<tr><th>ATS:</th>")
            ret.append("<td>%s</td>"%(res.value_from_header("__ats__"),))
            if self.average_line:
                ret.append("<td>&nbsp;&nbsp;avg line: %s </td>"%(
                    res.value_from_header("__t_average_line__",''))    )
            ret.append("</tr>")

        if self.ou:
            ret.append("<tr><th>OU:</th>")
            ret.append("<td>%s</td>"%(res.value_from_header("__ou__"),))
            if self.average_total:
                ret.append("<td>&nbsp;&nbsp;avg total: %s</td>"%(
                     res.value_from_header("__t_average_total__",''))    )
            ret.append("</tr>")

        ret.append("</table>")

        return '\n'.join(ret)


    def output_games(self,res):
        # need to find the range of rows to display
        score_offset = res.offset_from_header("Score")
        if score_offset is None: return "<!--No `Score` header-->"

        for start_games in range(len(res.headers)):
            if res.headers[start_games][:2] == '__': continue
            break
        len_res = len(res[start_games].data)
        #len_played = len(filter(lambda x:x[0] is not None,res[score_offset].data)) XXX picks up missing past games
        scores = res[score_offset].data
        i = 0
        for i in range(len_res-1,0,-1):
            if scores[i][0] is not None: break
        len_played = i + 1
        stop = min(len_res, len_played + self.show_unplayed)
        start = max(0,stop-self.show_games)
        ret = []
        ret.append("<table id='DT_Table'><thead><tr>")
        date_offset = res.offset_from_header("Date")
        game_headers = res.headers[date_offset:]
        for header in game_headers:
            ret.append("<th>%s</th>"%header)
        ret.append("</tr></thead>")
        len_game_headers = len(game_headers)
        len_res = len(res[date_offset])
        #for g in range(len(res[date_offset])):
        for g in range(start,stop):
            ret.append("<tr>")
            for h in range(len_game_headers):
                val = res[date_offset+h][g]
                #print "val:",val,"%s"%(val,)
                if val is None or val == (None,None): str_val = STR_NONE  # XXX need eigen handling of None
                else: str_val = res[date_offset+h].format(val)
                if date_offset+h == score_offset: str_val = "<b>%s</b>"%str_val
                ret.append("<td align=center>%s</td>"%str_val)
            ret.append("</tr>")
        ret.append("</tr>")
        ret.append("</table>")
        return "\n".join(ret)

    def output(self,res,**kwargs):
        query_title = kwargs.get("query_title","")
        ret = []
        ret.append("<!--Start Summary-->")
        ret.append("<TABLE border=0 bgcolor=FFFFFF>")
        if query_title:
            ret.append("<!--Start Key Row--><TR bgcolor=DDDDDD><TH>%s</TH></TR><!--End Key Row-->"%cgi.escape(query_title))
        ret.append("<!--Start Records Row--><TR><TD>")
        #print "building summary records"
        ret.append(self.output_records(res))
        #print "built summary records"
        ret.append("</TD></TR><!--End Records Row-->")

        #ret.append("<!--Start Stats Row--><TR><TD>")
        #ret.append(summary_stats_table(res,**kwargs))
        #ret.append("</TD></TR><!--End Stats Row-->")
        #print "building game table"
        ret.append("<!--Start Games Row--><TR><TD>")
        ret.append(self.output_games(res))
        ret.append("</TD></TR><!--End Games Row-->")
        #print "built"
        ret.append("</TABLE>")
        return "\n".join(ret)


### tests and demos ####

def test_query(sdb):
    print sdb.sdb_query("(date,points,team,o:team)@season=2011")


def test_summary(sdb):
    Q = Query_Summary(headers=sdb.headers,ats=0)
    res = sdb.sdb_query(Q.select()+'@'+"team[0]=C and site")
    #print res
    #return
    html = ''
    for r in res:
            html += Q.output(r) #summary_html(r,query_name=' '.join(r.name[-1]),n_games=30,n_unplayed=20)
    open("/tmp/sdb.html",'w').write(html)
    #print html

def test_records(sdb):
    Q = Query_Records(headers=sdb.headers,ou=1)
    res = sdb.sdb_query(Q.select() + '@team[0]=A and site')
    print res
    html =  Q.output(res)
    open("/tmp/sdb.html",'w').write(html)
    #print html

def test_scatter(sdb):
    Q = Flot_Scatter(headers=sdb.headers)
    res = sdb.sdb_query("(points,o:points)@team=Bears and season=2011")[0]
    print res.data,type(res.data)
    str_data = str(res[0].data).replace('(','[').replace(')',']') # tuple to list
    print "ts.str_data:",str_data
    print Q.output(res)

def dump_trends(sdb):
    kwargs = {}
    kwargs["min_profit"] = 0
    kwargs["client"] = 'KS'
    kwargs["sport"] = 'MLB'
    kwargs["show_record"] = 1
    kwargs["bet"] = 'SU'
    kwargs["fout"] = '/tmp/format.pkl'
    kwargs["side"] = 'on'
    kwargs["flip_record"] = 0
    kwargs["column_flavor"] = "Best_Profit"

    Q = Dump_Trends(headers=sdb.headers,**kwargs)
    res = sdb.sdb_query(" Best_Profit((t:runs-o:runs,t:line,date,team),give_up=(10,0),perfect=None,roi=0) as record,U((date,team)*(date >= 20150527)) as future_dateteam@t:team,League and t:season=2015,1 and (site=home) as 'at home',(site=away) as 'on the road',1 and (line<-105) as 'as a favorite',(0<line) as 'as a dog',(line<=-140) as 'as a 140+ favorite',(140<=line) as 'as a 140+ dog',(170<=line) as 'as a 170+ dog',(line<=-200) as 'as a 200+ favorite',(-120<=line<=120) as 'when within 20 cents of pickem',1 and (6<=tp:runs and tp:season=season) as '[3] after scoring 6+ runs'")

    #print res
    html =  Q.output(res)
    #print html



if __name__ == "__main__":
    from MLB.loader import mlb as sdb
    #sdb.show_metacode = 1
    #test_query(mlb)
    #test_game_fields(sdb)
    #test_summary(sdb)
    #test_records(sdb)
    #test_scatter(sdb)
    dump_trends(sdb)

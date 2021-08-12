"""
Update the database from a client entered form with fields or from text data with headers
"""
from NFL.loader import nfl
import S2.update, S2.common_methods
import PyQL.html_tools

def form_fields(**kwargs):
    return S2.update.form_fields(nfl,**kwargs)

def post_fields(**kwargs):
    return S2.update.post_fields(**kwargs)    


def abbreviate(n):
    if 'touchdowns' in n: return 'tds'
    if 'yards' in n: return 'yds'
    if 'interceptions' in n: return 'ints'
    if 'returns' in n: return 'returns'
    if 'longest' in n: return 'longest'
    return n


def form_game(**kwargs):
    # form for game stats
    client =  kwargs.get("client")
    write_as = kwargs.get("write as")
    date = kwargs.get("date")
    team = kwargs.get("team")
    if not client or not date or not team:
        return "This method requires date and team" # and all I have is %s"%kwargs
    # get default fields for this client
    # stats are handled 'naturally' by S2.update.post_fields EXCEPT the special quarter scores 
    stats = ["points","quarter scores", # these first 2 are handled separately. see below: for stat in stats[2:]  
             "first downs","passing first downs","rushing first downs","penalty first downs",
             "third downs attempted", "third downs made","fourth downs attempted", "fourth downs made",
             "plays","drives",
             "passes","completions","passing yards","interceptions","sacks","sack yards",
             "rushes","rushing yards",
             "red zones attempted", "red zones made",
             "penalties", "penalty yards",
             "fumbles", "fumbles lost",
             "touchdowns","rushing touchdowns","passing touchdowns",
             "time of possession",
             "punts","average punt yards",
             "field goals attempted","field goals",
             "goal to go attempted","goal to go made",
             "return yards",
             "surface"
             ]
    fields = ["o:team","line","total"]+map(lambda x:'t:'+x,stats) + map(lambda x:'o:'+x,stats) 
    sdql = "%s @ %s=date and team=%s and _i%%2=0"%(','.join(fields),date,team)
    #print "sdql:",sdql
    res = nfl.query(sdql)
    if not res or not res[0]:
        return "Nothing to update for %s on %s."%(team,date)
    res = res[0]


    o_team = ('%s'%(res.value_from_header('o:team'),)).strip()   
    owner = write_as or client
    key = "%s_%s|"%(date,team)
    html = "<form method=post>\n"
    html += "Line %s"%PyQL.html_tools.input(name='%s%s.line'%(key,owner),value=('%s'%res.value_from_header('line','')).strip(),size=4)
    html += "Total %s"%PyQL.html_tools.input(name='%s%s.total'%(key,owner),value=('%s'%res.value_from_header('total','')).strip(),size=4)
    html += "<P>"
    html += "Paste your box score data or enter values below.<BR>"
    #html += "url: %s<BR>"%PyQL.html_tools.input(name='%s%s.url'%(key,owner),size=12)
    html += "%s<p><p>"%PyQL.html_tools.textarea(name='%s%s._file_box'%(key,owner),rows=3,cols=60)
    
    # stats
    
    html += "<table><tr><th></th><th bgcolor='#CCCCCC'>%s</th><th bgcolor='#CCCCCC'>%s</th></tr>"%(o_team,team)
    #html += "<tr><th colspan=3 align=left bgcolor='#EEEEEE'>Game Stats</th></tr>"
    for stat in stats:
        ov = res.value_from_header('o:'+stat)[0]
        if ov is None: ov = ''
        tv = res.value_from_header('t:'+stat)[0]
        if tv is None: tv = ''
        
        html += "<tr><th align=right>%s</th><th>%s</th><th>%s</th></tr>"%(stat,
                   PyQL.html_tools.input(name="%so:%s.%s"%(key,owner,stat),value=ov,size=8),
                   PyQL.html_tools.input(name="%st:%s.%s"%(key,owner,stat),value=tv,size=8) )
    html += "</table>\n"
    player_fields = {}
    player_fields['passing'] = "name, passes, completions, interceptions thrown, passing touchdowns, passing conversions, passing yards".split(",")
    player_fields['rushing'] = "name, rushes, rushing yards, rushing touchdowns, rushing conversions, longest rush".split(",")
    player_fields['receiving'] = "name, receptions, receiving yards, receiving touchdowns, passing conversions, longest reception".split(",")
    player_fields['punting'] = "name, punts, average punt yards, longest punt, punts inside the twenty".split(",")
    player_fields['kickoff returns'] = "name, kickoff returns, kickoff return yards, longest kickoff return".split(",")
    player_fields['punt returns'] = "name, punt returns, punt return yards, longest punt return".split(",")
    player_fields['kicking'] = "name, field goals, field goals attempted, longest field goal, kicking extra points, kicking extra points attempted".split(",")
    player_fields['fumbles'] = "name, fumbles, fumbles lost, fumbles recovered, fumble yards".split(",")    
    for ps in ['passing','rushing','receiving','kicking','punting','kickoff returns','punt returns','fumbles']:
        fields = map(lambda x:x.strip(),player_fields[ps])
        abbr_fields = map(abbreviate,fields)
        
        sdql = "_t%%2,%s @ date = %s and team in [%s,%s] "%(','.join(fields),date,team,o_team)
        res = nfl.player_dts[ps.replace(' ','_')].query(sdql)
        pt = ['','']

        if not res or not res[0]:
            np = 0
        else:
            res = res[0]
            np = len(res[0])
        for p in range(np+4):
            if p<np:
                i = res[0][p]
            else:
                i = p%2 # add blanks to each team
            pt[i] += "<tr>"
            #print 'fields:',fields
            for c in range(len(fields)):    #html += "Line %s"%PyQL.html_tools.input(name='%s%s.line'%(key,owner),value='%s'%res.value_from_header('line'),size=4)
                if p<np: value = res[c+1][p]
                else: value=''                                 #     date_team|owner.site /Table:index.field
                pt[i] += "<td>%s</td>"%(PyQL.html_tools.input(name='%s%s.%s/%s:%d.%s'%(key,owner,['t:','o:'][i],ps.title().replace(' ','_'),p,fields[c]),value='%s'%(value,),size=12*(c==0) or 3),)
            pt[i] += "</tr>\n"
            
        html += "<HR><table border=0>\n"
        html += "<tr><th colspan=%d align=left bgcolor='#EEEEEE'>%s %s</th></tr>\n"%(len(fields),o_team,ps.title())
        html += "<tr><th>%s</th></tr>\n"%('</th><th>'.join(abbr_fields),)
        html += pt[1]
        html += "<tr><th colspan=%d align=left bgcolor='#EEEEEE'>%s %s</th></tr>\n"%(len(fields),team,ps.title())
        #html += "<tr><th>%s</th></tr>"%('</th><th>'.join(abbr_fields),)
        html += pt[0]        
        html += "</table>\n"
    html += "<input type='submit' name='submit' value='Update!'>"
    html += "</form>"
    return html
    




def test():
    k = {}
    k['date']=20140907
    k['team'] = 'Jets'
    k['client'] = 'SDB'
    res = form_game(**k)
    print res

if __name__ == "__main__":
    test()

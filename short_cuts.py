# expand short cuts common among sports
import re,string,glob,os
import PyQL.py_tools
from S2.directory import TOP_DIR

HIDE_A_QUOTE = '_hIdEaQuOtE'

SUMMATIVES = {'A':'Average','S':'Sum','R':'Replace'}

SUMMATIVE_PAT = re.compile("(?P<team>[tos]+)(?P<season>p*)(?P<repeat>[0-9]*)(?P<summative>[%s])\([\s]*(?P<team_level_flag>Team:)?(?P<parameter>(?:\([^),@]*?\))*?[^@),]+)[\s]*(?:@(?P<condition>(?:\([^),@]*?\))*?[^@),]+))?(?P<N>,[\s]*N[\s]*=[\s]*[0-9,]+|)[\s]*\)"%(''.join(SUMMATIVES.keys()),)) # added Team 20200113
#SUMMATIVE_PAT = re.compile("(?P<team>[tos]+)(?P<season>p*)(?P<repeat>[0-9]*)(?P<summative>[%s])\([\s]*(?P<parameter>(?:\([^),@]*?\))*?[^@),]+)[\s]*(?:@(?P<condition>(?:\([^),@]*?\))*?[^@),]+))?(?P<N>,[\s]*N[\s]*=[\s]*[0-9,]+|)[\s]*\)"%(''.join(SUMMATIVES.keys()),)) # added condition 20120312SUMMATIVE_PAT = re.compile("(?P<team>[tos]+)(?P<season>p*)(?P<repeat>[0-9]*)(?P<summative>[%s])\([\s]*(?P<parameter>(?:\([^),@]*?\))*?[^@),]+)[\s]*(?:@(?P<condition>(?:\([^),@]*?\))*?[^@),]+))?(?P<N>,[\s]*N[\s]*=[\s]*[0-9,]+|)[\s]*\)"%(''.join(SUMMATIVES.keys()),)) # added condition 20120312
#SUMMATIVE_PAT = re.compile("(?P<team>[tospnPNS]+)(?P<summative>[AS])\([\s]*(?P<parameter>(?:\([^),@]*?\))*?[^@),]+)[\s]*(?:@(?P<condition>(?:\([^),@]*?\))*?[^@),]+))?(?P<N>,[\s]*N[\s]*=[\s]*[0-9,]+|)[\s]*\)") # added condition 20120312kwargs.get('short_cuts',[])
#SUMMATIVE_PAT = re.compile("(?P<team>[tospnPNS]+)(?P<summative>[AS])\([\s]*(?P<parameter>(?:\([^),@]*?\))*?[^@),]+)[\s]*(?:@(?P<condition>(?:\([^),@]*?\))*?[^@),]+))?(?P<N>,[\s]*N[\s]*=[\s]*[0-9,]+|)[\s]*\)(\[[^]]+\])?") # added condition 20120312, added square bracket 20140904
MATH_PAT = re.compile("([\s]*[+-/*][\s]*)")
START = "([^A-Z])"
PREFIX_RE = "(?P<prefix>[sSpPnNto0-9]+:|)"
STAT_PREFIX_RE = START+r"(?:([A-Za-z0-9]+):)?(?:([A-Za-z\. 0-9]+):)?(?:([sSpPnNto0-9]+):)?"

def protect_quotes(text,d,n=0):
    ret = '' # return a string with quoted text subed out and a dict with sub these back
    in_quote = ''  #the flavor of the quote
    quote = ''
    len_text = len(text)
    i = -1
    while i < len_text-1:
        i += 1
        c = text[i]
        if c in ['"',"'"] and  i < (len_text - 3) and c == text[i+1] == text[i+2]:
            c = 3*c
            i += 2
        #print "c,i:",c,i
        if in_quote and c==in_quote: # end quote - write to d
            quote += c
            key = "%s%d_"%(HIDE_A_QUOTE,n)
            assert not d.has_key(key)
            d[key] = quote
            #print "close quote",key,quote
            n += 1
            quote = ''
            in_quote = ''
            ret += "%s"%key

        elif in_quote:   # continue with a quote
            quote += c
        elif not in_quote and c in ["'","'''",'"','"""']:     # start new quote
            in_quote = c
            quote = c
            #print "start new quote of flavor:",c
        else:             # not a quote
            ret += c
    return ret,d,n

def expand(text,clients=[],sport='default'):
    #CLIENT_SHORT_CUTS = load_short_cuts(); print "short cuts reloading CLIENT SC: turno OFF for PROSD!"
    #print "scsc.expand gets:",text
    # each method can add new as terms which need to be protected.
    n = 0
    d = {}
    text = text.replace(" and "," |and| ")
    text = text.replace(" or "," |or| ")

    # this wants to be first to handle nested as:  tA(PY)
    text,d,n = protect_quotes(text,d,n)
    #print "protected1:",text
    text = expand_summative(text,sport=sport)

    for client in clients:
        #print "client:",client
        if CLIENT_SHORT_CUTS.get(client,{}).get(sport.upper()):
            #print "short cuts.sport:",sport
            text,d,n = protect_quotes(text,d,n)
            text = CLIENT_SHORT_CUTS[client][sport.upper()].expand(text)
            #print "csc.txt:",text
    #for k in d.keys(): text = text.replace(k,d[k])
    #print "expanded summative:",text
    text,d,n = protect_quotes(text,d,n)
    #print "protected2:",text
    text = expand_multiple_letters(text,sport)
    #for k in d.keys(): text = text.replace(k,d[k])

    text,d,n = protect_quotes(text,d,n)
    #print "protected3:",text
    #print "protece43d:",text
    #print "d:",d
    text = expand_single_letters(text,sport)
    for k in d.keys():
        #print "replacing `%s`\nwith: `%s`"%(k,d[k])
        text = text.replace(k,d[k])

    text = text.replace("|and|"," and ")
    text = text.replace("|or|"," or ")
    text = text.replace("  "," ")

    return text

def sub_single(g):
    ret = ""
    start,team,player,reference = g.group(1),g.group(2),g.group(3),g.group(4)
    #print "ss:",start,team,player,reference
    if team: ret += team + ":"
    if player: ret += player + ":"
    if reference: ret += reference + ":"
    #print "ss.ret:",ret,len(ret)
    return string.strip(ret)

def sub_single_opponent(g):
    #print "sso: g.groups:%s"%(g.groups(),)
    ret = ''
    start,team,player,reference = g.group(1),g.group(2),g.group(3),g.group(4)
    if team: ret += team + ":"
    if player: ret += player + ":"
    if reference: ret += reference + ":"
    if ret:
        parts = map(string.strip,string.split(ret,':')[:-1])
        #print "parts:",parts
        if not parts: parts = ['o']
        else: parts[-1] += 'o'
        ret = string.join(parts,':')+':'
    return ret or "to:"

def sub_single_s(g): # for starter previous
    #print "sso: g.groups:%s"%(g.groups(),)
    ret = ''
    start,team,player,reference = g.group(1),g.group(2),g.group(3),g.group(4)
    if team: ret += team + ":"
    if player: ret += player + ":"
    if reference: ret += reference + ":"
    if ret:
        parts = map(string.strip,string.split(ret,':')[:-1])
        #print "parts:",parts
        if not parts: parts = ['s']
        else: parts[-1] += 's'
        ret = string.join(parts,':')+':'
    return ret or "ts:"

def replace_single_letter_short_cut(g,sport='default'):
    #print "sp[ort:",sport
    #print g.groups()
    start =  g.group("start")
    end = g.group("end")
    ret = ''
    prefix = string.strip(g.group("prefix") )
    abbreviations = g.group("abbreviations")

    #print "prefix",prefix
    #return "translated text"
    points = "points"
    if sport == 'nhl':
        points = "goals"
    elif sport == 'mlb':
        points = "runs"
    #print "goals:",points
    for character in abbreviations:
        if not character.strip():
            ret += " "
            continue
        ret = ret + " and "*(ret!='' and character not in [','])
        if character in "AH": ret += prefix + "site==" + {"A":"'away'","H":"'home'"}[character]
        #if character in ["W"]: ret += prefix[:-1]+"o:%s<"%points + prefix+points
        #if character in ["L"]: ret += prefix + points+ "<" + prefix[:-1]+"o:"+points
        # update 20130305 so that A(W)@team doesn't count runs<o:runs as false when they are both None
        if character in ["W"]: ret += "0<Team:%s%s-Team:%so:%s"%(prefix,points,prefix[:-1],points)
        if character in ["L"]: ret += "0<Team:%so:%s-Team:%s%s"%(prefix[:-1],points,prefix,points)
        if character in ["F"]:
            if sport in ['mlb','nhl']: ret += prefix+"line+0 < -105"
            else: ret += prefix+"line+0<0"
        if character in ["D"]:
            if sport in ['mlb','nhl']: ret += "-105 < " + prefix + "line"
            else: ret += prefix+"line+0>0"

        if character in ["O"]: ret += prefix + "total+0<" + prefix + points + '+' + prefix[:-1] + "o:"+points
        if character in ["U"]: ret += prefix + points + '+' + prefix[:-1] + "o:"+points + "< " + prefix+ "total"
        if character in ["C"]: ret += "("+prefix + "conference = " + prefix[:-1] + "o:conference)"
        if character in ["X"]:
            if sport=='mlb': ret += "9<len("+prefix+"inning runs)"
            elif sport=='ncaabb': ret += "2<len("+prefix+"half scores)"
            elif sport=='nhl': ret += "3<len("+prefix+"period scores)"
            else: ret += "4<len("+prefix+"quarter scores)"
        if character in [","]: ret += ','
        #print "char   ret:",character,ret
    ret = string.strip(ret)
    return "%s(%s) as '%s%s'"%(start, ret,prefix,abbreviations) + end

def expand_single_letters(text,sport="default"):
     # then handle single characgter shortcuts
    # loop to get possible nested matches such as W@H
    text = ' ' + text + ' '
    last_text = None
    abbr = "HAWLFDOUCX"
    while last_text != text:
        #print "last_text",last_text,"text",text
        last_text = text
        sport_re = "(?P<sport>[^>]+)>"
        start_re = "(?P<start>(?:^[\s]+)|(?:[@\(,])|(?:[^=><*/+-][\s]+))"
        end_re = "(?P<end>(?:[\)\,@])|(?:[\s]+[^=><*/+-])|(?:[\s]+$))"
        text = re.sub(start_re+PREFIX_RE+"(?P<abbreviations>[%s]+)"%abbr+end_re,
                                               lambda x,r=replace_single_letter_short_cut,s=sport:r(x,s),
                                               text)
    return string.strip(text)

# added 20121023: need to handle oA(points+line>o:points)
MATH_AND_COND_PAT = re.compile("((?:[\s]*[+-/*><=]+[\s]*)|(?: \|?and\|? ))")
def add_prefix_to_parameter(prefix,parameter):
    # parameter might be compound eg points - penalties
    terms = MATH_AND_COND_PAT.split(parameter)
    #print "math terms:",terms
    symbol = 0
    ret = ''
    for term in terms:
        if symbol:
            ret += term
            symbol = 0
        elif  term.strip().isdigit() or term=='.' or not term or term.startswith('_hIdEaQ'):
            ret += term
            symbol = 1
        else:
            #print "adding prefix to: `%s`"%term
            ret += prefix + ':' * (':' not in term) + string.strip(term)
            symbol = 1
    return ret

def summative_replace(g,sport='default'):
    team = g.group("team") # t, s, o, os, ts, tos
    while len(team)>1 and team.startswith('t'):
        team = team[1:]
    season = g.group("season") # any number of 'p's
    repeat = g.group("repeat")
    if repeat:
        repeat_as = repeat
        repeat = int(repeat)
    else:
        repeat_as = ''
        repeat = 0
    if season or repeat:
        season_ref = "-%d"%((repeat or 1) +(len(season) or 1) - 1,)
    else: season_ref = ''
    #print "team:",team
    # short cuts for columns are handled in columns.py
    group_summative = g.group("summative")
    summative = SUMMATIVES[group_summative]
    parameter = g.group("parameter")
    condition = (g.group("condition") or '').strip()
    team_level_flag = (g.group("team_level_flag") or '').strip()
    if condition: condition += " and "
    #print "paramtere:'%s'"%parameter
    mo = re.search(STAT_PREFIX_RE,' ' + parameter)
    team_term = {'s':'t','os':'o'}.get(team,team)
    inner_prefix = team_term+ (mo.group(2) or '')
    N = g.group("N") or ''
    if team_term == 't':
        prefix_parameter = parameter
    else:
        prefix_parameter = add_prefix_to_parameter(team_term,parameter)
    print_team_term = {'t':''}.get(team_term,team_term+':')
    inner_prefix = {'t':''}.get(inner_prefix,inner_prefix+':')
    ret=  summative + "(" + team_level_flag + prefix_parameter + "@" + add_prefix_to_parameter(team_term,condition) + ' ' +print_team_term +{'s':'starter','os':'starter'}.get(team,'team')+" and " + print_team_term + "season"
    #print "inner prefex:",inner_prefix
    if inner_prefix not in ['t:','','oo:','o:']:
        ret += " and " + inner_prefix + "season="+print_team_term+"season"
    ret +=  N +")"
    if season_ref: # invoke square brackets
        ret = "(" + ret # need to 'as' the summative and square bracked together.
        ret += '['+expand(add_prefix_to_parameter(team_term,condition),sport=sport) + ' ' +print_team_term +{'s':'starter','os':'starter'}.get(team,'team')+" and " + print_team_term + "season" + season_ref
        if inner_prefix not in ['t:','','oo:','o:']:
            ret += " and " + inner_prefix + "season"+season_ref+"="+print_team_term+"season"+season_ref
        ret += "])"


    cond = g.group("condition") or ''
    if cond: cond = '@' + cond
    as_term = g.group("team") + g.group("season") + repeat_as + g.group("summative") + "(" + g.group("parameter") + cond + N + ")"
    #print "as_term",as_term
    if HIDE_A_QUOTE in as_term:
        return ret # cannot add an as term with a quote
    return ret + " as '%s'"%as_term
    #return "(%s) as '%s'"%(ret,as_term )

def expand_summative(text,sport='default'):
    return SUMMATIVE_PAT.sub(lambda mo:summative_replace(mo,sport),text)

def expand_multiple_letters(text,sport='default'):
    text = ' %s '%text
    text = re.sub("([^a-zA-Z0-9_.'])today([^a-zA-Z0-9_('])",lambda g: g.group(1) + "PyQL.py_tools.today() as 'today' " + g.group(2),text)
    text = re.sub(PREFIX_RE + "(?P<abbreviation>HWP)",
       lambda g:'(Average(100*(('+g.group(1)+'W or '+g.group(1)+'L or 1/0) and '+g.group(1)+'W)@'+g.group(1)+'team and '+g.group(1)+'season and ' +g.group(1)+"site='home'" + (g.group(1) not in ['t','o','to',''])*(' and '+g.group(1)+'season=season')+")) as '"+g.group(1)+"H<|>W<|>P'",text)
    text = re.sub(PREFIX_RE + "(?P<abbreviation>AWP)",
       lambda g:'(Average(100*(('+g.group(1)+'W or '+g.group(1)+'L or 1/0) and '+g.group(1)+'W)@'+g.group(1)+'team and '+g.group(1)+'season and ' +g.group(1)+"site='away'" + (g.group(1) not in ['t','o','to',''])*(' and '+g.group(1)+'season=season')+")) as '"+g.group(1)+"A<|>W<|>P'",text)
    #text = re.sub(PREFIX_RE + "(?P<abbreviation>AWP)",
    #   lambda g:'(Average(100*('+g.group(1)+'W)@'+g.group(1)+'team and '+g.group(1)+'season and ' +g.group(1)+"site='away'" + (g.group(1) not in ['t','o','to',''])*(' and '+g.group(1)+'season=season')+")) as '"+g.group(1)+"A<|>W<|>P'",text)
    text = re.sub(PREFIX_RE + "(?P<abbreviation>[P]+RSW)",
       lambda g:'(Sum(('+g.group(1)+'W)@'+g.group(1)+'team and '+g.group(1)+'playoffs=0 and '+g.group(1)+'season)['+g.group(1)+'team and  '+g.group(1)+'playoffs=0 and '+g.group(1)+"season-"+"%d"%(len(g.group(2))-3,) + "]) as '"+g.group(1)+g.group(2)+"'",text)

    text = re.sub(PREFIX_RE + "(?P<abbreviation>WP)",
       lambda g:'(Average(100*(('+g.group(1)+'W or '+g.group(1)+'L or 1/0) and '+g.group(1)+'W)@'+g.group(1)+'team and '+g.group(1)+'season' + (g.group(1) not in ['t:','o:','to:',''])*(' and '+g.group(1)+'season=season')+")) as '"+g.group(1)+"WP'",text)
    if sport.lower() == 'nba':
        text = re.sub(STAT_PREFIX_RE + "(?P<abbreviation>FD.FP|(?<!\.)FP)",
                 lambda g,ss=sub_single:g.group(1)+'('+
                              ss(g)+"points+"+
                              ss(g)+"rebounds*1.2+"+
                              ss(g)+"assists*1.5+"+
                              ss(g)+"steals*2+"+
                              ss(g)+"blocks*2+"+
                              ss(g)+"turnovers*(-1)) as '%s%s'"%(ss(g),'<|>'.join(g.group(5))),  text)

        text = re.sub(STAT_PREFIX_RE + "(?P<abbreviation>DK.FP)",
                      lambda g,ss=sub_single:g.group(1)+'('+
                              ss(g)+'points+'+
                              ss(g)+"three pointers made*0.5+"+
                              ss(g)+"rebounds*1.25+"+
                              ss(g)+"assists*1.5+"+
                              ss(g)+"steals*2+"+
                              ss(g)+"blocks*2+"+
                              ss(g)+"turnovers*(-0.5) + {5:3,4:3,3:3,2:1.5}.get(("+
                                 ss(g)+"points>9)+("+
                                 ss(g)+"rebounds>9)+("+
                                 ss(g)+"assists>9)+("+
                                 ss(g)+"blocks>9)+("+
                                 ss(g)+"steals>9),0)) as '%s%s'"%(ss(g),'<|>'.join(g.group(5))),  text)


    elif sport.lower()=='nfl':
        text = re.sub(STAT_PREFIX_RE + "(DK\.OFP|OFP)",
          #lambda g,ss=sub_single:g.group(1)+"((300<="+ss(g)+"passing yards)*3+"+
          #      "(100<="+ss(g)+"rushing yards)*3+"+
          #      "(100<="+ss(g)+"receiving yards)*3+"+
                      lambda g,ss=sub_single:g.group(1)+"({1:3}.get((300<="+ss(g)+"passing yards),0)+"+
                         "{1:3}.get((100<="+ss(g)+"rushing yards),0)+"+
                         "{1:3}.get((100<="+ss(g)+"receiving yards),0)+"+
                         ss(g)+"passing yards*.04+"+
                         ss(g)+"passing touchdowns*4-"+
                         ss(g)+"interceptions thrown*1+"+
                         ss(g)+"receiving yards*.1+"+
                         ss(g)+"receptions+"+
                         ss(g)+"receiving touchdowns*6+"+
                         ss(g)+"rushing yards*.1+"+
                         ss(g)+"rushing touchdowns*6+"+
                         ss(g)+"punt return touchdowns*6+"+
                         ss(g)+"kickoff return touchdowns*6+"+
                         ss(g)+"passing conversions*2+"+
                         ss(g)+"receiving conversions*2+"+
                         ss(g)+"rushing conversions*2-"+
                         ss(g)+"fumbles lost) as '%s%s'"%(ss(g),'<|>'.join(g.group(5))),  text)
    if sport in ["nfl","cfl","nba","mlb","wnba","nhl"]:
        text = re.sub(STAT_PREFIX_RE + "(PO)",
               lambda g,ss=sub_single:g.group(1)+"("+ss(g)+"playoffs=1) as '%s%s'"%(ss(g),'<|>'.join(g.group(5))),  text)
    return text.replace('<|>','').strip()

def load_short_cuts():
    dsc = {}
    files = glob.glob(os.path.join(TOP_DIR,"Client",'*','*','Source','*_short_cuts.py'))
    files.sort()
    #print "sc files:",files
    for f in files:
        parts = f.split(os.path.sep)
        sport = parts[-3]
        client = parts[-4]
        dsc.setdefault(client,{})[sport] = PyQL.py_tools.importer(f)
    return dsc
CLIENT_SHORT_CUTS = load_short_cuts() # {"KS":{NFL:sc,NBA:sc...},{TH:{..}...}
#print "CLIENT_SHORT_CUTS",CLIENT_SHORT_CUTS

######## test #########

def test():
    text = """oA(Team:o:points,N=2)""" # and PRSWL and PO"""
    expanded = expand(text,clients=['KS'],sport='nfl')
    print "text:",text,"\nexpands to:",expanded


def test_suite():
    text = "p:P4+p:P3"
    expanded = expand(text,clients=['KS'],sport='nfl')
    print "text:",text,"\nexpands to:",expanded
    assert expanded == "(Average(100*((o:points<points) as 'W')@team and season)) as 'WP'>4 and first downs as 'FD'>5"


    text = "team as ' HD ' and HD and p:site"
    expanded = expand(text,sport='mlb')
    print "text:",text,"\nexpands to:",expanded
    assert expanded == "team as ' HD ' and (site=='home' and -105 < line) as 'HD' and p:site"

    text = "WP>4 and date>today"
    expanded = expand(text,sport='mlb')
    print "text:",text,"\nexpands to:",expanded
    assert expanded == "(Average(100*((o:runs<runs) as 'W')@team and season)) as 'WP'>4 and date>PyQL.py_tools.today() as 'today'"

    text = "p:P4+p:P3"
    expanded = expand(text,clients=['KS'],sport='nfl')
    print "text:",text,"\nexpands to:",expanded
    assert expanded == "(Average(100*((o:points<points) as 'W')@team and season)) as 'WP'>4 and first downs as 'FD'>5"

    text = """A(P1)@1,team and p:M3>=10"""
    expanded = expand(text,clients=['KS'],sport='nba')
    print "text:",text,"\nexpands to:",expanded

    text = """A(P1)@1,team and P6:M3>=10 and P4>5"""
    expanded = expand(text,clients=['KS'],sport='nfl')
    print "text:",text,"\nexpands to:",expanded


if __name__ == "__main__":
    test()
    #test_suite()

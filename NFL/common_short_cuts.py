# expand short cuts common among sports

import re,string
from PyQL.py_tools import split_not_protected

#SUMMATIVE_PAT = re.compile("(?P<team>[tos])(?P<summative>[AS])\([\s]*(?P<parameter>[^),]+)[\s]*(?P<N>,[\s]*N[\s]*=[\s]*[0-9]+|)[\s]*\)")

SUMMATIVE_PAT = re.compile("(?P<team>[tos])(?P<summative>[AS])\([\s]*(?P<parameter>(?:\([^),@]*?\))*?[^@),]+)[\s]*(?:@(?P<condition>(?:\([^),@]*?\))*?[^@),]+))?(?P<N>,[\s]*N[\s]*=[\s]*[0-9,]+|)[\s]*\)") # added condition 20120312
MATH_PAT = re.compile("([\s]*[+-/*][\s]*)")
START = "([^A-Z])"    
#PREFIX_RE = "(?P<prefix>[sSpPnNto:]*)"
PREFIX_RE = "(?P<prefix>[sSpPnNto0-9]+:|)"
STAT_PREFIX_RE = START+r"(?:([A-Za-z0-9]+):)?(?:([A-Za-z\. 0-9]+):)?(?:([sSpPnNto0-9]+):)?"
#SINGLE_QUOTE_PAT = re.compile("'([^']+)'")




def protect_sq(text):
    ret = '' # return a string with single quoted text subed out and a dict with sub these back
    d = {}
    in_quote = 0
    quote = ''
    n = 0
    for c in text:
        #print "c:",c
        if in_quote and c=="'": # end quote - write to d
            key = "_sq%d_"%n            
            d[key] = quote
            n += 1
            quote = ''
            in_quote = 0
            ret += "'%s'"%key 
        elif in_quote:   # continue with a quote
            quote += c
        elif c =="'":     # start new quote 
            in_quote = 1 
        else:             # not a quote
            ret += c
    return ret,d

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
            key = "_hIdEaQuOtE%d_"%n
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



def expand(text,sport='default'):
    #print "exp[and gets:",text
    # each method can add new as terms which need to be protected.
    n = 0
    d = {}
    text,d,n = protect_quotes(text,d,n)
    #print "protected1:",text
    #return
    text = expand_summative(text)
    #for k in d.keys(): text = text.replace(k,d[k])
    #print "expanded summative:",text
    text,d,n = protect_quotes(text,d,n)
    #print "protected2:",text    
    text = expand_multiple_letters(text)    
    #for k in d.keys(): text = text.replace(k,d[k])
    
    text,d,n = protect_quotes(text,d,n)
    #print "protected3:",text    
    #print "protece43d:",text
    #print "d:",d
    text = expand_single_letters(text,sport)
    for k in d.keys():
        #print "replacing `%s`\nwith: `%s`"%(k,d[k])
        text = text.replace(k,d[k])    
    return text 


def sub_single(g):
    ret = ""
    start,team,player,reference = g.group(1),g.group(2),g.group(3),g.group(4)
    if team: ret += team + ":"
    if player: ret += player + ":"
    if reference: ret += reference + ":"    
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
        if character in "AH": ret += prefix + "site==" + {"A":"away","H":"home"}[character]
        if character in ["W"]: ret += prefix[:-1]+"o:%s<"%points + prefix+points
        if character in ["L"]: ret += prefix + points+ "<" + prefix[:-1]+"o:"+points
        if character in ["F"]:
            if sport == 'mlb': ret += prefix+"line+0 < -105"
            else: ret += prefix+"line+0<0"
        if character in ["D"]:
            if sport == 'mlb': ret += "-105 < " + prefix + "line"
            else: ret += prefix+"line>0"

        if character in ["O"]: ret += prefix + "total+0<" + prefix + points + '+' + prefix[:-1] + "o:"+points
        if character in ["U"]: ret += prefix + points + '+' + prefix[:-1] + "o:"+points + "< " + prefix+ "total"
        if character in ["C"]: ret += "("+prefix + "conference = " + prefix[:-1] + "o:conference)"
        if character in ["X"] and sport=='mlb': ret += "9<len("+prefix+"inning runs)"          
        if character in [","]: ret += ','    
        #print "char   ret:",character,ret
    ret = string.strip(ret)
    return "%s(%s) as '%s%s'"%(start, ret,prefix,abbreviations) + end

def expand_single_letters(text,sport="default"):
     # then handle single characgter shortcuts    
    # loop to get possible nested matches such as W@H
    text = ' ' + text + ' '
    last_text = None
    abbr = "HAWLFDOUC"
    if sport == 'mlb': abbr += 'X'
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

def add_prefix_to_parameter(prefix,parameter):
    # parameter might be compound eg points - penalties
    terms = MATH_PAT.split(parameter)
    #print "math terms:",terms
    symbol = 0
    ret = ''
    for term in terms:
        if symbol:
            ret += term
            symbol = 0
        elif  term.strip().isdigit() or term=='.' or not term:
            ret += term
            symbol = 1
        else:
            ret += prefix + ':' * (':' not in term) + string.strip(term)
            symbol = 1
    return ret

def summative_replace(g):
    team = g.group("team")
    # short cuts for columns are handled in columns.py
    group_summative = g.group("summative")
    summative = {"A":"Average","S":"Sum"}[group_summative]
    parameter = g.group("parameter")
    condition = (g.group("condition") or '').strip()
    if condition: condition += " and "
    #print "paramtere:'%s'"%parameter
    mo = re.search(STAT_PREFIX_RE,' ' + parameter)
    team_term = {'s':'t'}.get(team,team)
    inner_prefix = team_term+ (mo.group(2) or '')
    N = g.group("N") or ''
    if team_term == 't':
        prefix_parameter = parameter
    else:
        prefix_parameter = add_prefix_to_parameter(team_term,parameter)
    print_team_term = {'t':''}.get(team_term,team_term+':')
    inner_prefix = {'t':''}.get(inner_prefix,inner_prefix+':')
    ret= summative + "(" + prefix_parameter + "@" + condition + print_team_term +{'s':'starter'}.get(team,'team')+" and " + print_team_term + "season"
    #print "inner prefex:",inner_prefix
    if inner_prefix not in ['t:','','oo:','o:']:
        ret += " and " + inner_prefix + "season="+print_team_term+"season"
    ret +=  N +")"
    cond = g.group("condition") or ''
    if cond: cond = '@' + cond 
    as_term = g.group("team") + g.group("summative") + "(" + g.group("parameter") + cond + N + ")"
    return ret + " as '%s'"%as_term # XX single quotes in summative fails ??

def expand_summative(text):
    return SUMMATIVE_PAT.sub(summative_replace,text) 

def expand_multiple_letters(text):
    text = re.sub(PREFIX_RE + "(?P<abbreviation>WP)",
       lambda g:'(Average(100*('+g.group(1)+'W)@'+g.group(1)+'team and '+g.group(1)+'season' + (g.group(1) not in ['t','o','to'])*(' and '+g.group(1)+'season=season')+")) as '"+g.group(1)+"WP'",text)
    return text



######## test #########

def test():
    #text = "   p:runs@tA(runs)>0"
    text = "1 as '__t_q4__'@S(W@team and season) and H"
    text = "Count(points) as '__N__',Record_WLPM(points-o:points,format='''lambda x:'%s-%s (%0.2f, %0.1f)'%(x[0],x[1],x[3],100.*x[0]/((x[0]+x[1]) or 1))''') as '__su__',Record_WLPM(points+line-o:points,format='''lambda x:'%s-%s-%s (%0.2f, %0.1f)'%(x[0],x[1],x[2],x[3],100.*x[0]/((x[0]+x[1]) or 1))''') as '__ats__',Record_WLPM(points+o:points-total,format='''lambda x:'%s-%s-%s (%0.2f, %0.1f)'%(x[0],x[1],x[2],x[3],100.*x[0]/((x[0]+x[1]) or 1))''') as '__ou__',Average(t:line,format='%0.1f') as '__t_average_line__',Average(t:total,format='%0.1f') as '__t_average_total__',Average(t:quarter scores[0],format='%0.1f') as '__t_q1__',Average(t:quarter scores[1],format='%0.1f') as '__t_q2__',Average(t:quarter scores[2],format='%0.1f') as '__t_q3__',Average(t:quarter scores[3],format='%0.1f') as '__t_q4__',Average(t:points,format='%0.1f') as '__t_total_points__'@HD"
    #text = "oS(o:yards+t:yards rushing,N=4) and A(rushing yards@team and season)<10"
    #text = "tS(earned runs + starter earned runs)/ tS(9 - starter innings pitched) "
    #text = "(date,self.nice_date(date),points,o:points,overtime)@ team=Bears and season=2010 as 'x'"
    #text = "pPo:WP as foo"
    #text = "team as ' HD ' and HD and p:site"
    #text = "HUD"
    print "text:",text
    print "expand:",expand(text,sport='mlb')    
    #text = "oS(9.0 - starter innings pitched)<20"
    #print "text:",text
    #print "expand_summative(text):",expand(text)    
    ##text = "ppp:HD"
    #print "text:",text
    #print "expand(text)",expand(text,'nfl')
    #text = "p5:XHD"
    #print "text:",text
    #print "expand(text for mlb)",expand(text,'mlb')
    #text = "ALA and team > ALA and ALA and team=ALA and ALA and ALA"
    #print "text:",text
    #print "expand(text for mlb)",expand(text,'mlb')
    #text = "p5:HDL"
    #print "text:",text
    #print "expand(text for nhl)",expand(text,sport='nhl')

if __name__ == "__main__":
    test()


   
 

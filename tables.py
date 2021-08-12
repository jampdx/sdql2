import sys,string,re
import PyQL.outputs

TABLES = {
" SU":
    ["S(~D~*(o:points<t:points),format='%d') as 'Wins'",
    "S(~D~*(o:points>t:points),format='%d') as 'Losses'",
    "S(~D~*(o:points==t:points+0),format='%d') as 'Pushes'"],
     "OU":
    ["S(~D~*(total<o:points+t:points),format='%d') as 'Over'",
    "S(~D~*(o:points+t:points<total),format='%d') as 'Under'",
    "S(~D~*(o:points+t:points==total),format='%d') as 'Pushes'",
    "A(~D~*(total),format='%0.1f') as 'Total'"],
}

DIFF_COND = {
    #"win-loss":["((W) or None)","((L) or None)"],
    #"over-under":["((O) or None)","((U) or None)"],
    "home-away":["((H) or None)","((A) or None)"],
    "fav-dog":["((F) or None)","((D) or None)"],
    "team-opp":"team"
    }

def select_table(**kwargs):
    options = kwargs.get("table_options",None)
    name = kwargs.get("form_name_table",'table')
    selected = kwargs.get(name,None)
    if not options:
        options = filter(lambda x:x[0]!='_',TABLES.keys())
        options.sort()
    ret = ['<select name="%s">'%name]
    for option in options:
        ret.append('<option%s value="%s">%s'%(" SELECTED"*(option==selected),option,option))
    ret.append('</select>')
    return string.join(ret,"\n")

def select_side(**kwargs):
    options = kwargs.get("side_options",None)
    name = kwargs.get("form_name_side",'side')
    selected = kwargs.get(name,None)
    if not options:
        options = ["team","opponent"]
    ret = ['<select name="%s">'%name]
    for option in options:
        ret.append('<option%s value="%s">%s'%(" SELECTED"*(option==selected),option,option))
    ret.append('</select>')
    return string.join(ret,"\n")

def select_diff(**kwargs):
    options = kwargs.get("diff_options",None)
    name = kwargs.get("form_name_diff",'diff')
    selected = kwargs.get(name,None)
    if not options:
        options = ['']+DIFF_COND.keys()
    ret = ['<select name="%s">'%name]
    for option in options:
        ret.append('<option%s value="%s">%s'%(" SELECTED"*(option==selected),option,option))
    ret.append('</select>')
    return string.join(ret,"\n")

def switch_sides(s):
    s = map(lambda x:x.replace('t:','TEAM:'),s)
    s = map(lambda x:x.replace('o:','t:'),s)
    return map(lambda x:x.replace('TEAM:','o:'),s)

def expand_diff(select,diff):
    #print "ediff gets",diff
    if not diff:
        return map(lambda x:x.replace('~D~','1'),select)
    if diff == "team":
        ret = []
        for t,o in zip(select,switch_sides(select)):
            ret.append(t.split(' as ')[0].replace('~D~','1') + "-" + o.replace('~D~','1'))
        return ret
    ret = []
    for s in select:
        ret.append(s.split(' as ')[0].replace('~D~',diff[0]) + "-" + s.replace('~D~',diff[1]))
    return ret

def prepare_select(s,side="t",diff=[]):
    #print "ps gets",diff
    if side and side[0] == "o":
        s = switch_sides(s)
    s = expand_diff(s,diff)
    return ",".join(s)


############# tests and demos ##############

# test from NFL/Source/tables.py

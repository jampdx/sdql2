def input(name,type='text',value='',size=20,checked=0,rlabel=''):
    svalue = str(value).replace("'",'"')
    if type.lower() == 'submit':
        return "<input type='%s' name='%s' value='%s'>"%(type,name,svalue)
    if type.lower() == 'checkbox':
        return "<input type='%s' name='%s' value='%s'%s>%s"%(type,name,svalue,' checked'*checked,rlabel)
    if type.lower() == 'radio':
        return "<input type='%s' name='%s' value='%s'%s>"%(type,name,svalue,' checked'*checked)
    return "<input type='%s' name='%s' value='%s' size=%s>"%(type,name,svalue,size)

def select(options,name,selected,size=1):
    if type(selected) is str: selected = [selected]
    ret = "<select name='%s' size=%s>"%(name,size)
    for option in options:
        ret += "<option%s>%s\n"%(' SELECTED'*(option in selected),option)
    ret += "</select>"
    return ret

def textarea(name,cols=80,rows=10,text=''):
    return "<textarea name='%s' cols=%s rows=%s>%s</textarea>"%(name,cols,rows,text)

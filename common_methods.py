import urllib,cgi,re

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

#def format_name(name):
#    return  name.title().replace('_',' ').replace('-',' ').replace('.','').replace("'",'').strip()


def format_name(name):
    if not name: return name # in case it is None
    name = name.replace(".",'').replace("-",' ').replace("'",'').replace(",",' ')
    name = re.sub('[\s]+',' ',name)
    return name.strip()

def insert_client(header,client):
    if ':' not in header: #no prefix
        return "%s.%s"%(client,header)
    pre,par = header.split(':',1)
    return "%s:%s.%s"%(pre,client,par)

# built for default lines to be entered for SDB - not used.
def insert_client_with_default(header,client):
    if ':' not in header: #no prefix
        return "((%s.%s is not None and %s.%s)  or %s)"%(client,header,client,header,header)
    pre,par = header.split(':',1)
    return "((%s:%s.%s is not None and %s:%s.%s) or %s:%s"%(pre,client,par,pre,client,par,pre,par)

def insert_clients(header,clients):
    if type(clients) is str: clients = [clients]
    lst = []
    if ':' not in header:
        pre,par = '',header
    else:
        pre,par = header.split(':',1)
        pre = pre + ':'

    for i in range(len(clients)):
        client = clients[i]
        lst.append("%s%s.%s"%(pre,client,par))

    return "(filter(lambda x:x is not None,%s)+[None])[0]"%lst

def safe_d_d_format(str_none=' ',sigfig=0): # if either two-ple item is None show STR_NONE
    if not str_none: str_none = ' ' # otherwise the 'and' will not work
    return "lambda x:(None in x and '%s') or '%%0.%df-%%0.%df'%%x"%(str_none,sigfig,sigfig)

def nice_twople_format(str_none=' ',delim='-',sigfig=0): # if one item of a tuple is None show others
    if not str_none: str_none = ' ' # otherwise the 'or' will not work
    return "lambda x:((x[0] is None)*'%s' or '%%0.%df'%%x[0]) + '%s' +((x[1] is None)*'%s' or '%%0.%df'%%x[1])"%(str_none,sigfig,delim,str_none,sigfig)

def key_to_query_link(key,**kwargs):
    # 20130604: key is either (sdql, as) or (sdql, as, reduced_as)
    #print "common.key_to_query_link:", key ,kwargs
    page = kwargs.get("page",kwargs.get('form_action',"query"))
    url = ' '.join(key[1])
    sdql = ' '.join(key[-1])
    sdql = re.sub("team[\s]*[=]+[\s]*","",sdql)
    if not page: return sdql
    if sdql and sdql[0] == '.': # magic! this means to get the url from key[0]
        sdql = sdql[1:]
        url = ' '.join(key[0])
        url_as = "(%s) as '%s'"%(url,sdql)
        return "<a href=%s?sdql=%s&output=summary&no_as_sdql=%s>%s</a>"%(page,urllib.quote(url_as),urllib.quote(url)
                                                                         ,cgi.escape(sdql))
    return "<a href=%s?sdql=%s&output=summary>%s</a>"%(page,urllib.quote(url)
                                                                         ,cgi.escape(sdql))



def values_and_percent(v1,v2,str_none=' ',sigfig=1):
    if None in [v1.value(),v2.value()]: return str_none
    fstr = "%%s-%%s (%%0.%d"%sigfig +"f%%)"
    return fstr%(v1,v2,100.*v1.value()/v2.value())

def value_or_str_none(value,str_none=' '):
    if value in [None,'None']: return str_none
    return value

def clean_parameters(parameters,owners=[]):
    #print "clean_pars gets",parameters
    if owners: parameters = filter(lambda x:('.' not in x) or ('.'.join(x.split(".")[:-1]) in owners),parameters)
    parameters = map(lambda x:x.split(".")[-1],parameters)
    parameters.sort()
    parameters = dict.fromkeys(parameters).keys()
    parameters.sort()
    p_str = str(filter(lambda x:x[0]!='_' and x!='gid',parameters))[1:-1]
    return p_str.replace("'","").replace('"','')


if __name__ == "__main__":
    #print clean_parameters(["Bob.Foo.points"],owners=['Bob.Foo'])
    print insert_client_with_default("P:runs","Bob")

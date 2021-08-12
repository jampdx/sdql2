Not used: do this under Client

import sys,os,string,glob,datetime,re
import PyQL.py_tools as py_tools
import cgi

PAT_1e1_and = re.compile("(1[\s]*[=]{1,2}[\s]*1[\s]+and[\s]+)")
PAT_and_1e1 = re.compile("([\s]+and[\s]*1[\s]*[=]{1,2}[\s]*1)")
PAT_1_and = re.compile("( 1[\s]+and[\s]+)")
PAT_and_1 = re.compile("([\s]+and[\s]*1 )")
PAT_and_1end = re.compile("([\s]+and[\s]*1$)")

def clean_join(key):
    # remove verbose (), remove 1=1 and join.
    #Commented out 20050215 as unneeded and to avoid "(a or b) and c" => "a or b and c"
    #key = map(lambda x:x[1:-1]*(len(x) and ',' not in x and x[0]=='(' and x[-1]==')') or x,key) # remove ( )
    key = " " + string.join(key,' ') + " "
    key = PAT_1e1_and.sub(lambda x:' ',key)
    key = PAT_and_1e1.sub(lambda x:' ',key)
    key = PAT_1_and.sub(lambda x:' ',key)
    key = PAT_and_1.sub(lambda x:' ',key)
    key = PAT_and_1end.sub(lambda x:' ',key)    
    key = string.replace(key,"  "," ")
    terms = py_tools.split_not_protected(key," and ")
    unique_terms = []
    for term in terms:
        if term not in unique_terms: unique_terms.append(term)
    key = string.join(unique_terms," and ")
    return string.strip(key)

class Situations:
    
    def __init__(self,verbose=0):
        self.nice_date = lambda d: datetime.datetime(int(d[:4]),int(d[4:6]),int(d[6:])).strftime("%B %d, %Y")
        
        self.verbose = verbose  
        if self.verbose: print "Situations.__init__: verbose mode is on"
        self.pat_sub_pairs = []
        self.pat_sub_cleanup_pairs = []        
        self.pat_sub_cleanup_pairs.append(("( 1[\s]*[=]{1,2}[\s]*1[\s]+and )",lambda x:' '))
        self.pat_sub_cleanup_pairs.append(("($1[\s]*[=]{1,2}[\s]*1[\s]+and )",lambda x:' '))        
        self.pat_sub_cleanup_pairs.append(("(and[\s]+1[\s]*[=]{1,2}[\s]*1 )",lambda x:' '))
        self.pat_sub_cleanup_pairs.append(("( and[\s]+1[\s]*[=]{1,2}[\s]*1$)",lambda x:' '))                                
        self.pat_sub_cleanup_pairs.append(("( 1[\s]*[=]{1,2}[\s]*1[\s]+)",lambda x:' '))
        self.pat_sub_cleanup_pairs.append(("($1[\s]*[=]{1,2}[\s]*1[\s]+)",lambda x:' '))
        self.pat_sub_cleanup_pairs.append(("( and[\s]+1$)",lambda x:' '))
        self.pat_sub_cleanup_pairs.append(("( and[\s]+1 )",lambda x:' '))        
        self.pat_sub_cleanup_pairs.append(("( 1[\s]+and )",lambda x:' '))
        self.pat_sub_cleanup_pairs.append(("($1[\s]+and )",lambda x:' '))        
        self.pat_sub_cleanup_pairs.append(("[\s]+",lambda g:' ')) # single spaces
        
    def format_key(self,key):
        link_key = []
        text_key = []
        for item in key:
            if type(item) in py_tools.py_types.sequences:
                text_key.append(item[0]); link_key.append(item[-1])
            else:
                text_key.append(item); link_key.append(item)                
                
        link_key = " " + clean_join(link_key) + " "
        #text_key = clean_join(text_key) 
        text_key =  " " + string.join(text_key) + " "     
        for old,new in self.pat_sub_pairs + self.pat_sub_cleanup_pairs:
            if self.verbose:
                print "Sports/Source/situations.py.format_key:",old,text_key
            type_old,type_new = type(old),type(new)            
            if type_new == type_old == type("abc"): 
                text_key = string.replace(text_key,old,new)
            elif callable(new): # a function for a re.sub
                if type_old is type("abc"): old = re.compile(old)
                #print "text_key:",text_key
                text_key = old.sub(new,text_key)
            else: print " the self.pat_sub tuples (old,new) can be (text,text),(regex,function), (text,function)"
        text_key = string.strip(text_key)
        return "<nobr><a href=query?text=%s&output=summary>%s</a></nobr>"%(cgi.escape(link_key),
                                                                          cgi.urllib.quote(text_key))

        
if __name__ == "__main__": 
    s = Situations()
    #s.pat_sub_pairs.append((" and |-"," "))    
    #s.pat_sub_pairs.append(("|-",""))
    s.pat_sub_pairs.append(("[\s]+and[\s]+\|-",lambda x:" "))    
    #s.pat_sub_pairs.append(("|-",""))
    #s.pat_sub_pairs.append(("(after [a home an away]+ game) after being",lambda g:g.group(1) + " as"))
    # get rid of and vs. season<1998 (no week)
    #and (2002,8) < =(season,week)
    s.pat_sub_pairs.append(("([\s]+and[\s]+)*([0-9]+)[\s]*<[\s]*=[\s]*season",
                                lambda g:" since "+g.group(2))) 

    s.pat_sub_pairs.append(("(and )*\(([0-9]+),([0-9]+)\)[\s]*<[\s]*=[\s]*\(season,week\)",
                                lambda g:" since week "+g.group(3)+", "+g.group(2))) 
    s.pat_sub_pairs.append(("(and )*([0-9]+)[\s]*<[\s]*=[\s]*\season",
                                lambda g:" since "+g.group(2))) 
    s.pat_sub_pairs.append(("(after a [home|away]* game) after being",lambda g:g.group(1) + " as"))
    s.pat_sub_pairs.append(("(after a home|an away game) after being",lambda g:g.group(1) + " as"))
    s.pat_sub_pairs.append(("([\s]+and[\s]+)*([0-9]+)[\s]*<[\s]*=[\s]*date",lambda g,nice_date=s.nice_date:" since "+nice_date(g.group(2))))     
    print s.format_key((("The Bears","team=Bears"),"and",("|-after a home game","p:site=home"),"and",("|-after being a dog","0<line"),"and 20041030<=date and 1=1."))


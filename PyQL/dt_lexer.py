import ply.lex as lex
import PyQL.columns
import string

# get the names of the PyQL columns to include in lexer.
AGGREGATORS = filter(lambda name:name[0]!='_' and name[0].upper()==name[0],dir(PyQL.columns))

class Lex_Error(Exception):
    """Raised when lex has parsing failure.
    """
def t_error(t):
    print "Illegal character: '%s'" % t.value[0]
    t.lexer.skip(1)
    #raise Lex_Error("Illegal character: '%s'" % t.value[0])

def t_squarebracket_error(t):
    print "Illegal character: '%s'" % t.value[0]
    t.lexer.skip(1)
    #raise Lex_Error("Illegal character in squarebracket: '%s'" % t.value[0])

def t_dict_error(t):
    print "Illegal character: '%s'" % t.value[0]
    t.lexer.skip(1)
    #raise Lex_Error("Illegal character in dict: '%s'" % t.value[0])

def t_aggregator_error(t):
    print "Illegal character: '%s'" % t.value[0]
    t.lexer.skip(1)
    #raise Lex_Error("Illegal character in aggregator: '%s'" % t.value[0])


states = (
    ('squarebracket','exclusive'),
    ('dict','exclusive'),
    ('aggregator','exclusive')
    )

reserved = {}

tokens = [
    "AS",
    "CONJUNCTION",
    "PARAMETER",
    "WORD",
    "PYTHON_WORD", #eg `math.e` or `string.upper` in `len(map(string.upper,map(lambda x ...` or `_batters`
    "AGGREGATOR",
    "PYTHON_FUNCTION",
    "COMPARATOR",
    "STRING",
    "DB_STRING", # eg Cubs
    "INTEGER",
    "FLOAT",
    "MATH",
    "SQUARE_BRACKET",
    "SPACE",
    "DOLLAR_INDEX",
    "DOLLAR_SLICE",
    "BAR",
    "DICT",
] + reserved.values()

literals = '@,()[]:{}'

#t_ignore = t_aggregator_ignore = '\t\n'
#t_squarebracket_ignore = '\t\n'

# Overwrite this doc string with a list of your dt parameters
# Sort longest to shortest and escape spaces
def t_PARAMETER(t):
    #r"""parameter\ longer|parameter"""
    r"""__YOUR PARAMETERS HERE__"""
    t.type = reserved.get(t.value, 'PARAMETER')
    return t
# repeat for alias
#def t_ALIAS_REFERENCE(t):
#    r"""__YOUR ALIAS_REFERENCES HERE__"""
#    t.type = reserved.get(t.value, 'ALIAS_REFERENCE')
#    return t
#def t_ALIAS_CONDITION(t):
#    r"""__YOUR ALIAS_CONDITIONS HERE__"""
#    t.type = reserved.get(t.value, 'ALIAS_CONDITION')
#    return t

def t_DB_STRING(t):
    r"""__YOUR STRINGS HERE__"""
    t.type = reserved.get(t.value, 'DB_STRING')
    return t

def t_BAR(t):
   r'[|].*'
   t.value = t.value.strip()
   return t

def t_DOLLAR_INDEX(t):
   r'[$][0-9]+'
   t.value = t.value.strip()
   return t

def t_DOLLAR_SLICE(t):
   r'[$][[][0-9]*:[0-9]*[]]'
   t.value = t.value.strip()
   return t

def t_AS(t):
   r'[\s]+as[\s]+'
   t.value = t.value.strip()
   return t

def t_CONJUNCTION(t):
   r'[\s]+and[\s]+|[\s]+or[\s]+'
   t.value = t.value.strip()
   return t

# I'm writing meta code anyway so just leave as strings.
def t_FLOAT(t):
    r'[\-0-9]*\.[0-9]+|[0-9]+\.[0-9]*'
    return t

def t_INTEGER(t): # added minus sign 20110902 for help with groupby: `line<-5,-6` was failing.
    r'[-]?[0-9]+'
    return t



def t_MATH(t):
   r'[\+\-\*\/]'
   return t

def t_COMPARATOR(t):
   r"!=|==|<=|>=|<|>|=|[\s]+is[\s]+not[\s]+|\bnot[\s]+in\b|[\s]+in[\s]+|[\s]+is[\s]+|\bnot[\s]+"
   t.type = reserved.get(t.value, 'COMPARATOR')
   t.value = t.value.strip()
   return t

# column flavors with tuple thrown in since it is parsed the same
def t_SQUARE_BRACKET(t):
    r"\["
    t.lexer.squarebracket_start = t.lexer.lexpos - len(t.value)
    t.lexer.sb_level = 1
    t.lexer.begin('squarebracket')

# Rules for the squarebracket state:
#  capture everything upto the next (unprotected) r_paren
def t_squarebracket_l_paren(t):
    r'\['
    t.lexer.sb_level +=1

def t_squarebracket_r_paren(t):
    r'\]'
    t.lexer.sb_level -=1

    # If closing paren, return the squarebracket with arguments
    if t.lexer.sb_level == 0:
         t.value = t.lexer.lexdata[t.lexer.squarebracket_start:t.lexer.lexpos]
         t.type = "SQUARE_BRACKET"
         t.lexer.begin('INITIAL')
         return t
#  string
def t_squarebracket_string(t):
   r'\"([^\\\n]|(\\.))*?\"'

#  character literal
def t_squarebracket_char(t):
   r'\'([^\\\n]|(\\.))*?\''

# Any sequence of characters (not braces, strings)
def t_squarebracket_characters(t):
   r'[^\[\]\'\"]+'


def t_DICT(t):
    r"\{"
    t.lexer.dict_start = t.lexer.lexpos - len(t.value)
    t.lexer.sb_level = 1
    t.lexer.begin('dict')


# Rules for the dict state:
#  capture everything upto the next (unprotected) r_paren
def t_dict_l_paren(t):
    r'\{'
    t.lexer.sb_level +=1

def t_dict_r_paren(t):
    r'\}'
    t.lexer.sb_level -=1

    # If closing paren, return the dict with arguments
    if t.lexer.sb_level == 0:
         t.value = t.lexer.lexdata[t.lexer.dict_start:t.lexer.lexpos]
         t.type = "DICT"
         t.lexer.begin('INITIAL')
         return t
#  string
def t_dict_string(t):
   r'\"([^\\\n]|(\\.))*?\"'

#  character literal
def t_dict_char(t):
   r'\'([^\\\n]|(\\.))*?\''

# Any sequence of characters (not curly braces, strings)
def t_dict_characters(t):
   r'[^\{\}\'\"]+'



def t_AGGREGATOR(t):
    r'[a-zA-Z_\.]*[\s]*\('    # 20110730: allowed space between function and `(` . e.g.:  `Sum (`
    t.lexer.aggregator_start = t.lexer.lexpos - len(t.value)
    t.lexer.ag_level = 1
    t.lexer.begin('aggregator')
#t_AGGREGATOR.__doc__ = '|'.join(map(lambda x:x+'\(',AGGREGATORS+['']))


# Rules for the aggregator state:
#  capture everything upto the next (unprotected) r_paren
def t_aggregator_l_paren(t):
    r'\('
    t.lexer.ag_level +=1

def t_aggregator_r_paren(t):
    r'\)'
    t.lexer.ag_level -=1

    # If closing paren, return the aggregator with arguments
    if t.lexer.ag_level == 0:
         t.value = t.lexer.lexdata[t.lexer.aggregator_start:t.lexer.lexpos]
         agg_name = string.split(t.value,'(')[0]
         if agg_name in AGGREGATORS: t.type = "AGGREGATOR"
         else: t.type = "PYTHON_FUNCTION"
         t.lexer.begin('INITIAL')
         return t

#  string
def t_aggregator_string(t):
   r'\"([^\\\n]|(\\.))*?\"'

#  character literal
def t_aggregator_char(t):
   r'\'([^\\\n]|(\\.))*?\''

# Any sequence of characters (not braces, strings)
def t_aggregator_characters(t):
   r'[^\(\)\'\"]+'

def t_STRING(t):
    r'(\'[^\']*\')|(\"[^\"]*\")'
    t.value = t.value.strip('"\'')
    return t


 # leave None, % and anything start with an underscore, or with a dot alone
def t_PYTHON_WORD(t):
    r'\bTrue\b|\bFalse\b|\bNone\b|%|_[a-zA-Z0-9_\.]+|[a-zA-Z]+[a-zA-Z0-9_]*\.[a-zA-Z0-9_\.]*[a-zA-Z0-9_]+|\bor\b'
    t.type = reserved.get(t.value, 'PYTHON_WORD')
    return t

def t_WORD(t): # don't allow a dot (allow at end?) here to distinguish python. E.g.:  math.e
    r'[a-zA-Z][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'WORD')
    return t

def t_SPACE(t):
    r'[\s]+'
    return t

lexer = lex.lex()
lexer.input(',1@()')
COMMA_TOK = lexer.token()
ONE_TOK = lexer.token()
AT_TOK = lexer.token()
L_PAREN_TOK = lexer.token()
R_PAREN_TOK = lexer.token()

# some problem with ply.lex when too many groups x headers
def test_lexer():
    pass


if __name__ == "__main__":

    #lexer.input("1*Average(weight)[age],Sum(age),(height,weight),str(age),self.custom(age)@age as Age and foo>4")
    lexer.input("age as Age,name or 'John Doe' as Name,height as Height@Sum(age) is None | $[1:]@$1<40")
    lexer.input("age @ (weight>100),(weight>150)")
    lexer.input("Bob Jones and parameter ''' and Bob Jones:p:parameter longer@age < -6, -7")

    while True:
        try:
            tok = lexer.token()
        except:
            print "error"
            break
        if not tok: break      # No more input
        print tok.type,
        print tok.value

    lexer.input("Bob Jones and parameter and Bob Jones:p:parameter longer@age < -6, -7")

    while True:
        tok = lexer.token()
        if not tok: break      # No more input
        print tok.type,
        print tok.value

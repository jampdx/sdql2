import ply.yacc as yacc
import ply.lex as lex
import dt_ply_lexer
from dt_ply_lexer import tokens

lexer = lex.lex(module=dt_ply_lexer,debug=0)

class PyQLError(Exception):
    """Raised when yacc has parsing failure.
    """
# top level query
class Query:
    fields = [] # [(text,type),...]
    condition_terms = [] # [[term],[list of terms],..]

query = Query()

def p_query(p):
    """query : fields '@' conditions
                   | fields  """  # the inside of summatives is also considered a query: Sum(points), Sum(points@H)
    if len(p) == 4: query.condition_terms = p[3]
    query.fields = p[1]
    p[0] = query

def p_field_term(p):
    """field : term
    """
    p[0] = p[1]

def p_fields_field(p):
    """fields : fields ',' field
    """
    p[0] = p[1] + [p[3]]

def p_fields(p):
    r'''fields : field
    '''
    p[0] = [p[1]]

def p_term_WITH_SQUARE_BRACKET(p):
    """term : term SQUARE_BRACKET
    """
    p[0] = p[1],(p[2],"SQUARE_BRACKET"),"WITH_SQUARE_BRACKET"


def p_term_AS(p):
    """term : term AS term
    """
    p[0] = p[1], (p[2],"AS") , p[3]

def p_term_MATH(p):
    """term : term MATH term
    """
    p[0] = ((p[1], (p[2],"MATH") , p[3]),'EXPRESSION')

def p_term_COMPARATOR(p):
    """term : term COMPARATOR term
    """
    p[0] = ((p[1], (p[2],"COMPARATOR") , p[3]),"COMPARISON")

def p_term_DICTIONARY(p):
    """term : DICTIONARY
    """
    p[0] = (p[1],"DICTIONARY")

def p_term_PARENTHESES(p):
    """term : PARENTHESES
    """
    p[0] = (p[1],"PARENTHESES")


def p_term_AGGRERGATOR(p):
    """term : AGGREGATOR
    """
    p[0] = (p[1],"AGGREGATOR")

def p_term_SQUARE_BRACKET(p): # inning runs + [0,0]
    """term : SQUARE_BRACKET
    """
    p[0] = (p[1],"SQUARE_BRACKET")

def p_term_PYTHON_FUNCTION(p):
    """term : PYTHON_FUNCTION
    """
    p[0] = (p[1],"PYTHON_FUNCTION")

def p_term_STRING(p):
    """term : STRING
    """
    p[0] = (p[1],"STRING")

def p_term_PARAMETER(p):
    """term : PARAMETER
    """
    p[0] = (p[1],"PARAMETER")

def p_term_WORD(p):
    """term : WORD
    """
    p[0] = (p[1],"WORD")

def p_term_INTEGER(p):
   """term : INTEGER
   """
   p[0] = (p[1],"INTEGER")

def p_term_FLOAT(p):
    """term : FLOAT
    """
    p[0] = (p[1],"FLOAT")

def p_term_PYTHON_DOT_FUNCTION(p):
    """term : term  PYTHON_DOT_FUNCTION """
    p[0] = (p[1], (p[2],"PYTHON_FUNCTION") ,"TERM_PYTHON_DOT_FUNCTION")


def p_conditions(p):
    """conditions : conditions CONJUNCTION condition
    """
    p[0] = p[1] + [[(p[2],'CONJUNCTION')]] + [p[3]]

def p_conditions_condition(p):
    r'''conditions : condition
    '''
    p[0] = [p[1]]

def p_condition_terms(p):
    """condition : terms
    """
    p[0] = p[1]


def p_terms_terms(p):
    r'''terms : terms ',' term    '''
    p[0] = p[1] + [p[3]]

def p_terms_term(p):
    r'''terms :  term    '''
    p[0] = [p[1]]


def p_error(p):
    raise PyQLError("Syntax Error near '%s'" % (p))



###########  tests #########
def test_lex(txt):
    print "input text:",txt
    print "gives these tokens:"
    lexer.input(txt)
    while True:
        tok = lexer.token()
        if not tok: break
        print tok
        #print tok.type, tok.value, tok.lineno, tok.lexpos


parser = yacc.yacc(debug=1)
print "built parser"

def test_ply(txt):
    result = parser.parse(txt,lexer=lexer,debug=1)
    print "text:",txt
    print "field items:"
    for item in result.fields:
        print item
    print "condition_terms:"
    for item in result.condition_terms:
        print item


def test_suite():
    text = " points>3,team @ team"
    test_ply(text)
    text = "points+4>6,hits-6+(points+4>30*2),Replace(team)[team],'foo'.upper() @ team,1"
    test_ply(text)
    text = "map(string.upper,map(lambda x:x[0],filter(lambda x:x[1]>'b',children)))[0:]@len(map(string.upper,map(lambda x:x[0],filter(lambda x,y='b':x[1]>y,children)[0:-1])))==1"
    test_ply(text)
    text = "age,','.join(children)@self.test((age,weight))==262"
    test_ply(text)

if __name__ == "__main__":
    test_suite()

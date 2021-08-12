import ply.yacc as yacc
import ply.lex as lex
import dt_lexer
from dt_lexer import tokens

lexer = lex.lex(module=dt_lexer,debug=0)

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
    """
    query.condition_terms = p[3]
    query.fields = p[1]
    p[0] = query

def p_fields_field(p):
    """fields : fields ',' field
    """
    p[0] = p[1] + [p[3]]

def p_fields(p):
    r'''fields : field'''
    p[0] = [p[1]]

def p_field_tuple(p):
    r"""field : '(' fields ')'"""
    p[0] = ([(p[1],'(')] + p[2] + [(p[3],')')],"TUPLE")

def p_field_as(p):
    """field : field AS field
    """
    p[0] = p[1], (p[2],"AS") , p[3]


def p_field_MATH(p):
    """field : field MATH field
    """
    p[0] = (p[1], (p[2],"MATH") , p[3],'EXPRESSION')

def p_field_COMPARATOR(p):
    """field : field COMPARATOR field
    """
    p[0] = (p[1], (p[2],"COMPARATOR") , p[3],"COMPARISON")

def p_field_AGGRERGATOR(p):
    """field : AGGREGATOR
    """
    p[0] = (p[1],"AGGREGATOR")

def p_field_STRING(p):
    """field : STRING
    """
    p[0] = (p[1],"STRING")

def p_field_PARAMETER(p):
    """field : PARAMETER
    """
    p[0] = (p[1],"PARAMETER")

def p_field_WORD(p):
    """field : WORD
    """
    p[0] = (p[1],"WORD")

def p_field_INTEGER(p):
   """field : INTEGER
   """
   p[0] = (p[1],"INTEGER")

def p_field_FLOAT(p):
    """field : FLOAT
    """
    p[0] = (p[1],"FLOAT")


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

def p_term_INTEGER(p):
    """term : INTEGER
    """
    p[0] = (p[1],"INTEGER")

def p_term_FLOAT(p):
    """term : FLOAT
    """
    p[0] = (p[1],"FLOAT")

def p_term_PARAMETER(p):
    """term : PARAMETER
    """
    p[0] = (p[1],"PARAMETER")



def p_term_WORD(p):
    """term : WORD
    """
    p[0] = (p[1],"WORD")


def p_term_MATH(p):
    """term : terms MATH terms
    """
    p[0] = (p[1], (p[2],"MATH") , p[3],'EXPRESSION')

def p_term_COMPARATOR(p):
    """term : terms COMPARATOR terms
    """
    p[0] = (p[1], [(p[2],"COMPARATOR")] , p[3],"COMPARISON")


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

def test_ply(txt):
    parser = yacc.yacc(debug=1)
    print "built parser"
    result = parser.parse(txt,lexer=lexer,debug=1)
    print "text:",txt
    print "fields:"
    for item in result.fields:
        print item
    print "condition_terms:"
    for item in result.condition_terms:
        print item


if __name__ == "__main__":

    #text = "points>8,Bob,Average(points),5+6/3@1,2,3<=hits,runs<4,5,6 and 20,15>walks>10 and team=Cubs,Reds"
    #text = "(70>60>points>30>20>10+10/22.>0),hits+(walks*balks),'bob,sally',(season,week)@team=Bears,Bills"
    text = "hits@team"
    test_lex(text)
    test_ply(text)

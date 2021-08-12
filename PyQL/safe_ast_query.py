"""

verify that something like this:

   db[5][index].upper() == 'BEARS' and db[12][index] * math.e > 50

contains only whitelisted constructs


"""

#SECRET_PREFIX = 'e4c1'
SECRET_PREFIX = '_'

OK_ATTRIBUTES = ('string', 'math', 'PyQL', 'self','re','random')
OK_SUBSCRIPTS = ('db',)
OK_NAMES = ('index', 'upper', 'lower', 'int', 'round','max', 'min', 'float', 'sum', 'list','xrange','izip',
            'None', 'True', 'False', 'zip', 'Cache_DT', 'DT', 'map','cmp','abs','sorted',
            'len', 'str', 'tuple', 'filter', 'self','abbreviate_month','abbreviate_year')
OK_FUNCS = ('_query')
import ast

def has_prefix(name):
    return name.startswith(SECRET_PREFIX)


def filter_node(node):
    t = type(node)

    # all of these are fine in themselves,
    # recursively check their contents

    if t == ast.Module:
        filter_node(node.body[0])

    elif t == ast.UnaryOp:
        filter_node(node.operand)

    elif t == ast.Expr:
        filter_node(node.value)

    elif t == ast.If:
        filter_node(node.test)
        [filter_node(n) for n in node.body]
        [filter_node(n) for n in node.orelse]

    elif t == ast.IfExp:
        filter_node(node.test)
        filter_node(node.body)
        filter_node(node.orelse)

    elif t == ast.Assign:
        for n in node.targets:
            if type(n) == ast.Name:
                if not has_prefix(n.id)         :
                    raise NameError(n.id)
            elif type(n) == ast.Subscript:
                pass # !!!
        filter_node(node.value)

    elif t == ast.AugAssign:
        filter_node(node.target)
        filter_node(node.value)

    elif t == ast.List or t == ast.Tuple:
        [filter_node(n) for n in node.elts]

    elif t == ast.Dict:
        [filter_node(n) for n in node.keys]
        [filter_node(n) for n in node.values]

    elif t == ast.TryExcept:
        [filter_node(n) for n in node.body]
        [filter_node(n) for n in node.handlers]
        [filter_node(n) for n in node.orelse]

    elif t == ast.ExceptHandler:
        filter_node(node.type)
        filter_node(node.name)
        [filter_node(n) for n in node.body]

    elif t == ast.BoolOp:
        # has an 'op' (we don't care) and 'values'
        [filter_node(n) for n in node.values]

    elif t == ast.FunctionDef:
        if node.name not in OK_FUNCS:
            print "safe_ast-qery.node.name:",node.name
            raise NameError
        [filter_node(n) for n in node.body]

    elif t == ast.BinOp:
        # left, op, right
        filter_node(node.left)
        filter_node(node.right)

    elif t == ast.Slice:
        # lower, upper, step
        filter_node(node.lower)
        filter_node(node.upper)
        filter_node(node.step)

    elif t == ast.Compare:
        #left, ops, comparators
        filter_node(node.left)
        [filter_node(n) for n in node.comparators]


    elif t in  [ast.Index,ast.Repr]:
        filter_node(node.value)

    # attributes, subscripts, and function calls are more complicated
    # check the left side against a whitelist

    elif t == ast.Attribute:
        # value.attr
        if type(node.value) == ast.Name:
            if node.value.id not in OK_ATTRIBUTES and not has_prefix(node.value.id):
                raise NameError(node.value.id)
        else:
            filter_node(node.value)

        filter_node(node.attr)


    elif t == ast.Subscript:
        # value[slice]
        if type(node.value) == ast.Subscript:
            # subscripts of subscripts...
            filter_node(node.value)
        elif type(node.value) == ast.Name:
            # check the name against the whitelist
            if node.value.id not in OK_SUBSCRIPTS \
                   and not has_prefix(node.value.id)                          :
                raise NameError(node.value.id)
        elif type(node.value) == ast.Attribute:
            filter_node(node.value.value)
            filter_node(node.value.attr)
        elif type(node.value) == ast.Dict:
            [filter_node(n) for n in node.value.keys]
            [filter_node(n) for n in node.value.values]

        elif type(node.value) == ast.Call:
            filter_node(node.value.func)
            [filter_node(n) for n in node.value.args]
            [filter_node(n) for n in node.value.keywords]
            filter_node(node.value.starargs)
            filter_node(node.value.kwargs)
        elif  type(node.value) == ast.BinOp:
            # left, op, righ
            filter_node(node.value.left)
            filter_node(node.value.right)
        else:
            #print "n.v",node.value
            # nothing else can be subscripted
            raise TypeError(node.value)

        filter_node(node.slice)


    elif t == ast.Call:
        # func, args, keywords, starargs, kwargs
        # if all subchecks are ok, it's ok to call
        filter_node(node.func)
        [filter_node(n) for n in node.args]
        [filter_node(n) for n in node.keywords]
        filter_node(node.starargs)
        filter_node(node.kwargs)

    elif t == ast.keyword:
        filter_node(node.arg)
        filter_node(node.value)

    elif t == ast.Lambda:
        # we want to be able to create and use our own arg names
        # but only for this one call.
        # manipulate the global OK_NAMES list and restore it
        # when we're done
        global OK_NAMES
        global OK_SUBSCRIPTS
        filter_node(node.args)

        old_names = OK_NAMES[:]
        old_subscripts = OK_SUBSCRIPTS[:]
        OK_NAMES += tuple([a.id for a in node.args.args])
        OK_SUBSCRIPTS += tuple([a.id for a in node.args.args])

        filter_node(node.body)

        OK_NAMES = old_names
        OK_SUBSCRIPTS = old_subscripts

    elif t == ast.arguments:
        #args, vararg, kwarg, defaults
        for n in node.args:
            if type(n) != ast.Name:
                raise TypeError(type(n))
        filter_node(node.vararg)
        filter_node(node.kwarg)
        [filter_node(n) for n in node.defaults]

    elif t == ast.For:
        # target, iter, body, orelse
        filter_node(node.target)
        filter_node(node.iter)
        [filter_node(n) for n in node.body]
        [filter_node(n) for n in node.orelse]

    elif t == ast.Name:
        # check the whitelist...
        if node.id not in OK_NAMES and not has_prefix(node.id):
            raise NameError(node.id)

    elif t == ast.Num or t == ast.Str or t == ast.Pass:
        # numbers and strings are safe
        pass

    elif t == str or t == type(None):
        # also safe
        pass

    else:
        # illegal construct
        raise TypeError(t)


def filter(query):
    node = ast.parse(query)
    filter_node(node)


if __name__ == '__main__':
    import sys
    filter("1 if 0 else 2")

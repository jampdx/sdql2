
from PyQL.py_tools import link

html = "<b>How to Query:</b>"
html += "<p>The basic SDQL syntax is: <em> fields @ conditions </em>.<p>"
html += "<em>fields</em> is a comma delimited list of one or more sql-like `select` terms."
html += "These can be built out of database parameters, constants, and python functions.<p>"

html += "<em>conditions</em> is a conjunction (`and` / `or`) delimited list of one or more sql-like `where` terms."
html += "As with fields, each condition can be built out of database parameters, constants, and python functions.<p>"
html += "The full SDQL query for average margin for each team is:"
html += link(page='query',sdql="A(margin) @ team")



if __name__ == "__main__":
    print html

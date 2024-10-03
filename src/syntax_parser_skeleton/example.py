from re import compile

from syntax_parser_skeleton import *
from syntax_parser_skeleton.derivatives import simpleregex
from syntax_parser_skeleton import visualisation

root = RootPhrase("#root")

_bracket = simpleregex.SimpleRegexPhrase(compile('\\('), compile('\\)'), id="bracket").add_self()
_funcall = simpleregex.SimpleRegexPhrase(compile('\\w+\\s*\\('), compile('\\)'), id="function")
_consoleline = simpleregex.SimpleRegexPhrase(compile('>>>'), compile('$'), id="consoleline").add_phrases(_funcall)
_variable = simpleregex.SimpleRegexPhrase(compile('\\w+(?!\\s*\\()'), compile(''), id="variable")
_operation = simpleregex.SimpleRegexPhrase(compile('[-+*/]'), compile(''), id="operation")
_curly_brackets = simpleregex.SimpleRegexPhrase(compile("\\{"), compile("}"), id="curly brackets")
_string = simpleregex.SimpleRegexPhrase(compile("'"), compile("'"), id="string").add_phrases(_curly_brackets)
_bracket.add_phrases(_variable, _operation, _string, _funcall)
root.add_phrases(_bracket, _variable, _operation, _string, _consoleline)
_consoleline.add_phrases(root.sub_phrases)
_consoleline.sub_phrases.discard(_consoleline)
_funcall.add_phrases(root.sub_phrases)
result = root.parse([
    ">>> prettyprint('( (a * b / (c + a)) * (b / (c – a) * b) / c ) + a')\n",
    "(\n",
    "   (\n",
    "       a * b / (c + a)\n",
    "   ) * (\n",
    "       b / (c – a) * b\n",
    "   ) / c \n",
    ") + a",
])

print(visualisation.pretty_xml_result(result))
visualisation.start_structure_graph_app(root)


Concept
#######

Objects
=======

=============================== =========================
``Phrase``                      Used to define the structure of the syntax tree.
``Token``                       Result value of the parsing process; container for text content and metadata.
``NodeToken`` (Token)           Derivative of ``Token`` for the typing of ``NodeToken``\ s. Always located at the first and last position of a ``Branch``.
``Branch`` (Token)              Result value of the parsing process; container for ``Token``\ s, ``NodeToken``\ s and sub-``Branch``\ es.
``Root`` (Phrase)               Derivative of ``Phrase`` as root object. User-defined ``Phrase``\ s are added here and contains the parse method.
``RootBranch`` (Branch)         Derivative of ``Branch`` as the main container. Is returned by Root.parse.
``RootToken`` (Token)           Derivative of ``Token`` for the main container.
``RootNodeToken`` (NodeToken)   Derivative of ``NodeToken``. Represents the start resp. the end of the parsed data.
=============================== =========================

Configuration and syntax tree definition
========================================

The ``Phrase`` derivatives are used to define the syntax tree.

    In theories of syntax, a ``Phrase`` is any group of words, or sometimes a single word, 
    which plays a particular role within the syntactic structure of a sentence.

Sub-\ ``Phrase``\ s are added to these. The end of a ``Phrase`` is defined by a derivative of ``Branch``.

The minimum configuration consists of overwriting the ``starts`` method in a derivative of ``Phrase``,
which in turn returns a derivative of ``Branch`` - with an override of the ``ends`` method 
corresponding to this derivative of ``Phrase``.

    ``Phrase.starts() → Branch.ends()``


Parsing process
===============

=========   ================================
Input:       A list of rows (``list[str]``)
Output:      ``RootBranch`` object
=========   ================================

In the iteration, (the remaining part of) a row is first searched for start-``NodeToken``\ s of sub-``Phrase``\ s
of the current ``Phrase``, then for the end-``NodeToken`` of the current ``Branch``.
A start-``NodeToken`` is defined by the return value of the ``starts`` method of a sub-``Phrase``. An end-``NodeToken``
is defined by the return value of the ``ends`` method of the current ``Branch``.

        Depending on the type of search function definition in ``starts`` and the scope of a row, it can be
        efficient to search for further start points or end points after a start-``NodeToken`` hit only in the previous
        content of this hit. The ``next_search_content`` method of ``Branch`` can be defined in more detail for
        this purpose. The hit instance is executed with the current content of the row in which the search is
        currently being performed as a parameter and should return the remaining content in which the search is
        to continue. By default, the content remains unchanged.

    The return value of ``starts`` of a ``Phrase`` must be an instance of ``Branch`` for a hit. The start-``NodeToken``
    within the object is created based on its parameterization. To use a derivative of ``NodeToken``/``Token`` for this, 
    the ``make_node`` method of a ``Branch`` derivative can be overwritten.

    The return value of ``ends`` of a ``Branch`` must be an instance of ``NodeToken``/``Token`` for a hit.


The magic method “less than” (``__lt__``) of the ``NodeToken`` object is used to determine which ``NodeToken`` appears first
in the row and is handled further. The relative start is used here by default.

After the ``NodeToken`` to be processed further has been determined, the previous content of the row is first added
to the currently active ``Branch`` as a ``Token`` object.
The ``call_branch_extend`` interface method of the ``Token`` instance is executed.

To use a ``Token`` derivative for this, the ``make_token`` method of a ``Branch`` derivative can be overwritten.

If it is an end-``NodeToken``, this is added to the active ``Branch`` and the previous ``Branch`` is then defined as the
new active ``Branch``. The ``call_branch_end`` interface method of the end-``NodeToken`` instance is executed.

If it is a start-``NodeToken``, its ``Branch`` is defined as the new active ``Branch`` and the start-``NodeToken`` is added to it.
The interface method ``call_branch_start`` of the start-``NodeToken`` instance is executed.

If no ``NodeToken`` is found, the current ``Branch`` is extended with a ``Token`` object as described above.

Finally, the remaining part of the row or the next row is passed to the next iteration.

Example
=======

.. code-block::
    python

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


.. code-block::
    python

    visualisation.start_structure_graph_app(root)

.. image:: https://raw.githubusercontent.com/srccircumflex/syntax-parser-skeleton/master/doc/graph.png
    :align: center

.. code-block::
    python

    print(visualisation.pretty_xml_result(result))

.. code-block::
    xml

    <?xml version="1.0" ?>
    <RB phrase="#root">
        <RN coord="0:0:0/0:0">''</RN>
        <B phrase="consoleline">
            <N coord="0:0:3/0:3">'&gt;&gt;&gt;'</N>
            <T coord="0:3:4/3:4">' '</T>
            <B phrase="function">
                <N coord="0:4:16/4:16">'prettyprint('</N>
                <B phrase="string">
                    <N coord="0:16:17/16:17">&quot;'&quot;</N>
                    <T coord="0:17:66/17:66">'( (a * b / (c + a)) * (b / (c – a) * b) / c ) + a'</T>
                    <N coord="0:66:67/66:67">&quot;'&quot;</N>
                </B>
                <N coord="0:67:68/67:68">')'</N>
            </B>
            <N coord="0:68:68/68:68">''</N>
        </B>
        <RT coord="0:68:69/68:69">'\n'</RT>
        <B phrase="bracket">
            <N coord="1:0:1/69:70">'('</N>
            <T coord="1:1:2/70:71">'\n'</T>
            <T coord="2:0:3/71:74">'   '</T>
            <B phrase="bracket">
                <N coord="2:3:4/74:75">'('</N>
                <T coord="2:4:5/75:76">'\n'</T>
                <T coord="3:0:7/76:83">'       '</T>
                <B phrase="variable">
                    <N coord="3:7:8/83:84">'a'</N>
                    <N coord="3:8:8/84:84">''</N>
                </B>
                <T coord="3:8:9/84:85">' '</T>
                <B phrase="operation">
                    <N coord="3:9:10/85:86">'*'</N>
                    <N coord="3:10:10/86:86">''</N>
                </B>
                <T coord="3:10:11/86:87">' '</T>
                <B phrase="variable">
                    <N coord="3:11:12/87:88">'b'</N>
                    <N coord="3:12:12/88:88">''</N>
                </B>
                <T coord="3:12:13/88:89">' '</T>
                <B phrase="operation">
                    <N coord="3:13:14/89:90">'/'</N>
                    <N coord="3:14:14/90:90">''</N>
                </B>
                <T coord="3:14:15/90:91">' '</T>
                <B phrase="bracket">
                    <N coord="3:15:16/91:92">'('</N>
                    <B phrase="variable">
                        <N coord="3:16:17/92:93">'c'</N>
                        <N coord="3:17:17/93:93">''</N>
                    </B>
                    <T coord="3:17:18/93:94">' '</T>
                    <B phrase="operation">
                        <N coord="3:18:19/94:95">'+'</N>
                        <N coord="3:19:19/95:95">''</N>
                    </B>
                    <T coord="3:19:20/95:96">' '</T>
                    <B phrase="variable">
                        <N coord="3:20:21/96:97">'a'</N>
                        <N coord="3:21:21/97:97">''</N>
                    </B>
                    <N coord="3:21:22/97:98">')'</N>
                </B>
                <T coord="3:22:23/98:99">'\n'</T>
                <T coord="4:0:3/99:102">'   '</T>
                <N coord="4:3:4/102:103">')'</N>
            </B>
            <T coord="4:4:5/103:104">' '</T>
            <B phrase="operation">
                <N coord="4:5:6/104:105">'*'</N>
                <N coord="4:6:6/105:105">''</N>
            </B>
            <T coord="4:6:7/105:106">' '</T>
            <B phrase="bracket">
                <N coord="4:7:8/106:107">'('</N>
                <T coord="4:8:9/107:108">'\n'</T>
                <T coord="5:0:7/108:115">'       '</T>
                <B phrase="variable">
                    <N coord="5:7:8/115:116">'b'</N>
                    <N coord="5:8:8/116:116">''</N>
                </B>
                <T coord="5:8:9/116:117">' '</T>
                <B phrase="operation">
                    <N coord="5:9:10/117:118">'/'</N>
                    <N coord="5:10:10/118:118">''</N>
                </B>
                <T coord="5:10:11/118:119">' '</T>
                <B phrase="bracket">
                    <N coord="5:11:12/119:120">'('</N>
                    <B phrase="variable">
                        <N coord="5:12:13/120:121">'c'</N>
                        <N coord="5:13:13/121:121">''</N>
                    </B>
                    <T coord="5:13:16/121:124">' – '</T>
                    <B phrase="variable">
                        <N coord="5:16:17/124:125">'a'</N>
                        <N coord="5:17:17/125:125">''</N>
                    </B>
                    <N coord="5:17:18/125:126">')'</N>
                </B>
                <T coord="5:18:19/126:127">' '</T>
                <B phrase="operation">
                    <N coord="5:19:20/127:128">'*'</N>
                    <N coord="5:20:20/128:128">''</N>
                </B>
                <T coord="5:20:21/128:129">' '</T>
                <B phrase="variable">
                    <N coord="5:21:22/129:130">'b'</N>
                    <N coord="5:22:22/130:130">''</N>
                </B>
                <T coord="5:22:23/130:131">'\n'</T>
                <T coord="6:0:3/131:134">'   '</T>
                <N coord="6:3:4/134:135">')'</N>
            </B>
            <T coord="6:4:5/135:136">' '</T>
            <B phrase="operation">
                <N coord="6:5:6/136:137">'/'</N>
                <N coord="6:6:6/137:137">''</N>
            </B>
            <T coord="6:6:7/137:138">' '</T>
            <B phrase="variable">
                <N coord="6:7:8/138:139">'c'</N>
                <N coord="6:8:8/139:139">''</N>
            </B>
            <T coord="6:8:10/139:141">' \n'</T>
            <N coord="7:0:1/141:142">')'</N>
        </B>
        <RT coord="7:1:2/142:143">' '</RT>
        <B phrase="operation">
            <N coord="7:2:3/143:144">'+'</N>
            <N coord="7:3:3/144:144">''</N>
        </B>
        <RT coord="7:3:4/144:145">' '</RT>
        <B phrase="variable">
            <N coord="7:4:5/145:146">'a'</N>
        </B>
        <RN coord="7:5:5/146:146">''</RN>
    </RB>
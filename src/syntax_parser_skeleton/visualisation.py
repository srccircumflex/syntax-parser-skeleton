from syntax_parser_skeleton import RootPhrase, Branch


def pretty_xml_result(branch: Branch) -> str:
    import xml.dom.minidom
    return xml.dom.minidom.parseString(repr(branch)).toprettyxml()


def start_structure_graph_app(root: RootPhrase):
    from dash import Dash, html
    import dash_cytoscape as cyto

    touched = {root}
    elements = [{'data': {'id': root.id, 'label': root.id}, "classes": "red"}]

    def f(phrase):
        if phrase not in touched:
            touched.add(phrase)
            p_id = f'{phrase.id}'
            elements.append({'data': {'id': p_id, 'label': p_id}})
            for sub_phrase in phrase.sub_phrases:
                sp_id = f'{sub_phrase.id}'
                elements.append({'data': {'id': f"{p_id}\u2007{sp_id}", 'source': p_id, 'target': sp_id}, "classes": "dir"})
                f(sub_phrase)

    for p in root.sub_phrases:
        sp_id = f'{p.id}'
        elements.append({'data': {"id": f"{root.id}\u2007{sp_id}", 'source': root.id, 'target': sp_id}, "classes": "dir"})
        f(p)

    app = Dash(__name__)

    app.layout = html.Div([
        cyto.Cytoscape(
            layout={'name': 'circle'},
            style={'width': '100%', 'height': '100%'},
            elements=elements,
            stylesheet=[
                {
                    'selector': 'node',
                    'style': {
                        'content': 'data(label)'
                    }
                },
                {
                    'selector': 'edge',
                    'style': {
                        # The default curve style does not work with certain arrows
                        'curve-style': 'bezier'
                    }
                },
                {
                    'selector': '.red',
                    'style': {
                        'background-color': 'red',
                    }
                },
                {
                    'selector': '.dir',
                    'style': {
                        'target-arrow-shape': 'triangle',
                        'target-arrow-color': 'blue',
                    }
                },
            ]
        )
    ], style={"position": "absolute", "top": 0, "bottom": 0, "left": 0, "right": 0})
    app.run(debug=True)



from dash import Dash, html, dcc

import slack_track2 as st2



app = Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Attrition by Org/Week'),

    html.Div(children='''
        Breakdown of attrition by org of user and week of departure.
    '''),

    dcc.Graph(
        id='example-graph',
        figure=st2.weekly_and_org()
    )
])

if __name__ == '__main__':
    app.run_server("0.0.0.0", debug=True)
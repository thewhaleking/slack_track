from dash import Dash, html, dcc
from flask import redirect

import slack_track2 as st2

st2.get_new_data()
app = Dash(__name__)

app.layout = html.Div(
    children=[
        html.H1(children='Attrition by Org/Week'),

        html.Div(children='Breakdown of attrition by org of user and week of departure.'),

        dcc.Graph(
            id='example-graph',
            figure=st2.weekly_and_org()
        ),

        html.Div(children="By org"),
        dcc.Graph(
            id="org",
            figure=st2.org_d()
        ),

        html.Div(children="By week"),
        dcc.Graph(
            id="week",
            figure=st2.weekly_d()
        )
    ]
)


@app.server.get("/refresh_data")
def refresh_data():
    print("Data refreshed.")
    st2.get_new_data()
    return redirect("/")


if __name__ == '__main__':
    app.run_server("0.0.0.0", debug=True)

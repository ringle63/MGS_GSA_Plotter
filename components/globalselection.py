from dash import html, dcc


def create_globalselection(
        gsa_count,
        mmes_count,
        matched_count,
        analysis_methods,
        formations,
        boreholes,
):
    return html.Div(
        [
            html.H3("Global Selection"),

            html.P(f"GSA Samples: {gsa_count}"),
            html.P(f"MMES Samples: {mmes_count}"),
            html.P(f"Matched Samples: {matched_count}"),

            html.Hr(),

            html.Label("Analysis Method"),
            dcc.Dropdown(
                id="global-analysis-method",
                options=[
                    {"label": x, "value": x}
                    for x in analysis_methods
                ],
                multi=True,
                placeholder="All",
            ),

            html.Br(),

            html.Label("Formation"),
            dcc.Dropdown(
                id="global-formation",
                options=[
                    {"label": x, "value": x}
                    for x in formations
                ],
                multi=True,
                placeholder="All",
            ),

            html.Br(),

            html.Label("Borehole"),
            dcc.Dropdown(
                id="global-borehole",
                options=[
                    {"label": x, "value": x}
                    for x in boreholes
                ],
                multi=True,
                placeholder="All",
            ),

            html.Br(),

            html.Label("Samples"),
            dcc.Dropdown(
                id="global-samples",
                options=[],
                value=[],
                multi=True,
                placeholder="Select samples...",
                closeOnSelect=False,
            ),

            html.Br(),

            html.Button(
                "Select All Filtered",
                id="select-all-filtered",
                n_clicks=0,
            ),

            html.Button(
                "Clear Selection",
                id="clear-selection",
                n_clicks=0,
                style={"marginLeft": "10px"},
            ),

            html.Br(),
            html.Br(),

            html.Div(
                "Selected Samples: 0",
                id="selected-count",
            ),
        ],
        style={
            "width": "380px",
            "flexShrink": 0,
            "padding": "20px",
            "borderRight": "1px solid lightgray",
        },
    )

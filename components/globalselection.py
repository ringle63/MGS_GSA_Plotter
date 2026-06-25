from dash import html, dcc


def create_globalselection(
        gsa_count,
        mmes_count,
        matched_count,
        analysis_methods,
        formations,
        boreholes,
        filter_options,
):
    return html.Div(
        [
            html.H3("Global Selection"),

            html.P(f"GSA Samples: {gsa_count}"),
            html.P(f"MMES Samples: {mmes_count}"),
            html.P(f"Matched Samples: {matched_count}"),

            html.Hr(),

            html.H4("Query Builder"),

            html.Label("Field"),

            dcc.Dropdown(
                id="global-filter-field",
                options=[],
                placeholder="Field",
            ),

            html.Br(),

            html.Label("Operator"),

            dcc.Dropdown(
                id="global-filter-operator",
                options=[
                    {
                        "label": "IN",
                        "value": "IN",
                    },
                    {
                        "label": "NOT IN",
                        "value": "NOT IN",
                    },
                    {
                        "label": "Contains Text",
                        "value": "CONTAINS",
                    },
                ],
                value="IN",
                clearable=False,
            ),

            html.Br(),

            html.Label("Value"),

            html.Div(
                [

                    dcc.Dropdown(
                        id="global-filter-dropdown",
                        options=[],
                        multi=True,
                    ),

                    dcc.Input(
                        id="global-filter-text",
                        type="text",
                        placeholder="Enter text...",
                        style={
                            "width": "100%",
                            "display": "none",
                        },
                    ),

                    dcc.Input(
                        id="global-filter-number",
                        type="number",
                        placeholder="Value",
                        style={
                            "width": "100%",
                            "display": "none",
                        },
                    ),

                    html.Div(
                        [

                            dcc.Input(
                                id="global-filter-min",
                                type="number",
                                placeholder="Minimum",
                                style={
                                    "width": "48%",
                                },
                            ),

                            dcc.Input(
                                id="global-filter-max",
                                type="number",
                                placeholder="Maximum",
                                style={
                                    "width": "48%",
                                },
                            ),

                        ],
                        id="global-filter-between",
                        style={
                            "display": "none",
                            "justifyContent": "space-between",
                        },
                    ),

                ]
            ),

            html.Br(),

            html.Button(
                "Add Clause",
                id="add-global-filter",
                n_clicks=0,
            ),

            html.Br(),
            html.Br(),

            html.Button(
                "Apply Filter",
                id="apply-global-filter",
                n_clicks=0,
            ),

            html.Button(
                "Clear Filter",

                id="clear-global-filter",
                n_clicks=0,
                style={
                    "marginLeft": "10px",
                },
            ),

            html.Div(
                id="global-filter-list",
                style={
                    "marginTop": "10px",
                    "marginBottom": "10px",
                },
            ),

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

from dash import html, dcc


def create_panel(
        panel,
        display_number,
        analysis_method_options,
        formation_options,
        borehole_options,
        sample_options,
):
    graph_style = {
        "display": "flex",
        "flexDirection": "column",
        "minHeight": 0,
    }

    if panel["chart_type"] != "Grain Size Log":
        graph_style.update({
            "flex": "1",
            "height": "100%",
        })

    graph = html.Div(
        id={
            "type": "panel-content",
            "index": panel["id"],
        },
        style=graph_style,
    )

    if panel["chart_type"] == "Grain Size Log":
        graph = html.Div(
            graph,
            style={
                "height": "100%",
                "flex": "1 1 auto",
                "overflowY": "auto",
                "minHeight": 0,
            },
        )

    grain_log_header = None

    if panel["chart_type"] == "Grain Size Log":
        grain_log_header = html.Div(
            [

                html.Span(
                    "Gravel",
                    style={
                        "backgroundColor": "#5b0000",
                        "padding": "2px 6px",
                        "border": "1px solid black",
                    },
                ),

                html.Span(
                    "Very Coarse Sand",
                    style={
                        "backgroundColor": "#8b0000",
                        "padding": "2px 6px",
                        "border": "1px solid black",
                    },
                ),

                html.Span(
                    "Coarse Sand",
                    style={
                        "backgroundColor": "#cc5500",
                        "padding": "2px 6px",
                        "border": "1px solid black",
                    },
                ),

                html.Span(
                    "Medium Sand",
                    style={
                        "backgroundColor": "#ffb000",
                        "padding": "2px 6px",
                        "border": "1px solid black",
                    },
                ),

                html.Span(
                    "Fine Sand",
                    style={
                        "backgroundColor": "#ffff00",
                        "padding": "2px 6px",
                        "border": "1px solid black",
                    },
                ),

                html.Span(
                    "Very Fine Sand",
                    style={
                        "backgroundColor": "#ffff99",
                        "padding": "2px 6px",
                        "border": "1px solid black",
                    },
                ),

                html.Span(
                    "Silt",
                    style={
                        "backgroundColor": "#b2f0f0",
                        "padding": "2px 6px",
                        "border": "1px solid black",
                    },
                ),

                html.Span(
                    "Clay",
                    style={
                        "backgroundColor": "#0000ff",
                        "color": "white",
                        "padding": "2px 6px",
                        "border": "1px solid black",
                    },
                ),

            ],
            style={
                "display": "flex",
                "justifyContent": "center",
                "gap": "6px",
                "marginBottom": "10px",
                "flexWrap": "wrap",
            },
        )

    return html.Div(
        [
            html.Div(
                [
                    html.Button(
                        f"Panel {display_number}",
                        style={
                            "display": "inline-block",
                            "fontSize": "1.4em",
                            "fontWeight": "bold",
                            "border": "none",
                            "background": "none",
                            "padding": 0,
                            "cursor": "pointer",
                        },
                    ),

                    html.Button(
                        "⬇CSV",
                        id={
                            "type": "export-csv",
                            "index": panel["id"],
                        },
                        n_clicks=0,
                        style={
                            "float": "right",
                            "marginLeft": "5px",
                        },
                    ),

                    html.Button(
                        "📋",
                        id={
                            "type": "duplicate-panel",
                            "index": panel["id"],
                        },
                        n_clicks=0,
                        style={
                            "float": "right",
                            "marginLeft": "5px",
                        },
                    ),

                    html.Button(
                        "🗑",
                        id={
                            "type": "remove-panel",
                            "index": panel["id"],
                        },
                        n_clicks=0,
                        style={"float": "right"},
                    ),
                ]
            ),

            html.Div(
                [

                    html.Button(
                        (
                            "▼ Panel Controls"
                            if panel["controls_open"]
                            else "▶ Panel Controls"
                        ),
                        id={
                            "type": "toggle-controls",
                            "index": panel["id"],
                        },
                        n_clicks=0,
                        style={
                            "marginTop": "10px",
                            "marginBottom": "10px",
                            "width": "100%",
                            "textAlign": "left",
                        },
                    ),

                    html.Div(
                        [

                            html.Label("Chart Type"),

                            dcc.Dropdown(
                                id={
                                    "type": "chart-type",
                                    "index": panel["id"],
                                },
                                options=[
                                    "PSD Undersize",
                                    "PSD Frequency",
                                    "Ternary",
                                    "Grain Size Log",
                                    "Sample Information",
                                ],
                                value=panel["chart_type"],
                                clearable=False,
                            ),

                            html.Br(),

                            html.Button(
                                (
                                    "▼ Graph Options"
                                    if panel["graph_options_open"]
                                    else "▶ Graph Options"
                                ),
                                id={
                                    "type": "toggle-graph-options",
                                    "index": panel["id"],
                                },
                                n_clicks=0,
                                style={
                                    "marginTop": "10px",
                                    "marginBottom": "10px",
                                    "width": "100%",
                                    "textAlign": "left",
                                },
                            ),

                            # PSD-specific controls
                            html.Div(
                                [
                                    dcc.Checklist(
                                        id={
                                            "type": "show-legend",
                                            "index": panel["id"],
                                        },
                                        options=[{
                                            "label": "Show Legend",
                                            "value": "legend",
                                        }],
                                        value=["legend"] if panel["show_legend"] else [],
                                    ),

                                    dcc.Checklist(
                                        id={
                                            "type": "show-labels",
                                            "index": panel["id"],
                                        },
                                        options=[{
                                            "label": "Show Sample Labels",
                                            "value": "labels",
                                        }],
                                        value=["labels"] if panel["show_labels"] else [],
                                    ),

                                    html.Label("X Axis"),

                                    dcc.RadioItems(
                                        id={
                                            "type": "x-axis",
                                            "index": panel["id"],
                                        },
                                        options=[
                                            {"label": "Log", "value": "log"},
                                            {"label": "Linear", "value": "linear"},
                                            {"label": "Phi", "value": "phi"},
                                        ],
                                        value=panel["x_axis"],
                                        inline=True,
                                    ),

                                    html.Label("Reference Breaks"),

                                    dcc.Checklist(
                                        id={
                                            "type": "reference-breaks",
                                            "index": panel["id"],
                                        },
                                        options=[
                                            {"label": "8 µm", "value": "8"},
                                            {"label": "62.5 µm", "value": "62.5"},
                                        ],
                                        value=[
                                            x for x in [
                                                "8" if panel["show_break_8"] else None,
                                                "62.5" if panel["show_break_62_5"] else None,
                                            ]
                                            if x is not None
                                        ],
                                    ),
                                ],
                                style={
                                    "display": (
                                        "block"
                                        if (
                                                panel["chart_type"] in [
                                            "PSD Undersize",
                                            "PSD Frequency",
                                            "Ternary",
                                            "Grain Size Log",
                                        ]
                                                and panel.get("graph_options_open", True)
                                        )
                                        else "none"
                                    )
                                },
                            ),

                            html.Div(
                                [
                                    html.Label("Mastersizer Break"),

                                    dcc.RadioItems(
                                        id={
                                            "type": "mastersizer-break",
                                            "index": panel["id"],
                                        },
                                        options=[
                                            {"label": "2 µm", "value": 2},
                                            {"label": "4 µm", "value": 4},
                                            {"label": "8 µm", "value": 8},
                                        ],
                                        value=panel["mastersizer_break"],
                                        inline=True,
                                    ),

                                    html.Br(),

                                    html.Label("Pipette Break"),

                                    dcc.RadioItems(
                                        id={
                                            "type": "pipette-break",
                                            "index": panel["id"],
                                        },
                                        options=[
                                            {"label": "2 µm", "value": 2},
                                            {"label": "4 µm", "value": 4},
                                        ],
                                        value=panel["pipette_break"],
                                        inline=True,
                                    ),

                                    html.Br(),

                                    html.P(
                                        "Kehew: Fixed 4 µm"
                                    ),

                                    html.P(
                                        "Dry Sieve: Clay = 0, Silt = Fines_0_63"
                                    ),
                                    dcc.Checklist(
                                        id={
                                            "type": "show-usda",
                                            "index": panel["id"],
                                        },
                                        options=[
                                            {
                                                "label": "Show USDA Classes",
                                                "value": "usda",
                                            }
                                        ],
                                        value=(
                                            ["usda"]
                                            if panel["show_usda_triangle"]
                                            else []
                                        ),
                                    ),
                                ],
                                style={
                                    "display": (
                                        "block"
                                        if panel["chart_type"] in [
                                            "Ternary",
                                            "Grain Size Log",
                                        ]
                                        else "none"
                                    )
                                },
                            ),

                            html.Br(),

                            dcc.Checklist(
                                id={
                                    "type": "use-global",
                                    "index": panel["id"],
                                },
                                options=[
                                    {
                                        "label": "Use Global Selection",
                                        "value": "global",
                                    }
                                ],
                                value=["global"] if panel["use_global"] else [],
                            ),

                            html.Button(
                                (
                                    "▼ Override Selection"
                                    if panel["override_options_open"]
                                    else "▶ Override Selection"
                                ),
                                id={
                                    "type": "toggle-override-options",
                                    "index": panel["id"],
                                },
                                n_clicks=0,
                                style={
                                    "marginTop": "10px",
                                    "marginBottom": "10px",
                                    "width": "100%",
                                    "textAlign": "left",
                                },
                            ),

                            html.Div(
                                [
                                    html.Hr(),

                                    html.Label("Analysis Method"),

                                    dcc.Dropdown(
                                        id={
                                            "type": "override-methods",
                                            "index": panel["id"],
                                        },
                                        options=analysis_method_options,
                                        value=panel["override_methods"],
                                        multi=True,
                                    ),

                                    html.Br(),

                                    html.Label("Formation"),

                                    dcc.Dropdown(
                                        id={
                                            "type": "override-formations",
                                            "index": panel["id"],
                                        },
                                        options=formation_options,
                                        value=panel["override_formations"],
                                        multi=True,
                                    ),

                                    html.Br(),

                                    html.Label("Borehole"),

                                    dcc.Dropdown(
                                        id={
                                            "type": "override-boreholes",
                                            "index": panel["id"],
                                        },
                                        options=borehole_options,
                                        value=panel["override_boreholes"],
                                        multi=True,
                                    ),

                                    html.Br(),

                                    html.Label("Sample"),

                                    dcc.Dropdown(
                                        id={
                                            "type": "override-samples",
                                            "index": panel["id"],
                                        },
                                        options=sample_options,
                                        value=panel["override_samples"],
                                        multi=True,
                                    ),
                                ],
                                style={
                                    "display": (
                                        "block"
                                        if (
                                                not panel["use_global"]
                                                and panel.get("override_options_open", False)
                                        )
                                        else "none"
                                    )
                                },
                            ),

                            dcc.Download(
                                id={
                                    "type": "csv-download",
                                    "index": panel["id"],
                                },
                            ),

                        ],
                        style={
                            "display": (
                                "block"
                                if panel.get("controls_open", True)
                                else "none"
                            )
                        },
                    ),

                    # graph goes here
                    grain_log_header,

                    graph,

                ],
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "flex": "1 1 auto",
                    "minHeight": 0,
                },
            ),

        ],

        style={
            "border": "1px solid lightgray",
            "padding": "20px",
            "marginBottom": "20px",
            "height": "100%",
            "display": "flex",
            "flexDirection": "column",
            "minHeight": 0,
        }
    )

from dash import html, dcc

from logic.filters import (
    GROUP_BY_FIELDS,
    NUMERIC_FIELDS,
)


def create_panel(
        panel,
        display_number,
        group_by_options,
):
    panel.setdefault(
        "use_custom_groups",
        False,
    )

    panel.setdefault(
        "custom_groups",
        []
    )

    for group in panel["custom_groups"]:
        group.setdefault(
            "filters",
            []
        )

        group.setdefault(
            "pending_filters",
            []
        )

    panel.setdefault(
        "pending_custom_groups",
        []
    )

    panel.setdefault(
        "custom_group_builder_open",
        False
    )

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

    chart_type = panel["chart_type"]

    is_psd = chart_type in [
        "PSD Undersize",
        "PSD Frequency",
    ]

    is_ternary = (
            chart_type == "Ternary"
    )

    is_grain_log = (
            chart_type == "Grain Size Log"
    )

    supports_grouping = (
            is_psd
            or is_ternary
            or is_grain_log
    )

    supports_grain_breaks = (
            is_ternary
            or is_grain_log
    )

    supports_sample_display = (
            is_psd
            or is_ternary
    )

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
                                    html.Div(
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
                                        style={
                                            "display": (
                                                "block"
                                                if supports_sample_display
                                                else "none"
                                            )
                                        },
                                    ),

                                    html.Div(
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
                                        style={
                                            "display": (
                                                "block"
                                                if supports_sample_display
                                                else "none"
                                            )
                                        },
                                    ),

                                    html.Div(
                                        dcc.Checklist(
                                            id={
                                                "type": "show-samples",
                                                "index": panel["id"],
                                            },
                                            options=[{
                                                "label": "Show Samples",
                                                "value": "samples",
                                            }],
                                            value=(
                                                ["samples"]
                                                if panel.get(
                                                    "show_samples",
                                                    True,
                                                )
                                                else []
                                            ),
                                        ),
                                        style={
                                            "display": (
                                                "block"
                                                if supports_sample_display
                                                else "none"
                                            )
                                        },
                                    ),

                                    html.Div(
                                        dcc.Checklist(
                                            id={
                                                "type": "show-mean",
                                                "index": panel["id"],
                                            },
                                            options=[{
                                                "label": "Show Mean",
                                                "value": "mean",
                                            }],
                                            value=(
                                                ["mean"]
                                                if panel.get(
                                                    "show_mean",
                                                    False,
                                                )
                                                else []
                                            ),
                                        ),
                                        style={
                                            "display": (
                                                "block"
                                                if panel["chart_type"] in [
                                                    "PSD Undersize",
                                                    "PSD Frequency",
                                                ]
                                                else "none"
                                            )
                                        },
                                    ),

                                    html.Div(
                                        dcc.Checklist(
                                            id={
                                                "type": "show-grainlog-mean",
                                                "index": panel["id"],
                                            },
                                            options=[{
                                                "label": "Show Mean",
                                                "value": "mean",
                                            }],
                                            value=(
                                                ["mean"]
                                                if panel.get(
                                                    "show_grainlog_mean",
                                                    False,
                                                )
                                                else []
                                            ),
                                        ),
                                        style={
                                            "display": (
                                                "block"
                                                if is_grain_log
                                                else "none"
                                            )
                                        },
                                    ),

                                    html.Div(
                                        [
                                            html.Label("Sort By"),

                                            dcc.Dropdown(
                                                id={
                                                    "type": "grainlog-sort-field",
                                                    "index": panel["id"],
                                                },
                                                options=[
                                                            {
                                                                "label": "None",
                                                                "value": "None",
                                                            }
                                                        ]
                                                        + [
                                                            {
                                                                "label": label,
                                                                "value": field,
                                                            }
                                                            for field, label
                                                            in NUMERIC_FIELDS.items()
                                                        ],
                                                value=panel.get(
                                                    "grainlog_sort_field",
                                                    "None",
                                                ),
                                                clearable=False,
                                            ),
                                        ],
                                        style={
                                            "display":
                                                "block"
                                                if is_grain_log
                                                else "none"
                                        },
                                    ),

                                    html.Div(
                                        [
                                            html.Label("Sort Direction"),

                                            dcc.RadioItems(
                                                id={
                                                    "type": "grainlog-sort-direction",
                                                    "index": panel["id"],
                                                },
                                                options=[
                                                    {
                                                        "label": "Ascending",
                                                        "value": "asc",
                                                    },
                                                    {
                                                        "label": "Descending",
                                                        "value": "desc",
                                                    },
                                                ],
                                                value=(
                                                    "asc"
                                                    if panel.get(
                                                        "grainlog_sort_ascending",
                                                        True,
                                                    )
                                                    else "desc"
                                                ),
                                                inline=True,
                                            ),
                                        ],
                                        style={
                                            "display":
                                                "block"
                                                if is_grain_log
                                                else "none"
                                        },
                                    ),

                                    html.Div(
                                        dcc.Checklist(
                                            id={
                                                "type": "show-std1",
                                                "index": panel["id"],
                                            },
                                            options=[{
                                                "label": "Show ±1 Std Dev",
                                                "value": "std1",
                                            }],
                                            value=(
                                                ["std1"]
                                                if panel.get(
                                                    "show_std1",
                                                    False,
                                                )
                                                else []
                                            ),
                                        ),
                                        style={
                                            "display": (
                                                "block"
                                                if is_psd
                                                else "none"
                                            )
                                        },
                                    ),

                                    html.Div(
                                        dcc.Checklist(
                                            id={
                                                "type": "show-std2",
                                                "index": panel["id"],
                                            },
                                            options=[{
                                                "label": "Show ±2 Std Dev",
                                                "value": "std2",
                                            }],
                                            value=(
                                                ["std2"]
                                                if panel.get(
                                                    "show_std2",
                                                    False,
                                                )
                                                else []
                                            ),
                                        ),
                                        style={
                                            "display": (
                                                "block"
                                                if is_psd
                                                else "none"
                                            )
                                        },
                                    ),

                                    html.Div(
                                        dcc.Checklist(
                                            id={
                                                "type": "show-std3",
                                                "index": panel["id"],
                                            },
                                            options=[{
                                                "label": "Show ±3 Std Dev",
                                                "value": "std3",
                                            }],
                                            value=(
                                                ["std3"]
                                                if panel.get(
                                                    "show_std3",
                                                    False,
                                                )
                                                else []
                                            ),
                                        ),
                                        style={
                                            "display": (
                                                "block"
                                                if is_psd
                                                else "none"
                                            )
                                        },
                                    ),

                                    html.Div(
                                        [
                                            html.Label("Group By"),

                                            dcc.Dropdown(
                                                id={
                                                    "type": "group-by",
                                                    "index": panel["id"],
                                                },
                                                options=group_by_options,
                                                value=panel.get(
                                                    "group_by",
                                                    "None",
                                                ),
                                                clearable=False,
                                            ),
                                        ],
                                        id={
                                            "type": "group-by-container",
                                            "index": panel["id"],
                                        },
                                        style={
                                            "display": (
                                                "none"
                                                if panel.get(
                                                    "use_custom_groups",
                                                    False,
                                                )
                                                else (
                                                    "block"
                                                    if panel["chart_type"] in [
                                                        "PSD Undersize",
                                                        "PSD Frequency",
                                                        "Grain Size Log",
                                                        "Ternary",
                                                    ]
                                                    else "none"
                                                )
                                            )
                                        },
                                    ),

                                    html.Br(),

                                    dcc.Checklist(
                                        id={
                                            "type": "use-custom-groups",
                                            "index": panel["id"],
                                        },
                                        options=[
                                            {
                                                "label": " Use Custom Groups",
                                                "value": "custom",
                                            }
                                        ],
                                        value=(
                                            ["custom"]
                                            if panel.get(
                                                "use_custom_groups",
                                                False,
                                            )
                                            else []
                                        ),
                                    ),

                                    html.Div(
                                        id={
                                            "type": "custom-group-container",
                                            "index": panel["id"],
                                        },
                                        style={
                                            "display":
                                                "block"
                                                if panel.get(
                                                    "use_custom_groups",
                                                    False,
                                                )
                                                else "none",
                                            "marginTop": "10px",
                                        },
                                        children=[
                                            html.Button(
                                                "Add Group",
                                                id={
                                                    "type": "add-custom-group",
                                                    "index": panel["id"],
                                                },
                                                n_clicks=0,
                                            ),

                                            html.Div(
                                                id={
                                                    "type": "custom-group-list",
                                                    "index": panel["id"],
                                                },
                                            ),
                                        ],
                                    ),

                                    html.Div(
                                        dcc.Checklist(
                                            id={
                                                "type": "show-centroids",
                                                "index": panel["id"],
                                            },
                                            options=[{
                                                "label": "Show Group Centroids",
                                                "value": "centroids",
                                            }],
                                            value=(
                                                ["centroids"]
                                                if panel.get(
                                                    "show_centroids",
                                                    False,
                                                )
                                                else []
                                            ),
                                        ),
                                        style={
                                            "display": (
                                                "block"
                                                if panel["chart_type"] == "Ternary"
                                                else "none"
                                            )
                                        },
                                    ),

                                    html.Div(
                                        dcc.Checklist(
                                            id={
                                                "type": "show-covariance",
                                                "index": panel["id"],
                                            },
                                            options=[{
                                                "label": "Show Covariance Ellipses",
                                                "value": "covariance",
                                            }],
                                            value=(
                                                ["covariance"]
                                                if panel.get(
                                                    "show_covariance",
                                                    False,
                                                )
                                                else []
                                            ),
                                        ),
                                        style={
                                            "display": (
                                                "block"
                                                if is_ternary
                                                else "none"
                                            )
                                        },
                                    ),

                                    html.Br(),

                                    html.Div(
                                        [
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
                                        ],
                                        style={
                                            "display": (
                                                "block"
                                                if is_psd
                                                else "none"
                                            )
                                        },
                                    ),

                                    html.Div(
                                        [
                                            html.Label("Reference Breaks"),

                                            dcc.Checklist(
                                                id={
                                                    "type": "reference-breaks",
                                                    "index": panel["id"],
                                                },
                                                options=[
                                                    {"label": "2 µm", "value": "2"},
                                                    {"label": "4 µm", "value": "4"},
                                                    {"label": "8 µm", "value": "8"},
                                                    {"label": "50 µm", "value": "50"},
                                                    {"label": "62.5 µm", "value": "62.5"},
                                                ],
                                                value=[
                                                    x for x in [

                                                        "2"
                                                        if panel.get(
                                                            "show_break_2",
                                                            False,
                                                        )
                                                        else None,

                                                        "4"
                                                        if panel.get(
                                                            "show_break_4",
                                                            False,
                                                        )
                                                        else None,

                                                        "8"
                                                        if panel.get(
                                                            "show_break_8",
                                                            False,
                                                        )
                                                        else None,

                                                        "50"
                                                        if panel.get(
                                                            "show_break_50",
                                                            False,
                                                        )
                                                        else None,

                                                        "62.5"
                                                        if panel.get(
                                                            "show_break_62_5",
                                                            False,
                                                        )
                                                        else None,
                                                    ]
                                                    if x is not None
                                                ],
                                            ),
                                        ],
                                        style={
                                            "display": (
                                                "block"
                                                if is_psd
                                                else "none"
                                            )
                                        },
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

                                    html.Label("Mastersizer Sand/Silt Break"),

                                    dcc.RadioItems(
                                        id={
                                            "type": "mastersizer-sand-break",
                                            "index": panel["id"],
                                        },
                                        options=[
                                            {"label": "50 µm", "value": 50},
                                            {"label": "62.5 µm", "value": 62.5},
                                        ],
                                        value=panel["mastersizer_sand_break"],
                                        inline=True,
                                    ),

                                    html.Br(),

                                    html.P(
                                        "Kehew: Fixed 4 µm"
                                    ),

                                    html.P(
                                        "Dry Sieve: Clay = 0, Silt = Fines_0_63"
                                    ),

                                    html.Div(
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
                                        style={
                                            "display": (
                                                "block"
                                                if is_ternary
                                                else "none"
                                            )
                                        },
                                    ),
                                ],
                                style={
                                    "display": (
                                        "block"
                                        if supports_grain_breaks
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
                                    html.Div(
                                        [
                                            html.H4("Panel Query Builder"),

                                            html.Label("Field"),

                                            dcc.Dropdown(
                                                id={
                                                    "type": "panel-filter-field",
                                                    "index": panel["id"],
                                                },
                                                options=[
                                                    {
                                                        "label": label,
                                                        "value": field,
                                                    }
                                                    for field, label in (
                                                            GROUP_BY_FIELDS
                                                            | NUMERIC_FIELDS
                                                    ).items()
                                                ],
                                                placeholder="Field",
                                            ),

                                            html.Br(),

                                            html.Label("Operator"),

                                            dcc.Dropdown(
                                                id={
                                                    "type": "panel-filter-operator",
                                                    "index": panel["id"],
                                                },
                                                value="IN",
                                                clearable=False,
                                            ),

                                            html.Br(),

                                            html.Label("Value"),

                                            dcc.Dropdown(
                                                id={
                                                    "type": "panel-filter-dropdown",
                                                    "index": panel["id"],
                                                },
                                                multi=True,
                                            ),

                                            dcc.Input(
                                                id={
                                                    "type": "panel-filter-text",
                                                    "index": panel["id"],
                                                },
                                                type="text",
                                                placeholder="Enter text...",
                                                style={
                                                    "display": "none",
                                                    "width": "100%",
                                                },
                                            ),

                                            dcc.Input(
                                                id={
                                                    "type": "panel-filter-number",
                                                    "index": panel["id"],
                                                },
                                                type="number",
                                                placeholder="Value",
                                                style={
                                                    "display": "none",
                                                    "width": "100%",
                                                },
                                            ),

                                            html.Div(
                                                [
                                                    dcc.Input(
                                                        id={
                                                            "type": "panel-filter-min",
                                                            "index": panel["id"],
                                                        },
                                                        type="number",
                                                        placeholder="Minimum",
                                                        style={
                                                            "width": "48%",
                                                        },
                                                    ),
                                                    dcc.Input(
                                                        id={
                                                            "type": "panel-filter-max",
                                                            "index": panel["id"],
                                                        },
                                                        type="number",
                                                        placeholder="Maximum",
                                                        style={
                                                            "width": "48%",
                                                        },
                                                    ),
                                                ],
                                                id={
                                                    "type": "panel-filter-between",
                                                    "index": panel["id"],
                                                },
                                                style={
                                                    "display": "none",
                                                    "justifyContent": "space-between",
                                                },
                                            ),

                                            html.Br(),

                                            html.Button(
                                                "Add Clause",
                                                id={
                                                    "type": "add-panel-filter",
                                                    "index": panel["id"],
                                                },
                                                n_clicks=0,
                                            ),

                                            html.Br(),
                                            html.Br(),

                                            html.Button(
                                                "Apply Filter",
                                                id={
                                                    "type": "apply-panel-filter",
                                                    "index": panel["id"],
                                                },
                                                n_clicks=0,
                                            ),

                                            html.Button(
                                                "Clear Filter",
                                                id={
                                                    "type": "clear-panel-filter",
                                                    "index": panel["id"],
                                                },
                                                n_clicks=0,
                                                style={
                                                    "marginLeft": "10px",
                                                },
                                            ),

                                            html.Div(
                                                id={
                                                    "type": "panel-filter-list",
                                                    "index": panel["id"],
                                                },
                                                style={
                                                    "marginTop": "10px",
                                                },
                                            ),
                                        ],
                                        id={
                                            "type": "panel-query-builder-container",
                                            "index": panel["id"],
                                        },
                                        style={
                                            "display": (
                                                "none"
                                                if panel["use_global"]
                                                else "block"
                                            )
                                        },
                                    ),
                                ],
                                style={
                                    "display": (
                                        "block"
                                        if panel["override_options_open"]
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

                    html.Div(
                        id={
                            "type": "panel-selected-count",
                            "index": panel["id"],
                        },
                        children="Selected Samples: 0",
                        style={
                            "fontWeight": "bold",
                            "marginBottom": "10px",
                        },
                    ),

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

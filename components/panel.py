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

    panel.setdefault(
        "pca_vertical_x_field",
        "BoreholeID",
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

    # --------------------------------------------------------
    # PCA report-section visibility
    #
    # Backward compatibility:
    # older saved states used show_depth_borehole instead of
    # the unified pca_report_sections setting.
    # --------------------------------------------------------

    if "pca_report_sections" not in panel:

        panel["pca_report_sections"] = [
            "scores",
            "scree",
            "loadings",
            "hierarchy",
            "heatmap",
            "grain_histogram",
            "silhouette",
            "cluster_summary",
            "depth",
        ]

        if panel.get(
                "show_depth_borehole",
                False,
        ):

            if (
                    "depth"
                    not in panel[
                "pca_report_sections"
            ]
            ):
                panel[
                    "pca_report_sections"
                ].append(
                    "depth"
                )

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

    is_pca = (
            chart_type == "PCA"
    )

    is_mastersizer_pca = (
            chart_type
            == "PCA - Mastersizer Only"
    )

    is_pca_report = (
            is_pca
            or is_mastersizer_pca
    )

    is_hierarchical = (
            chart_type
            == "Hierarchical Clustering"
    )

    is_multivariate = (
            is_pca_report
            or is_hierarchical
    )

    supports_grouping = (
            is_psd
            or is_ternary
            or is_grain_log
            or is_pca_report
    )

    supports_grain_breaks = (
            is_ternary
            or is_grain_log
            or is_pca_report
    )

    supports_sample_display = (
            is_psd
            or is_ternary
            or is_pca
    )

    display_option_choices = []

    if is_psd:
        display_option_choices.extend(
            [
                {"label": "Show Legend", "value": "legend"},
                {"label": "Show Sample Labels", "value": "labels"},
                {"label": "Show Samples", "value": "samples"},
                {"label": "Show Mean", "value": "mean"},
                {"label": "Show ±1 Std Dev", "value": "std1"},
                {"label": "Show ±2 Std Dev", "value": "std2"},
                {"label": "Show ±3 Std Dev", "value": "std3"},
            ]
        )

    elif is_ternary:
        display_option_choices.extend(
            [
                {"label": "Show Legend", "value": "legend"},
                {"label": "Show Sample Labels", "value": "labels"},
                {"label": "Show Samples", "value": "samples"},
                {"label": "Show Group Centroids", "value": "centroids"},
                {"label": "Show Covariance Ellipses", "value": "covariance"},
            ]
        )

    elif is_grain_log:
        display_option_choices.append(
            {"label": "Show Mean", "value": "grainlog_mean"}
        )

    elif is_pca:
        display_option_choices.append(
            {"label": "Show Sample Labels", "value": "labels"}
        )

    elif is_mastersizer_pca:
        display_option_choices.extend(
            [
                {"label": "Show Sample Labels", "value": "labels"},
                {"label": "Show ±1 Std Dev", "value": "std1"},
                {"label": "Show ±2 Std Dev", "value": "std2"},
                {"label": "Show ±3 Std Dev", "value": "std3"},
            ]
        )

    display_option_values = []

    for display_key, enabled in [
        ("legend", panel.get("show_legend", True)),
        ("labels", panel.get("show_labels", False)),
        ("samples", panel.get("show_samples", True)),
        ("mean", panel.get("show_mean", False)),
        ("grainlog_mean", panel.get("show_grainlog_mean", False)),
        ("std1", panel.get("show_std1", False)),
        ("std2", panel.get("show_std2", False)),
        ("std3", panel.get("show_std3", False)),
        ("centroids", panel.get("show_centroids", False)),
        ("covariance", panel.get("show_covariance", False)),
    ]:
        if enabled:
            display_option_values.append(
                display_key
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
                        "Panel Options",
                        type="button",
                        className="panel-options-open",
                        **{"data-panel-id": str(panel["id"])},
                        style={
                            "float": "right",
                            "marginLeft": "5px",
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
                    html.Div(
                        "Chart Type",
                        className="panel-chart-type-label",
                    ),
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
                            "PCA",
                            "PCA - Mastersizer Only",
                            "Sample Information",
                        ],
                        value=panel["chart_type"],
                        clearable=False,
                        style={"minWidth": "260px"},
                    ),
                ],
                className="panel-chart-type-row",
            ),

            html.Div(
                [

                    html.Dialog(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                f"Panel {display_number} Options",
                                                className="panel-options-title",
                                            ),
                                            html.Button(
                                                "×",
                                                id={
                                                    "type":
                                                        "cancel-panel-options-x",
                                                    "index": panel["id"],
                                                },
                                                n_clicks=0,
                                                type="button",
                                                className=(
                                                    "panel-options-close "
                                                    "panel-options-cancel"
                                                ),
                                                **{
                                                    "data-panel-id":
                                                        str(panel["id"])
                                                },
                                            ),
                                        ],
                                        className="panel-options-window-header",
                                    ),
                                    html.Div(
                                        id={
                                            "type": "panel-selected-count",
                                            "index": panel["id"],
                                        },
                                        children="Selected Samples: 0",
                                        className="panel-options-selected-count",
                                    ),
                                    html.Div(
                                        "Display & Axes",
                                        className="panel-options-section-title",
                                    ),

                                    # PSD-specific controls
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Label(
                                                        "Display Options"
                                                    ),

                                                    dcc.Dropdown(
                                                        id={
                                                            "type":
                                                                "display-options",
                                                            "index":
                                                                panel["id"],
                                                        },
                                                        options=
                                                        display_option_choices,
                                                        value=[
                                                            value
                                                            for value
                                                            in display_option_values
                                                            if value
                                                               in {
                                                                   option["value"]
                                                                   for option
                                                                   in display_option_choices
                                                               }
                                                        ],
                                                        multi=True,
                                                        closeOnSelect=False,
                                                        placeholder=(
                                                            "Select display options..."
                                                        ),
                                                    ),
                                                ],
                                                className="panel-options-wide",
                                                style={
                                                    "display": (
                                                        "block"
                                                        if display_option_choices
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

                                                    dcc.Dropdown(
                                                        id={"type": "grainlog-sort-direction", "index": panel["id"]},
                                                        options=[
                                                            {"label": "Ascending", "value": "asc"},
                                                            {"label": "Descending", "value": "desc"},
                                                        ],
                                                        value=("asc" if panel.get("grainlog_sort_ascending",
                                                                                  True) else "desc"),
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

                                            html.Br(),

                                            html.Div(
                                                [
                                                    html.Label("X Axis"),

                                                    dcc.Dropdown(
                                                        id={"type": "x-axis", "index": panel["id"]},
                                                        options=[
                                                            {"label": "Log", "value": "log"},
                                                            {"label": "Linear", "value": "linear"},
                                                            {"label": "Phi", "value": "phi"},
                                                        ],
                                                        value=panel["x_axis"],
                                                        clearable=False,
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
                                                    html.Label(
                                                        "Reference Breaks"
                                                    ),

                                                    dcc.Dropdown(
                                                        id={
                                                            "type":
                                                                "reference-breaks",
                                                            "index":
                                                                panel["id"],
                                                        },
                                                        options=[
                                                            {"label": "2 µm", "value": "2"},
                                                            {"label": "4 µm", "value": "4"},
                                                            {"label": "8 µm", "value": "8"},
                                                            {"label": "50 µm", "value": "50"},
                                                            {"label": "62.5 µm", "value": "62.5"},
                                                        ],
                                                        value=[
                                                            value
                                                            for value in [
                                                                "2" if panel.get("show_break_2", False) else None,
                                                                "4" if panel.get("show_break_4", False) else None,
                                                                "8" if panel.get("show_break_8", False) else None,
                                                                "50" if panel.get("show_break_50", False) else None,
                                                                "62.5" if panel.get("show_break_62_5", False) else None,
                                                            ]
                                                            if value is not None
                                                        ],
                                                        multi=True,
                                                        closeOnSelect=False,
                                                        placeholder=(
                                                            "Select reference breaks..."
                                                        ),
                                                    ),
                                                ],
                                                className="panel-options-wide",
                                                style={
                                                    "display": (
                                                        "block"
                                                        if (
                                                                is_psd
                                                                or is_mastersizer_pca
                                                        )
                                                        else "none"
                                                    )
                                                },
                                            ),

                                            # ---------------------------------
                                            # ---------------------------------
                                            html.Div(
                                                "PCA & Clustering",
                                                className="panel-options-section-title",
                                                style={
                                                    "display": (
                                                        "block"
                                                        if is_pca_report
                                                        else "none"
                                                    )
                                                },
                                            ),

                                            # PCA / multivariate analysis
                                            # ---------------------------------

                                            html.Div(
                                                [
                                                    html.Hr(),

                                                    html.Div(
                                                        [
                                                            html.Label(
                                                                "Mastersizer PCA Data"
                                                            ),

                                                            dcc.Dropdown(
                                                                id={"type": "mastersizer-pca-input",
                                                                    "index": panel["id"]},
                                                                options=[
                                                                    {"label": "Frequency Bins (FR)",
                                                                     "value": "frequency"},
                                                                    {"label": "PSD Undersize Bins", "value": "psd"},
                                                                ],
                                                                value=panel.get("mastersizer_pca_input", "frequency"),
                                                                clearable=False,
                                                            ),

                                                            html.Div(
                                                                (
                                                                    "Frequency mode follows the "
                                                                    "compositional CLR workflow. "
                                                                    "PSD mode uses cumulative "
                                                                    "undersize bins."
                                                                ),

                                                                style={
                                                                    "fontSize":
                                                                        "0.78rem",

                                                                    "color":
                                                                        "#667085",

                                                                    "marginTop":
                                                                        "4px",
                                                                },
                                                            ),

                                                            html.Br(),
                                                        ],

                                                        style={
                                                            "display":
                                                                (
                                                                    "block"
                                                                    if is_mastersizer_pca
                                                                    else "none"
                                                                ),
                                                        },
                                                    ),

                                                    html.Label(
                                                        "Analysis Variables",
                                                        style={
                                                            "display":
                                                                (
                                                                    "block"
                                                                    if is_pca
                                                                    else "none"
                                                                ),
                                                        },
                                                    ),

                                                    dcc.Dropdown(
                                                        id={
                                                            "type":
                                                                "analysis-variables",
                                                            "index":
                                                                panel["id"],
                                                        },

                                                        options=[
                                                            {
                                                                "label": label,
                                                                "value": field,
                                                            }
                                                            for field, label
                                                            in NUMERIC_FIELDS.items()
                                                        ],

                                                        value=panel.get(
                                                            "analysis_variables",
                                                            [],
                                                        ),

                                                        multi=True,

                                                        placeholder=(
                                                            "Select 2 or more variables..."
                                                        ),

                                                        style={
                                                            "display":
                                                                (
                                                                    "block"
                                                                    if is_pca
                                                                    else "none"
                                                                ),
                                                        },
                                                    ),

                                                    html.Br(),

                                                    dcc.Checklist(
                                                        id={
                                                            "type":
                                                                "analysis-standardize",
                                                            "index":
                                                                panel["id"],
                                                        },

                                                        options=[
                                                            {
                                                                "label":
                                                                    (
                                                                        " Standardize PSD bins "
                                                                        "(Frequency/CLR ignores this)"
                                                                        if is_mastersizer_pca
                                                                        else " Standardize variables"
                                                                    ),
                                                                "value":
                                                                    "standardize",
                                                            }
                                                        ],

                                                        value=(
                                                            [
                                                                "standardize"
                                                            ]
                                                            if panel.get(
                                                                "analysis_standardize",
                                                                True,
                                                            )
                                                            else []
                                                        ),
                                                    ),

                                                    dcc.Checklist(
                                                        id={
                                                            "type":
                                                                "show-loading-arrows",
                                                            "index":
                                                                panel["id"],
                                                        },
                                                        options=[
                                                            {
                                                                "label":
                                                                    " Show Loading Arrows",
                                                                "value":
                                                                    "arrows",
                                                            }
                                                        ],
                                                        value=(
                                                            ["arrows"]
                                                            if panel.get(
                                                                "show_loading_arrows",
                                                                False,
                                                            )
                                                            else []
                                                        ),
                                                    ),

                                                    html.Br(),

                                                    html.Hr(),

                                                    html.Div(
                                                        "Hierarchical Clustering",
                                                        className=(
                                                            "panel-options-subsection-title"
                                                        ),
                                                    ),

                                                    html.Label(
                                                        "Linkage Method"
                                                    ),

                                                    dcc.Dropdown(
                                                        id={
                                                            "type":
                                                                "cluster-linkage",
                                                            "index":
                                                                panel["id"],
                                                        },

                                                        options=[
                                                            {
                                                                "label": "Ward",
                                                                "value": "ward",
                                                            },
                                                            {
                                                                "label": "Average",
                                                                "value": "average",
                                                            },
                                                            {
                                                                "label": "Complete",
                                                                "value": "complete",
                                                            },
                                                            {
                                                                "label": "Single",
                                                                "value": "single",
                                                            },
                                                        ],

                                                        value=panel.get(
                                                            "cluster_linkage",
                                                            "ward",
                                                        ),

                                                        clearable=False,
                                                    ),

                                                    html.Br(),

                                                    html.Label(
                                                        "Distance Metric"
                                                    ),

                                                    dcc.Dropdown(
                                                        id={
                                                            "type":
                                                                "cluster-metric",
                                                            "index":
                                                                panel["id"],
                                                        },

                                                        options=[
                                                            {
                                                                "label":
                                                                    "Euclidean",
                                                                "value":
                                                                    "euclidean",
                                                            },
                                                            {
                                                                "label":
                                                                    "Manhattan",
                                                                "value":
                                                                    "cityblock",
                                                            },
                                                            {
                                                                "label":
                                                                    "Cosine",
                                                                "value":
                                                                    "cosine",
                                                            },
                                                        ],

                                                        value=panel.get(
                                                            "cluster_metric",
                                                            "euclidean",
                                                        ),

                                                        clearable=False,
                                                    ),

                                                    html.Br(),

                                                    html.Label(
                                                        "Number of Clusters (k)"
                                                    ),

                                                    dcc.Dropdown(
                                                        id={"type": "cluster-k", "index": panel["id"]},
                                                        options=[{"label": str(i), "value": i} for i in range(2, 11)],
                                                        value=panel.get("cluster_k", 4),
                                                        clearable=False,
                                                    ),

                                                    html.Br(),

                                                    html.Label(
                                                        "Hierarchy Summary Variables"
                                                    ),

                                                    dcc.Dropdown(
                                                        id={
                                                            "type":
                                                                "hierarchy-summary-variables",
                                                            "index":
                                                                panel["id"],
                                                        },

                                                        options=[
                                                            {
                                                                "label": label,
                                                                "value": field,
                                                            }
                                                            for field, label
                                                            in NUMERIC_FIELDS.items()
                                                        ],

                                                        value=panel.get(
                                                            "hierarchy_summary_variables",
                                                            panel.get(
                                                                "analysis_variables",
                                                                [],
                                                            ),
                                                        ),

                                                        multi=True,

                                                        placeholder=(
                                                            "Select variables to summarize..."
                                                        ),
                                                    ),

                                                    html.Br(),

                                                    html.Label(
                                                        "Hierarchy Summary Statistics"
                                                    ),

                                                    dcc.Dropdown(
                                                        id={
                                                            "type":
                                                                "hierarchy-summary-stats",
                                                            "index":
                                                                panel["id"],
                                                        },
                                                        options=[
                                                            {
                                                                "label":
                                                                    "Sample Count (N)",
                                                                "value":
                                                                    "n",
                                                            },
                                                            {
                                                                "label":
                                                                    "Median",
                                                                "value":
                                                                    "median",
                                                            },
                                                            {
                                                                "label":
                                                                    "IQR (Q25–Q75)",
                                                                "value":
                                                                    "iqr",
                                                            },
                                                            {
                                                                "label":
                                                                    "Mean",
                                                                "value":
                                                                    "mean",
                                                            },
                                                            {
                                                                "label":
                                                                    "Std Dev",
                                                                "value":
                                                                    "std",
                                                            },
                                                            {
                                                                "label":
                                                                    "Min–Max",
                                                                "value":
                                                                    "minmax",
                                                            },
                                                        ],
                                                        value=panel.get(
                                                            "hierarchy_summary_stats",
                                                            [
                                                                "n",
                                                                "median",
                                                            ],
                                                        ),
                                                        multi=True,
                                                        closeOnSelect=False,
                                                        placeholder=(
                                                            "Select summary statistics..."
                                                        ),
                                                    ),

                                                    html.Br(),

                                                    html.Label(
                                                        "PCA Point Grouping"
                                                    ),

                                                    dcc.Dropdown(
                                                        id={"type": "pca-color-mode", "index": panel["id"]},
                                                        options=[
                                                            {"label": "Group By / Custom Groups", "value": "group"},
                                                            {"label": "Hierarchical Cluster", "value": "cluster"},
                                                        ],
                                                        value=panel.get("pca_color_mode", "group"),
                                                        clearable=False,
                                                    ),

                                                    html.Br(),

                                                    html.Details(
                                                        [
                                                            html.Summary(
                                                                "Displayed Report Sections",
                                                                style={
                                                                    "cursor":
                                                                        "pointer",
                                                                    "fontWeight":
                                                                        "600",
                                                                    "padding":
                                                                        "6px 0",
                                                                },
                                                            ),

                                                            dcc.Checklist(
                                                                id={
                                                                    "type":
                                                                        "pca-report-sections",
                                                                    "index":
                                                                        panel["id"],
                                                                },

                                                                options=[
                                                                    {
                                                                        "label":
                                                                            " PCA Scores",
                                                                        "value":
                                                                            "scores",
                                                                    },
                                                                    {
                                                                        "label":
                                                                            " Scree Plot",
                                                                        "value":
                                                                            "scree",
                                                                    },
                                                                    {
                                                                        "label":
                                                                            " Loadings",
                                                                        "value":
                                                                            "loadings",
                                                                    },
                                                                    {
                                                                        "label":
                                                                            " Cluster Hierarchy Summary",
                                                                        "value":
                                                                            "hierarchy",
                                                                    },
                                                                    {
                                                                        "label":
                                                                            " Cluster / Group Heatmap",
                                                                        "value":
                                                                            "heatmap",
                                                                    },
                                                                    {
                                                                        "label":
                                                                            (
                                                                                " Mastersizer Mean / SD Curves"
                                                                                if is_mastersizer_pca
                                                                                else " Grain-Fraction Histograms"
                                                                            ),
                                                                        "value":
                                                                            "grain_histogram",
                                                                    },
                                                                    {
                                                                        "label":
                                                                            " Silhouette by k",
                                                                        "value":
                                                                            "silhouette",
                                                                    },
                                                                    {
                                                                        "label":
                                                                            " Cluster Summary",
                                                                        "value":
                                                                            "cluster_summary",
                                                                    },
                                                                    {
                                                                        "label":
                                                                            (
                                                                                " Vertical Cluster / "
                                                                                "Group Profile"
                                                                            ),
                                                                        "value":
                                                                            "depth",
                                                                    },
                                                                ],

                                                                value=panel.get(
                                                                    "pca_report_sections",
                                                                    [
                                                                        "scores",
                                                                        "scree",
                                                                        "loadings",
                                                                        "hierarchy",
                                                                        "heatmap",
                                                                        "grain_histogram",
                                                                        "silhouette",
                                                                        "cluster_summary",
                                                                        "depth",
                                                                    ],
                                                                ),

                                                                style={
                                                                    "display":
                                                                        "grid",
                                                                    "gridTemplateColumns":
                                                                        "1fr",
                                                                    "gap":
                                                                        "5px",
                                                                    "padding":
                                                                        "7px 10px 10px 10px",
                                                                },
                                                            ),
                                                        ],

                                                        open=False,

                                                        style={
                                                            "border":
                                                                "1px solid #d0d5dd",
                                                            "borderRadius":
                                                                "4px",
                                                            "padding":
                                                                "0 8px",
                                                        },
                                                    ),

                                                    html.Br(),

                                                    html.Div(
                                                        "Vertical Cluster / Group Profile",
                                                        className=(
                                                            "panel-options-subsection-title"
                                                        ),
                                                    ),

                                                    html.Label(
                                                        "X Axis Category"
                                                    ),

                                                    dcc.Dropdown(
                                                        id={
                                                            "type":
                                                                "pca-vertical-x-field",
                                                            "index":
                                                                panel["id"],
                                                        },

                                                        options=(
                                                                [
                                                                    {
                                                                        "label":
                                                                            "Borehole ID",
                                                                        "value":
                                                                            "BoreholeID",
                                                                    }
                                                                ]
                                                                + [
                                                                    {
                                                                        "label": label,
                                                                        "value": field,
                                                                    }
                                                                    for field, label
                                                                    in GROUP_BY_FIELDS.items()
                                                                    if field != "BoreholeID"
                                                                ]
                                                        ),

                                                        value=panel.get(
                                                            "pca_vertical_x_field",
                                                            "BoreholeID",
                                                        ),

                                                        clearable=False,
                                                    ),

                                                    html.Br(),

                                                    html.Label(
                                                        "Vertical Axis"
                                                    ),

                                                    dcc.Dropdown(
                                                        id={"type": "borehole-vertical-axis", "index": panel["id"]},
                                                        options=[
                                                            {"label": "Depth", "value": "depth"},
                                                            {"label": "Elevation", "value": "elevation"},
                                                        ],
                                                        value=panel.get("borehole_vertical_axis", "depth"),
                                                        clearable=False,
                                                    ),
                                                ],

                                                className="pca-options-grid panel-options-wide",
                                                style={
                                                    "display": (
                                                        "grid"
                                                        if is_pca_report
                                                        else "none"
                                                    )
                                                },
                                            ),
                                        ],
                                        className="basic-options-grid",
                                        style={
                                            "display": (
                                                "grid"
                                                if (
                                                        panel["chart_type"] in [
                                                    "PSD Undersize",
                                                    "PSD Frequency",
                                                    "Ternary",
                                                    "Grain Size Log",
                                                    "PCA",
                                                    "PCA - Mastersizer Only",
                                                    "Hierarchical Clustering",
                                                ]
                                                )
                                                else "none"
                                            )
                                        },
                                    ),

                                    html.Div(
                                        "Grain-Size Settings",
                                        className="panel-options-section-title",
                                        style={
                                            "display": (
                                                "block"
                                                if supports_grain_breaks
                                                else "none"
                                            )
                                        },
                                    ),

                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Label(
                                                        "Mastersizer Clay/Silt Break"
                                                    ),
                                                    dcc.Dropdown(
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
                                                        clearable=False,
                                                    ),
                                                ],
                                                className="grain-setting-item",
                                            ),

                                            html.Div(
                                                [
                                                    html.Label(
                                                        "Mastersizer Sand/Silt Break"
                                                    ),
                                                    dcc.Dropdown(
                                                        id={
                                                            "type":
                                                                "mastersizer-sand-break",
                                                            "index": panel["id"],
                                                        },
                                                        options=[
                                                            {"label": "50 µm", "value": 50},
                                                            {"label": "62.5 µm", "value": 62.5},
                                                        ],
                                                        value=panel[
                                                            "mastersizer_sand_break"
                                                        ],
                                                        clearable=False,
                                                    ),
                                                ],
                                                className="grain-setting-item",
                                            ),

                                            html.Div(
                                                [
                                                    html.Label(
                                                        "Pipette Clay/Silt Break"
                                                    ),
                                                    dcc.Dropdown(
                                                        id={
                                                            "type": "pipette-break",
                                                            "index": panel["id"],
                                                        },
                                                        options=[
                                                            {"label": "2 µm", "value": 2},
                                                            {"label": "4 µm", "value": 4},
                                                        ],
                                                        value=panel["pipette_break"],
                                                        clearable=False,
                                                    ),
                                                ],
                                                className="grain-setting-item",
                                            ),

                                            html.Div(
                                                [
                                                    html.Label("Include Gravel"),
                                                    dcc.Dropdown(
                                                        id={
                                                            "type": "grainlog-gravel",
                                                            "index": panel["id"],
                                                        },
                                                        options=[
                                                            {
                                                                "label": "Mastersizer",
                                                                "value": "Mastersizer",
                                                            },
                                                            {
                                                                "label": "Pipette",
                                                                "value": "Pipette",
                                                            },
                                                            {
                                                                "label": "Kehew",
                                                                "value": "Kehew",
                                                            },
                                                            {
                                                                "label": "Dry Sieve",
                                                                "value": "Dry Sieve",
                                                            },
                                                        ],
                                                        value=[
                                                            method
                                                            for method, enabled
                                                            in panel.get(
                                                                "grainlog_gravel_settings",
                                                                {
                                                                    "Mastersizer": False,
                                                                    "Pipette": True,
                                                                    "Kehew": True,
                                                                    "Dry Sieve": True,
                                                                },
                                                            ).items()
                                                            if enabled
                                                        ],
                                                        multi=True,
                                                        closeOnSelect=False,
                                                        placeholder=(
                                                            "Select methods that "
                                                            "include gravel..."
                                                        ),
                                                    ),
                                                ],
                                                className=(
                                                    "grain-setting-item "
                                                    "grain-setting-wide"
                                                ),
                                            ),

                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            html.Strong(
                                                                "Kehew: "
                                                            ),
                                                            html.Span(
                                                                "Clay/Silt Break = 4 µm"
                                                            ),
                                                        ]
                                                    ),
                                                    html.Div(
                                                        [
                                                            html.Strong(
                                                                "Dry Sieve: "
                                                            ),
                                                            html.Span(
                                                                "Clay = 0; "
                                                                "Silt = 0–63 µm"
                                                            ),
                                                        ]
                                                    ),
                                                ],
                                                className="grain-setting-note",
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
                                                className="grain-setting-wide",
                                                style={
                                                    "display": (
                                                        "block"
                                                        if is_ternary
                                                        else "none"
                                                    )
                                                },
                                            ),
                                        ],
                                        className="grain-options-grid",
                                        style={
                                            "display": (
                                                "grid"
                                                if supports_grain_breaks
                                                else "none"
                                            )
                                        },
                                    ),

                                    html.Div(
                                        "Grouping",
                                        className="panel-options-section-title",
                                        style={
                                            "display": (
                                                "block"
                                                if supports_grouping
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
                                                    if supports_grouping
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
                                        style={
                                            "display": (
                                                "block"
                                                if supports_grouping
                                                else "none"
                                            )
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
                                                if (
                                                        supports_grouping
                                                        and panel.get(
                                                    "use_custom_groups",
                                                    False,
                                                )
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

                                    html.Div("Selection & Filters", className="panel-options-section-title"),

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
                                        "▶ Override Selection",
                                        type="button",
                                        className="panel-override-toggle",
                                        **{
                                            "data-panel-id":
                                                str(panel["id"])
                                        },
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
                                                    "display": "block"
                                                },
                                            ),
                                        ],
                                        id=(
                                            f"panel-override-content-"
                                            f"{panel['id']}"
                                        ),
                                        className="panel-override-content",
                                        style={
                                            "display": "none",
                                        },
                                    ),

                                    html.Div(
                                        [
                                            html.Button(
                                                "Cancel",
                                                id={
                                                    "type":
                                                        "cancel-panel-options",
                                                    "index": panel["id"],
                                                },
                                                n_clicks=0,
                                                type="button",
                                                className=(
                                                    "panel-options-cancel "
                                                    "panel-options-cancel-button"
                                                ),
                                                **{
                                                    "data-panel-id":
                                                        str(panel["id"])
                                                },
                                            ),
                                            html.Button(
                                                "Apply",
                                                id={
                                                    "type":
                                                        "apply-panel-options",
                                                    "index": panel["id"],
                                                },
                                                n_clicks=0,
                                                type="button",
                                                className=(
                                                    "panel-options-apply "
                                                    "panel-options-apply-button"
                                                ),
                                                **{
                                                    "data-panel-id":
                                                        str(panel["id"])
                                                },
                                            ),
                                        ],
                                        className="panel-options-footer",
                                    ),
                                ],
                                className="panel-options-scroll",
                            ),
                            dcc.Download(
                                id={
                                    "type": "csv-download",
                                    "index": panel["id"],
                                },
                            )
                        ],
                        id=f"panel-options-dialog-{panel['id']}",
                        className="panel-options-window",
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
            "padding": "10px",
            "marginBottom": "12px",
            "height": "100%",
            "display": "flex",
            "flexDirection": "column",
            "minHeight": 0,
        }
    )

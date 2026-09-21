from dash import (
    Dash,
    html,
    dcc,
    Input,
    Output,
    State,
    MATCH,
    ALL,
    Patch,
    callback_context,
)
import copy
import pandas as pd

import base64
import json
from datetime import datetime

from logic.data_loader import (
    load_gsa_lab,
    load_mmes,
    load_mmes_rs,
)
from components.globalselection import create_globalselection
from components.panel import create_panel
from charts.psd import make_psd_plot
from charts.frequency import make_frequency_plot
from charts.ternary import make_ternary_plot

from charts.pca import make_pca_plot
from charts.mastersizer_pca import (
    make_mastersizer_pca_plot,
)

from charts.hierarchical import (
    make_hierarchical_plot,
)

from charts.grainlog import (
    make_grain_log,
)

from charts.sample_information import (
    make_sample_information,
)

from logic.exporters import (
    get_psd_export_df,
    get_frequency_export_df,
    get_ternary_export_df,
    get_grainlog_export_df,
    get_pca_export_df,
    get_mastersizer_pca_export_df,
    get_hierarchical_export_df,
    add_export_metadata,
)

from logic.panel_filters import (
    get_panel_samples,
    apply_panel_filters,
)

from logic.filters import (
    FILTER_FIELDS,
    GROUP_BY_FIELDS,
    NUMERIC_FIELDS,
    apply_filters,
    NULL_VALUE,
)

from logic.custom_groups import (
    build_custom_groups,
    has_custom_groups,
)

from logic.text_normalization import (
    normalize_identifier_list,
)

from dash.exceptions import PreventUpdate

from dash_rgl import RGLLayout

gsa_df = load_gsa_lab()
mmes_df = load_mmes()
mmes_rs_df = load_mmes_rs()

print(
    "Analysis methods in raw dataframe:"
)
print(
    sorted(
        gsa_df["analysis_method"]
        .dropna()
        .unique()
    )
)

analysis_methods = sorted(
    gsa_df["analysis_method"]
    .dropna()
    .astype(str)
    .unique()
)

formations = sorted(
    gsa_df["formation"]
    .dropna()
    .astype(str)
    .unique()
)

boreholes = sorted(
    gsa_df["BoreholeID"]
    .dropna()
    .astype(str)
    .unique()
)

filter_options = {}

for field in FILTER_FIELDS:

    if field not in gsa_df.columns:
        continue

    series = gsa_df[field]

    values = sorted(
        series
        .dropna()
        .astype(str)
        .unique()
    )

    if series.isna().any():
        values = [NULL_VALUE] + values

    filter_options[field] = [
        {
            "label": v,
            "value": v,
        }
        for v in values
    ]

group_by_options = [
    {
        "label": "None",
        "value": "None",
    }
]

group_by_options.extend(
    [
        {
            "label": label,
            "value": field,
        }
        for field, label
        in GROUP_BY_FIELDS.items()
        if field in gsa_df.columns
    ]
)

primary_mmes_ids = set(
    mmes_df[
        "Sample_Name_Final"
    ].astype(str)
)

rs_mmes_ids = set(
    mmes_rs_df[
        "Sample_Name_Final"
    ].astype(str)
)

mmes_ids = (
        primary_mmes_ids
        | rs_mmes_ids
)

matched_count = (
    gsa_df["GSA_ID"]
    .astype(str)
    .isin(mmes_ids)
    .sum()
)

print(
    f"GSA samples: "
    f"{len(gsa_df)}"
)

print(
    f"MMES PRIMARY samples: "
    f"{len(mmes_df)}"
)

print(
    f"MMES RS samples: "
    f"{len(mmes_rs_df)}"
)

print(
    f"MMES unique samples: "
    f"{len(mmes_ids)}"
)

print(
    f"Matched samples: "
    f"{matched_count}"
)

print(
    "Duplicate GSA IDs:",
    gsa_df[
        "GSA_ID"
    ].duplicated().sum(),
)

print(
    "Duplicate PRIMARY MMES IDs:",
    mmes_df[
        "Sample_Name_Final"
    ].duplicated().sum(),
)

print(
    "Duplicate RS MMES IDs:",
    mmes_rs_df[
        "Sample_Name_Final"
    ].duplicated().sum(),
)

app = Dash(
    __name__,
    external_scripts=[
        (
            "https://cdnjs.cloudflare.com/ajax/libs/"
            "html2canvas/1.4.1/html2canvas.min.js"
        ),
    ],
)
app.title = "MGS_GSA_Plotter"



def _find_panel_index(panel_data, panel_id):
    """Return the list index for a stable panel id."""
    for i, panel in enumerate(panel_data or []):
        if panel.get("id") == panel_id:
            return i
    return None


def _get_panel_copy(panel_data, panel_id):
    """Deep-copy one panel by stable id without mutating the Store state."""
    index = _find_panel_index(panel_data, panel_id)

    if index is None:
        return None, None

    return index, copy.deepcopy(panel_data[index])





app.layout = html.Div(
    [
        html.H1("MGS_GSA_Plotter"),

        html.Div(
            [
                html.Button(
                    "Save State",
                    id="save-state-btn",
                    n_clicks=0,
                ),

                dcc.Download(
                    id="download-state",
                ),

                dcc.Upload(
                    id="load-state-upload",
                    children=html.Button(
                        "Load State",
                    ),
                    multiple=False,
                ),

                dcc.ConfirmDialog(
                    id="load-state-confirm",
                    message=(
                        "Loading a saved state will replace "
                        "your current workspace. Continue?"
                    ),
                ),
            ],
            style={
                "display": "flex",
                "gap": "10px",
                "marginBottom": "20px",
            },
        ),

        dcc.Store(
            id="panel-store",
            data=[
                {
                    "id": 1,
                    "chart_type": "PSD Undersize",
                    "use_global": True,

                    "show_legend": True,
                    "show_labels": False,

                    "show_samples": True,
                    "show_mean": False,
                    "show_grainlog_mean": False,
                    "grainlog_sort_field": "None",
                    "grainlog_sort_ascending": True,
                    "group_by": "None",
                    "show_std1": False,
                    "show_std2": False,
                    "show_std3": False,

                    "show_centroids": False,
                    "show_covariance": False,

                    "analysis_variables": [],
                    "analysis_standardize": True,
                    "mastersizer_pca_input": "frequency",

                    "cluster_linkage": "ward",
                    "cluster_metric": "euclidean",
                    "cluster_k": 4,

                    "pca_color_mode": "group",
                    "show_loading_arrows": False,
                    "show_depth_borehole": True,
                    "pca_report_sections": [
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
                    "borehole_vertical_axis": "depth",
                    "pca_vertical_x_field": "BoreholeID",
                    "hierarchy_summary_stats": [
                        "n",
                        "median",
                    ],
                    "hierarchy_summary_variables": [],

                    "x_axis": "log",

                    "show_break_2": False,
                    "show_break_4": False,
                    "show_break_8": True,
                    "show_break_50": False,
                    "show_break_62_5": True,

                    "mastersizer_break": 8,
                    "pipette_break": 2,
                    "mastersizer_sand_break": 62.5,
                    "grainlog_gravel_settings": {
                        "Mastersizer": False,
                        "Pipette": True,
                        "Kehew": True,
                        "Dry Sieve": True,
                    },

                    "show_usda_triangle": True,

                    "panel_filters": [],
                    "pending_panel_filters": [],
                    "pending_custom_groups": [],
                    "custom_group_builder_open": False,

                    "use_custom_groups": False,
                    "custom_groups": [],

                    "graph_options_open": True,
                    "override_options_open": False,

                    "controls_open": True,
                }
            ],
        ),

        dcc.Store(
            id="panel-applied-store",
            data=[
                {
                    "id": 1,
                    "chart_type": "PSD Undersize",
                    "use_global": True,

                    "show_legend": True,
                    "show_labels": False,

                    "show_samples": True,
                    "show_mean": False,
                    "show_grainlog_mean": False,
                    "grainlog_sort_field": "None",
                    "grainlog_sort_ascending": True,
                    "group_by": "None",
                    "show_std1": False,
                    "show_std2": False,
                    "show_std3": False,

                    "show_centroids": False,
                    "show_covariance": False,

                    "analysis_variables": [],
                    "analysis_standardize": True,
                    "mastersizer_pca_input": "frequency",

                    "cluster_linkage": "ward",
                    "cluster_metric": "euclidean",
                    "cluster_k": 4,

                    "pca_color_mode": "group",
                    "show_loading_arrows": False,
                    "show_depth_borehole": True,
                    "pca_report_sections": [
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
                    "borehole_vertical_axis": "depth",
                    "pca_vertical_x_field": "BoreholeID",
                    "hierarchy_summary_stats": [
                        "n",
                        "median",
                    ],
                    "hierarchy_summary_variables": [],

                    "x_axis": "log",

                    "show_break_2": False,
                    "show_break_4": False,
                    "show_break_8": True,
                    "show_break_50": False,
                    "show_break_62_5": True,

                    "mastersizer_break": 8,
                    "pipette_break": 2,
                    "mastersizer_sand_break": 62.5,
                    "grainlog_gravel_settings": {
                        "Mastersizer": False,
                        "Pipette": True,
                        "Kehew": True,
                        "Dry Sieve": True,
                    },

                    "show_usda_triangle": True,

                    "panel_filters": [],
                    "pending_panel_filters": [],
                    "pending_custom_groups": [],
                    "custom_group_builder_open": False,

                    "use_custom_groups": False,
                    "custom_groups": [],

                    "graph_options_open": True,
                    "override_options_open": False,

                    "controls_open": True,
                }
            ],
        ),

        dcc.Store(
            id="panel-reset-revision",
            data=0,
        ),

        dcc.Store(
            id="global-filters",
            data=[],
        ),

        dcc.Store(
            id="pending-global-filters",
            data=[],
        ),

        dcc.Store(
            id="layout-store",
            data=[],
        ),

        dcc.Store(
            id="loaded-state",
            data=None,
        ),

        dcc.Store(
            id="pending-layout-restore",
            data=[],
        ),

        html.Div(
            [
                create_globalselection(
                    len(gsa_df),
                    len(mmes_ids),
                    matched_count,
                    analysis_methods,
                    formations,
                    boreholes,
                    filter_options,
                ),

                html.Div(
                    [
                        html.Button(
                            "Add Panel",
                            id="add-panel",
                            n_clicks=0,
                            style={
                                "marginBottom": "15px",
                            },
                        ),

                        html.Div(
                            [
                                RGLLayout(
                                    id="panel-container",
                                    layout=[],
                                ),
                            ],
                            style={
                                "overflowX": "auto",
                                "overflowY": "hidden",
                                "width": "100%",
                            },
                        ),
                    ],
                    style={
                        "flex": 1,
                        "padding": "20px",
                        "minWidth": 0,
                        "overflowX": "auto",
                    },
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "flex-start",
                "width": "100%",
            },
        ),
    ]
)


@app.callback(
    Output(
        "download-state",
        "data",
    ),
    Input(
        "save-state-btn",
        "n_clicks",
    ),
    State(
        "panel-applied-store",
        "data",
    ),
    State(
        "layout-store",
        "data",
    ),
    State(
        "global-filters",
        "data",
    ),
    State(
        "pending-global-filters",
        "data",
    ),
    State(
        "global-samples",
        "value",
    ),
    prevent_initial_call=True,
)
def save_state(
        n_clicks,
        panel_store,
        layout_store,
        global_filters,
        pending_global_filters,
        global_samples,
):
    state = {
        "app": "MGS_GSA_Plotter",
        "version": "17.0",
        "saved_at":
            datetime.now().isoformat(),

        "panel_store":
            panel_store,

        "layout_store":
            layout_store,

        "global_filters":
            global_filters,

        "pending_global_filters":
            pending_global_filters,

        "global_samples":
            global_samples,
    }

    return dict(
        content=json.dumps(
            state,
            indent=2,
        ),
        filename=(
            f"MGS_GSA_State_"
            f"{datetime.now():%Y%m%d_%H%M%S}.json"
        ),
    )


@app.callback(
    Output(
        "loaded-state",
        "data",
    ),
    Output(
        "load-state-confirm",
        "displayed",
    ),
    Input(
        "load-state-upload",
        "contents",
    ),
    prevent_initial_call=True,
)
def load_state_file(
        contents,
):
    if not contents:
        raise PreventUpdate

    _, content_string = contents.split(",")

    decoded = base64.b64decode(
        content_string
    )

    state = json.loads(
        decoded.decode(
            "utf-8"
        )
    )

    if (
            state.get("app")
            != "MGS_GSA_Plotter"
    ):
        raise PreventUpdate

    return (
        state,
        True,
    )


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Output(
        "panel-applied-store",
        "data",
        allow_duplicate=True,
    ),
    Output(
        "global-filters",
        "data",
        allow_duplicate=True,
    ),
    Output(
        "pending-global-filters",
        "data",
        allow_duplicate=True,
    ),
    Output(
        "global-samples",
        "value",
        allow_duplicate=True,
    ),
    Output(
        "pending-layout-restore",
        "data",
        allow_duplicate=True,
    ),
    Input(
        "load-state-confirm",
        "submit_n_clicks",
    ),
    State(
        "loaded-state",
        "data",
    ),
    prevent_initial_call=True,
)
def apply_loaded_state(
        n_clicks,
        state,
):
    if not state:
        raise PreventUpdate

    loaded_panels = state.get(
        "panel_store",
        [],
    )

    return (
        copy.deepcopy(loaded_panels),
        copy.deepcopy(loaded_panels),

        state.get(
            "global_filters",
            [],
        ),

        state.get(
            "pending_global_filters",
            [],
        ),

        normalize_identifier_list(
            state.get(
                "global_samples",
                [],
            )
        ),

        state.get(
            "layout_store",
            [],
        ),
    )


@app.callback(
    Output(
        "layout-store",
        "data",
    ),
    Input(
        "panel-container",
        "layout",
    ),
    prevent_initial_call=True,
)
def store_layout(layout):
    return layout


@app.callback(
    Output(
        "panel-container",
        "layout",
        allow_duplicate=True,
    ),
    Output(
        "layout-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        "pending-layout-restore",
        "data",
    ),
    prevent_initial_call=True,
)
def restore_layout(
        layout_data,
):
    if not layout_data:
        raise PreventUpdate

    return (
        layout_data,
        layout_data,
    )


@app.callback(
    Output(
        "global-samples",
        "options",
    ),
    Input(
        "global-filters",
        "data",
    ),
)
def update_sample_options(
        filters,
):
    filters = filters or []

    filtered = apply_filters(
        gsa_df,
        filters,
    )

    sample_ids = sorted(
        filtered["GSA_ID"]
        .dropna()
        .astype(str)
        .unique()
    )

    return [
        {
            "label": sample,
            "value": sample,
        }
        for sample in sample_ids
    ]


@app.callback(
    Output("selected-count", "children"),
    Input("global-samples", "value"),
)
def update_selected_count(selected_samples):
    count = len(selected_samples) if selected_samples else 0

    return f"Selected Samples: {count}"


@app.callback(
    Output(
        {
            "type": "panel-selected-count",
            "index": MATCH,
        },
        "children",
    ),
    Input(
        "panel-store",
        "data",
    ),
    Input(
        "global-samples",
        "value",
    ),
    State(
        {
            "type": "panel-selected-count",
            "index": MATCH,
        },
        "id",
    ),
)
def update_panel_selected_count(
        panel_data,
        global_samples,
        component_id,
):
    if (
            not panel_data
            or component_id is None
    ):
        raise PreventUpdate

    panel_id = component_id[
        "index"
    ]

    panel = next(
        (
            candidate
            for candidate
            in panel_data
            if candidate.get(
                "id"
            ) == panel_id
        ),
        None,
    )

    if panel is None:
        raise PreventUpdate

    samples = get_panel_samples(
        panel,
        global_samples,
        gsa_df,
    )

    source = (
        "Global"
        if panel.get(
            "use_global",
            True,
        )
        else "Panel"
    )

    return (
        f"{source} Selection: "
        f"{len(samples)} samples"
    )


@app.callback(
    Output(
        "global-filter-field",
        "options",
    ),
    Input(
        "global-filters",
        "data",
    ),
)
def load_filter_fields(_):
    fields = {}

    fields.update(FILTER_FIELDS)
    fields.update(NUMERIC_FIELDS)

    return [
        {
            "label": label,
            "value": field,
        }
        for field, label
        in fields.items()
    ]


@app.callback(
    Output(
        "global-filter-operator",
        "options",
    ),
    Input(
        "global-filter-field",
        "value",
    ),
)
def update_operator_options(
        field,
):
    if field in NUMERIC_FIELDS:
        return [
            {"label": "=", "value": "="},
            {"label": "!=", "value": "!="},
            {"label": "<", "value": "<"},
            {"label": "<=", "value": "<="},
            {"label": ">", "value": ">"},
            {"label": ">=", "value": ">="},
            {"label": "BETWEEN", "value": "BETWEEN"},
        ]

    return [
        {"label": "IN", "value": "IN"},
        {"label": "NOT IN", "value": "NOT IN"},
        {"label": "CONTAINS", "value": "CONTAINS"},
    ]


@app.callback(
    Output(
        "global-filter-dropdown",
        "options",
        allow_duplicate=True,
    ),
    Input(
        "global-filter-field",
        "value",
    ),
    State(
        "global-filter-operator",
        "value",
    ),
    prevent_initial_call=True,
)
def update_filter_values(
        field,
        operator,
):
    if operator == "CONTAINS":
        raise PreventUpdate

    if (
            field is None
            or field not in filter_options
    ):
        return []

    return filter_options[field]


@app.callback(
    Output(
        "pending-global-filters",
        "data",
    ),
    Input(
        "add-global-filter",
        "n_clicks",
    ),
    Input(
        "clear-global-filter",
        "n_clicks",
    ),
    State(
        "pending-global-filters",
        "data",
    ),
    State(
        "global-filter-field",
        "value",
    ),
    State(
        "global-filter-operator",
        "value",
    ),
    State(
        "global-filter-dropdown",
        "value",
    ),
    State(
        "global-filter-text",
        "value",
    ),
    State(
        "global-filter-number",
        "value",
    ),
    State(
        "global-filter-min",
        "value",
    ),
    State(
        "global-filter-max",
        "value",
    ),
    prevent_initial_call=True,
)
def update_global_filters(
        add_clicks,
        clear_clicks,
        filters,
        field,
        operator,
        dropdown_value,
        text_value,
        number_value,
        minimum_value,
        maximum_value,
):
    trigger = (
        callback_context
        .triggered_id
    )

    filters = (
            filters or []
    )

    if operator == "CONTAINS":

        value = text_value

    elif field in NUMERIC_FIELDS:

        if operator == "BETWEEN":

            value = [
                minimum_value,
                maximum_value,
            ]

        else:

            value = number_value

    else:

        value = dropdown_value

    if trigger != "add-global-filter":
        raise PreventUpdate

    if field is None:
        raise PreventUpdate

    if operator == "BETWEEN":

        if (
                value[0] is None
                or value[1] is None
        ):
            raise PreventUpdate

    elif value in [
        None,
        [],
        "",
    ]:
        raise PreventUpdate

    new_clause = {
        "field": field,
        "operator": operator,
        "value": value,
        "logic": (
            "AND"
            if filters
            else None
        )
    }

    for existing in filters:

        existing_value = existing["value"]

        if isinstance(existing_value, list):
            existing_value = sorted(existing_value)

        compare_value = value

        if isinstance(compare_value, list):
            compare_value = sorted(compare_value)

        if (
                existing["field"] == field
                and existing["operator"] == operator
                and existing_value == compare_value
        ):
            raise PreventUpdate

    new_filters = filters.copy()
    new_filters.append(new_clause)

    return new_filters


@app.callback(
    Output(
        "global-filters",
        "data",
        allow_duplicate=True,
    ),
    Output(
        "pending-global-filters",
        "data",
        allow_duplicate=True,
    ),
    Input(
        "clear-global-filter",
        "n_clicks",
    ),
    prevent_initial_call=True,
)
def clear_global_filters(
        n_clicks,
):
    return [], []


@app.callback(
    Output(
        "global-filter-list",
        "children",
    ),
    Input(
        "pending-global-filters",
        "data",
    ),
)
def show_filter_list(
        filters,
):
    if not filters:
        return []

    rows = []

    for i, clause in enumerate(filters):

        if (
                clause["operator"] == "BETWEEN"
        ):
            values = (
                f"{clause['value'][0]} "
                f"and "
                f"{clause['value'][1]}"
            )

        elif isinstance(
                clause["value"],
                list,
        ):
            if isinstance(clause["value"], list):

                if len(clause["value"]) <= 5:

                    values = ", ".join(
                        map(str, clause["value"])
                    )

                else:

                    values = (
                            ", ".join(
                                map(
                                    str,
                                    clause["value"][:5]
                                )
                            )
                            + f" ... ({len(clause['value'])} selected)"
                    )

            if len(values) > 100:
                values = values[:100] + "..."
        else:
            values = str(
                clause["value"]
            )

        field_name = FILTER_FIELDS.get(
            clause["field"],
            clause["field"],
        )

        rows.append(
            html.Div(
                [
                    html.Div(
                        [

                            html.Div(
                                dcc.Dropdown(
                                    id={
                                        "type": "filter-logic",
                                        "index": i,
                                    },
                                    options=[
                                        {
                                            "label": "AND",
                                            "value": "AND",
                                        },
                                        {
                                            "label": "OR",
                                            "value": "OR",
                                        },
                                    ],
                                    value=clause.get(
                                        "logic",
                                        "AND",
                                    ),
                                    clearable=False,
                                    style={
                                        "width": "90px",
                                    },
                                ),
                                style={
                                    "marginBottom": "5px",
                                    "display":
                                        "none"
                                        if i == 0
                                        else "block",
                                },
                            ),

                            html.Span(
                                f"{i + 1}. "
                                f"{field_name} "
                                f"{clause['operator']} "
                                f"{values}"
                            ),

                        ],
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                            "flex": 1,
                        },
                    ),

                    html.Button(
                        "✕",
                        id={
                            "type": "remove-global-filter",
                            "index": i,
                        },
                        n_clicks=0,
                        style={
                            "marginLeft": "10px",
                            "padding": "0px 6px",
                            "height": "24px",
                            "lineHeight": "20px",
                            "color": "red",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "marginBottom": "5px",
                },
            )
        )

    return rows


@app.callback(
    Output(
        "pending-global-filters",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "remove-global-filter",
            "index": ALL,
        },
        "n_clicks",
    ),
    State(
        "pending-global-filters",
        "data",
    ),
    prevent_initial_call=True,
)
def remove_global_filter(
        clicks,
        filters,
):
    if not any(clicks):
        raise PreventUpdate

    trigger = callback_context.triggered_id

    if (
            trigger is None
            or not filters
    ):
        raise PreventUpdate

    index = trigger["index"]

    new_filters = filters.copy()

    new_filters.pop(index)

    return new_filters


@app.callback(
    Output(
        "pending-global-filters",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "filter-logic",
            "index": ALL,
        },
        "value",
    ),
    State(
        "pending-global-filters",
        "data",
    ),
    prevent_initial_call=True,
)
def update_filter_logic(
        logic_values,
        filters,
):
    if (
            not filters
            or len(filters)
            != len(logic_values)
    ):
        raise PreventUpdate

    new_filters = copy.deepcopy(
        filters
    )

    for i, value in enumerate(
            logic_values
    ):
        if i == 0:
            continue

        new_filters[i]["logic"] = value

    return new_filters


@app.callback(
    Output(
        "global-filters",
        "data",
        allow_duplicate=True,
    ),
    Input(
        "apply-global-filter",
        "n_clicks",
    ),
    State(
        "pending-global-filters",
        "data",
    ),
    prevent_initial_call=True,
)
def apply_global_filters(
        n_clicks,
        filters,
):
    return filters or []


@app.callback(
    Output(
        "global-samples",
        "value",
        allow_duplicate=True,
    ),
    Input(
        "global-samples",
        "options",
    ),
    State(
        "global-filters",
        "data",
    ),
    prevent_initial_call=True,
)
def auto_select_filtered(
        options,
        filters,
):
    if not filters:
        return []

    return [
        option["value"]
        for option in (
                options or []
        )
    ]


@app.callback(
    Output("global-samples", "value"),
    [
        Input("clear-selection", "n_clicks"),
    ],
    State("global-samples", "options"),
    prevent_initial_call=True,
)
def modify_sample_selection(
        clear_clicks,
        sample_options,
):
    trigger = callback_context.triggered[0]["prop_id"].split(".")[0]

    if trigger == "clear-selection":
        return []

    raise PreventUpdate


@app.callback(
    Output(
        "global-filter-dropdown",
        "style",
    ),
    Output(
        "global-filter-text",
        "style",
    ),
    Output(
        "global-filter-number",
        "style",
    ),
    Output(
        "global-filter-between",
        "style",
    ),
    Input(
        "global-filter-field",
        "value",
    ),
    Input(
        "global-filter-operator",
        "value",
    ),
)
def toggle_filter_inputs(
        field,
        operator,
):
    if field in NUMERIC_FIELDS:

        if operator == "BETWEEN":
            return (
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
                {
                    "display": "flex",
                    "justifyContent": "space-between",
                },
            )

        return (
            {"display": "none"},
            {"display": "none"},
            {"width": "100%"},
            {"display": "none"},
        )

    if operator == "CONTAINS":
        return (
            {"display": "none"},
            {"width": "100%"},
            {"display": "none"},
            {"display": "none"},
        )

    return (
        {"width": "100%"},
        {"display": "none"},
        {"display": "none"},
        {"display": "none"},
    )


@app.callback(
    Output("panel-container", "children"),
    Input("panel-applied-store", "data"),
    Input("panel-reset-revision", "data"),
)
def render_panels(
        panel_data,
        _reset_revision,
):
    panels = []

    for display_number, panel in enumerate(panel_data, start=1):
        panels.append(
            create_panel(
                panel,
                display_number,
                group_by_options,
            )
        )

    return panels


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Output(
        "panel-applied-store",
        "data",
        allow_duplicate=True,
    ),
    Input("add-panel", "n_clicks"),
    State("panel-store", "data"),
    State("panel-applied-store", "data"),
    prevent_initial_call=True,
)
def add_panel(
        n_clicks,
        panel_data,
        applied_data,
):
    if not n_clicks:
        raise PreventUpdate

    panel_data = panel_data or []
    applied_data = applied_data or []

    if max(
            len(panel_data),
            len(applied_data),
    ) >= 8:
        raise PreventUpdate

    existing_ids = [
        panel["id"]
        for panel in (
            list(panel_data)
            + list(applied_data)
        )
    ]

    next_id = max(
        existing_ids,
        default=0,
    ) + 1

    new_panel = {
        "id": next_id,
        "chart_type": "PSD Undersize",
        "use_global": True,

        "show_legend": True,
        "show_labels": False,
        "show_samples": True,
        "show_mean": False,
        "show_grainlog_mean": False,
        "grainlog_sort_field": "None",
        "grainlog_sort_ascending": True,
        "group_by": "None",
        "show_std1": False,
        "show_std2": False,
        "show_std3": False,
        "show_centroids": False,
        "show_covariance": False,

        "analysis_variables": [],
        "analysis_standardize": True,
        "mastersizer_pca_input": "frequency",

        "cluster_linkage": "ward",
        "cluster_metric": "euclidean",
        "cluster_k": 4,

        "pca_color_mode": "group",
        "show_loading_arrows": False,
        "show_depth_borehole": True,
        "pca_report_sections": [
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
        "borehole_vertical_axis": "depth",
        "pca_vertical_x_field": "BoreholeID",
        "hierarchy_summary_stats": [
            "n",
            "median",
        ],
        "hierarchy_summary_variables": [],

        "x_axis": "log",

        "show_break_2": False,
        "show_break_4": False,
        "show_break_8": True,
        "show_break_50": False,
        "show_break_62_5": True,

        "mastersizer_break": 8,
        "mastersizer_sand_break": 62.5,
        "pipette_break": 2,

        "grainlog_gravel_settings": {
            "Mastersizer": False,
            "Pipette": True,
            "Kehew": True,
            "Dry Sieve": True,
        },

        "show_usda_triangle": True,

        "panel_filters": [],
        "pending_panel_filters": [],
        "pending_custom_groups": [],
        "custom_group_builder_open": False,

        "use_custom_groups": False,
        "custom_groups": [],

        "graph_options_open": True,
        "override_options_open": False,
        "controls_open": True,
    }

    panel_patch = Patch()
    panel_patch.append(
        copy.deepcopy(new_panel)
    )

    applied_patch = Patch()
    applied_patch.append(
        copy.deepcopy(new_panel)
    )

    return panel_patch, applied_patch


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Output(
        "panel-applied-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "remove-panel",
            "index": MATCH,
        },
        "n_clicks",
    ),
    State(
        {
            "type": "remove-panel",
            "index": MATCH,
        },
        "id",
    ),
    State("panel-store", "data"),
    State("panel-applied-store", "data"),
    prevent_initial_call=True,
)
def remove_panel(
        n_clicks,
        component_id,
        panel_data,
        applied_data,
):
    if not n_clicks or component_id is None:
        raise PreventUpdate

    panel_data = panel_data or []
    applied_data = applied_data or []

    if len(applied_data) <= 1:
        raise PreventUpdate

    panel_id = component_id["index"]

    panel_index = _find_panel_index(
        panel_data,
        panel_id,
    )
    applied_index = _find_panel_index(
        applied_data,
        panel_id,
    )

    if panel_index is None or applied_index is None:
        raise PreventUpdate

    panel_patch = Patch()
    del panel_patch[panel_index]

    applied_patch = Patch()
    del applied_patch[applied_index]

    return panel_patch, applied_patch


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Output(
        "panel-applied-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "duplicate-panel",
            "index": MATCH,
        },
        "n_clicks",
    ),
    State(
        {
            "type": "duplicate-panel",
            "index": MATCH,
        },
        "id",
    ),
    State("panel-store", "data"),
    State("panel-applied-store", "data"),
    prevent_initial_call=True,
)
def duplicate_panel(
        n_clicks,
        component_id,
        panel_data,
        applied_data,
):
    if not n_clicks or component_id is None:
        raise PreventUpdate

    panel_data = panel_data or []
    applied_data = applied_data or []

    if max(
            len(panel_data),
            len(applied_data),
    ) >= 8:
        raise PreventUpdate

    panel_id = component_id["index"]

    original = next(
        (
            panel
            for panel in applied_data
            if panel.get("id") == panel_id
        ),
        None,
    )

    if original is None:
        raise PreventUpdate

    existing_ids = [
        panel["id"]
        for panel in (
            list(panel_data)
            + list(applied_data)
        )
    ]

    next_id = max(
        existing_ids,
        default=0,
    ) + 1

    new_panel = copy.deepcopy(original)
    new_panel["id"] = next_id

    panel_patch = Patch()
    panel_patch.append(
        copy.deepcopy(new_panel)
    )

    applied_patch = Patch()
    applied_patch.append(
        copy.deepcopy(new_panel)
    )

    return panel_patch, applied_patch


@app.callback(
    Output(
        {
            "type": "panel-query-builder-container",
            "index": MATCH,
        },
        "style",
    ),
    Input(
        {
            "type": "use-global",
            "index": MATCH,
        },
        "value",
    ),
)
def show_hide_panel_query_builder(
        use_global_value,
):
    if "global" in (use_global_value or []):
        return {
            "display": "none",
        }

    return {
        "display": "block",
    }


@app.callback(
    Output(
        {
            "type": "panel-filter-operator",
            "index": MATCH,
        },
        "options",
    ),
    Input(
        {
            "type": "panel-filter-field",
            "index": MATCH,
        },
        "value",
    ),
)
def update_panel_operator_options(
        field,
):
    if field in NUMERIC_FIELDS:
        return [
            {"label": "=", "value": "="},
            {"label": "!=", "value": "!="},
            {"label": "<", "value": "<"},
            {"label": "<=", "value": "<="},
            {"label": ">", "value": ">"},
            {"label": ">=", "value": ">="},
            {"label": "BETWEEN", "value": "BETWEEN"},
        ]

    return [
        {"label": "IN", "value": "IN"},
        {"label": "NOT IN", "value": "NOT IN"},
        {"label": "CONTAINS", "value": "CONTAINS"},
    ]


@app.callback(
    Output(
        {
            "type": "panel-filter-dropdown",
            "index": MATCH,
        },
        "options",
    ),
    Input(
        {
            "type": "panel-filter-field",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "panel-filter-operator",
            "index": MATCH,
        },
        "value",
    ),
)
def update_panel_filter_values(
        field,
        operator,
):
    if operator == "CONTAINS":
        return []

    if (
            field is None
            or field not in filter_options
    ):
        return []

    return filter_options[field]


@app.callback(
    Output(
        {
            "type": "panel-filter-dropdown",
            "index": MATCH,
        },
        "style",
    ),
    Output(
        {
            "type": "panel-filter-text",
            "index": MATCH,
        },
        "style",
    ),
    Output(
        {
            "type": "panel-filter-number",
            "index": MATCH,
        },
        "style",
    ),
    Output(
        {
            "type": "panel-filter-between",
            "index": MATCH,
        },
        "style",
    ),
    Input(
        {
            "type": "panel-filter-field",
            "index": MATCH,
        },
        "value",
    ),
    Input(
        {
            "type": "panel-filter-operator",
            "index": MATCH,
        },
        "value",
    ),
)
def toggle_panel_filter_inputs(
        field,
        operator,
):
    if field in NUMERIC_FIELDS:

        if operator == "BETWEEN":
            return (
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
                {
                    "display": "flex",
                    "justifyContent": "space-between",
                },
            )

        return (
            {"display": "none"},
            {"display": "none"},
            {"width": "100%"},
            {"display": "none"},
        )

    if operator == "CONTAINS":
        return (
            {"display": "none"},
            {"width": "100%"},
            {"display": "none"},
            {"display": "none"},
        )

    return (
        {"width": "100%"},
        {"display": "none"},
        {"display": "none"},
        {"display": "none"},
    )


@app.callback(
    Output(
        {
            "type": "custom-group-filter-operator",
            "panel": MATCH,
            "group": MATCH,
        },
        "options",
    ),
    Input(
        {
            "type": "custom-group-filter-field",
            "panel": MATCH,
            "group": MATCH,
        },
        "value",
    ),
)
def update_custom_group_operator_options(
        field,
):
    if field in NUMERIC_FIELDS:
        return [
            {"label": "=", "value": "="},
            {"label": "!=", "value": "!="},
            {"label": "<", "value": "<"},
            {"label": "<=", "value": "<="},
            {"label": ">", "value": ">"},
            {"label": ">=", "value": ">="},
            {"label": "BETWEEN", "value": "BETWEEN"},
        ]

    return [
        {"label": "IN", "value": "IN"},
        {"label": "NOT IN", "value": "NOT IN"},
        {"label": "CONTAINS", "value": "CONTAINS"},
    ]


@app.callback(
    Output(
        {
            "type": "custom-group-filter-dropdown",
            "panel": MATCH,
            "group": MATCH,
        },
        "options",
    ),
    Input(
        {
            "type": "custom-group-filter-field",
            "panel": MATCH,
            "group": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "custom-group-filter-operator",
            "panel": MATCH,
            "group": MATCH,
        },
        "value",
    ),
)
def update_custom_group_filter_values(
        field,
        operator,
):
    if operator == "CONTAINS":
        return []

    if (
            field is None
            or field not in filter_options
    ):
        return []

    return filter_options[field]


@app.callback(
    Output(
        {
            "type": "custom-group-filter-dropdown",
            "panel": MATCH,
            "group": MATCH,
        },
        "style",
    ),
    Output(
        {
            "type": "custom-group-filter-text",
            "panel": MATCH,
            "group": MATCH,
        },
        "style",
    ),
    Output(
        {
            "type": "custom-group-filter-number",
            "panel": MATCH,
            "group": MATCH,
        },
        "style",
    ),
    Output(
        {
            "type": "custom-group-filter-between",
            "panel": MATCH,
            "group": MATCH,
        },
        "style",
    ),
    Input(
        {
            "type": "custom-group-filter-field",
            "panel": MATCH,
            "group": MATCH,
        },
        "value",
    ),
    Input(
        {
            "type": "custom-group-filter-operator",
            "panel": MATCH,
            "group": MATCH,
        },
        "value",
    ),
)
def toggle_custom_group_filter_inputs(
        field,
        operator,
):
    if field in NUMERIC_FIELDS:

        if operator == "BETWEEN":
            return (
                {"display": "none"},
                {"display": "none"},
                {"display": "none"},
                {
                    "display": "flex",
                    "justifyContent": "space-between",
                },
            )

        return (
            {"display": "none"},
            {"display": "none"},
            {"width": "100%"},
            {"display": "none"},
        )

    if operator == "CONTAINS":
        return (
            {"display": "none"},
            {"width": "100%"},
            {"display": "none"},
            {"display": "none"},
        )

    return (
        {"width": "100%"},
        {"display": "none"},
        {"display": "none"},
        {"display": "none"},
    )


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "add-panel-filter",
            "index": MATCH,
        },
        "n_clicks",
    ),
    State(
        "panel-store",
        "data",
    ),
    State(
        {
            "type": "panel-filter-field",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "panel-filter-operator",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "panel-filter-dropdown",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "panel-filter-text",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "panel-filter-number",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "panel-filter-min",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "panel-filter-max",
            "index": MATCH,
        },
        "value",
    ),
    prevent_initial_call=True,
)
def add_panel_filter(
        n_clicks,
        panel_data,
        field,
        operator,
        dropdown_value,
        text_value,
        number_value,
        minimum_value,
        maximum_value,
):
    if not n_clicks:
        raise PreventUpdate

    trigger = callback_context.triggered_id

    if trigger is None:
        raise PreventUpdate

    panel_id = trigger["index"]
    panel_index, panel = _get_panel_copy(
        panel_data,
        panel_id,
    )

    if panel is None:
        raise PreventUpdate

    filters = copy.deepcopy(
        panel.get(
            "pending_panel_filters",
            [],
        )
    )

    if operator == "CONTAINS":
        value = text_value

    elif field in NUMERIC_FIELDS:
        if operator == "BETWEEN":
            value = [
                minimum_value,
                maximum_value,
            ]
        else:
            value = number_value

    else:
        value = dropdown_value

    if field is None:
        raise PreventUpdate

    if operator == "BETWEEN":
        if (
                value[0] is None
                or value[1] is None
        ):
            raise PreventUpdate

    elif value in [
        None,
        [],
        "",
    ]:
        raise PreventUpdate

    filters.append(
        {
            "field": field,
            "operator": operator,
            "value": value,
            "logic": (
                "AND"
                if filters
                else None
            ),
        }
    )

    panel["pending_panel_filters"] = filters

    patch = Patch()
    patch[panel_index] = panel
    return patch


@app.callback(
    Output(
        {
            "type": "panel-filter-list",
            "index": MATCH,
        },
        "children",
    ),
    Input(
        "panel-store",
        "data",
    ),
    State(
        {
            "type": "panel-filter-list",
            "index": MATCH,
        },
        "id",
    ),
)
def show_panel_filter_list(
        panel_data,
        component_id,
):
    panel_id = component_id["index"]

    panel = next(
        (
            p
            for p in panel_data
            if p["id"] == panel_id
        ),
        None,
    )

    if panel is None:
        raise PreventUpdate

    filters = panel.get(
        "pending_panel_filters",
        [],
    )

    if not filters:
        return []

    rows = []

    for i, clause in enumerate(filters):

        if clause["operator"] == "BETWEEN":

            values = (
                f"{clause['value'][0]}"
                f" and "
                f"{clause['value'][1]}"
            )

        elif isinstance(
                clause["value"],
                list,
        ):
            if isinstance(clause["value"], list):

                if len(clause["value"]) <= 5:

                    values = ", ".join(
                        map(str, clause["value"])
                    )

                else:

                    values = (
                            ", ".join(
                                map(
                                    str,
                                    clause["value"][:5]
                                )
                            )
                            + f" ... ({len(clause['value'])} selected)"
                    )

        else:
            values = str(
                clause["value"]
            )

        field_name = (
                FILTER_FIELDS.get(
                    clause["field"],
                    clause["field"],
                )
                or
                NUMERIC_FIELDS.get(
                    clause["field"],
                    clause["field"],
                )
        )

        rows.append(
            html.Div(
                [
                    html.Div(
                        [

                            html.Div(
                                dcc.Dropdown(
                                    id={
                                        "type": "panel-filter-logic",
                                        "index": i,
                                        "panel": panel_id,
                                    },
                                    options=[
                                        {
                                            "label": "AND",
                                            "value": "AND",
                                        },
                                        {
                                            "label": "OR",
                                            "value": "OR",
                                        },
                                    ],
                                    value=clause.get(
                                        "logic",
                                        "AND",
                                    ),
                                    clearable=False,
                                    style={
                                        "width": "90px",
                                    },
                                ),
                                style={
                                    "display":
                                        "none"
                                        if i == 0
                                        else "block",
                                    "marginBottom": "5px",
                                },
                            ),

                            html.Span(
                                f"{i + 1}. "
                                f"{field_name} "
                                f"{clause['operator']} "
                                f"{values}"
                            ),
                        ],
                        style={
                            "display": "flex",
                            "flexDirection": "column",
                            "flex": 1,
                        },
                    ),

                    html.Button(
                        "✕",
                        id={
                            "type": "remove-panel-filter",
                            "index": i,
                            "panel": panel_id,
                        },
                        n_clicks=0,
                        style={
                            "marginLeft": "10px",
                            "padding": "0px 6px",
                            "height": "24px",
                            "lineHeight": "20px",
                            "color": "red",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "marginBottom": "5px",
                },
            )
        )

    return rows


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "remove-panel-filter",
            "index": MATCH,
            "panel": MATCH,
        },
        "n_clicks",
    ),
    State(
        {
            "type": "remove-panel-filter",
            "index": MATCH,
            "panel": MATCH,
        },
        "id",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def remove_panel_filter(
        n_clicks,
        component_id,
        panel_data,
):
    if not n_clicks or component_id is None:
        raise PreventUpdate

    clause_index = component_id["index"]
    panel_id = component_id["panel"]

    panel_index, panel = _get_panel_copy(
        panel_data,
        panel_id,
    )

    if panel is None:
        raise PreventUpdate

    filters = copy.deepcopy(
        panel.get(
            "pending_panel_filters",
            [],
        )
    )

    if clause_index >= len(filters):
        raise PreventUpdate

    filters.pop(clause_index)
    panel["pending_panel_filters"] = filters

    patch = Patch()
    patch[panel_index] = panel
    return patch


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "panel-filter-logic",
            "index": MATCH,
            "panel": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "panel-filter-logic",
            "index": MATCH,
            "panel": MATCH,
        },
        "id",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def update_panel_filter_logic(
        logic_value,
        component_id,
        panel_data,
):
    if component_id is None:
        raise PreventUpdate

    panel_id = component_id["panel"]
    clause_index = component_id["index"]

    if clause_index == 0:
        raise PreventUpdate

    panel_index, panel = _get_panel_copy(
        panel_data,
        panel_id,
    )

    if panel is None:
        raise PreventUpdate

    filters = copy.deepcopy(
        panel.get(
            "pending_panel_filters",
            [],
        )
    )

    if clause_index >= len(filters):
        raise PreventUpdate

    filters[clause_index]["logic"] = (
        logic_value
        or "AND"
    )
    panel["pending_panel_filters"] = filters

    patch = Patch()
    patch[panel_index] = panel
    return patch


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "apply-panel-filter",
            "index": MATCH,
        },
        "n_clicks",
    ),
    State(
        {
            "type": "apply-panel-filter",
            "index": MATCH,
        },
        "id",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def apply_panel_filter_callback(
        n_clicks,
        component_id,
        panel_data,
):
    if not n_clicks or component_id is None:
        raise PreventUpdate

    panel_id = component_id["index"]
    panel_index, panel = _get_panel_copy(
        panel_data,
        panel_id,
    )

    if panel is None:
        raise PreventUpdate

    panel["panel_filters"] = copy.deepcopy(
        panel.get(
            "pending_panel_filters",
            [],
        )
    )

    patch = Patch()
    patch[panel_index] = panel
    return patch


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "clear-panel-filter",
            "index": MATCH,
        },
        "n_clicks",
    ),
    State(
        {
            "type": "clear-panel-filter",
            "index": MATCH,
        },
        "id",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def clear_panel_filters(
        n_clicks,
        component_id,
        panel_data,
):
    if not n_clicks or component_id is None:
        raise PreventUpdate

    panel_id = component_id["index"]
    panel_index, panel = _get_panel_copy(
        panel_data,
        panel_id,
    )

    if panel is None:
        raise PreventUpdate

    panel["pending_panel_filters"] = []
    panel["panel_filters"] = []

    patch = Patch()
    patch[panel_index] = panel
    return patch


@app.callback(
    Output(
        {
            "type": "panel-content",
            "index": MATCH,
        },
        "children",
    ),
    Input(
        "panel-applied-store",
        "data",
    ),
    Input(
        "global-samples",
        "value",
    ),
    Input(
        "layout-store",
        "data",
    ),
    State(
        {
            "type": "panel-content",
            "index": MATCH,
        },
        "id",
    ),
)
def update_graph(
        panel_data,
        global_samples,
        layout_data,
        component_id,
):
    if (
            panel_data is None
            or component_id is None
    ):
        raise PreventUpdate

    panel_id = component_id[
        "index"
    ]

    panel_position = None
    panel = None

    for position, candidate in enumerate(
            panel_data
    ):

        if candidate.get(
                "id"
        ) == panel_id:

            panel_position = position
            panel = candidate.copy()
            break

    if panel is None:
        raise PreventUpdate

    global_samples = (
        global_samples
        or []
    )

    layout_lookup = {
        item["i"]: item
        for item in (
            layout_data
            or []
        )
    }

    chart_type = panel.get(
        "chart_type",
        "PSD Undersize",
    )

    # Hidden-but-always-active PCA behavior.
    if chart_type == "PCA":
        panel[
            "show_legend"
        ] = True

    if (
            chart_type
            == "PCA - Mastersizer Only"
    ):
        panel[
            "show_mean"
        ] = True

    layout = layout_lookup.get(
        str(
            panel_position
        )
    )

    if layout:
        panel[
            "layout"
        ] = layout

    panel_samples = get_panel_samples(
        panel,
        global_samples,
        gsa_df,
    )

    panel[
        "grouped_samples"
    ] = None

    if (
            panel.get(
                "use_custom_groups",
                False,
            )
            and has_custom_groups(
                panel
            )
    ):

        subset = gsa_df[
            gsa_df[
                "GSA_ID"
            ]
            .astype(str)
            .isin(
                panel_samples
            )
        ]

        panel[
            "grouped_samples"
        ] = build_custom_groups(
            panel.get(
                "custom_groups",
                [],
            ),
            subset,
        )

    if chart_type == "PSD Undersize":

        fig = make_psd_plot(
            gsa_df,
            mmes_df,
            mmes_rs_df,
            panel_samples,
            panel,
        )

    elif chart_type == "PSD Frequency":

        fig = make_frequency_plot(
            gsa_df,
            mmes_df,
            mmes_rs_df,
            panel_samples,
            panel,
        )

    elif chart_type == "Ternary":

        fig = make_ternary_plot(
            gsa_df,
            mmes_df,
            panel_samples,
            panel,
        )

    elif chart_type == "Grain Size Log":

        fig = make_grain_log(
            gsa_df,
            mmes_df,
            panel_samples,
            panel,
        )

    elif chart_type == "PCA":

        fig = make_pca_plot(
            gsa_df,
            mmes_df,
            mmes_rs_df,
            panel_samples,
            panel,
        )

    elif (
            chart_type
            == "PCA - Mastersizer Only"
    ):

        fig = make_mastersizer_pca_plot(
            gsa_df,
            mmes_df,
            mmes_rs_df,
            panel_samples,
            panel,
        )

    elif (
            chart_type
            == "Hierarchical Clustering"
    ):

        fig = make_hierarchical_plot(
            gsa_df,
            panel_samples,
            panel,
        )

    elif (
            chart_type
            == "Sample Information"
    ):

        fig = make_sample_information(
            gsa_df,
            panel_samples,
        )

    else:

        import plotly.graph_objects as go

        fig = go.Figure()

        fig.update_layout(
            title=(
                f"{chart_type} Coming Soon"
            )
        )

    if (
            chart_type
            == "Sample Information"
    ):

        return html.Div(
            fig,
            style={
                "flex": "1 1 auto",
                "height": "100%",
                "display": "flex",
                "flexDirection": "column",
                "minHeight": 0,
            },
        )

    if (
            chart_type
            == "Grain Size Log"
    ):

        return dcc.Graph(
            figure=fig,
            responsive=False,
            style={
                "width": "100%",
            },
            config={
                "responsive": True,
                "toImageButtonOptions": {
                    "format": "png",
                    "filename": (
                        f"MGS_GSA_"
                        f"{chart_type.replace(' ', '_')}"
                    ),
                    "scale": 2,
                },
            },
        )

    if chart_type in [
        "PCA",
        "PCA - Mastersizer Only",
    ]:

        return html.Div(
            fig,
            style={
                "height": "100%",
                "width": "100%",
                "overflowY": "auto",
                "overflowX": "auto",
                "minWidth": 0,
                "boxSizing": "border-box",
            },
        )

    return dcc.Graph(
        figure=fig,
        responsive=True,
        style={
            "height": "100%",
            "width": "100%",
        },
        config={
            "responsive": True,
            "toImageButtonOptions": {
                "format": "png",
                "filename": (
                    f"MGS_GSA_"
                    f"{chart_type.replace(' ', '_')}"
                ),
                "scale": 2,
            },
        },
    )


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Output(
        "panel-applied-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "chart-type",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "chart-type",
            "index": MATCH,
        },
        "id",
    ),
    State("panel-store", "data"),
    State("panel-applied-store", "data"),
    prevent_initial_call=True,
)
def update_chart_types(
        chart_type,
        component_id,
        panel_data,
        applied_data,
):
    if chart_type is None or component_id is None:
        raise PreventUpdate

    panel_id = component_id["index"]

    panel_index, panel = _get_panel_copy(
        panel_data,
        panel_id,
    )
    applied_index, applied_panel = _get_panel_copy(
        applied_data,
        panel_id,
    )

    # A dynamically-created dropdown can briefly exist before both
    # stores have completed the Add Panel update. Never let that
    # transient state replace either store.
    if panel is None or applied_panel is None:
        raise PreventUpdate

    if (
            panel.get("chart_type") == chart_type
            and applied_panel.get("chart_type") == chart_type
    ):
        raise PreventUpdate

    for target in (
            panel,
            applied_panel,
    ):
        target["chart_type"] = chart_type

        if chart_type == "PCA":
            target["show_legend"] = True

        if chart_type == "PCA - Mastersizer Only":
            target["show_mean"] = True

    panel_patch = Patch()
    panel_patch[panel_index] = panel

    applied_patch = Patch()
    applied_patch[applied_index] = applied_panel

    return panel_patch, applied_patch




@app.callback(
    Output(
        {
            "type": "custom-group-container",
            "index": MATCH,
        },
        "style",
    ),
    Input(
        {
            "type": "use-custom-groups",
            "index": MATCH,
        },
        "value",
    ),
)
def toggle_custom_groups(
        values,
):
    if "custom" in (
            values or []
    ):
        return {
            "display": "block",
            "marginTop": "10px",
        }

    return {
        "display": "none",
        "marginTop": "10px",
    }


@app.callback(
    Output(
        {
            "type": "group-by-container",
            "index": MATCH,
        },
        "style",
    ),
    Input(
        {
            "type": "use-custom-groups",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "chart-type",
            "index": MATCH,
        },
        "value",
    ),
)
def toggle_group_by_visibility(
        values,
        chart_type,
):
    supports_grouping = chart_type in [
        "PSD Undersize",
        "PSD Frequency",
        "Grain Size Log",
        "Ternary",
        "PCA",
        "PCA - Mastersizer Only",
    ]

    if not supports_grouping:
        return {
            "display": "none",
        }

    if "custom" in (values or []):
        return {
            "display": "none",
        }

    return {
        "display": "block",
    }


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "add-custom-group",
            "index": MATCH,
        },
        "n_clicks",
    ),
    State(
        {
            "type": "add-custom-group",
            "index": MATCH,
        },
        "id",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def add_custom_group(
        n_clicks,
        component_id,
        panel_data,
):
    if not n_clicks or component_id is None:
        raise PreventUpdate

    panel_id = component_id["index"]
    panel_index, panel = _get_panel_copy(
        panel_data,
        panel_id,
    )

    if panel is None:
        raise PreventUpdate

    groups = copy.deepcopy(
        panel.get(
            "custom_groups",
            [],
        )
    )

    if len(groups) >= 20:
        raise PreventUpdate

    groups.append(
        {
            "name": f"Group {len(groups) + 1}",
            "filters": [],
            "pending_filters": [],
        }
    )

    panel["custom_groups"] = groups

    patch = Patch()
    patch[panel_index] = panel
    return patch


def _build_custom_group_filter_rows(
        panel_id,
        group_index,
        filters,
):
    rows = []

    for i, clause in enumerate(
            filters
            or []
    ):

        if (
                clause["operator"]
                == "BETWEEN"
        ):

            values = (
                f"{clause['value'][0]}"
                f" and "
                f"{clause['value'][1]}"
            )

        elif isinstance(
                clause["value"],
                list,
        ):

            values = ", ".join(
                map(
                    str,
                    clause["value"],
                )
            )

        else:

            values = str(
                clause["value"]
            )

        field_name = (
                FILTER_FIELDS.get(
                    clause["field"],
                    clause["field"],
                )
                or
                NUMERIC_FIELDS.get(
                    clause["field"],
                    clause["field"],
                )
        )

        rows.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                dcc.Dropdown(
                                    id={
                                        "type":
                                            "custom-group-filter-logic",
                                        "panel":
                                            panel_id,
                                        "group":
                                            group_index,
                                        "index":
                                            i,
                                    },
                                    options=[
                                        {
                                            "label":
                                                "AND",
                                            "value":
                                                "AND",
                                        },
                                        {
                                            "label":
                                                "OR",
                                            "value":
                                                "OR",
                                        },
                                    ],
                                    value=clause.get(
                                        "logic",
                                        "AND",
                                    ),
                                    clearable=False,
                                    style={
                                        "width":
                                            "90px",
                                    },
                                ),
                                style={
                                    "display":
                                        "none"
                                        if i == 0
                                        else "block",
                                },
                            ),

                            html.Span(
                                f"{i + 1}. "
                                f"{field_name} "
                                f"{clause['operator']} "
                                f"{values}"
                            ),
                        ],
                        style={
                            "display":
                                "flex",
                            "flexDirection":
                                "column",
                            "flex":
                                1,
                        },
                    ),

                    html.Button(
                        "✕",
                        id={
                            "type":
                                "remove-custom-group-filter",
                            "panel":
                                panel_id,
                            "group":
                                group_index,
                            "index":
                                i,
                        },
                        n_clicks=0,
                        style={
                            "marginLeft":
                                "10px",
                            "color":
                                "red",
                        },
                    ),
                ],
                style={
                    "display":
                        "flex",
                    "alignItems":
                        "center",
                    "marginBottom":
                        "5px",
                },
            )
        )

    return rows


@app.callback(
    Output(
        {
            "type": "custom-group-list",
            "index": MATCH,
        },
        "children",
    ),
    Input(
        "panel-store",
        "data",
    ),
    State(
        {
            "type": "custom-group-list",
            "index": MATCH,
        },
        "id",
    ),
)
def render_custom_groups(
        panel_data,
        component_id,
):
    panel_id = component_id["index"]

    panel = next(
        (
            p
            for p in panel_data
            if p["id"] == panel_id
        ),
        None,
    )

    if panel is None:
        raise PreventUpdate

    groups = panel.get(
        "custom_groups",
        [],
    )

    children = []

    for i, group in enumerate(
            groups
    ):
        children.append(
            html.Div(
                [

                    dcc.Input(
                        id={
                            "type":
                                "custom-group-name",
                            "panel":
                                panel_id,
                            "group":
                                i,
                        },
                        value=group["name"],
                        style={
                            "width": "100%",
                            "fontWeight": "bold",
                            "marginBottom": "10px",
                        },
                    ),

                    html.Label("Field"),

                    dcc.Dropdown(
                        id={
                            "type":
                                "custom-group-filter-field",
                            "panel":
                                panel_id,
                            "group":
                                i,
                        },
                        options=[
                            {
                                "label": label,
                                "value": field,
                            }
                            for field, label
                            in (
                                    GROUP_BY_FIELDS
                                    |
                                    NUMERIC_FIELDS
                            ).items()
                        ],
                    ),

                    html.Br(),

                    html.Label("Operator"),

                    dcc.Dropdown(
                        id={
                            "type":
                                "custom-group-filter-operator",
                            "panel":
                                panel_id,
                            "group":
                                i,
                        },
                        value="IN",
                        clearable=False,
                    ),

                    html.Br(),

                    html.Label("Value"),

                    dcc.Dropdown(
                        id={
                            "type":
                                "custom-group-filter-dropdown",
                            "panel":
                                panel_id,
                            "group":
                                i,
                        },
                        multi=True,
                    ),

                    dcc.Input(
                        id={
                            "type":
                                "custom-group-filter-text",
                            "panel":
                                panel_id,
                            "group":
                                i,
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
                            "type":
                                "custom-group-filter-number",
                            "panel":
                                panel_id,
                            "group":
                                i,
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
                                    "type":
                                        "custom-group-filter-min",
                                    "panel":
                                        panel_id,
                                    "group":
                                        i,
                                },
                                type="number",
                                placeholder="Minimum",
                                style={
                                    "width": "48%",
                                },
                            ),

                            dcc.Input(
                                id={
                                    "type":
                                        "custom-group-filter-max",
                                    "panel":
                                        panel_id,
                                    "group":
                                        i,
                                },
                                type="number",
                                placeholder="Maximum",
                                style={
                                    "width": "48%",
                                },
                            ),
                        ],
                        id={
                            "type":
                                "custom-group-filter-between",
                            "panel":
                                panel_id,
                            "group":
                                i,
                        },
                        style={
                            "display": "none",
                            "justifyContent":
                                "space-between",
                        },
                    ),

                    html.Br(),

                    html.Button(
                        "Add Clause",
                        id={
                            "type":
                                "add-custom-group-filter",
                            "panel":
                                panel_id,
                            "group":
                                i,
                        },
                    ),

                    html.Br(),
                    html.Br(),

                    html.Button(
                        "Apply Group",
                        id={
                            "type":
                                "apply-custom-group-filter",
                            "panel":
                                panel_id,
                            "group":
                                i,
                        },
                    ),

                    html.Button(
                        "Clear Group",
                        id={
                            "type":
                                "clear-custom-group-filter",
                            "panel":
                                panel_id,
                            "group":
                                i,
                        },
                        style={
                            "marginLeft": "10px",
                        },
                    ),

                    html.Button(
                        "Remove Group",
                        id={
                            "type":
                                "remove-custom-group",
                            "panel":
                                panel_id,
                            "group":
                                i,
                        },
                        style={
                            "marginLeft": "10px",
                            "color": "red",
                        },
                    ),

                    html.Div(
                        id={
                            "type":
                                "custom-group-filter-list",
                            "panel":
                                panel_id,
                            "group":
                                i,
                        },
                        children=(
                            _build_custom_group_filter_rows(
                                panel_id,
                                i,
                                group.get(
                                    "pending_filters",
                                    [],
                                ),
                            )
                        ),
                        style={
                            "marginTop": "10px",
                        },
                    ),
                ],
                style={
                    "border":
                        "1px solid #ccc",
                    "padding":
                        "10px",
                    "marginTop":
                        "10px",
                },
            )
        )

    return children


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "add-custom-group-filter",
            "panel": MATCH,
            "group": MATCH,
        },
        "n_clicks",
    ),
    State(
        "panel-store",
        "data",
    ),
    State(
        {
            "type": "custom-group-filter-field",
            "panel": MATCH,
            "group": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "custom-group-filter-operator",
            "panel": MATCH,
            "group": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "custom-group-filter-dropdown",
            "panel": MATCH,
            "group": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "custom-group-filter-text",
            "panel": MATCH,
            "group": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "custom-group-filter-number",
            "panel": MATCH,
            "group": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "custom-group-filter-min",
            "panel": MATCH,
            "group": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "custom-group-filter-max",
            "panel": MATCH,
            "group": MATCH,
        },
        "value",
    ),
    prevent_initial_call=True,
)
def add_custom_group_filter(
        n_clicks,
        panel_data,
        field,
        operator,
        dropdown_value,
        text_value,
        number_value,
        minimum_value,
        maximum_value,
):
    if not n_clicks:
        raise PreventUpdate

    trigger = callback_context.triggered_id

    if trigger is None:
        raise PreventUpdate

    panel_id = trigger["panel"]
    group_index = trigger["group"]

    panel_index, panel = _get_panel_copy(
        panel_data,
        panel_id,
    )

    if panel is None:
        raise PreventUpdate

    groups = copy.deepcopy(
        panel.get(
            "custom_groups",
            [],
        )
    )

    if group_index >= len(groups):
        raise PreventUpdate

    filters = copy.deepcopy(
        groups[group_index].get(
            "pending_filters",
            [],
        )
    )

    if operator == "CONTAINS":
        value = text_value

    elif field in NUMERIC_FIELDS:
        if operator == "BETWEEN":
            value = [
                minimum_value,
                maximum_value,
            ]
        else:
            value = number_value

    else:
        value = dropdown_value

    if field is None:
        raise PreventUpdate

    if operator == "BETWEEN":
        if (
                value[0] is None
                or value[1] is None
        ):
            raise PreventUpdate

    elif value in [
        None,
        [],
        "",
    ]:
        raise PreventUpdate

    filters.append(
        {
            "field": field,
            "operator": operator,
            "value": value,
            "logic": (
                "AND"
                if filters
                else None
            ),
        }
    )

    groups[group_index]["pending_filters"] = filters
    panel["custom_groups"] = groups

    patch = Patch()
    patch[panel_index] = panel
    return patch




@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "remove-custom-group-filter",
            "panel": MATCH,
            "group": MATCH,
            "index": MATCH,
        },
        "n_clicks",
    ),
    State(
        {
            "type": "remove-custom-group-filter",
            "panel": MATCH,
            "group": MATCH,
            "index": MATCH,
        },
        "id",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def remove_custom_group_filter(
        n_clicks,
        component_id,
        panel_data,
):
    if not n_clicks or component_id is None:
        raise PreventUpdate

    panel_id = component_id["panel"]
    group_index = component_id["group"]
    clause_index = component_id["index"]

    panel_index, panel = _get_panel_copy(
        panel_data,
        panel_id,
    )

    if panel is None:
        raise PreventUpdate

    groups = copy.deepcopy(
        panel.get(
            "custom_groups",
            [],
        )
    )

    if group_index >= len(groups):
        raise PreventUpdate

    filters = copy.deepcopy(
        groups[group_index].get(
            "pending_filters",
            [],
        )
    )

    if clause_index >= len(filters):
        raise PreventUpdate

    filters.pop(clause_index)
    groups[group_index]["pending_filters"] = filters
    panel["custom_groups"] = groups

    patch = Patch()
    patch[panel_index] = panel
    return patch


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "custom-group-filter-logic",
            "panel": MATCH,
            "group": MATCH,
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "custom-group-filter-logic",
            "panel": MATCH,
            "group": MATCH,
            "index": MATCH,
        },
        "id",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def update_custom_group_filter_logic(
        logic_value,
        component_id,
        panel_data,
):
    if component_id is None:
        raise PreventUpdate

    panel_id = component_id["panel"]
    group_index = component_id["group"]
    clause_index = component_id["index"]

    if clause_index == 0:
        raise PreventUpdate

    panel_index, panel = _get_panel_copy(
        panel_data,
        panel_id,
    )

    if panel is None:
        raise PreventUpdate

    groups = copy.deepcopy(
        panel.get(
            "custom_groups",
            [],
        )
    )

    if group_index >= len(groups):
        raise PreventUpdate

    filters = copy.deepcopy(
        groups[group_index].get(
            "pending_filters",
            [],
        )
    )

    if clause_index >= len(filters):
        raise PreventUpdate

    filters[clause_index]["logic"] = (
        logic_value
        or "AND"
    )
    groups[group_index]["pending_filters"] = filters
    panel["custom_groups"] = groups

    patch = Patch()
    patch[panel_index] = panel
    return patch


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "apply-custom-group-filter",
            "panel": MATCH,
            "group": MATCH,
        },
        "n_clicks",
    ),
    State(
        "panel-store",
        "data",
    ),
    State(
        {
            "type": "custom-group-name",
            "panel": MATCH,
            "group": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "custom-group-name",
            "panel": MATCH,
            "group": MATCH,
        },
        "id",
    ),
    prevent_initial_call=True,
)
def apply_custom_group_filters(
        n_clicks,
        panel_data,
        group_name,
        component_id,
):
    if not n_clicks or component_id is None:
        raise PreventUpdate

    panel_id = component_id["panel"]
    group_index = component_id["group"]

    panel_index, panel = _get_panel_copy(
        panel_data,
        panel_id,
    )

    if panel is None:
        raise PreventUpdate

    groups = copy.deepcopy(
        panel.get(
            "custom_groups",
            [],
        )
    )

    if group_index >= len(groups):
        raise PreventUpdate

    group = groups[group_index]

    if (
            group_name is not None
            and str(group_name).strip()
    ):
        group["name"] = str(group_name).strip()

    group["filters"] = copy.deepcopy(
        group.get(
            "pending_filters",
            [],
        )
    )

    panel["custom_groups"] = groups

    patch = Patch()
    patch[panel_index] = panel
    return patch


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "clear-custom-group-filter",
            "panel": MATCH,
            "group": MATCH,
        },
        "n_clicks",
    ),
    State(
        {
            "type": "clear-custom-group-filter",
            "panel": MATCH,
            "group": MATCH,
        },
        "id",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def clear_custom_group_filters(
        n_clicks,
        component_id,
        panel_data,
):
    if not n_clicks or component_id is None:
        raise PreventUpdate

    panel_id = component_id["panel"]
    group_index = component_id["group"]

    panel_index, panel = _get_panel_copy(
        panel_data,
        panel_id,
    )

    if panel is None:
        raise PreventUpdate

    groups = copy.deepcopy(
        panel.get(
            "custom_groups",
            [],
        )
    )

    if group_index >= len(groups):
        raise PreventUpdate

    groups[group_index]["pending_filters"] = []
    groups[group_index]["filters"] = []
    panel["custom_groups"] = groups

    patch = Patch()
    patch[panel_index] = panel
    return patch


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "remove-custom-group",
            "panel": MATCH,
            "group": MATCH,
        },
        "n_clicks",
    ),
    State(
        {
            "type": "remove-custom-group",
            "panel": MATCH,
            "group": MATCH,
        },
        "id",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def remove_custom_group(
        n_clicks,
        component_id,
        panel_data,
):
    if not n_clicks or component_id is None:
        raise PreventUpdate

    panel_id = component_id["panel"]
    group_index = component_id["group"]

    panel_index, panel = _get_panel_copy(
        panel_data,
        panel_id,
    )

    if panel is None:
        raise PreventUpdate

    groups = copy.deepcopy(
        panel.get(
            "custom_groups",
            [],
        )
    )

    if group_index >= len(groups):
        raise PreventUpdate

    groups.pop(group_index)
    panel["custom_groups"] = groups

    patch = Patch()
    patch[panel_index] = panel
    return patch


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Output(
        "panel-applied-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "apply-panel-options",
            "index": MATCH,
        },
        "n_clicks",
    ),
    State(
        {
            "type": "apply-panel-options",
            "index": MATCH,
        },
        "id",
    ),
    State(
        {
            "type": "display-options",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "group-by",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "x-axis",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "reference-breaks",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "grainlog-sort-field",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "grainlog-sort-direction",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "grainlog-gravel",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "analysis-variables",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "analysis-standardize",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "mastersizer-pca-input",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "cluster-linkage",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "cluster-metric",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "cluster-k",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "pca-color-mode",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "show-loading-arrows",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "pca-report-sections",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "pca-vertical-x-field",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "borehole-vertical-axis",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "hierarchy-summary-stats",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "hierarchy-summary-variables",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "mastersizer-break",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "mastersizer-sand-break",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "pipette-break",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "show-usda",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "use-custom-groups",
            "index": MATCH,
        },
        "value",
    ),
    State(
        {
            "type": "use-global",
            "index": MATCH,
        },
        "value",
    ),
    State(
        "panel-store",
        "data",
    ),
    State(
        "panel-applied-store",
        "data",
    ),
    prevent_initial_call=True,
)
def apply_panel_options(
        n_clicks,
        component_id,
        display_options,
        group_by,
        x_axis,
        reference_breaks,
        grainlog_sort_field,
        grainlog_sort_direction,
        grainlog_gravel,
        analysis_variables,
        analysis_standardize,
        mastersizer_pca_input,
        cluster_linkage,
        cluster_metric,
        cluster_k,
        pca_color_mode,
        show_loading_arrows,
        pca_report_sections,
        pca_vertical_x_field,
        borehole_vertical_axis,
        hierarchy_summary_stats,
        hierarchy_summary_variables,
        mastersizer_break,
        mastersizer_sand_break,
        pipette_break,
        show_usda,
        use_custom_groups,
        use_global,
        draft_data,
        applied_data,
):
    if not n_clicks or component_id is None:
        raise PreventUpdate

    panel_id = component_id["index"]

    draft_index, panel = _get_panel_copy(
        draft_data,
        panel_id,
    )
    applied_index, applied_panel = _get_panel_copy(
        applied_data,
        panel_id,
    )

    if panel is None or applied_panel is None:
        raise PreventUpdate

    chart_type = panel.get(
        "chart_type",
        applied_panel.get(
            "chart_type",
            "PSD Undersize",
        ),
    )

    selected_display = display_options or []

    panel["show_legend"] = (
        True
        if chart_type == "PCA"
        else "legend" in selected_display
    )
    panel["show_labels"] = "labels" in selected_display
    panel["show_samples"] = "samples" in selected_display
    panel["show_mean"] = (
        True
        if chart_type == "PCA - Mastersizer Only"
        else "mean" in selected_display
    )
    panel["show_grainlog_mean"] = (
        "grainlog_mean" in selected_display
    )
    panel["show_std1"] = "std1" in selected_display
    panel["show_std2"] = "std2" in selected_display
    panel["show_std3"] = "std3" in selected_display
    panel["show_centroids"] = "centroids" in selected_display
    panel["show_covariance"] = "covariance" in selected_display

    panel["group_by"] = group_by or "None"
    panel["x_axis"] = x_axis or "log"

    selected_breaks = reference_breaks or []
    panel["show_break_2"] = "2" in selected_breaks
    panel["show_break_4"] = "4" in selected_breaks
    panel["show_break_8"] = "8" in selected_breaks
    panel["show_break_50"] = "50" in selected_breaks
    panel["show_break_62_5"] = "62.5" in selected_breaks

    panel["grainlog_sort_field"] = (
        grainlog_sort_field
        if grainlog_sort_field is not None
        else panel.get("grainlog_sort_field", "None")
    )
    panel["grainlog_sort_ascending"] = (
        (grainlog_sort_direction or "asc") == "asc"
    )

    selected_gravel = grainlog_gravel or []
    panel["grainlog_gravel_settings"] = {
        "Mastersizer": "Mastersizer" in selected_gravel,
        "Pipette": "Pipette" in selected_gravel,
        "Kehew": "Kehew" in selected_gravel,
        "Dry Sieve": "Dry Sieve" in selected_gravel,
    }

    panel["analysis_variables"] = analysis_variables or []
    panel["analysis_standardize"] = (
        "standardize" in (analysis_standardize or [])
    )
    panel["mastersizer_pca_input"] = (
        mastersizer_pca_input or "frequency"
    )
    panel["cluster_linkage"] = cluster_linkage or "ward"
    panel["cluster_metric"] = cluster_metric or "euclidean"
    panel["cluster_k"] = int(cluster_k or 4)
    panel["pca_color_mode"] = pca_color_mode or "group"
    panel["show_loading_arrows"] = (
        "arrows" in (show_loading_arrows or [])
    )
    panel["pca_report_sections"] = pca_report_sections or []
    panel["pca_vertical_x_field"] = (
        pca_vertical_x_field or "BoreholeID"
    )
    panel["borehole_vertical_axis"] = (
        borehole_vertical_axis or "depth"
    )
    panel["show_depth_borehole"] = (
        "depth" in panel["pca_report_sections"]
    )
    panel["hierarchy_summary_stats"] = (
        hierarchy_summary_stats or []
    )
    panel["hierarchy_summary_variables"] = (
        hierarchy_summary_variables or []
    )

    if panel["cluster_linkage"] == "ward":
        panel["cluster_metric"] = "euclidean"

    if mastersizer_break is not None:
        panel["mastersizer_break"] = mastersizer_break

    if mastersizer_sand_break is not None:
        panel["mastersizer_sand_break"] = mastersizer_sand_break

    if pipette_break is not None:
        panel["pipette_break"] = pipette_break

    panel["show_usda_triangle"] = (
        "usda" in (show_usda or [])
    )

    panel["use_custom_groups"] = (
        "custom" in (use_custom_groups or [])
    )

    if panel["use_custom_groups"]:
        panel["group_by"] = "None"

    panel["use_global"] = (
        "global" in (use_global or [])
    )

    # Commit exactly this one panel. Query-builder state already lives
    # in the draft panel and is preserved by using that panel as base.
    applied_panel = copy.deepcopy(panel)

    draft_patch = Patch()
    draft_patch[draft_index] = panel

    applied_patch = Patch()
    applied_patch[applied_index] = applied_panel

    return draft_patch, applied_patch


def _cancel_one_panel(
        panel_id,
        draft_data,
        applied_data,
        revision,
):
    draft_index = _find_panel_index(
        draft_data,
        panel_id,
    )
    applied_index, applied_panel = _get_panel_copy(
        applied_data,
        panel_id,
    )

    if draft_index is None or applied_panel is None:
        raise PreventUpdate

    draft_patch = Patch()
    draft_patch[draft_index] = applied_panel

    return (
        draft_patch,
        int(revision or 0) + 1,
    )


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Output(
        "panel-reset-revision",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "cancel-panel-options",
            "index": MATCH,
        },
        "n_clicks",
    ),
    State(
        {
            "type": "cancel-panel-options",
            "index": MATCH,
        },
        "id",
    ),
    State("panel-store", "data"),
    State("panel-applied-store", "data"),
    State("panel-reset-revision", "data"),
    prevent_initial_call=True,
)
def cancel_panel_options(
        n_clicks,
        component_id,
        draft_data,
        applied_data,
        revision,
):
    if not n_clicks or component_id is None:
        raise PreventUpdate

    return _cancel_one_panel(
        component_id["index"],
        draft_data,
        applied_data,
        revision,
    )


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Output(
        "panel-reset-revision",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "cancel-panel-options-x",
            "index": MATCH,
        },
        "n_clicks",
    ),
    State(
        {
            "type": "cancel-panel-options-x",
            "index": MATCH,
        },
        "id",
    ),
    State("panel-store", "data"),
    State("panel-applied-store", "data"),
    State("panel-reset-revision", "data"),
    prevent_initial_call=True,
)
def cancel_panel_options_x(
        n_clicks,
        component_id,
        draft_data,
        applied_data,
        revision,
):
    if not n_clicks or component_id is None:
        raise PreventUpdate

    return _cancel_one_panel(
        component_id["index"],
        draft_data,
        applied_data,
        revision,
    )


@app.callback(
    Output(
        {
            "type": "csv-download",
            "index": MATCH,
        },
        "data",
    ),
    Input(
        {
            "type": "export-csv",
            "index": MATCH,
        },
        "n_clicks",
    ),
    State("panel-applied-store", "data"),
    State("global-samples", "value"),
    prevent_initial_call=True,
)
def export_csv(
        n_clicks,
        panel_data,
        global_samples,
):
    trigger = callback_context.triggered_id

    panel_id = trigger["index"]

    panel = next(
        (
            p
            for p in panel_data
            if p["id"] == panel_id
        ),
        None,
    )

    if panel is None:
        raise PreventUpdate

    chart_type = panel["chart_type"]

    panel_samples = get_panel_samples(
        panel,
        global_samples,
        gsa_df,
    )

    if chart_type == "Sample Information":

        df = gsa_df[
            gsa_df["GSA_ID"]
            .astype(str)
            .isin(panel_samples or [])
        ]

        filename = "Sample_Information.csv"

    elif chart_type == "PSD Undersize":

        df = get_psd_export_df(
            mmes_df,
            mmes_rs_df,
            panel_samples,
        )

        filename = "PSD_Undersize.csv"

    elif chart_type == "PSD Frequency":

        df = get_frequency_export_df(
            mmes_df,
            mmes_rs_df,
            panel_samples,
        )

        filename = "PSD_Frequency.csv"

    elif chart_type == "Ternary":

        df = get_ternary_export_df(
            gsa_df,
            panel_samples,
            panel,
        )

        filename = "Ternary.csv"

    elif chart_type == "Grain Size Log":

        df = get_grainlog_export_df(
            gsa_df,
            panel_samples,
            panel,
        )

        filename = "Grain_Size_Log.csv"

    elif chart_type == "PCA":

        df = get_pca_export_df(
            gsa_df,
            panel_samples,
            panel,
        )

        filename = "PCA.csv"

    elif chart_type == "PCA - Mastersizer Only":

        df = get_mastersizer_pca_export_df(
            gsa_df,
            mmes_df,
            mmes_rs_df,
            panel_samples,
            panel,
        )

        filename = "PCA_Mastersizer_Only.csv"

    elif (
            chart_type
            == "Hierarchical Clustering"
    ):

        df = get_hierarchical_export_df(
            gsa_df,
            panel_samples,
            panel,
        )

        filename = (
            "Hierarchical_Clustering.csv"
        )

    else:
        return None

    df = add_export_metadata(
        df,
        gsa_df,
        panel,
    )

    return dcc.send_data_frame(
        df.to_csv,
        filename,
        index=False,
    )


if __name__ == "__main__":
    app.run(debug=True)

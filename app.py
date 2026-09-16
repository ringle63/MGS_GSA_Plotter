from dash import (
    Dash,
    html,
    dcc,
    Input,
    Output,
    State,
    MATCH,
    ALL,
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

app = Dash(__name__)
app.title = "MGS_GSA_Plotter"

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
        "panel-store",
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

    return (
        state.get(
            "panel_store",
            [],
        ),

        state.get(
            "global_filters",
            [],
        ),

        state.get(
            "pending_global_filters",
            [],
        ),

        state.get(
            "global_samples",
            [],
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
            "index": ALL,
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
)
def update_panel_selected_counts(
        panel_data,
        global_samples,
):
    if not panel_data:
        raise PreventUpdate

    ctx = callback_context

    if not ctx.outputs_list:
        raise PreventUpdate

    expected_outputs = len(
        ctx.outputs_list
    )

    results = []

    for panel in panel_data:

        samples = get_panel_samples(
            panel,
            global_samples,
            gsa_df,
        )

        if panel["use_global"]:
            source = "Global"
        else:
            source = "Panel"

        results.append(
            f"{source} Selection: {len(samples)} samples"
        )

    if len(results) != expected_outputs:
        raise PreventUpdate

    return results


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
    Input("panel-store", "data"),
)
def render_panels(panel_data):
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
    Output("panel-store", "data"),
    Input("add-panel", "n_clicks"),
    State("panel-store", "data"),
    prevent_initial_call=True,
)
def add_panel(
        n_clicks,
        panel_data,
):
    if len(panel_data) >= 8:
        return panel_data

    next_id = max(
        panel["id"]
        for panel in panel_data
    ) + 1

    panel_data.append(
        {
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
    )

    return panel_data


@app.callback(
    Output("panel-store", "data", allow_duplicate=True),
    Input(
        {
            "type": "remove-panel",
            "index": ALL,
        },
        "n_clicks",
    ),
    State("panel-store", "data"),
    prevent_initial_call=True,
)
def remove_panel(
        n_clicks,
        panel_data,
):
    trigger = callback_context.triggered

    if not trigger:
        return panel_data

    trigger_id = eval(
        trigger[0]["prop_id"].split(".")[0]
    )

    panel_id = trigger_id["index"]

    if len(panel_data) == 1:
        return panel_data

    return [
        panel
        for panel in panel_data
        if panel["id"] != panel_id
    ]


@app.callback(
    Output("panel-store", "data", allow_duplicate=True),
    Input(
        {
            "type": "duplicate-panel",
            "index": ALL,
        },
        "n_clicks",
    ),
    State("panel-store", "data"),
    prevent_initial_call=True,
)
def duplicate_panel(
        n_clicks,
        panel_data,
):
    trigger = callback_context.triggered

    if not trigger:
        return panel_data

    if len(panel_data) >= 8:
        return panel_data

    trigger_id = eval(
        trigger[0]["prop_id"].split(".")[0]
    )

    panel_id = trigger_id["index"]

    original = next(
        panel
        for panel in panel_data
        if panel["id"] == panel_id
    )

    next_id = max(
        panel["id"]
        for panel in panel_data
    ) + 1

    new_panel = copy.deepcopy(original)

    new_panel["id"] = next_id

    panel_data.append(new_panel)

    return panel_data


@app.callback(
    Output("panel-store", "data", allow_duplicate=True),
    Input(
        {
            "type": "use-global",
            "index": ALL,
        },
        "value",
    ),
    State("panel-store", "data"),
    prevent_initial_call=True,
)
def update_use_global(
        checklist_values,
        panel_data,
):
    if (
            panel_data is None
            or checklist_values is None
            or len(panel_data) != len(checklist_values)
    ):
        raise PreventUpdate

    for panel, values in zip(
            panel_data,
            checklist_values,
    ):
        panel["use_global"] = (
                "global" in values
        )

    return panel_data


@app.callback(
    Output(
        {
            "type": "panel-query-builder-container",
            "index": ALL,
        },
        "style",
    ),
    Input(
        {
            "type": "use-global",
            "index": ALL,
        },
        "value",
    ),
)
def show_hide_panel_query_builder(
        use_global_values,
):
    styles = []

    for value in use_global_values:

        if "global" in (value or []):

            styles.append(
                {
                    "display": "none",
                }
            )

        else:

            styles.append(
                {
                    "display": "block",
                }
            )

    return styles


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
    trigger = callback_context.triggered_id

    if trigger is None:
        raise PreventUpdate

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

    filters = panel.get(
        "pending_panel_filters",
        [],
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

    new_clause = {
        "field": field,
        "operator": operator,
        "value": value,
        "logic": (
            "AND"
            if filters
            else None
        ),
    }

    filters.append(
        new_clause
    )

    panel["pending_panel_filters"] = filters

    return panel_data


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
            "index": ALL,
            "panel": ALL,
        },
        "n_clicks",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def remove_panel_filter(
        clicks,
        panel_data,
):
    if not any(clicks):
        raise PreventUpdate

    trigger = callback_context.triggered_id

    if trigger is None:
        raise PreventUpdate

    clause_index = trigger["index"]
    panel_id = trigger["panel"]

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
        []
    )

    if clause_index >= len(filters):
        raise PreventUpdate

    new_filters = filters.copy()
    new_filters.pop(clause_index)

    panel["pending_panel_filters"] = new_filters

    return panel_data


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "panel-filter-logic",
            "index": ALL,
            "panel": ALL,
        },
        "value",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def update_panel_filter_logic(
        logic_values,
        panel_data,
):
    trigger = callback_context.triggered_id

    if trigger is None:
        raise PreventUpdate

    panel_id = trigger["panel"]

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
        []
    )

    if not filters:
        raise PreventUpdate

    new_filters = copy.deepcopy(
        filters
    )

    for i, value in enumerate(
            logic_values
    ):
        if i == 0:
            continue

        if i < len(new_filters):
            new_filters[i]["logic"] = value

    panel["pending_panel_filters"] = new_filters

    return panel_data


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "apply-panel-filter",
            "index": ALL,
        },
        "n_clicks",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def apply_panel_filter_callback(
        clicks,
        panel_data,
):
    if not any(clicks):
        raise PreventUpdate

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

    panel["panel_filters"] = copy.deepcopy(
        panel.get(
            "pending_panel_filters",
            [],
        )
    )

    return panel_data


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "clear-panel-filter",
            "index": ALL,
        },
        "n_clicks",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def clear_panel_filters(
        clicks,
        panel_data,
):
    if not any(clicks):
        raise PreventUpdate

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

    panel["pending_panel_filters"] = []
    panel["panel_filters"] = []

    return panel_data


@app.callback(
    Output(
        {
            "type": "panel-content",
            "index": ALL,
        },
        "children",
    ),
    [
        Input(
            {
                "type": "chart-type",
                "index": ALL,
            },
            "value",
        ),
        Input("global-samples", "value"),
        Input("layout-store", "data"),
    ],
    State("panel-store", "data"),
)
def update_graphs(
        chart_types,
        global_samples,
        layout_data,
        panel_data,
):
    if (
            panel_data is None
            or chart_types is None
            or len(panel_data) != len(chart_types)
    ):
        raise PreventUpdate

    contents = []

    global_samples = global_samples or []

    layout_lookup = {
        item["i"]: item
        for item in (layout_data or [])
    }

    for panel, chart_type in zip(
            panel_data,
            chart_types,
    ):

        panel = panel.copy()

        layout = layout_lookup.get(
            str(panel["id"] - 1)
        )

        if layout:
            panel["layout"] = layout

        panel_samples = get_panel_samples(
            panel,
            global_samples,
            gsa_df,
        )

        panel["grouped_samples"] = None

        if (
                panel.get(
                    "use_custom_groups",
                    False,
                )
                and has_custom_groups(
            panel
        )
        ):
            print(panel["custom_groups"])

            subset = gsa_df[
                gsa_df["GSA_ID"]
                .astype(str)
                .isin(panel_samples)
            ]

            panel["grouped_samples"] = (
                build_custom_groups(
                    panel.get(
                        "custom_groups",
                        [],
                    ),
                    subset,
                )
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

        elif chart_type == "Sample Information":

            fig = make_sample_information(
                gsa_df,
                panel_samples,
            )

        else:

            import plotly.graph_objects as go

            fig = go.Figure()

            fig.update_layout(
                title=f"{chart_type} Coming Soon"
            )

        if chart_type == "Sample Information":
            contents.append(
                html.Div(
                    fig,
                    style={
                        "flex": "1 1 auto",
                        "height": "100%",
                        "display": "flex",
                        "flexDirection": "column",
                        "minHeight": 0,
                    },
                )
            )

        elif chart_type == "Grain Size Log":

            contents.append(
                dcc.Graph(
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
            )

        else:

            contents.append(

                dcc.Graph(

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

            )

    return contents


@app.callback(
    Output("panel-store", "data", allow_duplicate=True),
    [
        Input({"type": "show-legend", "index": ALL}, "value"),
        Input({"type": "show-labels", "index": ALL}, "value"),
        Input({"type": "show-samples", "index": ALL}, "value"),
        Input({"type": "show-mean", "index": ALL}, "value"),
        Input(
            {
                "type": "show-grainlog-mean",
                "index": ALL,
            },
            "value",
        ),
        Input({"type": "show-std1", "index": ALL}, "value"),
        Input({"type": "show-std2", "index": ALL}, "value"),
        Input({"type": "show-std3", "index": ALL}, "value"),
        Input({"type": "group-by", "index": ALL}, "value"),
        Input({"type": "show-centroids", "index": ALL}, "value"),
        Input({"type": "show-covariance", "index": ALL}, "value"),
        Input({"type": "x-axis", "index": ALL}, "value"),
        Input({"type": "reference-breaks", "index": ALL}, "value"),
        Input(
            {
                "type": "grainlog-sort-field",
                "index": ALL,
            },
            "value",
        ),
        Input(
            {
                "type": "grainlog-sort-direction",
                "index": ALL,
            },
            "value",
        ),
        Input(
            {
                "type": "grainlog-gravel",
                "index": ALL,
            },
            "value",
        ),
    ],
    State("panel-store", "data"),
    prevent_initial_call=True,
)
def update_psd_settings(
        legends,
        labels,
        samples,
        means,
        grainlog_means,
        std1,
        std2,
        std3,
        groups,
        centroids,
        covariance,
        axes,
        breaks,
        grainlog_sort_fields,
        grainlog_sort_directions,
        grainlog_gravel,
        panel_data,
):
    if (
            panel_data is None
            or legends is None
            or labels is None
            or axes is None
            or breaks is None
            or len(panel_data) != len(legends)
            or len(panel_data) != len(labels)
            or len(panel_data) != len(samples)
            or len(panel_data) != len(means)
            or len(panel_data) != len(std1)
            or len(panel_data) != len(std2)
            or len(panel_data) != len(std3)
            or len(panel_data) != len(groups)
            or len(panel_data) != len(centroids)
            or len(panel_data) != len(covariance)
            or len(panel_data) != len(axes)
            or len(panel_data) != len(breaks)
            or len(panel_data) != len(grainlog_means)
            or len(panel_data) != len(grainlog_sort_fields)
            or len(panel_data) != len(grainlog_sort_directions)
            or len(panel_data) != len(grainlog_gravel)
    ):
        raise PreventUpdate

    for i, panel in enumerate(panel_data):
        panel["show_legend"] = (
                "legend" in legends[i]
        )

        panel["show_labels"] = (
                "labels" in labels[i]
        )

        panel["show_samples"] = (
                "samples" in (samples[i] or [])
        )

        panel["show_mean"] = (
                "mean" in (means[i] or [])
        )

        panel["show_grainlog_mean"] = (
                "mean"
                in (grainlog_means[i] or [])
        )

        panel["show_std1"] = (
                "std1" in (std1[i] or [])
        )

        panel["show_std2"] = (
                "std2" in (std2[i] or [])
        )

        panel["show_std3"] = (
                "std3" in (std3[i] or [])
        )

        panel["group_by"] = (
            groups[i]
            if groups[i] is not None
            else "None"
        )

        panel["show_centroids"] = (
                "centroids"
                in (centroids[i] or [])
        )

        panel["show_covariance"] = (
                "covariance"
                in (covariance[i] or [])
        )

        panel["x_axis"] = axes[i]

        panel["show_break_2"] = (
                "2" in (breaks[i] or [])
        )

        panel["show_break_4"] = (
                "4" in (breaks[i] or [])
        )

        panel["show_break_8"] = (
                "8" in (breaks[i] or [])
        )

        panel["show_break_50"] = (
                "50" in (breaks[i] or [])
        )

        panel["show_break_62_5"] = (
                "62.5" in (breaks[i] or [])
        )
        panel["grainlog_sort_field"] = (
            grainlog_sort_fields[i]
        )

        panel["grainlog_sort_ascending"] = (
                grainlog_sort_directions[i]
                == "asc"
        )
        selected = (
                grainlog_gravel[i]
                or []
        )

        panel["grainlog_gravel_settings"] = {
            "Mastersizer":
                "Mastersizer" in selected,

            "Pipette":
                "Pipette" in selected,

            "Kehew":
                "Kehew" in selected,

            "Dry Sieve":
                "Dry Sieve" in selected,
        }

    return panel_data


@app.callback(
    Output("panel-store", "data", allow_duplicate=True),
    Input(
        {"type": "chart-type", "index": ALL},
        "value",
    ),
    State("panel-store", "data"),
    prevent_initial_call=True,
)
def update_chart_types(
        chart_types,
        panel_data,
):
    if (
            panel_data is None
            or chart_types is None
            or len(panel_data) != len(chart_types)
    ):
        raise PreventUpdate

    for panel, chart_type in zip(panel_data, chart_types):
        panel["chart_type"] = chart_type

    return panel_data


@app.callback(
    Output("panel-store", "data", allow_duplicate=True),
    [
        Input(
            {
                "type": "mastersizer-break",
                "index": ALL,
            },
            "value",
        ),
        Input(
            {
                "type": "mastersizer-sand-break",
                "index": ALL,
            },
            "value",
        ),
        Input(
            {
                "type": "pipette-break",
                "index": ALL,
            },
            "value",
        ),
        Input(
            {
                "type": "show-usda",
                "index": ALL,
            },
            "value",
        ),
    ],
    State("panel-store", "data"),
    prevent_initial_call=True,
)
def update_ternary_settings(
        mastersizer_breaks,
        mastersizer_sand_breaks,
        pipette_breaks,
        show_usda,
        panel_data,
):
    if (
            panel_data is None
            or mastersizer_breaks is None
            or pipette_breaks is None
            or len(panel_data) != len(mastersizer_breaks)
            or len(panel_data) != len(pipette_breaks)
    ):
        raise PreventUpdate

    for i, panel in enumerate(panel_data):
        panel["mastersizer_break"] = (
            mastersizer_breaks[i]
        )

        panel["mastersizer_sand_break"] = (
            mastersizer_sand_breaks[i]
        )

        panel["pipette_break"] = (
            pipette_breaks[i]
        )

        panel["show_usda_triangle"] = (
                "usda" in (show_usda[i] or [])
        )

    return panel_data


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),

    Input(
        {
            "type": "toggle-controls",
            "index": ALL,
        },
        "n_clicks",
    ),

    Input(
        {
            "type": "toggle-graph-options",
            "index": ALL,
        },
        "n_clicks",
    ),

    Input(
        {
            "type": "toggle-override-options",
            "index": ALL,
        },
        "n_clicks",
    ),

    State(
        "panel-store",
        "data",
    ),

    prevent_initial_call=True,
)
def toggle_panel_sections(
        controls_clicks,
        graph_clicks,
        override_clicks,
        panel_data,
):
    trigger = callback_context.triggered_id

    if trigger is None:
        return panel_data

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

    if trigger["type"] == "toggle-controls":

        panel["controls_open"] = (
            not panel["controls_open"]
        )

    elif trigger["type"] == "toggle-graph-options":

        panel["graph_options_open"] = (
            not panel["graph_options_open"]
        )

    elif trigger["type"] == "toggle-override-options":

        panel["override_options_open"] = (
            not panel["override_options_open"]
        )

    return panel_data


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
            "type": "use-custom-groups",
            "index": ALL,
        },
        "value",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def update_custom_group_toggle(
        values,
        panel_data,
):
    for panel, value in zip(
            panel_data,
            values,
    ):
        use_custom = (
                "custom"
                in (value or [])
        )

        panel["use_custom_groups"] = use_custom

        if use_custom:
            panel["group_by"] = "None"

    return panel_data


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "add-custom-group",
            "index": ALL,
        },
        "n_clicks",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def add_custom_group(
        clicks,
        panel_data,
):
    trigger = (
        callback_context
        .triggered_id
    )

    if trigger is None:
        raise PreventUpdate

    panel_id = trigger["index"]

    for panel in panel_data:

        if (
                panel["id"]
                != panel_id
        ):
            continue

        groups = panel.setdefault(
            "custom_groups",
            [],
        )

        if len(groups) >= 20:
            break

        groups.append(
            {
                "name":
                    f"Group {len(groups) + 1}",

                "filters": [],
                "pending_filters": [],
            }
        )
        print(callback_context.triggered_id)
        break

    return panel_data


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
    trigger = callback_context.triggered_id

    if trigger is None:
        raise PreventUpdate

    panel_id = trigger["panel"]
    group_index = trigger["group"]

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
        []
    )

    if group_index >= len(groups):
        raise PreventUpdate

    group = groups[group_index]

    filters = group.get(
        "pending_filters",
        []
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

    new_clause = {
        "field": field,
        "operator": operator,
        "value": value,
        "logic": (
            "AND"
            if filters
            else None
        ),
    }

    filters.append(
        new_clause
    )

    group["pending_filters"] = filters

    return panel_data


@app.callback(
    Output(
        {
            "type": "custom-group-filter-list",
            "panel": MATCH,
            "group": MATCH,
        },
        "children",
    ),
    Input(
        "panel-store",
        "data",
    ),
    State(
        {
            "type": "custom-group-filter-list",
            "panel": MATCH,
            "group": MATCH,
        },
        "id",
    ),
)
def show_custom_group_filter_list(
        panel_data,
        component_id,
):
    panel_id = component_id["panel"]
    group_index = component_id["group"]

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
        []
    )

    if group_index >= len(groups):
        raise PreventUpdate

    filters = groups[group_index].get(
        "pending_filters",
        []
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

            values = ", ".join(
                map(
                    str,
                    clause["value"]
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
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "remove-custom-group-filter",
            "panel": ALL,
            "group": ALL,
            "index": ALL,
        },
        "n_clicks",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def remove_custom_group_filter(
        clicks,
        panel_data,
):
    if not any(clicks):
        raise PreventUpdate

    trigger = callback_context.triggered_id

    if trigger is None:
        raise PreventUpdate

    panel_id = trigger["panel"]
    group_index = trigger["group"]
    clause_index = trigger["index"]

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
        []
    )

    if group_index >= len(groups):
        raise PreventUpdate

    filters = groups[group_index].get(
        "pending_filters",
        []
    )

    if clause_index >= len(filters):
        raise PreventUpdate

    new_filters = filters.copy()

    new_filters.pop(
        clause_index
    )

    groups[group_index][
        "pending_filters"
    ] = new_filters

    return panel_data


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "custom-group-filter-logic",
            "panel": ALL,
            "group": ALL,
            "index": ALL,
        },
        "value",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def update_custom_group_filter_logic(
        logic_values,
        panel_data,
):
    trigger = callback_context.triggered_id

    if trigger is None:
        raise PreventUpdate

    panel_id = trigger["panel"]
    group_index = trigger["group"]

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
        []
    )

    if group_index >= len(groups):
        raise PreventUpdate

    filters = groups[group_index].get(
        "pending_filters",
        []
    )

    if not filters:
        raise PreventUpdate

    new_filters = copy.deepcopy(
        filters
    )

    for i, value in enumerate(
            logic_values
    ):
        if i == 0:
            continue

        if i < len(new_filters):
            new_filters[i]["logic"] = value

    groups[group_index][
        "pending_filters"
    ] = new_filters

    return panel_data


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
    if not n_clicks:
        raise PreventUpdate

    panel_id = component_id["panel"]
    group_index = component_id["group"]

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
        []
    )

    if group_index >= len(groups):
        raise PreventUpdate

    group = groups[group_index]

    # Save the group name
    if (
            group_name is not None
            and str(group_name).strip()
    ):
        group["name"] = (
            str(group_name)
            .strip()
        )

    # Save the filters
    group["filters"] = copy.deepcopy(
        group.get(
            "pending_filters",
            []
        )
    )
    print(group["pending_filters"])
    print(group["filters"])

    return panel_data


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "clear-custom-group-filter",
            "panel": ALL,
            "group": ALL,
        },
        "n_clicks",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def clear_custom_group_filters(
        clicks,
        panel_data,
):
    if not any(clicks):
        raise PreventUpdate

    trigger = callback_context.triggered_id

    if trigger is None:
        raise PreventUpdate

    panel_id = trigger["panel"]
    group_index = trigger["group"]

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
        []
    )

    if group_index >= len(groups):
        raise PreventUpdate

    groups[group_index][
        "pending_filters"
    ] = []

    groups[group_index][
        "filters"
    ] = []

    return panel_data


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    Input(
        {
            "type": "remove-custom-group",
            "panel": ALL,
            "group": ALL,
        },
        "n_clicks",
    ),
    State(
        "panel-store",
        "data",
    ),
    prevent_initial_call=True,
)
def remove_custom_group(
        clicks,
        panel_data,
):
    if not any(clicks):
        raise PreventUpdate

    trigger = callback_context.triggered_id

    if trigger is None:
        raise PreventUpdate

    panel_id = trigger["panel"]
    group_index = trigger["group"]

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
        []
    )

    if (
            group_index
            >= len(groups)
    ):
        raise PreventUpdate

    groups.pop(group_index)

    return panel_data


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
    State("panel-store", "data"),
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

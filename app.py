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

from logic.data_loader import (
    load_gsa_lab,
    load_mmes,
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
)

from logic.panel_filters import (
    get_panel_samples,
)

from dash.exceptions import PreventUpdate

from dash_rgl import RGLLayout

print("RGLLayout =", RGLLayout)
print("Type =", type(RGLLayout))

gsa_df = load_gsa_lab()
mmes_df = load_mmes()

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

analysis_method_options = [
    {"label": x, "value": x}
    for x in analysis_methods
]

formation_options = [
    {"label": x, "value": x}
    for x in formations
]

borehole_options = [
    {"label": x, "value": x}
    for x in boreholes
]

sample_options = [
    {"label": x, "value": x}
    for x in sorted(
        gsa_df["GSA_ID"]
        .dropna()
        .astype(str)
        .unique()
    )
]

mmes_ids = set(
    mmes_df["Sample_Name_Final"].astype(str)
)

matched_count = (
    gsa_df["GSA_ID"]
    .astype(str)
    .isin(mmes_ids)
    .sum()
)

print(f"GSA samples: {len(gsa_df)}")
print(f"MMES samples: {len(mmes_df)}")
print(f"Matched samples: {matched_count}")
print(gsa_df["GSA_ID"].duplicated().sum())
print(mmes_df["Sample_Name_Final"].duplicated().sum())

app = Dash(__name__)
app.title = "MGS_GSA_Plotter"

app.layout = html.Div(
    [
RGLLayout(
    children=[
        html.Div(
            "Panel 1",
            style={
                "backgroundColor": "#d9edf7",
                "padding": "20px",
            },
        ),
        html.Div(
            "Panel 2",
            style={
                "backgroundColor": "#dff0d8",
                "padding": "20px",
            },
        ),
    ]
),
        html.H1("MGS_GSA_Plotter"),

        dcc.Store(
            id="panel-store",
            data=[
                {
                    "id": 1,
                    "chart_type": "PSD Undersize",
                    "use_global": True,

                    "show_legend": True,
                    "show_labels": False,

                    "x_axis": "log",

                    "show_break_8": True,
                    "show_break_62_5": True,

                    "mastersizer_break": 8,
                    "pipette_break": 2,

                    "override_methods": [],
                    "override_formations": [],
                    "override_boreholes": [],
                    "override_samples": [],

                    "graph_options_open": True,
                    "override_options_open": False,

                    "panel_open": True,
                }
            ],
        ),

        create_globalselection(
            len(gsa_df),
            len(mmes_df),
            matched_count,
            analysis_methods,
            formations,
            boreholes,
        ),

        html.Div(
            [
                html.Button(
                    "Add Panel",
                    id="add-panel",
                    n_clicks=0,
                ),

                html.Div(
                    id="panel-container",
                    style={"marginTop": "20px"},
                ),
            ],
            style={
                "width": "75%",
                "display": "inline-block",
                "padding": "20px",
            },
        ),
    ]
)


@app.callback(
    Output("global-samples", "options"),
    [
        Input("global-analysis-method", "value"),
        Input("global-formation", "value"),
        Input("global-borehole", "value"),
    ],
)
def update_sample_options(
        selected_methods,
        selected_formations,
        selected_boreholes,
):
    filtered = gsa_df.copy()

    # AND logic
    if selected_methods:
        filtered = filtered[
            filtered["analysis_method"].astype(str).isin(selected_methods)
        ]

    if selected_formations:
        filtered = filtered[
            filtered["formation"].astype(str).isin(selected_formations)
        ]

    if selected_boreholes:
        filtered = filtered[
            filtered["BoreholeID"].astype(str).isin(selected_boreholes)
        ]

    sample_ids = sorted(
        filtered["GSA_ID"]
        .dropna()
        .astype(str)
        .unique()
    )

    return [
        {"label": sample, "value": sample}
        for sample in sample_ids
    ]


@app.callback(
    Output(
        "panel-store",
        "data",
        allow_duplicate=True,
    ),
    [
        Input(
            {
                "type": "override-methods",
                "index": ALL,
            },
            "value",
        ),

        Input(
            {
                "type": "override-formations",
                "index": ALL,
            },
            "value",
        ),

        Input(
            {
                "type": "override-boreholes",
                "index": ALL,
            },
            "value",
        ),

        Input(
            {
                "type": "override-samples",
                "index": ALL,
            },
            "value",
        ),
    ],

    State(
        "panel-store",
        "data",
    ),

    prevent_initial_call=True,
)
def update_panel_overrides(
        methods,
        formations,
        boreholes,
        samples,
        panel_data,
):
    if (
            panel_data is None
            or methods is None
            or formations is None
            or boreholes is None
            or samples is None
            or len(panel_data) != len(methods)
            or len(panel_data) != len(formations)
            or len(panel_data) != len(boreholes)
            or len(panel_data) != len(samples)
    ):
        raise PreventUpdate

    for i, panel in enumerate(panel_data):
        panel["override_methods"] = (
            methods[i]
            if methods[i] is not None
            else []
        )

        panel["override_formations"] = (
            formations[i]
            if formations[i] is not None
            else []
        )

        panel["override_boreholes"] = (
            boreholes[i]
            if boreholes[i] is not None
            else []
        )

        panel["override_samples"] = (
            samples[i]
            if samples[i] is not None
            else []
        )

    return panel_data


@app.callback(
    Output("selected-count", "children"),
    Input("global-samples", "value"),
)
def update_selected_count(selected_samples):
    count = len(selected_samples) if selected_samples else 0

    return f"Selected Samples: {count}"


@app.callback(
    Output("global-samples", "value"),
    [
        Input("select-all-filtered", "n_clicks"),
        Input("clear-selection", "n_clicks"),
    ],
    State("global-samples", "options"),
    prevent_initial_call=True,
)
def modify_sample_selection(
        select_all_clicks,
        clear_clicks,
        sample_options,
):
    trigger = callback_context.triggered[0]["prop_id"].split(".")[0]

    if trigger == "select-all-filtered":
        return [
            option["value"]
            for option in sample_options
        ]

    elif trigger == "clear-selection":
        return []

    return []


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
                analysis_method_options,
                formation_options,
                borehole_options,
                sample_options,
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
            "x_axis": "log",
            "show_break_8": True,
            "show_break_62_5": True,

            "mastersizer_break": 8,
            "pipette_break": 2,

            "override_methods": [],
            "override_formations": [],
            "override_boreholes": [],
            "override_samples": [],

            "graph_options_open": True,
            "override_options_open": False,

            "panel_open": True,
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
    ],
    State("panel-store", "data"),
)
def update_graphs(
        chart_types,
        global_samples,
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

    for panel, chart_type in zip(
            panel_data,
            chart_types,
    ):

        panel_samples = get_panel_samples(
            panel,
            global_samples,
            gsa_df,
        )

        if chart_type == "PSD Undersize":

            fig = make_psd_plot(
                mmes_df,
                panel_samples,
                panel["show_legend"],
                panel["show_labels"],
                panel["x_axis"],
                panel["show_break_8"],
                panel["show_break_62_5"],
            )

        elif chart_type == "PSD Frequency":

            fig = make_frequency_plot(
                mmes_df,
                panel_samples,
                panel["show_legend"],
                panel["show_labels"],
                panel["x_axis"],
                panel["show_break_8"],
                panel["show_break_62_5"],
            )

        elif chart_type == "Ternary":

            fig = make_ternary_plot(
                gsa_df,
                panel_samples,
                panel,
            )

        elif chart_type == "Grain Size Log":

            fig = make_grain_log(
                gsa_df,
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
            contents.append(fig)

        else:

            contents.append(
                dcc.Graph(
                    figure=fig,
                    config={
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
        Input({"type": "x-axis", "index": ALL}, "value"),
        Input({"type": "reference-breaks", "index": ALL}, "value"),
    ],
    State("panel-store", "data"),
    prevent_initial_call=True,
)
def update_psd_settings(
        legends,
        labels,
        axes,
        breaks,
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
            or len(panel_data) != len(axes)
            or len(panel_data) != len(breaks)
    ):
        raise PreventUpdate

    for i, panel in enumerate(panel_data):
        panel["show_legend"] = (
                "legend" in legends[i]
        )

        panel["show_labels"] = (
                "labels" in labels[i]
        )

        panel["x_axis"] = axes[i]

        panel["show_break_8"] = (
                "8" in breaks[i]
        )

        panel["show_break_62_5"] = (
                "62.5" in breaks[i]
        )

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
                "type": "pipette-break",
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
        pipette_breaks,
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

        panel["pipette_break"] = (
            pipette_breaks[i]
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
            "type": "toggle-panel",
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
        panel_clicks,
        graph_clicks,
        override_clicks,
        panel_data,
):
    trigger = callback_context.triggered_id

    if trigger is None:
        return panel_data

    panel_id = trigger["index"]

    panel = next(
        p
        for p in panel_data
        if p["id"] == panel_id
    )

    if trigger["type"] == "toggle-panel":
        panel["panel_open"] = (
            not panel["panel_open"]
        )

    if trigger["type"] == "toggle-graph-options":

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
        p
        for p in panel_data
        if p["id"] == panel_id
    )

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
            panel_samples,
        )

        filename = "PSD_Undersize.csv"

    elif chart_type == "PSD Frequency":

        df = get_frequency_export_df(
            mmes_df,
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

    return dcc.send_data_frame(
        df.to_csv,
        filename,
        index=False,
    )


if __name__ == "__main__":
    app.run(debug=True)

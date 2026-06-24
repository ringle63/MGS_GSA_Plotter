import plotly.graph_objects as go

from logic.grainbreaks import (
    get_grain_log_classes,
)

from logic.legendsorting import (
    gsa_sort_key,
)

def make_grain_log(
    gsa_df,
    mmes_df,
    selected_samples,
    panel,
):

    fig = go.Figure()

    subset = gsa_df[
        gsa_df["GSA_ID"]
        .astype(str)
        .isin(selected_samples)
    ]

    subset = (
        subset.assign(
            _sort_key=subset["GSA_ID"]
            .apply(gsa_sort_key)
        )
        .sort_values("_sort_key")
        .drop(columns="_sort_key")
    )

    settings = {
        "Mastersizer": panel["mastersizer_break"],
        "MastersizerSand": panel["mastersizer_sand_break"],
        "Pipette": panel["pipette_break"],
    }

    mmes_lookup = (
        mmes_df
        .set_index("Sample_Name_Final")
        .to_dict("index")
    )

    classes_order = [
        "Clay",
        "Silt",
        "Very Fine Sand",
        "Fine Sand",
        "Medium Sand",
        "Coarse Sand",
        "Very Coarse Sand",
        "Gravel",
    ]

    colors = {
        "Gravel": "#5b0000",
        "Very Coarse Sand": "#8b0000",
        "Coarse Sand": "#cc5500",
        "Medium Sand": "#ffb000",
        "Fine Sand": "#ffff00",
        "Very Fine Sand": "#ffff99",
        "Silt": "#b2f0f0",
        "Clay": "#0000ff",
    }

    y_labels = []

    class_values = {
        cls: []
        for cls in classes_order
    }

    customdata = []

    for _, row in subset.iterrows():

        mmes_row = mmes_lookup.get(
            str(row["GSA_ID"])
        )

        grain = get_grain_log_classes(
            row,
            mmes_row,
            settings,
        )

        if grain is None:
            continue

        sample = row["GSA_ID"]

        y_labels.append(sample)

        customdata.append(
            [
                sample,
                grain["method"],
                grain["break"],
                grain["Gravel"],
                grain["Very Coarse Sand"],
                grain["Coarse Sand"],
                grain["Medium Sand"],
                grain["Fine Sand"],
                grain["Very Fine Sand"],
                grain["Silt"],
                grain["Clay"],
            ]
        )

        for cls in classes_order:
            class_values[cls].append(
                grain[cls]
            )

    for cls in classes_order:
        fig.add_trace(
            go.Bar(
                y=y_labels,
                x=class_values[cls],
                orientation="h",
                name=cls,
                marker_color=colors[cls],
                width=0.9,

                customdata=customdata,

                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Method: %{customdata[1]}<br>"
                    "Break: %{customdata[2]}<br>"
                    "<br>"
                    "Gravel: %{customdata[3]:.1f}%<br>"
                    "Very Coarse Sand: %{customdata[4]:.1f}%<br>"
                    "Coarse Sand: %{customdata[5]:.1f}%<br>"
                    "Medium Sand: %{customdata[6]:.1f}%<br>"
                    "Fine Sand: %{customdata[7]:.1f}%<br>"
                    "Very Fine Sand: %{customdata[8]:.1f}%<br>"
                    "Silt: %{customdata[9]:.1f}%<br>"
                    "Clay: %{customdata[10]:.1f}%"
                    "<extra></extra>"
                ),
            )
        )

    sample_height = 18
    figure_height = (
            len(y_labels) * sample_height
            + 90
    )

    fig.layout.meta = {
        "figure_height": figure_height
    }

    fig.update_layout(
        title="Grain Size Log",

        autosize=False,
        height=figure_height,

        barmode="stack",

        showlegend=False,

        xaxis=dict(
            title="Percent (%)",
            range=[100, 0],
            fixedrange=True,
        ),

        yaxis=dict(
            autorange="reversed",
            side="right",
            title="",
            automargin=True,
        ),

        margin=dict(
            l=20,
            r=80,
            t=50,
            b=40,
        ),
    )

    print(
        f"Samples: {len(y_labels)}, "
        f"Figure height: {figure_height}"
    )

    return fig
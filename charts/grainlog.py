import plotly.graph_objects as go

from logic.grainbreaks import (
    get_grain_log_classes,
)


def make_grain_log(
    gsa_df,
    selected_samples,
    panel,
):

    fig = go.Figure()

    subset = gsa_df[
        gsa_df["GSA_ID"]
        .astype(str)
        .isin(selected_samples)
    ]

    settings = {
        "Mastersizer": panel["mastersizer_break"],
        "Pipette": panel["pipette_break"],
    }

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

    hover_text = []

    for _, row in subset.iterrows():

        grain = get_grain_log_classes(
            row,
            settings,
        )

        if grain is None:
            continue

        sample = row["GSA_ID"]

        y_labels.append(sample)

        hover_text.append(
            (
                f"{sample}<br>"
                f"Method: {grain['method']}<br>"
                f"Break: {grain['break']}<br>"
                f"Clay: {grain['Clay']:.1f}%<br>"
                f"Silt: {grain['Silt']:.1f}%"
            )
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

                customdata=hover_text,

                hovertemplate=(
                    "%{customdata}<br>"
                    f"{cls}: "
                    "%{x:.1f}%"
                    "<extra></extra>"
                ),
            )
        )

    figure_height = max(
        300,
        len(y_labels) * 18,
    )

    fig.update_layout(
        title="Grain Size Log",

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

    return fig
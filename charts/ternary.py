import plotly.graph_objects as go

from logic.grainbreaks import get_grain_fractions

from logic.usda_triangle import add_usda_triangle


def make_ternary_plot(
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

    for _, row in subset.iterrows():

        fractions = get_grain_fractions(
            row,
            settings,
        )

        if fractions is None:
            continue

        sample = row["GSA_ID"]

        fig.add_trace(
            go.Scatterternary(
                a=[fractions["clay"]],
                b=[fractions["sand"]],
                c=[fractions["silt"]],

                mode="markers",

                name=sample,

                hovertemplate=
                (
                    f"{sample}<br>"
                    f"Method: {fractions['method']}<br>"
                    f"Break: {fractions['break']}<br>"
                    f"Clay: {fractions['clay']:.2f}%<br>"
                    f"Silt: {fractions['silt']:.2f}%<br>"
                    f"Sand: {fractions['sand']:.2f}%"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title="Ternary Plot",

        showlegend=panel["show_legend"],

        autosize=True,

        ternary=dict(
            sum=100,

            aaxis=dict(
                title="",
                tick0=0,
                dtick=10,
                showgrid=True,
            ),

            baxis=dict(
                title="",
                tick0=0,
                dtick=10,
                showgrid=True,
            ),

            caxis=dict(
                title="",
                tick0=0,
                dtick=10,
                showgrid=True,
            ),
        ),
    )

    fig.update_layout(
        annotations=[]
    )

    # ---------- AXIS LABELS ----------

    # Hide axis labels on narrow panels
    # ---------- AXIS LABELS ----------

    # ---------- AXIS LABELS ----------

    show_axis_annotations = (
            panel.get("layout", {}).get("w", 12) >= 10
    )

    if show_axis_annotations:

        fig.add_annotation(
            text="percent clay",
            x=0.35,
            y=0.49,
            textangle=-60,
            showarrow=False,
            font=dict(
                size=18,
                color="gray",
            ),
        )

        fig.add_annotation(
            text="percent silt",
            x=0.65,
            y=0.49,
            textangle=60,
            showarrow=False,
            font=dict(
                size=18,
                color="gray",
            ),
        )

        fig.add_annotation(
            text="percent sand",
            x=0.50,
            y=-0.14,
            showarrow=False,
            font=dict(
                size=18,
                color="gray",
            ),
        )

        # ---------- CLAY ARROW ----------

        fig.add_annotation(
            x=0.33,
            y=0.49,
            ax=-35,
            ay=65,
            xref="paper",
            yref="paper",
            axref="pixel",
            ayref="pixel",
            showarrow=True,
            arrowhead=2,
            arrowcolor="gray",
        )

        # ---------- SILT ARROW ----------

        fig.add_annotation(
            x=0.67,
            y=0.49,
            ax=35,
            ay=65,
            xref="paper",
            yref="paper",
            axref="pixel",
            ayref="pixel",
            showarrow=True,
            arrowhead=2,
            arrowcolor="gray",
        )

        # ---------- SAND ARROW ----------

        fig.add_annotation(
            x=0.50,
            y=-0.18,
            ax=80,
            ay=0,
            xref="paper",
            yref="paper",
            axref="pixel",
            ayref="pixel",
            showarrow=True,
            arrowhead=2,
            arrowcolor="gray",
        )

    if fig.layout.annotations is None:
        fig.update_layout(annotations=[])

    if panel["show_usda_triangle"]:
        fig = add_usda_triangle(fig)


    return fig

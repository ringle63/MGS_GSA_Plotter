import plotly.graph_objects as go

from logic.grainbreaks import get_grain_fractions


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
                b=[fractions["silt"]],
                c=[fractions["sand"]],

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

        ternary=dict(
            sum=100,

            aaxis_title="Clay",

            baxis_title="Silt",

            caxis_title="Sand",
        ),
    )

    return fig
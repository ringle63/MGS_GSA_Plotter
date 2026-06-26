import plotly.graph_objects as go

from logic.legendsorting import (
    gsa_sort_key,
)

import pandas as pd

from logic.filters import NULL_VALUE

from logic.groupcolors import (
    build_group_colors,
    darken_color,
)

def make_frequency_plot(
        gsa_df,
        mmes_df,
        selected_samples,
        panel,
):
    show_legend = panel["show_legend"]
    show_labels = panel["show_labels"]
    show_samples = panel["show_samples"]
    show_mean = panel["show_mean"]
    show_std1 = panel["show_std1"]
    show_std2 = panel["show_std2"]
    show_std3 = panel["show_std3"]
    group_by = panel["group_by"]
    x_axis = panel["x_axis"]
    show_break_2 = panel.get(
        "show_break_2",
        False,
    )

    show_break_4 = panel.get(
        "show_break_4",
        False,
    )

    show_break_8 = panel["show_break_8"]

    show_break_50 = panel.get(
        "show_break_50",
        False,
    )

    show_break_62_5 = panel["show_break_62_5"]

    fig = go.Figure()

    sample_groups = {}
    group_colors = {}

    if not selected_samples:
        fig.update_layout(
            title="No samples selected"
        )
        return fig

    FR_cols = sorted(
        [
            c for c in mmes_df.columns
            if c.startswith("FR_")
        ],
        key=lambda x: float(
            x.replace("FR_", "").replace("_", ".")
        )
    )

    x_vals = [
        float(
            c.replace("FR_", "").replace("_", ".")
        )
        for c in FR_cols
    ]

    plot_x = x_vals.copy()

    if x_axis == "phi":
        import numpy as np

        plot_x = [
            -np.log2(x / 1000)
            for x in plot_x
        ]

    subset = (
        mmes_df[
            mmes_df["Sample_Name_Final"]
            .astype(str)
            .isin(selected_samples)
        ]
            .copy()
    )

    if group_by != "None":

        if group_by == "GSA_ID":

            subset["_group"] = (
                subset["Sample_Name_Final"]
                .astype(str)
            )

            groups = sorted(
                subset["_group"]
                .fillna(NULL_VALUE)
                .unique()
            )

            group_colors = (
                build_group_colors(
                    groups
                )
            )

        else:

            sample_groups = (
                gsa_df[
                    ["GSA_ID", group_by]
                ]
                .drop_duplicates("GSA_ID")
                .set_index("GSA_ID")[group_by]
                .to_dict()
            )

            subset["_group"] = (
                subset["Sample_Name_Final"]
                .astype(str)
                .map(sample_groups)
                .fillna(NULL_VALUE)
            )
            groups = sorted(
                subset["_group"]
                .fillna(NULL_VALUE)
                .unique()
            )

            group_colors = (
                build_group_colors(
                    groups
                )
            )

    subset = (
        subset.assign(
            _sort_key=subset[
                "Sample_Name_Final"
            ].apply(gsa_sort_key)
        )
        .sort_values("_sort_key")
        .drop(columns="_sort_key")
    )



    if show_samples:

        for _, row in subset.iterrows():

            sample = str(
                row["Sample_Name_Final"]
            )

            y_vals = row[
                FR_cols
            ].tolist()

            mode = (
                "lines+text"
                if show_labels
                else "lines"
            )

            line_color = None

            if group_by != "None":

                if group_by == "GSA_ID":

                    group_name = sample

                else:

                    group_name = row["_group"]

                line_color = (
                    group_colors[
                        group_name
                    ]
                )

            fig.add_trace(
                go.Scatter(
                    x=plot_x,
                    y=y_vals,
                    mode=mode,
                    name=sample,
                    showlegend=show_legend,

                    line=dict(
                        color=line_color,
                    ),

                    text=[
                             None
                         ] * (
                                 len(y_vals) - 1
                         ) + [sample],

                    textposition="middle right",
                )
            )

    if show_mean and len(subset):

        if group_by == "None":

            grouped = {
                "Mean": subset
            }

        else:

            grouped = {
                str(name): df
                for name, df in subset.groupby("_group")
            }

        for group_name, group_df in grouped.items():

            if len(group_df) == 0:
                continue

            if len(group_df) < 2:
                continue

            mean_curve = (
                group_df[FR_cols]
                .astype(float)
                .mean()
            )

            std_curve = (
                group_df[FR_cols]
                .astype(float)
                .std()
            )

            plus1 = (
                    mean_curve + std_curve
            ).clip(0, 100)

            minus1 = (
                    mean_curve - std_curve
            ).clip(0, 100)

            plus2 = (
                    mean_curve + 2 * std_curve
            ).clip(0, 100)

            minus2 = (
                    mean_curve - 2 * std_curve
            ).clip(0, 100)

            plus3 = (
                    mean_curve + 3 * std_curve
            ).clip(0, 100)

            minus3 = (
                    mean_curve - 3 * std_curve
            ).clip(0, 100)

            fig.add_trace(
                go.Scatter(
                    x=plot_x,
                    y=mean_curve,
                    mode="lines",
                    name=f"{group_name} Mean",
                    line=dict(
                        width=5,
                        dash="dash",
                        color="black",
                    ),
                    hovertemplate=(
                        f"{group_name} Mean"
                        "<br>"
                        "Grain Size: %{x:.3g} µm"
                        "<br>"
                        "Frequency: %{y:.1f}%"
                        "<extra></extra>"
                    ),
                )
            )

            if show_std1:

                for y, sign in [
                    (plus1, "+1σ"),
                    (minus1, "-1σ"),
                ]:
                    fig.add_trace(
                        go.Scatter(
                            x=plot_x,
                            y=y,
                            mode="lines",
                            name=f"{group_name} {sign}",
                            line=dict(
                                color=darken_color(
                                    group_colors[
                                        group_name
                                    ],
                                    factor=0.35,
                                ),
                                width=2,
                                dash="dot",
                            ),
                            hovertemplate=(
                                f"{group_name} {sign}"
                                "<br>"
                                "Grain Size: %{x:.3g} µm"
                                "<br>"
                                "Frequency: %{y:.1f}%"
                                "<extra></extra>"
                            ),
                        )
                    )

            if show_std2:

                for y, sign in [
                    (plus2, "+2σ"),
                    (minus2, "-2σ"),
                ]:
                    fig.add_trace(
                        go.Scatter(
                            x=plot_x,
                            y=y,
                            mode="lines",
                            name=f"{group_name} {sign}",
                            line=dict(
                                color=darken_color(
                                    group_colors[
                                        group_name
                                    ],
                                    factor=0.35,
                                ),
                                width=2,
                                dash="dashdot",
                            ),
                            hovertemplate=(
                                f"{group_name} {sign}"
                                "<br>"
                                "Grain Size: %{x:.3g} µm"
                                "<br>"
                                "Frequency: %{y:.1f}%"
                                "<extra></extra>"
                            ),
                        )
                    )

            if show_std3:

                for y, sign in [
                    (plus3, "+3σ"),
                    (minus3, "-3σ"),
                ]:
                    fig.add_trace(
                        go.Scatter(
                            x=plot_x,
                            y=y,
                            mode="lines",
                            name=f"{group_name} {sign}",
                            line=dict(
                                color=darken_color(
                                    group_colors[
                                        group_name
                                    ],
                                    factor=0.35,
                                ),
                                width=1,
                                dash="longdash",
                            ),
                            hovertemplate=(
                                f"{group_name} {sign}"
                                "<br>"
                                "Grain Size: %{x:.3g} µm"
                                "<br>"
                                "Frequency: %{y:.1f}%"
                                "<extra></extra>"
                            ),
                        )
                    )

    fig.update_layout(
        title="PSD Frequency",
        xaxis_title="Grain Size (µm)",
        yaxis_title="Frequency (%)",
        hovermode="closest",
        autosize=True,
        margin=dict(
            l=50,
            r=20,
            t=40,
            b=50,
        ),
    )

    if x_axis == "log":
        fig.update_xaxes(type="log")

    elif x_axis == "linear":
        pass

    elif x_axis == "phi":
        fig.update_xaxes(
            title="Phi (φ)"
        )

    reference_breaks = []

    if show_break_2:
        reference_breaks.append(2)

    if show_break_4:
        reference_breaks.append(4)

    if show_break_8:
        reference_breaks.append(8)

    if show_break_50:
        reference_breaks.append(50)

    if show_break_62_5:
        reference_breaks.append(62.5)

    if x_axis == "phi":
        import numpy as np

        reference_breaks = [
            -np.log2(x / 1000)
            for x in reference_breaks
        ]

    for x in reference_breaks:
        fig.add_vline(
            x=x,
            line_dash="dash",
        )

    return fig

import plotly.graph_objects as go

from logic.grainbreaks import get_grain_fractions

from logic.usda_triangle import add_usda_triangle

from logic.legendsorting import (
    gsa_sort_key,
)

import pandas as pd

import numpy as np

from logic.filters import NULL_VALUE

from logic.groupcolors import (
    build_group_colors,
    darken_color,
)

def make_ternary_plot(
        gsa_df,
        mmes_df,
        selected_samples,
        panel,
):
    fig = go.Figure()

    group_colors = {}

    subset = (
        gsa_df[
            gsa_df["GSA_ID"]
            .astype(str)
            .isin(selected_samples)
        ]
            .copy()
    )

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
        "MastersizerSand": panel[
            "mastersizer_sand_break"
        ],
        "Pipette": panel["pipette_break"],
    }

    mmes_lookup = (
        mmes_df
        .set_index("Sample_Name_Final")
        .to_dict("index")
    )

    custom_groups = panel.get(
        "grouped_samples"
    )

    using_custom_groups = (
            custom_groups is not None
    )

    sample_to_group = {}
    sample_to_groups = {}

    if using_custom_groups:
        (
            sample_to_groups,
            sample_to_group,
        ) = custom_groups

    points = []

    for _, row in subset.iterrows():

        mmes_row = mmes_lookup.get(
            str(row["GSA_ID"])
        )

        fractions = get_grain_fractions(
            row,
            mmes_row,
            settings,
        )

        if fractions is None:
            continue

        sample = row["GSA_ID"]

        if using_custom_groups:

            group = sample_to_group.get(
                str(sample),
                NULL_VALUE,
            )

        elif (
                panel["group_by"] != "None"
                and panel["group_by"] in row
        ):
            value = row[panel["group_by"]]

            if (
                    value is None
                    or str(value) == "nan"
            ):
                group = NULL_VALUE
            else:
                group = value

        else:
            group = "All Samples"

        points.append(
            {
                "sample": sample,
                "group": str(group),
                "clay": fractions["clay"],
                "silt": fractions["silt"],
                "sand": fractions["sand"],
                "method": fractions["method"],
                "break": fractions["break"],
            }
        )

    points_df = pd.DataFrame(points)

    group_by = panel.get(
        "group_by",
        "None",
    )

    plot_df = points_df.copy()

    if (
            not using_custom_groups
            and (
                not group_by
                or group_by == "None"
            )
    ):
        plot_df["group"] = "All Samples"

    if using_custom_groups:

        groups = sorted(
            {
                group
                for groups_list
                in sample_to_groups.values()
                for group in groups_list
            }
        )

        if (
                plot_df["group"]
                        .eq(NULL_VALUE)
                        .any()
        ):
            groups.append(NULL_VALUE)

    else:

        groups = sorted(
            plot_df["group"]
            .fillna(NULL_VALUE)
            .unique()
        )

    group_colors = (
        build_group_colors(
            groups
        )
    )

    mode = []

    if panel.get(
            "show_samples",
            True,
    ):
        mode.append("markers")

    if panel.get(
            "show_labels",
            False,
    ):
        mode.append("text")

    mode = "+".join(mode)

    if mode != "":

        for _, row in plot_df.iterrows():
            fig.add_trace(
                go.Scatterternary(
                    a=[row["clay"]],
                    b=[row["sand"]],
                    c=[row["silt"]],

                    mode=mode,

                    marker=dict(
                        size=8,

                        color=(
                            group_colors[row["group"]]
                            if (
                                    using_custom_groups
                                    or group_by != "None"
                            )
                            else None
                        ),

                        line=dict(
                            width=1,
                            color=(
                                darken_color(
                                    group_colors[row["group"]],
                                    factor=0.25,
                                )
                                if group_by != "None"
                                else None
                            ),
                        ),
                    ),

                    text=[row["sample"]],
                    textposition="top center",

                    name=row["sample"],

                    hovertemplate=
                    (
                        f"{row['sample']}<br>"
                        f"Clay: {row['clay']:.2f}%<br>"
                        f"Sand: {row['sand']:.2f}%<br>"
                        f"Silt: {row['silt']:.2f}%"
                        "<extra></extra>"
                    ),

                    showlegend=panel["show_legend"],
                )
            )

    fig.update_layout(
        title="Ternary Plot",

        showlegend=panel["show_legend"],

        autosize=True,

        margin=dict(
            l=20,
            r=20,
            t=40,
            b=70,
        ),

        ternary=dict(
            sum=100,

            aaxis=dict(
                title="Clay",
                tick0=0,
                dtick=10,
                showgrid=True,
            ),

            baxis=dict(
                title="Sand",
                tick0=0,
                dtick=10,
                showgrid=True,
            ),

            caxis=dict(
                title="Silt",
                tick0=0,
                dtick=10,
                showgrid=True,
            ),
        ),
    )

    print(
        "show_centroids =",
        panel.get("show_centroids", False)
    )

    print(
        "group_by =",
        panel.get("group_by", "None")
    )

    print(
        "points empty =",
        points_df.empty
    )

    if (
            panel.get(
                "show_centroids",
                False,
            )
            and not points_df.empty
    ):

        if using_custom_groups:

            centroid_rows = []

            for group_name in group_colors:

                samples = [
                    sample
                    for sample, groups
                    in sample_to_groups.items()
                    if group_name in groups
                ]

                group_df = plot_df[
                    plot_df["sample"].isin(samples)
                ]

                if len(group_df) == 0:
                    continue

                centroid_rows.append(
                    {
                        "group": group_name,
                        "clay": group_df["clay"].mean(),
                        "sand": group_df["sand"].mean(),
                        "silt": group_df["silt"].mean(),
                    }
                )

            centroids = pd.DataFrame(
                centroid_rows
            )

        else:

            centroids = (
                plot_df
                .groupby("group")[
                    [
                        "clay",
                        "sand",
                        "silt",
                    ]
                ]
                .mean()
                .reset_index()
            )

        symbols = [
            "diamond",
            "square",
            "x",
            "cross",
            "triangle-up",
            "triangle-down",
            "star",
        ]

        print(plot_df.head())
        print(centroids)

        for i, row in centroids.iterrows():
            fig.add_trace(
                go.Scatterternary(
                    a=[row["clay"]],
                    b=[row["sand"]],
                    c=[row["silt"]],

                    mode="markers",

                    marker=dict(
                        size=10,
                        color=darken_color(
                            group_colors[
                                row["group"]
                            ],
                            factor=0.35,
                        ),
                        symbol=symbols[
                            i % len(symbols)
                            ],
                        line=dict(
                            color="black",
                            width=2,
                        ),
                    ),

                    name=(
                        f"{row['group']} "
                        f"Centroid"
                    ),

                    hovertemplate=(
                        f"{row['group']} "
                        f"Centroid"
                        "<br>"
                        f"Clay: "
                        f"{row['clay']:.2f}%"
                        "<br>"
                        f"Sand: "
                        f"{row['sand']:.2f}%"
                        "<br>"
                        f"Silt: "
                        f"{row['silt']:.2f}%"
                        "<extra></extra>"
                    ),

                    showlegend=panel["show_legend"],
                )
            )

    if (
            panel.get(
                "show_covariance",
                False,
            )
            and not plot_df.empty
    ):

        if using_custom_groups:

            grouped = {}

            for group_name in group_colors:
                samples = [
                    sample
                    for sample, groups
                    in sample_to_groups.items()
                    if group_name in groups
                ]

                grouped[group_name] = plot_df[
                    plot_df["sample"].isin(samples)
                ]

        else:

            grouped = {
                str(name): df
                for name, df in plot_df.groupby("group")
            }

        for group_name, group_df in grouped.items():

            if len(group_df) < 3:
                continue

            clay = group_df["clay"].to_numpy()
            sand = group_df["sand"].to_numpy()

            x = (
                    sand
                    + 0.5 * clay
            )

            y = (
                    clay
                    * np.sqrt(3)
                    / 2
            )

            cov = np.cov(
                np.vstack(
                    [x, y]
                )
            )

            eigvals, eigvecs = (
                np.linalg.eigh(cov)
            )

            order = (
                eigvals
                .argsort()[::-1]
            )

            eigvals = eigvals[order]
            eigvecs = eigvecs[:, order]

            theta = np.linspace(
                0,
                2 * np.pi,
                200,
            )

            scale = 2

            ellipse = np.array(
                [
                    scale
                    * np.sqrt(eigvals[0])
                    * np.cos(theta),

                    scale
                    * np.sqrt(eigvals[1])
                    * np.sin(theta),
                ]
            )

            ellipse = (
                    eigvecs
                    @ ellipse
            )

            x0 = x.mean()
            y0 = y.mean()

            ellipse_x = (
                    ellipse[0]
                    + x0
            )

            ellipse_y = (
                    ellipse[1]
                    + y0
            )

            ellipse_clay = (
                    2
                    * ellipse_y
                    / np.sqrt(3)
            )

            ellipse_sand = (
                    ellipse_x
                    - 0.5
                    * ellipse_clay
            )

            ellipse_silt = (
                    100
                    - ellipse_clay
                    - ellipse_sand
            )

            mask = (
                    (ellipse_clay >= 0)
                    & (ellipse_sand >= 0)
                    & (ellipse_silt >= 0)
                    & (ellipse_clay <= 100)
                    & (ellipse_sand <= 100)
                    & (ellipse_silt <= 100)
            )

            fig.add_trace(
                go.Scatterternary(
                    a=ellipse_clay[mask],
                    b=ellipse_sand[mask],
                    c=ellipse_silt[mask],

                    mode="lines",

                    line=dict(
                        color=darken_color(
                            group_colors[
                                group_name
                            ],
                            factor=0.25,
                        ),
                        width=2,
                    ),

                    name=(
                        f"{group_name} "
                        f"Covariance"
                    ),

                    hovertemplate=(
                        f"{group_name} "
                        f"Covariance"
                        "<br>"
                        f"N = {len(group_df)}"
                        "<extra></extra>"
                    ),

                    showlegend=panel[
                        "show_legend"
                    ],
                )
            )

    if panel["show_usda_triangle"]:
        fig = add_usda_triangle(fig)

    return fig

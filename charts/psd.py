import plotly.graph_objects as go
import numpy as np
import pandas as pd

from logic.legendsorting import (
    gsa_sort_key,
)

from logic.filters import NULL_VALUE

from logic.mmes_helpers import (
    get_sample_mmes_row,
    get_psd_columns,
)

from logic.groupcolors import (
    build_group_colors,
    darken_color,
)


def make_psd_plot(
        gsa_df,
        mmes_df,
        mmes_rs_df,
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



    plotted_samples = []
    sample_curves = {}

    for sample in selected_samples:

        (
            row,
            source,
        ) = get_sample_mmes_row(
            sample,
            mmes_df,
            mmes_rs_df,
        )

        if row is None:
            continue

        plotted_samples.append(str(sample))

        (
            psd_cols,
            x_vals,
        ) = get_psd_columns(
            source,
            mmes_df,
            mmes_rs_df,
        )

        y_vals = row[
            psd_cols
        ].tolist()

        sample_curves[str(sample)] = {
            "source": source,
            "x": x_vals,
            "y": y_vals,
        }

    subset = pd.DataFrame(
        {
            "Sample_Name_Final":
                plotted_samples
        }
    )

    if using_custom_groups:

        subset["_group"] = (
            subset["Sample_Name_Final"]
            .astype(str)
            .map(sample_to_group)
            .fillna(NULL_VALUE)
        )

        groups = sorted(
            {
                group
                for groups_list
                in sample_to_groups.values()
                for group in groups_list
            }
        )

        if (
                subset["_group"]
                        .eq(NULL_VALUE)
                        .any()
        ):
            groups.append(NULL_VALUE)

        group_colors = build_group_colors(groups)

    elif group_by != "None":

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

            if sample not in sample_curves:
                continue

            curve = sample_curves[sample]

            x_vals = curve["x"]
            y_vals = curve["y"]

            plot_x = x_vals.copy()

            if x_axis == "phi":
                plot_x = [
                    -np.log2(x / 1000)
                    for x in plot_x
                ]

            mode = (
                "lines+text"
                if show_labels
                else "lines"
            )

            line_color = None

            if using_custom_groups or group_by != "None":

                if group_by == "GSA_ID":
                    group_name = sample
                else:
                    group_name = row["_group"]

                line_color = (
                    group_colors.get(
                        group_name,
                        "#808080"
                    )
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
                         ) + [
                             sample
                         ],
                    textposition="middle right",
                )
            )

    if show_mean and len(subset):

        # -------------------------------------------------
        # Build groups exactly as before
        # -------------------------------------------------

        if (
                group_by == "None"
                and not using_custom_groups
        ):

            grouped = {
                "Mean": subset
            }

            group_colors = {
                "Mean": "#1f77b4"
            }

        elif using_custom_groups:

            grouped = {}

            for group_name in group_colors:

                samples = [
                    sample
                    for sample, groups
                    in sample_to_groups.items()
                    if group_name in groups
                ]

                group_df = subset[
                    subset["Sample_Name_Final"]
                    .astype(str)
                    .isin(samples)
                ]

                grouped[group_name] = group_df

        else:

            grouped = {
                str(name): df
                for name, df
                in subset.groupby("_group")
            }

        # -------------------------------------------------
        # Calculate mean/std for each group
        # -------------------------------------------------

        for group_name, group_df in grouped.items():

            group_samples = (
                group_df["Sample_Name_Final"]
                .astype(str)
                .tolist()
            )

            group_samples = [
                sample
                for sample in group_samples
                if sample in sample_curves
            ]

            # A displayed group mean requires at least
            # two total samples.
            if len(group_samples) < 2:
                continue

            # -------------------------------------------------
            # Split samples by MMES source
            # -------------------------------------------------

            source_samples = {}

            for sample in group_samples:

                source = sample_curves[
                    sample
                ]["source"]

                source_samples.setdefault(
                    source,
                    []
                ).append(sample)

            # -------------------------------------------------
            # Calculate native-bin summary for each source
            #
            # Individual sample curves are NOT interpolated.
            # Each source is summarized on its own native bins.
            # -------------------------------------------------

            source_summaries = {}

            for source, samples in source_samples.items():

                first_curve = sample_curves[
                    samples[0]
                ]

                source_x = np.asarray(
                    first_curve["x"],
                    dtype=float,
                )

                source_curves = []

                for sample in samples:

                    curve = sample_curves[sample]

                    curve_x = np.asarray(
                        curve["x"],
                        dtype=float,
                    )

                    curve_y = np.asarray(
                        curve["y"],
                        dtype=float,
                    )

                    # Samples from the same source should
                    # have identical native grain-size bins.
                    if (
                            len(curve_x) != len(source_x)
                            or not np.array_equal(
                                curve_x,
                                source_x,
                            )
                    ):
                        continue

                    source_curves.append(
                        curve_y
                    )

                if not source_curves:
                    continue

                source_curves = np.asarray(
                    source_curves,
                    dtype=float,
                )

                source_n = len(
                    source_curves
                )

                source_mean = np.nanmean(
                    source_curves,
                    axis=0,
                )

                # n = 1 is allowed for a source when the
                # final group contains samples from another
                # source. Its within-source variance is zero.
                if source_n > 1:

                    source_var = np.nanvar(
                        source_curves,
                        axis=0,
                        ddof=1,
                    )

                else:

                    source_var = np.zeros_like(
                        source_mean,
                        dtype=float,
                    )

                source_summaries[source] = {
                    "n": source_n,
                    "x": source_x,
                    "mean": source_mean,
                    "var": source_var,
                }

            if not source_summaries:
                continue

            total_n = sum(
                summary["n"]
                for summary
                in source_summaries.values()
            )

            if total_n < 2:
                continue

            # -------------------------------------------------
            # ONE SOURCE
            #
            # Preserve native bins. No interpolation.
            # -------------------------------------------------

            if len(source_summaries) == 1:

                summary = next(
                    iter(
                        source_summaries.values()
                    )
                )

                if summary["n"] < 2:
                    continue

                mean_x = summary["x"]
                mean_curve = summary["mean"]

                std_curve = np.sqrt(
                    summary["var"]
                )

            # -------------------------------------------------
            # MULTIPLE SOURCES
            #
            # Interpolate only the SOURCE SUMMARY curves,
            # never the individual sample curves.
            # -------------------------------------------------

            else:

                summaries = list(
                    source_summaries.values()
                )

                # Restrict the combined curve to the grain-size
                # range actually covered by every source.
                common_min = max(
                    np.min(summary["x"])
                    for summary in summaries
                )

                common_max = min(
                    np.max(summary["x"])
                    for summary in summaries
                )

                if common_min >= common_max:
                    continue

                # Use the union of the native measurement bins
                # from both sources within their shared range.
                mean_x = np.unique(
                    np.concatenate([
                        summary["x"][
                            (
                                summary["x"] >= common_min
                            )
                            & (
                                summary["x"] <= common_max
                            )
                        ]
                        for summary in summaries
                    ])
                )

                if len(mean_x) == 0:
                    continue

                # PSD grain-size bins are logarithmically
                # distributed, so interpolate in log grain-size
                # space rather than raw linear micrometers.
                log_mean_x = np.log10(
                    mean_x
                )

                interpolated_summaries = []

                for summary in summaries:

                    source_x = summary["x"]

                    log_source_x = np.log10(
                        source_x
                    )

                    interp_mean = np.interp(
                        log_mean_x,
                        log_source_x,
                        summary["mean"],
                    )

                    interp_var = np.interp(
                        log_mean_x,
                        log_source_x,
                        summary["var"],
                    )

                    interpolated_summaries.append({
                        "n": summary["n"],
                        "mean": interp_mean,
                        "var": interp_var,
                    })

                # ---------------------------------------------
                # Weighted combined mean
                # ---------------------------------------------

                mean_curve = np.zeros(
                    len(mean_x),
                    dtype=float,
                )

                for summary in interpolated_summaries:

                    mean_curve += (
                        summary["n"]
                        * summary["mean"]
                    )

                mean_curve /= total_n

                # ---------------------------------------------
                # Combined sample variance
                #
                # Includes:
                #   1. within-source variation
                #   2. between-source mean differences
                #
                # This is NOT an average of the source SDs.
                # ---------------------------------------------

                combined_m2 = np.zeros(
                    len(mean_x),
                    dtype=float,
                )

                for summary in interpolated_summaries:

                    n = summary["n"]
                    source_mean = summary["mean"]
                    source_var = summary["var"]

                    if n > 1:

                        combined_m2 += (
                            (n - 1)
                            * source_var
                        )

                    combined_m2 += (
                        n
                        * (
                            source_mean
                            - mean_curve
                        ) ** 2
                    )

                combined_var = (
                    combined_m2
                    / (total_n - 1)
                )

                std_curve = np.sqrt(
                    np.maximum(
                        combined_var,
                        0,
                    )
                )

            # -------------------------------------------------
            # Build standard-deviation curves
            # -------------------------------------------------

            plus1 = np.clip(
                mean_curve + std_curve,
                0,
                100,
            )

            minus1 = np.clip(
                mean_curve - std_curve,
                0,
                100,
            )

            plus2 = np.clip(
                mean_curve + 2 * std_curve,
                0,
                100,
            )

            minus2 = np.clip(
                mean_curve - 2 * std_curve,
                0,
                100,
            )

            plus3 = np.clip(
                mean_curve + 3 * std_curve,
                0,
                100,
            )

            minus3 = np.clip(
                mean_curve - 3 * std_curve,
                0,
                100,
            )

            # -------------------------------------------------
            # Convert mean x-axis to selected display axis
            # -------------------------------------------------

            mean_plot_x = mean_x.copy()

            if x_axis == "phi":

                mean_plot_x = (
                    -np.log2(
                        mean_x / 1000
                    )
                )

            # ---------------------------------------------
            # Group color
            # ---------------------------------------------

            group_color = group_colors.get(
                group_name,
                "#808080",
            )

            mean_color = darken_color(
                group_color,
                factor=0.35,
            )

            # ---------------------------------------------
            # Mean
            # ---------------------------------------------

            fig.add_trace(
                go.Scatter(
                    x=mean_plot_x,
                    y=mean_curve,
                    mode="lines",
                    name=f"{group_name} Mean",
                    line=dict(
                        width=5,
                        dash="dash",
                        color=mean_color,
                    ),
                    hovertemplate=(
                        f"{group_name} Mean"
                        "<br>"
                        "Grain Size: %{x:.3g} µm"
                        "<br>"
                        "Percent Passing: %{y:.1f}%"
                        "<extra></extra>"
                    ),
                )
            )

            # ---------------------------------------------
            # ±1 standard deviation
            # ---------------------------------------------

            if show_std1:

                for y, sign in [
                    (plus1, "+1σ"),
                    (minus1, "-1σ"),
                ]:

                    fig.add_trace(
                        go.Scatter(
                            x=mean_plot_x,
                            y=y,
                            mode="lines",
                            name=(
                                f"{group_name} "
                                f"{sign}"
                            ),
                            line=dict(
                                color=mean_color,
                                width=2,
                                dash="dot",
                            ),
                            hovertemplate=(
                                f"{group_name} {sign}"
                                "<br>"
                                "Grain Size: %{x:.3g} µm"
                                "<br>"
                                "Percent Passing: %{y:.1f}%"
                                "<extra></extra>"
                            ),
                        )
                    )

            # ---------------------------------------------
            # ±2 standard deviations
            # ---------------------------------------------

            if show_std2:

                for y, sign in [
                    (plus2, "+2σ"),
                    (minus2, "-2σ"),
                ]:

                    fig.add_trace(
                        go.Scatter(
                            x=mean_plot_x,
                            y=y,
                            mode="lines",
                            name=(
                                f"{group_name} "
                                f"{sign}"
                            ),
                            line=dict(
                                color=mean_color,
                                width=2,
                                dash="dashdot",
                            ),
                            hovertemplate=(
                                f"{group_name} {sign}"
                                "<br>"
                                "Grain Size: %{x:.3g} µm"
                                "<br>"
                                "Percent Passing: %{y:.1f}%"
                                "<extra></extra>"
                            ),
                        )
                    )

            # ---------------------------------------------
            # ±3 standard deviations
            # ---------------------------------------------

            if show_std3:

                for y, sign in [
                    (plus3, "+3σ"),
                    (minus3, "-3σ"),
                ]:

                    fig.add_trace(
                        go.Scatter(
                            x=mean_plot_x,
                            y=y,
                            mode="lines",
                            name=(
                                f"{group_name} "
                                f"{sign}"
                            ),
                            line=dict(
                                color=mean_color,
                                width=1,
                                dash="longdash",
                            ),
                            hovertemplate=(
                                f"{group_name} {sign}"
                                "<br>"
                                "Grain Size: %{x:.3g} µm"
                                "<br>"
                                "Percent Passing: %{y:.1f}%"
                                "<extra></extra>"
                            ),
                        )
                    )

    fig.update_layout(
        title="PSD Undersize",
        xaxis_title="Grain Size (µm)",
        yaxis_title="Percent Passing (%)",
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

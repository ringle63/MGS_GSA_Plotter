import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from plotly.subplots import make_subplots

from dash import (
    html,
    dcc,
)

from logic.groupcolors import (
    build_group_colors,
)

from logic.mmes_helpers import (
    get_sample_mmes_row,
    get_psd_columns,
    get_fr_columns,
)

from logic.multivariate import (
    calculate_pca,
    calculate_hierarchical,
)

from logic.mastersizer_multivariate import (
    prepare_mastersizer_analysis,
)

from charts.pca import (
    GRAPH_CONFIG,
    _get_existing_groups,
    _get_borehole_data,
    _card,
    _make_score_figure,
    _make_scree_figure,
    _make_silhouette_figure,
    _make_cluster_membership_table,
    _make_group_cluster_heatmap,
    _build_summary_table,
    _build_hierarchy_panel,
    _make_borehole_figure,
)


def _make_mastersizer_loadings_figure(
        loadings,
        bin_sizes,
        input_mode,
):
    """
    Ordered PC1/PC2 loading curves.

    A curve is more readable than ~100 grouped loading bars when
    each variable is an ordered particle-size bin.
    """

    records = []

    for variable in loadings.index:

        if variable not in bin_sizes:
            continue

        records.append(
            (
                float(
                    bin_sizes[
                        variable
                    ]
                ),
                float(
                    loadings.loc[
                        variable,
                        "PC1",
                    ]
                ),
                float(
                    loadings.loc[
                        variable,
                        "PC2",
                    ]
                ),
            )
        )

    records.sort(
        key=lambda row: row[0]
    )

    fig = go.Figure()

    if not records:
        return fig

    x = [
        row[0]
        for row in records
    ]

    pc1 = [
        row[1]
        for row in records
    ]

    pc2 = [
        row[2]
        for row in records
    ]

    fig.add_trace(
        go.Scatter(
            x=x,
            y=pc1,
            mode="lines",
            name="PC1",
            hovertemplate=(
                "Particle size: %{x:.4g} µm"
                "<br>PC1 loading: %{y:.4f}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x,
            y=pc2,
            mode="lines",
            name="PC2",
            hovertemplate=(
                "Particle size: %{x:.4g} µm"
                "<br>PC2 loading: %{y:.4f}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_hline(
        y=0,
        line_width=1,
        line_dash="dot",
    )

    fig.update_layout(
        height=390,

        margin=dict(
            l=70,
            r=25,
            t=15,
            b=65,
        ),

        legend=dict(
            orientation="h",
            x=0.5,
            y=1.08,
            xanchor="center",
        ),
    )

    fig.update_xaxes(
        type="log",
        title="Particle Size (µm)",
        automargin=True,
    )

    fig.update_yaxes(
        title="PCA Loading",
        automargin=True,
    )

    return fig


def _top_loading_arrows(
        loadings,
        bin_sizes,
        n=12,
):
    """
    Keep loading-arrow mode usable by showing only the strongest
    PC1/PC2 vectors rather than every Mastersizer bin.
    """

    if loadings is None or loadings.empty:
        return loadings

    strength = np.sqrt(
        loadings["PC1"] ** 2
        + loadings["PC2"] ** 2
    )

    keep = (
        strength
        .sort_values(
            ascending=False
        )
        .head(n)
        .index
        .tolist()
    )

    output = (
        loadings
        .loc[
            keep,
            [
                "PC1",
                "PC2",
            ],
        ]
        .copy()
    )

    output.index = [
        (
            f"{bin_sizes.get(variable, float('nan')):.4g} µm"
        )
        for variable
        in keep
    ]

    return output


def _native_curve_for_sample(
        sample,
        input_mode,
        mmes_df,
        mmes_rs_df,
):
    (
        row,
        source,
    ) = get_sample_mmes_row(
        sample,
        mmes_df,
        mmes_rs_df,
    )

    if row is None:
        return None

    if input_mode == "psd":

        columns, x_values = (
            get_psd_columns(
                source,
                mmes_df,
                mmes_rs_df,
            )
        )

    else:

        columns, x_values = (
            get_fr_columns(
                source,
                mmes_df,
                mmes_rs_df,
            )
        )

    y_values = pd.to_numeric(
        row[columns],
        errors="coerce",
    ).to_numpy(
        dtype=float
    )

    x_values = np.asarray(
        x_values,
        dtype=float,
    )

    valid = (
        np.isfinite(x_values)
        & (x_values > 0)
        & np.isfinite(y_values)
    )

    if valid.sum() < 2:
        return None

    return {
        "source":
            source,

        "x":
            x_values[
                valid
            ],

        "y":
            y_values[
                valid
            ],
    }


def _combine_group_curve_summary(
        group_samples,
        input_mode,
        mmes_df,
        mmes_rs_df,
):
    """
    Same PRIMARY/RS summary architecture used by the normal
    PSD/Frequency charts:

      * summarize each source on its native grid
      * if only one source, retain that native grid
      * if sources are mixed, interpolate SOURCE summaries only
        in log grain-size space
      * combine means and sample variances using sample counts
    """

    curves = {}

    for sample in group_samples:

        curve = _native_curve_for_sample(
            sample,
            input_mode,
            mmes_df,
            mmes_rs_df,
        )

        if curve is not None:
            curves[
                str(sample)
            ] = curve

    if len(curves) < 2:
        return None

    source_samples = {}

    for sample, curve in curves.items():

        source_samples.setdefault(
            curve[
                "source"
            ],
            [],
        ).append(
            sample
        )

    source_summaries = {}

    for source, samples in (
            source_samples.items()
    ):

        first = curves[
            samples[0]
        ]

        source_x = np.asarray(
            first[
                "x"
            ],
            dtype=float,
        )

        source_curves = []

        for sample in samples:

            curve = curves[
                sample
            ]

            curve_x = np.asarray(
                curve[
                    "x"
                ],
                dtype=float,
            )

            curve_y = np.asarray(
                curve[
                    "y"
                ],
                dtype=float,
            )

            if (
                    len(curve_x)
                    != len(source_x)
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

        source_summaries[
            source
        ] = {
            "n":
                source_n,

            "x":
                source_x,

            "mean":
                source_mean,

            "var":
                source_var,
        }

    if not source_summaries:
        return None

    total_n = sum(
        summary[
            "n"
        ]
        for summary
        in source_summaries.values()
    )

    if total_n < 2:
        return None

    if len(
            source_summaries
    ) == 1:

        summary = next(
            iter(
                source_summaries.values()
            )
        )

        if summary[
            "n"
        ] < 2:
            return None

        mean_x = summary[
            "x"
        ]

        mean_curve = summary[
            "mean"
        ]

        std_curve = np.sqrt(
            summary[
                "var"
            ]
        )

    else:

        summaries = list(
            source_summaries.values()
        )

        common_min = max(
            np.min(
                summary[
                    "x"
                ]
            )
            for summary
            in summaries
        )

        common_max = min(
            np.max(
                summary[
                    "x"
                ]
            )
            for summary
            in summaries
        )

        if common_min >= common_max:
            return None

        mean_x = np.unique(
            np.concatenate(
                [
                    summary[
                        "x"
                    ][
                        (
                            summary[
                                "x"
                            ]
                            >= common_min
                        )
                        & (
                            summary[
                                "x"
                            ]
                            <= common_max
                        )
                    ]
                    for summary
                    in summaries
                ]
            )
        )

        if len(mean_x) == 0:
            return None

        log_mean_x = np.log10(
            mean_x
        )

        interpolated = []

        for summary in summaries:

            log_source_x = np.log10(
                summary[
                    "x"
                ]
            )

            interp_mean = np.interp(
                log_mean_x,
                log_source_x,
                summary[
                    "mean"
                ],
            )

            interp_var = np.interp(
                log_mean_x,
                log_source_x,
                summary[
                    "var"
                ],
            )

            interpolated.append(
                {
                    "n":
                        summary[
                            "n"
                        ],

                    "mean":
                        interp_mean,

                    "var":
                        interp_var,
                }
            )

        mean_curve = np.zeros(
            len(
                mean_x
            ),
            dtype=float,
        )

        for summary in interpolated:

            mean_curve += (
                summary[
                    "n"
                ]
                * summary[
                    "mean"
                ]
            )

        mean_curve /= total_n

        combined_m2 = np.zeros(
            len(
                mean_x
            ),
            dtype=float,
        )

        for summary in interpolated:

            n = summary[
                "n"
            ]

            source_mean = summary[
                "mean"
            ]

            source_var = summary[
                "var"
            ]

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
            / (
                total_n
                - 1
            )
        )

        std_curve = np.sqrt(
            np.maximum(
                combined_var,
                0,
            )
        )

    return {
        "x":
            mean_x,

        "mean":
            mean_curve,

        "std":
            std_curve,

        "n":
            total_n,
    }


def _make_curve_small_multiples(
        scores,
        input_mode,
        mmes_df,
        mmes_rs_df,
        display_group_colors,
        cluster_palette,
        color_mode,
        show_mean,
        show_std1,
        show_std2,
        show_std3,
):
    """
    One mini native-data PSD/Frequency summary per current
    cluster/group, arranged four across when space permits.
    """

    groups = (
        scores[
            "_group"
        ]
        .astype(str)
        .value_counts()
        .index
        .tolist()
    )

    if not groups:

        fig = go.Figure()

        fig.add_annotation(
            text="No curve groups available.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
        )

        return fig

    n_cols = min(
        4,
        len(
            groups
        ),
    )

    n_rows = int(
        math.ceil(
            len(
                groups
            )
            / n_cols
        )
    )

    if n_rows <= 1:
        vertical_spacing = 0.0
    else:
        vertical_spacing = min(
            0.038,
            0.18
            / (
                n_rows
                - 1
            ),
        )

    fig = make_subplots(
        rows=n_rows,
        cols=n_cols,
        subplot_titles=[
            str(
                group
            )
            for group
            in groups
        ],
        # Four-across layout with enough horizontal separation
        # to keep neighboring axes readable without wasting space.
        horizontal_spacing=0.055,
        vertical_spacing=
            vertical_spacing,
    )

    std_levels = []

    if show_std3:
        std_levels.append(
            3
        )

    if show_std2:
        std_levels.append(
            2
        )

    if show_std1:
        std_levels.append(
            1
        )

    # Draw wider bands first.
    std_levels = sorted(
        std_levels,
        reverse=True,
    )

    for index, group in enumerate(
            groups
    ):

        row_num = (
            index
            // n_cols
        ) + 1

        col_num = (
            index
            % n_cols
        ) + 1

        group_samples = (
            scores.loc[
                scores[
                    "_group"
                ]
                .astype(str)
                == str(
                    group
                ),
                "GSA_ID",
            ]
            .astype(str)
            .tolist()
        )

        summary = (
            _combine_group_curve_summary(
                group_samples,
                input_mode,
                mmes_df,
                mmes_rs_df,
            )
        )

        if summary is None:

            fig.add_annotation(
                text="N < 2",
                x=0.5,
                y=0.5,
                xref=(
                    "x domain"
                    if (
                        row_num == 1
                        and col_num == 1
                    )
                    else None
                ),
                yref=(
                    "y domain"
                    if (
                        row_num == 1
                        and col_num == 1
                    )
                    else None
                ),
                showarrow=False,
                row=row_num,
                col=col_num,
            )

            continue

        if color_mode == "cluster":

            color = (
                cluster_palette.get(
                    str(
                        group
                    ),
                    "#777777",
                )
            )

        else:

            color = (
                display_group_colors.get(
                    str(
                        group
                    ),
                    "#777777",
                )
            )

        x = np.asarray(
            summary[
                "x"
            ],
            dtype=float,
        )

        mean = np.asarray(
            summary[
                "mean"
            ],
            dtype=float,
        )

        std = np.asarray(
            summary[
                "std"
            ],
            dtype=float,
        )

        for level in std_levels:

            lower = (
                mean
                - (
                    level
                    * std
                )
            )

            upper = (
                mean
                + (
                    level
                    * std
                )
            )

            if input_mode == "psd":

                lower = np.clip(
                    lower,
                    0,
                    100,
                )

                upper = np.clip(
                    upper,
                    0,
                    100,
                )

            else:

                lower = np.clip(
                    lower,
                    0,
                    None,
                )

            alpha = {
                1:
                    0.22,

                2:
                    0.14,

                3:
                    0.09,
            }[
                level
            ]

            fill_color = (
                color
                if str(
                    color
                ).startswith(
                    "rgba"
                )
                else (
                    "rgba("
                    + ",".join(
                        str(
                            int(
                                str(
                                    color
                                ).lstrip(
                                    "#"
                                )[
                                    i:
                                    i + 2
                                ],
                                16,
                            )
                        )
                        for i
                        in (
                            0,
                            2,
                            4,
                        )
                    )
                    + f",{alpha})"
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=lower,
                    mode="lines",
                    line=dict(
                        width=0,
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                ),
                row=row_num,
                col=col_num,
            )

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=upper,
                    mode="lines",
                    line=dict(
                        width=0,
                    ),
                    fill="tonexty",
                    fillcolor=
                        fill_color,
                    hovertemplate=(
                        f"{group}"
                        f"<br>±{level} SD"
                        "<br>Particle size: %{x:.4g} µm"
                        "<br>Upper: %{y:.3f}"
                        "<extra></extra>"
                    ),
                    showlegend=False,
                ),
                row=row_num,
                col=col_num,
            )

        if show_mean:

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=mean,
                    mode="lines",
                    line=dict(
                        color=color,
                        width=2,
                    ),
                    customdata=np.full(
                        len(
                            x
                        ),
                        summary[
                            "n"
                        ],
                    ),
                    hovertemplate=(
                        f"{group}"
                        "<br>Particle size: %{x:.4g} µm"
                        "<br>Mean: %{y:.3f}"
                        "<br>N: %{customdata}"
                        "<extra></extra>"
                    ),
                    showlegend=False,
                ),
                row=row_num,
                col=col_num,
            )

        fig.update_xaxes(
            type="log",
            tickfont=dict(
                size=9,
            ),
            automargin=True,
            row=row_num,
            col=col_num,
        )

        if input_mode == "psd":

            fig.update_yaxes(
                range=[
                    0,
                    100,
                ],
                tickfont=dict(
                    size=9,
                ),
                automargin=True,
                row=row_num,
                col=col_num,
            )

        else:

            fig.update_yaxes(
                rangemode="tozero",
                tickfont=dict(
                    size=9,
                ),
                automargin=True,
                row=row_num,
                col=col_num,
            )

    # Middle-ground row height: compact, but with enough
    # room for subplot titles and log-scale x-axis labels.
    figure_height = max(
        520,
        320
        * n_rows,
    )

    fig.update_layout(
        height=
            figure_height,

        margin=dict(
            l=70,
            r=30,
            t=48,
            b=76,
        ),

        showlegend=False,
    )

    fig.add_annotation(
        text="Particle Size (µm, log scale)",
        x=0.5,
        y=-0.075,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(
            size=11,
        ),
    )

    fig.add_annotation(
        text=(
            "Undersize (%)"
            if input_mode
            == "psd"
            else "Frequency (%)"
        ),
        x=-0.045,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        textangle=-90,
        font=dict(
            size=11,
        ),
    )

    return fig


def make_mastersizer_pca_plot(
        gsa_df,
        mmes_df,
        mmes_rs_df,
        selected_samples,
        panel,
):
    """
    Mastersizer-only PCA report.

    Reuses the generic PCA report architecture while building
    PCA variables automatically from either:
      * FR frequency bins, or
      * PSD undersize bins.
    """

    input_mode = panel.get(
        "mastersizer_pca_input",
        "frequency",
    )

    standardize_requested = (
        panel.get(
            "analysis_standardize",
            True,
        )
    )

    prepared_input = (
        prepare_mastersizer_analysis(
            gsa_df,
            mmes_df,
            mmes_rs_df,
            selected_samples,
            input_mode=
                input_mode,
        )
    )

    if prepared_input is None:

        return html.Div(
            (
                "Mastersizer PCA — fewer than two usable "
                "Mastersizer samples or insufficient common "
                "particle-size bins were available."
            ),

            style={
                "padding":
                    "20px",

                "fontWeight":
                    "600",
            },
        )

    analysis_df = (
        prepared_input[
            "dataframe"
        ]
    )

    analysis_samples = (
        prepared_input[
            "samples"
        ]
    )

    variables = (
        prepared_input[
            "variables"
        ]
    )

    if input_mode == "frequency":

        # Frequency analysis follows the original R primary
        # workflow: CLR coordinates are centered by PCA but are
        # not rescaled to unit variance.
        standardize = False

    else:

        standardize = bool(
            standardize_requested
        )

    linkage_method = panel.get(
        "cluster_linkage",
        "ward",
    )

    distance_metric = panel.get(
        "cluster_metric",
        "euclidean",
    )

    cluster_k = panel.get(
        "cluster_k",
        4,
    )

    color_mode = panel.get(
        "pca_color_mode",
        "group",
    )

    show_loading_arrows = panel.get(
        "show_loading_arrows",
        False,
    )

    report_sections = set(
        panel.get(
            "pca_report_sections",
            [
                "scores",
                "scree",
                "loadings",
                "hierarchy",
                "heatmap",
                "grain_histogram",
                "silhouette",
                "cluster_summary",
            ],
        )
        or []
    )

    show_depth_borehole = (
        "depth"
        in report_sections
    )

    borehole_vertical_axis = panel.get(
        "borehole_vertical_axis",
        "depth",
    )

    hierarchy_summary_stats = panel.get(
        "hierarchy_summary_stats",
        [
            "n",
            "median",
        ],
    )

    hierarchy_summary_variables = [
        variable
        for variable
        in (
            panel.get(
                "hierarchy_summary_variables",
                [],
            )
            or []
        )
        if variable
        in analysis_df.columns
    ]

    pca_result = calculate_pca(
        analysis_df,
        analysis_samples,
        variables,
        standardize=standardize,
    )

    if pca_result is None:

        return html.Div(
            "Mastersizer PCA could not be calculated.",
            style={
                "padding":
                    "20px",
            },
        )

    cluster_result = (
        calculate_hierarchical(
            analysis_df,
            analysis_samples,
            variables,
            standardize=standardize,
            linkage_method=
                linkage_method,
            distance_metric=
                distance_metric,
            cluster_k=
                cluster_k,
            silhouette_k_min=2,
            silhouette_k_max=10,
            summary_variables=
                hierarchy_summary_variables,
        )
    )

    if cluster_result is None:

        return html.Div(
            "Mastersizer PCA / clustering could not be calculated.",
            style={
                "padding":
                    "20px",
            },
        )

    scores = (
        pca_result[
            "scores"
        ]
        .copy()
        .merge(
            cluster_result[
                "clusters"
            ],
            on="GSA_ID",
            how="left",
        )
    )

    selected_k = (
        cluster_result[
            "selected_k"
        ]
    )

    cluster_names = [
        f"Cluster {cluster}"
        for cluster
        in sorted(
            cluster_result[
                "clusters"
            ][
                "Cluster"
            ]
            .astype(int)
            .unique()
        )
    ]

    cluster_palette = (
        build_group_colors(
            cluster_names
        )
    )

    if color_mode == "cluster":

        scores[
            "_group"
        ] = (
            "Cluster "
            + scores[
                "Cluster"
            ]
            .astype(int)
            .astype(str)
        )

    else:

        scores = _get_existing_groups(
            scores,
            gsa_df,
            panel,
        )

    display_groups = sorted(
        scores[
            "_group"
        ]
        .astype(str)
        .unique()
    )

    if color_mode == "cluster":

        display_group_colors = (
            cluster_palette
        )

    else:

        display_group_colors = (
            build_group_colors(
                display_groups
            )
        )

    show_labels = panel.get(
        "show_labels",
        False,
    )

    show_legend = panel.get(
        "show_legend",
        True,
    )

    if input_mode == "frequency":

        input_label = (
            "Frequency Bins (FR)"
        )

        preprocessing_label = (
            "FR bins → ≥80% zero-bin removal → "
            "closure → multiplicative zero replacement → CLR"
        )

    else:

        input_label = (
            "PSD Undersize Bins"
        )

        preprocessing_label = (
            "PSD bins on common log-size grid; "
            + (
                "standardized"
                if standardize
                else "unstandardized"
            )
        )

    source_counts = (
        prepared_input[
            "source_counts"
        ]
    )

    source_text = ", ".join(
        (
            f"{source}: {count}"
        )
        for source, count
        in sorted(
            source_counts.items()
        )
    )

    header = html.Div(
        [
            html.Div(
                "PCA - Mastersizer Only",

                style={
                    "fontSize":
                        "1.35rem",

                    "fontWeight":
                        "500",

                    "marginBottom":
                        "2px",
                },
            ),

            html.Div(
                (
                    f"{len(scores)} samples; "
                    f"{len(pca_result['variables'])} retained bins; "
                    f"{cluster_result['linkage_method'].title()} linkage; "
                    f"{cluster_result['distance_metric'].title()} distance; "
                    f"sources: {source_text}"
                ),

                style={
                    "fontSize":
                        "0.90rem",

                    "marginBottom":
                        "7px",
                },
            ),

            html.Div(
                [
                    html.Span(
                        "PCA Input: ",
                        style={
                            "fontWeight":
                                "700",
                        },
                    ),

                    html.Span(
                        input_label
                    ),

                    html.Br(),

                    html.Span(
                        "Preprocessing: ",
                        style={
                            "fontWeight":
                                "700",
                        },
                    ),

                    html.Span(
                        preprocessing_label
                    ),

                    html.Br(),

                    html.Span(
                        "Retained particle-size range: ",
                        style={
                            "fontWeight":
                                "700",
                        },
                    ),

                    html.Span(
                        (
                            f"{min(prepared_input['retained_x']):.4g}"
                            "–"
                            f"{max(prepared_input['retained_x']):.4g} µm"
                        )
                    ),
                ],

                style={
                    "fontSize":
                        "0.91rem",

                    "lineHeight":
                        "1.45",
                },
            ),
        ],

        style={
            "gridColumn":
                "1 / -1",

            "marginBottom":
                "2px",
        },
    )

    score_loadings = (
        pca_result[
            "loadings"
        ]
    )

    if show_loading_arrows:

        score_loadings = (
            _top_loading_arrows(
                score_loadings,
                prepared_input[
                    "bin_sizes"
                ],
                n=12,
            )
        )

    score_fig = (
        _make_score_figure(
            scores,
            pca_result[
                "explained_variance_ratio"
            ],
            score_loadings,
            display_group_colors,
            show_labels,
            show_legend,
            color_mode,
            show_loading_arrows=
                show_loading_arrows,
        )
    )

    # Mastersizer PCA can contain well over 100 components.
    # The scree chart itself only displays components explaining
    # at least 0.1% of total variance. This removes the long tail
    # of nearly-zero bars instead of merely hiding their labels,
    # so the useful PCs occupy the full chart width.
    scree_explained = np.asarray(
        pca_result[
            "explained_variance_ratio"
        ],
        dtype=float,
    )

    scree_cumulative = np.asarray(
        pca_result[
            "cumulative_variance_ratio"
        ],
        dtype=float,
    )

    scree_keep = (
        scree_explained
        * 100.0
        >= 0.1
    )

    # PCA components are ordered from greatest to least
    # explained variance, so this normally keeps one continuous
    # leading block of PCs.
    scree_explained_display = (
        scree_explained[
            scree_keep
        ]
    )

    scree_cumulative_display = (
        scree_cumulative[
            scree_keep
        ]
    )

    # Defensive fallback: always show at least PC1.
    if len(
            scree_explained_display
    ) == 0:

        scree_explained_display = (
            scree_explained[
                :1
            ]
        )

        scree_cumulative_display = (
            scree_cumulative[
                :1
            ]
        )

    # Build the Mastersizer scree plot directly with a numeric
    # component axis. Using categorical "PC1", "PC2", ... values
    # can retain a much larger category domain in Plotly after
    # the long PCA tail is removed, which leaves the retained
    # bars bunched at the left. A numeric axis guarantees that
    # the retained PCs fill the available chart width.
    scree_component_numbers = np.arange(
        1,
        len(
            scree_explained_display
        )
        + 1,
        dtype=int,
    )

    scree_component_labels = [
        f"PC{i}"
        for i
        in scree_component_numbers
    ]

    scree_fig = go.Figure()

    scree_fig.add_trace(
        go.Bar(
            x=scree_component_numbers,
            y=(
                scree_explained_display
                * 100.0
            ),

            width=0.82,

            customdata=(
                scree_cumulative_display
                * 100.0
            ),

            hovertemplate=(
                "PC%{x}"
                "<br>Variance explained: %{y:.2f}%"
                "<br>Cumulative: %{customdata:.2f}%"
                "<extra></extra>"
            ),
        )
    )

    scree_fig.update_layout(
        height=390,

        margin=dict(
            l=65,
            r=20,
            t=15,
            b=85,
        ),

        showlegend=False,
        bargap=0.10,
    )

    scree_fig.update_xaxes(
        title="Principal Component",

        type="linear",

        range=[
            0.35,
            len(
                scree_component_numbers
            )
            + 0.65,
        ],

        tickmode="array",
        tickvals=
            scree_component_numbers,
        ticktext=
            scree_component_labels,

        tickangle=-45,

        tickfont=dict(
            size=10,
        ),

        automargin=True,
    )

    scree_fig.update_yaxes(
        title="Variance Explained (%)",

        rangemode="tozero",

        automargin=True,
    )

    loadings_fig = (
        _make_mastersizer_loadings_figure(
            pca_result[
                "loadings"
            ],
            prepared_input[
                "bin_sizes"
            ],
            input_mode,
        )
    )

    silhouette_fig = (
        _make_silhouette_figure(
            cluster_result[
                "silhouette"
            ],
            selected_k,
        )
    )

    hierarchy_panel = (
        _build_hierarchy_panel(
            cluster_result[
                "hierarchy"
            ],
            hierarchy_summary_variables,
            selected_k,
            cluster_palette,
            hierarchy_summary_stats,
        )
    )

    # For Mastersizer PCA, avoid a ~100-column bin summary.
    # Reuse the selected descriptive summary variables instead.
    selected_k_summary = None

    hierarchy = (
        cluster_result.get(
            "hierarchy"
        )
    )

    if (
            hierarchy is not None
            and selected_k
            in hierarchy[
                "summaries"
            ]
    ):

        selected_k_summary = (
            hierarchy[
                "summaries"
            ][
                selected_k
            ]
        )

    if selected_k_summary is None:

        selected_k_summary = (
            cluster_result[
                "cluster_summary"
            ]
        )

        summary_variables = []

    else:

        summary_variables = (
            hierarchy_summary_variables
        )

    summary_table = (
        _build_summary_table(
            selected_k_summary,
            summary_variables,
            cluster_palette,
        )
    )

    if color_mode == "cluster":

        membership_fig = (
            _make_cluster_membership_table(
                scores,
                selected_k,
                cluster_palette,
            )
        )

        membership_title = (
            "Cluster Membership "
            f"(k = {selected_k})"
        )

        membership_filename = (
            "MGS_GSA_Mastersizer_PCA_"
            "Cluster_Membership"
        )

    else:

        membership_fig = (
            _make_group_cluster_heatmap(
                scores,
                selected_k,
            )
        )

        membership_title = (
            "Group × Cluster Heatmap "
            f"(k = {selected_k})"
        )

        membership_filename = (
            "MGS_GSA_Mastersizer_PCA_"
            "Group_Cluster_Heatmap"
        )

    curve_fig = (
        _make_curve_small_multiples(
            scores,
            input_mode,
            mmes_df,
            mmes_rs_df,
            display_group_colors,
            cluster_palette,
            color_mode,
            panel.get(
                "show_mean",
                False,
            ),
            panel.get(
                "show_std1",
                False,
            ),
            panel.get(
                "show_std2",
                False,
            ),
            panel.get(
                "show_std3",
                False,
            ),
        )
    )

    curve_label = (
        "PSD Undersize"
        if input_mode
        == "psd"
        else "Frequency"
    )

    report_id = (
        f"pca-report-"
        f"{panel['id']}"
    )

    download_controls = html.Div(
        [
            html.Button(
                "⬇ PNG Report",

                id=(
                    "download-pca-report-"
                    f"{panel['id']}"
                ),

                n_clicks=0,

                **{
                    "data-panel-id":
                        str(
                            panel[
                                "id"
                            ]
                        )
                },

                style={
                    "padding":
                        "6px 10px",

                    "cursor":
                        "pointer",
                },
            ),
        ],

        style={
            "display":
                "flex",

            "justifyContent":
                "flex-end",

            "marginBottom":
                "6px",
        },
    )

    pair_grid_style = {
        "display":
            "grid",

        "gridTemplateColumns":
            (
                "repeat("
                "auto-fit, "
                "minmax("
                "460px, 1fr"
                ")"
            ),

        "gap":
            "22px",

        "width":
            "100%",

        "alignItems":
            "start",
    }

    dashboard_children = [
        header,
    ]

    if "scores" in report_sections:

        dashboard_children.append(
            _card(
                "PCA Scores",

                dcc.Graph(
                    figure=score_fig,
                    responsive=True,
                    config={
                        **GRAPH_CONFIG,

                        "toImageButtonOptions": {
                            "format":
                                "png",

                            "filename":
                                "MGS_GSA_Mastersizer_PCA_Scores",

                            "scale":
                                2,
                        },
                    },
                    style={
                        "width":
                            "100%",
                    },
                ),
            )
        )

    if "heatmap" in report_sections:

        dashboard_children.append(
            _card(
                membership_title,

                dcc.Graph(
                    figure=
                        membership_fig,
                    responsive=True,
                    config={
                        **GRAPH_CONFIG,

                        "toImageButtonOptions": {
                            "format":
                                "png",

                            "filename":
                                membership_filename,

                            "scale":
                                2,
                        },
                    },
                    style={
                        "width":
                            "100%",
                    },
                ),
            )
        )

    # Reuse the generic "grain_histogram" report-section value
    # so saved section visibility stays compatible. In this
    # Mastersizer-only report the card contains native MMES curves.
    if "grain_histogram" in report_sections:

        curve_height = (
            curve_fig.layout.height
            or 500
        )

        dashboard_children.append(
            _card(
                (
                    f"Mean {curve_label} Curves — "
                    + (
                        f"Clusters (k = {selected_k})"
                        if color_mode
                        == "cluster"
                        else "Current Grouping"
                    )
                ),

                dcc.Graph(
                    figure=
                        curve_fig,

                    responsive=True,

                    config={
                        **GRAPH_CONFIG,

                        "toImageButtonOptions": {
                            "format":
                                "png",

                            "filename":
                                (
                                    "MGS_GSA_Mastersizer_PCA_"
                                    f"{curve_label.replace(' ', '_')}_Curves"
                                ),

                            "scale":
                                2,
                        },
                    },

                    style={
                        "width":
                            "100%",

                        "height":
                            f"{int(curve_height)}px",

                        "minHeight":
                            f"{int(curve_height)}px",
                    },
                ),
            )
        )

    upper_pair = []

    if "scree" in report_sections:

        upper_pair.append(
            _card(
                "Scree Plot",

                dcc.Graph(
                    figure=
                        scree_fig,
                    responsive=True,
                    config={
                        **GRAPH_CONFIG,

                        "toImageButtonOptions": {
                            "format":
                                "png",

                            "filename":
                                "MGS_GSA_Mastersizer_PCA_Scree",

                            "scale":
                                2,
                        },
                    },
                    style={
                        "width":
                            "100%",
                    },
                ),
            )
        )

    if "loadings" in report_sections:

        upper_pair.append(
            _card(
                "PC1 / PC2 Loading Curves",

                dcc.Graph(
                    figure=
                        loadings_fig,
                    responsive=True,
                    config={
                        **GRAPH_CONFIG,

                        "toImageButtonOptions": {
                            "format":
                                "png",

                            "filename":
                                "MGS_GSA_Mastersizer_PCA_Loadings",

                            "scale":
                                2,
                        },
                    },
                    style={
                        "width":
                            "100%",
                    },
                ),
            )
        )

    if upper_pair:

        dashboard_children.append(
            html.Div(
                upper_pair,
                style=
                    pair_grid_style,
            )
        )

    if "hierarchy" in report_sections:

        dashboard_children.append(
            _card(
                (
                    "Cluster Hierarchy Summary "
                    f"(selected k = {selected_k})"
                ),
                hierarchy_panel,
            )
        )

    lower_pair = []

    if "silhouette" in report_sections:

        lower_pair.append(
            _card(
                "Silhouette by Number of Clusters",

                dcc.Graph(
                    figure=
                        silhouette_fig,
                    responsive=True,
                    config={
                        **GRAPH_CONFIG,

                        "toImageButtonOptions": {
                            "format":
                                "png",

                            "filename":
                                "MGS_GSA_Mastersizer_PCA_Silhouette",

                            "scale":
                                2,
                        },
                    },
                    style={
                        "width":
                            "100%",
                    },
                ),
            )
        )

    if "cluster_summary" in report_sections:

        lower_pair.append(
            _card(
                (
                    "Cluster Summary "
                    f"(k = {selected_k})"
                ),
                summary_table,
            )
        )

    if lower_pair:

        dashboard_children.append(
            html.Div(
                lower_pair,
                style=
                    pair_grid_style,
            )
        )

    if show_depth_borehole:

        depth_result = (
            _get_borehole_data(
                gsa_df,
                cluster_result[
                    "clusters"
                ],
                vertical_axis=
                    borehole_vertical_axis,
            )
        )

        if (
                depth_result is not None
                and not depth_result[
                    "data"
                ].empty
        ):

            depth_fig = (
                _make_borehole_figure(
                    depth_result[
                        "data"
                    ],
                    cluster_palette,
                    depth_result[
                        "vertical_field"
                    ],
                    depth_result[
                        "vertical_label"
                    ],
                    depth_result[
                        "reverse_y"
                    ],
                )
            )

            depth_child = html.Div(
                [
                    html.Div(
                        (
                            "Drag the lower-right resize handle "
                            "to make this plot taller or shorter."
                        ),
                        style={
                            "fontSize":
                                "0.78rem",

                            "color":
                                "#667085",

                            "marginBottom":
                                "4px",
                        },
                    ),

                    dcc.Graph(
                        figure=
                            depth_fig,
                        responsive=True,
                        config={
                            **GRAPH_CONFIG,

                            "toImageButtonOptions": {
                                "format":
                                    "png",

                                "filename":
                                    (
                                        "MGS_GSA_Mastersizer_PCA_"
                                        "Clusters_by_Borehole"
                                    ),

                                "scale":
                                    2,
                            },
                        },
                        style={
                            "width":
                                "100%",

                            "height":
                                "100%",
                        },
                    ),
                ],
                style={
                    "height":
                        "560px",

                    "minHeight":
                        "360px",

                    "maxHeight":
                        "1400px",

                    "resize":
                        "vertical",

                    "overflow":
                        "hidden",

                    "width":
                        "100%",

                    "boxSizing":
                        "border-box",
                },
            )

        else:

            message = (
                "Depth / borehole data unavailable."
            )

            if depth_result is not None:

                message = (
                    depth_result[
                        "message"
                    ]
                    or message
                )

            depth_child = html.Div(
                message,
                style={
                    "padding":
                        "20px",
                },
            )

        dashboard_children.append(
            _card(
                (
                    "Cluster by Borehole — "
                    f"{depth_result['vertical_label']} "
                    "(up to 20 boreholes; ≥5 samples)"
                ),
                depth_child,
            )
        )

    report = html.Div(
        dashboard_children,

        id=
            report_id,

        style={
            "display":
                "flex",

            "flexDirection":
                "column",

            "gap":
                "22px",

            "width":
                "100%",

            "padding":
                "8px",

            "boxSizing":
                "border-box",

            "backgroundColor":
                "white",
        },
    )

    return html.Div(
        [
            download_controls,
            report,
        ],

        style={
            "width":
                "100%",

            "minWidth":
                0,
        },
    )

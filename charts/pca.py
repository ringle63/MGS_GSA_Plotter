import math
import re

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dash import (
    html,
    dcc,
    dash_table,
)

from logic.filters import (
    NULL_VALUE,
    GROUP_BY_FIELDS,
)
from logic.groupcolors import build_group_colors
from logic.grainbreaks import get_grain_log_classes
from logic.multivariate import (
    calculate_pca,
    calculate_hierarchical,
)

GRAPH_CONFIG = {
    "responsive": True,
    "displaylogo": False,
    "toImageButtonOptions": {
        "format": "png",
        "scale": 2,
    },
}


def _get_existing_groups(
        scores,
        gsa_df,
        panel,
):
    """
    Apply existing Group By / Custom Groups to PCA scores.
    """

    scores = scores.copy()

    group_by = panel.get(
        "group_by",
        "None",
    )

    custom_groups = panel.get(
        "grouped_samples"
    )

    using_custom_groups = (
            custom_groups
            is not None
    )

    if using_custom_groups:

        (
            _,
            sample_to_group,
        ) = custom_groups

        scores["_group"] = (
            scores["GSA_ID"]
            .astype(str)
            .map(sample_to_group)
            .fillna(NULL_VALUE)
            .astype(str)
        )

    elif (
            group_by
            and group_by != "None"
            and group_by in gsa_df.columns
    ):

        lookup = (
            gsa_df[
                [
                    "GSA_ID",
                    group_by,
                ]
            ]
            .drop_duplicates(
                "GSA_ID"
            )
            .copy()
        )

        lookup["GSA_ID"] = (
            lookup["GSA_ID"]
            .astype(str)
        )

        lookup = (
            lookup
            .set_index(
                "GSA_ID"
            )[
                group_by
            ]
            .to_dict()
        )

        scores["_group"] = (
            scores["GSA_ID"]
            .astype(str)
            .map(lookup)
            .fillna(NULL_VALUE)
            .astype(str)
        )

    else:

        scores["_group"] = (
            "All Samples"
        )

    return scores


def _borehole_sort_key(
        borehole_id,
):
    """
    Natural alphanumeric sort for BoreholeID.

    Sorting proceeds segment-by-segment across hyphens, with
    numeric portions compared numerically and letter portions
    compared case-insensitively. Letter suffixes are preserved
    as the final sort component.
    """

    text = str(
        borehole_id
    ).strip().upper()

    segments = re.split(
        r"-+",
        text,
    )

    key = []

    for segment in segments:

        tokens = re.findall(
            r"\d+|[A-Z]+|[^A-Z0-9]+",
            segment,
        )

        segment_key = []

        for token in tokens:

            if token.isdigit():

                segment_key.append(
                    (
                        0,
                        int(
                            token
                        ),
                    )
                )

            else:

                segment_key.append(
                    (
                        1,
                        token,
                    )
                )

        key.append(
            tuple(
                segment_key
            )
        )

    return tuple(
        key
    )


def _get_borehole_data(
        gsa_df,
        cluster_df,
        vertical_axis="depth",
        x_field="BoreholeID",
):
    """
    Build vertical cluster-interpretation data for a selectable
    categorical x-axis and either depth or sample elevation.

    x_field:
        Any categorical GSA field present in gsa_df.
        BoreholeID uses natural alphanumeric ordering.
        Other fields use case-insensitive alphabetical ordering.
    """

    if vertical_axis == "elevation":

        vertical_field = (
            "sample_elevation"
        )

        vertical_label = (
            "Elevation (ft)"
        )

        reverse_y = False

    else:

        vertical_field = (
            "depth_ft"
        )

        vertical_label = (
            "Depth (ft)"
        )

        reverse_y = True

    if x_field not in gsa_df.columns:

        return {
            "data":
                pd.DataFrame(),

            "message":
                f"{x_field} is unavailable.",

            "vertical_field":
                vertical_field,

            "vertical_label":
                vertical_label,

            "reverse_y":
                reverse_y,

            "x_field":
                x_field,

            "x_label":
                x_field,
        }

    if vertical_field not in gsa_df.columns:

        return {
            "data":
                pd.DataFrame(),

            "message":
                (
                    f"{vertical_field} is unavailable "
                    "in the GSA table."
                ),

            "vertical_field":
                vertical_field,

            "vertical_label":
                vertical_label,

            "reverse_y":
                reverse_y,

            "x_field":
                x_field,

            "x_label":
                x_field,
        }

    subset = (
        gsa_df[
            [
                "GSA_ID",
                x_field,
                vertical_field,
            ]
        ]
        .copy()
    )

    subset["GSA_ID"] = (
        subset["GSA_ID"]
        .astype(str)
    )

    subset[
        vertical_field
    ] = pd.to_numeric(
        subset[
            vertical_field
        ],
        errors="coerce",
    )

    subset = (
        subset
        .merge(
            cluster_df,
            on="GSA_ID",
            how="inner",
        )
        .dropna(
            subset=[
                x_field,
                vertical_field,
                "Cluster",
            ]
        )
    )

    if subset.empty:

        return {
            "data":
                pd.DataFrame(),

            "message":
                (
                    f"No analyzed samples contain "
                    f"{vertical_label.lower()} and "
                    f"{x_field}."
                ),

            "vertical_field":
                vertical_field,

            "vertical_label":
                vertical_label,

            "reverse_y":
                reverse_y,

            "x_field":
                x_field,

            "x_label":
                x_field,
        }

    subset[
        x_field
    ] = (
        subset[
            x_field
        ]
        .astype(str)
    )

    counts = (
        subset[
            x_field
        ]
        .value_counts()
    )

    eligible = counts[
        counts >= 5
    ]

    if eligible.empty:

        return {
            "data":
                pd.DataFrame(),

            "message":
                (
                    f"No {x_field} categories contain at least "
                    "5 analyzed samples."
                ),

            "vertical_field":
                vertical_field,

            "vertical_label":
                vertical_label,

            "reverse_y":
                reverse_y,

            "x_field":
                x_field,

            "x_label":
                x_field,
        }

    # Retain the 50 eligible categories with the largest analyzed
    # sample counts, then display them in an intuitive order.
    keep_categories = (
        eligible
        .head(50)
        .index
        .tolist()
    )

    if x_field == "BoreholeID":

        keep_categories = sorted(
            keep_categories,
            key=_borehole_sort_key,
        )

    else:

        keep_categories = sorted(
            keep_categories,
            key=lambda value:
                str(
                    value
                ).casefold(),
        )

    subset = (
        subset[
            subset[
                x_field
            ]
            .isin(
                keep_categories
            )
        ]
        .copy()
    )

    subset[
        x_field
    ] = pd.Categorical(
        subset[
            x_field
        ],
        categories=
            keep_categories,
        ordered=True,
    )

    subset = (
        subset
        .sort_values(
            [
                x_field,
                vertical_field,
            ]
        )
    )

    x_label = (
        "BoreholeID"
        if x_field == "BoreholeID"
        else (
            GROUP_BY_FIELDS.get(
                x_field,
                x_field,
            )
            if "GROUP_BY_FIELDS" in globals()
            else x_field
        )
    )

    return {
        "data":
            subset,

        "message":
            None,

        "vertical_field":
            vertical_field,

        "vertical_label":
            vertical_label,

        "reverse_y":
            reverse_y,

        "x_field":
            x_field,

        "x_label":
            x_label,
    }



def _card(
        title,
        child,
        full_width=False,
        min_height=None,
):
    """
    Responsive dashboard card.
    """

    style = {
        "background":
            "white",

        "border":
            "1px solid #d8dde6",

        "borderRadius":
            "6px",

        "padding":
            "10px",

        "minWidth":
            0,

        "boxSizing":
            "border-box",

        "overflow":
            "hidden",
    }

    if full_width:
        style[
            "gridColumn"
        ] = "1 / -1"

    if min_height is not None:
        style[
            "minHeight"
        ] = f"{min_height}px"

    return html.Div(
        [
            html.Div(
                title,

                style={
                    "fontSize":
                        "1.08rem",

                    "fontWeight":
                        "600",

                    "marginBottom":
                        "6px",
                },
            ),

            child,
        ],

        style=style,
    )


# Fixed cluster symbol mapping.
#
# Keep this stable so Cluster 1 always means the same symbol
# everywhere in the PCA report, regardless of Group By color.
CLUSTER_SYMBOLS = {
    1: "circle",
    2: "square",
    3: "diamond",
    4: "cross",
    5: "x",
    6: "triangle-up",
    7: "triangle-down",
    8: "triangle-left",
    9: "triangle-right",
    10: "star",
}


def _cluster_symbol(
        cluster,
):
    """
    Return a stable Plotly marker symbol for cluster 1-10.
    """

    try:
        cluster = int(
            cluster
        )

    except (
            TypeError,
            ValueError,
    ):
        return "circle"

    return CLUSTER_SYMBOLS.get(
        cluster,
        "circle",
    )


def _add_pca_legends(
        fig,
        groups,
        group_colors,
        clusters,
        color_mode,
        show_legend,
):
    """
    Add clean PCA legend keys without creating one entry for
    every Group × Cluster trace.

    The legend is split between two independent Plotly legends
    so long Group By lists remain fully visible without the
    legend's internal scroll bar.

    Existing-group coloring:
      - colored circle legend = group colors
      - black symbol legend = cluster symbols

    Cluster coloring:
      - each cluster gets its cluster color + cluster symbol
    """

    if not show_legend:
        return

    def _legend_column(index):
        return (
            "legend"
            if index % 2 == 0
            else "legend2"
        )

    if color_mode == "cluster":

        first_in_column = {
            "legend": True,
            "legend2": True,
        }

        for index, cluster in enumerate(
                clusters
        ):

            cluster_name = (
                f"Cluster {cluster}"
            )

            legend_name = (
                _legend_column(
                    index
                )
            )

            show_title = (
                first_in_column[
                    legend_name
                ]
            )

            first_in_column[
                legend_name
            ] = False

            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],

                    mode="markers",

                    name=cluster_name,

                    legend=
                        legend_name,

                    legendgroup=
                        "cluster_symbols",

                    legendgrouptitle_text=(
                        "Clusters"
                        if show_title
                        else None
                    ),

                    marker=dict(
                        size=10,

                        color=group_colors.get(
                            cluster_name,
                            "#777777",
                        ),

                        symbol=_cluster_symbol(
                            cluster
                        ),

                        line=dict(
                            width=0.8,
                            color="#333333",
                        ),
                    ),

                    hoverinfo="skip",

                    showlegend=True,
                )
            )

    else:

        # ----------------------------------------------------
        # Group-color legend split between two columns.
        # ----------------------------------------------------

        first_group_in_column = {
            "legend": True,
            "legend2": True,
        }

        for index, group in enumerate(
                groups
        ):

            legend_name = (
                _legend_column(
                    index
                )
            )

            show_title = (
                first_group_in_column[
                    legend_name
                ]
            )

            first_group_in_column[
                legend_name
            ] = False

            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],

                    mode="markers",

                    name=str(group),

                    legend=
                        legend_name,

                    legendgroup=
                        "group_colors",

                    legendgrouptitle_text=(
                        "Group Colors"
                        if show_title
                        else None
                    ),

                    marker=dict(
                        size=10,

                        color=group_colors[
                            group
                        ],

                        symbol="circle",

                        line=dict(
                            width=0.8,
                            color="#333333",
                        ),
                    ),

                    hoverinfo="skip",

                    showlegend=True,
                )
            )

        # ----------------------------------------------------
        # Cluster-symbol keys are distributed across the same
        # two legend columns.
        # ----------------------------------------------------

        first_cluster_in_column = {
            "legend": True,
            "legend2": True,
        }

        # Continue the alternating sequence after the groups so
        # both columns stay balanced overall.
        cluster_offset = len(
            groups
        )

        for index, cluster in enumerate(
                clusters
        ):

            legend_name = (
                _legend_column(
                    cluster_offset
                    + index
                )
            )

            show_title = (
                first_cluster_in_column[
                    legend_name
                ]
            )

            first_cluster_in_column[
                legend_name
            ] = False

            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],

                    mode="markers",

                    name=(
                        f"Cluster "
                        f"{cluster}"
                    ),

                    legend=
                        legend_name,

                    legendgroup=
                        "cluster_symbols",

                    legendgrouptitle_text=(
                        "Cluster Symbols"
                        if show_title
                        else None
                    ),

                    marker=dict(
                        size=10,

                        color="#4a4a4a",

                        symbol=_cluster_symbol(
                            cluster
                        ),

                        line=dict(
                            width=0.8,
                            color="#222222",
                        ),
                    ),

                    hoverinfo="skip",

                    showlegend=True,
                )
            )

def _add_loading_arrows(
        fig,
        scores,
        loadings,
):
    """
    Overlay PC1/PC2 loading vectors on the PCA scores plot.

    PCA loadings and PCA scores are on different numerical scales,
    so the vectors are scaled only for display. Their directions
    and relative lengths are preserved.
    """

    if (
            loadings is None
            or loadings.empty
            or "PC1" not in loadings.columns
            or "PC2" not in loadings.columns
    ):
        return

    score_x = pd.to_numeric(
        scores["PC1"],
        errors="coerce",
    ).dropna()

    score_y = pd.to_numeric(
        scores["PC2"],
        errors="coerce",
    ).dropna()

    if (
            score_x.empty
            or score_y.empty
    ):
        return

    # Robust ranges prevent a few extreme samples from shrinking
    # all arrows to nearly zero.
    x_low = float(
        score_x.quantile(
            0.05
        )
    )
    x_high = float(
        score_x.quantile(
            0.95
        )
    )
    y_low = float(
        score_y.quantile(
            0.05
        )
    )
    y_high = float(
        score_y.quantile(
            0.95
        )
    )

    x_half_range = max(
        abs(x_low),
        abs(x_high),
        1e-9,
    )

    y_half_range = max(
        abs(y_low),
        abs(y_high),
        1e-9,
    )

    max_loading_x = max(
        float(
            loadings["PC1"]
            .abs()
            .max()
        ),
        1e-9,
    )

    max_loading_y = max(
        float(
            loadings["PC2"]
            .abs()
            .max()
        ),
        1e-9,
    )

    x_scale = (
            0.70
            * x_half_range
            / max_loading_x
    )

    y_scale = (
            0.70
            * y_half_range
            / max_loading_y
    )

    scale = min(
        x_scale,
        y_scale,
    )

    for i, (variable, row) in enumerate(
            loadings.iterrows()
    ):
        x_end = (
                float(
                    row["PC1"]
                )
                * scale
        )

        y_end = (
                float(
                    row["PC2"]
                )
                * scale
        )

        # ----------------------------------------------------
        # Arrow only
        # ----------------------------------------------------

        fig.add_annotation(
            x=x_end,
            y=y_end,

            ax=0,
            ay=0,

            xref="x",
            yref="y",
            axref="x",
            ayref="y",

            text="",

            showarrow=True,

            arrowhead=3,
            arrowsize=1.0,
            arrowwidth=1.5,
            arrowcolor="#c62828",
        )

        # ----------------------------------------------------
        # Variable label at arrow endpoint
        # ----------------------------------------------------

        label_offset = (
                14
                + (
                        10
                        * (i % 3)
                )
        )

        fig.add_annotation(
            x=x_end,
            y=y_end,

            xref="x",
            yref="y",

            text=str(
                variable
            ),

            showarrow=False,

            xshift=(
                label_offset
                if x_end >= 0
                else -label_offset
            ),

            yshift=(
                (
                        12
                        + (
                                9
                                * (i % 3)
                        )
                )
                if y_end >= 0
                else (
                        -12
                        - (
                                9
                                * (i % 3)
                        )
                )
            ),

            font=dict(
                size=10,
                color="#c62828",
            ),

            bgcolor=(
                "rgba(255,255,255,0.85)"
            ),

            borderpad=2,
        )


def _make_score_figure(
        scores,
        explained,
        loadings,
        group_colors,
        show_labels,
        show_legend,
        color_mode,
        show_loading_arrows=False,
):
    """
    PCA PC1-vs-PC2 score figure.

    Cluster assignment is ALWAYS encoded by marker symbol.

    Color encoding:
      color_mode == "group"
          color = Group By / Custom Group
          symbol = Cluster

      color_mode == "cluster"
          color = Cluster
          symbol = Cluster

    Traces are split internally by Group × Cluster so each
    point can retain both encodings. Clean dummy legend traces
    are added separately to avoid a huge combined legend.
    """

    fig = go.Figure()

    groups = sorted(
        scores["_group"]
        .astype(str)
        .unique()
    )

    clusters = sorted(
        scores["Cluster"]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    # --------------------------------------------------------
    # Actual data traces:
    # one trace per Group × Cluster combination.
    #
    # These do NOT appear in the legend. Separate legend keys
    # are added below.
    # --------------------------------------------------------

    for group in groups:

        group_subset = scores[
            scores["_group"]
            .astype(str)
            == str(group)
            ]

        group_clusters = sorted(
            group_subset[
                "Cluster"
            ]
            .dropna()
            .astype(int)
            .unique()
            .tolist()
        )

        for cluster in group_clusters:
            trace_df = group_subset[
                group_subset[
                    "Cluster"
                ]
                .astype(int)
                == int(cluster)
                ]

            mode = (
                "markers+text"
                if show_labels
                else "markers"
            )

            fig.add_trace(
                go.Scatter(
                    x=trace_df["PC1"],
                    y=trace_df["PC2"],

                    mode=mode,

                    name=(
                        f"{group} — "
                        f"Cluster {cluster}"
                    ),

                    showlegend=False,

                    marker=dict(
                        size=8,

                        color=group_colors[
                            group
                        ],

                        symbol=_cluster_symbol(
                            cluster
                        ),

                        line=dict(
                            width=0.6,
                            color="rgba(40,40,40,0.65)",
                        ),
                    ),

                    text=(
                        trace_df[
                            "GSA_ID"
                        ]
                        if show_labels
                        else None
                    ),

                    textposition=
                    "top center",

                    customdata=(
                        trace_df[
                            [
                                "GSA_ID",
                                "_group",
                                "Cluster",
                            ]
                        ]
                        .to_numpy()
                    ),

                    hovertemplate=(
                        "Sample: %{customdata[0]}"
                        "<br>Group/Color: %{customdata[1]}"
                        "<br>Cluster: %{customdata[2]}"
                        f"<br>Cluster symbol: "
                        f"{_cluster_symbol(cluster)}"
                        "<br>PC1: %{x:.3f}"
                        "<br>PC2: %{y:.3f}"
                        "<extra></extra>"
                    ),
                )
            )

    # --------------------------------------------------------
    # Readable legends
    # --------------------------------------------------------

    _add_pca_legends(
        fig,
        groups,
        group_colors,
        clusters,
        color_mode,
        show_legend,
    )

    if show_loading_arrows:
        _add_loading_arrows(
            fig,
            scores,
            loadings,
        )

    pc1_pct = (
            explained[0]
            * 100
    )

    pc2_pct = (
            explained[1]
            * 100
    )

    fig.add_hline(
        y=0,
        line_width=1,
        line_dash="dot",
    )

    fig.add_vline(
        x=0,
        line_width=1,
        line_dash="dot",
    )

    fig.update_layout(
        height=520,

        # Reserve space on the right for two legend columns.
        margin=dict(
            l=65,
            r=330,
            t=15,
            b=60,
        ),

        hovermode=
        "closest",

        legend=dict(
            orientation="v",

            x=1.01,
            y=1.0,

            xanchor="left",
            yanchor="top",

            tracegroupgap=6,

            font=dict(
                size=11,
            ),
        ),

        legend2=dict(
            orientation="v",

            x=1.18,
            y=1.0,

            xanchor="left",
            yanchor="top",

            tracegroupgap=6,

            font=dict(
                size=11,
            ),
        ),
    )

    fig.update_xaxes(
        title=(
            f"PC1 "
            f"({pc1_pct:.1f}% variance)"
        ),

        automargin=True,
    )

    fig.update_yaxes(
        title=(
            f"PC2 "
            f"({pc2_pct:.1f}% variance)"
        ),

        automargin=True,
    )

    return fig


def _make_scree_figure(
        explained,
        cumulative,
):
    """
    Scree plot with cumulative variance in hover.
    """

    component_names = [
        f"PC{i + 1}"
        for i in range(
            len(explained)
        )
    ]

    explained_percent = (
            explained
            * 100
    )

    cumulative_percent = (
            cumulative
            * 100
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=component_names,
            y=explained_percent,

            customdata=
            cumulative_percent,

            hovertemplate=(
                "%{x}"
                "<br>Variance explained: %{y:.1f}%"
                "<br>Cumulative: %{customdata:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=390,

        margin=dict(
            l=65,
            r=20,
            t=15,
            b=65,
        ),

        showlegend=False,
    )

    fig.update_xaxes(
        title=
        "Principal Component",

        automargin=True,
    )

    fig.update_yaxes(
        title=
        "Variance Explained (%)",

        rangemode=
        "tozero",

        automargin=True,
    )

    return fig


def _make_loadings_figure(
        loadings,
):
    """
    Horizontal PC1 / PC2 loadings plot.
    """

    variable_names = list(
        loadings.index
    )

    variable_names = list(
        reversed(
            variable_names
        )
    )

    pc1 = (
        loadings.loc[
            variable_names,
            "PC1",
        ]
        .tolist()
    )

    pc2 = (
        loadings.loc[
            variable_names,
            "PC2",
        ]
        .tolist()
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            y=variable_names,
            x=pc1,

            orientation="h",

            name="PC1",

            hovertemplate=(
                "Variable: %{y}"
                "<br>PC1 loading: %{x:.3f}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Bar(
            y=variable_names,
            x=pc2,

            orientation="h",

            name="PC2",

            hovertemplate=(
                "Variable: %{y}"
                "<br>PC2 loading: %{x:.3f}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_vline(
        x=0,
        line_width=1,
        line_dash="dot",
    )

    fig.update_layout(
        height=max(
            390,
            55
            + (
                    34
                    * len(
                variable_names
            )
            ),
        ),

        barmode="group",

        margin=dict(
            l=120,
            r=20,
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
        title="Loading",
        automargin=True,
    )

    fig.update_yaxes(
        title="Variable",
        automargin=True,
    )

    return fig


def _make_silhouette_figure(
        silhouette_df,
        selected_k,
):
    """
    Average silhouette width by cluster count.
    """

    fig = go.Figure()

    if silhouette_df.empty:

        fig.add_annotation(
            text=(
                "Silhouette analysis unavailable "
                "for this sample count."
            ),

            x=0.5,
            y=0.5,

            xref="paper",
            yref="paper",

            showarrow=False,
        )

    else:

        fig.add_trace(
            go.Scatter(
                x=silhouette_df["k"],
                y=silhouette_df[
                    "silhouette"
                ],

                mode=
                "lines+markers",

                hovertemplate=(
                    "k = %{x}"
                    "<br>Average silhouette: %{y:.3f}"
                    "<extra></extra>"
                ),
            )
        )

        fig.add_vline(
            x=selected_k,
            line_width=1.5,
            line_dash="dash",
        )

        best_row = (
            silhouette_df
            .loc[
                silhouette_df[
                    "silhouette"
                ]
            .idxmax()
            ]
        )

        best_k = int(
            best_row["k"]
        )

        best_value = float(
            best_row[
                "silhouette"
            ]
        )

        label = (
            f"Highest: k={best_k}"
        )

        if best_k == selected_k:
            label = (
                f"Selected / highest: "
                f"k={best_k}"
            )

        fig.add_annotation(
            x=best_k,
            y=best_value,

            text=label,

            showarrow=True,
            arrowhead=2,

            xshift=18,
            yshift=18,

            bgcolor=
            "rgba(255,255,255,0.85)",
        )

        fig.update_xaxes(
            tickmode="array",

            tickvals=
            silhouette_df[
                "k"
            ]
            .tolist(),

            range=[
                silhouette_df[
                    "k"
                ]
            .min()
                - 0.5,

                silhouette_df[
                    "k"
                ]
            .max()
                + 0.5,
            ],
        )

    fig.update_layout(
        height=390,

        margin=dict(
            l=70,
            r=25,
            t=20,
            b=65,
        ),

        showlegend=False,
    )

    fig.update_xaxes(
        title=
        "Number of Clusters (k)",

        automargin=True,
    )

    fig.update_yaxes(
        title=
        "Average Silhouette Width",

        automargin=True,
    )

    return fig


def _hex_to_rgba(
        value,
        alpha,
):
    """
    Convert #RRGGBB into CSS rgba().
    """

    if not (
            isinstance(
                value,
                str,
            )
            and value.startswith(
        "#"
    )
            and len(value) == 7
    ):
        return (
            "rgba(245,247,250,"
            f"{alpha})"
        )

    red = int(
        value[1:3],
        16,
    )

    green = int(
        value[3:5],
        16,
    )

    blue = int(
        value[5:7],
        16,
    )

    return (
        f"rgba({red},"
        f"{green},"
        f"{blue},"
        f"{alpha})"
    )


def _make_cluster_membership_table(
        scores,
        selected_k,
        cluster_palette,
):
    """
    Current-k cluster membership summary.

    This is the "Hierarchical Cluster" organization:
      Cluster | N

    Cluster colors match the PCA / hierarchy palette.
    """

    counts = (
        scores[
            "Cluster"
        ]
        .dropna()
        .astype(int)
        .value_counts()
        .reindex(
            range(
                1,
                selected_k + 1,
            ),
            fill_value=0,
        )
        .sort_index()
    )

    cluster_labels = [
        f"Cluster {cluster}"
        for cluster in counts.index
    ]

    cluster_fill = [
        _hex_to_rgba(
            cluster_palette.get(
                label,
                "#777777",
            ),
            0.18,
        )
        for label in cluster_labels
    ]

    max_count = max(
        int(
            counts.max()
        ),
        1,
    )

    count_fill = []

    for count in counts.tolist():
        # Light-to-darker blue intensity based on cluster size.
        # Keep the cells pale enough for black text.
        alpha = (
                0.08
                + (
                        0.28
                        * (
                                float(count)
                                / max_count
                        )
                )
        )

        count_fill.append(
            f"rgba(49,130,189,{alpha:.3f})"
        )

    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=[
                    140,
                    100,
                ],

                header=dict(
                    values=[
                        "<b>Cluster</b>",
                        "<b>Number of Samples</b>",
                    ],

                    align=[
                        "left",
                        "center",
                    ],

                    fill_color=
                    "#eef2f7",

                    font=dict(
                        size=12,
                    ),

                    height=30,
                ),

                cells=dict(
                    values=[
                        cluster_labels,
                        counts.astype(int).tolist(),
                    ],

                    align=[
                        "left",
                        "center",
                    ],

                    fill_color=[
                        cluster_fill,
                        count_fill,
                    ],

                    font=dict(
                        size=12,
                    ),

                    height=28,
                ),
            )
        ]
    )

    fig.update_layout(
        height=max(
            250,
            90
            + (
                    30
                    * selected_k
            ),
        ),

        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
    )

    return fig


def _make_group_cluster_heatmap(
        scores,
        selected_k,
):
    """
    Current-k Group By / Custom Group × Cluster heatmap.

    Rows:
        current Group By / Custom Group categories

    Columns:
        Cluster 1 ... Cluster k

    Cell text:
        sample count

    Cell fill:
        percentage of samples WITHIN that group assigned to
        the cluster, matching the interpretation style of the
        original R report.
    """

    heatmap_df = (
        scores[
            [
                "_group",
                "Cluster",
            ]
        ]
        .dropna(
            subset=[
                "_group",
                "Cluster",
            ]
        )
        .copy()
    )

    if heatmap_df.empty:
        fig = go.Figure()

        fig.add_annotation(
            text=(
                "No grouped cluster membership data "
                "are available."
            ),

            x=0.5,
            y=0.5,

            xref="paper",
            yref="paper",

            showarrow=False,
        )

        fig.update_layout(
            height=300,
        )

        return fig

    heatmap_df[
        "Cluster"
    ] = (
        heatmap_df[
            "Cluster"
        ]
        .astype(int)
    )

    heatmap_df[
        "_group"
    ] = (
        heatmap_df[
            "_group"
        ]
        .astype(str)
    )

    cluster_numbers = list(
        range(
            1,
            selected_k + 1,
        )
    )

    counts = pd.crosstab(
        heatmap_df[
            "_group"
        ],
        heatmap_df[
            "Cluster"
        ],
    )

    counts = counts.reindex(
        columns=cluster_numbers,
        fill_value=0,
    )

    # Sort groups by total analyzed sample count, largest first.
    group_totals = (
        counts
        .sum(
            axis=1
        )
    )

    counts = counts.loc[
        group_totals
        .sort_values(
            ascending=False
        )
        .index
    ]

    row_totals = (
        counts
        .sum(
            axis=1
        )
        .replace(
            0,
            pd.NA,
        )
    )

    percentages = (
            counts
            .div(
                row_totals,
                axis=0,
            )
            .fillna(0)
            * 100.0
    )

    x_labels = [
        f"C{cluster}"
        for cluster in cluster_numbers
    ]

    y_labels = (
        counts
        .index
        .astype(str)
        .tolist()
    )

    count_values = (
        counts
        .astype(int)
        .to_numpy()
    )

    percentage_values = (
        percentages
        .to_numpy(
            dtype=float
        )
    )

    # Build explicit hover information so both N and % are
    # available without cluttering cell text.
    customdata = []

    for group_name in y_labels:

        row_data = []

        total_n = int(
            counts.loc[
                group_name
            ]
            .sum()
        )

        for cluster in cluster_numbers:
            row_data.append(
                [
                    group_name,
                    int(
                        counts.loc[
                            group_name,
                            cluster,
                        ]
                    ),
                    float(
                        percentages.loc[
                            group_name,
                            cluster,
                        ]
                    ),
                    total_n,
                ]
            )

        customdata.append(
            row_data
        )

    fig = go.Figure(
        data=[
            go.Heatmap(
                z=percentage_values,

                x=x_labels,
                y=y_labels,

                text=
                count_values,

                texttemplate=
                "%{text}",

                textfont=dict(
                    size=11,
                ),

                customdata=
                customdata,

                zmin=0,
                zmax=100,

                colorscale=
                "Blues",

                colorbar=dict(
                    title=(
                        "% within<br>group"
                    )
                ),

                hovertemplate=(
                    "Group: %{customdata[0]}"
                    "<br>Cluster: %{x}"
                    "<br>N: %{customdata[1]}"
                    "<br>% of group: %{customdata[2]:.1f}%"
                    "<br>Group total N: %{customdata[3]}"
                    "<extra></extra>"
                ),
            )
        ]
    )

    # Give every heatmap category a real minimum row height.
    # More importantly, force Plotly to draw EVERY y-axis tick
    # instead of automatically skipping labels when many groups
    # are present.
    heatmap_row_height = 30

    fig.update_layout(
        height=max(
            360,
            150
            + (
                heatmap_row_height
                * len(
                    y_labels
                )
            ),
        ),

        margin=dict(
            l=220,
            r=80,
            t=20,
            b=70,
        ),

        xaxis=dict(
            title=(
                f"Hierarchical Cluster "
                f"(k = {selected_k})"
            ),

            side="bottom",
        ),

        yaxis=dict(
            title="Group",

            autorange=
                "reversed",

            automargin=True,

            # Explicit array ticks prevent Plotly from
            # auto-skipping group names.
            tickmode="array",
            tickvals=y_labels,
            ticktext=y_labels,

            tickfont=dict(
                size=11,
            ),

            ticks="",
        ),
    )

    return fig


GRAIN_CLASS_ORDER = [
    "Clay",
    "Silt",
    "Very Fine Sand",
    "Fine Sand",
    "Medium Sand",
    "Coarse Sand",
    "Very Coarse Sand",
    "Gravel",
]

GRAIN_CLASS_LABELS = {
    "Clay": "C",
    "Silt": "Si",
    "Very Fine Sand": "VFS",
    "Fine Sand": "FS",
    "Medium Sand": "MS",
    "Coarse Sand": "CS",
    "Very Coarse Sand": "VCS",
    "Gravel": "G",
}


def _build_mmes_lookup(
        mmes_df,
        mmes_rs_df,
):
    """
    Build a PRIMARY-first MMES row lookup.

    The grain-class calculator only needs MMES data for
    Mastersizer 50 µm sand/silt breaks with 2 or 4 µm clay
    breaks. For all other settings, the GSA table is enough.

    If a matching sample exists in both sources, PRIMARY wins.
    """

    lookup = {}

    if (
            mmes_rs_df is not None
            and not mmes_rs_df.empty
            and "Sample_Name_Final"
            in mmes_rs_df.columns
    ):

        for _, row in mmes_rs_df.iterrows():
            sample = str(
                row[
                    "Sample_Name_Final"
                ]
            )

            lookup[
                sample
            ] = row.to_dict()

    if (
            mmes_df is not None
            and not mmes_df.empty
            and "Sample_Name_Final"
            in mmes_df.columns
    ):

        for _, row in mmes_df.iterrows():
            sample = str(
                row[
                    "Sample_Name_Final"
                ]
            )

            # PRIMARY intentionally overwrites RS.
            lookup[
                sample
            ] = row.to_dict()

    return lookup


def _build_grain_fraction_dataframe(
        gsa_df,
        mmes_df,
        mmes_rs_df,
        scores,
        panel,
):
    """
    Calculate the same 8 grain classes used by Grain Size Log
    for the samples that survived the PCA complete-case filter.

    This reuses the existing break/gravel implementation:
      - Mastersizer clay break: 2 / 4 / 8 µm
      - Mastersizer sand/silt: 50 / 62.5 µm
      - Pipette clay break: 2 / 4 µm
      - Kehew: fixed 4 µm
      - Dry Sieve: fixed fines behavior
      - Include Gravel settings by method

    The current PCA display group is carried through in _group.
    When PCA Point Grouping is "cluster", _group is Cluster N.
    Otherwise _group is the current Group By / Custom Group.
    """

    if scores is None or scores.empty:
        return pd.DataFrame()

    score_lookup = (
        scores[
            [
                "GSA_ID",
                "_group",
                "Cluster",
            ]
        ]
        .copy()
    )

    score_lookup[
        "GSA_ID"
    ] = (
        score_lookup[
            "GSA_ID"
        ]
        .astype(str)
    )

    score_lookup = (
        score_lookup
        .drop_duplicates(
            "GSA_ID"
        )
        .set_index(
            "GSA_ID"
        )
        .to_dict(
            "index"
        )
    )

    selected_ids = set(
        score_lookup.keys()
    )

    subset = (
        gsa_df[
            gsa_df[
                "GSA_ID"
            ]
            .astype(str)
            .isin(
                selected_ids
            )
        ]
            .copy()
    )

    subset[
        "GSA_ID"
    ] = (
        subset[
            "GSA_ID"
        ]
        .astype(str)
    )

    subset = (
        subset
        .drop_duplicates(
            "GSA_ID"
        )
    )

    settings = {
        "Mastersizer":
            panel.get(
                "mastersizer_break",
                8,
            ),

        "MastersizerSand":
            panel.get(
                "mastersizer_sand_break",
                62.5,
            ),

        "Pipette":
            panel.get(
                "pipette_break",
                2,
            ),

        "GravelSettings":
            panel.get(
                "grainlog_gravel_settings",
                {
                    "Mastersizer":
                        False,

                    "Pipette":
                        True,

                    "Kehew":
                        True,

                    "Dry Sieve":
                        True,
                },
            ),
    }

    mmes_lookup = _build_mmes_lookup(
        mmes_df,
        mmes_rs_df,
    )

    records = []

    for _, sample_row in subset.iterrows():

        sample = str(
            sample_row[
                "GSA_ID"
            ]
        )

        score_info = (
            score_lookup.get(
                sample
            )
        )

        if score_info is None:
            continue

        mmes_row = (
            mmes_lookup.get(
                sample
            )
        )

        try:

            grain = (
                get_grain_log_classes(
                    sample_row,
                    mmes_row,
                    settings,
                )
            )

        except (
                KeyError,
                TypeError,
                ValueError,
        ):

            # A requested break may require a raw MMES field
            # unavailable for this source/sample. Skip that
            # sample rather than breaking the full PCA report.
            continue

        if grain is None:
            continue

        record = {
            "GSA_ID":
                sample,

            "_group":
                str(
                    score_info[
                        "_group"
                    ]
                ),

            "Cluster":
                int(
                    score_info[
                        "Cluster"
                    ]
                ),

            "Method":
                grain.get(
                    "method"
                ),

            "Break":
                grain.get(
                    "break"
                ),
        }

        valid = True

        for grain_class in (
                GRAIN_CLASS_ORDER
        ):

            value = pd.to_numeric(
                pd.Series(
                    [
                        grain.get(
                            grain_class,
                            0,
                        )
                    ]
                ),
                errors="coerce",
            ).iloc[0]

            if pd.isna(value):
                valid = False
                break

            record[
                grain_class
            ] = float(
                value
            )

        if not valid:
            continue

        records.append(
            record
        )

    return pd.DataFrame(
        records
    )


def _make_grain_fraction_histogram(
        grain_df,
        color_mode,
        display_group_colors,
        cluster_palette,
):
    """
    One histogram panel per current group/cluster.

    Each subplot shows the median calculated grain-fraction
    percentages from finest to coarsest:
    Clay -> Silt -> VFS -> FS -> MS -> CS -> VCS -> Gravel

    This is intentionally discrete and not interpolated.
    """

    if (
            grain_df is None
            or grain_df.empty
    ):
        fig = go.Figure()

        fig.add_annotation(
            text=(
                "No samples have usable grain-fraction "
                "data for the current break/gravel settings."
            ),
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
        )

        fig.update_layout(
            height=420,
            margin=dict(
                l=60,
                r=30,
                t=20,
                b=70,
            ),
        )

        return fig

    groups = (
        grain_df["_group"]
        .astype(str)
        .value_counts()
        .index
        .tolist()
    )

    n_groups = len(groups)

    if n_groups <= 4:
        n_cols = n_groups
    else:
        n_cols = 4

    n_rows = int(
        math.ceil(
            n_groups / n_cols
        )
    )

    grain_tick_labels = [
        GRAIN_CLASS_LABELS.get(
            grain_class,
            grain_class,
        )
        for grain_class in GRAIN_CLASS_ORDER
    ]

    subplot_titles = [
        str(group)
        for group in groups
    ]

    # Plotly limits vertical_spacing to <= 1 / (rows - 1).
    # Use a dynamic spacing value so the histogram grid remains
    # valid even when many groups create many subplot rows.
    if n_rows <= 1:
        vertical_spacing = 0.0
    else:
        # Keep total whitespace modest so the plotting areas use
        # most of the available vertical space.
        vertical_spacing = min(
            0.055,
            0.24 / (n_rows - 1),
        )

    fig = make_subplots(
        rows=n_rows,
        cols=n_cols,
        subplot_titles=subplot_titles,
        shared_yaxes=True,
        horizontal_spacing=0.10,
        vertical_spacing=vertical_spacing,
    )

    for idx, group in enumerate(groups):

        row_num = (idx // n_cols) + 1
        col_num = (idx % n_cols) + 1

        group_df = grain_df[
            grain_df["_group"]
            .astype(str)
            == str(group)
        ]

        medians = []
        q25_values = []
        q75_values = []

        for grain_class in GRAIN_CLASS_ORDER:

            values = pd.to_numeric(
                group_df[grain_class],
                errors="coerce",
            ).dropna()

            if values.empty:
                medians.append(None)
                q25_values.append(None)
                q75_values.append(None)
            else:
                medians.append(
                    float(values.median())
                )
                q25_values.append(
                    float(values.quantile(0.25))
                )
                q75_values.append(
                    float(values.quantile(0.75))
                )

        customdata = [
            [
                grain_class,
                int(len(group_df)),
                q25,
                q75,
            ]
            for grain_class, q25, q75 in zip(
                GRAIN_CLASS_ORDER,
                q25_values,
                q75_values,
            )
        ]

        if color_mode == "cluster":
            color = cluster_palette.get(
                str(group),
                "#777777",
            )
        else:
            color = display_group_colors.get(
                str(group),
                "#777777",
            )

        fig.add_trace(
            go.Bar(
                x=grain_tick_labels,
                y=medians,
                name=str(group),
                marker=dict(
                    color=color,
                ),
                customdata=customdata,
                showlegend=False,
                hovertemplate=(
                    "Group: "
                    + str(group)
                    + "<br>Class: %{customdata[0]}"
                    + "<br>Median: %{y:.2f}%"
                    + "<br>Q25: %{customdata[2]:.2f}%"
                    + "<br>Q75: %{customdata[3]:.2f}%"
                    + "<br>N: %{customdata[1]}"
                    + "<extra></extra>"
                ),
            ),
            row=row_num,
            col=col_num,
        )

        fig.update_xaxes(
            categoryorder="array",
            categoryarray=grain_tick_labels,
            tickangle=0,
            automargin=True,
            tickfont=dict(size=9),
            row=row_num,
            col=col_num,
        )

        fig.update_yaxes(
            rangemode="tozero",
            automargin=True,
            row=row_num,
            col=col_num,
        )

    figure_height = max(
        540,
        280 * n_rows,
    )

    fig.update_layout(
        height=figure_height,
        margin=dict(
            l=70,
            r=30,
            t=40,
            b=70,
        ),
        bargap=0.0,
        bargroupgap=0.0,
    )

    # Bottom overall x-axis label
    fig.add_annotation(
        text=(
            "Calculated Grain-Size Class "
            "(C=Clay, Si=Silt, VFS=Very Fine Sand, "
            "FS=Fine Sand, MS=Medium Sand, "
            "CS=Coarse Sand, VCS=Very Coarse Sand, G=Gravel)"
        ),
        x=0.5,
        y=-0.08,
        xref="paper",
        yref="paper",
        showarrow=False,
        xanchor="center",
        font=dict(size=11),
    )

    # Left overall y-axis label
    fig.add_annotation(
        text="Median Percentage (%)",
        x=-0.06,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        textangle=-90,
        xanchor="center",
        yanchor="middle",
        font=dict(size=12),
    )

    return fig


def _grain_fraction_settings_text(
        panel,
        grain_df,
):
    """
    Compact description of the fraction settings actually used.
    """

    gravel_settings = (
        panel.get(
            "grainlog_gravel_settings",
            {}
        )
    )

    gravel_methods = [
        method
        for method in [
            "Mastersizer",
            "Pipette",
            "Kehew",
            "Dry Sieve",
        ]
        if gravel_settings.get(
            method,
            False,
        )
    ]

    gravel_text = (
        ", ".join(
            gravel_methods
        )
        if gravel_methods
        else "none"
    )

    usable_n = (
        len(
            grain_df
        )
        if grain_df is not None
        else 0
    )

    return (
        f"Median calculated percentages; usable N={usable_n}; "
        f"Mastersizer clay break="
        f"{panel.get('mastersizer_break', 8)} µm; "
        f"Mastersizer sand/silt break="
        f"{panel.get('mastersizer_sand_break', 62.5)} µm; "
        f"Pipette clay break="
        f"{panel.get('pipette_break', 2)} µm; "
        f"gravel included for: {gravel_text}."
    )


def _format_summary_value(
        row,
        variable,
):
    """
    Format Median [Q25-Q75].
    """

    median = row.get(
        f"{variable}_median"
    )

    q25 = row.get(
        f"{variable}_q25"
    )

    q75 = row.get(
        f"{variable}_q75"
    )

    if pd.isna(median):
        return ""

    return (
        f"{median:.3f} "
        f"[{q25:.3f}–{q75:.3f}]"
    )


def _format_number(
        value,
):
    if pd.isna(value):
        return ""

    return f"{value:.3f}"


def _hierarchy_stat_lines(
        row,
        variable,
        selected_stats,
):
    """
    Build the selected hierarchy summary-stat lines for
    one variable.
    """

    lines = []

    if "median" in selected_stats:
        lines.append(
            (
                "Median",
                _format_number(
                    row.get(
                        f"{variable}_median"
                    )
                ),
            )
        )

    if "iqr" in selected_stats:

        q25 = row.get(
            f"{variable}_q25"
        )

        q75 = row.get(
            f"{variable}_q75"
        )

        value = ""

        if (
                pd.notna(q25)
                and pd.notna(q75)
        ):
            value = (
                f"{q25:.3f}–"
                f"{q75:.3f}"
            )

        lines.append(
            (
                "IQR",
                value,
            )
        )

    if "mean" in selected_stats:
        lines.append(
            (
                "Mean",
                _format_number(
                    row.get(
                        f"{variable}_mean"
                    )
                ),
            )
        )

    if "std" in selected_stats:
        lines.append(
            (
                "Std Dev",
                _format_number(
                    row.get(
                        f"{variable}_std"
                    )
                ),
            )
        )

    if "minmax" in selected_stats:

        minimum = row.get(
            f"{variable}_min"
        )

        maximum = row.get(
            f"{variable}_max"
        )

        value = ""

        if (
                pd.notna(minimum)
                and pd.notna(maximum)
        ):
            value = (
                f"{minimum:.3f}–"
                f"{maximum:.3f}"
            )

        lines.append(
            (
                "Min–Max",
                value,
            )
        )

    return lines


def _build_summary_table(
        summary,
        variables,
        cluster_palette,
):
    """
    Readable horizontally-scrollable cluster table.
    """

    records = []

    for _, row in summary.iterrows():

        cluster = int(
            row["Cluster"]
        )

        record = {
            "Cluster":
                f"Cluster {cluster}",

            "N":
                int(
                    row["n"]
                ),
        }

        for variable in variables:
            record[variable] = (
                _format_summary_value(
                    row,
                    variable,
                )
            )

        records.append(record)

    columns = [
        {
            "name":
                "Cluster",

            "id":
                "Cluster",
        },
        {
            "name":
                "N",

            "id":
                "N",
        },
    ]

    columns.extend(
        [
            {
                "name":
                    variable,

                "id":
                    variable,
            }
            for variable
            in variables
        ]
    )

    style_data_conditional = []

    for cluster_name, color in (
            cluster_palette.items()
    ):
        style_data_conditional.append(
            {
                "if": {
                    "filter_query":
                        (
                            "{Cluster} = "
                            f"'{cluster_name}'"
                        ),

                    "column_id":
                        "Cluster",
                },

                "backgroundColor":
                    _hex_to_rgba(
                        color,
                        0.18,
                    ),

                "fontWeight":
                    "600",
            }
        )

    return dash_table.DataTable(
        data=records,
        columns=columns,

        fixed_columns={
            "headers":
                True,

            "data":
                2,
        },

        style_table={
            "overflowX":
                "auto",

            "minWidth":
                "100%",
        },

        style_header={
            "fontWeight":
                "600",

            "backgroundColor":
                "#eef2f7",

            "whiteSpace":
                "normal",

            "height":
                "auto",

            "textAlign":
                "center",
        },

        style_cell={
            "minWidth":
                "115px",

            "width":
                "140px",

            "maxWidth":
                "220px",

            "padding":
                "7px",

            "fontSize":
                "12px",

            "whiteSpace":
                "normal",

            "height":
                "auto",

            "textAlign":
                "center",
        },

        style_cell_conditional=[
            {
                "if": {
                    "column_id":
                        "Cluster"
                },

                "minWidth":
                    "90px",

                "width":
                    "90px",
            },
            {
                "if": {
                    "column_id":
                        "N"
                },

                "minWidth":
                    "60px",

                "width":
                    "60px",
            },
        ],

        style_data_conditional=
        style_data_conditional,

        page_action="none",
    )


def _build_hierarchy_panel(
        hierarchy,
        variables,
        selected_k,
        cluster_palette,
        selected_stats,
):
    """
    Compact hierarchy summary:
      broad -> intermediate -> selected k

    No distance axis and no individual sample branches.

    Summary statistics are user-selectable. Parent nodes also
    list the final selected-k clusters they contain.
    """

    if hierarchy is None:
        return html.Div(
            "Hierarchy unavailable."
        )

    selected_stats = (
            selected_stats
            or []
    )

    levels = hierarchy[
        "levels"
    ]

    memberships = hierarchy[
        "memberships"
    ]

    summaries = hierarchy[
        "summaries"
    ]

    selected_membership = (
        memberships[
            selected_k
        ]
        .copy()
    )

    rows = []

    for level in levels:

        summary = summaries[
            level
        ]

        level_membership = (
            memberships[
                level
            ]
            .copy()
        )

        nodes = []

        for _, row in (
                summary
                        .sort_values(
                    "Cluster"
                )
                        .iterrows()
        ):

            cluster = int(
                row[
                    "Cluster"
                ]
            )

            cluster_samples = (
                level_membership[
                    level_membership[
                        "Cluster"
                    ]
                    .astype(int)
                    == cluster
                    ][
                    "GSA_ID"
                ]
                    .astype(str)
            )

            descendants = (
                selected_membership[
                    selected_membership[
                        "GSA_ID"
                    ]
                    .astype(str)
                    .isin(
                        cluster_samples
                    )
                ][
                    "Cluster"
                ]
                    .astype(int)
                    .unique()
                    .tolist()
            )

            descendants = sorted(
                descendants
            )

            summary_lines = []

            for variable in variables:

                stat_lines = _hierarchy_stat_lines(
                    row,
                    variable,
                    selected_stats,
                )

                if not stat_lines:
                    continue

                variable_children = [
                    html.Div(
                        variable,

                        style={
                            "fontWeight":
                                "700",

                            "fontSize":
                                "0.80rem",

                            "marginTop":
                                "4px",
                        },
                    )
                ]

                for label, value in stat_lines:
                    variable_children.append(
                        html.Div(
                            [
                                html.Span(
                                    f"{label}: ",

                                    style={
                                        "fontWeight":
                                            "600",
                                    },
                                ),

                                html.Span(
                                    value
                                ),
                            ],

                            style={
                                "fontSize":
                                    "0.76rem",

                                "lineHeight":
                                    "1.25",
                            },
                        )
                    )

                summary_lines.append(
                    html.Div(
                        variable_children,

                        style={
                            "marginBottom":
                                "4px",
                        },
                    )
                )

            descendant_chips = []

            for descendant in descendants:
                cluster_name = (
                    f"Cluster "
                    f"{descendant}"
                )

                color = (
                    cluster_palette.get(
                        cluster_name,
                        "#777777",
                    )
                )

                descendant_chips.append(
                    html.Span(
                        f"C{descendant}",

                        style={
                            "display":
                                "inline-block",

                            "padding":
                                "2px 6px",

                            "marginRight":
                                "4px",

                            "marginTop":
                                "4px",

                            "borderRadius":
                                "9px",

                            "fontSize":
                                "0.74rem",

                            "fontWeight":
                                "600",

                            "backgroundColor":
                                _hex_to_rgba(
                                    color,
                                    0.18,
                                ),

                            "border":
                                (
                                    "1px solid "
                                    f"{color}"
                                ),
                        },
                    )
                )

            cluster_name = (
                f"Cluster {cluster}"
            )

            if level == selected_k:

                border_color = (
                    cluster_palette.get(
                        cluster_name,
                        "#6b7280",
                    )
                )

                background = (
                    _hex_to_rgba(
                        border_color,
                        0.10,
                    )
                )

            else:

                border_color = (
                    "#9aa4b2"
                )

                background = (
                    "#f8fafc"
                )

            heading_children = [
                html.Span(
                    f"C{cluster}",

                    style={
                        "fontSize":
                            "1.0rem",

                        "fontWeight":
                            "700",
                    },
                ),
            ]

            if "n" in selected_stats:
                heading_children.append(
                    html.Span(
                        (
                            f"n = "
                            f"{int(row['n'])}"
                        ),

                        style={
                            "fontSize":
                                "0.80rem",

                            "marginLeft":
                                "10px",

                            "color":
                                "#52606d",
                        },
                    )
                )

            node_children = [
                html.Div(
                    heading_children
                ),
            ]

            if summary_lines:
                node_children.append(
                    html.Div(
                        summary_lines,

                        style={
                            "marginTop":
                                "6px",
                        },
                    )
                )

            if level != selected_k:
                node_children.append(
                    html.Div(
                        [
                            html.Div(
                                (
                                    f"Contains k="
                                    f"{selected_k}:"
                                ),

                                style={
                                    "fontSize":
                                        "0.74rem",

                                    "color":
                                        "#667085",

                                    "marginTop":
                                        "6px",
                                },
                            ),

                            html.Div(
                                descendant_chips
                            ),
                        ]
                    )
                )

            nodes.append(
                html.Div(
                    node_children,

                    style={
                        "border":
                            (
                                "2px solid "
                                f"{border_color}"
                            ),

                        "borderRadius":
                            "6px",

                        "backgroundColor":
                            background,

                        "padding":
                            "8px",

                        "minWidth":
                            "190px",

                        "boxSizing":
                            "border-box",
                    },
                )
            )

        rows.append(
            html.Div(
                [
                    html.Div(
                        (
                                f"k = {level}"
                                + (
                                    " (selected)"
                                    if level
                                       == selected_k
                                    else ""
                                )
                        ),

                        style={
                            "fontWeight":
                                "700",

                            "fontSize":
                                "0.93rem",

                            "marginBottom":
                                "7px",
                        },
                    ),

                    html.Div(
                        nodes,

                        style={
                            "display":
                                "grid",

                            "gridTemplateColumns":
                                (
                                    "repeat("
                                    "auto-fit, "
                                    "minmax("
                                    "190px, 1fr"
                                    ")"
                                ),

                            "gap":
                                "8px",
                        },
                    ),
                ],

                style={
                    "marginBottom":
                        "16px",
                },
            )
        )

    if selected_stats:

        stat_label_lookup = {
            "n":
                "N",

            "median":
                "Median",

            "iqr":
                "IQR",

            "mean":
                "Mean",

            "std":
                "Std Dev",

            "minmax":
                "Min–Max",
        }

        selected_stat_text = ", ".join(
            stat_label_lookup.get(
                stat,
                stat,
            )
            for stat
            in selected_stats
        )

    else:

        selected_stat_text = (
            "none"
        )

    return html.Div(
        [
            html.Div(
                (
                    "Broad → intermediate → detailed "
                    "cuts of the same hierarchical tree. "
                    f"Displayed statistics: "
                    f"{selected_stat_text}."
                ),

                style={
                    "fontSize":
                        "0.82rem",

                    "color":
                        "#667085",

                    "marginBottom":
                        "10px",
                },
            ),

            *rows,
        ]
    )


def _make_borehole_figure(
        borehole_df,
        cluster_palette,
        display_group_colors,
        color_mode,
        vertical_field,
        vertical_label,
        reverse_y,
        x_field="BoreholeID",
        x_label="BoreholeID",
        show_legend=True,
):
    """
    Borehole cluster view using the same visual encoding as PCA scores.

    Existing grouping:
        color  = Group By / Custom Group
        symbol = hierarchical cluster

    Hierarchical cluster grouping:
        color  = cluster
        symbol = cluster
    """

    fig = go.Figure()

    groups = sorted(
        borehole_df[
            "_group"
        ]
        .fillna(
            NULL_VALUE
        )
        .astype(str)
        .unique()
        .tolist()
    )

    clusters = sorted(
        borehole_df[
            "Cluster"
        ]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    for group in groups:

        group_df = borehole_df[
            borehole_df[
                "_group"
            ]
            .fillna(
                NULL_VALUE
            )
            .astype(str)
            == str(
                group
            )
        ]

        group_clusters = sorted(
            group_df[
                "Cluster"
            ]
            .dropna()
            .astype(int)
            .unique()
            .tolist()
        )

        for cluster in group_clusters:

            subset = group_df[
                group_df[
                    "Cluster"
                ]
                .astype(int)
                == int(
                    cluster
                )
            ]

            cluster_name = (
                f"Cluster {cluster}"
            )

            if color_mode == "cluster":

                marker_color = (
                    cluster_palette.get(
                        cluster_name,
                        "#777777",
                    )
                )

            else:

                marker_color = (
                    display_group_colors.get(
                        str(
                            group
                        ),
                        "#777777",
                    )
                )

            fig.add_trace(
                go.Scatter(
                    x=subset[
                        x_field
                    ],

                    y=subset[
                        vertical_field
                    ],

                    mode="markers",

                    name=(
                        f"{group} — "
                        f"{cluster_name}"
                    ),

                    showlegend=False,

                    marker=dict(
                        size=9,

                        color=marker_color,

                        symbol=
                            _cluster_symbol(
                                cluster
                            ),

                        line=dict(
                            width=0.7,
                            color="#333333",
                        ),
                    ),

                    customdata=(
                        subset[
                            [
                                "GSA_ID",
                                "_group",
                                "Cluster",
                            ]
                        ]
                        .to_numpy()
                    ),

                    hovertemplate=(
                        "Sample: %{customdata[0]}"
                        "<br>Group/Color: %{customdata[1]}"
                        f"<br>{x_label}: %{{x}}"
                        f"<br>{vertical_label}: "
                        "%{y:.2f}"
                        "<br>Cluster: %{customdata[2]}"
                        f"<br>Cluster symbol: "
                        f"{_cluster_symbol(cluster)}"
                        "<extra></extra>"
                    ),
                )
            )

    _add_pca_legends(
        fig,
        groups,
        (
            cluster_palette
            if color_mode == "cluster"
            else display_group_colors
        ),
        clusters,
        color_mode,
        show_legend,
    )

    fig.update_layout(
        autosize=True,

        margin=dict(
            l=75,
            r=330
            if show_legend
            else 30,
            t=20,
            b=110,
        ),

        legend=dict(
            orientation="v",
            x=1.01,
            y=1.0,
            xanchor="left",
            yanchor="top",
            tracegroupgap=6,
            font=dict(
                size=11,
            ),
        ),

        legend2=dict(
            orientation="v",
            x=1.18,
            y=1.0,
            xanchor="left",
            yanchor="top",
            tracegroupgap=6,
            font=dict(
                size=11,
            ),
        ),
    )

    if (
            str(
                borehole_df[
                    x_field
                ].dtype
            )
            == "category"
    ):

        present_categories = set(
            borehole_df[
                x_field
            ]
            .astype(str)
            .tolist()
        )

        x_order = [
            str(
                value
            )
            for value
            in borehole_df[
                x_field
            ].cat.categories
            if str(
                value
            )
            in present_categories
        ]

    else:

        x_order = (
            borehole_df[
                x_field
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        if x_field == "BoreholeID":

            x_order = sorted(
                x_order,
                key=_borehole_sort_key,
            )

        else:

            x_order = sorted(
                x_order,
                key=lambda value:
                    str(
                        value
                    ).casefold(),
            )

    fig.update_xaxes(
        title=x_label,

        categoryorder="array",
        categoryarray=x_order,

        tickangle=-45,

        automargin=True,
    )

    fig.update_yaxes(
        title=vertical_label,

        autorange=(
            "reversed"
            if reverse_y
            else True
        ),

        automargin=True,
    )

    return fig



def make_pca_plot(
        gsa_df,
        mmes_df,
        mmes_rs_df,
        selected_samples,
        panel,
):
    """
    Responsive integrated generic PCA / hierarchical
    analysis dashboard.

    Returns a Dash component, not one giant Plotly figure.
    """

    variables = panel.get(
        "analysis_variables",
        [],
    )

    standardize = panel.get(
        "analysis_standardize",
        True,
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

    report_sections = panel.get(
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

    report_sections = set(
        report_sections
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

    vertical_x_field = panel.get(
        "pca_vertical_x_field",
        "BoreholeID",
    )

    hierarchy_summary_stats = panel.get(
        "hierarchy_summary_stats",
        [
            "n",
            "median",
        ],
    )

    hierarchy_summary_variables = panel.get(
        "hierarchy_summary_variables",
        variables,
    )

    hierarchy_summary_variables = [
        variable
        for variable in (
                hierarchy_summary_variables
                or []
        )
        if variable in gsa_df.columns
    ]

    # --------------------------------------------------------
    # PCA
    # --------------------------------------------------------

    pca_result = calculate_pca(
        gsa_df,
        selected_samples,
        variables,
        standardize=standardize,
    )

    if pca_result is None:
        return html.Div(
            (
                "PCA — select at least two usable numeric "
                "variables and two complete samples."
            ),

            style={
                "padding":
                    "20px",

                "fontWeight":
                    "600",
            },
        )

    # --------------------------------------------------------
    # Hierarchical clustering
    # --------------------------------------------------------

    cluster_result = calculate_hierarchical(
        gsa_df,
        selected_samples,
        variables,
        standardize=standardize,
        linkage_method=linkage_method,
        distance_metric=distance_metric,
        cluster_k=cluster_k,
        silhouette_k_min=2,
        silhouette_k_max=10,
        summary_variables=hierarchy_summary_variables,
    )

    if cluster_result is None:
        return html.Div(
            (
                "PCA / clustering could not be calculated."
            ),

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
    )

    scores = (
        scores
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

    # --------------------------------------------------------
    # Final selected-k cluster colors
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # PCA point grouping
    # --------------------------------------------------------

    if color_mode == "cluster":

        scores["_group"] = (
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
        scores["_group"]
        .astype(str)
        .unique()
    )

    if color_mode == "cluster":

        # Use the exact same cluster colors as the hierarchy
        # and depth/borehole views.
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

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    preprocessing = (
        "Standardized"
        if standardize
        else "Unstandardized"
    )

    color_description = (
        "hierarchical cluster"
        if color_mode
           == "cluster"
        else "existing grouping"
    )

    selected_variables = (
        ", ".join(
            pca_result[
                "variables"
            ]
        )
    )

    header = html.Div(
        [
            html.Div(
                (
                    "Generic PCA / Hierarchical "
                    f"Analysis — {preprocessing}"
                ),

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
                    f"{len(pca_result['variables'])} variables; "
                    f"{cluster_result['linkage_method'].title()} linkage; "
                    f"{cluster_result['distance_metric'].title()} distance; "
                    f"PCA colored by {color_description}"
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
                        "Selected Variables: ",

                        style={
                            "fontWeight":
                                "700",
                        },
                    ),

                    html.Span(
                        selected_variables
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

    # --------------------------------------------------------
    # Independent figures
    # --------------------------------------------------------

    score_fig = _make_score_figure(
        scores,
        pca_result[
            "explained_variance_ratio"
        ],
        pca_result[
            "loadings"
        ],
        display_group_colors,
        show_labels,
        show_legend,
        color_mode,
        show_loading_arrows=
        show_loading_arrows,
    )

    scree_fig = _make_scree_figure(
        pca_result[
            "explained_variance_ratio"
        ],
        pca_result[
            "cumulative_variance_ratio"
        ],
    )

    loadings_fig = _make_loadings_figure(
        pca_result[
            "loadings"
        ]
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

    summary_table = (
        _build_summary_table(
            cluster_result[
                "cluster_summary"
            ],
            pca_result[
                "variables"
            ],
            cluster_palette,
        )
    )

    # --------------------------------------------------------
    # Current-k membership heatmap / table
    #
    # The existing PCA Point Grouping toggle controls the
    # organization:
    #
    #   Group By / Custom Groups -> Group × Cluster heatmap
    #   Hierarchical Cluster     -> Cluster | N table
    #
    # This keeps the heatmap behavior synchronized with the
    # existing grouping architecture without adding another
    # redundant mode control.
    # --------------------------------------------------------

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
            "MGS_GSA_PCA_"
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
            "MGS_GSA_PCA_"
            "Group_Cluster_Heatmap"
        )

    # --------------------------------------------------------
    # Calculated grain-fraction histogram
    #
    # Uses the same current PCA organization as point coloring:
    #   cluster mode -> one bar trace per current-k cluster
    #   group mode   -> one bar trace per Group By / Custom Group
    #
    # Fraction math is reused directly from Grain Size Log.
    # --------------------------------------------------------

    grain_fraction_df = (
        _build_grain_fraction_dataframe(
            gsa_df,
            mmes_df,
            mmes_rs_df,
            scores,
            panel,
        )
    )

    grain_histogram_fig = (
        _make_grain_fraction_histogram(
            grain_fraction_df,
            color_mode,
            display_group_colors,
            cluster_palette,
        )
    )

    grain_histogram_settings = (
        _grain_fraction_settings_text(
            panel,
            grain_fraction_df,
        )
    )

    # --------------------------------------------------------
    # Responsive dashboard rows
    #
    # The pair grids use all available horizontal space.
    # With enough width they display side-by-side; with less
    # width they stack automatically.
    # --------------------------------------------------------

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
                            panel["id"]
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

    # --------------------------------------------------------
    # PCA Scores
    # --------------------------------------------------------

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
                                "MGS_GSA_PCA_Scores",

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

    # --------------------------------------------------------
    # Current-k Cluster / Group Heatmap
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Calculated Grain-Fraction Histogram
    # --------------------------------------------------------

    if "grain_histogram" in report_sections:
        dashboard_children.append(
            _card(
                (
                        "Calculated Grain-Fraction Histograms — "
                        + (
                            f"Clusters (k = {selected_k})"
                            if color_mode == "cluster"
                            else "Current Grouping"
                        )
                ),

                html.Div(
                    [
                        html.Div(
                            grain_histogram_settings,

                            style={
                                "fontSize":
                                    "0.80rem",

                                "color":
                                    "#667085",

                                "marginBottom":
                                    "4px",
                            },
                        ),

                        dcc.Graph(
                            figure=
                            grain_histogram_fig,

                            responsive=True,

                            config={
                                **GRAPH_CONFIG,

                                "toImageButtonOptions": {
                                    "format":
                                        "png",

                                    "filename":
                                        (
                                            "MGS_GSA_PCA_"
                                            "Grain_Fraction_Histograms"
                                        ),

                                    "scale":
                                        2,
                                },
                            },

                            style={
                                "width":
                                    "100%",

                                # Plotly's responsive sizing otherwise
                                # collapses this many-row subplot figure
                                # back toward the default graph height.
                                # Force the Dash graph container to match
                                # the height calculated by the figure.
                                "height":
                                    (
                                        f"{int(grain_histogram_fig.layout.height)}px"
                                        if grain_histogram_fig.layout.height
                                        else "520px"
                                    ),

                                "minHeight":
                                    (
                                        f"{int(grain_histogram_fig.layout.height)}px"
                                        if grain_histogram_fig.layout.height
                                        else "520px"
                                    ),
                            },
                        ),
                    ]
                ),
            )
        )

    # --------------------------------------------------------
    # Scree + Loadings
    # --------------------------------------------------------

    upper_pair = []

    if "scree" in report_sections:
        upper_pair.append(
            _card(
                "Scree Plot",

                dcc.Graph(
                    figure=scree_fig,
                    responsive=True,

                    config={
                        **GRAPH_CONFIG,

                        "toImageButtonOptions": {
                            "format":
                                "png",

                            "filename":
                                "MGS_GSA_PCA_Scree",

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
                "PC1 / PC2 Loadings",

                dcc.Graph(
                    figure=loadings_fig,
                    responsive=True,

                    config={
                        **GRAPH_CONFIG,

                        "toImageButtonOptions": {
                            "format":
                                "png",

                            "filename":
                                "MGS_GSA_PCA_Loadings",

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

                style=pair_grid_style,
            )
        )

    # --------------------------------------------------------
    # Hierarchy Summary
    # --------------------------------------------------------

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
    # --------------------------------------------------------
    # Silhouette + Cluster Summary
    # --------------------------------------------------------

    lower_pair = []

    if "silhouette" in report_sections:
        lower_pair.append(
            _card(
                "Silhouette by Number of Clusters",

                dcc.Graph(
                    figure=silhouette_fig,
                    responsive=True,

                    config={
                        **GRAPH_CONFIG,

                        "toImageButtonOptions": {
                            "format":
                                "png",

                            "filename":
                                "MGS_GSA_PCA_Silhouette",

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

                style=pair_grid_style,
            )
        )

    # --------------------------------------------------------
    # Optional depth / borehole
    # --------------------------------------------------------

    if show_depth_borehole:

        depth_result = _get_borehole_data(
            gsa_df,
            scores[
                [
                    "GSA_ID",
                    "Cluster",
                    "_group",
                ]
            ],
            vertical_axis=
            borehole_vertical_axis,
            x_field=
            vertical_x_field,
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
                    display_group_colors,
                    color_mode,
                    depth_result[
                        "vertical_field"
                    ],
                    depth_result[
                        "vertical_label"
                    ],
                    depth_result[
                        "reverse_y"
                    ],
                    x_field=
                        depth_result[
                            "x_field"
                        ],
                    x_label=
                        depth_result[
                            "x_label"
                        ],
                    show_legend=
                        show_legend,
                )
            )

            # Native CSS vertical resize handle. The graph fills
            # this container and Plotly responds to its size.
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
                        figure=depth_fig,
                        responsive=True,

                        config={
                            **GRAPH_CONFIG,

                            "toImageButtonOptions": {
                                "format":
                                    "png",

                                "filename":
                                    (
                                        "MGS_GSA_PCA_"
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
                    "Cluster by "
                    f"{depth_result['x_label']} — "
                    f"{depth_result['vertical_label']} "
                    "(up to 50 categories; ≥5 samples)"
                ),

                depth_child,
            )
        )

    # --------------------------------------------------------
    # Explicit note when depth is one of the variables
    # --------------------------------------------------------

    selected_vertical_analysis_field = (
        "sample_elevation"
        if borehole_vertical_axis
           == "elevation"
        else "depth_ft"
    )

    if (
            show_depth_borehole
            and selected_vertical_analysis_field
            in pca_result[
        "variables"
    ]
    ):
        dashboard_children.append(
            html.Div(
                (
                    f"Note: {selected_vertical_analysis_field} "
                    "is one of the analysis variables, so the "
                    "borehole pattern partly reflects that "
                    "variable being used in the clustering."
                ),

                style={
                    "fontSize":
                        "0.82rem",

                    "fontStyle":
                        "italic",

                    "color":
                        "#667085",
                },
            )
        )

    report = html.Div(
        dashboard_children,

        id=report_id,

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

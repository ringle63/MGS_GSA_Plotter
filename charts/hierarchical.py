import plotly.graph_objects as go

from logic.multivariate import (
    calculate_hierarchical,
)


def make_hierarchical_plot(
        gsa_df,
        selected_samples,
        panel,
):
    fig = go.Figure()

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

    result = calculate_hierarchical(
        gsa_df,
        selected_samples,
        variables,
        standardize=standardize,
        linkage_method=linkage_method,
        distance_metric=distance_metric,
        cluster_k=cluster_k,
        silhouette_k_min=2,
        silhouette_k_max=10,
    )

    if result is None:

        fig.update_layout(
            title=(
                "Hierarchical Clustering — "
                "select at least two usable "
                "numeric variables and two "
                "complete samples"
            )
        )

        return fig

    dendro = result[
        "dendrogram"
    ]

    for xs, ys in zip(
            dendro[
                "icoord"
            ],
            dendro[
                "dcoord"
            ],
    ):

        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,

                mode="lines",

                showlegend=False,

                hoverinfo="skip",

                line=dict(
                    width=1.5,
                ),
            )
        )

    labels = (
        dendro[
            "ivl"
        ]
    )

    tickvals = [
        5 + (
                10
                * i
        )
        for i in range(
            len(labels)
        )
    ]

    show_labels = (
            len(labels)
            <= 40
    )

    if (
            result[
                "cut_height"
            ]
            is not None
    ):

        fig.add_hline(
            y=result[
                "cut_height"
            ],

            line_width=2,

            line_dash="dash",

            annotation_text=(
                f"k = "
                f"{result['selected_k']}"
            ),

            annotation_position=(
                "top right"
            ),
        )

    preprocessing = (
        "Standardized"
        if standardize
        else "Unstandardized"
    )

    fig.update_layout(
        title=(
            f"Hierarchical Clustering — "
            f"{result['linkage_method'].title()} Linkage"
            f"<br>"
            f"<sup>"
            f"{preprocessing}; "
            f"{result['distance_metric'].title()} distance; "
            f"k = {result['selected_k']}; "
            f"{len(result['samples'])} samples; "
            f"{len(result['variables'])} variables"
            f"</sup>"
        ),

        xaxis=dict(
            title="Samples",

            tickmode="array",

            tickvals=(
                tickvals
                if show_labels
                else []
            ),

            ticktext=(
                labels
                if show_labels
                else []
            ),

            tickangle=-90,
        ),

        yaxis=dict(
            title="Cluster Distance",
        ),

        hovermode=False,

        margin=dict(
            b=140,
        ),
    )

    return fig
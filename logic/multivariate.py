import numpy as np
import pandas as pd

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from scipy.cluster.hierarchy import (
    linkage,
    dendrogram,
    cut_tree,
)


# ============================================================
# SHARED DATA PREPARATION
# ============================================================

def prepare_multivariate_data(
        gsa_df,
        selected_samples,
        variables,
        standardize=True,
):
    """
    Build the common numeric matrix used by PCA and
    hierarchical clustering.

    Complete-case behavior:
    a sample is included only when it has a numeric
    value for every selected variable.

    Constant variables are removed automatically.
    """

    selected_samples = [
        str(sample)
        for sample in (
                selected_samples
                or []
        )
    ]

    variables = [
        variable
        for variable in (
                variables
                or []
        )
        if variable in gsa_df.columns
    ]

    if len(variables) < 2:
        return None

    subset = (
        gsa_df[
            gsa_df["GSA_ID"]
            .astype(str)
            .isin(selected_samples)
        ][
            [
                "GSA_ID",
                *variables,
            ]
        ]
        .copy()
    )

    subset["GSA_ID"] = (
        subset["GSA_ID"]
        .astype(str)
    )

    subset = (
        subset
        .drop_duplicates(
            "GSA_ID"
        )
    )

    for variable in variables:

        subset[variable] = (
            pd.to_numeric(
                subset[variable],
                errors="coerce",
            )
        )

    # --------------------------------------------------------
    # Complete-case analysis
    # --------------------------------------------------------

    subset = (
        subset
        .dropna(
            subset=variables
        )
        .reset_index(
            drop=True
        )
    )

    if len(subset) < 2:
        return None

    # --------------------------------------------------------
    # Remove constant variables
    # --------------------------------------------------------

    usable_variables = []

    for variable in variables:

        values = (
            subset[variable]
            .to_numpy(
                dtype=float
            )
        )

        if np.nanstd(values) > 0:

            usable_variables.append(
                variable
            )

    if len(usable_variables) < 2:
        return None

    subset = (
        subset[
            [
                "GSA_ID",
                *usable_variables,
            ]
        ]
        .copy()
    )

    raw_matrix = (
        subset[
            usable_variables
        ]
        .to_numpy(
            dtype=float
        )
    )

    # --------------------------------------------------------
    # Optional standardization
    # --------------------------------------------------------

    if standardize:

        scaler = StandardScaler()

        matrix = (
            scaler
            .fit_transform(
                raw_matrix
            )
        )

    else:

        scaler = None
        matrix = raw_matrix.copy()

    return {
        "samples":
            subset[
                "GSA_ID"
            ].tolist(),

        "variables":
            usable_variables,

        "dataframe":
            subset,

        "raw_matrix":
            raw_matrix,

        "matrix":
            matrix,

        "standardized":
            bool(
                standardize
            ),

        "scaler":
            scaler,
    }


# ============================================================
# PCA
# ============================================================

def calculate_pca(
        gsa_df,
        selected_samples,
        variables,
        standardize=True,
):
    """
    Calculate PCA scores, loadings, and explained variance.
    """

    prepared = prepare_multivariate_data(
        gsa_df,
        selected_samples,
        variables,
        standardize=standardize,
    )

    if prepared is None:
        return None

    matrix = prepared[
        "matrix"
    ]

    n_components = min(
        matrix.shape[0],
        matrix.shape[1],
    )

    if n_components < 2:
        return None

    model = PCA(
        n_components=n_components
    )

    scores = (
        model
        .fit_transform(
            matrix
        )
    )

    component_names = [
        f"PC{i + 1}"
        for i in range(
            n_components
        )
    ]

    scores_df = pd.DataFrame(
        scores,
        columns=component_names,
    )

    scores_df.insert(
        0,
        "GSA_ID",
        prepared[
            "samples"
        ],
    )

    loadings = pd.DataFrame(
        model.components_.T,
        index=prepared[
            "variables"
        ],
        columns=component_names,
    )

    explained = (
        model
        .explained_variance_ratio_
    )

    cumulative = np.cumsum(
        explained
    )

    return {
        **prepared,

        "model":
            model,

        "scores":
            scores_df,

        "loadings":
            loadings,

        "explained_variance_ratio":
            explained,

        "cumulative_variance_ratio":
            cumulative,
    }


# ============================================================
# CLUSTER HELPERS
# ============================================================

def _resolve_cluster_settings(
        linkage_method,
        distance_metric,
):
    linkage_method = (
        linkage_method
        or "ward"
    )

    distance_metric = (
        distance_metric
        or "euclidean"
    )

    # Ward clustering requires Euclidean distance.
    if linkage_method == "ward":
        distance_metric = "euclidean"

    return (
        linkage_method,
        distance_metric,
    )


def _get_cut_height(
        linkage_matrix,
        n_samples,
        k,
):
    """
    Return a dendrogram height between the merge that
    produces k clusters and the next merge above it.

    This is only a display threshold. Cluster membership
    itself comes from cut_tree().
    """

    if (
            linkage_matrix is None
            or len(linkage_matrix) == 0
    ):
        return None

    if k <= 1:
        return (
                float(
                    linkage_matrix[
                        -1,
                        2,
                    ]
                )
                + 1e-9
        )

    if k >= n_samples:

        return 0.0

    lower_index = (
            n_samples
            - k
            - 1
    )

    upper_index = (
            n_samples
            - k
    )

    lower_height = (
        0.0
        if lower_index < 0
        else float(
            linkage_matrix[
                lower_index,
                2,
            ]
        )
    )

    upper_height = float(
        linkage_matrix[
            upper_index,
            2,
        ]
    )

    return (
            lower_height
            + upper_height
    ) / 2.0


# ============================================================
# HIERARCHICAL CLUSTERING
# ============================================================


def _build_cluster_summary(
        prepared,
        cluster_labels,
        summary_df=None,
        summary_variables=None,
):
    """
    Summarize each cluster using the original, unstandardized
    analysis variables.

    Returns:
      Cluster
      n
      <variable>_median
      <variable>_q25
      <variable>_q75
    """

    if summary_df is None:

        summary_source = (
            prepared["dataframe"]
            .copy()
        )

        variables = list(
            prepared["variables"]
        )

    else:

        summary_source = (
            summary_df
            .copy()
        )

        variables = [
            variable
            for variable in (
                summary_variables
                or []
            )
            if variable in summary_source.columns
        ]

    summary_source[
        "GSA_ID"
    ] = (
        summary_source[
            "GSA_ID"
        ]
        .astype(str)
    )

    summary_source = (
        summary_source
        .set_index(
            "GSA_ID"
        )
        .reindex(
            prepared[
                "samples"
            ]
        )
        .reset_index()
    )

    summary_source[
        "Cluster"
    ] = cluster_labels

    records = []

    for cluster in sorted(
            summary_source["Cluster"]
            .astype(int)
            .unique()
    ):

        cluster_df = summary_source[
            summary_source["Cluster"]
            .astype(int)
            == int(cluster)
        ]

        record = {
            "Cluster": int(cluster),
            "n": int(len(cluster_df)),
        }

        for variable in variables:

            series = pd.to_numeric(
                cluster_df[variable],
                errors="coerce",
            ).dropna()

            if series.empty:
                record[f"{variable}_median"] = np.nan
                record[f"{variable}_q25"] = np.nan
                record[f"{variable}_q75"] = np.nan
                record[f"{variable}_mean"] = np.nan
                record[f"{variable}_std"] = np.nan
                record[f"{variable}_min"] = np.nan
                record[f"{variable}_max"] = np.nan

            else:
                record[f"{variable}_median"] = float(
                    series.median()
                )
                record[f"{variable}_q25"] = float(
                    series.quantile(0.25)
                )
                record[f"{variable}_q75"] = float(
                    series.quantile(0.75)
                )
                record[f"{variable}_mean"] = float(
                    series.mean()
                )

                std_value = series.std(
                    ddof=1
                )

                record[f"{variable}_std"] = (
                    float(std_value)
                    if pd.notna(std_value)
                    else np.nan
                )

                record[f"{variable}_min"] = float(
                    series.min()
                )
                record[f"{variable}_max"] = float(
                    series.max()
                )

        records.append(record)

    return pd.DataFrame(records)


def _build_cluster_hierarchy(
        linkage_matrix,
        prepared,
        selected_k,
        summary_df=None,
        summary_variables=None,
):
    """
    Build a compact broad -> intermediate -> selected-k
    hierarchy from the SAME hierarchical tree.

    Display levels:
      k = 2
      k = ceil(selected_k / 2)
      k = selected_k

    Duplicate levels are removed.

    The returned relationships identify which child cluster
    belongs to which parent cluster. Summaries use the
    original, unstandardized selected variables.
    """

    n_samples = len(
        prepared["samples"]
    )

    if (
            linkage_matrix is None
            or n_samples < 2
    ):
        return None

    selected_k = max(
        2,
        min(
            int(selected_k),
            n_samples,
        ),
    )

    intermediate_k = max(
        2,
        int(
            np.ceil(
                selected_k / 2
            )
        ),
    )

    levels = []

    for k in [
        2,
        intermediate_k,
        selected_k,
    ]:

        if (
                k <= n_samples
                and k not in levels
        ):
            levels.append(k)

    memberships = {}
    summaries = {}

    for k in levels:

        labels = (
            cut_tree(
                linkage_matrix,
                n_clusters=[k],
            )
            .reshape(-1)
            + 1
        )

        memberships[k] = pd.DataFrame(
            {
                "GSA_ID": [
                    str(sample)
                    for sample
                    in prepared["samples"]
                ],
                "Cluster":
                    labels.astype(int),
            }
        )

        summaries[k] = _build_cluster_summary(
            prepared,
            labels.astype(int),
            summary_df=summary_df,
            summary_variables=summary_variables,
        )

    relationships = []

    for parent_k, child_k in zip(
            levels[:-1],
            levels[1:],
    ):

        parent = (
            memberships[parent_k]
            .rename(
                columns={
                    "Cluster":
                        "ParentCluster"
                }
            )
        )

        child = (
            memberships[child_k]
            .rename(
                columns={
                    "Cluster":
                        "ChildCluster"
                }
            )
        )

        merged = (
            parent
            .merge(
                child,
                on="GSA_ID",
                how="inner",
            )
        )

        relationship_counts = (
            merged
            .groupby(
                [
                    "ParentCluster",
                    "ChildCluster",
                ]
            )
            .size()
            .reset_index(
                name="n"
            )
        )

        for _, row in relationship_counts.iterrows():

            relationships.append(
                {
                    "parent_k":
                        int(parent_k),

                    "parent_cluster":
                        int(
                            row[
                                "ParentCluster"
                            ]
                        ),

                    "child_k":
                        int(child_k),

                    "child_cluster":
                        int(
                            row[
                                "ChildCluster"
                            ]
                        ),

                    "n":
                        int(
                            row["n"]
                        ),
                }
            )

    return {
        "levels":
            levels,

        "memberships":
            memberships,

        "summaries":
            summaries,

        "relationships":
            relationships,
    }


def calculate_hierarchical(
        gsa_df,
        selected_samples,
        variables,
        standardize=True,
        linkage_method="ward",
        distance_metric="euclidean",
        cluster_k=4,
        silhouette_k_min=2,
        silhouette_k_max=10,
        summary_variables=None,
):
    """
    Build one hierarchical clustering tree from the same
    matrix used by PCA.

    cluster_k controls only the cut of that existing tree.

    Silhouette values are calculated for candidate k values
    without rebuilding the hierarchical tree.

    The compact hierarchy summary is also derived from this
    same linkage tree, so k=2, intermediate k, and selected k
    are nested views of the same solution.
    """

    prepared = prepare_multivariate_data(
        gsa_df,
        selected_samples,
        variables,
        standardize=standardize,
    )

    if prepared is None:
        return None

    matrix = prepared["matrix"]
    n_samples = len(matrix)

    if n_samples < 2:
        return None

    (
        linkage_method,
        distance_metric,
    ) = _resolve_cluster_settings(
        linkage_method,
        distance_metric,
    )

    # --------------------------------------------------------
    # Build the hierarchical tree ONCE
    # --------------------------------------------------------

    linkage_matrix = linkage(
        matrix,
        method=linkage_method,
        metric=distance_metric,
    )

    # --------------------------------------------------------
    # Selected cluster cut
    # --------------------------------------------------------

    requested_k = int(
        cluster_k
        or 4
    )

    selected_k = max(
        2,
        min(
            requested_k,
            n_samples,
        ),
    )

    cluster_labels = (
        cut_tree(
            linkage_matrix,
            n_clusters=[
                selected_k
            ],
        )
        .reshape(-1)
        + 1
    )

    cluster_labels = (
        cluster_labels
        .astype(int)
    )

    cluster_df = pd.DataFrame(
        {
            "GSA_ID":
                prepared["samples"],

            "Cluster":
                cluster_labels,
        }
    )

    # --------------------------------------------------------
    # Keep dendrogram data for backwards compatibility with
    # old saved "Hierarchical Clustering" panels.
    # The integrated PCA dashboard no longer renders the
    # sample-level dendrogram.
    # --------------------------------------------------------

    cut_height = _get_cut_height(
        linkage_matrix,
        n_samples,
        selected_k,
    )

    dendrogram_data = dendrogram(
        linkage_matrix,
        labels=prepared[
            "samples"
        ],
        no_plot=True,
        color_threshold=cut_height,
        above_threshold_color="#6b7280",
    )

    # --------------------------------------------------------
    # Silhouette evaluation
    # --------------------------------------------------------

    silhouette_records = []

    candidate_max = min(
        int(
            silhouette_k_max
            or 10
        ),
        n_samples - 1,
    )

    candidate_min = max(
        2,
        int(
            silhouette_k_min
            or 2
        ),
    )

    if candidate_max >= candidate_min:

        for k in range(
                candidate_min,
                candidate_max + 1,
        ):

            labels = (
                cut_tree(
                    linkage_matrix,
                    n_clusters=[
                        k
                    ],
                )
                .reshape(-1)
            )

            unique_labels = np.unique(
                labels
            )

            if not (
                    1
                    < len(unique_labels)
                    < n_samples
            ):
                continue

            try:

                value = silhouette_score(
                    matrix,
                    labels,
                    metric=distance_metric,
                )

            except Exception:
                continue

            silhouette_records.append(
                {
                    "k":
                        int(k),

                    "silhouette":
                        float(value),
                }
            )

    silhouette_df = pd.DataFrame(
        silhouette_records,
        columns=[
            "k",
            "silhouette",
        ],
    )

    # --------------------------------------------------------
    # Optional independent hierarchy-summary variables
    #
    # Clustering/PCA still use ONLY the selected analysis
    # variables. These extra variables are descriptive only.
    # --------------------------------------------------------

    summary_variables = [
        variable
        for variable in (
            summary_variables
            or prepared[
                "variables"
            ]
        )
        if variable in gsa_df.columns
    ]

    summary_df = (
        gsa_df[
            [
                "GSA_ID",
                *summary_variables,
            ]
        ]
        .copy()
    )

    summary_df[
        "GSA_ID"
    ] = (
        summary_df[
            "GSA_ID"
        ]
        .astype(str)
    )

    for variable in summary_variables:

        summary_df[
            variable
        ] = pd.to_numeric(
            summary_df[
                variable
            ],
            errors="coerce",
        )

    summary_df = (
        summary_df
        .drop_duplicates(
            "GSA_ID"
        )
    )

    # --------------------------------------------------------
    # Selected-k summary + compact hierarchy
    # --------------------------------------------------------

    cluster_summary = _build_cluster_summary(
        prepared,
        cluster_labels,
    )

    hierarchy = _build_cluster_hierarchy(
        linkage_matrix,
        prepared,
        selected_k,
        summary_df=summary_df,
        summary_variables=summary_variables,
    )

    return {
        **prepared,

        "linkage_method":
            linkage_method,

        "distance_metric":
            distance_metric,

        "linkage_matrix":
            linkage_matrix,

        "dendrogram":
            dendrogram_data,

        "selected_k":
            selected_k,

        "clusters":
            cluster_df,

        "cut_height":
            cut_height,

        "silhouette":
            silhouette_df,

        "cluster_summary":
            cluster_summary,

        "hierarchy":
            hierarchy,
    }

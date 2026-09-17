import numpy as np
import pandas as pd

from logic.custom_groups import (
    build_custom_groups,
    has_custom_groups,
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


def get_psd_export_df(
        mmes_df,
        mmes_rs_df,
        selected_samples,
):
    selected_samples = selected_samples or []

    # -------------------------------------------------
    # Get native PSD columns for each MMES source
    # -------------------------------------------------

    primary_cols, primary_x = get_psd_columns(
        "PRIMARY",
        mmes_df,
        mmes_rs_df,
    )

    rs_cols, rs_x = get_psd_columns(
        "RS",
        mmes_df,
        mmes_rs_df,
    )

    # -------------------------------------------------
    # Build one combined column order.
    #
    # PRIMARY and RS use different native bins, so
    # preserve all native fields and sort them by
    # grain size.
    # -------------------------------------------------

    curve_fields = []

    for col, x in zip(
            primary_cols,
            primary_x,
    ):
        curve_fields.append(
            (float(x), col)
        )

    for col, x in zip(
            rs_cols,
            rs_x,
    ):
        curve_fields.append(
            (float(x), col)
        )

    curve_fields.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    psd_cols = []

    for _, col in curve_fields:

        if col not in psd_cols:
            psd_cols.append(col)

    # -------------------------------------------------
    # Build export rows using the same source lookup
    # used by the PSD plot.
    #
    # This preserves PRIMARY-first lookup behavior if
    # a sample name happens to exist in both sources.
    # -------------------------------------------------

    records = []

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

        if source == "PRIMARY":

            source_cols = primary_cols

        elif source == "RS":

            source_cols = rs_cols

        else:
            continue

        record = {
            "GSA_ID": str(sample),
        }

        for col in source_cols:
            record[col] = row[col]

        records.append(record)

    # -------------------------------------------------
    # Create dataframe.
    #
    # Columns belonging to the other MMES source will
    # naturally remain blank/NaN for that sample.
    # -------------------------------------------------

    if not records:
        return pd.DataFrame(
            columns=[
                "GSA_ID",
                *psd_cols,
            ]
        )

    subset = pd.DataFrame(
        records
    )

    for col in psd_cols:

        if col not in subset.columns:
            subset[col] = pd.NA

    subset = subset[
        [
            "GSA_ID",
            *psd_cols,
        ]
    ]

    return subset


def get_frequency_export_df(
        mmes_df,
        mmes_rs_df,
        selected_samples,
):
    selected_samples = selected_samples or []

    # -------------------------------------------------
    # Get native frequency columns for each MMES source
    # -------------------------------------------------

    primary_cols, primary_x = get_fr_columns(
        "PRIMARY",
        mmes_df,
        mmes_rs_df,
    )

    rs_cols, rs_x = get_fr_columns(
        "RS",
        mmes_df,
        mmes_rs_df,
    )

    # -------------------------------------------------
    # Build one combined column order.
    #
    # Preserve both native bin schemes and sort fields
    # by grain size.
    # -------------------------------------------------

    curve_fields = []

    for col, x in zip(
            primary_cols,
            primary_x,
    ):
        curve_fields.append(
            (float(x), col)
        )

    for col, x in zip(
            rs_cols,
            rs_x,
    ):
        curve_fields.append(
            (float(x), col)
        )

    curve_fields.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    fr_cols = []

    for _, col in curve_fields:

        if col not in fr_cols:
            fr_cols.append(col)

    # -------------------------------------------------
    # Build export rows using the same source lookup
    # used by the Frequency plot.
    # -------------------------------------------------

    records = []

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

        if source == "PRIMARY":

            source_cols = primary_cols

        elif source == "RS":

            source_cols = rs_cols

        else:
            continue

        record = {
            "GSA_ID": str(sample),
        }

        for col in source_cols:
            record[col] = row[col]

        records.append(record)

    # -------------------------------------------------
    # Create dataframe.
    #
    # Native bins from the other source remain blank
    # for each sample.
    # -------------------------------------------------

    if not records:
        return pd.DataFrame(
            columns=[
                "GSA_ID",
                *fr_cols,
            ]
        )

    subset = pd.DataFrame(
        records
    )

    for col in fr_cols:

        if col not in subset.columns:
            subset[col] = pd.NA

    subset = subset[
        [
            "GSA_ID",
            *fr_cols,
        ]
    ]

    return subset


def get_ternary_export_df(
        gsa_df,
        selected_samples,
        panel,
):
    subset = gsa_df[
        gsa_df["GSA_ID"]
        .astype(str)
        .isin(selected_samples)
    ].copy()

    export_fields = [
        "GSA_ID",
        "analysis_method",
    ]

    method_fields = {}

    # Mastersizer
    ms_break = panel["mastersizer_break"]

    if ms_break == 2:
        method_fields["Mastersizer"] = [
            "Clay0_2",
            "Silt2_625",
            "Sand625_2000",
        ]

    elif ms_break == 4:
        method_fields["Mastersizer"] = [
            "Clay0_4",
            "Silt_4_625",
            "Sand625_2000",
        ]

    elif ms_break == 8:
        method_fields["Mastersizer"] = [
            "Clay0_8",
            "Silt_8_625",
            "Sand625_2000",
        ]

    # Pipette
    pip_break = panel["pipette_break"]

    if pip_break == 2:
        method_fields["Pipette"] = [
            "ClayG_0_2",
            "SiltG_2_625",
            "SandG_625_2000",
        ]

    elif pip_break == 4:
        method_fields["Pipette"] = [
            "ClayG_0_4",
            "SiltG_4_625",
            "SandG_625_2000",
        ]

    # Kehew
    method_fields["Kehew"] = [
        "ClayG_0_4",
        "SiltG_4_625",
        "SandG_625_2000",
    ]

    # Dry Sieve
    method_fields["Dry Sieve"] = [
        "Fines_0_63",
        "Sand625_2000",
    ]

    for fields in method_fields.values():

        for field in fields:

            if field not in export_fields:
                export_fields.append(field)

    export_fields = [
        field
        for field in export_fields
        if field in subset.columns
    ]

    return subset[export_fields]


def get_grainlog_export_df(
        gsa_df,
        selected_samples,
        panel,
):
    subset = gsa_df[
        gsa_df["GSA_ID"]
        .astype(str)
        .isin(selected_samples)
    ].copy()

    export_fields = [
        "GSA_ID",
        "analysis_method",
    ]

    method_fields = {}

    ms_break = panel["mastersizer_break"]

    if ms_break == 2:
        method_fields["Mastersizer"] = [
            "Clay0_2",
            "Silt2_625",
        ]

    elif ms_break == 4:
        method_fields["Mastersizer"] = [
            "Clay0_4",
            "Silt_4_625",
        ]

    elif ms_break == 8:
        method_fields["Mastersizer"] = [
            "Clay0_8",
            "Silt_8_625",
        ]

    method_fields["Mastersizer"] += [
        "sandfrac_vf",
        "sandfrac_f",
        "sandfrac_m",
        "sandfrac_c",
        "sandfrac_vc",
    ]

    pip_break = panel["pipette_break"]

    if pip_break == 2:
        method_fields["Pipette"] = [
            "ClayG_0_2",
            "SiltG_2_625",
        ]

    elif pip_break == 4:
        method_fields["Pipette"] = [
            "ClayG_0_4",
            "SiltG_4_625",
        ]

    method_fields["Pipette"] += [
        "sandfracG_vf",
        "sandfracG_f",
        "sandfracG_m",
        "sandfracG_c",
        "sandfracG_vc",
        "GravelG_2000_3500",
    ]

    method_fields["Kehew"] = [
        "ClayG_0_4",
        "SiltG_4_625",

        "sandfracG_vf",
        "sandfracG_f",
        "sandfracG_m",
        "sandfracG_c",
        "sandfracG_vc",

        "GravelG_2000_3500",
    ]

    method_fields["Dry Sieve"] = [
        "FinesG_0_63",

        "sandfracG_vf",
        "sandfracG_f",
        "sandfracG_m",
        "sandfracG_c",
        "sandfracG_vc",

        "GravelG_2000_3500",
    ]

    for fields in method_fields.values():

        for field in fields:

            if field not in export_fields:
                export_fields.append(field)

    export_fields = [
        field
        for field in export_fields
        if field in subset.columns
    ]

    return subset[export_fields]


def get_pca_export_df(
        gsa_df,
        selected_samples,
        panel,
):
    pca_result = calculate_pca(
        gsa_df,
        selected_samples,
        panel.get(
            "analysis_variables",
            [],
        ),
        standardize=panel.get(
            "analysis_standardize",
            True,
        ),
    )

    if pca_result is None:

        return pd.DataFrame(
            columns=[
                "GSA_ID",
            ]
        )

    cluster_result = calculate_hierarchical(
        gsa_df,
        selected_samples,
        panel.get(
            "analysis_variables",
            [],
        ),
        standardize=panel.get(
            "analysis_standardize",
            True,
        ),
        linkage_method=panel.get(
            "cluster_linkage",
            "ward",
        ),
        distance_metric=panel.get(
            "cluster_metric",
            "euclidean",
        ),
        cluster_k=panel.get(
            "cluster_k",
            4,
        ),
        silhouette_k_min=2,
        silhouette_k_max=10,
    )

    output = (
        pca_result[
            "dataframe"
        ]
        .copy()
    )

    output = (
        output
        .merge(
            pca_result[
                "scores"
            ],
            on="GSA_ID",
            how="left",
        )
    )

    if cluster_result is not None:

        cluster_column = (
            f"Cluster_k"
            f"{cluster_result['selected_k']}"
        )

        clusters = (
            cluster_result[
                "clusters"
            ]
            .rename(
                columns={
                    "Cluster":
                        cluster_column
                }
            )
        )

        output = (
            output
            .merge(
                clusters,
                on="GSA_ID",
                how="left",
            )
        )

    return output



def get_mastersizer_pca_export_df(
        gsa_df,
        mmes_df,
        mmes_rs_df,
        selected_samples,
        panel,
):
    """
    Export Mastersizer-only PCA scores and current-k cluster
    assignments.

    The raw native PSD/FR exports remain handled by their
    existing dedicated exporters.
    """

    input_mode = panel.get(
        "mastersizer_pca_input",
        "frequency",
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

        return pd.DataFrame(
            columns=[
                "GSA_ID",
            ]
        )

    analysis_df = (
        prepared_input[
            "dataframe"
        ]
    )

    variables = (
        prepared_input[
            "variables"
        ]
    )

    samples = (
        prepared_input[
            "samples"
        ]
    )

    standardize = (
        False
        if input_mode
        == "frequency"
        else panel.get(
            "analysis_standardize",
            True,
        )
    )

    pca_result = calculate_pca(
        analysis_df,
        samples,
        variables,
        standardize=
            standardize,
    )

    if pca_result is None:

        return pd.DataFrame(
            columns=[
                "GSA_ID",
            ]
        )

    cluster_result = (
        calculate_hierarchical(
            analysis_df,
            samples,
            variables,
            standardize=
                standardize,
            linkage_method=
                panel.get(
                    "cluster_linkage",
                    "ward",
                ),
            distance_metric=
                panel.get(
                    "cluster_metric",
                    "euclidean",
                ),
            cluster_k=
                panel.get(
                    "cluster_k",
                    4,
                ),
            silhouette_k_min=2,
            silhouette_k_max=10,
        )
    )

    output = (
        pca_result[
            "scores"
        ]
        .copy()
    )

    output.insert(
        1,
        "Mastersizer_PCA_Input",
        (
            "PSD Undersize"
            if input_mode
            == "psd"
            else "Frequency"
        ),
    )

    output.insert(
        2,
        "Mastersizer_PCA_Bins",
        len(
            variables
        ),
    )

    output.insert(
        3,
        "Mastersizer_PCA_Min_um",
        float(
            np.min(
                prepared_input[
                    "retained_x"
                ]
            )
        ),
    )

    output.insert(
        4,
        "Mastersizer_PCA_Max_um",
        float(
            np.max(
                prepared_input[
                    "retained_x"
                ]
            )
        ),
    )

    if cluster_result is not None:

        cluster_column = (
            f"Cluster_k"
            f"{cluster_result['selected_k']}"
        )

        clusters = (
            cluster_result[
                "clusters"
            ]
            .rename(
                columns={
                    "Cluster":
                        cluster_column
                }
            )
        )

        output = (
            output
            .merge(
                clusters,
                on="GSA_ID",
                how="left",
            )
        )

    return output


def get_hierarchical_export_df(
        gsa_df,
        selected_samples,
        panel,
):
    result = calculate_hierarchical(
        gsa_df,
        selected_samples,
        panel.get(
            "analysis_variables",
            [],
        ),
        standardize=panel.get(
            "analysis_standardize",
            True,
        ),
        linkage_method=panel.get(
            "cluster_linkage",
            "ward",
        ),
        distance_metric=panel.get(
            "cluster_metric",
            "euclidean",
        ),
    )

    if result is None:
        return pd.DataFrame(
            columns=[
                "GSA_ID",
                "Cluster_Order",
            ]
        )

    ordered_samples = (
        result[
            "dendrogram"
        ][
            "ivl"
        ]
    )

    order_lookup = {
        str(sample): i + 1
        for i, sample
        in enumerate(
            ordered_samples
        )
    }

    output = (
        result[
            "dataframe"
        ]
        .copy()
    )

    output[
        "Cluster_Order"
    ] = (
        output[
            "GSA_ID"
        ]
        .astype(str)
        .map(
            order_lookup
        )
    )

    output = (
        output
        .sort_values(
            "Cluster_Order"
        )
        .reset_index(
            drop=True
        )
    )

    return output


def add_export_metadata(
        df,
        gsa_df,
        panel,
):
    """
    Adds:

    - BoreholeID
    - Group

    to all export dataframes.
    """

    if df.empty:
        return df

    #
    # BoreholeID
    #

    borehole_lookup = (
        gsa_df[
            [
                "GSA_ID",
                "BoreholeID",
            ]
        ]
        .drop_duplicates(
            "GSA_ID"
        )
        .set_index(
            "GSA_ID"
        )[
            "BoreholeID"
        ]
        .to_dict()
    )

    df["BoreholeID"] = (
        df["GSA_ID"]
        .astype(str)
        .map(borehole_lookup)
    )

    #
    # Group
    #

    group_lookup = {}

    #
    # Custom Groups
    #

    if has_custom_groups(panel):

        (
            sample_to_groups,
            _,
        ) = build_custom_groups(
            panel.get(
                "custom_groups",
                [],
            ),
            gsa_df,
        )

        for (
                sample,
                groups,
        ) in sample_to_groups.items():
            group_lookup[
                str(sample)
            ] = "; ".join(
                sorted(groups)
            )

    #
    # Top-level grouping
    #

    elif (
            panel.get("group_by")
            and panel.get("group_by") != "None"
    ):

        field = panel["group_by"]

        temp = gsa_df[
            [
                "GSA_ID",
                field,
            ]
        ].copy()

        temp[field] = (
            temp[field]
            .fillna(
                "<null>"
            )
            .astype(str)
        )

        group_lookup = (
            temp
            .set_index(
                "GSA_ID"
            )[
                field
            ]
            .to_dict()
        )

    #
    # No grouping
    #

    else:

        group_lookup = {
            str(sample):
                "All Samples"
            for sample
            in df["GSA_ID"]
        }

    df["Group"] = (
        df["GSA_ID"]
        .astype(str)
        .map(group_lookup)
        .fillna(
            "All Samples"
        )
    )

    #
    # Move metadata columns to front
    #

    first_cols = [
        c
        for c in [
            "GSA_ID",
            "BoreholeID",
            "Group",
        ]
        if c in df.columns
    ]

    other_cols = [
        c
        for c in df.columns
        if c not in first_cols
    ]

    return df[
        first_cols
        + other_cols
        ]

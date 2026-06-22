def get_psd_export_df(
        mmes_df,
        selected_samples,
):
    psd_cols = sorted(
        [
            c for c in mmes_df.columns
            if c.startswith("PSD_")
        ],
        key=lambda x: float(
            x.replace("PSD_", "").replace("_", ".")
        )
    )

    export_cols = [
                      "Sample_Name_Final",
                  ] + psd_cols

    subset = mmes_df[
        mmes_df["Sample_Name_Final"]
        .astype(str)
        .isin(selected_samples)
    ][export_cols].copy()

    subset = subset.rename(
        columns={
            "Sample_Name_Final": "GSA_ID"
        }
    )

    return subset


def get_frequency_export_df(
        mmes_df,
        selected_samples,
):
    fr_cols = sorted(
        [
            c for c in mmes_df.columns
            if c.startswith("FR_")
        ],
        key=lambda x: float(
            x.replace("FR_", "").replace("_", ".")
        )
    )

    export_cols = [
                      "Sample_Name_Final",
                  ] + fr_cols

    subset = mmes_df[
        mmes_df["Sample_Name_Final"]
        .astype(str)
        .isin(selected_samples)
    ][export_cols].copy()

    subset = subset.rename(
        columns={
            "Sample_Name_Final": "GSA_ID",
        }
    )

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
from logic.text_normalization import (
    normalize_identifier,
)


def get_sample_mmes_row(
        sample,
        mmes_df,
        mmes_rs_df,
):
    """
    Find a Mastersizer row without treating case or extra
    whitespace in the sample ID as meaningful.

    PRIMARY retains precedence if the normalized ID exists in
    both datasets.
    """

    sample = (
        normalize_identifier(
            sample
        )
    )

    # Normal app data are already normalized once by the data
    # loaders, so use the fast direct comparison first.
    row = mmes_df[
        mmes_df[
            "Sample_Name_Final"
        ]
        .astype(str)
        == sample
    ]

    # Defensive fallback for a dataframe supplied from somewhere
    # outside the normal loader path.
    if not len(row):

        primary_ids = (
            mmes_df[
                "Sample_Name_Final"
            ]
            .map(
                normalize_identifier
            )
        )

        row = mmes_df[
            primary_ids
            == sample
        ]

    if len(row):
        return (
            row.iloc[
                0
            ],
            "PRIMARY",
        )

    row = mmes_rs_df[
        mmes_rs_df[
            "Sample_Name_Final"
        ]
        .astype(str)
        == sample
    ]

    if not len(row):

        rs_ids = (
            mmes_rs_df[
                "Sample_Name_Final"
            ]
            .map(
                normalize_identifier
            )
        )

        row = mmes_rs_df[
            rs_ids
            == sample
        ]

    if len(row):
        return (
            row.iloc[
                0
            ],
            "RS",
        )

    return (
        None,
        None,
    )


def get_psd_columns(
        source,
        mmes_df,
        mmes_rs_df,
):
    df = (
        mmes_df
        if source == "PRIMARY"
        else mmes_rs_df
    )

    cols = sorted(
        [
            c
            for c in df.columns
            if c.startswith("PSD_")
        ],
        key=lambda x:
        float(
            x.replace(
                "PSD_",
                ""
            ).replace(
                "_",
                "."
            )
        )
    )

    x_vals = [
        float(
            c.replace(
                "PSD_",
                ""
            ).replace(
                "_",
                "."
            )
        )
        for c in cols
    ]

    return (
        cols,
        x_vals,
    )


def get_fr_columns(
        source,
        mmes_df,
        mmes_rs_df,
):
    df = (
        mmes_df
        if source == "PRIMARY"
        else mmes_rs_df
    )

    cols = sorted(
        [
            c
            for c in df.columns
            if c.startswith("FR_")
        ],
        key=lambda x:
        float(
            x.replace(
                "FR_",
                ""
            ).replace(
                "_",
                "."
            )
        )
    )

    x_vals = [
        float(
            c.replace(
                "FR_",
                ""
            ).replace(
                "_",
                "."
            )
        )
        for c in cols
    ]

    return (
        cols,
        x_vals,
    )

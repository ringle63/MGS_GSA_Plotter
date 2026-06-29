def get_sample_mmes_row(
        sample,
        mmes_df,
        mmes_rs_df,
):
    sample = str(sample)

    row = mmes_df[
        mmes_df["Sample_Name_Final"]
        .astype(str)
        == sample
        ]

    if len(row):
        return (
            row.iloc[0],
            "PRIMARY",
        )

    row = mmes_rs_df[
        mmes_rs_df["Sample_Name_Final"]
        .astype(str)
        == sample
        ]

    if len(row):
        return (
            row.iloc[0],
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

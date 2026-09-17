import pandas as pd

from logic.filters import (
    FILTER_FIELDS,
)

from logic.text_normalization import (
    normalize_identifier,
    normalize_identifier_series,
    standardize_category_series,
)


# Fields treated as identifiers instead of display categories.
# These are normalized to upper case + collapsed whitespace.
GSA_IDENTIFIER_FIELDS = {
    "GSA_ID",
    "BoreholeID",
}


def _standardize_gsa_text(
        df,
):
    """
    Normalize the text fields used for selection, filtering,
    grouping, sorting, legends, heatmaps, and reports.

    Categorical fields are title-cased after whitespace
    normalization. Identifier fields are upper-cased.

    This happens once at data load so the rest of the app sees
    one canonical category instead of separate values such as
    "Sandy Loam", "Sandy loam", and "SANDY   LOAM".
    """

    df = df.copy()

    for field in GSA_IDENTIFIER_FIELDS:

        if field in df.columns:

            df[
                field
            ] = (
                normalize_identifier_series(
                    df[
                        field
                    ]
                )
            )

    category_fields = [
        field
        for field
        in FILTER_FIELDS
        if (
            field
            not in GSA_IDENTIFIER_FIELDS
            and field
            in df.columns
        )
    ]

    for field in category_fields:

        df[
            field
        ] = (
            standardize_category_series(
                df[
                    field
                ]
            )
        )

    return df


def _standardize_mmes_text(
        df,
):
    """
    Normalize the MMES sample identifier used to match PRIMARY
    and RS records to GSA_ID.
    """

    df = df.copy()

    if (
            "Sample_Name_Final"
            in df.columns
    ):

        df[
            "Sample_Name_Final"
        ] = (
            normalize_identifier_series(
                df[
                    "Sample_Name_Final"
                ]
            )
        )

    return df


def load_gsa_lab(
        path="data/GSA_Lab_070726.xlsx",
):
    df = pd.read_excel(
        path
    )

    return _standardize_gsa_text(
        df
    )


def load_mmes(
        path="data/GSA_MMES_062726.xlsx",
):
    df = pd.read_excel(
        path
    )

    return _standardize_mmes_text(
        df
    )


def load_mmes_rs(
        path="data/RS_GSA_MMES_062926.xlsx",
):
    df = pd.read_excel(
        path
    )

    return _standardize_mmes_text(
        df
    )


def get_psd_columns(
        mmes_df,
):
    return sorted(
        [
            c
            for c
            in mmes_df.columns
            if c.startswith(
                "PSD_"
            )
        ],
        key=lambda x:
        float(
            x.replace(
                "PSD_",
                "",
            ).replace(
                "_",
                ".",
            )
        ),
    )


def get_fr_columns(
        mmes_df,
):
    return sorted(
        [
            c
            for c
            in mmes_df.columns
            if c.startswith(
                "FR_"
            )
        ],
        key=lambda x:
        float(
            x.replace(
                "FR_",
                "",
            ).replace(
                "_",
                ".",
            )
        ),
    )


def build_master_lookup(
        gsa_df,
        mmes_df,
):
    """
    Returns a dictionary keyed by normalized GSA_ID containing
    metadata about MMES availability.
    """

    mmes_ids = {
        normalize_identifier(
            sample
        )
        for sample
        in mmes_df[
            "Sample_Name_Final"
        ]
        .dropna()
        .tolist()
    }

    lookup = {}

    for _, row in (
            gsa_df.iterrows()
    ):

        gsa_id = (
            normalize_identifier(
                row[
                    "GSA_ID"
                ]
            )
        )

        lookup[
            gsa_id
        ] = {
            "has_mmes":
                gsa_id
                in mmes_ids,

            "analysis_method":
                row.get(
                    "analysis_method",
                    row.get(
                        "Analysis_Method",
                        None,
                    ),
                ),
        }

    return lookup

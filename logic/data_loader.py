import pandas as pd

from logic.filters import (
    FILTER_FIELDS,
)

from logic.text_normalization import (
    collapse_whitespace,
    normalize_text_key,
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

# Geological codes, acronyms, and reviewer prose must not be title-cased.
# They still use normalized keys to unify case/whitespace variants.
GSA_PRESERVE_CASE_FIELDS = {
    "age",
    "lobe",
    "Surface_Map_Unit",
    "Reviewer_Notes",
}


def _standardize_preserving_case(series):
    """Collapse whitespace and unify equivalent text without altering codes."""
    display_values = series.map(collapse_whitespace)
    canonical_values = {}

    def canonicalize(value):
        key = normalize_text_key(value)
        if key is None:
            return value
        return canonical_values.setdefault(key, value)

    return display_values.map(canonicalize)


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

        if field in GSA_PRESERVE_CASE_FIELDS:
            df[field] = _standardize_preserving_case(df[field])
        else:
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
        path="data/GSA_Lab_110526.xlsx",
):
    df = pd.read_excel(
        path
    )

    return _standardize_gsa_text(
        df
    )


def load_mmes(
        path="data/GSA_MMES_091826.xlsx",
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



def load_data_bundle(
        gsa_path="data/GSA_Lab_110526.xlsx",
        primary_path="data/GSA_MMES_091826.xlsx",
        rs_path="data/RS_GSA_MMES_062926.xlsx",
        expected_columns=None,
):
    """Read and validate all three source workbooks before returning any data.

    An exception leaves the caller's existing in-memory data untouched.
    Paths match the existing individual loaders and are reread on each call.
    """
    frames = {}
    sources = (
        ("GSA", gsa_path, load_gsa_lab),
        ("PRIMARY MMES", primary_path, load_mmes),
        ("RS MMES", rs_path, load_mmes_rs),
    )

    for label, path, loader in sources:
        try:
            frame = loader(path)
        except Exception as exc:
            raise RuntimeError(
                f"Could not read {label} ({path}): {exc}"
            ) from exc

        required = (
            {"GSA_ID", "analysis_method", "BoreholeID", "formation"}
            if label == "GSA"
            else {"Sample_Name_Final"}
        )
        missing = required - set(frame.columns)
        if expected_columns is not None:
            missing |= (
                set(expected_columns.get(label, ())) - set(frame.columns)
            )
        if missing:
            raise ValueError(
                f"{label} ({path}) is missing columns: "
                + ", ".join(sorted(missing))
            )
        if frame.empty:
            raise ValueError(f"{label} ({path}) contains no data rows")
        frames[label] = frame

    gsa = frames["GSA"]
    primary = frames["PRIMARY MMES"]
    rs = frames["RS MMES"]
    primary_ids = set(primary["Sample_Name_Final"].dropna().astype(str))
    rs_ids = set(rs["Sample_Name_Final"].dropna().astype(str))
    mmes_ids = primary_ids | rs_ids
    matched_count = int(gsa["GSA_ID"].dropna().astype(str).isin(mmes_ids).sum())

    return {
        "gsa_df": gsa,
        "mmes_df": primary,
        "mmes_rs_df": rs,
        "mmes_ids": mmes_ids,
        "matched_count": matched_count,
    }


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

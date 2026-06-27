import pandas as pd


def normalize_text_columns(df):
    """
    Normalize all text columns:
    - trim whitespace
    - collapse repeated spaces
    - convert to lowercase
    - convert empty strings to NA
    """

    df = df.copy()

    text_cols = df.select_dtypes(
        include=["object", "string"]
    ).columns

    for col in text_cols:
        df[col] = (
            df[col]
            .astype("string")
            .str.strip()
            .str.replace(
                r"\s+",
                " ",
                regex=True,
            )
            .str.upper()
        )

        df[col] = df[col].replace(
            {
                "": pd.NA,
                "nan": pd.NA,
                "none": pd.NA,
            }
        )

    return df


def load_gsa_lab(path="data/GSA_Lab_061626.xlsx"):
    df = pd.read_excel(path)
    return normalize_text_columns(df)


def load_mmes(path="data/GSA_MastersizerMMES_Data061626.xlsx"):
    df = pd.read_excel(path)
    return normalize_text_columns(df)


def get_psd_columns(mmes_df):
    return sorted(
        [c for c in mmes_df.columns if c.startswith("PSD_")],
        key=lambda x: float(x.replace("PSD_", "").replace("_", "."))
    )


def get_fr_columns(mmes_df):
    return sorted(
        [c for c in mmes_df.columns if c.startswith("FR_")],
        key=lambda x: float(x.replace("FR_", "").replace("_", "."))
    )


def build_master_lookup(gsa_df, mmes_df):
    """
    Returns a dictionary keyed by GSA_ID containing
    metadata about MMES availability.
    """

    mmes_ids = set(mmes_df["Sample_Name_Final"].astype(str))

    lookup = {}

    for _, row in gsa_df.iterrows():
        gsa_id = str(row["GSA_ID"])

        lookup[gsa_id] = {
            "has_mmes": gsa_id in mmes_ids,
            "analysis_method": row.get("Analysis_Method", None),
        }

    return lookup

import pandas as pd


def load_gsa_lab(path="data/GSA_Lab_062726.xlsx"):
    return pd.read_excel(path)


def load_mmes(path="data/GSA_MMES_062726.xlsx"):
    return pd.read_excel(path)

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
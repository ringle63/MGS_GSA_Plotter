from logic.filters import (
    apply_filters,
)

from logic.text_normalization import (
    normalize_identifier_list,
)


def apply_panel_filters(
        panel,
        gsa_df,
):
    filters = panel.get(
        "panel_filters",
        [],
    )

    if not filters:
        return gsa_df.iloc[0:0].copy()

    return apply_filters(
        gsa_df,
        filters,
    )


def get_panel_samples(
        panel,
        global_samples,
        gsa_df,
):
    if panel["use_global"]:
        return normalize_identifier_list(
            global_samples
        )

    filtered = apply_panel_filters(
        panel,
        gsa_df,
    )

    return (
        filtered["GSA_ID"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

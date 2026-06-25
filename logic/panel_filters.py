from logic.filters import (
    apply_filters,
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
    # Use global selection
    if panel["use_global"]:
        return global_samples or []

    filtered = apply_panel_filters(
        panel,
        gsa_df,
    )

    if panel["override_methods"]:
        filtered = filtered[
            filtered["analysis_method"]
            .astype(str)
            .isin(panel["override_methods"])
        ]

    if panel["override_formations"]:
        filtered = filtered[
            filtered["formation"]
            .astype(str)
            .isin(panel["override_formations"])
        ]

    if panel["override_boreholes"]:
        filtered = filtered[
            filtered["BoreholeID"]
            .astype(str)
            .isin(panel["override_boreholes"])
        ]

    if panel["override_samples"]:
        filtered = filtered[
            filtered["GSA_ID"]
            .astype(str)
            .isin(panel["override_samples"])
        ]

    return (
        filtered["GSA_ID"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

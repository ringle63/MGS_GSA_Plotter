from logic.filters import apply_filters


def build_custom_groups(
        groups,
        gsa_df,
):
    """
    Returns

    sample_to_groups:
        sample -> list of groups

    sample_to_primary_group:
        sample -> first matching group
    """

    sample_to_groups = {}
    sample_to_primary_group = {}

    for group in groups:

        name = group.get(
            "name",
            "Unnamed Group",
        )

        filters = group.get(
            "filters",
            [],
        )

        if not filters:
            continue

        subset = apply_filters(
            gsa_df,
            filters,
        )

        samples = (
            subset["GSA_ID"]
            .dropna()
            .astype(str)
            .unique()
        )

        for sample in samples:

            sample_to_groups.setdefault(
                sample,
                [],
            ).append(name)

            if (
                    sample
                    not in sample_to_primary_group
            ):
                sample_to_primary_group[
                    sample
                ] = name

    return (
        sample_to_groups,
        sample_to_primary_group,
    )

def get_custom_group_names(
        panel,
):
    return [
        group["name"]
        for group in panel.get(
            "custom_groups",
            [],
        )
        if group.get("name")
    ]


def has_custom_groups(
        panel,
):
    return (
        panel.get(
            "use_custom_groups",
            False,
        )
        and
        len(
            panel.get(
                "custom_groups",
                [],
            )
        ) > 0
    )
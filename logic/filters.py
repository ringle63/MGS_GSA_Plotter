import pandas as pd

from logic.text_normalization import (
    normalize_text_key,
)

NULL_VALUE = "<null>"

FILTER_FIELDS = {
    "analysis_method": "Analysis Method",
    "formation": "Formation",
    "BoreholeID": "Borehole",
    "GSA_ID": "Sample ID",
    "class_usda": "USDA Class",
    "class_usc": "USC Class",
    "class_uw": "UW Class",
    "class_folk": "Folk Class",
    "prim_material": "Primary Material",
    "Origin": "Origin",
    "County": "County",
    "primary_color": "Primary Color",
}

GROUP_BY_FIELDS = FILTER_FIELDS.copy()

NUMERIC_FIELDS = {
    "depth_ft": "Depth (ft)",
    "sample_elevation": "Sample Elevation",

    "sandfrac_vf": "Sand Fraction - Very Fine",
    "sandfrac_f": "Sand Fraction - Fine",
    "sandfrac_m": "Sand Fraction - Medium",
    "sandfrac_c": "Sand Fraction - Coarse",
    "sandfrac_vc": "Sand Fraction - Very Coarse",
    "sandfrac_total": "Sand Fraction - Total",

    "Clay0_2": "Clay0_2",
    "Clay0_4": "Clay0_4",
    "Clay0_8": "Clay0_8",

    "Silt2_625": "Silt2_625",
    "Silt_4_625": "Silt_4_625",
    "Silt_8_625": "Silt_8_625",
    "Silt_8_50": "Silt_8_50",

    "Sand625_2000": "Sand625_2000",
    "Sand_50_2000": "Sand_50_2000",

    "VFSand_50_125": "VFSand_50_125",

    "ClayG_0_2": "ClayG_0_2",
    "ClayG_0_4": "ClayG_0_4",
    "ClayG_0_8": "ClayG_0_8",

    "SiltG_2_625": "SiltG_2_625",
    "SiltG_4_625": "SiltG_4_625",
    "SiltG_8_625": "SiltG_8_625",

    "SandG_625_2000": "SandG_625_2000",
    "GravelG_2000_3500": "GravelG_2000_3500",

    "laser_obscuration": "Laser Obscuration",

    "Fines_0_63": "Fines_0_63",
    "FinesG_0_63": "FinesG_0_63",

    "sandfracG_vf": "Sand Fraction w/Grav - Very Fine",
    "sandfracG_f": "Sand Fraction w/Grav - Fine",
    "sandfracG_m": "Sand Fraction w/Grav - Medium",
    "sandfracG_c": "Sand Fraction w/Grav - Coarse",
    "sandfracG_vc": "Sand Fraction w/Grav - Very Coarse",
    "sandfracG_total": "Sand Fraction w/Grav - Total",
}


def _normalized_text_series(
        series,
):
    """
    Case/whitespace-insensitive comparison representation.
    """

    return series.map(
        normalize_text_key
    )


def _normalized_filter_values(
        value,
):
    """
    Normalize one or many categorical filter values.
    """

    values = (
        value
        if isinstance(
            value,
            list,
        )
        else [
            value
        ]
    )

    return [
        normalize_text_key(
            item
        )
        for item
        in values
        if item
        != NULL_VALUE
    ]


def apply_filters(
        df,
        filters,
):
    if not filters:
        return df.copy()

    combined_mask = None

    for clause in filters:

        field = clause.get(
            "field"
        )

        operator = clause.get(
            "operator"
        )

        value = clause.get(
            "value"
        )

        logic = clause.get(
            "logic",
            "AND",
        )

        if (
                not field
                or field
                not in df.columns
                or value
                in [
                    None,
                    [],
                    "",
                ]
        ):
            continue

        is_numeric = (
            field
            in NUMERIC_FIELDS
        )

        if is_numeric:

            series = pd.to_numeric(
                df[
                    field
                ],
                errors="coerce",
            )

            normalized_series = None

        else:

            series = df[
                field
            ]

            normalized_series = (
                _normalized_text_series(
                    series
                )
            )

        if operator == "IN":

            raw_values = (
                value
                if isinstance(
                    value,
                    list,
                )
                else [
                    value
                ]
            )

            contains_null = (
                NULL_VALUE
                in raw_values
            )

            values = (
                _normalized_filter_values(
                    raw_values
                )
            )

            mask = (
                normalized_series
                .isin(
                    values
                )
            )

            if contains_null:

                mask |= (
                    series.isna()
                )

        elif operator == "NOT IN":

            raw_values = (
                value
                if isinstance(
                    value,
                    list,
                )
                else [
                    value
                ]
            )

            contains_null = (
                NULL_VALUE
                in raw_values
            )

            values = (
                _normalized_filter_values(
                    raw_values
                )
            )

            mask = ~(
                normalized_series
                .isin(
                    values
                )
            )

            if contains_null:

                mask &= ~(
                    series.isna()
                )

        elif operator == "CONTAINS":

            search = (
                normalize_text_key(
                    value
                )
                or ""
            )

            mask = (
                normalized_series
                .fillna(
                    ""
                )
                .str.contains(
                    search,
                    case=True,
                    regex=False,
                    na=False,
                )
            )

        elif operator == "=":

            if is_numeric:

                mask = (
                    series
                    == float(
                        value
                    )
                )

            else:

                mask = (
                    normalized_series
                    == normalize_text_key(
                        value
                    )
                )

        elif operator == "!=":

            if is_numeric:

                mask = (
                    series
                    != float(
                        value
                    )
                )

            else:

                mask = (
                    normalized_series
                    != normalize_text_key(
                        value
                    )
                )

        elif operator == "<":

            mask = (
                series
                < float(
                    value
                )
            )

        elif operator == "<=":

            mask = (
                series
                <= float(
                    value
                )
            )

        elif operator == ">":

            mask = (
                series
                > float(
                    value
                )
            )

        elif operator == ">=":

            mask = (
                series
                >= float(
                    value
                )
            )

        elif operator == "BETWEEN":

            minimum = float(
                value[
                    0
                ]
            )

            maximum = float(
                value[
                    1
                ]
            )

            mask = (
                (
                    series
                    >= minimum
                )
                &
                (
                    series
                    <= maximum
                )
            )

        else:

            continue

        if combined_mask is None:

            combined_mask = mask

        elif logic == "OR":

            combined_mask |= mask

        else:

            combined_mask &= mask

    if combined_mask is None:

        return df.copy()

    return df.loc[
        combined_mask
    ]

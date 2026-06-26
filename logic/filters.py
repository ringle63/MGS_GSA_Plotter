import pandas as pd

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

    "Sand625_2000": "Sand625_2000",

    "ClayG_0_2": "ClayG_0_2",
    "ClayG_0_4": "ClayG_0_4",

    "SiltG_2_625": "SiltG_2_625",
    "SiltG_4_625": "SiltG_4_625",

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


def apply_filters(
        df,
        filters,
):
    if not filters:
        return df.copy()

    combined_mask = None

    for clause in filters:

        field = clause.get("field")
        operator = clause.get("operator")
        value = clause.get("value")
        logic = clause.get(
            "logic",
            "AND",
        )

        if (
                not field
                or value in [
            None,
            [],
            "",
        ]
        ):
            continue

        if field in NUMERIC_FIELDS:

            series = pd.to_numeric(
                df[field],
                errors="coerce",
            )

        else:

            series = df[field]

        if operator == "IN":

            contains_null = (
                NULL_VALUE in value
                if isinstance(value, list)
                else False
            )

            values = [
                v
                for v in value
                if v != NULL_VALUE
            ]

            mask = series.astype(str).isin(values)

            if contains_null:
                mask |= series.isna()

        elif operator == "NOT IN":

            contains_null = (
                NULL_VALUE in value
                if isinstance(value, list)
                else False
            )

            values = [
                v
                for v in value
                if v != NULL_VALUE
            ]

            mask = ~series.astype(str).isin(values)

            if contains_null:
                mask &= ~series.isna()

        elif operator == "CONTAINS":

            search = str(value).lower()

            mask = (
                series
                .astype(str)
                .str.lower()
                .str.contains(
                    search,
                    na=False,
                )
            )
        elif operator == "=":

            if field in NUMERIC_FIELDS:
                mask = (
                        series
                        == float(value)
                )
            else:
                mask = (
                        series.astype(str)
                        == str(value)
                )

        elif operator == "!=":

            if field in NUMERIC_FIELDS:
                mask = (
                        series
                        != float(value)
                )
            else:
                mask = (
                        series.astype(str)
                        != str(value)
                )

        elif operator == "<":
            mask = (
                    series
                    < float(value)
            )

        elif operator == "<=":
            mask = (
                    series
                    <= float(value)
            )

        elif operator == ">":
            mask = (
                    series
                    > float(value)
            )

        elif operator == ">=":
            mask = (
                    series
                    >= float(value)
            )

        elif operator == "BETWEEN":

            minimum = float(
                value[0]
            )

            maximum = float(
                value[1]
            )

            mask = (
                    (series >= minimum)
                    &
                    (series <= maximum)
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

def get_grain_fractions(
        sample_row,
        mmes_row,
        ternary_settings,
):
    """
    Returns:
    {
        "clay": ...,
        "silt": ...,
        "sand": ...,
        "method": ...,
        "break": ...
    }
    """

    method = sample_row["analysis_method"]

    if method == "Mastersizer":

        clay_break = ternary_settings["Mastersizer"]

        sand_break = ternary_settings[
            "MastersizerSand"
        ]

    elif method == "Pipette":

        clay_break = ternary_settings["Pipette"]

    elif method == "Kehew":

        clay_break = 4

    elif method == "Dry Sieve":

        return {
            "clay": 0,
            "silt": sample_row["Fines_0_63"],
            "sand": sample_row["Sand625_2000"],
            "method": method,
            "break": "Fixed",
        }

    else:

        return None

    clay_field = f"Clay0_{clay_break}"

    if clay_break == 2:
        silt_field = "Silt2_625"
    else:
        silt_field = f"Silt_{clay_break}_625"

    # Mastersizer gets special handling because the
    # sand/silt break can come from MMES data.

    if method == "Mastersizer":

        if mmes_row is None:
            return None

        clay = sample_row[clay_field]

        if sand_break == 62.5:

            silt = sample_row[silt_field]
            sand = sample_row["Sand625_2000"]

        else:  # 50 µm break

            sand = (
                    mmes_row["Result_In_Range___50_2000__μm"]
                    +
                    mmes_row["Result_In_Range___2000_3500__μm"]
            )

            if clay_break == 2:

                silt = mmes_row[
                    "Result_In_Range___2_50__μm"
                ]

            elif clay_break == 8:

                silt = mmes_row[
                    "Result_In_Range___8_50__μm"
                ]

            else:  # 4 µm

                silt = (
                        100
                        - sand
                        - mmes_row[
                            "Result_In_Range___0_4__μm"
                        ]
                )

        return {
            "clay": clay,
            "silt": silt,
            "sand": sand,
            "method": method,
            "break": f"{clay_break}/{sand_break}",
        }

    # Everyone else uses the existing logic

    return {
        "clay": sample_row[clay_field],
        "silt": sample_row[silt_field],
        "sand": sample_row["Sand625_2000"],
        "method": method,
        "break": clay_break,
    }


def get_grain_log_classes(
        sample_row,
        mmes_row,
        settings,
):
    method = sample_row["analysis_method"]

    if method == "Mastersizer":

        clay_break = settings["Mastersizer"]
        sand_break = settings["MastersizerSand"]

        clay_field = f"Clay0_{clay_break}"

        if clay_break == 2:
            silt_field = "Silt2_625"
        else:
            silt_field = f"Silt_{clay_break}_625"

        if sand_break == 62.5:

            vf_sand = sample_row["sandfrac_vf"]
            silt = sample_row[silt_field]

        else:

            if mmes_row is None:
                return None

            vf_sand = mmes_row[
                "Result_In_Range___50_125__μm"
            ]

            if clay_break == 2:

                silt = mmes_row[
                    "Result_In_Range___2_50__μm"
                ]

            elif clay_break == 8:

                silt = mmes_row[
                    "Result_In_Range___8_50__μm"
                ]

            else:

                silt = (
                        100
                        - mmes_row[
                            "Result_In_Range___50_2000__μm"
                        ]
                        - mmes_row[
                            "Result_In_Range___2000_3500__μm"
                        ]
                        - mmes_row[
                            "Result_In_Range___0_4__μm"
                        ]
                )

        grain = {
            "Gravel": 0,
            "Very Coarse Sand": sample_row["sandfrac_vc"],
            "Coarse Sand": sample_row["sandfrac_c"],
            "Medium Sand": sample_row["sandfrac_m"],
            "Fine Sand": sample_row["sandfrac_f"],
            "Very Fine Sand": vf_sand,
            "Silt": silt,
            "Clay": sample_row[clay_field],
            "method": method,
            "break": f"{clay_break}/{sand_break}",
        }

        for key, value in grain.items():

            if key in ["method", "break"]:
                continue

            if value is None or str(value) == "nan":
                grain[key] = 0

        return grain
    elif method == "Pipette":

        clay_break = settings["Pipette"]

        clay_field = f"ClayG_0_{clay_break}"
        silt_field = f"SiltG_{clay_break}_625"

    elif method == "Kehew":

        clay_field = "ClayG_0_4"
        silt_field = "SiltG_4_625"

    elif method == "Dry Sieve":

        grain = {
            "Gravel": sample_row["GravelG_2000_3500"],
            "Very Coarse Sand": sample_row["sandfracG_vc"],
            "Coarse Sand": sample_row["sandfracG_c"],
            "Medium Sand": sample_row["sandfracG_m"],
            "Fine Sand": sample_row["sandfracG_f"],
            "Very Fine Sand": sample_row["sandfracG_vf"],
            "Silt": sample_row["FinesG_0_63"],
            "Clay": 0,
            "method": method,
            "break": "Fixed",
        }

        for key, value in grain.items():

            if key in ["method", "break"]:
                continue

            if value is None or str(value) == "nan":
                grain[key] = 0

        return grain

    else:
        return None

    grain = {
        "Gravel": sample_row["GravelG_2000_3500"],
        "Very Coarse Sand": sample_row["sandfracG_vc"],
        "Coarse Sand": sample_row["sandfracG_c"],
        "Medium Sand": sample_row["sandfracG_m"],
        "Fine Sand": sample_row["sandfracG_f"],
        "Very Fine Sand": sample_row["sandfracG_vf"],
        "Silt": sample_row[silt_field],
        "Clay": sample_row[clay_field],
        "method": method,
        "break": (
            clay_break if method == "Pipette"
            else 4
        ),
    }

    for key, value in grain.items():

        if key in ["method", "break"]:
            continue

        if value is None or str(value) == "nan":
            grain[key] = 0

    return grain

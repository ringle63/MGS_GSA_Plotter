def get_grain_fractions(
    sample_row,
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

    return {
        "clay": sample_row[clay_field],
        "silt": sample_row[silt_field],
        "sand": sample_row["Sand625_2000"],
        "method": method,
        "break": clay_break,
    }

def get_grain_log_classes(
    sample_row,
    settings,
):

    method = sample_row["analysis_method"]

    if method == "Mastersizer":

        clay_break = settings["Mastersizer"]

        clay_field = f"Clay0_{clay_break}"

        if clay_break == 2:
            silt_field = "Silt2_625"
        else:
            silt_field = f"Silt_{clay_break}_625"

        return {
            "Gravel": 0,
            "Very Coarse Sand": sample_row["sandfrac_vc"],
            "Coarse Sand": sample_row["sandfrac_c"],
            "Medium Sand": sample_row["sandfrac_m"],
            "Fine Sand": sample_row["sandfrac_f"],
            "Very Fine Sand": sample_row["sandfrac_vf"],
            "Silt": sample_row[silt_field],
            "Clay": sample_row[clay_field],
            "method": method,
            "break": clay_break,
        }

    elif method == "Pipette":

        clay_break = settings["Pipette"]

        clay_field = f"ClayG_0_{clay_break}"
        silt_field = f"SiltG_{clay_break}_625"

    elif method == "Kehew":

        clay_field = "ClayG_0_4"
        silt_field = "SiltG_4_625"

    elif method == "Dry Sieve":

        return {
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

    else:
        return None

    return {
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
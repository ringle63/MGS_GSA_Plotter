import re

import pandas as pd


_WHITESPACE_RE = re.compile(r"\s+")


def _is_missing(value):
    """
    Safe scalar missing-value check.
    """

    if value is None:
        return True

    try:
        return bool(
            pd.isna(value)
        )
    except (
            TypeError,
            ValueError,
        ):
        return False


def collapse_whitespace(
        value,
):
    """
    Strip leading/trailing whitespace and collapse any internal
    whitespace run to one ordinary space.

    Examples
    --------
    "  Sandy   Loam " -> "Sandy Loam"
    "Fine\tSand"      -> "Fine Sand"
    """

    if _is_missing(
            value
    ):
        return value

    text = str(
        value
    ).strip()

    return _WHITESPACE_RE.sub(
        " ",
        text,
    )


def normalize_text_key(
        value,
):
    """
    Comparison key for categorical text.

    Case and extra whitespace are ignored. The returned key is
    intended for equality, IN/NOT IN, contains matching,
    deduplication, and category recognition -- not display.
    """

    if _is_missing(
            value
    ):
        return None

    text = collapse_whitespace(
        value
    )

    if text == "":
        return ""

    return text.casefold()


def standardize_category_text(
        value,
):
    """
    Standard display value for categorical fields.

    Categories are whitespace-normalized and title-cased so
    values such as:
        "Sandy Loam"
        "sandy loam"
        "SANDY   LOAM"
    all become:
        "Sandy Loam"
    """

    if _is_missing(
            value
    ):
        return value

    text = collapse_whitespace(
        value
    )

    if text == "":
        return ""

    return text.title()


def normalize_identifier(
        value,
):
    """
    Normalize an identifier for matching/display.

    IDs are whitespace-normalized and upper-cased rather than
    title-cased.

    Examples
    --------
    " mon-26-01 " -> "MON-26-01"
    "ott-21-01-1" -> "OTT-21-01-1"
    """

    if _is_missing(
            value
    ):
        return value

    text = collapse_whitespace(
        value
    )

    if text == "":
        return ""

    return text.upper()


def normalize_identifier_list(
        values,
):
    """
    Normalize a list of IDs while preserving order and removing
    duplicates created only by case/spacing differences.
    """

    output = []
    seen = set()

    for value in (
            values
            or []
    ):

        normalized = (
            normalize_identifier(
                value
            )
        )

        if _is_missing(
                normalized
        ):
            continue

        key = normalize_text_key(
            normalized
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        output.append(
            normalized
        )

    return output


def standardize_category_series(
        series,
):
    """
    Apply display standardization to a pandas Series.
    """

    return series.map(
        standardize_category_text
    )


def normalize_identifier_series(
        series,
):
    """
    Apply identifier normalization to a pandas Series.
    """

    return series.map(
        normalize_identifier
    )

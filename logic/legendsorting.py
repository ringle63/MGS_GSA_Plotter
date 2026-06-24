import re


def gsa_sort_key(gsa_id):
    """
    Natural sort for GSA IDs.

    Examples
    --------
    OTT-21-01-1
    OTT-21-01-2
    OTT-21-01-2M
    OTT-21-01-10

    MUS-MON-12-1
    MUS-MON-12-2
    MUS-MON-12-10
    """

    if gsa_id is None:
        return ("", float("inf"), "")

    gsa_id = str(gsa_id).strip()

    if "-" not in gsa_id:
        return (gsa_id, float("inf"), "")

    prefix, suffix = gsa_id.rsplit("-", 1)

    match = re.match(
        r"(\d+)(.*)",
        suffix,
    )

    if match:

        number = int(
            match.group(1)
        )

        letters = (
            match.group(2)
            .strip()
            .upper()
        )

    else:

        number = float("inf")
        letters = suffix.upper()

    return (
        prefix.upper(),
        number,
        letters,
    )
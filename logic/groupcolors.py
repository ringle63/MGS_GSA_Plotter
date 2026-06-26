import plotly.colors as pc


BASE_COLORS = (
    pc.qualitative.Alphabet
    + pc.qualitative.Plotly
)


def build_group_colors(groups):
    """
    Build a color dictionary for the groups
    currently present in the figure.

    Parameters
    ----------
    groups : iterable

    Returns
    -------
    dict
    """

    groups = list(groups)

    return {
        group: BASE_COLORS[
            i % len(BASE_COLORS)
        ]
        for i, group in enumerate(groups)
    }


def darken_color(color, factor=0.25):
    """
    Darken a color.

    Parameters
    ----------
    color : str
        '#RRGGBB' or 'rgb(r,g,b)'

    factor : float
        0.0 = unchanged
        1.0 = black
    """

    if color.startswith("rgb"):

        values = (
            color.replace("rgb(", "")
            .replace(")", "")
            .split(",")
        )

        r, g, b = [
            int(v)
            for v in values
        ]

    else:

        color = color.lstrip("#")

        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)

    r = int(r * (1 - factor))
    g = int(g * (1 - factor))
    b = int(b * (1 - factor))

    return f"rgb({r},{g},{b})"
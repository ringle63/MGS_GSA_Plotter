import plotly.colors as pc


BASE_COLORS = pc.qualitative.Plotly


def get_group_color(group_name):
    colors = BASE_COLORS
    index = abs(hash(str(group_name))) % len(colors)
    return colors[index]


def lighten_color(hex_color, factor=0.55):
    hex_color = hex_color.lstrip("#")

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)

    return f"rgb({r},{g},{b})"
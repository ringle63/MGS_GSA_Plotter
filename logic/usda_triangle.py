import plotly.graph_objects as go

def line(
        label,
        a1,
        b1,
        c1,
        a2,
        b2,
        c2,
):
    return {
        "label": label,
        "a": [a1, a2],
        "b": [b1, b2],
        "c": [c1, c2],
    }


USDA_LINES = [

    line(
        "Clay=40",
        40, 0, 60,
        40, 45, 15,
    ),

    line(
        "Clay=27",
        27, 0, 73,
        27, 45, 28,
    ),

    line(
        "Clay=20",
        20, 80, 0,
        20, 52, 28,
    ),

    line(
        "Sand=45",
        55, 45, 0,
        27, 45, 28,
    ),

    line(
        "Sand=65",
        35, 65, 0,
        35, 45, 20,
    ),

    line(
        "Sand=20",
        40, 20, 40,
        27, 20, 53,
    ),

    line(
        "Silt=80",
        0, 20, 80,
        12, 8, 80,
    ),

    line(
        "Clay=12",
        12, 8, 80,
        12, 0, 88,
    ),

    line(
        "Silt=50",
        0, 50, 50,
        27, 23, 50,
    ),

    line(
        "Silt=40",
        40, 20, 40,
        60, 0, 40,
    ),

    line(
        "Silt+2Clay=30",
        0, 70, 30,
        15, 85, 0,
    ),

    line(
        "Silt+1.5Clay=15",
        0, 85, 15,
        10, 90, 0,
    ),

    line(
        "Silt=28",
        20, 52, 28,
        27, 45, 28,
    ),

    line(
        "Sand=52",
        20, 52, 28,
        7, 53, 40,
    ),

    line(
        "Clay=7",
        7, 53, 40,
        7, 43, 50,
    ),

]

TEXT_LABELS = [

    ("Clay", 64, 18, 18),

    ("Silty<br>Clay", 48, 6, 46),

    ("Sandy<br>Clay", 42, 51, 7),

    ("Clay<br>Loam", 33, 35, 32),

    ("Silty<br>Clay<br>Loam", 33, 11, 56),

    ("Sandy<br>Clay<br>Loam", 27, 62, 11),

    ("Loam", 17, 42, 41),

    ("Silt<br>Loam", 13, 25, 62),

    ("Silt", 5, 7, 88),

    ("Sandy<br>Loam", 10, 67, 23),

    ("Loamy<br>Sand", 8, 83, 9),

    ("Sand", 4, 91, 5),
]


def add_usda_triangle(fig):

    for seg in USDA_LINES:
        fig.add_trace(
            go.Scatterternary(
                a=seg["a"],
                b=seg["b"],
                c=seg["c"],
                mode="lines",
                line=dict(
                    color="black",
                    width=1.5,
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    for label, a, b, c in TEXT_LABELS:
        fig.add_trace(
            go.Scatterternary(
                a=[a],
                b=[b],
                c=[c],
                mode="text",
                text=[label],
                textfont=dict(
                    size=8,
                    color="black",
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    return fig

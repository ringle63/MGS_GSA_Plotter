import plotly.graph_objects as go

from logic.grainbreaks import (
    get_grain_log_classes,
)

from logic.legendsorting import (
    gsa_sort_key,
)

from logic.filters import NULL_VALUE

def make_grain_log(
    gsa_df,
    mmes_df,
    selected_samples,
    panel,
):

    fig = go.Figure()

    subset = gsa_df[
        gsa_df["GSA_ID"]
        .astype(str)
        .isin(selected_samples)
    ]

    group_by = panel.get(
        "group_by",
        "None",
    )

    custom_groups = panel.get(
        "grouped_samples"
    )

    using_custom_groups = (
            custom_groups is not None
    )

    sample_to_group = {}
    sample_to_groups = {}

    if using_custom_groups:
        (
            sample_to_groups,
            sample_to_group,
        ) = custom_groups

    subset = (
        subset.assign(
            _sort_key=subset["GSA_ID"]
            .apply(gsa_sort_key)
        )
    )

    if using_custom_groups:

        subset["_group"] = (
            subset["GSA_ID"]
            .astype(str)
            .map(sample_to_group)
            .fillna(NULL_VALUE)
        )

        subset = subset.sort_values(
            ["_group", "_sort_key"]
        )

    elif (
            group_by
            and group_by != "None"
    ):

        subset = subset.sort_values(
            [group_by, "_sort_key"]
        )
    else:
        subset = (
            subset.sort_values("_sort_key")
        )

    subset = subset.drop(
        columns="_sort_key"
    )

    settings = {
        "Mastersizer": panel["mastersizer_break"],
        "MastersizerSand": panel["mastersizer_sand_break"],
        "Pipette": panel["pipette_break"],
    }

    mmes_lookup = (
        mmes_df
        .set_index("Sample_Name_Final")
        .to_dict("index")
    )

    classes_order = [
        "Clay",
        "Silt",
        "Very Fine Sand",
        "Fine Sand",
        "Medium Sand",
        "Coarse Sand",
        "Very Coarse Sand",
        "Gravel",
    ]

    colors = {
        "Gravel": "#5b0000",
        "Very Coarse Sand": "#8b0000",
        "Coarse Sand": "#cc5500",
        "Medium Sand": "#ffb000",
        "Fine Sand": "#ffff00",
        "Very Fine Sand": "#ffff99",
        "Silt": "#b2f0f0",
        "Clay": "#0000ff",
    }

    y_labels = []

    group_line_positions = []

    group_label_positions = []

    last_group = None

    class_values = {
        cls: []
        for cls in classes_order
    }

    customdata = []

    for _, row in subset.iterrows():

        current_group = None

        if using_custom_groups:

            current_group = (
                sample_to_group.get(
                    str(row["GSA_ID"]),
                    NULL_VALUE,
                )
            )

        elif (
                group_by
                and group_by != "None"
        ):

            value = row[group_by]

            if (
                    value is None
                    or str(value) == "nan"
            ):
                current_group = NULL_VALUE
            else:
                current_group = str(value)

        mmes_row = mmes_lookup.get(
            str(row["GSA_ID"])
        )

        grain = get_grain_log_classes(
            row,
            mmes_row,
            settings,
        )

        if grain is None:
            continue

        if (
                current_group
                != last_group
        ):
            if last_group is not None:

                spacer = ""

                y_labels.append(
                    spacer
                )

                customdata.append(
                    [None] * 11
                )

                for cls in classes_order:
                    class_values[cls].append(
                        0
                    )

            header = (
                f"── {current_group} ──"
            )

            y_labels.append(
                header
            )

            customdata.append(
                [None] * 11
            )

            for cls in classes_order:
                class_values[cls].append(
                    0
                )

            group_label_positions.append(
                header
            )

            group_line_positions.append(
                header
            )

            last_group = current_group

        sample = row["GSA_ID"]

        y_labels.append(sample)

        customdata.append(
            [
                sample,
                grain["method"],
                grain["break"],
                grain["Gravel"],
                grain["Very Coarse Sand"],
                grain["Coarse Sand"],
                grain["Medium Sand"],
                grain["Fine Sand"],
                grain["Very Fine Sand"],
                grain["Silt"],
                grain["Clay"],
            ]
        )

        for cls in classes_order:
            class_values[cls].append(
                grain[cls]
            )

    for cls in classes_order:
        fig.add_trace(
            go.Bar(
                y=y_labels,
                x=class_values[cls],
                orientation="h",
                name=cls,
                marker_color=colors[cls],
                width=0.9,
                hoverinfo="skip",

                customdata=customdata,

                hovertemplate=[
                    (
                        "<extra></extra>"
                        if row[0] is None
                        else
                        (
                            "<b>%{customdata[0]}</b><br>"
                            "Method: %{customdata[1]}<br>"
                            "Break: %{customdata[2]}<br>"
                            "<br>"
                            "Gravel: %{customdata[3]:.1f}%<br>"
                            "Very Coarse Sand: %{customdata[4]:.1f}%<br>"
                            "Coarse Sand: %{customdata[5]:.1f}%<br>"
                            "Medium Sand: %{customdata[6]:.1f}%<br>"
                            "Fine Sand: %{customdata[7]:.1f}%<br>"
                            "Very Fine Sand: %{customdata[8]:.1f}%<br>"
                            "Silt: %{customdata[9]:.1f}%<br>"
                            "Clay: %{customdata[10]:.1f}%"
                            "<extra></extra>"
                        )
                    )
                    for row in customdata
                ],
            )
        )

    sample_height = 18
    figure_height = (
            len(y_labels)
            * sample_height
            + 120
    )

    fig.layout.meta = {
        "figure_height": figure_height
    }

    for label in group_line_positions:
        fig.add_hline(
            y=label,
            line_width=1.5,
            line_color="black",
        )

    fig.update_layout(
        title="Grain Size Log",

        autosize=False,
        height=figure_height,

        barmode="stack",

        showlegend=False,

        xaxis=dict(
            title="Percent (%)",
            range=[100, 0],
            fixedrange=True,
        ),

        yaxis=dict(
            autorange="reversed",
            side="right",
            title="",
            automargin=True,
            tickfont=dict(
                size=11,
            ),
        ),

        margin=dict(
            l=20,
            r=80,
            t=50,
            b=40,
        ),
    )

    print(
        f"Samples: {len(y_labels)}, "
        f"Figure height: {figure_height}"
    )

    return fig
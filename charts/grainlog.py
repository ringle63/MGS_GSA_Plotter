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
    sort_field = panel.get(
        "grainlog_sort_field",
        "None",
    )

    ascending = panel.get(
        "grainlog_sort_ascending",
        True,
    )

    if (
            sort_field != "None"
            and sort_field in subset.columns
    ):
        if using_custom_groups:

            new_order = []

            all_groups = sorted(
                {
                    g
                    for groups
                    in sample_to_groups.values()
                    for g in groups
                }
            )

            for group_name in all_groups:
                group_samples = [
                    sample
                    for sample, groups
                    in sample_to_groups.items()
                    if group_name in groups
                ]

                group_df = subset[
                    subset["GSA_ID"]
                    .astype(str)
                    .isin(group_samples)
                ].copy()

                group_df = group_df.sort_values(
                    sort_field,
                    ascending=ascending,
                    na_position="last",
                )

                new_order.extend(
                    group_df["GSA_ID"]
                    .astype(str)
                    .tolist()
                )

            subset = (
                subset.set_index(
                    subset["GSA_ID"]
                    .astype(str)
                )
                .loc[new_order]
                .reset_index(drop=True)
            )

        elif (
                group_by
                and group_by != "None"
        ):

            subset = subset.sort_values(
                [group_by, sort_field],
                ascending=[
                    True,
                    ascending,
                ],
                na_position="last",
            )

        else:

            subset = subset.sort_values(
                sort_field,
                ascending=ascending,
                na_position="last",
            )

    settings = {
        "Mastersizer":
            panel["mastersizer_break"],

        "MastersizerSand":
            panel["mastersizer_sand_break"],

        "Pipette":
            panel["pipette_break"],

        "GravelSettings":
            panel.get(
                "grainlog_gravel_settings",
                {
                    "Mastersizer": False,
                    "Pipette": True,
                    "Kehew": True,
                    "Dry Sieve": True,
                },
            ),
    }

    show_grainlog_mean = panel.get(
        "show_grainlog_mean",
        False,
    )

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

    display_labels = []

    group_line_positions = []

    group_label_positions = []

    last_group = None

    class_values = {
        cls: []
        for cls in classes_order
    }

    customdata = []

    mean_rows = {}

    if using_custom_groups:

        all_groups = sorted(
            {
                g
                for groups
                in sample_to_groups.values()
                for g in groups
            }
        )

        for group_name in all_groups:
            samples = [
                sample
                for sample, groups
                in sample_to_groups.items()
                if group_name in groups
            ]

            mean_rows[group_name] = subset[
                subset["GSA_ID"]
                .astype(str)
                .isin(samples)
            ]

    elif (
            group_by
            and group_by != "None"
    ):

        for name, df in subset.groupby(
                group_by,
                dropna=False,
        ):

            if (
                    name is None
                    or str(name) == "nan"
            ):
                name = NULL_VALUE

            mean_rows[str(name)] = df

    else:

        mean_rows["All Samples"] = subset

    if show_grainlog_mean:

        if using_custom_groups:

            for group_name in mean_rows:

                y_labels.append(
                    f"__MEAN__{group_name}"
                )

                customdata.append(
                    [None] * 12
                )

                for cls in classes_order:
                    class_values[cls].append(0)

        elif (
                not group_by
                or group_by == "None"
        ):

            y_labels.append(
                "__MEAN__All Samples"
            )

            customdata.append(
                [None] * 12
            )

            for cls in classes_order:
                class_values[cls].append(0)
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
                    [None] * 12
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

            if (
                    show_grainlog_mean
                    and not using_custom_groups
            ):

                mean_label = (
                    f"__MEAN__{current_group}"
                )

                y_labels.append(
                    mean_label
                )

                customdata.append(
                    [None] * 12
                )

                for cls in classes_order:
                    class_values[cls].append(0)

            customdata.append(
                [None] * 12
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

        if (
                sort_field != "None"
                and sort_field in row.index
        ):
            sort_value = row[sort_field]

            if (
                    sort_value is None
                    or str(sort_value) == "nan"
            ):
                sort_value = None

            else:
                sort_value = round(float(sort_value), 2)

                if sort_value.is_integer():
                    sort_value = int(sort_value)

        else:
            sort_value = None

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
                sort_value,
            ]
        )

        for cls in classes_order:
            class_values[cls].append(
                grain[cls]
            )

    if show_grainlog_mean:

        for i, label in enumerate(y_labels):

            if not str(label).startswith(
                    "__MEAN__"
            ):
                continue

            group_name = (
                str(label)
                .replace(
                    "__MEAN__",
                    ""
                )
            )

            group_df = mean_rows.get(
                group_name
            )

            if (
                    group_df is None
                    or len(group_df) == 0
            ):
                continue

            grains = []

            for _, row in group_df.iterrows():

                sample = str(row["GSA_ID"])

                mmes_row = mmes_lookup.get(sample)

                grain = get_grain_log_classes(
                    row,
                    mmes_row,
                    settings,
                )

                if grain is not None:
                    grain["_sample"] = sample
                    grains.append(grain)

            if not grains:
                continue

            for cls in classes_order:

                values = [
                    (
                        0
                        if (
                                g[cls] is None
                                or str(g[cls]) == "nan"
                        )
                        else g[cls]
                    )
                    for g in grains
                ]

                class_values[cls][i] = (
                        sum(values)
                        / len(values)
                )

            customdata[i] = [
                f"{group_name} Mean",
                "",
                "",
                class_values["Gravel"][i],
                class_values["Very Coarse Sand"][i],
                class_values["Coarse Sand"][i],
                class_values["Medium Sand"][i],
                class_values["Fine Sand"][i],
                class_values["Very Fine Sand"][i],
                class_values["Silt"][i],
                class_values["Clay"][i],
                None,
            ]


    # ==========================
    # DISPLAY LABELS
    # ==========================

    display_labels = []

    for label in y_labels:
        if str(label).startswith("__MEAN__"):

            display_labels.append(
                label.replace(
                    "__MEAN__",
                    "MEAN: "
                )
            )

        else:
            display_labels.append(label)

    for cls in classes_order:
        fig.add_trace(
            go.Bar(
                y=display_labels,
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
                            +
                            (
                                f"Sort ({sort_field}): "
                                "%{customdata[11]}<br>"
                                if (
                                    sort_field != "None"
                                )
                                else ""
                            )
                            +
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

    return fig
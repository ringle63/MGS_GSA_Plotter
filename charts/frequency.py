import plotly.graph_objects as go


def make_frequency_plot(
    mmes_df,
    selected_samples,
    show_legend,
    show_labels,
    x_axis,
    show_break_8,
    show_break_62_5,
):
    fig = go.Figure()

    if not selected_samples:
        fig.update_layout(
            title="No samples selected"
        )
        return fig

    FR_cols = sorted(
        [
            c for c in mmes_df.columns
            if c.startswith("FR_")
        ],
        key=lambda x: float(
            x.replace("FR_", "").replace("_", ".")
        )
    )

    x_vals = [
        float(
            c.replace("FR_", "").replace("_", ".")
        )
        for c in FR_cols
    ]

    subset = mmes_df[
        mmes_df["Sample_Name_Final"]
        .astype(str)
        .isin(selected_samples)
    ]

    for _, row in subset.iterrows():

        sample = str(row["Sample_Name_Final"])

        y_vals = row[FR_cols].tolist()

        plot_x = x_vals.copy()

        if x_axis == "phi":
            import numpy as np

            plot_x = [
                -np.log2(x / 1000)
                for x in plot_x
            ]

        mode = "lines+text" if show_labels else "lines"

        fig.add_trace(
            go.Scatter(
                x=plot_x,
                y=y_vals,
                mode=mode,
                name=sample,
                showlegend=show_legend,
                text=[None] * (len(y_vals) - 1) + [sample],
                textposition="middle right",
            )
        )

    fig.update_layout(
        title="PSD Frequency",
        xaxis_title="Grain Size (µm)",
        yaxis_title="Frequency (%)",
        hovermode="closest",
    )

    if x_axis == "log":
        fig.update_xaxes(type="log")

    elif x_axis == "linear":
        pass

    elif x_axis == "phi":
        fig.update_xaxes(
            title="Phi (φ)"
        )

    break_8 = 8
    break_62 = 62.5

    if x_axis == "phi":
        import numpy as np

        break_8 = -np.log2(8 / 1000)
        break_62 = -np.log2(62.5 / 1000)

    if show_break_8:
        fig.add_vline(
            x=break_8,
            line_dash="dash",
        )

    if show_break_62_5:
        fig.add_vline(
            x=break_62,
            line_dash="dash",
        )

    return fig
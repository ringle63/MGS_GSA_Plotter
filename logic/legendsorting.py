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

# Shared Plotly legend organization for grouped PSD and ternary charts.
# The original trace order (and thus draw order) is intentionally retained.
_GROUP_SUMMARY_SUFFIXES = (
    " Mean",
    " +1σ",
    " -1σ",
    " +2σ",
    " -2σ",
    " +3σ",
    " -3σ",
    " Centroid",
    " Covariance",
)


def organize_grouped_legend(fig, sample_to_group, group_names):
    """Display group heading, summary traces, then naturally sorted samples.

    Only Plotly legend properties are changed. The traces' data, colors,
    visibility, and draw order are preserved. A sample in overlapping
    Custom Groups is listed once under its primary (plotted) group;
    summaries for every matching Custom Group are independently listed.
    """
    groups = list(dict.fromkeys(str(group) for group in group_names))
    if not groups:
        return fig

    sample_to_group = {
        str(sample): str(group)
        for sample, group in sample_to_group.items()
    }
    summary_to_group = {
        f"{group}{suffix}": (group, priority)
        for group in groups
        for priority, suffix in enumerate(_GROUP_SUMMARY_SUFFIXES)
    }
    grouped = {group: {'summaries': [], 'samples': []} for group in groups}

    for trace in fig.data:
        name = str(trace.name or '')
        if name in sample_to_group and sample_to_group[name] in grouped:
            grouped[sample_to_group[name]]['samples'].append(trace)
        elif name in summary_to_group:
            group, priority = summary_to_group[name]
            grouped[group]['summaries'].append((priority, trace))

    rank = 0
    for group_index, group in enumerate(groups):
        traces = [
            trace for _, trace in sorted(
                grouped[group]['summaries'], key=lambda item: item[0]
            )
        ]
        traces.extend(sorted(
            grouped[group]['samples'],
            key=lambda trace: gsa_sort_key(trace.name),
        ))
        # Do not show a header for an empty category.
        first_visible = next(
            (trace for trace in traces if trace.showlegend is not False),
            None,
        )
        for trace in traces:
            trace.legendgroup = f'gsa-group-{group_index}'
            trace.legendrank = rank
            rank += 1
            if trace is first_visible:
                trace.legendgrouptitle = dict(text=group)

    # Plotly sorts legend entries by rank *within* their legend group.
    # Do not reorder fig.data: summary/centroid traces should still be
    # drawn on top of sample traces as in the original charts.
    fig.update_layout(legend=dict(
        traceorder='grouped',
        groupclick='toggleitem',
    ))
    return fig

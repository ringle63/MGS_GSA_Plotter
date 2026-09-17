import numpy as np
import pandas as pd

from logic.mmes_helpers import (
    get_sample_mmes_row,
    get_psd_columns,
    get_fr_columns,
)


ZERO_PREVALENCE_CUTOFF = 0.80


def _curve_columns(
        input_mode,
        source,
        mmes_df,
        mmes_rs_df,
):
    """
    Return native curve columns/x-values for the requested mode.
    """

    if input_mode == "psd":
        return get_psd_columns(
            source,
            mmes_df,
            mmes_rs_df,
        )

    return get_fr_columns(
        source,
        mmes_df,
        mmes_rs_df,
    )


def _numeric_curve(
        row,
        columns,
):
    values = pd.to_numeric(
        row[columns],
        errors="coerce",
    ).to_numpy(
        dtype=float
    )

    return values


def _interpolate_log_x(
        source_x,
        source_y,
        target_x,
):
    """
    Interpolate a Mastersizer curve in log10 grain-size space.

    This is used ONLY to create one common analysis matrix when
    PRIMARY and RS native bin locations differ.
    """

    source_x = np.asarray(
        source_x,
        dtype=float,
    )

    source_y = np.asarray(
        source_y,
        dtype=float,
    )

    target_x = np.asarray(
        target_x,
        dtype=float,
    )

    valid = (
        np.isfinite(source_x)
        & np.isfinite(source_y)
        & (source_x > 0)
    )

    if valid.sum() < 2:
        return None

    source_x = source_x[valid]
    source_y = source_y[valid]

    order = np.argsort(source_x)

    source_x = source_x[order]
    source_y = source_y[order]

    return np.interp(
        np.log10(target_x),
        np.log10(source_x),
        source_y,
    )


def _multiplicative_zero_replacement(
        matrix,
        frac=0.65,
        threshold=0.5,
):
    """
    Python implementation of the CZM branch used by
    zCompositions::cmultRepl() for closed proportions.

    This mirrors the R algorithm used in the original
    Mastersizer workflow:

      cmultRepl(
          X_prop,
          label=0,
          method="CZM",
          output="prop",
          z.warning=0.80,
          z.delete=FALSE
      )

    For CZM:
      1. data are closed to proportions;
      2. the nominal replacement is threshold / row_sum;
      3. if that exceeds the smallest observed positive
         proportion for a part, use frac * column minimum;
      4. multiply the non-zero parts by
         (1 - sum(replacements)).

    With already-closed rows, row_sum is 1, so the nominal
    CZM replacement is 0.5 and the column-minimum adjustment
    normally controls the actual imputed value.
    """

    matrix = np.asarray(
        matrix,
        dtype=float,
    )

    closed = matrix.copy()

    closed = np.where(
        np.isfinite(
            closed
        ),
        closed,
        0.0,
    )

    closed = np.clip(
        closed,
        0.0,
        None,
    )

    row_sums = closed.sum(
        axis=1,
        keepdims=True,
    )

    valid_rows = (
        row_sums[
            :,
            0
        ]
        > 0
    )

    closed[
        valid_rows,
        :
    ] = (
        closed[
            valid_rows,
            :
        ]
        / row_sums[
            valid_rows,
            :
        ]
    )

    # Column minimum among observed positive values.
    # This corresponds to cmultRepl after count-zero labels
    # have been converted to NA for the minimum calculation.
    colmins = np.full(
        closed.shape[1],
        np.nan,
        dtype=float,
    )

    for j in range(
            closed.shape[1]
    ):

        positive = closed[
            :,
            j
        ][
            closed[
                :,
                j
            ]
            > 0
        ]

        if len(
                positive
        ):

            colmins[
                j
            ] = float(
                np.min(
                    positive
                )
            )

    output = closed.copy()

    for i in range(
            closed.shape[0]
    ):

        row = closed[
            i,
            :
        ].copy()

        zero_mask = (
            row
            <= 0
        )

        if not np.any(
                zero_mask
        ):
            output[
                i,
                :
            ] = row
            continue

        if not valid_rows[
            i
        ]:
            output[
                i,
                :
            ] = np.nan
            continue

        # CZM nominal replacement:
        # threshold / n, with n=1 for closed proportions.
        nominal = (
            threshold
            / float(
                row.sum()
            )
        )

        replacements = np.full(
            int(
                zero_mask.sum()
            ),
            nominal,
            dtype=float,
        )

        zero_columns = np.where(
            zero_mask
        )[0]

        for k, column in enumerate(
                zero_columns
        ):

            column_min = (
                colmins[
                    column
                ]
            )

            if (
                    np.isfinite(
                        column_min
                    )
                    and replacements[
                        k
                    ]
                    > column_min
            ):

                replacements[
                    k
                ] = (
                    frac
                    * column_min
                )

        replacement_mass = float(
            replacements.sum()
        )

        if (
                not np.isfinite(
                    replacement_mass
                )
                or replacement_mass
                >= 1.0
        ):
            output[
                i,
                :
            ] = np.nan
            continue

        row[
            zero_columns
        ] = replacements

        row[
            ~zero_mask
        ] = (
            (
                1.0
                - replacement_mass
            )
            * row[
                ~zero_mask
            ]
        )

        output[
            i,
            :
        ] = row

    return output



def _clr_transform(
        matrix,
):
    log_matrix = np.log(
        matrix
    )

    return (
        log_matrix
        - np.mean(
            log_matrix,
            axis=1,
            keepdims=True,
        )
    )


def prepare_mastersizer_analysis(
        gsa_df,
        mmes_df,
        mmes_rs_df,
        selected_samples,
        input_mode="frequency",
):
    """
    Build a common-bin Mastersizer analysis dataframe.

    input_mode:
      "frequency"
          FR-style variables. Bins at >=80% zeros are removed,
          rows are closed, zeros are multiplicatively replaced,
          and CLR coordinates are returned for PCA/clustering.

      "psd"
          PSD undersize variables. Cumulative undersize values
          are interpolated onto the common analysis grid and
          returned directly. Optional standardization is applied
          later by the generic PCA engine.

    PRIMARY and RS retain their native bins for normal plotting.
    Interpolation here is only the deliberate harmonization step
    needed because PCA requires every sample to share one set of
    variables.
    """

    input_mode = (
        "psd"
        if str(input_mode).lower() == "psd"
        else "frequency"
    )

    selected_samples = [
        str(sample)
        for sample in (
            selected_samples
            or []
        )
    ]

    native_curves = {}
    source_grids = {}

    for sample in selected_samples:

        (
            row,
            source,
        ) = get_sample_mmes_row(
            sample,
            mmes_df,
            mmes_rs_df,
        )

        if row is None:
            continue

        columns, x_values = (
            _curve_columns(
                input_mode,
                source,
                mmes_df,
                mmes_rs_df,
            )
        )

        if len(columns) < 3:
            continue

        y_values = _numeric_curve(
            row,
            columns,
        )

        x_values = np.asarray(
            x_values,
            dtype=float,
        )

        if (
                len(x_values)
                != len(y_values)
        ):
            continue

        valid = (
            np.isfinite(x_values)
            & (x_values > 0)
            & np.isfinite(y_values)
        )

        if valid.sum() < 3:
            continue

        x_values = x_values[valid]
        y_values = y_values[valid]

        native_curves[
            sample
        ] = {
            "source":
                source,

            "x":
                x_values,

            "y":
                y_values,
        }

        source_grids[
            source
        ] = x_values

    if len(native_curves) < 2:
        return None

    grids = list(
        source_grids.values()
    )

    if len(grids) == 1:

        common_x = np.asarray(
            grids[0],
            dtype=float,
        )

    else:

        common_min = max(
            float(
                np.min(grid)
            )
            for grid
            in grids
        )

        common_max = min(
            float(
                np.max(grid)
            )
            for grid
            in grids
        )

        if common_min >= common_max:
            return None

        common_x = np.unique(
            np.concatenate(
                [
                    grid[
                        (
                            grid
                            >= common_min
                        )
                        & (
                            grid
                            <= common_max
                        )
                    ]
                    for grid
                    in grids
                ]
            )
        )

    common_x = common_x[
        np.isfinite(
            common_x
        )
        & (
            common_x > 0
        )
    ]

    common_x = np.sort(
        np.unique(
            common_x
        )
    )

    if len(common_x) < 3:
        return None

    analysis_samples = []
    rows = []

    for sample, curve in (
            native_curves.items()
    ):

        if (
                len(curve["x"])
                == len(common_x)
                and np.allclose(
                    curve["x"],
                    common_x,
                    rtol=0,
                    atol=0,
                )
        ):
            values = np.asarray(
                curve["y"],
                dtype=float,
            )

        else:
            values = (
                _interpolate_log_x(
                    curve["x"],
                    curve["y"],
                    common_x,
                )
            )

        if values is None:
            continue

        if (
                len(values)
                != len(common_x)
                or not np.all(
                    np.isfinite(
                        values
                    )
                )
        ):
            continue

        analysis_samples.append(
            sample
        )

        rows.append(
            np.asarray(
                values,
                dtype=float,
            )
        )

    if len(rows) < 2:
        return None

    matrix = np.asarray(
        rows,
        dtype=float,
    )

    retained_x = common_x.copy()

    zero_prevalence = None

    if input_mode == "frequency":

        matrix = np.clip(
            matrix,
            0.0,
            None,
        )

        zero_prevalence = np.mean(
            matrix <= 0,
            axis=0,
        )

        retain_mask = (
            zero_prevalence
            < ZERO_PREVALENCE_CUTOFF
        )

        if retain_mask.sum() < 2:
            return None

        matrix = matrix[
            :,
            retain_mask
        ]

        retained_x = (
            retained_x[
                retain_mask
            ]
        )

        row_sums = matrix.sum(
            axis=1,
            keepdims=True,
        )

        valid_rows = (
            np.isfinite(
                row_sums[:, 0]
            )
            & (
                row_sums[:, 0]
                > 0
            )
        )

        matrix = matrix[
            valid_rows,
            :
        ]

        analysis_samples = [
            sample
            for sample, keep
            in zip(
                analysis_samples,
                valid_rows,
            )
            if keep
        ]

        if len(matrix) < 2:
            return None

        matrix = (
            matrix
            / matrix.sum(
                axis=1,
                keepdims=True,
            )
        )

        matrix = (
            _multiplicative_zero_replacement(
                matrix
            )
        )

        valid_rows = np.all(
            np.isfinite(
                matrix
            )
            & (
                matrix > 0
            ),
            axis=1,
        )

        matrix = matrix[
            valid_rows,
            :
        ]

        analysis_samples = [
            sample
            for sample, keep
            in zip(
                analysis_samples,
                valid_rows,
            )
            if keep
        ]

        if len(matrix) < 2:
            return None

        matrix = _clr_transform(
            matrix
        )

    variable_names = [
        (
            "MSBIN_"
            f"{i:04d}"
        )
        for i
        in range(
            len(
                retained_x
            )
        )
    ]

    analysis_df = pd.DataFrame(
        matrix,
        columns=variable_names,
    )

    analysis_df.insert(
        0,
        "GSA_ID",
        analysis_samples,
    )

    # Merge GSA metadata/numeric fields so the generic hierarchy
    # summary and borehole interpretation architecture can be
    # reused unchanged.
    metadata = (
        gsa_df[
            gsa_df[
                "GSA_ID"
            ]
            .astype(str)
            .isin(
                analysis_samples
            )
        ]
        .copy()
    )

    metadata[
        "GSA_ID"
    ] = (
        metadata[
            "GSA_ID"
        ]
        .astype(str)
    )

    metadata = (
        metadata
        .drop_duplicates(
            "GSA_ID"
        )
    )

    metadata_fields = [
        column
        for column
        in metadata.columns
        if (
            column
            != "GSA_ID"
            and column
            not in analysis_df.columns
        )
    ]

    analysis_df = (
        analysis_df
        .merge(
            metadata[
                [
                    "GSA_ID",
                    *metadata_fields,
                ]
            ],
            on="GSA_ID",
            how="left",
        )
    )

    bin_lookup = {
        variable:
            float(x)
        for variable, x
        in zip(
            variable_names,
            retained_x,
        )
    }

    source_counts = {}

    for sample in analysis_samples:

        source = (
            native_curves[
                sample
            ][
                "source"
            ]
        )

        source_counts[
            source
        ] = (
            source_counts.get(
                source,
                0,
            )
            + 1
        )

    return {
        "dataframe":
            analysis_df,

        "samples":
            analysis_samples,

        "variables":
            variable_names,

        "bin_sizes":
            bin_lookup,

        "input_mode":
            input_mode,

        "native_curves":
            {
                sample:
                    native_curves[
                        sample
                    ]
                for sample
                in analysis_samples
            },

        "common_x":
            common_x,

        "retained_x":
            retained_x,

        "zero_prevalence":
            zero_prevalence,

        "zero_prevalence_cutoff":
            ZERO_PREVALENCE_CUTOFF,

        "source_counts":
            source_counts,

        # FR is already CLR-transformed and should not be
        # standardized again. PSD can use the existing toggle.
        "force_standardize":
            False
            if input_mode
            == "frequency"
            else None,
    }

from dash import dash_table
import pandas as pd

from logic.legendsorting import (
    gsa_sort_key,
)

BASE_FIELDS = [
    "GSA_ID",
    "BoreholeID",
    "depth_ft",
    "analysis_method",
    "formation",
    "County",
    "Origin",

    "weight",
    "munsell_code",
    "primary_color",
    "prim_material",

    "class_usda",
    "class_usc",
    "class_uw",
    "class_folk",

    "sample_total",
    "matrix_total",

    "surf_elev",
    "sample_elevation",

    "max_clast",

    "sandfrac_vf",
    "sandfrac_f",
    "sandfrac_m",
    "sandfrac_c",
    "sandfrac_vc",
    "sandfrac_total",

    "Clay0_2",
    "Clay0_4",
    "Clay0_8",

    "Silt2_625",
    "Silt_4_625",
    "Silt_8_625",

    "Sand625_2000",

    "ClayG_0_2",
    "ClayG_0_4",

    "SiltG_2_625",
    "SiltG_4_625",

    "SandG_625_2000",

    "GravelG_2000_3500",

    "laser_obscuration",
    "Fines_0_63",

    "sandfracG_vf",
    "sandfracG_f",
    "sandfracG_m",
    "sandfracG_c",
    "sandfracG_vc",

    "FinesG_0_63",
    "sandfracG_total",
]


MASTERSIZER_FIELDS = [
    "Particle_Absorption_Index",
    "Span",
    "Uniformity",
    "Specific_Surface_Area",
    "Concentration",

    "Dx__10_",
    "Dx__30_",
    "Dx__50_",
    "Dx__60_",
    "Dx__90_",

    "Result_In_Range___0_2__μm",
    "Result_In_Range___2_50__μm",
    "Result_In_Range___50_2000__μm",
    "Result_In_Range___2000_3500__μm",

    "Result_In_Range___0_4__μm",
    "Result_In_Range___4_62_5__μm",
    "Result_In_Range___62_5_2000__μm",

    "Result_In_Range___0_5__μm",
    "Result_In_Range___5_50__μm",
    "Result_In_Range___5_62_5__μm",

    "Result_In_Range___0_6__μm",
    "Result_In_Range___6_50__μm",
    "Result_In_Range___6_62_5__μm",

    "Result_In_Range___0_8__μm",
    "Result_In_Range___8_50__μm",
    "Result_In_Range___8_62_5__μm",

    "Result_In_Range___50_125__μm",
    "Result_In_Range___62_5_125__μm",
    "Result_In_Range___125_250__μm",
    "Result_In_Range___250_500__μm",
    "Result_In_Range___500_1000__μm",
    "Result_In_Range___1000_2000__μm",

    "Laser_Obscuration",
    "Weighted_Residual",
]

def make_sample_information(
    gsa_df,
    selected_samples,
):

    subset = gsa_df[
        gsa_df["GSA_ID"]
        .astype(str)
        .isin(selected_samples)
    ].copy()

    fields = BASE_FIELDS + MASTERSIZER_FIELDS

    existing_fields = [
        f for f in fields
        if f in subset.columns
    ]

    subset = subset[existing_fields]

    subset = (
        subset.assign(
            _sort_key=subset["GSA_ID"]
            .apply(gsa_sort_key)
        )
        .sort_values("_sort_key")
        .drop(columns="_sort_key")
    )

    subset = subset.fillna("")

    return dash_table.DataTable(
        columns=[
            {
                "name": c,
                "id": c,
            }
            for c in subset.columns
        ],

        data=subset.to_dict("records"),

        style_data={
            "whiteSpace": "normal",
            "height": "auto",
        },

        fixed_rows={"headers": True},

        fixed_columns={
            "headers": True,
            "data": 1,
        },

        sort_action="native",

        filter_action="native",

        page_action="none",

        style_table={
            "overflowX": "auto",
            "overflowY": "auto",
            "height": "100%",
            "width": "100%",
            "minWidth": "100%",
        },

        style_cell={
            "textAlign": "left",
            "minWidth": "100px",
            "width": "100px",
            "maxWidth": "250px",
            "whiteSpace": "normal",
        },

        style_header={
            "fontWeight": "bold",
        },
    )
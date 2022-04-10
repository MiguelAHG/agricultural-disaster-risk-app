"""
Main script for the app.
"""

# Note: use streamlit_env, not base.

import pandas as pd
import geopandas as gpd
import streamlit as st
import altair as alt

# Import from local scripts
from app_graphing import graphing_feature
from app_map import map_feature
from app_barangay_summary import barangay_summary_feature
from app_home import home_feature
from app_select_variable import selection_help_page

# Cache the function that gets the data.
@st.cache(suppress_st_warning = True, allow_output_mutation = True)
def get_data():
    
    topojson_url = "https://raw.githubusercontent.com/MiguelAHG/agricultural-disaster-risk-app/main/geodata/barangay_topojson.json"

    topo_data = alt.topo_feature(
        url = topojson_url,
        feature = "barangay_geodata",
    )

    db = pd.read_excel(
        "./cleaning_outputs/divided_database.xlsx",
        # Get all sheets
        sheet_name = None,
    )

    # Generate mi_df
    mi_df_rows = []

    # Add a row representing the Barangay variable.
    brgy_dct = {
        "Sector": "(Barangay)",
        "Element": "None",
        "Hazard": "None",
        "Disaster Risk Aspect": "None",
        "Detail": "None",
    }
    brgy_row = pd.Series(
        brgy_dct,
        name = 0,
    )
    brgy_tuple = tuple(brgy_dct.values())

    mi_df_rows.append(brgy_row)

    for index, row in db["library"].iterrows():
        first_four = row.loc[["Sector", "Element", "Hazard", "Disaster Risk Aspect"]]
        sid = str(row["SID"])

        # Get sheet associated with row. Do not include BID column.
        sheet = db[sid].drop("BID", axis = 1)

        # Make new rows showing the sheet's column names.
        for detail_col in sheet.columns:
            new_row = first_four.copy()
            new_row["Detail"] = detail_col
            mi_df_rows.append(new_row)

    mi_df = pd.DataFrame(mi_df_rows).reset_index(drop = True)

    # Generate flat_df
    flat_df = pd.DataFrame()

    bid_row = {
            "Sector": "(Barangay)",
            "Element": "None",
            "Hazard": "None",
            "Disaster Risk Aspect": "None",
            "Detail": "None",
        }

    bid_tuple = tuple(bid_row.values())

    for index, row in db["library"].iterrows():
        first_four = row.loc[["Sector", "Element", "Hazard", "Disaster Risk Aspect"]]
        sid = str(row["SID"])
        
        sheet = db[sid].copy()

        # Add MultiIndex
        mi_rows = []
        sheet_num_cols = sheet.shape[1]

        for col in sheet.columns:
            if col == "BID":
                new_mi_row = bid_row
            else:
                new_mi_row = {}
                for i, item in first_four.iteritems():
                    new_mi_row[i] = item
                new_mi_row["Detail"] = col
            mi_rows.append(new_mi_row)

        mi_rows_df = pd.DataFrame(mi_rows)

        sheet.columns = pd.MultiIndex.from_frame(mi_rows_df)

        if sid == "0":
            flat_df = sheet.copy()
        else:
            flat_df = flat_df.merge(
                sheet,
                how = "outer",
                # Put BID column tuple inside another tuple
                # Otherwise, each item in the initial tuple is considered a separate column
                on = (bid_tuple,),
            )

    bid_to_brgy = {}
    for index, row in db["barangay_id"].iterrows():
        bid_to_brgy[row["BID"]] = row["NAME_3"]

    flat_df[bid_tuple] = flat_df[bid_tuple].replace(bid_to_brgy)

    flat_df.columns = ["/".join(tup) for tup in flat_df.columns]

    flat_df = flat_df.rename(columns = {"(Barangay)/None/None/None/None": "(Barangay)"})

    gdf = gpd.read_file("./geodata/gadm_butuan_city_barangays.gpkg")

    return mi_df, flat_df, topo_data, db, gdf

if __name__ == "__main__":

    st.set_page_config(
        page_title = "agriHanda",
        page_icon = ":ear_of_rice:",
        initial_sidebar_state = "expanded",
    )

    st.title("agriHanda :ear_of_rice:")
    st.caption("Agricultural Disaster Risk App for Butuan City")

    # Get the data.
    mi_df, flat_df, topo_data, db, gdf = get_data()

    # Sidebar to choose which feature of the app to use.
    with st.sidebar:
        st.markdown("# App Features")
        feature = st.radio(
            "",
            [
                "Home Page",
                "Map of Butuan City",
                "Barangay Data Summaries",
                "Graphing Tool",
                "Help: Variable Selection"
            ],
        )

    if feature == "Home Page":
        home_feature()
    elif feature == "Map of Butuan City":
        map_feature(mi_df, flat_df, topo_data, gdf)
    elif feature == "Barangay Data Summaries":
        barangay_summary_feature(mi_df, flat_df, db)
    elif feature == "Graphing Tool":
        graphing_feature(mi_df, flat_df)
    elif feature == "Help: Variable Selection":
        selection_help_page(mi_df, flat_df)
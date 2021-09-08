"""
Main script for the app.
"""

# Note: use streamlit_env, not base.

import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
import geopandas as gpd

# Import from local scripts
from app_graphing import graphing_feature
from app_map import map_feature
from app_barangay_summary import barangay_summary_feature
from app_home import home_feature

# Cache the function that gets the data.
@st.cache(suppress_st_warning = True, allow_output_mutation = True)
def get_data():
    mi_df = pd.read_csv("./cleaning_outputs/multiindex_frame.csv")
    flat_df = pd.read_csv("./cleaning_outputs/flat_label_data.csv")
    
    my_url = "https://raw.githubusercontent.com/MiguelAHG/agricultural-disaster-risk-app/main/geodata/barangay_topojson.json"

    topo_data = alt.topo_feature(
        url = my_url,
        feature = "barangay_geodata",
    )

    return mi_df, flat_df, topo_data

if __name__ == "__main__":

    st.title("Agricultural Disaster Risk App for Butuan City")

    # Code for online version
    # if pw != st.secrets["PASSWORD"]:
    #     st.stop()

    # Get the data.
    mi_df, flat_df, topo_data = get_data()

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
            ],
        )

    if feature == "Home Page":
        home_feature()
    elif feature == "Map of Butuan City":
        map_feature(mi_df, flat_df, topo_data)
    elif feature == "Barangay Data Summaries":
        barangay_summary_feature(mi_df, flat_df)
    elif feature == "Graphing Tool":
        graphing_feature(mi_df, flat_df)
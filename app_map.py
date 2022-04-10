import pandas as pd
import numpy as np
import streamlit as st
from PIL import Image
import plotly.express as px

from app_select_variable import selection_help_box, selection_feature

def map_feature(mi_df, flat_df, gdf):
    """Map of Butuan City feature."""

    st.title("Interactive Map")
    st.markdown("""This feature provides an interactive map of Butuan City and its barangays. Use the sidebar on the left to select a variable. This will be used to color-code the barangays.""")

    # In the sidebar, let the user select
    with st.sidebar:
        st.markdown("---")
        st.markdown("# Variable Selection")

        selection_help_box()

        map_var, map_dtype, map_encoding = selection_feature(mi_df, flat_df, var_name = "Map")

    # Get the text from the lowest level in the hierarchy.
    map_detail = map_var.split("/")[-1]

    st.markdown("## Map")

    with st.expander("How to Use Map"):
        help_text = f"Colored areas indicate barangays where data is available. The hue of each barangay indicates how high the value of `{map_detail}` is. Refer to the legend.\n\nHover over a city to see its name and the exact value of `{map_detail}`. Pan by dragging with the left mouse button. Zoom in and out with the scroll wheel. To save a photo, adjust the pan and zoom to the desired area. Then, hover over the top right of the image and click the camera button (Download plot as a png)."
        st.markdown(help_text)

    map_df = flat_df.copy()

    # If the chosen variable contains strings, drop rows with missing values in that variable.
    # This will prevent an error from occurring.
    object_col_df = map_df.select_dtypes(include = "object")
    if map_var in object_col_df.columns:
        map_df = map_df.dropna(axis = 0, subset = [map_var])

    fig = px.choropleth_mapbox(
        map_df,
        geojson = gdf.set_index("NAME_3").geometry,
        locations = "(Barangay)",
        color = map_var,
        color_continuous_scale = "Viridis",
        range_color = None,
        mapbox_style = "carto-positron",
        zoom = 9.7,
        # Center the map on Butuan City's coordinates.
        center = {"lat": 8.94917, "lon": 125.54361},
        opacity = 0.5,
        hover_name = "(Barangay)",
        hover_data = [map_var],
        # Shorten the chosen variable to just its Detail level
        # when displaying it in the map.
        labels = {map_var: map_detail},
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    st.plotly_chart(fig)

    # Open data maps
    st.markdown("## Open Data Maps\n\nThese are more detailed maps about specific hazards in Butuan City.")
    with st.expander("See Open Data Maps"):
        od_map = st.selectbox(
            "Subject",
            options = [
                "Active Faults",
                "Earthquake Induced Landslide",
                "Flood",
                "Ground Shaking",
                "Liquefaction",
                "Rain Induced Landslide",
                "Soil Erosion",
                "Storm Surge",
            ]
        )

        try:
            img = Image.open("./open_data_maps/{}.jpg".format(od_map))
        except IOError:
            st.markdown("An error occurred in retrieving the map.")

        st.image(img)

    # External map websites
    st.markdown("""---

## Other Map Websites

- [Google Maps](https://www.google.com.ph/maps/place/Butuan+City,+Agusan+Del+Norte/@8.8955225,125.442357,11z/data=!3m1!4b1!4m5!3m4!1s0x3301e998b1704fcf:0x85e95810384ea2d6!8m2!3d8.9475377!4d125.5406234)
- [UP NOAH (Nationwide Operational Assessment of Hazards)](http://noah.up.edu.ph/#/)
- [PHIVOLCS FaultFinder](https://faultfinder.phivolcs.dost.gov.ph/)""")
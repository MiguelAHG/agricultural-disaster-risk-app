import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
from PIL import Image

from app_select_variable import select_variable

def map_feature(mi_df, flat_df, topo_data):
    """Map of Butuan City feature."""

    st.title("Interactive Map")
    st.markdown("""This feature provides an interactive map of Butuan City and its barangays. Use the sidebar on the left to select a variable. This will be used color the barangays.""")

    # In the sidebar, let the user select
    with st.sidebar:
        st.markdown("---")
        st.markdown("# Variable Selection")
        map_var, map_dtype, map_encoding = select_variable(mi_df, flat_df, var_name = "Map")

    # Get the text from the lowest level in the hierarchy.
    map_detail = map_var.split("/")[-1]

    st.markdown("## Map")

    with st.expander("View Map", expanded = True):

        # Base layer.
        # Use if the chosen variable is the barangay.
        base = (
            alt.Chart(topo_data)
            .mark_geoshape(
                stroke = "black"
            )
            .properties(
                height = 500,
            )
        )

        map = base.encode(
            tooltip = [
                alt.Tooltip(
                    shorthand = "properties.NAME_3",
                    title = "Barangay",
                    type = "nominal",
                ),
            ]
        )

        # Choropleth layer
        if map_var != "(Barangay)":
            
            # Legend title only shows Detail level of hierarchy
            legend_title = map_var.split("/")[-1]
            
            color_basic = alt.Color(
                map_var,
                type = map_encoding,
                scale = alt.Scale(scheme = "blueorange"),
                legend = alt.Legend(title = legend_title)
            )

            selection_exists = True

            if map_dtype == "number":

                view = st.radio(
                    label = "Map View",
                    options = ["See All Barangays", "Highlight Barangays"],
                )

                if st.checkbox("Help", value = False):
                    st.markdown("'See All Barangays' colors all barangays where there is data.\n\n'Highlight Barangays' provides a slider to highlight specific barangays based on variable value.")

                if view == "See All Barangays":
                    selection_exists = False
                    color_special = color_basic

                elif view == "Highlight Barangays":

                    # Slider selection for numerical variables

                    data_col = flat_df[map_var].dropna()

                    min_value = min(data_col)
                    max_value = max(data_col)
                    step_value = (max_value - min_value) * 0.01
                    close_value = (max_value - min_value) * 0.10

                    slider = alt.binding_range(
                        min = min_value,
                        max = max_value,
                        step = step_value,
                        name = "Select values near:"
                    )

                    selection = alt.selection_single(
                        name = "SliderSelector",
                        fields = ["select_near"],
                        bind = slider,
                    )

                    color_special = alt.condition(
                        # This expression returns True if the real values are close to the selected value.
                        # "Close" means within 10% of the total range of values.
                        predicate = np.abs(alt.datum[map_var] - selection["select_near"]) <= close_value,
                        if_true = color_basic,
                        if_false = alt.value("white"),
                    )

            elif map_dtype == "text":

                # Standard multi-select for text variables.

                if st.checkbox("Help", value = False):
                    st.markdown("Click on a barangay in order to highlight all barangays that share the same category.\n\nTo return the map to its original state, click on an empty space near the edge of the map.")

                selection = alt.selection_multi(fields = [map_var])

                color_special = alt.condition(
                    selection,
                    color_basic,
                    alt.value("white"),
                )

            choro = (
                base
                .encode(
                    tooltip = [
                        alt.Tooltip(
                            shorthand = "properties.NAME_3",
                            type = "nominal",
                            title = "Barangay",
                        ),
                        alt.Tooltip(
                            shorthand = map_var,
                            type = map_encoding,
                            title = map_detail,
                        )
                    ],
                    color = color_special,
                )
                .transform_lookup(
                    lookup = "properties.NAME_3",
                    from_ = alt.LookupData(flat_df, "(Barangay)", [map_var]),
                )
            )

            if selection_exists:
                choro = choro.add_selection(selection)

            map = base + choro

        # Display map
        st.altair_chart(map, use_container_width = True)

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
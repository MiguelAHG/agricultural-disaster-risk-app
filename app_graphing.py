import pandas as pd
import numpy as np
import altair as alt
import streamlit as st

# Import custom function
from app_select_variable import select_variable

def graphing_feature(mi_df, flat_df):
    """Graphing feature of app."""

    st.title("Graphing Tool")
    st.markdown("This feature allows the user to choose specific variables and generate tables and graphs.")

    st.markdown("## Chart Configuration")
    st.markdown("### Mark Type")

    st.markdown("""Select a mark type, which is the shape used to represent the data. Note that one may select Bar and Univariate in order to create a histogram.""")

    mark_options = [
        "Area",
        "Bar",
        "Boxplot",
        "Line",
        "Point",
    ]

    mark_type = st.selectbox(
        label = "Mark Type for Chart",
        options = mark_options,
    )

    st.markdown("### Number of Variables")

    ub = st.radio(
        label = "Number of Variables",
        options = [
            "1 (Univariate)",
            "2 (Bivariate)"
        ],
        help = "If Univariate is selected, it is assumed that you want to plot a distributional chart like a histogram.",
    )

    num_vars = int(ub[0])

    st.markdown("### Select Variables")

    st.markdown("""The variables have been grouped into a heirarchical structure for ease of use. Each variable name is composed of a Sector, Element, Hazard, Disaster Risk Aspect, and Detail. The option that you choose at a higher level will change the options available at a lower level. Thus, please answer the selectboxes from **top to bottom**.

Also, note that some variable names may have (dot) or (bracket) in them. This means that special characters like . [ ] were removed in order to avoid errors in the program.""")

    cols = st.columns(num_vars)

    with cols[0]:
        x_label, x_dtype, x_encoding = select_variable(mi_df, flat_df, var_name = "x")
        var_list = [x_label]

    if num_vars == 2:
        with cols[1]:
            y_label, y_dtype, y_encoding = select_variable(mi_df, flat_df, var_name = "y")
            var_list.append(y_label)
    else:
        y_label = "count()"
        y_encoding = alt.Undefined

    st.markdown("## Results")

    st.markdown("A new table and chart are generated every time the variables are changed. To avoid slow-downs, please minimize the 'Display Table' and 'Display Chart' boxes before making changes to the variables.")

    st.markdown("### Table")

    table_expander = st.expander(
        label = "Display Table",
        expanded = False,
    )

    with table_expander:
        display_table = (
            flat_df[var_list].copy()
            .sort_values(var_list[0])
        )

        if st.checkbox("Remove null values"):
            display_table = display_table.dropna()

        st.dataframe(display_table)

    st.markdown("### Chart")

    st.markdown("""Note the following:

- Numerical variables are aggregated using the mean by default.
- Use the buttons near the top right corner of the chart in order to expand it or save it to your device.""")

    # Pick a chart height
    height_px = st.number_input(
        label = "Chart height (pixels)",
        min_value = 300,
        max_value = 1000,
        value = 500,
        help = "The default chart height is 500 pixels. The chart width is proportional to the width of your browser."
    )

    chart_expander = st.expander(
        label = "Display Chart",
        expanded = False,
    )

    with chart_expander:

        # Error message to ensure quantitative variable for boxplot
        if mark_type == "Boxplot" and ("quantitative" not in [x_encoding, y_encoding]):
            st.error("Error: You have selected a boxplot. At least one variable must have Numerical data type and Quantitative encoding.")
            st.stop()

        # Drop rows with nulls
        flat_df = flat_df[var_list].dropna()

        # Make the chart object
        chart = alt.Chart(flat_df)

        # Whether to bin the x axis.
        bin_x = False

        if mark_type == "Area":
            show_points = st.checkbox("Show points on chart")
            chart = chart.mark_area(point = show_points)

        elif mark_type == "Bar":
            if num_vars == 1 and x_encoding == "quantitative":
                bin_x = st.checkbox("Bin the x-axis (for histogram)")

            chart = chart.mark_bar()

        elif mark_type == "Boxplot":
            chart = chart.mark_boxplot(ticks = True)
            # Set ticks to true so that even very short ranges, or single values, can be seen.

        elif mark_type == "Line":
            show_points = st.checkbox("Show points on chart")
            chart = chart.mark_line(point = show_points)

        elif mark_type == "Point":
            chart = chart.mark_point()

        # Unique axis title for barangay variable
        if x_label.startswith("(Barangay)"):
            x_title = "(Barangay)"
        else:
            x_title = x_label

        chart = chart.encode(
            x = alt.X(
                shorthand = x_label,
                type = x_encoding,
                bin = bin_x,
                title = x_title,
            ),
        )

        if not (mark_type == "Boxplot" and num_vars == 1):
            
            chart = chart.encode(
                y = alt.Y(
                    shorthand = y_label,
                    type = y_encoding,
                ),
            )

        chart = chart.properties(
            title = "Chart Type: " + mark_type,
            height = height_px,
        ).interactive()

        st.altair_chart(chart, use_container_width = True)
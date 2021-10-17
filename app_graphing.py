import altair as alt
import streamlit as st

# Import custom function
from app_select_variable import selection_help_box, selection_feature

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

    selection_help_box()

    cols = st.columns(num_vars)

    with cols[0]:
        x_label, x_dtype, x_encoding = selection_feature(mi_df, flat_df, var_name = "x")
        var_list = [x_label]

    if num_vars == 2:
        with cols[1]:
            y_label, y_dtype, y_encoding = selection_feature(mi_df, flat_df, var_name = "y")
            var_list.append(y_label)
    else:
        y_label = "count()"
        y_encoding = "quantitative"

    # Check first if x label and y label are the same
    if x_label == y_label:
        st.markdown("---\n\n**Warning**: The two variables are the same. Please select two different variables before proceeding.")
        return

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

        # At least 1 variable must be quantitative for the inputs to be valid for a boxplot.
        invalid_for_boxplot = (
            mark_type == "Boxplot"
            and (
                (
                    num_vars == 1
                    and x_encoding != "quantitative"
                )
                or
                (
                    num_vars == 2
                    and ("quantitative" not in [x_encoding, y_encoding])
                )
            )
        )

        if invalid_for_boxplot:
            st.warning("Warning: You have selected a boxplot. Please ensure that at least one variable has both Numerical data type and Quantitative encoding type.")
            st.stop()

        subset = var_list.copy()
        
        if "(Barangay)" not in subset:
            subset.append("(Barangay)")
        
        flat_df_subset = flat_df[subset].dropna() # Drop rows with nulls

        # Make the chart object
        chart = alt.Chart(flat_df_subset)

        # Whether to bin the x axis.
        bin_x = False

        if mark_type == "Area":
            show_points = st.checkbox("Show points on chart")
            chart = chart.mark_area(point = show_points)

        elif mark_type == "Bar":
            if num_vars == 1 and x_encoding == "quantitative":
                bin_x = st.checkbox(
                    "Bin the x-axis to produce a histogram",
                    value = True,
                )

            chart = chart.mark_bar()

        elif mark_type == "Boxplot":
            chart = chart.mark_boxplot(ticks = True)
            # Set ticks to true so that even very short ranges, or single values, can be seen.

        elif mark_type == "Line":
            show_points = st.checkbox("Show points on chart")
            chart = chart.mark_line(point = show_points)

        elif mark_type == "Point":
            chart = chart.mark_point()

        # Use Detail level as title.
        x_title = x_label.split("/")[-1]

        chart = chart.encode(
            x = alt.X(
                shorthand = x_label,
                type = x_encoding,
                bin = bin_x,
                title = x_title,
            ),
        )

        # List of variables to show in the tooltip
        tooltip_list = []
        if "(Barangay)" not in var_list:
            tooltip_list.append(
                alt.Tooltip("(Barangay)", type = "nominal")
            )

        tooltip_list.append(
            alt.Tooltip(x_label, type = x_encoding, title = x_title)
        )

        # Do not encode the y variable if the chart is a univariate boxplot.
        # This is done in order to avoid an error.
        if not (mark_type == "Boxplot" and num_vars == 1):
            
            # Use Detail level as title.
            y_title = y_label.split("/")[-1]

            chart = chart.encode(
                y = alt.Y(
                    shorthand = y_label,
                    type = y_encoding,
                    title = y_title,
                ),
            )

            tooltip_list.append(
                alt.Tooltip(y_label, type = y_encoding, title = y_title)
            )

        # Do not use a tooltip if the graph is a univariate histogram.
        # When a tooltip is used, the histogram is not drawn properly.
        if not bin_x:
            chart = chart.encode(
                tooltip = tooltip_list
            )

        chart = (
            chart
            .properties(
                title = "Chart Type: " + mark_type,
                height = height_px,
            )
            .interactive()
        )

        st.altair_chart(chart, use_container_width = True)
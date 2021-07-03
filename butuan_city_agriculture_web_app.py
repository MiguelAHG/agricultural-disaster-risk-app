# Use streamlit_env, not base.

import pandas as pd
import numpy as np
import altair as alt
import streamlit as st

from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype

# Cache the function that gets the data.
@st.cache(suppress_st_warning = True)
def get_data():
    orig_df = pd.read_csv(
        "./butuan_city_combined_agriculture_data.csv",
        index_col = 0,
        header = list(range(5)),
    )

    # DataFrame of the MultiIndex columns
    mi_df = orig_df.columns.to_frame()

    # Edit the indices so that there are no dots or brackets. These can cause semantic errors in Altair.
    for mi_level in mi_df:
        mi_df[mi_level] = (
            mi_df[mi_level]
            .str.replace(".", "(dot)", regex = False)
            .str.replace("[\[\]]", "(bracket)", regex = True)
        )

    orig_df.columns = pd.MultiIndex.from_frame(mi_df)

    # Flatten the MultiIndex columns into strings so that they can be used in Altair.
    flat_cols = (
        mi_df
        .transpose()
        .apply(lambda series: series.str.cat(sep = "/"))
    )

    flat_df = orig_df.copy()
    flat_df.columns = flat_cols

    return orig_df, mi_df, flat_df


# Password to use the app
st.markdown("This app is restricted to the members of the team. Type the password in order to use it.")
pw = st.text_input("Password")

if pw != "sus amogus":
    st.stop()


orig_df, mi_df, flat_df = get_data()

st.title("Visualization App for Butuan City's Open Agriculture Data")

st.markdown("# Chart Configuration")
st.markdown("## Mark Type")

st.markdown("""Note:

- One may select Bar and Univariate in order to create a histogram.
- One may select Point in order to create a scatter plot.""")

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

st.markdown("## Variables")

ub = st.radio(
    label = "Number of Variables",
    options = [
        "1 (Univariate)",
        "2 (Bivariate)"
    ],
    help = "If Univariate is selected, it is assumed that you want to plot a distributional chart like a histogram. The **frequency of the x variable** will be supplied as the y variable when needed.",
)

num_vars = int(ub[0])

st.markdown("### Select Variables")

st.markdown("""Since there are many variables, these have been grouped into a **heirarchical structure** for ease of use. Each variable name is composed of a Sector, Element, Hazard, Disaster Risk Aspect, and Detail. The option that you choose at a higher level will change the options available at a lower level. Thus, please answer the selectboxes from **top to bottom**.

Also, note that some variable names may have (dot) or (bracket) in them. This means that special characters like . [ ] were removed in order to avoid errors in the program.""")

def select_variable(var_name = "x"):

    """Select a variable in the columns of flat_df.
    This function references the following in the global namespace: mi_df, flat_df."""

    st.markdown("#### {} Variable".format(var_name))

    narrow_down = mi_df.copy()
    selection_list = []

    help_dict = {
        "Sector": "Select the general sector or subsector that you would like to know about. Currently, only Agriculture data are available. You may also select (Barangay) in order to compare barangays.",
        "Element": "Select an element which may be affected by hazards. For example, the elements under Agriculture are Crops, Fisheries, and Livestock.",
        "Hazard": "Select a hazard which may harm the element. Currently, only natural hazards are available.",
        "Disaster Risk Aspect": "Select one of the aspects used to determine disaster risk, such as exposure, sensitivity, etc.",
        "Detail": "Select one of various specific pieces of information.",
    }

    for mi_level in narrow_down.columns:
        options = narrow_down[mi_level].unique()

        selection = st.selectbox(
            label = mi_level,
            options = options,
            help = help_dict[mi_level],
            key = f"{var_name} {mi_level}", # Use a unique key so that the app can differentiate between selectboxes.
        )

        if selection == "(Barangay)" and mi_level == "Sector":
            selection_list = ["(Barangay)", "None", "None", "None", "None"]
            break

        narrow_down = narrow_down[
            narrow_down[mi_level] == selection
        ]

        selection_list.append(selection)

    final_label = "/".join(selection_list)
    st.write("Final {} variable: {}".format(
        var_name,
        final_label,
    ))

    data_col = flat_df[final_label]

    # Use Pandas API type-checking functions to determine encodings.
    if is_string_dtype(data_col):
        st.write("Data type: Text")
        st.write("Encoding type: Nominal")

        encoding = "nominal"

        # alt.Undefined allows a argument to not be supplied.
        # In this case, the nominal encoding cannot be used with an aggregation function.

    elif is_numeric_dtype(data_col):
        st.write("Data type: Numerical")

        help_str = """'Quantitative' means that the variable is continuous, e.g., '1, 1.1, 1.25'.

'Ordinal' means that the variable is discrete, e.g., '1, 2, 3'.

'Nominal' means that the numbers represent labels, not measurements."""

        encoding = st.radio(
            label = "Encoding type:",
            options = [
                "Quantitative",
                "Ordinal",
                "Nominal",
            ],
            help = help_str,
            key = f"{var_name} encoding",
        )
        encoding = encoding.lower()
    
    return final_label, encoding

cols = st.beta_columns(num_vars)

with cols[0]:
    x_label, x_encoding = select_variable(var_name = "x")
    var_list = [x_label]

if num_vars == 2:
    with cols[1]:
        y_label, y_encoding = select_variable(var_name = "y")
        var_list.append(y_label)
else:
    y_label = "count()"
    y_encoding = alt.Undefined

encoding_dict = {y_label: y_encoding, x_label: x_encoding}
# y comes first in the encoding_dict since it is usually the one that's aggregated.

st.markdown("# Results")

st.markdown("A new table and chart are generated every time the variables are changed. To avoid slow-downs, please uncheck 'Generate a Table' and 'Generate a Chart' before making changes to the variables.")

st.markdown("## Table")

if st.checkbox("Generate a Table"):
    display_table = flat_df[var_list].copy()

    if st.checkbox("Remove null values"):
        display_table = display_table.dropna()

    st.dataframe(display_table)

st.markdown("## Chart")

st.markdown("""Note the following:

- Numerical variables are aggregated using the **mean** by default. This can be changed by using the 'Aggregate one quantitative variable' option. This option only appears below when appropriate.
- Use the buttons near the top right corner of the chart in order to expand it or save it to your device.""")

# Pick a chart height
height_px = st.number_input(
    label = "Chart height (pixels)",
    min_value = 300,
    max_value = 1000,
    value = 500,
    help = "The default chart height is 500 pixels. The chart width is proportional to the width of your browser."
)

# Dictionary of chart options
chart_options = {
    "bin_x": False,
}

chart_checkbox = st.checkbox("Generate a Chart")

if chart_checkbox:

    # Error message to ensure quantitative variable for boxplot
    if mark_type == "Boxplot" and ("quantitative" not in [x_encoding, y_encoding]):
        st.error("Error: You have selected a boxplot. At least one variable must have Numerical data type and Quantitative encoding.")
        st.stop()

    # Select an aggregation function
    which_var = None
    aggfunc = None

    if "quantitative" in encoding_dict.values() and mark_type != "Boxplot":
        if st.checkbox("Aggregate one quantitative variable"):
            which_var = st.selectbox(
                label = "Variable to aggregate",
                options = [key for key in encoding_dict if encoding_dict[key] == "quantitative"]
            )
            aggfunc = st.selectbox(
                label = "Aggregation Function",
                options = [
                    "Mean",
                    "Median",
                    "Min",
                    "Max",
                    "Sum",
                    "Product",
                ],
            ).lower() # Use lowercase

    # Drop rows with nulls
    flat_df = flat_df[var_list].dropna()

    # Make the chart object
    chart = alt.Chart(flat_df)

    if mark_type == "Area":
        show_points = st.checkbox("Show points on chart")
        chart = chart.mark_area(point = show_points)

    elif mark_type == "Bar":
        if num_vars == 1 and x_encoding == "quantitative":
            chart_options["bin_x"] = st.checkbox("Bin the x-axis (for histogram)")

        chart = chart.mark_bar()

    elif mark_type == "Boxplot":
        chart = chart.mark_boxplot(ticks = True)
        # Set ticks to true so that even very short ranges, or single values, can be seen.

    elif mark_type == "Line":
        show_points = st.checkbox("Show points on chart")
        chart = chart.mark_line(point = show_points)

    elif mark_type == "Point":
        chart = chart.mark_point()

    # Aggregation condition
    if which_var == x_label:
        x_shorthand = f"{aggfunc}({x_label})"
    else:
        x_shorthand = x_label

    chart = chart.encode(
        x = alt.X(
            shorthand = x_shorthand,
            type = x_encoding,
            bin = chart_options["bin_x"]
        ),
    )

    if not (mark_type == "Boxplot" and num_vars == 1):
        if which_var == y_label:
            y_shorthand = f"{aggfunc}({y_label})"
        else:
            y_shorthand = y_label
        
        chart = chart.encode(
            y = alt.Y(
                shorthand = y_shorthand,
                type = y_encoding,
            ),
        )

    chart = chart.properties(
        title = "Chart Type: " + mark_type,
        height = height_px,
    ).interactive()

    st.altair_chart(chart, use_container_width = True)
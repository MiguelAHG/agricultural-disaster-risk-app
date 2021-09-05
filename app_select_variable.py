import pandas as pd
import numpy as np
import streamlit as st

from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype

def select_variable(mi_df, flat_df, var_name = "x"):

    """Select a variable in the hierarchical system."""
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

    if selection_list[0] == "(Barangay)":
        show_label = "(Barangay)"
        final_label = "(Barangay)"
    else:
        final_label = "/".join(selection_list)
        show_label = final_label

    st.write("Final {} variable: {}".format(
        var_name,
        show_label,
    ))

    data_col = flat_df[final_label]

    # Use Pandas API type-checking functions to determine encodings.
    if is_string_dtype(data_col):
        st.write("Data type: Text")
        st.write("Encoding type: Nominal")

        data_type = "text"
        encoding = "nominal"

    elif is_numeric_dtype(data_col):
        st.write("Data type: Numerical")

        help_str = """'Quantitative' means that the variable represents a quantitative count or measurement. For example, 1, 1.1, and 1.25.

'Ordinal' means that the variable is qualitative and ordered. For example, a rating from 1 to 5.

'Nominal' means that the numbers represent qualitative unordered labels. For example, an ID number."""

        data_type = "number"

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
        
    return final_label, data_type, encoding
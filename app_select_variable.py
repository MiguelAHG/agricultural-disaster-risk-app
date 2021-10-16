import streamlit as st

from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype

def selection_feature(mi_df, flat_df, var_name = "x"):

    """Select a variable in the hierarchical system."""
    st.markdown("---\n\n#### {} Variable".format(var_name))

    first_radio = st.radio(
        "What variable would you like to select?",
        options = [
            "Barangay",
            "Other variable",
        ],
        key = f"{var_name} radio",
    )

    if first_radio == "Barangay":
        show_label = "(Barangay)"
        final_label = "(Barangay)"

    else:
        # Variable selection system for hierarchy of labels

        narrow_down = (
            mi_df
            .copy()
            # Drop the row for (Barangay).
            .loc[mi_df["Sector"] != "(Barangay)"]
        )

        selection_list = []

        help_dict = {
            "Sector": "Currently, only data on the Agriculture sector are available.",
            "Element": "Select an element which may be affected by hazards. For example, the elements under Agriculture are Crops, Fisheries, and Livestock.",
            "Hazard": "Select a hazard which may harm the element. Currently, only natural hazards are available.",
            "Disaster Risk Aspect": "Select one of the aspects used to determine disaster risk, such as exposure, sensitivity, etc.",
            "Detail": "Select a specific piece of information.",
        }

        for mi_level in narrow_down.columns:
            
            if len(selection_list) > 0:
                prev_selections = "/".join(selection_list)
            else:
                prev_selections = "no selection"

            options = narrow_down[mi_level].unique()
            
            selection = st.selectbox(
                label = mi_level,
                options = options,
                help = help_dict[mi_level],
                key = f"variable: {var_name}, selections: {prev_selections}",
                # Use a unique key so that the app can differentiate between selectboxes.
                # prev_selections is included so that the app doesn't get confused
                # when a higher level changes the options at a lower level.
            )

            narrow_down = narrow_down.loc[
                narrow_down[mi_level] == selection,
                :
            ]

            selection_list.append(selection)

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

    st.markdown("---")
    return final_label, data_type, encoding









def selection_help_box():
    """Display a box with advice on how to use the variable selection system."""

    st.markdown("If you need help with this, please read the 'Help: Variable Selection' page.")








def selection_help_page(mi_df, flat_df):
    """Display a page that explains how the variable selection system works."""

    st.markdown("""# Help: Variable Selection

This page will help you understand how to use the variable selection system in "Map of Butuan City" and "Graphing Tool".""")

    st.markdown("""## Understanding the Dataset
    
The variables in the dataset have been grouped together to make it easier to navigate through them. This is a hierarchy with 5 levels.""")

    st.image("./figures/hierarchy_of_labels.png")

    figure_explanation = """The five levels of the hierarchy are explained below.

- Sector
    - Due to the scope of the project, the only sector available is Agriculture.
- Element
    - Exposed elements are “people, property, systems, or other elements present in hazard zones that are thereby subject to potential losses” (UNISDR, 2009).
    - The dataset contains Crops, Livestock, and Fisheries.
- Hazard
    - Hazards are dangerous objects, activities, or occurrences that may cause harm to elements (UNISDR, 2009).
    - The dataset contains Drought, Flood, Rain-Induced Landslide, Sea Level Rise, and Storm Surge.
- Disaster Risk Aspect
    - This level contains general aspects relating to disaster risk: Hazard, Exposure, Sensitivity, Degree of Impact, Adaptive Capacity, and Overall Risk.
- Detail
    - This is the bottom-most level of the hierarchy. It contains various specific details.
    - For example, it contains key metrics of disaster risk, such as Vulnerability Score and Risk Score.
"""

    with st.expander("Click me for an explanation of the levels of the hierarchy.", expanded = False):
        st.markdown(figure_explanation)

    system_explanation = """## How to Select a Variable

First, you have to select "Barangay" or "Other variable".

- Barangay: This variable contains the names of the barangays. This is useful for making bar charts.
- Other variable: Select a variable in the hierarchy.
    
In the hierarchy, the option that you choose at a higher level will change the options available at a lower level. Because of this, it is good to answer the selectboxes from **top to bottom**.

For example, if the element “Crops” is selected, 6 hazard options are available. However, if the element “Fisheries” is selected, only 4 hazard options are available. This is what we mean when we say that changing a higher level changes the options at a lower level."""

    st.markdown(system_explanation)

    full_practice_text = """## Practice Selecting a Variable
    
The variable selection system is given below, so try practicing here. Your task is to find the following variable:

- *Sector*: Agriculture
- *Element*: Livestock
- *Hazard*: Flood
- *Disaster Risk Aspect*: Overall Risk
- *Detail*: Vulnerability Score 

Remember to answer the selectboxes from top to bottom. A message will appear at the bottom of the page telling you if you found the variable."""

    st.markdown(full_practice_text)

    sample_label, sample_dtype, sample_encoding = selection_feature(mi_df, flat_df, var_name = "practice")
    
    # Change the found variable based on whether the correct label was found.
    found = (sample_label == "Agriculture/Livestock/Flood/Overall Risk/Vulnerability Score")

    if found:
        st.markdown("## [\U00002714] You found it!\n\nNow you know how to use the variable selection system.")
    else:
        st.markdown("## [\U0000274C] You haven't found the variable yet.")
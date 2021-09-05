import pandas as pd
import numpy as np
import streamlit as st

import matplotlib.pyplot as plt
import seaborn as sns

# For matplotlib charts
from matplotlib.backends.backend_agg import RendererAgg
from io import BytesIO

def barangay_summary_feature(mi_df, flat_df):
    """Barangay Data Summary feature."""

    st.title("Barangay Data Summaries")
    st.markdown("""This feature lets you select one barangay and get a summary of the most important data on agricultural disaster risk. Select a barangay from the options, or search for one by typing inside the box.""")

    # Let the user select a barangay.
    barangay = st.selectbox(
        label = "Select barangay",
        options = flat_df["(Barangay)"],
    )

    # Make a hierarchically labeled DataFrame again.
    orig_df = flat_df.copy().set_index("Index/Barangay")
    orig_df.columns = pd.MultiIndex.from_frame(mi_df)

    # Geological areas affectd by hazards
    geo_areas_list = list(
        orig_df
        .loc[
            barangay,
            orig_df.columns.get_level_values("Detail") == "Geographical Area Or Ecosystem"
        ]
        .dropna()
        .unique()
    )

    # Join the list into a string to be displayed on screen.
    geo_areas_str = "- " + "\n- ".join(geo_areas_list)
    geo_message = "Geological areas affected by hazards\n" + geo_areas_str

    st.markdown(geo_message)

    #---
    # Identify the element-hazard combinations of the barangay.

    # This df contains the "This Hazard May Affect The Element" columns.
    # These columns were added during cleaning.
    may_affect = (
        orig_df
        .loc[
            barangay,
            orig_df.columns.get_level_values("Detail") == "This Hazard May Affect The Element"
        ]
        .dropna() # A null value in these columns means that the element does not exist in records for this barangay.
    )
    may_affect = may_affect.loc[may_affect == "Yes"]

    # These are Series containing the hazards and elements at risk in the barangay.
    hazards = pd.Series(
        may_affect.index.get_level_values("Hazard")
    )
    elements = pd.Series(
        may_affect.index.get_level_values("Element"),
    )

    # df of element-hazard combinations
    eh_combos = pd.concat(
        [elements, hazards],
        axis = 1,
    )

    # This function gets the risk category of a given e-h combination.
    get_category = lambda series, cat_name: orig_df.at[
        barangay,
        (
            "Agriculture",
            series["Element"],
            series["Hazard"],
            "Overall Risk",
            cat_name,
        )
    ]

    eh_combos["Vulnerability Category"] = eh_combos.apply(
        get_category,
        axis = 1,
        cat_name = "Vulnerability Category",
    )

    eh_combos["Risk Category"] = eh_combos.apply(
        get_category,
        axis = 1,
        cat_name = "Risk Category",
    )

    # This df is the version displayed on screen.
    # Duplicate elements are not shown so it looks hierarchical.
    eh_display = eh_combos.copy()
    eh_display.loc[
        eh_combos.duplicated(subset = "Element", keep = "first"),
        "Element"
    ] = ""

    # Dictionaries to convert risk categories to numbers.
    risk_cat_to_num = {
        "Low Risk": 1,
        "Moderate Risk": 3,
        "High Risk": 5,
        "Very High Risk": 6,
    }
    vulnerability_cat_to_num = {
        "Low": 1,
        "Medium Low": 2,
        "Medium": 3,
        "Medium High": 4,
        "High": 5,
    }

    # This df contains numbers only. It is for the heatmap.
    eh_grid = eh_display.copy()
    eh_grid["Vulnerability Category"] = eh_display["Vulnerability Category"].replace(vulnerability_cat_to_num)
    eh_grid["Risk Category"] = eh_display["Risk Category"].replace(risk_cat_to_num)
    eh_grid.loc[:, ["Element", "Hazard"]] = 0


    st.markdown("Agricultural elements and the hazards affecting them")
    st.markdown("")

    # Use matplotlib inside a lock because it is not thread-safe.
    _lock = RendererAgg.lock
    with _lock:
        # Plot a heatmap of the risk category values.

        # Vertical size of heatmap is based on the number of element-hazard combinations.
        vertical_size = 1.5 + eh_grid.shape[0] * 0.3

        fig = plt.figure(figsize = (9.5, vertical_size))
        ax = sns.heatmap(
            eh_grid,
            vmin = 0, # Anchor colors on 0 and 4.
            vmax = 6,
            cbar = False, # Do not draw a color bar.
            cmap = "BuPu", # Use Blue for low values and Purple for high ones.
            annot = eh_display, # Write the data value in each cell.
            fmt = "", # This is set because the annotations are strings. It prevents an error.
            linewidths = 1, # Make gaps between cells.
        )

        # Set font size to 11 in all cells
        for text in ax.texts:
            text.set_fontsize(11)

        # Move x axis ticks to top
        ax.xaxis.tick_top()

        # Make ticks invisible but keep tick labels
        ax.tick_params(axis = "both", which = "both", length = 0)

        # Set size of x labels
        plt.xticks(rotation = 0, size = 10)

        # Remove y tick labels
        plt.yticks(ticks = [])

        # Store the heatmap as an image, then display the image in streamlit.
        # This makes the display size consistent.
        # If the figure is used, the chart will have a different size depending on the height-width proportion.
        chart = BytesIO()
        fig.savefig(chart, format = "png")
        st.image(chart)


    # Let the user select element-hazard combination.
    with st.sidebar:
        st.markdown("## Agricultural Element and Hazard")

        element_select = st.selectbox(
            label = "Element",
            options = elements.unique(),
        )

        hazard_select = st.selectbox(
            label = "Hazard",
            options = eh_combos.loc[
                eh_combos["Element"] == element_select,
                "Hazard"
            ]
        )

    st.markdown("---")
    st.markdown("Select an element and hazard in the sidebar to the left for more details.")
    st.markdown("# {}: {}".format(element_select, hazard_select))

    # List of key categories
    cat_list = [
        "Degree Of Impact Category",
        "Vulnerability Category",
        "Risk Category",
    ]

    # Boolean masks
    correct_element = (orig_df.columns.get_level_values("Element") == element_select)
    correct_hazard = (orig_df.columns.get_level_values("Hazard") == hazard_select)

    category_cols = (
        correct_element 
        & correct_hazard
        & pd.Series(orig_df.columns.get_level_values("Detail")).isin(cat_list).tolist()
    )

    # This df contains key categories for the barangay.
    key_categories = (
        orig_df
        .loc[
            barangay,
            category_cols
        ]
    )

    key_categories.index = key_categories.index.get_level_values("Detail")

    key_categories = key_categories.loc[cat_list] # Reorder by label

    st.markdown("## Key Categories")
    st.dataframe(key_categories)

    # From here, we prepare to get the key scores.

    # Boolean masks
    hazard_specific_scores = correct_hazard & (
        pd.Series(orig_df.columns.get_level_values("Detail"))
        .isin([
            "Likelihood Of Occurrence",
            "Exposure Score",
            "Degree Of Impact Score",
            "Severity Of Consequence Score",
            "Vulnerability Score",
            "Risk Score",
        ])
        .tolist()
    )
    # General scores are the same for all hazards under one element.
    general_scores = (
        (orig_df.columns.get_level_values("Hazard") == "All Hazards")
        & (
            pd.Series(orig_df.columns.get_level_values("Detail"))
            .isin([
                "Sensitivity Score",
                "Adaptive Capacity Score",
            ])
            .tolist()
        )
    )

    score_cols = (correct_element & (hazard_specific_scores | general_scores))

    # Series of key scores
    key_scores = orig_df.loc[
        barangay,
        score_cols
    ]

    key_scores.index = key_scores.index.get_level_values("Detail")

    key_scores.name = "Score"

    key_score_cols = orig_df.loc[:, score_cols]
    key_score_cols.columns = key_score_cols.columns.get_level_values("Detail")

    def get_brgy_percentile(col, barangay):
        """Take a Series of scores and a barangay name, which is part of the Series index.
    Return the percentile of the barangay's score as a string."""
        col = col.dropna()
        barangay_value = col[barangay]
        percentile = sum(col <= barangay_value) / len(col) * 100
        percentile = str(round(percentile, 2))

        return percentile

    # Series of percentiles
    key_score_percentiles = key_score_cols.apply(
        get_brgy_percentile,
        barangay = barangay,
        axis = 0,
    )

    key_score_percentiles.name = "Percentile"
    key_score_percentiles.index = key_score_percentiles.index.get_level_values("Detail")

    # df combining scores and percentiles
    key_score_df = pd.concat(
        [key_scores, key_score_percentiles],
        axis = 1,
    )

    # List of ll possible score labels. This is here for ordering the df rows.
    all_score_labels = [
        "Likelihood Of Occurrence",
        "Exposure Score",
        "Sensitivity Score",
        "Degree Of Impact Score",
        "Adaptive Capacity Score",
        "Vulnerability Score",
        "Severity Of Consequence Score",
        "Risk Score",
    ]

    # For scores that are missing for some reason, set their value to Unknown.

    for score_name in all_score_labels:
        if score_name not in key_score_df.index.tolist():
            new_row = pd.Series(
                [["Unknown", "Unknown"]],
                index = ["Score", "Percentile"],
                name = score_name,
            )
            key_score_df = key_score_df.append(new_row)

    key_score_df = key_score_df.loc[all_score_labels]

    # Display message and df of scores and percentiles.
    st.markdown("""## Key Scores""")
   
    st.dataframe(key_score_df)

    with st.expander("Help"):
        st.markdown("""Here is how the scores were calculated.

- Degree of Impact Score = mean(Exposure Score, Sensitivity Score)
- Vulnerability Score = Degree of Impact Score / Adaptive Capacity Score
- Risk Score = Severity of Consequence Score x Likelihood of Occurrence

Percentiles are given in comparison to other barangays with the same element and hazard combination. A percentile near 100 means that  the score is relatively high.""")

    with st.expander("Display Histograms"):

        st.caption("The red line in each histogram represents the score of {}.".format(barangay))

        # Make a 4 x 2 grid of histograms for the 8 scores.
        for grid_row in range(4):
            grid_columns = st.columns(2)

            col_num = -1
            df_part = key_score_df.iloc[grid_row * 2 : grid_row * 2 + 2]

            st.markdown("---")

            for score_name, row in df_part.iterrows():
                col_num += 1
                
                with grid_columns[col_num]:
                    score_value = row["Score"]
                    perc = "{}%".format(row["Percentile"])
                    if not isinstance(score_value, str):
                        score_value = round(score_value, 2)

                    st.markdown("{}: {}".format(score_name, score_value))
                    st.metric("Percentile", perc)

                    _lock = RendererAgg.lock
                    with _lock:
                        # Histogram with red line.

                        fig = plt.figure(figsize = (4.5, 3.5))

                        ax = sns.histplot(
                            key_score_cols,
                            x = score_name,
                            bins = 10,
                            fill = False,
                        )

                        # Red line indicating the barangay's score.
                        ax.axvline(x = score_value, color = "red")

                        # Make ticks invisible but keep tick labels
                        ax.tick_params(axis = "both", which = "both", length = 0)

                        # Make some spines invisible
                        for location in ["top", "right"]:
                            ax.spines[location].set_visible(False)

                        ax.set_xlabel(score_name, size = 12)
                        ax.set_ylabel("Count", size = 12)

                        # Store the graph as an image, then display the image in streamlit.
                        # This makes the display size consistent.
                        # If the figure is used, the chart will have a different size depending on the height-width proportion.
                        chart = BytesIO()
                        fig.savefig(chart, format = "png")
                        st.image(chart)
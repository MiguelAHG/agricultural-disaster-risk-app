import pandas as pd
import streamlit as st
import altair as alt
import matplotlib.pyplot as plt
import seaborn as sns

# For matplotlib charts
from matplotlib.backends.backend_agg import RendererAgg
from io import BytesIO

@st.cache_data(ttl = None)
def make_hierarchical(flat_df, mi_df):
    """Recreate the original hierarchical DataFrame."""

    orig_df = flat_df.copy().set_index("(Barangay)")
    mi_df = mi_df.drop(0, axis = 0)
    orig_df.columns = pd.MultiIndex.from_frame(mi_df)

    return orig_df

def barangay_summary_feature(mi_df, flat_df, db):
    """Barangay Data Summary feature."""

    # Make a hierarchically labeled DataFrame again.
    orig_df = make_hierarchical(flat_df, mi_df)

    st.title("Barangay Data Summaries")
    st.markdown("""This feature lets you select one barangay and get a summary of the most important data on agricultural disaster risk. Select a barangay from the options, or search for one by typing inside the box.""")
    st.caption("Only barangays where data is available can be selected.")

    # This only contains the barangays in the Sparta open data,
    # and not the ones from GADM.
    open_data_barangays = flat_df["(Barangay)"].tolist()

    # Let the user select a barangay.
    barangay = st.selectbox(
        label = "Select barangay",
        options = open_data_barangays,
    )

    # Geological areas affected by hazards
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

    # DataFrame of element and hazard combinations
    eh_combos = db["library"][["Element", "Hazard"]].drop_duplicates()

    eh_combos = eh_combos.loc[eh_combos["Hazard"] != "All Hazards"]

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

    eh_combos = eh_combos.dropna(subset = ["Vulnerability Category", "Risk Category"])

    # Create separate Series of elements and hazards.
    # This is done after dropping rows with nulls in Vulnerability Category and Risk Category.
    elements = eh_combos["Element"].copy()
    hazards = eh_combos["Hazard"].copy()

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

    st.markdown("---")
    st.markdown("# Agricultural Element and Hazard")
    st.markdown("Select an element and hazard for more details about how these affect the barangay.")

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

    st.markdown("## Risk of {} Against {}".format(element_select, hazard_select))



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

    st.markdown("### Key Categories")
    st.dataframe(key_categories)

    # Help box
    with st.expander("Info on Categories", expanded = False):
        st.markdown("""- Degree of Impact Category: This describes how greatly the element would be impacted if the hazard occurred. In other words, it describes potential damage.

- Vulnerability Category: This describes Degree of Impact while taking Adaptive Capacity into account. Vulnerability is lower if the barangay has better resources to prevent damage or recover from it.

- Risk Category: This describes how likely it is for the hazard to occur in the barangay, as well as how severe the consequence of the hazard may be.""")
    

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

    # Get percentile of selected barangay with respect to other barangays

    def get_brgy_percentile(col, barangay):
        """Take a Series of scores and a barangay name, which is part of the Series index.
    Return the percentile of the barangay's score as a string."""
        col = col.dropna()
        num_brgys = len(col)

        barangay_value = col[barangay]
        percentile = sum(col <= barangay_value) / num_brgys * 100
        percentile = str(round(percentile, 2))

        return percentile, num_brgys

    percentile_rows = []
    for col_name in key_score_cols.columns:
        col = key_score_cols[col_name].copy()
        percentile, num_brgys = get_brgy_percentile(col, barangay)
        new_percentile_row = pd.Series(
            {"Percentile": percentile, "Number of Barangays": num_brgys},
            name = col_name
        )
        percentile_rows.append(new_percentile_row)

    key_score_percentiles = pd.DataFrame(percentile_rows)


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
                [["Unknown", "Unknown", "Unknown"]],
                index = ["Score", "Percentile", "Number of Barangays"],
                name = score_name,
            )
            key_score_df = key_score_df.append(new_row)

    key_score_df = key_score_df.loc[all_score_labels]

    # Display message and df of scores and percentiles.
    st.markdown("""### Key Scores""")
   
    st.dataframe(key_score_df)

    # Help box
    with st.expander("Info on Scores"):
        st.markdown("""Here is how the scores were calculated.

- Degree of Impact Score = mean(Exposure Score, Sensitivity Score)
- Vulnerability Score = Degree of Impact Score / Adaptive Capacity Score
- Risk Score = Severity of Consequence Score x Likelihood of Occurrence

For each score, a percentile is given in comparison to other barangays (where applicable). A percentile near 100 means that  the score is relatively high. The 'Number of Barangays' column is provided to let you know how many barangays were involved in the calculations for percentiles.""")


    # Histogram feature
    st.markdown("## Histograms of Scores\n\nThese histograms can help see how high or low the score of {} is in comparison to other barangays' score.".format(barangay))

    with st.expander("Display Histograms"):

        st.markdown("The red line in each histogram represents the score of {}.\n\n---".format(barangay))

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

                    if score_value == "Unknown":
                        score_display = "Unknown"
                    else:
                        score_display = round(score_value, 2)
                    

                    st.markdown("{}: {}".format(score_name, score_display))
                    st.metric("Percentile", perc)

                    if score_value != "Unknown":

                        # Histogram layer
                        hist = (
                            alt.Chart(key_score_cols)
                            .mark_bar()
                            .encode(
                                x = alt.X(
                                    score_name,
                                    type = "quantitative",
                                    title = score_name,
                                    bin = True,
                                ),
                                y = alt.Y(
                                    "count()",
                                    title = "Count",
                                ),
                            )
                        )

                        # Red line layer
                        line = (
                            alt.Chart(key_score_cols)
                            .mark_rule(
                                color = "red",
                                size = 5,
                            )
                            .encode(
                                x = alt.X(score_name),
                            )
                            .transform_filter(
                                alt.datum[score_name] == score_value
                            )
                        )

                        # Combined layers
                        chart = (
                            (hist + line)
                            .properties(height = 200)
                        )

                        st.altair_chart(chart, use_container_width = True)
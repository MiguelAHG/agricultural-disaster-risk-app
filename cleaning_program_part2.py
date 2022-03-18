#%%
import pandas as pd
import numpy as np
import geopandas as gpd

#%%
combined_df = (
    pd.read_csv(
        "./cleaning_outputs/hierarchical_label_data.csv",
        header = list(range(5)),
        index_col = 0,
    )
    .drop(("(Barangay)", "None", "None", "None", "None"), axis = 1)
)

combined_df
# %%
gdf = gpd.read_file("geodata/gadm36_PHL.gpkg")

gdf
# %%
# Table of all barangays in Butuan City and their GIDs
# Names are based on GADM
def gid3_to_id(series):
    """Take a series and convert Butuan City barangays' GID_3 strings to ID code integers."""
    result = (
        series
        .str.extract(r"PHL.2.2.([0-9]+)_1", expand = False)
        .astype("int64")
    )
    return result

butuan_gid_2 = "PHL.2.2_1"

brgy_sheet = (
    gdf
    .loc[
        gdf["GID_2"] == butuan_gid_2,
        ["GID_3", "NAME_3"]
    ]
)

brgy_sheet["BID"] = gid3_to_id(brgy_sheet["GID_3"])

brgy_sheet
#%%
# Convert names to GIDs

# Read a CSV containing the GID of each barangay.
# Names here are based on the output hierarchical_label_data.csv, not GADM.
brgy_gids_df = pd.read_csv("./cleaning_inputs/barangay_GIDs_for_hierarchical_label_data.csv")

brgy_gids_dct = brgy_gids_df.set_index("orig_name").to_dict()["GID_3"]

# In combined_df's index, replace barangay names with their ID codes
new_index = gid3_to_id(
    combined_df
    .index
    .to_series()
    .replace(brgy_gids_dct)
)

new_index.name = "BID"

new_index
#%%
combined_df.index = new_index

combined_df.index
# %%
# Make a DataFrame representing column MultiIndex
mi_df = combined_df.columns.to_frame()

mi_df
#%%
# Make library sheet
library_sheet = (
    mi_df
    .drop(columns = "Detail")
    .drop_duplicates(keep = "first")
    .reset_index(drop = True)
)

# Sheet ID
library_sheet["SID"] = library_sheet.index.to_series().astype(str)

library_sheet
#%%
# Create dictionary
# Keys: int (SID)
# Values: DataFrame (data sheet)
sid_dct = {
    "library": library_sheet,
    "barangay_id": brgy_sheet,
}

upper_levels = ["Sector", "Element", "Hazard", "Disaster Risk Aspect"]

for index, row in library_sheet.iterrows():

    # Get sheet ID
    sid = row["SID"]

    # Make a list of boolean masks where the values are True for the matching items on each level
    masks = []
    for level_name in upper_levels:
        level_mask = combined_df.columns.get_level_values(level_name) == row[level_name]
        masks.append(level_mask)
    
    # Combine the masks into one final mask. The final mask is True for a column if all individual masks are True for that column.
    final_mask = masks[0]
    for level_mask in masks[1:]:
        final_mask = (final_mask & level_mask)

    data_sheet = (
        combined_df
        # Index the combined dataset by using the mask on the column axis
        .loc[:, final_mask]
        # Keep only the Detail level of the columns
        .droplevel(upper_levels, axis = 1)
        # Drop rows with all missing values
        .dropna(axis = 0, how = "all")
        # Make the index a column in the data sheet
        .reset_index(drop = False)
    )

    # Add sheet to the dictionary of all sheets
    sid_dct[sid] = data_sheet
#%%
# Save all sheets to one excel file
with pd.ExcelWriter(path = "./cleaning_outputs/divided_database.xlsx") as writer:

    for sid, sheet in sid_dct.items():
        sheet.to_excel(
            writer,
            sheet_name = sid,
            index = False,
        )
#%%
import pandas as pd
import numpy as np
import re
import os
import geopandas as gpd
import json
from pytopojson import topology

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

brgy_sheet["ID"] = gid3_to_id(brgy_sheet["GID_3"])

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

new_index
#%%
combined_df.index = new_index

combined_df.index
# %%

#%%
# Import packages
import pandas as pd
import numpy as np
import geopandas as gpd
import json
from pytopojson import topology

#%%
# Open geodata and convert geojson to topojson
# This is necessary for an Altair map
gdf = gpd.read_file("geodata/gadm36_PHL.gpkg")

gdf = (
    gdf
    .loc[gdf["NAME_2"] == "Butuan City"] # Get all Butuan City barangays
)

gdf["NAME_3"] = (
    gdf["NAME_3"]
    .str.title() # Title case
    .str.replace(" Poblacion", "", regex = False) # Delete Poblacion from barangay names
    .str.replace("ñ", "n", regex = False) # Use regular letter n
)

geo_str = gdf.to_json()
geo_dct = json.loads(geo_str)

tpg = topology.Topology()
topojson = tpg({"barangay_geodata": geo_dct})

with open("./geodata/barangay_topojson.json", "w") as f:
    json.dump(topojson, f, indent = 4)

#%%
# Open data again but save as GPKG
# Do not edit barangay names' spelling

gdf2 = gpd.read_file("geodata/gadm36_PHL.gpkg")

gdf2 = (
    gdf2
    .loc[gdf2["NAME_2"] == "Butuan City"] # Get all Butuan City barangays
)

# Save the Butuan City geodata to a GPKG file
gdf2.to_file("./geodata/gadm_butuan_city_barangays.gpkg")
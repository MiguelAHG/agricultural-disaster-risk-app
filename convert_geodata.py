import pandas as pd
import numpy as np
import geopandas as gpd
import json
from pytopojson import topology

# Open geodata
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

# Convert geojson to topojson
# This is necessary for the map
geo_str = gdf.to_json()
geo_dct = json.loads(geo_str)

tpg = topology.Topology()
topojson = tpg({"barangay_geodata": geo_dct})

with open("./geodata/barangay_topojson.json", "w") as f:
    json.dump(topojson, f, indent = 4)
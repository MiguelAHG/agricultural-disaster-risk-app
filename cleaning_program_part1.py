import pandas as pd
import numpy as np
import re
import os

def my_mkdir(subdir_str):
    """Make a subdirectory if it doesn't exist yet."""
    if not os.path.exists("./{}".format(subdir_str)):
        os.mkdir(subdir_str)

def make_list_uniform(lst):
    """Take a list of strings and make it uniform."""
    if (isinstance(lst, list)):
        result = [
            item.strip().upper() # Make the text uniform
            for item in lst
            if not re.match(r"^\s*$", item) # Remove blank strings
        ]
        return result
    else:
        return np.nan

if __name__ == "__main__":

    # Make a new directory for output files.
    my_mkdir("cleaning_outputs")

    element_groups = pd.read_excel("./cleaning_inputs/element_groups.xlsx")

    # Dict where cleaned datasets will be stored.
    cleaned_datasets = {}

    # Loop the code for each Excel file that will be cleaned.
    for index, group in element_groups.iterrows():

        # Get sector (e.g., agriculture) and element (e.g., livestock)
        sector_name, element_name = group["file_name"].split("_")
        
        # Read the Excel file into a Series of DataFrames.
        data = pd.read_excel(
            "./cleaning_inputs/{}.xlsx".format(group["file_name"]),
            sheet_name = None,
        )
        data = pd.Series(data)

        # Clean up the data dictionary.
        data.dictionary = (
            data.dictionary
            .iloc[
                :group["data_ncols"],
                :8 # Always take columns 0 to 7 for the data dictionary
            ]
            .fillna(0) # Fill nulls with zeros.
            .set_index("column_name") # Set column_name column as index
        )

        # Make the index of the data dictionary uniform.
        uniform_colnames = (
            data.dictionary.index
            .to_series()
            .str.strip()
            .str.title()
            .str.replace("/", "(slash)") # Replace slashes in column headers. This will be important for the web app.
        )

        # Include disaster risk aspect in the column names.
        data.dictionary.index = (
            data.dictionary["disaster_risk_aspect"]
            .str.cat(["/" for i in data.dictionary.index])
            .str.cat(uniform_colnames)
        )

        # Convert specific columns in the data dictionary to booleans
        for label in ["is_list", "drop", "unique"]:
            data.dictionary[label] = data.dictionary[label].astype(bool)

        # A list of columns that must be dropped from the data sheets.
        drop_cols = list(
            data.dictionary.index
            [data.dictionary["drop"]]
        )

        # A list of empty columns in the data sheets.
        empty_cols = list(
            data.dictionary.index
            [data.dictionary["data_type"] == "missing"]
        )

        # Edit the main sheets
        main_sheets = [sheet for sheet in data.index if sheet != "dictionary"]
        for sheet in main_sheets:

            # Limit the rows and columns in the DataFrame.
            # This is needed since reading an Excel file often results in extra empty rows and columns.
            data[sheet] = (
                data[sheet]
                .iloc[
                    :group["data_nrows"],
                    :group["data_ncols"]
                ]
            )

            # Set the sheet's columns to the uniformly formatted labels in the data dictionary.
            data[sheet].columns = data.dictionary.index

            # Make the barangay names uniformly formatted.
            data[sheet]["Index/Barangay"] = (
                data[sheet]["Index/Barangay"]
                .str.strip()
                .str.title()
            )

            # Edit the sheet.
            data[sheet] = (
                data[sheet]
                .set_index("Index/Barangay") # Set barangay as the DF's index
                .sort_index()
                .drop( # Drop unnecessary columns
                    drop_cols + empty_cols,
                    axis = 1,
                )
            )
            
            # Find text columns and make their text uniform (strip extra whitespace and use title case).
            
            text_cols = (
                data[sheet]
                .select_dtypes(include = "object")
                .columns
                .tolist()
            )
            
            for text_col in text_cols:
                data[sheet][text_col] = (
                    data[sheet][text_col]
                    .str.strip() # Remove extra whitespace.
                    .str.title() # Use title case.
                )

        # Drop rows from the data dictionary.
        data.dictionary = data.dictionary.drop(
            drop_cols + empty_cols,
            axis = 0,
        )

        # Create general_df, a DataFrame that contains the columns that are common to
        # all of the data sheets under the same element.

        reference_sheet = group["reference_sheet"]

        unique_list = list(
            data.dictionary.index
            [data.dictionary["unique"]]
        )

        general_df = data[reference_sheet].drop(
            unique_list,
            axis = 1,
        )

        # Remove the general columns from the main sheets
        for sheet in main_sheets:
            data[sheet] = data[sheet].loc[:, unique_list]

            # Append the row below for MultiIndex purposes later on
            hazard_row = pd.Series(
                {label: sheet for label in data[sheet].columns},
                name = "Hazard",
            )

            data[sheet] = data[sheet].append(hazard_row)
            
        # Identify columns in general_df containing lists
        list_cols = (
            data.dictionary.index
            [data.dictionary["is_list"]]
            .tolist()
        )           

        # Clean up list columns and convert them.
        for orig_name in list_cols:
            # Make a deep copy of the original column, and edit it.
            col_copy = (
                general_df[orig_name]
                .str.strip()
                .str.cat(["," for i in range(len(general_df))]) # Append a comma at the end of each string
                .str.replace("\n", ",") # Replace newlines with commas
                .str.replace(r"s(?=,)", "", regex = True) # Delete trailing s characters
                .str.split(",").copy() # Split on commas
                .apply(make_list_uniform)
            ).copy()

            # Dict that will contain the new columns that will be generated.
            new_dct = {}

            # Iterate over the column. Each value is a list object.
            for index, lst in col_copy.iteritems():
                if not isinstance(lst, list):
                    continue
                for item in lst:
                    # New column name
                    new_name = "{}_{}".format(orig_name, item)

                    # If the key doesn't exist yet, create it and make a new column of No values.
                    # Set the relevant cell to Yes.
                    new_dct.setdefault(new_name, col_copy.apply(lambda x: "No"))
                    new_dct[new_name][index] = "Yes"

            # Make the dict a DataFrame.
            new_df = pd.DataFrame(new_dct)
            
            # Save new columns as a CSV for manual checking.
            # This is commented since it is no longer needed.

            # new_df.to_csv("./cleaning_outputs/{sector}_{element}_{orig}.csv".format(
            #     sector = sector_name,
            #     element = element_name,
            #     orig = orig_name,
            # ))

            general_df = (
                general_df
                .drop(orig_name, axis = 1) # Drop original column
                .merge(
                    new_df,
                    how = "left", # Left join to keep all existing data
                    left_index = True,
                    right_index = True,
                )
                .sort_index(axis = 1)
            )
        
        # Row that indicates that the information is general and not specific to any hazard.
        # This row will eventually be part of the column MultiIndex.
        general_row = pd.Series(
            {label: "All Hazards" for label in general_df.columns},
            name = "Hazard",
        )
        general_df = general_df.append(general_row)

        # Combine the general columns and the unique columns
        to_combine = [general_df] + [data[sheet] for sheet in main_sheets]

        combined_df = pd.concat(
            to_combine,
            axis = 1,
            join = "outer",
        )
        
        # Append the 3 rows below so that they can be part of a MultiIndex later on.

        sector_row = pd.Series(
            {label: sector_name for label in combined_df.columns},
            name = "Sector",
        )

        element_row = pd.Series(
            {label: element_name for label in combined_df.columns},
            name = "Element",
        )

        detail_row = pd.Series(
            combined_df.columns,
            index = combined_df.columns,
            name = "Detail",
        )

        combined_df = (
            combined_df
            .append(element_row)
            .append(sector_row)
            .append(detail_row)
        )

        # Create a horizontal MultiIndex in combined_df.

        # Levels of the MultiIndex
        mi_levels = ["Sector", "Element", "Hazard", "Detail"]

        # Make an array that will serve as the template for the MultiIndex.
        multiindex_array = (
            combined_df
            .loc[mi_levels]
            .to_numpy()
        )

        # Set the MultiIndex horizontally.
        combined_df.columns = pd.MultiIndex.from_arrays(
            multiindex_array,
            names = mi_levels, # Give a name to each level in the MultiIndex.
        )
        
        combined_df = (
            combined_df
            .drop(mi_levels, axis = 0) # Drop the rows that were used for the MultiIndex.
            .dropna(axis = 1, how = "all") # Drop columns that are filled completely with null values.
            .sort_index(axis = 0) # Sort the MultiIndex rows and columns.
            .sort_index(axis = 1)
        )

        # Put the combined DataFrame into the cleaned_datasets dict.
        key = group["file_name"]
        cleaned_datasets[key] = combined_df

    # Get a list containing the cleaned DataFrames.
    element_dfs = list(cleaned_datasets.values())

    # Combine all of the DataFrames into one big one.
    full_data = pd.concat(
        element_dfs,
        axis = 1,
        join = "outer",
    )

    # Edit the MultiIndex to include a Disaster Risk Aspect level.
    mi_df = full_data.columns.to_frame()

    def split_slash(text, get = 0):
        """Take a string, split it on slashes, and return an element at a certain index in the list."""
        contents = text.split("/")
        return contents[get]

    mi_df["Disaster Risk Aspect"] = mi_df["Detail"].apply(split_slash, get = 0)
    mi_df["Detail"] = mi_df["Detail"].apply(split_slash, get = 1)

    # Reorder the levels to be used in the MultiIndex.
    mi_df = mi_df[["Sector", "Element", "Hazard", "Disaster Risk Aspect", "Detail"]]

    full_data.columns = pd.MultiIndex.from_frame(mi_df)

    # Include Barangay as a column.
    brgy_mi = tuple(["(Barangay)"] + ["None" for i in range(len(full_data.columns[0]) - 1)])
    full_data[brgy_mi] = full_data.index

    # Sort full_data's columns and indices.
    full_data = (
        full_data
        .sort_index(axis = 0)
        .sort_index(axis = 1)
    )


    #------
    # Make mi_df, flat_df, gdf

    orig_df = full_data

    # DataFrame of the MultiIndex columns
    mi_df = orig_df.columns.to_frame()

    # Edit the indices so that there are no dots or brackets. These can cause semantic errors in Altair.
    for mi_level in mi_df.columns:
        mi_df[mi_level] = (
            mi_df[mi_level]
            .str.replace(".", "", regex = False)
            .str.replace("[\[\]]", "", regex = True)
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

    # Rename barangay column so it is shorter.
    flat_df = flat_df.rename(
        {"(Barangay)/None/None/None/None": "(Barangay)"},
        axis = 1,
    )

    # Save files

    mi_df.to_csv("./cleaning_outputs/multiindex_frame.csv", index = False)
    flat_df.to_csv("./cleaning_outputs/flat_label_data.csv")

    full_data.to_csv("./cleaning_outputs/hierarchical_label_data.csv")
    full_data.to_excel("./cleaning_outputs/hierarchical_label_data.xlsx")
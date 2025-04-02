import pandas as pd

def load_station_inventory(file_path="ghcnd-stations.txt"):
    # Read the file with only the necessary columns: 'ID' (station code) and 'State'
    colspecs = [(0, 11)]  # Only the station code, 11 characters
    columns = ["ID"]
    df_stations = pd.read_fwf(file_path, colspecs=colspecs, header=None, names=columns)
    
    # Loop through each station code and extract the state abbreviation dynamically
    state_abbr_list = []

    for station_code in df_stations["ID"]:
        # After the station code, find the first two alphabetic characters
        state_abbr = ''.join([char for char in station_code[2:] if char.isalpha()][:2])  # Take the first two letters
        
        # Append the state abbreviation to the list
        state_abbr_list.append(state_abbr)

    # Add the state abbreviation list as a new column
    df_stations["State_Abbr"] = state_abbr_list

    # Convert the DataFrame to a string representation, row by row
    df_as_string = df_stations.to_string(index=False)

    return df_as_string

# Example usage
station_data_str = load_station_inventory("ghcnd-stations.txt")
print(station_data_str)

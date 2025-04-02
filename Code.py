import pandas as pd
import us
import streamlit as st

def load_station_inventory(file_path="ghcnd-stations.txt"):
    try:
        # Read the fixed-width file with specific column widths for station code and state
        colspecs = [(0, 11)]  # Station code length (11 characters)
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

        # Filter rows where ID starts with 'USC00'
        df_stations = df_stations[df_stations["ID"].str.startswith("USC00")]

        # Return the dataframe so we can display it in Streamlit
        return df_stations

    except Exception as e:
        st.error(f"Error loading the station inventory: {e}")
        return None

# Streamlit UI elements
st.title("Station Inventory with State Abbreviations")

# Display instructions
st.markdown("""
This table shows the **station ID** and the corresponding **state abbreviation** extracted from the station codes. 
Only stations with an ID starting with "USC00" are included.
""")

# Example usage
file_path = "ghcnd-stations.txt"  # File path to the uploaded stations file
df_stations = load_station_inventory(file_path)

if df_stations is not None:
    # Display the table in Streamlit
    st.subheader("Station Inventory Table (ID starts with 'USC00')")
    st.dataframe(df_stations[["ID", "State_Abbr"]])  # Display only ID and State_Abbr columns
else:
    st.write("No data to display.")

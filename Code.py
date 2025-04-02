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

        # Filter rows where ID starts with 'US'
        df_stations = df_stations[df_stations["ID"].str.startswith("US")]

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
Only stations with an ID starting with "US" are included.
""")

# Example usage
file_path = "ghcnd-stations.txt"  # File path to the uploaded stations file
df_stations = load_station_inventory(file_path)

if df_stations is not None:
    # Display the table in Streamlit
    st.subheader("Station Inventory Table (ID starts with 'US')")
    st.dataframe(df_stations[["ID", "State_Abbr"]])  # Display only ID and State_Abbr columns
else:
    st.write("No data to display.")

# Function to load climate data and extract specific columns
def load_climate_data(file_path="Climate data.csv"):
    try:
        # Load the climate data CSV
        df = pd.read_csv(file_path)
        
        # Extract the necessary columns
        df_climate = df[["STATION", "DATE", "PRCP", "TAVG"]]
        
        # Return the filtered dataframe
        return df_climate

    except Exception as e:
        st.error(f"Error loading the climate data: {e}")
        return None

# Streamlit UI elements
st.title("Climate Data Extraction")

# Display instructions
st.markdown("""
This table shows the **station code**, **date**, **precipitation (PRCP)**, and **temperature (TAVG)** extracted from the climate dataset.
""")

# Example usage
file_path = "Climate data.csv"  # File path to the uploaded climate data file
df_climate = load_climate_data(file_path)

if df_climate is not None:
    # Display the filtered data in Streamlit
    st.subheader("Filtered Climate Data")
    st.dataframe(df_climate)  # Display only the required columns
else:
    st.write("No data to display.")


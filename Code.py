import pandas as pd
import us
import streamlit as st

# Function to load the processed station data
def load_processed_station_data(file_path="ghcnd-stations-processed.txt"):
    try:
        # Read the data from the file
        df = pd.read_csv(file_path, header=None, names=["ID", "State_Abbr"], sep=" ")
        
        return df
    except Exception as e:
        st.error(f"Error loading the processed station data: {e}")
        return None

# Streamlit UI elements
st.title("Processed Station Data")

# Display instructions
st.markdown("""
This table shows the **station ID** and the corresponding **state abbreviation (State_Abbr)** extracted from the processed station file.
""")

# Example usage
file_path = "ghcnd-stations-processed.txt"  # File path to the uploaded processed file
df_stations = load_processed_station_data(file_path)

if df_stations is not None:
    # Display the table in Streamlit
    st.subheader("Processed Station Data")
    st.dataframe(df_stations)  # Display the table with ID and State_Abbr columns
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

# Streamlit UI elements
st.title("Climate Data with State Abbreviations")

# Display instructions
st.markdown("""
This table shows the **station code**, **date**, **precipitation (PRCP)**, and **temperature (TAVG)** extracted from the climate dataset.
We have replaced the **station code (STATION)** with the **state abbreviation (State_Abbr)**.
""")

# Load the data
file_path_stations = "ghcnd-stations-processed.txt"  # File path to the uploaded stations file
file_path_climate = "Climate data.csv"  # File path to the uploaded climate data file

df_stations = load_processed_station_data(file_path_stations)
df_climate = load_climate_data(file_path_climate)

if df_stations is not None and df_climate is not None:
    # Merge the climate data with the station data on 'STATION' and 'ID'
    df_merged = pd.merge(df_climate, df_stations[['ID', 'State_Abbr']], left_on='STATION', right_on='ID', how='left')
    
    # Drop the 'ID' column as it is no longer needed
    df_merged = df_merged.drop(columns=['ID'])

    # Sort the merged dataframe by state abbreviation
    df_sorted = df_merged.sort_values(by='State_Abbr')
    
    # Display the new table in Streamlit
    st.subheader("Climate Data with State Abbreviation")
    st.dataframe(df_merged[["State_Abbr", "DATE", "PRCP", "TAVG"]])  # Display the updated table with State_Abbr

else:
    st.write("No data to display.")


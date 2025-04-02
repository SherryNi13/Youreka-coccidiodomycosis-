import streamlit as st
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import seaborn as sns
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import us

st.title("Coccidioidomycosis & Climate Analysis with Station Mapping")

# Load NOAA Station Data (converted to state names)
@st.cache_data
def load_station_inventory(file_path="ghcnd-stations.txt"):
    colspecs = [(0, 11), (38, 68)]  # Only read 'ID' and 'Station_Name'
    columns = ["ID", "Station_Name"]
    df_stations = pd.read_fwf(file_path, colspecs=colspecs, header=None, names=columns)
    df_stations["Station_Name"] = df_stations["Station_Name"].str.strip()
    df_stations["State_Full"] = df_stations["Station_Name"].apply(lambda x: us.states.lookup(x.split()[-1]).name if x.split()[-1] else "")
    return df_stations

# Example usage
df_stations = load_station_inventory()
print(df_stations.head())
'''
st.write("Station Data Loaded:", df_stations.head())

# Load and Clean Coccidioidomycosis Data
@st.cache_data
def load_disease_data(file_path="Climate data.csv"):
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    df.rename(columns={
        "Mmwryear": "MMWR Year",
        "AsIr_2019": "ASIR",
        "Temperature": "TAVG",
        "Avg_Humidity": "Humidity",
        "Precipitation": "PRCP",
        "Station": "STATION"
    }, inplace=True)
    return df

df_disease = load_disease_data()
st.write("Disease Data Loaded:", df_disease.head())

# Merge the climate data with the station inventory (using the STATION ID to map to State_Full)
df_merged = pd.merge(df_disease, df_stations[["ID", "State_Full"]], left_on="STATION", right_on="ID", how="left")

# Renaming columns to match the datasets from 2014-2022 and the climate station dataset
new_column_names = {
    "STATION": "Station_ID",
    "DATE": "Date",
    "HN01": "High_Temperature",
    "LN01": "Low_Temperature",
    "PRCP": "Precipitation",
    "TAVG": "Average_Temperature",
    "ID": "Identifier",
    "State_Full": "Full_State_Name"
}

df_merged.rename(columns=new_column_names, inplace=True)

st.write("Merged DataFrame:", df_merged.head())

# Check the columns in df_merged
st.write("Columns in df_merged:", df_merged.columns.tolist())

# Now try to display the dataframe
st.subheader("Merged Dataset: Coccidioidomycosis & Climate Data")
try:
    st.dataframe(df_merged[["Station_ID", "Date", "High_Temperature", "Low_Temperature", "Precipitation", "Average_Temperature", "Identifier", "Full_State_Name"]].dropna().reset_index(drop=True))
except KeyError as e:
    st.error(f"KeyError: {e}. Available columns in df_merged: {df_merged.columns.tolist()}")

'''
'''
# Regression analysis
st.header("Regression Analysis: Climate Parameters vs. ASIR")

# Ensure necessary columns are present
required_columns = ["High_Temperature", "Low_Temperature", "Average_Temperature", "Precipitation"]
if not all(col in df_merged.columns for col in required_columns):
    st.error(f"Missing columns for regression: {', '.join([col for col in required_columns if col not in df_merged.columns])}")
else:
    # Simple Linear Regression: High_Temperature ~ Average_Temperature
    model_temp = smf.ols("High_Temperature ~ Average_Temperature", data=df_merged).fit()
    st.subheader("Simple Regression: High_Temperature ~ Average_Temperature")
    st.text(model_temp.summary())
    fig_reg_temp, ax_reg_temp = plt.subplots(figsize=(8, 6))
    sns.regplot(x="Average_Temperature", y="High_Temperature", data=df_merged, ax=ax_reg_temp)
    ax_reg_temp.set_title("High_Temperature vs Average_Temperature (°F)")
    st.pyplot(fig_reg_temp)

    # Simple Linear Regression: High_Temperature ~ Precipitation
    model_hum = smf.ols("High_Temperature ~ Precipitation", data=df_merged).fit()
    st.subheader("Simple Regression: High_Temperature ~ Precipitation")
    st.text(model_hum.summary())
    fig_reg_hum, ax_reg_hum = plt.subplots(figsize=(8, 6))
    sns.regplot(x="Precipitation", y="High_Temperature", data=df_merged, ax=ax_reg_hum)
    ax_reg_hum.set_title("High_Temperature vs Precipitation")
    st.pyplot(fig_reg_hum)

    # Multiple Regression: High_Temperature ~ Average_Temperature + Precipitation
    formula = "High_Temperature ~ Average_Temperature + Precipitation"
    model_multi = smf.ols(formula, data=df_merged).fit()
    st.subheader("Multiple Regression")
    st.write("Formula used:", formula)
    st.text(model_multi.summary())
    
    st.subheader("Scatter Plots for Predictors")
    for var in ["Average_Temperature", "Precipitation"]:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.regplot(x=var, y="High_Temperature", data=df_merged, ax=ax)
        ax.set_title(f"High_Temperature vs {var}")
        st.pyplot(fig)
'''

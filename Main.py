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
    colspecs = [(0, 11), (12, 20), (21, 30), (31, 37), (38, 68), (69, 71), (72, 75), (76, 79), (80, 85)]
    columns = ["ID", "Latitude", "Longitude", "Elevation", "Station_Name", "State", "GSN_Flag", "HCN_Flag", "WMO_ID"]
    df_stations = pd.read_fwf(file_path, colspecs=colspecs, header=None, names=columns)
    df_stations["State"] = df_stations["State"].str.strip()
    df_stations["Latitude"] = pd.to_numeric(df_stations["Latitude"], errors="coerce")
    df_stations["Longitude"] = pd.to_numeric(df_stations["Longitude"], errors="coerce")
    df_stations["State_Full"] = df_stations["State"].apply(lambda x: us.states.lookup(x).name if x else "")
    return df_stations

df_stations = load_station_inventory()
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
st.write("Merged DataFrame:", df_merged.head())

# Check the columns in df_merged
st.write("Columns in df_merged:", df_merged.columns.tolist())

# Now try to display the dataframe
st.subheader("Merged Dataset: Coccidioidomycosis & Climate Data")
try:
    st.dataframe(df_merged[["STATION", "MMWR Year", "ASIR", "State_Full", "TAVG", "Humidity", "PRCP"]].dropna().reset_index(drop=True))
except KeyError as e:
    st.error(f"KeyError: {e}. Available columns in df_merged: {df_merged.columns.tolist()}")

# Regression analysis
st.header("Regression Analysis: Climate Parameters vs. ASIR")

# Ensure necessary columns are present
required_columns = ["ASIR", "TAVG", "Humidity", "PRCP"]
if not all(col in df_merged.columns for col in required_columns):
    st.error(f"Missing columns for regression: {', '.join([col for col in required_columns if col not in df_merged.columns])}")
else:
    # Simple Linear Regression: ASIR ~ TAVG
    model_temp = smf.ols("ASIR ~ TAVG", data=df_merged).fit()
    st.subheader("Simple Regression: ASIR ~ TAVG")
    st.text(model_temp.summary())
    fig_reg_temp, ax_reg_temp = plt.subplots(figsize=(8, 6))
    sns.regplot(x="TAVG", y="ASIR", data=df_merged, ax=ax_reg_temp)
    ax_reg_temp.set_title("ASIR vs TAVG (°F)")
    st.pyplot(fig_reg_temp)

    # Simple Linear Regression: ASIR ~ Humidity
    model_hum = smf.ols("ASIR ~ Humidity", data=df_merged).fit()
    st.subheader("Simple Regression: ASIR ~ Humidity")
    st.text(model_hum.summary())
    fig_reg_hum, ax_reg_hum = plt.subplots(figsize=(8, 6))
    sns.regplot(x="Humidity", y="ASIR", data=df_merged, ax=ax_reg_hum)
    ax_reg_hum.set_title("ASIR vs Humidity")
    st.pyplot(fig_reg_hum)

    # Multiple Regression: ASIR ~ TAVG + Humidity + PRCP
    formula = "ASIR ~ TAVG + Humidity + PRCP"
    model_multi = smf.ols(formula, data=df_merged).fit()
    st.subheader("Multiple Regression")
    st.write("Formula used:", formula)
    st.text(model_multi.summary())
    
    st.subheader("Scatter Plots for Predictors")
    for var in ["TAVG", "Humidity", "PRCP"]:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.regplot(x=var, y="ASIR", data=df_merged, ax=ax)
        ax.set_title(f"Coccidioidomycosis vs {var}")
        st.pyplot(fig)

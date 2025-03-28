import streamlit as st
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import seaborn as sns
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import us

st.title("Climate & Coccidioidomycosis Regression Analysis with Station Mapping")

st.markdown("""
This app:
- Reads NOAA’s station inventory (ghcnd-stations.txt) and converts station IDs to locations (states).
- Loads climate and coccidioidomycosis case data (Climate data.csv) and merges it with station info.
- Runs regression analyses (simple & multiple) using ASIR as the dependent variable and climate parameters (TAVG, Humidity, PRCP) as predictors.
""")

###############################
# 1. Process NOAA Station Data
###############################

st.header("NOAA Station Inventory Conversion")

# Define fixed-width file column specifications for ghcnd-stations.txt.
colspecs = [(0,11), (12,20), (21,30), (31,37), (38,68), (69,71), (72,75), (76,79), (80,85)]
columns = ["ID", "Latitude", "Longitude", "Elevation", "Station_Name", "State", "GSN_Flag", "HCN_Flag", "WMO_ID"]

@st.cache_data(show_spinner=False)
def load_station_inventory(file_path="ghcnd-stations.txt"):
    df_stations = pd.read_fwf(file_path, colspecs=colspecs, header=None, names=columns)
    # Strip whitespace from text columns.
    df_stations["ID"] = df_stations["ID"].str.strip()
    df_stations["Station_Name"] = df_stations["Station_Name"].str.strip()
    df_stations["State"] = df_stations["State"].str.strip()
    # Convert numeric columns.
    df_stations["Latitude"] = pd.to_numeric(df_stations["Latitude"], errors="coerce")
    df_stations["Longitude"] = pd.to_numeric(df_stations["Longitude"], errors="coerce")
    df_stations["Elevation"] = pd.to_numeric(df_stations["Elevation"], errors="coerce")
    return df_stations

df_stations = load_station_inventory()

# Set up geolocator for reverse geocoding (for missing state info).
geolocator = Nominatim(user_agent="ghcnd_station_geocoder")
geocode = RateLimiter(geolocator.reverse, min_delay_seconds=1)

def get_state_from_coords(row):
    # Only attempt reverse geocoding if state field is missing.
    if row["State"]:
        return row["State"]
    try:
        location = geocode((row["Latitude"], row["Longitude"]))
        if location:
            address = location.raw.get("address", {})
            return address.get("state", "")
    except Exception:
        return ""
    return ""

# For U.S. stations missing a state code, try to fill it via reverse geocoding.
mask_missing_state = df_stations["State"] == ""
if mask_missing_state.any():
    st.write("Reverse geocoding missing U.S. state codes (this may take a while)...")
    df_stations.loc[mask_missing_state, "State"] = df_stations[mask_missing_state].apply(get_state_from_coords, axis=1)

# Convert U.S. state abbreviations to full names using the us library.
def state_abbr_to_full(state_value):
    st_obj = us.states.lookup(state_value)
    return st_obj.name if st_obj else state_value

df_stations["State_Full"] = df_stations["State"].apply(state_abbr_to_full)

st.dataframe(df_stations.head(10))

##########################################
# 2. Load Climate and Coccidioidomycosis Data
##########################################

st.header("Climate & Coccidioidomycosis Data")

@st.cache_data(show_spinner=False)
def load_climate_data(file_path="Climate data.csv"):
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    return df

try:
    df_climate = load_climate_data()
    st.success("Climate data loaded successfully.")
except Exception as e:
    st.error(f"Error loading climate data: {e}")

st.subheader("Climate Data Preview")
st.dataframe(df_climate.head())

# We assume the climate data has a "STATION" column that corresponds to NOAA station IDs.
if "STATION" not in df_climate.columns:
    st.error("The climate data must contain a 'STATION' column.")
else:
    # Merge station inventory into climate data.
    df_merged = pd.merge(df_climate, df_stations[["ID", "State_Full"]], left_on="STATION", right_on="ID", how="left")
    st.subheader("Merged Data Preview (Climate + Station Info)")
    st.dataframe(df_merged.head())

##########################################
# 3. Regression Analysis
##########################################

st.header("Regression Analysis")

# For regression, we require the following columns:
# - ASIR: dependent variable (cases incidence)
# - TAVG: average annual temperature (°F)
# - Humidity: (assumed to be in the data)
# - PRCP: total annual precipitation (inches)
required_cols = ["ASIR", "TAVG", "Humidity", "PRCP"]

missing = [col for col in required_cols if col not in df_merged.columns]
if missing:
    st.error(f"Missing required columns for regression: {missing}. Please check your Climate data CSV.")
else:
    st.success("All required regression columns found.")

    # ---- Simple Linear Regression for Temperature (TAVG) ----
    model_temp = smf.ols("ASIR ~ TAVG", data=df_merged).fit()
    st.subheader("Simple Linear Regression: ASIR ~ TAVG")
    st.text(model_temp.summary())

    fig_temp, ax_temp = plt.subplots(figsize=(8, 6))
    sns.regplot(x="TAVG", y="ASIR", data=df_merged, ax=ax_temp)
    ax_temp.set_title("ASIR vs Average Temperature (°F)")
    st.pyplot(fig_temp)

    # ---- Simple Linear Regression for Humidity ----
    model_hum = smf.ols("ASIR ~ Humidity", data=df_merged).fit()
    st.subheader("Simple Linear Regression: ASIR ~ Humidity")
    st.text(model_hum.summary())

    fig_hum, ax_hum = plt.subplots(figsize=(8, 6))
    sns.regplot(x="Humidity", y="ASIR", data=df_merged, ax=ax_hum)
    ax_hum.set_title("ASIR vs Humidity")
    st.pyplot(fig_hum)

    # ---- Multiple Linear Regression ----
    formula = "ASIR ~ TAVG + Humidity + PRCP"
    model_multi = smf.ols(formula, data=df_merged).fit()
    st.subheader("Multiple Linear Regression")
    st.write("Formula used:", formula)
    st.text(model_multi.summary())

    # ---- Separate Scatter Plots for Each Predictor ----
    st.subheader("Scatter Plots for Climate Parameters")
    for var in ["TAVG", "Humidity", "PRCP"]:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.regplot(x=var, y="ASIR", data=df_merged, ax=ax)
        ax.set_title(f"ASIR vs {var}")
        st.pyplot(fig)

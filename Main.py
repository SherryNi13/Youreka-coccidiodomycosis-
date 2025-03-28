import streamlit as st
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import seaborn as sns
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import us

st.title("Coccidioidomycosis & Climate Analysis with Station Mapping")

st.markdown("""
This app performs the following tasks:
1. Loads NOAA’s station inventory and translates station IDs into state names.
2. Loads a cleaned coccidioidomycosis & climate dataset (2014–2022), renames its columns as needed,
   and merges it with the station inventory.
3. Displays the merged dataset for case numbers by year (with state names), and lets you view a trendline
   graph of ASIR for a selected state.
4. Displays the translated (merged) climate dataset.
5. Generates regression line graphs (and summaries) using climate parameters (TAVG, Humidity, PRCP) versus ASIR.
""")

####################################
# Section 1: Process NOAA Station Data
####################################
st.header("1. NOAA Station Inventory Conversion")

# Define fixed-width column specifications per ghcnd-stations.txt.
colspecs = [(0, 11), (12, 20), (21, 30), (31, 37), (38, 68), (69, 71), (72, 75), (76, 79), (80, 85)]
columns = ["ID", "Latitude", "Longitude", "Elevation", "Station_Name", "State", "GSN_Flag", "HCN_Flag", "WMO_ID"]

@st.cache_data
def load_station_inventory(file_path="ghcnd-stations.txt"):
    df_stations = pd.read_fwf(file_path, colspecs=colspecs, header=None, names=columns)
    df_stations["ID"] = df_stations["ID"].str.strip()
    df_stations["Station_Name"] = df_stations["Station_Name"].str.strip()
    df_stations["State"] = df_stations["State"].str.strip()
    df_stations["Latitude"] = pd.to_numeric(df_stations["Latitude"], errors="coerce")
    df_stations["Longitude"] = pd.to_numeric(df_stations["Longitude"], errors="coerce")
    df_stations["Elevation"] = pd.to_numeric(df_stations["Elevation"], errors="coerce")
    return df_stations

df_stations = load_station_inventory()

# Set up geolocator and rate limiter for reverse geocoding.
geolocator = Nominatim(user_agent="ghcnd_station_geocoder")
geocode = RateLimiter(geolocator.reverse, min_delay_seconds=1)

def get_state_from_coords(row):
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

# Fill missing state codes via reverse geocoding.
mask_missing = df_stations["State"] == ""
if mask_missing.any():
    st.write("Reverse geocoding missing state codes (this may take some time)...")
    df_stations.loc[mask_missing, "State"] = df_stations[mask_missing].apply(get_state_from_coords, axis=1)

def state_abbr_to_full(state_value):
    # Updated function to handle missing or non-string values.
    if not isinstance(state_value, str) or not state_value.strip():
        return ""
    st_obj = us.states.lookup(state_value)
    return st_obj.name if st_obj else state_value

df_stations["State_Full"] = df_stations["State"].apply(state_abbr_to_full)

st.subheader("Station Inventory Sample")
st.dataframe(df_stations.head(10))

####################################
# Section 2: Load & Merge Disease/Climate Data
####################################
st.header("2. Load and Merge Coccidioidomycosis Data")

@st.cache_data
def load_disease_data(file_path="Climate data.csv"):
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    # Debug: show original column names.
    st.write("Original climate data columns:", df.columns.tolist())
    # Rename columns to match the names expected by the app.
    df.rename(columns={
        "Mmwryear": "MMWR Year",
        "AsIr_2019": "ASIR",
        "Temperature": "TAVG",
        "Avg_Humidity": "Humidity",
        "Precipitation": "PRCP",
        "Station": "STATION"
    }, inplace=True)
    st.write("Renamed climate data columns:", df.columns.tolist())
    return df

try:
    df_disease = load_disease_data()
    st.success("Disease data loaded successfully.")
except Exception as e:
    st.error(f"Error loading disease data: {e}")

st.subheader("Disease Data Sample")
st.dataframe(df_disease.head())

# Merge disease data with station inventory (using station ID).
if "STATION" not in df_disease.columns:
    st.error("Disease data must include a 'STATION' column.")
else:
    df_merged = pd.merge(df_disease, df_stations[["ID", "State_Full"]], left_on="STATION", right_on="ID", how="left")
    st.subheader("Merged Dataset: Case Numbers by Year and State")
    st.dataframe(df_merged[["STATION", "MMWR Year", "ASIR", "State_Full"]].dropna().reset_index(drop=True))

####################################
# Section 3: Trendline Graph for Disease Data
####################################
st.header("3. Coccidioidomycosis Trendline Graph by State")

# Check that the merged data contains the required columns.
if not {"MMWR Year", "ASIR", "State_Full"}.issubset(df_merged.columns):
    st.error("Merged data must include 'MMWR Year', 'ASIR', and 'State_Full' columns.")
else:
    states = sorted(df_merged["State_Full"].dropna().unique())
    selected_state = st.selectbox("Select a state to view its trend:", states)
    df_state = df_merged[df_merged["State_Full"] == selected_state].sort_values("MMWR Year")
    if df_state.empty:
        st.warning("No data available for the selected state.")
    else:
        fig_trend, ax_trend = plt.subplots(figsize=(8, 6))
        ax_trend.plot(df_state["MMWR Year"], df_state["ASIR"], marker="o", linestyle="-")
        ax_trend.set_title(f"ASIR Trend in {selected_state} (2014-2022)")
        ax_trend.set_xlabel("MMWR Year")
        ax_trend.set_ylabel("ASIR")
        st.pyplot(fig_trend)

####################################
# Section 4: Display Translated Climate Dataset
####################################
st.header("4. Translated Climate Dataset")
# Display the full merged dataset (which now includes climate parameters and station state info).
st.dataframe(df_merged.head())

####################################
# Section 5: Regression Analysis with Climate Data
####################################
st.header("5. Regression Analysis: Climate Parameters vs. ASIR")

# Ensure the merged dataset contains the required regression columns.
required_reg = ["ASIR", "TAVG", "Humidity", "PRCP"]
missing_reg = [col for col in required_reg if col not in df_merged.columns]
if missing_reg:
    st.error(f"Missing columns for regression: {missing_reg}")
else:
    st.success("All required regression columns found.")

    # Simple Regression: ASIR ~ TAVG
    model_temp = smf.ols("ASIR ~ TAVG", data=df_merged).fit()
    st.subheader("Simple Regression: ASIR ~ TAVG")
    st.text(model_temp.summary())
    fig_reg_temp, ax_reg_temp = plt.subplots(figsize=(8, 6))
    sns.regplot(x="TAVG", y="ASIR", data=df_merged, ax=ax_reg_temp)
    ax_reg_temp.set_title("ASIR vs TAVG (°F)")
    st.pyplot(fig_reg_temp)

    # Simple Regression: ASIR ~ Humidity
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
        ax.set_title(f"_

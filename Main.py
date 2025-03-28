import streamlit as st
import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import seaborn as sns
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import us

st.title("Coccidioidomycosis & Climate Analysis")

st.markdown("""
This app performs the following tasks:
1. Loads NOAA’s station inventory and converts station IDs into location (state) information.
2. Loads a climate & coccidioidomycosis dataset (Climate data.csv) and merges it with the station info.
3. Displays the merged dataset and a trendline graph (disease ASIR over years) for each state.
4. Runs regression analyses (simple & multiple) to investigate the correlation between climate parameters (TAVG, Humidity, PRCP) and ASIR.
""")

###############################
# 1. Process NOAA Station Data
###############################

st.header("NOAA Station Inventory Conversion")

# Define fixed-width file column specifications (per NOAA ghcnd-stations.txt format)
colspecs = [(0, 11), (12, 20), (21, 30), (31, 37), (38, 68), (69, 71), (72, 75), (76, 79), (80, 85)]
columns = ["ID", "Latitude", "Longitude", "Elevation", "Station_Name", "State", "GSN_Flag", "HCN_Flag", "WMO_ID"]

@st.cache_data(show_spinner=False)
def load_station_inventory(file_path="ghcnd-stations.txt"):
    df_stations = pd.read_fwf(file_path, colspecs=colspecs, header=None, names=columns)
    # Clean text fields.
    df_stations["ID"] = df_stations["ID"].str.strip()
    df_stations["Station_Name"] = df_stations["Station_Name"].str.strip()
    df_stations["State"] = df_stations["State"].str.strip()
    # Convert numeric columns.
    df_stations["Latitude"] = pd.to_numeric(df_stations["Latitude"], errors="coerce")
    df_stations["Longitude"] = pd.to_numeric(df_stations["Longitude"], errors="coerce")
    df_stations["Elevation"] = pd.to_numeric(df_stations["Elevation"], errors="coerce")
    return df_stations

df_stations = load_station_inventory()

# Set up geolocator for reverse geocoding.
geolocator = Nominatim(user_agent="ghcnd_station_geocoder")
geocode = RateLimiter(geolocator.reverse, min_delay_seconds=1)

def get_state_from_coords(row):
    # Only attempt if state is missing.
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

mask_missing_state = df_stations["State"] == ""
if mask_missing_state.any():
    st.write("Performing reverse geocoding for stations missing state codes (this may take some time)...")
    df_stations.loc[mask_missing_state, "State"] = df_stations[mask_missing_state].apply(get_state_from_coords, axis=1)

def state_abbr_to_full(state_value):
    # Check if the value is a non-empty string.
    if not isinstance(state_value, str) or not state_value.strip():
        return ""
    st_obj = us.states.lookup(state_value)
    return st_obj.name if st_obj else state_value

df_stations["State_Full"] = df_stations["State"].apply(state_abbr_to_full)

st.subheader("Station Inventory Preview")
st.dataframe(df_stations.head(10))

##########################################
# 2. Load and Merge Climate & Disease Data
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

# Merge station info with climate data based on station ID.
# We assume the climate data has a "STATION" column matching the "ID" in the station inventory.
if "STATION" not in df_climate.columns:
    st.error("The climate data must include a 'STATION' column.")
else:
    df_merged = pd.merge(df_climate, df_stations[["ID", "State_Full"]], left_on="STATION", right_on="ID", how="left")
    st.subheader("Merged Dataset (Climate & Disease + Station Info)")
    st.dataframe(df_merged.head())

##########################################
# 3. Display Disease Trends
##########################################

st.header("Coccidioidomycosis Disease Trends")

# We assume that the merged dataset contains:
# - "MMWR Year": the reporting year.
# - "ASIR": the disease incidence rate (cases per unit population).
# - "State_Full": the state name.
if not {"MMWR Year", "ASIR", "State_Full"}.issubset(df_merged.columns):
    st.error("Merged data must include 'MMWR Year', 'ASIR', and 'State_Full' columns.")
else:
    st.subheader("Merged Disease Data Table")
    st.dataframe(df_merged[["STATION", "MMWR Year", "ASIR", "State_Full"]].dropna().reset_index(drop=True))
    
    st.subheader("Trendline Graph by State")
    states = df_merged["State_Full"].dropna().unique()
    selected_state = st.selectbox("Select a state to view disease trend:", sorted(states))
    
    df_state = df_merged[df_merged["State_Full"] == selected_state]
    # Sort by year to create a proper time series.
    df_state = df_state.sort_values("MMWR Year")
    
    if df_state.empty:
        st.warning("No data for the selected state.")
    else:
        fig_state, ax_state = plt.subplots(figsize=(8, 6))
        ax_state.plot(df_state["MMWR Year"], df_state["ASIR"], marker="o", linestyle="-")
        ax_state.set_title(f"Coccidioidomycosis ASIR Trend in {selected_state}")
        ax_state.set_xlabel("MMWR Year")
        ax_state.set_ylabel("ASIR")
        st.pyplot(fig_state)

##########################################
# 4. Regression Analysis (Climate vs. Disease)
##########################################

st.header("Regression Analysis: Climate Parameters vs. ASIR")

# We require the following columns for regression:
# "ASIR", "TAVG" (average temperature in °F), "Humidity", and "PRCP" (precipitation in inches)
required_cols = ["ASIR", "TAVG", "Humidity", "PRCP"]
missing_cols = [col for col in required_cols if col not in df_merged.columns]
if missing_cols:
    st.error(f"Missing required columns for regression: {missing_cols}. Check your Climate data CSV.")
else:
    st.success("All required regression columns found.")

    # ---- Simple Regression: ASIR ~ TAVG ----
    model_temp = smf.ols("ASIR ~ TAVG", data=df_merged).fit()
    st.subheader("Simple Regression: ASIR ~ TAVG")
    st.text(model_temp.summary())

    fig_reg_temp, ax_reg_temp = plt.subplots(figsize=(8, 6))
    sns.regplot(x="TAVG", y="ASIR", data=df_merged, ax=ax_reg_temp)
    ax_reg_temp.set_title("ASIR vs Average Temperature (°F)")
    st.pyplot(fig_reg_temp)

    # ---- Simple Regression: ASIR ~ Humidity ----
    model_hum = smf.ols("ASIR ~ Humidity", data=df_merged).fit()
    st.subheader("Simple Regression: ASIR ~ Humidity")
    st.text(model_hum.summary())

    fig_reg_hum, ax_reg_hum = plt.subplots(figsize=(8, 6))
    sns.regplot(x="Humidity", y="ASIR", data=df_merged, ax=ax_reg_hum)
    ax_reg_hum.set_title("ASIR vs Humidity")
    st.pyplot(fig_reg_hum)

    # ---- Multiple Regression: ASIR ~ TAVG + Humidity + PRCP ----
    formula = "ASIR ~ TAVG + Humidity + PRCP"
    model_multi = smf.ols(formula, data=df_merged).fit()
    st.subheader("Multiple Regression")
    st.write("Formula used:", formula)
    st.text(model_multi.summary())

    st.subheader("Scatter Plots for Each Predictor")
    for var in ["TAVG", "Humidity", "PRCP"]:
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.regplot(x=var, y="ASIR", data=df_merged, ax=ax)
        ax.set_title(f"ASIR vs {var}")
        st.pyplot(fig)

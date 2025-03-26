import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Set Streamlit page config
st.set_page_config(page_title="Coccidioidomycosis Scatter Plots", layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("coccidioidomycosis_cases_by_state_2014_2022.csv")
    df['State'] = df['State'].str.strip()
    df = df.dropna(subset=['State', 'Cases', 'Year'])
    df['Cases'] = pd.to_numeric(df['Cases'], errors='coerce')
    df = df.dropna(subset=['Cases'])
    df['Year'] = df['Year'].astype(int)
    return df

df = load_data()

# Sidebar year selector
years = sorted(df['Year'].unique())
selected_year = st.sidebar.selectbox("Select Year", years, index=len(years)-1)

# Filter and sort data
states_order = sorted(df['State'].unique())
yearly_data = df[df['Year'] == selected_year].set_index('State').reindex(states_order).reset_index()

# Title
st.title(f"Coccidioidomycosis Cases by State - {selected_year}")

# Plot
fig, ax = plt.subplots(figsize=(14, 6))
ax.scatter(yearly_data['State'], yearly_data['Cases'], color='blue')
ax.set_xlabel("State")
ax.set_ylabel("Number of Cases")
ax.set_title(f"Coccidioidomycosis in {selected_year}")
plt.xticks(rotation=90)
plt.grid(True, linestyle='--', alpha=0.5)
st.pyplot(fig)

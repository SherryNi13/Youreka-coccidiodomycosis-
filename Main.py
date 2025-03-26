import pandas as pd
import matplotlib.pyplot as plt
import os

# Load dataset (assumes CSV is in the same directory)
file_path = 'coccidioidomycosis_cases_by_state_2014_2022.csv'
df = pd.read_csv(file_path)

# Clean data
df['State'] = df['State'].str.strip()
df = df.dropna(subset=['State', 'Cases', 'Year'])  # remove rows missing key info
df['Cases'] = pd.to_numeric(df['Cases'], errors='coerce')
df = df.dropna(subset=['Cases'])  # remove rows where 'Cases' became NaN after conversion
df['Year'] = df['Year'].astype(int)

# Sort states alphabetically for consistent X-axis ordering
states_order = sorted(df['State'].unique())

# Generate scatter plots for each year
unique_years = sorted(df['Year'].unique())

for year in unique_years:
    yearly_data = df[df['Year'] == year]
    
    # Ensure X is aligned with sorted state order
    yearly_data = yearly_data.set_index('State').reindex(states_order).reset_index()

    plt.figure(figsize=(14, 6))
    plt.scatter(yearly_data['State'], yearly_data['Cases'], color='blue')
    plt.title(f'Coccidioidomycosis Cases by State - {year}')
    plt.xlabel('State')
    plt.ylabel('Number of Cases')
    plt.xticks(rotation=90)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

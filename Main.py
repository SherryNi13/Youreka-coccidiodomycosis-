import streamlit as st
import pandas as pd
import os

def detect_cum_column(df, target_year=None):
    """
    Detects and returns the column name that likely contains the cumulative value.
    If a target_year is provided, it prioritizes columns that contain both 'cum' and the target year.
    """
    if target_year is not None:
        target_str = str(target_year)
        target_candidates = [col for col in df.columns if 'cum' in col.lower() and target_str in col.lower()]
        if target_candidates:
            return target_candidates[0]
    # Fallback: return any column containing 'cum'
    cum_cols = [col for col in df.columns if 'cum' in col.lower()]
    if not cum_cols:
        return None
    # If there's a column exactly named "cum", use it.
    for col in cum_cols:
        if col.lower() == 'cum':
            return col
    return cum_cols[0]

def clean_and_aggregate_data(file_path, state_col='State', year_col='Year', target_year=None):
    """
    Reads a CSV file, detects the appropriate cumulative column using the target_year if provided,
    and aggregates data so that for each state and year the last (accumulated) value is used.
    """
    df = pd.read_csv(file_path)
    
    # Detect the cumulative column, with a preference for one containing the target year.
    cum_col = detect_cum_column(df, target_year)
    if cum_col is None:
        raise ValueError(f"No cumulative column found in {file_path}.")
    
    # Keep only the necessary columns and rename the cumulative column to "Value".
    df = df[[state_col, year_col, cum_col]].copy()
    df.rename(columns={cum_col: "Value"}, inplace=True)
    
    # Ensure the year column is numeric.
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
    
    # For duplicate state entries, take the last one (assumed to be the final cumulative count).
    aggregated_df = df.groupby([state_col, year_col], as_index=False).last()
    return aggregated_df

def process_year_data(year, file_paths, state_col='State', year_col='Year'):
    """
    Processes a single year's dataset(s). For 2019 (or any year with multiple files), if multiple files are provided,
    they are merged state-wise.
    """
    dfs = []
    for path in file_paths:
        if os.path.exists(path):
            st.write(f"Processing {path} for year {year}...")
            try:
                # Use target_year to choose the proper "cum" column.
                df = clean_and_aggregate_data(path, state_col, year_col, target_year=year)
                dfs.append(df)
            except Exception as e:
                st.error(f"Error processing {path}: {e}")
        else:
            st.write(f"File {path} not found for year {year}.")
    
    if not dfs:
        return None
    elif len(dfs) == 1:
        return dfs[0]
    else:
        # Merge multiple datasets (e.g., two files for a given year) on State and Year.
        merged = pd.merge(dfs[0], dfs[1], on=[state_col, year_col], how='outer', suffixes=('_1', '_2'))
        
        def choose_value(row, threshold=0.1):
            v1 = row.get('Value_1')
            v2 = row.get('Value_2')
            if pd.isnull(v1) and not pd.isnull(v2):
                return v2
            if pd.isnull(v2) and not pd.isnull(v1):
                return v1
            if pd.isnull(v1) and pd.isnull(v2):
                return None
            # Both values exist: calculate relative difference.
            avg = (v1 + v2) / 2
            rel_diff = abs(v1 - v2) / avg if avg != 0 else 0
            if rel_diff < threshold:
                return avg
            else:
                return min(v1, v2)
        
        merged['Value'] = merged.apply(choose_value, axis=1)
        return merged[[state_col, year_col, 'Value']]

def compile_data(year_start=2014, year_end=2022, file_prefix='dataset_', file_suffix='.csv', state_col='State', year_col='Year'):
    """
    Loops over years and processes each year’s dataset(s). For example, for 2019,
    it expects two files (e.g. dataset_2019a.csv and dataset_2019b.csv) and merges them.
    """
    compiled_data = pd.DataFrame()
    for year in range(year_start, year_end + 1):
        if year == 2019:
            # For 2019, assume two files (adjust names if needed).
            file_paths = [f"{file_prefix}{year}a{file_suffix}", f"{file_prefix}{year}b{file_suffix}"]
        else:
            file_paths = [f"{file_prefix}{year}{file_suffix}"]
        
        year_data = process_year_data(year, file_paths, state_col, year_col)
        if year_data is not None:
            compiled_data = pd.concat([compiled_data, year_data], ignore_index=True)
        else:
            st.write(f"No data found for year {year}.")
    
    return compiled_data

def fill_missing_states(df, region_to_states, state_col='State', year_col='Year', value_col='Value'):
    """
    For each year and each defined region, if some states are missing,
    compute the missing values by subtracting the sum of available states from the regional total.
    If multiple states are missing, the difference is evenly distributed.
    Regional total rows (where the state equals the region name) are removed after filling.
    """
    new_rows = []
    for year in df[year_col].unique():
        year_df = df[df[year_col] == year]
        for region, states in region_to_states.items():
            region_row = year_df[year_df[state_col] == region]
            if not region_row.empty:
                region_total = region_row.iloc[0][value_col]
                present_states = year_df[year_df[state_col].isin(states)]
                present_state_names = present_states[state_col].tolist()
                missing_states = [s for s in states if s not in present_state_names]
                if missing_states:
                    present_sum = present_states[value_col].sum()
                    missing_total = region_total - present_sum
                    missing_value = missing_total / len(missing_states)
                    for missing_state in missing_states:
                        new_row = {state_col: missing_state, year_col: year, value_col: missing_value}
                        new_rows.append(new_row)
    
    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    region_names = list(region_to_states.keys())
    df = df[~df[state_col].isin(region_names)]
    return df

# --- Streamlit App ---

st.title("Compiled, Cleaned, and Filled Data")

# Define region-to-states mapping (adjust as needed).
region_to_states = {
    "S. Atlantic": ["Florida", "Georgia", "South Carolina", "North Carolina", "Virginia"],
    # Additional regions and their states can be added here.
}

# Step 1: Compile the data from 2014 to 2022.
data = compile_data(2014, 2022)

if data.empty:
    st.error("No data loaded. Please ensure your CSV files are in the correct location and named appropriately.")
else:
    # Step 2: Fill missing state data using regional totals.
    data_filled = fill_missing_states(data, region_to_states)
    data_filled = data_filled.sort_values(by=["Year", "State"]).reset_index(drop=True)
    
    # --- Output ---
    st.subheader("Final Compiled Data (Table)")
    st.dataframe(data_filled)
    
    st.subheader("Cumulative Cases Trend (Graph)")
    selected_state = st.selectbox("Select a state to view its trend:", data_filled["State"].unique())
    state_data = data_filled[data_filled["State"] == selected_state].set_index("Year")
    st.line_chart(state_data[["Value"]])

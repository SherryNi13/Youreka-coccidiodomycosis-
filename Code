import pandas as pd
import us

def load_station_inventory(file_path="ghcnd-stations.txt"):
    colspecs = [(0, 11), (38, 40)]  # Only read 'ID' and 'State'
    columns = ["ID", "State"]
    df_stations = pd.read_fwf(file_path, colspecs=colspecs, header=None, names=columns)
    df_stations["State"] = df_stations["State"].str.strip()
    df_stations["State_Full"] = df_stations["State"].apply(lambda x: us.states.lookup(x).name if x else "")
    return df_stations

# Example usage
df_stations = load_station_inventory()
print(df_stations.head())

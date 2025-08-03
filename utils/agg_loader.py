import json
import os
from datetime import datetime, timedelta
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

def load_recent_agg_csvs(directory: str, highlight_well: int = 1, minutes_back: int = 30):
    # שליפת רשימת בארות מהקונפיג
    config_path = os.path.join("config", "session_config.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    well_numbers = config.get("parameters", {}).get("well_numbers", list(range(1, 37)))
    control_well = config.get("control_well")
    if control_well and isinstance(control_well, int):
        well_numbers = [w for w in well_numbers if w < control_well]

    cutoff_time = datetime.now() - timedelta(minutes=minutes_back)

    def read_and_prepare_csv(well_number):
        filename = f'{directory}/Time_points_dfs_{str(well_number).zfill(2)}.csv'
        df = pd.read_csv(filename)
        df['Time_Stamp'] = pd.to_datetime(df['Time_Stamp'], format='%Y%m%d-%H%M%S')
        df = df[df['Time_Stamp'] >= cutoff_time]
        df['well_number'] = well_number
        return df

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(read_and_prepare_csv, well_numbers))

    all_data = pd.concat(results, ignore_index=True)
    all_data['Time_Stamp'] = all_data['Time_Stamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    return all_data.to_dict(orient='records')   
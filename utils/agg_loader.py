import json
import os
from datetime import datetime, timedelta
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

def load_recent_agg_csvs(directory: str, highlight_well: int = 1, minutes_back: int = 30):
    """
    Load recent aggregated CSV files from a directory for specified wells, filtering data by a time cutoff.

    Args:
        directory (str): Path to the directory containing CSV files.
        highlight_well (int, optional): Well number to highlight. Defaults to 1.
        minutes_back (int, optional): Number of minutes back from current time to filter data. Defaults to 30.

    Returns:
        list: A list of dictionaries representing the filtered data from all wells.
    """
    # Load configuration and validate well numbers
    config_path = os.path.join("config", "session_config.json")
    well_numbers = list(range(1, 37))  # default well numbers
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        params = config.get("parameters", {})
        if isinstance(params, dict):
            wells = params.get("well_numbers")
            if isinstance(wells, list) and all(isinstance(w, int) for w in wells):
                well_numbers = wells
        control_well = config.get("control_well")
        if isinstance(control_well, int):
            well_numbers = [w for w in well_numbers if w < control_well]
    except (FileNotFoundError, json.JSONDecodeError):
        # If config file is missing or invalid, proceed with default well_numbers
        pass

    cutoff_time = datetime.now() - timedelta(minutes=minutes_back)

    def read_and_prepare_csv(well_number):
        filename = os.path.join(directory, f'Time_points_dfs_{str(well_number).zfill(2)}.csv')
        try:
            df = pd.read_csv(filename)
            if 'Time_Stamp' not in df.columns:
                raise ValueError(f"Missing 'Time_Stamp' column in file {filename}")
            df['Time_Stamp'] = pd.to_datetime(df['Time_Stamp'], errors='coerce', format='%Y%m%d-%H%M%S')
            df = df.dropna(subset=['Time_Stamp'])
            df = df[df['Time_Stamp'] >= cutoff_time]
            df['well_number'] = well_number
            return df
        except (FileNotFoundError, pd.errors.EmptyDataError, ValueError):
            # Return empty DataFrame if file missing, empty, or invalid
            return pd.DataFrame(columns=['Time_Stamp', 'well_number'])

    results = []
    with ThreadPoolExecutor() as executor:
        future_to_well = {executor.submit(read_and_prepare_csv, w): w for w in well_numbers}
        for future in as_completed(future_to_well):
            df = future.result()
            if not df.empty:
                results.append(df)

    if results:
        all_data = pd.concat(results, ignore_index=True)
        all_data['Time_Stamp'] = all_data['Time_Stamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        return all_data.to_dict(orient='records')
    else:
        return []
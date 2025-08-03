import os
import glob
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import shutil
from datetime import datetime

def read_csv(file):
    number = file.split('_')[-1].split('.')[0]
    df = pd.read_csv(file)
    return number, df

def update_log(log_file, processed_files):
    with open(log_file, 'a') as log:
        for file in processed_files:
            log.write(f"{file},{datetime.now().isoformat()}\n")

def get_processed_files(log_file):
    if not os.path.exists(log_file):
        open(log_file, 'w').close()  # Create the log file if it doesn't exist
        return {}
    processed_files = {}
    with open(log_file, 'r') as log:
        for line in log:
            file, timestamp = line.strip().split(',')
            processed_files[file] = datetime.fromisoformat(timestamp)
    return processed_files

def Agg_CSV(path_Agg, csv_directory, log_file='processed_files.log'):
    # Get a list of all the CSV files in the directory and its subdirectories
    csv_files = glob.glob(os.path.join(path_Agg, '**', 'Time_points_dfs_*.csv'), recursive=True)
    
    # Read the log file to get already processed files
    processed_files = get_processed_files(log_file)
    
    # Filter files based on modification time
    files_to_process = []
    for file in csv_files:
        mod_time = datetime.fromtimestamp(os.path.getmtime(file))
        if file not in processed_files or mod_time > processed_files[file]:
            files_to_process.append(file)
    
    if not files_to_process:
        print("No new or updated files to process.")
        return
    
    # Use ThreadPoolExecutor for parallel processing of CSV files
    dfs = {}
    with ThreadPoolExecutor() as executor:
        for number, df in executor.map(read_csv, files_to_process):
            if number not in dfs:
                dfs[number] = df
            else:
                dfs[number] = pd.concat([dfs[number], df], axis=0, ignore_index=True)
    
    # Read existing aggregated files and update them with new data
    for number in dfs.keys():
        agg_file_path = os.path.join(csv_directory, f'Time_points_dfs_{number}.csv')
        if os.path.exists(agg_file_path):
            existing_df = pd.read_csv(agg_file_path)
            dfs[number] = pd.concat([existing_df, dfs[number]], axis=0, ignore_index=True)
    
    # Update the Time_interval column for each DataFrame
    for number, df in dfs.items():
        df = df.drop_duplicates().sort_values(by=['Time_Stamp']).reset_index(drop=True)
        df['Time_interval'] = df['Time_Stamp'].rank(method='dense').astype(int)
        dfs[number] = df
    
    # Create the CSV directory if it doesn't exist
    os.makedirs(csv_directory, exist_ok=True)
    
    # Save the aggregated CSV files in the CSV directory
    for number, df in dfs.items():
        file_name = f'Time_points_dfs_{number}.csv'
        file_path = os.path.join(csv_directory, file_name)
        df.to_csv(file_path, index=False)
    
    # Update the log file with the processed files
    update_log(log_file, files_to_process)
    print("Processing complete. Log file updated.")


def clear_and_copy_csv_files(src_directory, dest_directory):
    # Ensure the destination directory exists
    if not os.path.exists(dest_directory):
        os.makedirs(dest_directory)
    
    # Remove all CSV files in the destination directory
    for file in glob.glob(os.path.join(dest_directory, '*.csv')):
        os.remove(file)

    # Copy all CSV files from the source directory to the destination directory
    for file in glob.glob(os.path.join(src_directory, '*.csv')):
        shutil.copy(file, dest_directory)


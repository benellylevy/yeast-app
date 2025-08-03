import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

base_Temp = 30
range_Temp = 22
curve = 1.1

def calculate_ref_val_try(df, val_F, baseline):
    now = datetime.now()
    time_to_integrate = now - timedelta(minutes=60)
    
    df = df.groupby(by='Time_Stamp').apply(lambda x: x[val_F].nlargest(int(len(x)*0.2)).mean())
    val = df.tail(6).mean() / baseline
    print('The value calculated is '+str(df.tail(6).mean()))
    
    return val

def dec_exp(x, range_Temp ,base_Temp, curve):
    if x==0:
        y_value = base_Temp + 0.5
        y_crit = (y_value - base_Temp) / range_Temp
        x_crit = -curve * np.log(y_crit)
        print('Multiplaction of F needed to reach 0.5 a dgree from target is: '+ str(x_crit))
    y = np.exp(-x/curve)
    return (base_Temp + y*range_Temp)

def calculate_baseline(csv_directory, FeedBack_well, val_F):
    # בונים נתיב לקובץ CSV עבור באר המשוב
    feedback_csv = os.path.join(csv_directory, 'Time_points_dfs_' + str(FeedBack_well) + '.csv')
    # טוען את הנתונים
    df = pd.read_csv(feedback_csv)
    # קיבוץ לפי Time_Stamp וחישוב ממוצע
    df_grouped = df.groupby(by='Time_Stamp').mean()
    # לקיחת 6 השורות האחרונות וממוצע הכולל
    baseline_value = df_grouped.tail(6).mean()[val_F]
    baseline_value = round(baseline_value)
    print("Calculated baseline:", baseline_value)
    return baseline_value

def calculate_baseline_20(csv_directory, FeedBack_well, val_F):
    """
    Calculate the baseline value for a given well and feature, considering only the top 20% of values.

    Parameters:
    csv_directory (str): The directory containing the CSV files.
    FeedBack_well (str): The well identifier.
    val_F (str): The feature column name to calculate the baseline for.

    Returns:
    int: The rounded baseline value.
    """
    df = pd.read_csv(csv_directory + 'Time_points_dfs_' + FeedBack_well + '.csv')
    df = df.groupby(by='Time_Stamp').apply(lambda x: x[val_F].nlargest(int(len(x) * 0.2)).mean())
    baseline = df.tail(6).mean()
    return round(baseline)

def calculate_baseline_20_for_all(csv_directory, wells_range, val_F):
    """
    Calculate the baseline value for a range of wells and a given feature, considering only the top 20% of values.

    Parameters:
    csv_directory (str): The directory containing the CSV files.
    wells_range (list): A list of well identifiers to process.
    val_F (str): The feature column name to calculate the baseline for.

    Returns:
    dict: A dictionary where keys are well identifiers and values are the rounded baseline values.
    """
    baseline_values = {}
    for well in wells_range:
        feedback_csv = os.path.join(csv_directory, f'Time_points_dfs_{well}.csv')
        df = pd.read_csv(feedback_csv)
        df = df.groupby(by='Time_Stamp').apply(lambda x: x[val_F].nlargest(int(len(x) * 0.2)).mean())
        baseline = df.tail(6).mean()
        baseline_values[well] = round(baseline)
    return baseline_values
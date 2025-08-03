import time
import traceback
import pandas as pd
import math
import time
import ujson
import glob
from datetime import datetime, timedelta
import numpy as np
import os
# Import the necessary functions from the other scripts
from feedback import calculate_ref_val_try, dec_exp
from tgmassage import send_telegram_alert, Vacuum
from publish import Publish_stats
from files_worker import Agg_CSV, clear_and_copy_csv_files

# Define the parameters for the feedback curve
base_Temp = 30
range_Temp = 22
curve = 1.1

with open("config/session_config.json", "r", encoding="utf-8") as f:
    session_config = json.load(f)
agg_path = session_config["paths"]["agg_path"]
config_path = os.path.join(agg_path, "config.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

base_folder = config["experiment_folder"]
baseline = config["baseline_value"]
FeedBack_well = str(config["highlight_well"]).zfill(2)
control_well = str(config["control_well"]).zfill(2)
# Define the path to the folder containing the CSV files


MAX_RETRIES = 15
retry_count = 0

while True:
    try:
        #####################################################
        # ↓↓↓ כאן כל הסקריפט שלך נשאר בדיוק כמו שהוא ↓↓↓
        #     כולל הלולאה הפנימית while True==True
        #     אין צורך ב-break בסוף!
        #####################################################


        def mean_chip_temp_from_files(name_folder, num_files=50):
            files = sorted(glob.glob(name_folder + '/*.json'), reverse=True)[:num_files]
            chip_temps = []
            for file in files:
                with open(file, 'r') as f:
                   data = ujson.load(f)
                   chip_temps.append(data['T_CHIP(celcius)'])
            return sum(chip_temps) / len(chip_temps)

        def temp_from_percent(percent_above):
            base_Temp = 30
            range_Temp = 9
            curve = 40  # קבוע מחושב לפי הדרישה שלך
            y = np.exp(-percent_above / curve)
            return round(base_Temp + y * range_Temp, 2)
        
        def dec_exp(x, range_Temp ,base_Temp, curve):
            if x==0:
                y_value = base_Temp + 0.5
                y_crit = (y_value - base_Temp) / range_Temp
                x_crit = -curve * np.log(y_crit)
                print('Multiplaction of F needed to reach 0.5 a dgree from target is: '+ str(x_crit))
            y = np.exp(-x/curve)
            return (base_Temp + y*range_Temp)

        def calculate_ref_val_try(df, val_F, baseline):
        # baseline הוא ערך הסף שמעליו התא נחשב "מבטא"
        # val_F הוא שם העמודה של עוצמת הפלואורסצנציה

     # קבץ לפי טיימסטמפ, עבור כל טיימסטמפ – חשב את אחוז התאים שמעל baseline
            def percent_above_threshold(x):
                return (x[val_F] >= baseline).sum() / len(x) * 100  # אחוז התאים שמעל הסף

            percent_above = df.groupby(by='Time_Stamp').apply(percent_above_threshold)
            val = percent_above.tail(4).mean()  # ממוצע האחוז ב-6 הזמנים האחרונים (כמו בקוד שלך)

            print('The value calculated is '+str(val))

            return val


        # Define the paths to the relevant folders and files
        path_Agg = os.path.join(base_folder, 'IMG\\')
        csv_directory = os.path.join(base_folder, 'AGG_CSV\\')
        csv_for_fig = os.path.join(base_folder, 'AGG_CSV_FIGS\\')
        log_file = os.path.join(csv_directory, 'processed_files.csv')
        name_folder = glob.glob(os.path.join(base_folder, 'TEMP', '*'))[0]


        values = pd.DataFrame(columns=['Ref_val','Temp_sent','Time'])

        temp_to_send = 39
        Temp_crit = 2
        cell_control = 40
        val_F='mean_F_C2'

        path_csv = csv_directory

        log_file_path = path_csv + 'Feedback_log.csv'

        # Check if the log file exists
        if os.path.exists(log_file_path):
            # If it exists, read the existing data into the DataFrame
            values = pd.read_csv(log_file_path)
            # Drop any unnamed columns
            values = values.loc[:, ~values.columns.str.contains('^Unnamed')]
        else:
           # If it does not exist, create a new DataFrame with the appropriate columns
           values = pd.DataFrame(columns=['Ref_val', 'Temp_sent', 'Time'])


        try:
            while True==True:
                delta =temp_to_send-mean_chip_temp_from_files(name_folder) 
                if delta > Temp_crit:
                   send_telegram_alert("Temp is NOT correct!!! Delta is: "+str(delta))

            
                Agg_CSV(path_Agg, csv_directory, log_file=log_file)
                try:
                   clear_and_copy_csv_files(csv_directory, csv_for_fig)
                except:
                   pass
        
                df = pd.read_csv(path_csv+'Time_points_dfs_'+str(FeedBack_well)+'.csv')


                ref_val = calculate_ref_val_try(df, val_F, baseline)
                print(math.isnan(ref_val))

                if math.isnan(ref_val):
                    print('Val is nan')
                    pass

                else:
                    print (ref_val)
                    temp_to_send = temp_from_percent(ref_val)
                    if temp_to_send> 39:
                        temp_to_send = 39
                    temp_to_send = round(temp_to_send, 2)
                    temp = temp_to_send
                    DeadBand = 0.15
                    Channel_temp_control_enum = 2
                    Start_T_Control = True

                df_control = pd.read_csv(path_csv+'Time_points_dfs_'+str(control_well)+'.csv')
                number_cell_control = df_control['Number_cells'].iloc[-1]
                try:
                    if number_cell_control > cell_control:
                        Vacuum()
                        send_telegram_alert('Cells in main channel. Vacuum activated')
                except:
                    pass



                now = datetime.now()

                current_time = now.strftime("%Y-%m-%d %H:%M:%S")

                Publish_stats(temp,DeadBand,Channel_temp_control_enum,Start_T_Control)

                try:
                    values_uni = {'Ref_val': ref_val, 'Temp_sent': temp_to_send, 'Time': current_time}
                    print(values_uni)
                    values = values.append(values_uni, ignore_index=True)
                    print(values.tail())
                    values.to_csv(path_csv + 'Feedback_log.csv', index=False)
                    print('this step worked')
                except Exception as e:
                    print(f"An exception occurred when appending or saving data: {e}")
                    # Optionally, log the error or take other actions
                    send_telegram_alert('NaN encountered, skipped')
                    pass
                time.sleep(432)

        except Exception as e:
            print(f"An exception occurred: {e}")
            send_telegram_alert("FeedBack stopped!!!")

    
        finally:
            # Save the log file
            values.to_csv(log_file_path, index=False)
        # אם הכל תקין — אפס את מונה השגיאות
        retry_count = 0

    except Exception as e:
        retry_count += 1
        print(f"\n⚠️ ניסיון מספר {retry_count} נכשל:\n{traceback.format_exc()}")
        send_telegram_alert(f"❌ FeedBack script failed (attempt {retry_count}/{MAX_RETRIES}). Retrying in 7 minutes.")

        if retry_count >= MAX_RETRIES:
            send_telegram_alert("❌ FeedBack stopped permanently after 4 failed attempts.")
            break  # יוצא מהלולאה החיצונית, הסקריפט נעצר

        print("🕒 ממתין 7 דקות לפני ניסיון נוסף...\n")
        time.sleep(420)

    else:
        # אם לא הייתה שגיאה — המשך ללולאה שוב (אין צורך ב-break)
        pass

    # המשך ללולאה אין-סופית

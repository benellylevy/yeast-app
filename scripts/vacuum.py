import pandas as pd
import time
from tgmassage import send_telegram_alert, Vacuum

def call_vacuum_every_30_minutes():
    while True:
        try:
            Vacuum()
            #send_telegram_alert("Vacuum activated as part of 3-minute routine.")
            time.sleep(1 * 60)  # Wait for 30 minutes
        except Exception as e:
            send_telegram_alert(f"Error occurred during vacuum routine: {e}".replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("]", "\\]").replace("(", "\\(").replace(")", "\\)").replace("~", "\\~").replace("`", "\\`").replace(">", "\\>").replace("#", "\\#").replace("+", "\\+").replace("-", "\\-").replace("=", "\\=").replace("|", "\\|").replace("{", "\\{").replace("}", "\\}").replace(".", "\\.").replace("!", "\\!"))
            time.sleep(3 * 60)  # Rest for 30 minutes in case of error

def monitor_csv(file_path):
    while True:
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Check the "Cell_number" column from the last row
            if df["Number_cells"].iloc[::-1].sum() > 35:
                Vacuum()
                #send_telegram_alert("Cell count exceeded threshold. Vacuum activated.")
                time.sleep(1 * 60)
            else:
                time.sleep(1 * 60)  # Rest for 15 minutes
        except Exception as e:
            send_telegram_alert(f"Error occurred: {e}".replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("]", "\\]").replace("(", "\\(").replace(")", "\\)").replace("~", "\\~").replace("`", "\\`").replace(">", "\\>").replace("#", "\\#").replace("+", "\\+").replace("-", "\\-").replace("=", "\\=").replace("|", "\\|").replace("{", "\\{").replace("}", "\\}").replace(".", "\\.").replace("!", "\\!"))
            time.sleep(1 * 60)  # Rest for 15 minutes in case of error

# Example usage
#monitor_csv('B:/my_experiment/WELLS_20250325/AGG_CSV_FIGS/Time_points_dfs_37.csv')
for _ in range(45):
    call_vacuum_every_30_minutes()
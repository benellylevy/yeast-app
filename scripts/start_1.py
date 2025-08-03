import os
import shutil
import json
from datetime import datetime

def initialize_experiment_folders(base_directory):
    """
    יצירת תיקיות ניסוי חדשות במבנה קבוע, כולל תיקיות משנה, תיקיית טמפרטורה, 
    וכתיבת קבצי config גם לתיקיית הניסוי וגם לקונפיג הכללי של הממשק.
    """

    # יצירת שם תיקייה לפי תאריך היום
    today = datetime.now().strftime('%Y%m%d')
    main_folder = f"WELLS_{today}"
    experiment_folder = os.path.join(base_directory, main_folder)

    # יצירת תיקיית הניסוי הראשית
    if not os.path.exists(experiment_folder):
        os.mkdir(experiment_folder)

    # יצירת תיקיות המשנה
    subfolders = ['IMG', 'TEMP', 'AGG_CSV', 'IMG_CSV', 'MOVIES', 'AGG_CSV_FIGS']
    for subfolder in subfolders:
        path = os.path.join(experiment_folder, subfolder)
        if not os.path.exists(path):
            os.mkdir(path)

    # הגדרת תיקיית TEMP
    temp_folder_path = os.path.join(experiment_folder, 'TEMP')

    # שם תיקיית הטמפרטורה לפי תאריך + 00/12
    now = datetime.now()
    h = "00" if now.hour < 12 else "12"
    temp_subfolder_name = now.strftime('%Y%m%d') + h
    name_folder = os.path.join(temp_folder_path, temp_subfolder_name)

    try:
        os.mkdir(name_folder)
    except Exception as e:
        print("התיקייה כבר קיימת, משתמשים בה:", e)

    print(f"Experiment folder: {experiment_folder}")
    print(f"Temperature folder (name_folder): {name_folder}")

    # הגדרת נתיבים לקבצים נוספים
    csv_directory = os.path.join(experiment_folder, 'IMG_CSV')
    path_Agg = os.path.join(experiment_folder, 'AGG_CSV')
    csv_for_fig = os.path.join(experiment_folder, 'AGG_CSV_FIGS')
    log_file = os.path.join(path_Agg, "Feedback_log.csv")

    # יצירת config.json לתוך תיקיית הניסוי
    config = {
        "experiment_folder": experiment_folder,
        "name_folder": name_folder,
        "csv_directory": csv_directory,
        "path_Agg": path_Agg,
        "csv_for_fig": csv_for_fig,
        "log_file": log_file
    }

    config_path = os.path.join(experiment_folder, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

    print(f"Config written to: {config_path}")

    # כתיבת session_config.json כללי לממשק Flask
    session_config = {
        "paths": {
            "agg_path": experiment_folder,
            "mqtt_path": name_folder
        },
    }

    os.makedirs("config", exist_ok=True)
    with open("config/session_config.json", "w", encoding="utf-8") as f:
        json.dump(session_config, f, ensure_ascii=False, indent=2)

    print("Session config written to: config/session_config.json")

    return experiment_folder

if __name__ == "__main__":
    base_dir = r"B:/my_experiment"
    initialize_experiment_folders(base_dir)
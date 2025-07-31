# ==========================
# Analyse Path API Endpoints
# ==========================

@app.route("/get_analyse_path")
def get_analyse_path():
    """
    מחזיר את הנתיב הנוכחי של analyse (csv_directory) מתוך config.json
    """
    try:
        with open("config/session_config.json", "r") as f:
            session_config = json.load(f)
        experiment_folder = session_config["paths"]["agg_path"]
        config_path = os.path.join(experiment_folder, "config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return jsonify({"csv_directory": config.get("csv_directory", "")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/set_analyse_path", methods=["POST"])
def set_analyse_path():
    """
    מעדכן את csv_directory בקובץ config.json של הניסוי
    """
    try:
        new_path = request.json.get("csv_directory")
        if not new_path:
            return jsonify({"error": "Missing csv_directory"}), 400
        with open("config/session_config.json", "r") as f:
            session_config = json.load(f)
        experiment_folder = session_config["paths"]["agg_path"]
        config_path = os.path.join(experiment_folder, "config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        config["csv_directory"] = new_path
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return jsonify({"status": f"csv_directory updated to {new_path}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Imports - כל הספריות והמודולים הדרושים
import os
import json
import glob
import subprocess
import threading
from datetime import datetime

import pandas as pd
from flask import Flask, render_template, jsonify, request, session
from flask_cors import CORS

from utils.agg_loader import load_recent_agg_csvs

# הגדרות מערכת - יצירת האפליקציה, מפתחות, משתנים גלובליים
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # מפתח סודי לשימוש ב-session
CORS(app)  # מאפשר CORS לכולם

processes = {}  # מילון לשמירת תהליכים שרצים ברקע

# פונקציות עזר - פונקציות שמבצעות פעולות חוזרות ונשנות

def run_script(name, path):
    """
    מריץ סקריפט פייתון בשם מסוים ברקע אם הוא לא כבר רץ.
    name - שם מזהה לתהליך
    path - נתיב לקובץ הסקריפט להרצה
    """
    if name in processes:
        return
    def _run():
        processes[name] = subprocess.Popen(["python", path])
        processes[name].wait()
        del processes[name]
    threading.Thread(target=_run).start()


def load_temperature_json_series(folder_path, t0, max_files=30):
    """
    טוען סידרת טמפרטורות מקבצי JSON בתיקייה, מסנן לפי תאריך התחלה t0.
    מחזיר רשימה של dict עם זמן וערך טמפרטורה.
    """
    files = sorted(glob.glob(os.path.join(folder_path, "*.json")))
    data = []
    for file in files[-max_files:]:
        try:
            name = os.path.basename(file).replace(".json", "")
            timestamp = datetime.strptime(name, "%Y%m%d_%H%M%S")
            if timestamp >= t0:
                with open(file, "r") as f:
                    content = json.load(f)
                    if "chip_temp" in content:
                        data.append({
                            "x": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            "y": content["chip_temp"]
                        })
        except Exception as e:
            print(f"Error reading {file}: {e}")
    return data


# ראוטים API - כל הכתובות שהאפליקציה מקבלת ומחזירה נתונים

@app.route("/")
def index():
    """
    דף הבית - מחזיר את העמוד הראשי.
    """
    return render_template("index.html")


@app.route("/set_paths", methods=["POST"])
def set_paths():
    """
    מקבל נתיבי agg_path ו-mqtt_path ומאחסן אותם ב-session ובקובץ config/session_config.json.
    כולל גם רשימת מספרי בארות (well_numbers).
    """
    data = request.json
    session["agg_path"] = data.get("agg_path")
    session["mqtt_path"] = data.get("mqtt_path")

    config_data = {
        "paths": {
            "agg_path": data.get("agg_path"),
            "mqtt_path": data.get("mqtt_path")
        },
        "parameters": {
            "well_numbers": data.get("well_numbers", list(range(1, 37)))
        }
    }

    os.makedirs("config", exist_ok=True)
    with open("config/session_config.json", "w") as f:
        json.dump(config_data, f, indent=2)

    return jsonify({"status": "paths and wells set"})


@app.route("/api/temperature")
def temperature():
    """
    מחזיר את הטמפרטורה העדכנית ביותר מתוך קובץ data/mqtt.csv.
    """
    try:
        with open("data/mqtt.csv", "r") as f:
            lines = f.readlines()
            last = lines[-1].strip().split(",")
            return jsonify({"time": last[0], "temperature": float(last[1])})
    except:
        return jsonify({"error": "No data"}), 500


@app.route("/api/agg_recent")
def agg_recent():
    """
    מחזיר נתוני GFP אגרגטיביים אחרונים מהנתיב שנשמר ב-session.
    מדגים שימוש ב-load_recent_agg_csvs.
    """
    try:
        path = session.get("agg_path")
        data = load_recent_agg_csvs(path, highlight_well=1, minutes_back=30)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/feedback_log")
def feedback_log():
    """
    מחזיר את 30 השורות האחרונות מקובץ הלוג המוגדר ב-config.json.
    """
    try:
        with open("config/session_config.json", "r") as f:
            session_config = json.load(f)
        experiment_folder = session_config["paths"]["agg_path"]
        config_path = os.path.join(experiment_folder, "config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        log_path = config.get("log_file")
        if not log_path or not os.path.exists(log_path):
            return jsonify({"error": "log_file not found in config"}), 400

        df = pd.read_csv(log_path)
        last_rows = df.tail(30).fillna('').to_dict(orient='records')
        return jsonify(last_rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/start_analyse")
def start_analyse():
    """
    מפעיל את סקריפט האנליזה scripts/analaize.py עם נתיב csv_directory מה-config.
    """
    try:
        with open("config/session_config.json", "r") as f:
            session_config = json.load(f)
        experiment_folder = session_config["paths"]["agg_path"]
        config_path = os.path.join(experiment_folder, "config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        csv_directory = config.get("csv_directory")
        if not csv_directory:
            return jsonify({"error": "csv_directory not found in config.json"}), 400
        run_script("start_analyse", f"scripts/analaize.py {csv_directory}")
        return jsonify({"status": "started analyse"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ראוטים להרצת סקריפטים שונים ברקע

@app.route("/make_dir")
def make_dir():
    """
    מריץ את סקריפט scripts/start_1.py בשם 'make_dir'.
    """
    run_script("make_dir", "scripts/start_1.py")
    return jsonify({"status": "started make_dir"})


@app.route("/start_acclimation")
def start_acclimation():
    """
    מריץ את סקריפט ההתחלה acclimation בשם 'start_1'.
    """
    run_script("start_1", "scripts/start_1.py")
    return jsonify({"status": "started acclimation"})


@app.route("/run_baseline")
def run_baseline():
    """
    מריץ את סקריפט baseline.py.
    """
    run_script("baseline", "scripts/baseline.py")
    return jsonify({"status": "started baseline"})


@app.route("/start_mqtt")
def start_mqtt():
    """
    מריץ את סקריפט mqtt.py עם נתיב הקונפיג מה-session.
    """
    try:
        with open("config/session_config.json", "r") as f:
            session_config = json.load(f)
        experiment_folder = session_config["paths"]["agg_path"]
        config_path = os.path.join(experiment_folder, "config.json")
        run_script("start_mqtt", f"scripts/mqtt.py {config_path}")
        return jsonify({"status": "started mqtt"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/start_feedback")
def start_feedback():
    """
    מריץ את סקריפט main_feedback.py.
    """
    run_script("main_feedback", "scripts/main_feedback.py")
    return jsonify({"status": "started feedback"})


@app.route("/start_secure_feedback")
def start_secure_feedback():
    """
    מריץ את סקריפט secure_feedback.py.
    """
    run_script("secure_feedback", "scripts/secure_feedback.py")
    return jsonify({"status": "started secure feedback"})


@app.route("/start_plot")
def start_plot():
    """
    מריץ את סקריפט plot_t_chip_every_10_files.py לצורך גרפים.
    """
    run_script("plot", "scripts/plot_t_chip_every_10_files.py")
    return jsonify({"status": "started plotting"})


@app.route("/running_processes")
def running_processes():
    """
    מחזיר רשימה של תהליכים שרצים כרגע.
    """
    return jsonify({"processes": list(processes.keys())})


@app.route("/stop_script/<name>")
def stop_script(name):
    """
    עוצר תהליך רקע לפי שם אם הוא רץ.
    """
    proc = processes.get(name)
    if proc:
        proc.terminate()
        return jsonify({"status": f"terminated {name}"})
    return jsonify({"status": f"{name} not running"}), 404


@app.route("/api/agg_dual")
def agg_dual():
    """
    מחזיר נתונים אגרגטיביים (GFP) וטמפרטורה יחד.
    טוען נתוני GFP ונתוני טמפרטורה מהנתיבים שב-config.
    """
    try:
        with open("config/session_config.json", "r") as f:
            config = json.load(f)

        agg_path = config["paths"]["agg_path"]
        mqtt_path = config["paths"]["mqtt_path"]

        gfp_data = load_recent_agg_csvs(agg_path, highlight_well=1, minutes_back=30)
        if not gfp_data:
            return jsonify({"error": "No GFP data"}), 400

        t0_str = gfp_data[0]["Time_Stamp"]
        t0 = datetime.strptime(t0_str, '%Y-%m-%d %H:%M:%S')
        temp_data = load_temperature_json_series(mqtt_path, t0)

        return jsonify({
            "gfp_data": gfp_data,
            "temp_data": temp_data,
            "t0": t0_str
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/refresh_dual_data")
def refresh_dual_data():
    """
    ריענון ידני של נתוני הגרף הראשי (לכפתור בצד הלקוח).
    פשוט מפנה לקריאה ל-agg_dual.
    """
    return agg_dual()


# הרצת Flask - הפעלת האפליקציה במצב דיבוג
if __name__ == "__main__":
    app.run(debug=True)
from datetime import datetime
import glob

# פונקציה לטעינת סידרת טמפרטורה מקבצי json בתיקייה
def load_temperature_json_series(folder_path, t0, max_files=30):
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

import subprocess
import threading
from utils.agg_loader import load_recent_agg_csvs
import json
from flask import Flask, render_template, jsonify, request, session
from flask_cors import CORS
import os

processes = {}

def run_script(name, path):
    if name in processes:
        return
    def _run():
        processes[name] = subprocess.Popen(["python", path])
        processes[name].wait()
        del processes[name]
    threading.Thread(target=_run).start()


app = Flask(__name__)

app.secret_key = 'your_secret_key'
CORS(app)

@app.route("/")
def index():
    return render_template("index.html")

# נתיב חדש להגדרת נתיבי agg_path ו-mqtt_path ב-session
@app.route("/set_paths", methods=["POST"])
def set_paths():
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

# דוגמה לנתיב שמחזיר טמפרטורה עדכנית
@app.route("/api/temperature")
def temperature():
    try:
        with open("data/mqtt.csv", "r") as f:
            lines = f.readlines()
            last = lines[-1].strip().split(",")
            return jsonify({"time": last[0], "temperature": float(last[1])})
    except:
        return jsonify({"error": "No data"}), 500


@app.route("/api/agg_recent")
def agg_recent():
    try:
        path = session.get("agg_path")
        data = load_recent_agg_csvs(path, highlight_well=1, minutes_back=30)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 50


# API routes for running scripts

@app.route("/start_acclimation")
def start_acclimation():
    run_script("start_1", "scripts/start_1.py")
    return jsonify({"status": "started acclimation"})

@app.route("/run_baseline")
def run_baseline():
    run_script("baseline", "scripts/baseline.py")
    return jsonify({"status": "started baseline"})

@app.route("/start_mqtt")
def start_mqtt():
    run_script("mqtt", "scripts/mqtt.py")
    return jsonify({"status": "started mqtt"})

@app.route("/start_feedback")
def start_feedback():
    run_script("main_feedback", "scripts/main_feedback.py")
    return jsonify({"status": "started feedback"})

@app.route("/start_secure_feedback")
def start_secure_feedback():
    run_script("secure_feedback", "scripts/secure_feedback.py")
    return jsonify({"status": "started secure feedback"})

@app.route("/start_plot")
def start_plot():
    run_script("plot", "scripts/plot_t_chip_every_10_files.py")
    return jsonify({"status": "started plotting"})

if __name__ == "__main__":
    app.run(debug=True)
@app.route("/running_processes")
def running_processes():
    return jsonify({"processes": list(processes.keys())})

@app.route("/stop_script/<name>")
def stop_script(name):
    proc = processes.get(name)
    if proc:
        proc.terminate()
        return jsonify({"status": f"terminated {name}"})
    return jsonify({"status": f"{name} not running"}), 404


# נתיב חדש שמחזיר נתונים אגרגטיביים וטמפרטורה יחד
@app.route("/api/agg_dual")
def agg_dual():
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

# נתיב חדש להפעלת ריענון ידני של הגרף הראשי (לכפתור בצד הלקוח)
@app.route("/refresh_dual_data")
def refresh_dual_data():
    return agg_dual()
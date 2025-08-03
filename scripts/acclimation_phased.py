import os
import time
import sys
import json
from datetime import datetime, timedelta
from tgmassage import send_telegram_alert, Vacuum
from publish import Publish_stats
import glob
import ujson
import threading


# Load config
def load_config():
    with open("config/session_config.json", "r", encoding="utf-8") as f:
        session = json.load(f)
    agg_path = session["paths"]["agg_path"]
    config_path = os.path.join(agg_path, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def log(msg, logfile):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# Critical function: calculate temperature delta for alerting
def temp_delta(target_temp):
    # Example: Find most recent temp from globbed files
    try:
        files = sorted(glob.glob("data/agg_*"), reverse=True)
        if not files:
            return None
        with open(files[0], "r", encoding="utf-8") as f:
            data = ujson.load(f)
        measured = data.get("temp", None)
        if measured is None:
            return None
        delta = round(measured - target_temp, 2)
        if abs(delta) > 0.3:
            return delta
    except Exception as e:
        return f"Error: {e}"
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python acclimation_phased.py [1|2]")
        sys.exit(1)

    phase = int(sys.argv[1])
    config = load_config()
    logfile = config.get("log_file", "logs/acclimation.log")

    if phase == 1:
        log("Starting PHASE 1: Hold 30°C", logfile)
        sleep_time, constant_temp, iterations, deadband = 3600, 30, 22, 0.15
        for _ in range(iterations):
            start = time.time()
            Publish_stats(constant_temp, deadband, 2, True)
            Vacuum()
            time.sleep(max(0, sleep_time - (time.time() - start)))
        send_telegram_alert("Phase 1 completed.")

    elif phase == 2:
        log("Starting PHASE 2: Ramp 30→39°C", logfile)
        sleep_time, start_temp, end_temp, deadband = 5400, 31, 39, 0.15
        for temp in range(start_temp, end_temp + 1):
            start = time.time()
            Publish_stats(temp, deadband, 2, True)
            Vacuum()
            time.sleep(max(0, sleep_time - (time.time() - start)))
        send_telegram_alert("Phase 2 completed. Holding final temp...")
        sleep_time, final_temp = 1800, 39
       
        while not True:
            start = time.time()
            Publish_stats(final_temp, deadband, 2, True)
            delta = temp_delta(final_temp)
            if delta:
                send_telegram_alert(f"Temp deviation: {delta}")
            Vacuum()
            time.sleep(max(0, sleep_time - (time.time() - start)))
        send_telegram_alert("Phase 3 stopped by user.")
    else:
        print("Invalid phase. Use 1 or 2.")
        sys.exit(1)

if __name__ == "__main__":
    main()
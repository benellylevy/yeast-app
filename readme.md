# 🧬 Yeast Control Panel – Intelligent Web-Based Experiment Manager

A full-stack web interface (Flask + HTML/JS + Python) for managing live, image-based yeast experiments involving temperature acclimation, fluorescence expression (GFP), and real-time feedback control.

---

## 🧪 What Is This Experiment?

This system is designed to monitor and regulate **yeast cell cultures** grown on a microfluidic chip under a microscope. The cells express GFP (Green Fluorescent Protein) as a function of stress. The goal is to:

- Maintain cells under **acclimation conditions**
- Slowly raise the temperature to stress levels (from 30°C to 39°C)
- Monitor the **GFP signal** in selected wells
- Trigger real-time **feedback loops** to control stress using external temperature changes

---

## 📦 Features of the Control Panel

- Web-based control interface via Flask
- Realtime plots: GFP expression + chip temperature
- Feedback log display
- Live logs of MQTT temperature values
- Buttons to start/stop each experiment phase
- Green indicators to show active scripts
- Configuration saved between runs

---

## 💻 Installation & Setup

1. **Create and activate environment** (recommended: `cellpose`)

```bash
conda activate cellpose
```

2. **Clone the project and install dependencies**

```bash
git clone https://github.com/YOUR_USERNAME/yeast-app.git
cd yeast-app
pip install -r requirements.txt
```

3. **Ensure your folder is writable**
- The project writes logs and config files to `config/` and into experiment folders you define.

---

## 🧭 Folder Structure per Experiment

When you click "Start New Experiment", the following structure is created:

```
WELLS_YYYYMMDD/
├── IMG/
├── TEMP/
│   └── YYYYMMDDhh/
├── AGG_CSV/
├── AGG_CSV_FIGS/
├── MOVIES/
├── IMG_CSV/
├── config.json
```

The main config paths are written into `config/session_config.json` and persist throughout the session.

---

## 🚀 Running the System

1. **Start the server**

```bash
python app.py
```

2. **Open the UI in a browser**

```
http://localhost:5000
```

3. **Click through the experiment steps as shown below.**

---

## 📋 Experiment Flow & Button Guide

| Step | Button | Description |
|------|--------|-------------|
| 1️⃣ | **Start New Experiment** | Creates new folder and config structure |
| 2️⃣ | **Track Temperature** | Starts `mqtt.py`, logs live JSON temperature files |
| 3️⃣ | **Start Acclimation** | Starts 30°C acclimation phase (phase 1) |
| 4️⃣ | **Skip to Ramp Up** | Starts temperature ramping (30°C → 39°C) over ~12h |
| 5️⃣ | **Analyze Images** | Prompts folder selection (e.g. `IMG/01/`), runs analysis |
| 6️⃣ | **Start Feedback** | Activates real-time feedback loop (uses `secure_feedback_precent.py`) |
| 7️⃣ | **Stop Feedback / Acclimation** | Terminates running scripts |
| 🛠️ | **Compute Baseline** | Uses CSVs to determine baseline GFP value |
| 🧠 | **Graph Display** | Shows dual graph: GFP + Temperature from live data |

---

## 🔧 Config Files

### `config/session_config.json`

Stores persistent paths and parameters:

```json
{
  "paths": {
    "agg_path": "B:/my_experiment/WELLS_20250804",
    "mqtt_path": "B:/my_experiment/WELLS_20250804/TEMP/2025080400"
  },
  "highlight_well": 8,
  "control_well": 36
}
```

### `config.json` (inside experiment folder)

Used by all scripts. Stores temp folder, output files, baseline values.

---

## 📈 Scripts Controlled

| Script | Purpose |
|--------|---------|
| `start_1.py` | Creates new experiment folders and base config |
| `mqtt.py` | Listens to external MQTT broker and logs temperature |
| `analaize.py` | Processes microscope images and outputs CSVs |
| `acclimation_phased.py` | 3-phase acclimation: 30°C hold, ramp-up, final hold |
| `secure_feedback_precent.py` | Core feedback loop using GFP → temperature mapping |
| `baseline.py` | Calculates baseline GFP expression |

---

## 🔐 Safety & Tips

- Never commit your Telegram bot token – use placeholders or `.env`
- Don't reuse experiment folders between runs
- All dynamic parameters are stored in config files
- You can stop any script at any time using the UI

---

## 🧠 Created by Ben Ellevy

Designed for intelligent, flexible, real-time experimentation with genetically engineered yeast.
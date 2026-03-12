"""
logger.py
---------
Saves every battery reading cycle to a CSV log file.
Logs: timestamp, input values, intelligence engine output, AI explanation.

Member-3 responsibility.
Called by: main.py
"""

import csv
import os
from datetime import datetime

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from battery_logic.battery_intelligence_module import BatteryInput, BIMOutput


# -----------------------------
# LOG FILE PATH
# -----------------------------

LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'battery_log.csv')


# -----------------------------
# CSV COLUMNS
# -----------------------------

CSV_HEADERS = [
    "timestamp",
    "cycle",
    "label",
    "soc",
    "voltage_trend",
    "drain_rate",
    "zone",
    "anomaly",
    "recommendation",
    "predicted_range_km",
    "ai_explanation"
]


# -----------------------------
# INITIALIZER
# -----------------------------

def init_logger():
    """
    Creates the logs directory and CSV file with headers if they don't exist.
    Call this once at system startup.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
        print(f"[Logger] Log file created: {LOG_FILE}")
    else:
        print(f"[Logger] Appending to existing log: {LOG_FILE}")


# -----------------------------
# LOG A READING
# -----------------------------

def log_to_csv(
    battery_input: BatteryInput,
    bim_output: BIMOutput,
    label: str = "Unknown",
    cycle: int = 1,
    ai_explanation: str = ""
):
    """
    Appends one battery reading cycle to the CSV log.

    Args:
        battery_input   : raw sensor values
        bim_output      : intelligence engine output
        label           : scenario/source label
        cycle           : reading cycle number
        ai_explanation  : AI-generated explanation string
    """
    row = {
        "timestamp":          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cycle":              cycle,
        "label":              label,
        "soc":                battery_input.soc,
        "voltage_trend":      battery_input.voltage_trend.value,
        "drain_rate":         battery_input.drain_rate.value,
        "zone":               bim_output.zone.value,
        "anomaly":            bim_output.anomaly.value,
        "recommendation":     bim_output.recommendation.value,
        "predicted_range_km": bim_output.predicted_range_km,
        "ai_explanation":     ai_explanation.replace("\n", " ").strip()
    }

    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writerow(row)


# -----------------------------
# READ LOG (utility)
# -----------------------------

def read_log() -> list:
    """
    Reads all rows from the CSV log. Returns list of dicts.
    Useful for testing or future dashboard integration.
    """
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


# -----------------------------
# CLEAR LOG (utility)
# -----------------------------

def clear_log():
    """Wipes the log and rewrites headers. Use carefully."""
    with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
    print("[Logger] Log cleared.")
"""
display.py
----------
Handles all terminal output for the EV Battery Monitoring System.
Now includes trend analysis section.

Member-3 responsibility.
Called by: main.py
"""

import sys
import os
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from battery_logic.battery_intelligence_module import BatteryInput, BIMOutput, BatteryZone, AnomalyStatus
from battery_logic.trend_analyser import TrendReport


# -----------------------------
# COLORS
# -----------------------------

COLORS = {
    "green":  "\033[92m",
    "yellow": "\033[93m",
    "red":    "\033[91m",
    "cyan":   "\033[96m",
    "magenta":"\033[95m",
    "white":  "\033[97m",
    "bold":   "\033[1m",
    "reset":  "\033[0m"
}

ZONE_COLORS = {
    BatteryZone.NOMINAL:   COLORS["green"],
    BatteryZone.DEGRADED:  COLORS["yellow"],
    BatteryZone.CRITICAL:  COLORS["red"]
}

ANOMALY_COLORS = {
    AnomalyStatus.NONE:       COLORS["green"],
    AnomalyStatus.TRANSIENT:  COLORS["yellow"],
    AnomalyStatus.PERSISTENT: COLORS["yellow"],
    AnomalyStatus.SEVERE:     COLORS["red"]
}

TREND_COLORS = {
    "worsening":          COLORS["red"],
    "rapidly declining":  COLORS["red"],
    "steadily declining": COLORS["yellow"],
    "slowly declining":   COLORS["yellow"],
    "stable":             COLORS["green"],
    "improving":          COLORS["green"],
    "recovering":         COLORS["green"],
    "frequent":           COLORS["red"],
    "occasional":         COLORS["yellow"],
    "rare or none":       COLORS["green"],
    "degrading":          COLORS["red"],
}


def _colored(text: str, color: str) -> str:
    return f"{color}{text}{COLORS['reset']}"


def _header(title: str):
    width = 60
    print("\n" + COLORS["bold"] + "=" * width + COLORS["reset"])
    print(COLORS["bold"] + f"  {title}".center(width) + COLORS["reset"])
    print(COLORS["bold"] + "=" * width + COLORS["reset"])


def _section(title: str):
    print(f"\n{COLORS['cyan']}{COLORS['bold']}── {title} {'─' * (50 - len(title))}{COLORS['reset']}")


def _trend_color(value: str) -> str:
    return TREND_COLORS.get(value, COLORS["white"])


# -----------------------------
# MAIN DISPLAY FUNCTION
# -----------------------------

def display_output(
    label: str,
    battery_input: BatteryInput,
    bim_output: BIMOutput,
    explanation: str,
    cycle: int = 1,
    trend: Optional[TrendReport] = None
):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    zone_color = ZONE_COLORS.get(bim_output.zone, COLORS["white"])
    anomaly_color = ANOMALY_COLORS.get(bim_output.anomaly, COLORS["white"])

    _header(f"EV Battery Report  |  Cycle #{cycle}")

    print(f"  Timestamp : {timestamp}")
    print(f"  Source    : {label}")

    # Raw Input
    _section("Battery Input")
    print(f"  SOC (State of Charge) : {battery_input.soc}%")
    print(f"  Voltage Trend         : {battery_input.voltage_trend.value}")
    print(f"  Drain Rate            : {battery_input.drain_rate.value}")

    # Intelligence Engine Output
    _section("Intelligence Analysis")
    print(f"  Zone            : {_colored(bim_output.zone.value, zone_color)}")
    print(f"  Anomaly         : {_colored(bim_output.anomaly.value, anomaly_color)}")
    print(f"  Predicted Range : {bim_output.predicted_range_km} km")
    print(f"  Recommendation  : {bim_output.recommendation.value}")

    # Trend Analysis (only shown after enough data)
    if trend is not None:
        _section("Trend Analysis")
        print(f"  Readings Tracked  : {trend.readings_analysed}")
        print(f"  SOC Trend         : {_colored(trend.soc_trend, _trend_color(trend.soc_trend))}")
        print(f"  Zone Trend        : {_colored(trend.zone_trend, _trend_color(trend.zone_trend))}")
        print(f"  Anomaly Frequency : {_colored(trend.anomaly_frequency, _trend_color(trend.anomaly_frequency))}")
        print(f"  Range Efficiency  : {_colored(trend.range_efficiency, _trend_color(trend.range_efficiency))}")

        if trend.alert_flags:
            print(f"\n  {COLORS['red']}{COLORS['bold']}⚠ ALERTS:{COLORS['reset']}")
            for flag in trend.alert_flags:
                print(f"    {COLORS['red']}→ {flag}{COLORS['reset']}")
        else:
            print(f"\n  {COLORS['green']}✓ No critical patterns detected{COLORS['reset']}")
    else:
        _section("Trend Analysis")
        print(f"  {COLORS['yellow']}Collecting data... trend available after 2 readings{COLORS['reset']}")

    # AI Explanation
    _section("AI Explanation")
    words = explanation.split()
    line = "  "
    for word in words:
        if len(line) + len(word) + 1 > 58:
            print(line)
            line = "  " + word + " "
        else:
            line += word + " "
    if line.strip():
        print(line)

    print("\n" + COLORS["bold"] + "=" * 60 + COLORS["reset"] + "\n")


# -----------------------------
# STARTUP BANNER
# -----------------------------

def display_banner():
    print(COLORS["cyan"] + COLORS["bold"])
    print("=" * 60)
    print("   GenAI-Assisted EV Battery Monitoring System")
    print("   Member-3 : System Integrator | Project Lead")
    print("   [ Trend Detection ENABLED ]")
    print("=" * 60)
    print(COLORS["reset"])


def display_shutdown():
    print(f"\n{COLORS['cyan']}System stopped. All readings saved to logs/battery_log.csv{COLORS['reset']}\n")
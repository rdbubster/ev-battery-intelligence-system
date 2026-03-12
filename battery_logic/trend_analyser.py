"""
trend_analyser.py
-----------------
Tracks battery readings over time and detects patterns.

This is what separates the system from a basic rule-based checker.
Instead of analyzing each reading in isolation, it watches for:

    - SOC declining consistently (battery draining fast)
    - SOC not recovering after expected charge time
    - Zone getting progressively worse (Nominal → Degraded → Critical)
    - Anomalies repeating across multiple readings (persistent fault)
    - Range shrinking faster than SOC drop (efficiency loss)

The TrendAnalyser maintains a rolling window of the last N readings
and produces a TrendReport that gets added to the AI prompt.

Member-3 responsibility.
Called by: main.py, formatter.py
"""

from dataclasses import dataclass, field
from collections import deque
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from battery_logic.battery_intelligence_module import (
    BatteryInput, BIMOutput, BatteryZone, AnomalyStatus
)


# -----------------------------
# CONFIGURATION
# -----------------------------

WINDOW_SIZE = 5   # Number of readings to track for trend analysis


# -----------------------------
# DATA STRUCTURES
# -----------------------------

@dataclass
class ReadingSnapshot:
    """One recorded reading stored in the trend window."""
    soc: float
    zone: BatteryZone
    anomaly: AnomalyStatus
    predicted_range_km: float


@dataclass
class TrendReport:
    """
    Output of TrendAnalyser — a human-readable summary of detected patterns.
    Gets injected into the AI prompt for richer context.
    """
    soc_trend: str                      # "declining", "stable", "recovering"
    zone_trend: str                     # "worsening", "stable", "improving"
    anomaly_frequency: str              # "frequent", "occasional", "none"
    range_efficiency: str               # "degrading", "stable", "improving"
    consecutive_anomalies: int          # How many readings in a row had anomalies
    consecutive_zone_worsening: int     # How many readings zone kept getting worse
    alert_flags: list                   # List of serious pattern alerts
    summary: str                        # One-line plain-English trend summary
    readings_analysed: int              # How many readings were used


# -----------------------------
# TREND ANALYSER
# -----------------------------

class TrendAnalyser:
    """
    Maintains a rolling window of battery readings and detects trends.

    Usage:
        analyser = TrendAnalyser(window_size=5)

        # After each BIM evaluation:
        analyser.record(battery_input, bim_output)
        trend = analyser.analyse()
    """

    ZONE_SEVERITY = {
        BatteryZone.NOMINAL:   0,
        BatteryZone.DEGRADED:  1,
        BatteryZone.CRITICAL:  2
    }

    ANOMALY_SEVERITY = {
        AnomalyStatus.NONE:       0,
        AnomalyStatus.TRANSIENT:  1,
        AnomalyStatus.PERSISTENT: 2,
        AnomalyStatus.SEVERE:     3
    }

    def __init__(self, window_size: int = WINDOW_SIZE):
        self.window_size = window_size
        self.window: deque = deque(maxlen=window_size)

    # -------------------------
    # Record a new reading
    # -------------------------

    def record(self, battery_input: BatteryInput, bim_output: BIMOutput):
        """Add a new reading to the trend window."""
        self.window.append(ReadingSnapshot(
            soc=battery_input.soc,
            zone=bim_output.zone,
            anomaly=bim_output.anomaly,
            predicted_range_km=bim_output.predicted_range_km
        ))

    # -------------------------
    # Analyse trends
    # -------------------------

    def analyse(self) -> Optional[TrendReport]:
        """
        Analyse the current window and return a TrendReport.
        Returns None if fewer than 2 readings recorded (not enough data).
        """
        if len(self.window) < 2:
            return None

        readings = list(self.window)
        n = len(readings)

        # --- SOC Trend ---
        soc_values = [r.soc for r in readings]
        soc_delta = soc_values[-1] - soc_values[0]
        avg_soc_drop_per_reading = soc_delta / (n - 1)

        if avg_soc_drop_per_reading < -5:
            soc_trend = "rapidly declining"
        elif avg_soc_drop_per_reading < -2:
            soc_trend = "steadily declining"
        elif avg_soc_drop_per_reading < 0:
            soc_trend = "slowly declining"
        elif avg_soc_drop_per_reading > 2:
            soc_trend = "recovering"
        else:
            soc_trend = "stable"

        # --- Zone Trend ---
        zone_severities = [self.ZONE_SEVERITY[r.zone] for r in readings]
        zone_delta = zone_severities[-1] - zone_severities[0]

        if zone_delta > 0:
            zone_trend = "worsening"
        elif zone_delta < 0:
            zone_trend = "improving"
        else:
            zone_trend = "stable"

        # --- Anomaly Frequency ---
        anomaly_severities = [self.ANOMALY_SEVERITY[r.anomaly] for r in readings]
        anomaly_count = sum(1 for s in anomaly_severities if s > 0)
        anomaly_ratio = anomaly_count / n

        if anomaly_ratio >= 0.8:
            anomaly_frequency = "frequent"
        elif anomaly_ratio >= 0.4:
            anomaly_frequency = "occasional"
        else:
            anomaly_frequency = "rare or none"

        # --- Consecutive Anomalies (tail streak) ---
        consecutive_anomalies = 0
        for r in reversed(readings):
            if self.ANOMALY_SEVERITY[r.anomaly] > 0:
                consecutive_anomalies += 1
            else:
                break

        # --- Consecutive Zone Worsening (tail streak) ---
        consecutive_zone_worsening = 0
        for i in range(len(readings) - 1, 0, -1):
            if zone_severities[i] > zone_severities[i - 1]:
                consecutive_zone_worsening += 1
            else:
                break

        # --- Range Efficiency ---
        ranges = [r.predicted_range_km for r in readings]
        socs   = [r.soc for r in readings]

        # Compare range-per-SOC-unit at start vs end
        range_per_soc_start = ranges[0]  / max(socs[0], 1)
        range_per_soc_end   = ranges[-1] / max(socs[-1], 1)
        efficiency_delta = range_per_soc_end - range_per_soc_start

        if efficiency_delta < -0.1:
            range_efficiency = "degrading"
        elif efficiency_delta > 0.1:
            range_efficiency = "improving"
        else:
            range_efficiency = "stable"

        # --- Alert Flags ---
        alert_flags = []

        if consecutive_anomalies >= 3:
            alert_flags.append(
                f"PERSISTENT FAULT: Anomaly detected in last {consecutive_anomalies} consecutive readings"
            )

        if consecutive_zone_worsening >= 2:
            alert_flags.append(
                f"ZONE DEGRADATION: Battery zone has worsened for {consecutive_zone_worsening} readings in a row"
            )

        if soc_trend == "rapidly declining":
            alert_flags.append(
                "RAPID DRAIN: SOC dropping faster than expected — check for abnormal load"
            )

        if range_efficiency == "degrading" and zone_trend == "worsening":
            alert_flags.append(
                "EFFICIENCY LOSS: Range shrinking faster than SOC drop — possible cell damage"
            )

        if readings[-1].zone == BatteryZone.CRITICAL and zone_trend == "worsening":
            alert_flags.append(
                "CRITICAL TRAJECTORY: Battery entered critical zone and trend is still worsening"
            )

        # --- Summary ---
        if alert_flags:
            summary = f"⚠ {len(alert_flags)} alert(s) detected. SOC is {soc_trend}, zone is {zone_trend}, anomalies are {anomaly_frequency}."
        else:
            summary = f"SOC is {soc_trend}, zone is {zone_trend}, anomalies are {anomaly_frequency}. No critical patterns detected."

        return TrendReport(
            soc_trend=soc_trend,
            zone_trend=zone_trend,
            anomaly_frequency=anomaly_frequency,
            range_efficiency=range_efficiency,
            consecutive_anomalies=consecutive_anomalies,
            consecutive_zone_worsening=consecutive_zone_worsening,
            alert_flags=alert_flags,
            summary=summary,
            readings_analysed=n
        )

    def has_enough_data(self) -> bool:
        return len(self.window) >= 2

    def reading_count(self) -> int:
        return len(self.window)
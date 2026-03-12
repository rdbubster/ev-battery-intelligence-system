"""
formatter.py
------------
Converts BatteryInput + BIMOutput + TrendReport into a structured prompt
for the GenAI explanation API.

Member-3 responsibility.
Called by: explainer.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from battery_logic.battery_intelligence_module import BatteryInput, BIMOutput
from battery_logic.trend_analyser import TrendReport
from typing import Optional


# -----------------------------
# SYSTEM PROMPT
# -----------------------------

SYSTEM_PROMPT = """You are an intelligent EV Battery Assistant embedded in a Battery Management System.

Your job is to:
1. Explain the current battery condition in simple, clear language.
2. Tell the user WHY the battery is in this state.
3. If trend data is provided, explain what the pattern means for the user.
4. Give 1-2 practical recommendations the user can act on immediately.

Keep your response under 6 sentences. Be direct. Avoid technical jargon.
Do not repeat the raw numbers back — interpret them."""


# -----------------------------
# USER PROMPT BUILDER
# -----------------------------

def format_for_ai(
    battery_input: BatteryInput,
    bim_output: BIMOutput,
    trend: Optional[TrendReport] = None
) -> dict:
    """
    Formats battery data + optional trend into a prompt dict.

    Returns:
        dict with keys: 'system' and 'user'
    """

    user_prompt = f"""Current Battery Status:
- State of Charge (SOC): {battery_input.soc}%
- Voltage Trend: {battery_input.voltage_trend.value}
- Drain Rate: {battery_input.drain_rate.value}

Intelligence Engine Analysis:
- Battery Zone: {bim_output.zone.value}
- Anomaly Detected: {bim_output.anomaly.value}
- System Recommendation: {bim_output.recommendation.value}
- Predicted Remaining Range: {bim_output.predicted_range_km} km"""

    # Inject trend data if available
    if trend is not None:
        alert_text = ""
        if trend.alert_flags:
            alert_text = "\n  Alerts:\n" + "\n".join(f"    - {a}" for a in trend.alert_flags)

        user_prompt += f"""

Historical Trend Analysis (last {trend.readings_analysed} readings):
- SOC Trend: {trend.soc_trend}
- Zone Trend: {trend.zone_trend}
- Anomaly Frequency: {trend.anomaly_frequency}
- Range Efficiency: {trend.range_efficiency}
- Consecutive Anomalies: {trend.consecutive_anomalies}
- Trend Summary: {trend.summary}{alert_text}"""

    user_prompt += "\n\nBased on this data, explain the battery condition and provide actionable advice."

    return {
        "system": SYSTEM_PROMPT,
        "user": user_prompt
    }


# -----------------------------
# JSON FORMAT (for logging/ESP32)
# -----------------------------

def format_as_json(battery_input: BatteryInput, bim_output: BIMOutput) -> dict:
    return {
        "input": {
            "soc": battery_input.soc,
            "voltage_trend": battery_input.voltage_trend.value,
            "drain_rate": battery_input.drain_rate.value
        },
        "output": {
            "zone": bim_output.zone.value,
            "anomaly": bim_output.anomaly.value,
            "recommendation": bim_output.recommendation.value,
            "predicted_range_km": bim_output.predicted_range_km
        }
    }
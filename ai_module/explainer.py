"""
explainer.py
------------
Orchestrates the full AI explanation pipeline.

Flow:
    BatteryInput + BIMOutput + TrendReport
            ↓
        formatter.py  (builds trend-aware prompt)
            ↓
        request.py    (sends to AI)
            ↓
        explanation   (returned to main.py)

Member-3 responsibility.
Called by: main.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from battery_logic.battery_intelligence_module import BatteryInput, BIMOutput
from battery_logic.trend_analyser import TrendReport
from ai_module.formatter import format_for_ai
from ai_module.request import get_ai_explanation
from typing import Optional


def explain_battery_state(
    battery_input: BatteryInput,
    bim_output: BIMOutput,
    trend: Optional[TrendReport] = None
) -> str:
    """
    Full pipeline: battery data + trend → AI explanation string.

    Args:
        battery_input : raw sensor input
        bim_output    : result from BatteryIntelligenceModule
        trend         : optional TrendReport from TrendAnalyser

    Returns:
        str: human-readable AI explanation
    """
    prompt = format_for_ai(battery_input, bim_output, trend)
    explanation = get_ai_explanation(prompt)
    return explanation
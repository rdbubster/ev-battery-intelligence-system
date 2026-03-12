"""
battery_simulation.py
---------------------
Simulates battery sensor readings until ESP32 hardware is connected.
Member-2 will replace this with real ESP32 serial data in Week 3.

Simulation modes:
    - STATIC   : returns a fixed battery state (default)
    - SEQUENCE : cycles through a list of scenarios automatically
    - RANDOM   : generates randomized battery readings
"""

import random
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from battery_logic.battery_intelligence_module import BatteryInput, VoltageTrend, DrainRate


# -----------------------------
# SIMULATION MODE
# -----------------------------

SIMULATION_MODE = "SEQUENCE"   # Options: "STATIC", "SEQUENCE", "RANDOM"


# -----------------------------
# PREDEFINED SCENARIOS
# -----------------------------

SCENARIOS = [
    {
        "label": "Nominal - Fully Charged, Stable",
        "input": BatteryInput(
            soc=90,
            voltage_trend=VoltageTrend.STABLE,
            drain_rate=DrainRate.SLOW
        )
    },
    {
        "label": "Degraded - Mid Charge, Slight Fluctuation",
        "input": BatteryInput(
            soc=55,
            voltage_trend=VoltageTrend.SLIGHT_FLUCTUATION,
            drain_rate=DrainRate.MODERATE
        )
    },
    {
        "label": "Degraded - Sudden Drop, Moderate Drain",
        "input": BatteryInput(
            soc=48,
            voltage_trend=VoltageTrend.SUDDEN_DROP,
            drain_rate=DrainRate.MODERATE
        )
    },
    {
        "label": "Critical - Low SOC, Fast Drain",
        "input": BatteryInput(
            soc=22,
            voltage_trend=VoltageTrend.STABLE,
            drain_rate=DrainRate.FAST
        )
    },
    {
        "label": "Critical - Severe Instability Override",
        "input": BatteryInput(
            soc=75,
            voltage_trend=VoltageTrend.REPEATED_INSTABILITY,
            drain_rate=DrainRate.ABNORMALLY_FAST
        )
    },
]

# Internal index for SEQUENCE mode
_scenario_index = 0


# -----------------------------
# STATIC MODE
# -----------------------------

def _get_static_input() -> BatteryInput:
    """Returns a fixed battery state. Edit values here to test specific scenarios."""
    return BatteryInput(
        soc=65,
        voltage_trend=VoltageTrend.STABLE,
        drain_rate=DrainRate.MODERATE
    )


# -----------------------------
# SEQUENCE MODE
# -----------------------------

def _get_next_scenario() -> tuple:
    """Cycles through predefined scenarios one by one."""
    global _scenario_index
    scenario = SCENARIOS[_scenario_index % len(SCENARIOS)]
    _scenario_index += 1
    return scenario["label"], scenario["input"]


# -----------------------------
# RANDOM MODE
# -----------------------------

def _get_random_input() -> BatteryInput:
    """Generates a random battery reading for stress testing."""
    return BatteryInput(
        soc=round(random.uniform(5, 100), 1),
        voltage_trend=random.choice(list(VoltageTrend)),
        drain_rate=random.choice(list(DrainRate))
    )


# -----------------------------
# PUBLIC INTERFACE
# -----------------------------

def get_simulated_input() -> tuple:
    """
    Returns (label, BatteryInput) based on SIMULATION_MODE.
    This is the function called by main.py.
    """
    if SIMULATION_MODE == "STATIC":
        inp = _get_static_input()
        return "Static Test Input", inp

    elif SIMULATION_MODE == "SEQUENCE":
        return _get_next_scenario()

    elif SIMULATION_MODE == "RANDOM":
        inp = _get_random_input()
        return "Random Input", inp

    else:
        raise ValueError(f"Unknown SIMULATION_MODE: {SIMULATION_MODE}")


def get_all_scenarios() -> list:
    """Returns all predefined scenarios. Used by test runner."""
    return SCENARIOS
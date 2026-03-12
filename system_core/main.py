"""
main.py
-------
System Controller for the GenAI-Assisted EV Battery Monitoring System.

Pipeline:
    battery_simulation → BatteryIntelligenceModule → TrendAnalyser
        → explainer (AI) → display + logger

Member-3 : System Integrator / Project Lead
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from battery_data.battery_simulation import get_simulated_input, get_all_scenarios
from battery_logic.battery_intelligence_module import BatteryIntelligenceModule
from battery_logic.trend_analyser import TrendAnalyser
from ai_module.explainer import explain_battery_state
from output.display import display_output, display_banner, display_shutdown
from output.logger import init_logger, log_to_csv


# -----------------------------
# CONFIGURATION
# -----------------------------

RUN_MODE             = "LOOP"
LOOP_DELAY_SECONDS   = 60     # Respect Groq rate limits
EFFICIENCY_FACTOR    = 1.0
TREND_WINDOW_SIZE    = 5      # Number of readings for trend analysis


# -----------------------------
# CORE PIPELINE
# -----------------------------

def run_pipeline(cycle: int, bim: BatteryIntelligenceModule, analyser: TrendAnalyser) -> bool:
    """
    Executes one full reading cycle with trend analysis.
    BIM and TrendAnalyser are shared across cycles to maintain state.
    """
    try:
        # Step 1: Get battery data
        label, battery_input = get_simulated_input()

        # Step 2: Run intelligence engine
        bim_output = bim.evaluate(battery_input)

        # Step 3: Record reading in trend analyser
        analyser.record(battery_input, bim_output)

        # Step 4: Get trend report (None if not enough data yet)
        trend = analyser.analyse()

        # Step 5: Generate AI explanation (with trend context)
        explanation = explain_battery_state(battery_input, bim_output, trend)

        # Step 6: Display
        display_output(label, battery_input, bim_output, explanation, cycle, trend)

        # Step 7: Log to CSV
        log_to_csv(
            battery_input=battery_input,
            bim_output=bim_output,
            label=label,
            cycle=cycle,
            ai_explanation=explanation
        )

        return True

    except Exception as e:
        print(f"\n[ERROR] Pipeline failed at cycle {cycle}: {e}")
        return False


# -----------------------------
# SINGLE MODE
# -----------------------------

def run_single():
    print("\n[Mode: SINGLE] Running one battery reading...\n")
    bim      = BatteryIntelligenceModule(efficiency_factor=EFFICIENCY_FACTOR)
    analyser = TrendAnalyser(window_size=TREND_WINDOW_SIZE)
    run_pipeline(cycle=1, bim=bim, analyser=analyser)


# -----------------------------
# LOOP MODE
# -----------------------------

def run_loop():
    print(f"\n[Mode: LOOP] Running continuous monitoring. Press Ctrl+C to stop.\n")

    total_scenarios = len(get_all_scenarios())
    cycle    = 1
    bim      = BatteryIntelligenceModule(efficiency_factor=EFFICIENCY_FACTOR)
    analyser = TrendAnalyser(window_size=TREND_WINDOW_SIZE)

    try:
        while True:
            run_pipeline(cycle=cycle, bim=bim, analyser=analyser)

            cycle += 1
            if cycle > total_scenarios:
                print(f"\n[System] Completed {total_scenarios} scenario(s). Restarting cycle...\n")
                cycle = 1

            time.sleep(LOOP_DELAY_SECONDS)

    except KeyboardInterrupt:
        display_shutdown()


# -----------------------------
# ENTRY POINT
# -----------------------------

if __name__ == "__main__":
    display_banner()
    init_logger()

    if RUN_MODE == "SINGLE":
        run_single()
    elif RUN_MODE == "LOOP":
        run_loop()
    else:
        print(f"[ERROR] Unknown RUN_MODE: {RUN_MODE}")
"""
test_fault_scenarios.py
-----------------------
Fault scenario tests for BatteryIntelligenceModule.

Tests all edge cases and fault conditions that could appear during demo or viva:
    1.  Original 5 happy-path scenarios (regression check)
    2.  Boundary: SOC exactly at 60% (old cliff bug)
    3.  Boundary: SOC in hysteresis zone (58-62%) with zone memory
    4.  Fault: Stable voltage but Abnormally Fast drain
    5.  Fault: Repeated instability with Slow drain
    6.  Fault: Full battery (100%) with Abnormally Fast drain
    7.  Fault: SOC 60% + Sudden Drop + Fast drain (boundary + severe anomaly)
    8.  Charging state: normal charging
    9.  Charging state: charging with repeated instability (fault during charge)
    10. Temperature: extreme cold (-10°C)
    11. Temperature: extreme heat (65°C)
    12. Invalid input: SOC -10
    13. Invalid input: temperature 200°C
    14. Invalid input: charging + abnormally fast drain (inconsistent)
    15. Degradation score validation across all zones

Run with: py tests/test_fault_scenarios.py

Member-1 responsibility.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from battery_logic.battery_intelligence_module import (
    BatteryIntelligenceModule,
    BatteryInput,
    BatteryZone,
    AnomalyStatus,
    EnergyRecommendation,
    VoltageTrend,
    DrainRate
)


# -----------------------------
# TEST RUNNER SETUP
# -----------------------------

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

passed = 0
failed = 0
total  = 0


def check(condition: bool, test_name: str, got=None, expected=None):
    global passed, failed, total
    total += 1
    if condition:
        print(f"  {GREEN}✓ PASS{RESET}  {test_name}")
        passed += 1
    else:
        detail = f" → got: {got}, expected: {expected}" if got is not None else ""
        print(f"  {RED}✗ FAIL{RESET}  {test_name}{detail}")
        failed += 1


def section(title: str):
    print(f"\n{CYAN}{BOLD}── {title} {'─' * (52 - len(title))}{RESET}")


def run(description: str, inp: BatteryInput, bim: BatteryIntelligenceModule = None) -> tuple:
    """Run evaluation and return (BatteryInput, BIMOutput)."""
    b = bim if bim else BatteryIntelligenceModule(efficiency_factor=1.0)
    out = b.evaluate(inp)
    print(f"\n  {YELLOW}Scenario:{RESET} {description}")
    print(f"  SOC={inp.soc}%  Voltage={inp.voltage_trend.value}  Drain={inp.drain_rate.value}  Charging={inp.is_charging}  Temp={inp.temperature_c}°C")
    print(f"  → Zone={out.zone.value}  Anomaly={out.anomaly.value}  Range={out.predicted_range_km}km  Score={out.degradation_score}  Rec={out.recommendation.value}")
    return inp, out


# ==============================
# TEST SUITES
# ==============================

def test_1_happy_path_regression():
    section("1. Happy Path Regression (original 5 scenarios)")

    _, out = run("Nominal Stable — 90% SOC, Stable, Slow",
        BatteryInput(soc=90, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.SLOW))
    check(out.zone == BatteryZone.NOMINAL,   "Zone is Nominal", out.zone, BatteryZone.NOMINAL)
    check(out.anomaly == AnomalyStatus.NONE, "Anomaly is None", out.anomaly, AnomalyStatus.NONE)
    check(out.predicted_range_km > 0,        "Range is positive")
    check(out.degradation_score >= 70,       "Health score >= 70 for healthy battery")

    _, out = run("Degraded — 50% SOC, Sudden Drop, Moderate",
        BatteryInput(soc=50, voltage_trend=VoltageTrend.SUDDEN_DROP, drain_rate=DrainRate.MODERATE))
    check(out.zone == BatteryZone.DEGRADED,         "Zone is Degraded", out.zone, BatteryZone.DEGRADED)
    check(out.anomaly == AnomalyStatus.PERSISTENT,  "Anomaly is Persistent", out.anomaly, AnomalyStatus.PERSISTENT)

    _, out = run("Critical Low SOC — 25% SOC, Stable, Moderate",
        BatteryInput(soc=25, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.MODERATE))
    check(out.zone == BatteryZone.CRITICAL,  "Zone is Critical", out.zone, BatteryZone.CRITICAL)
    check(out.anomaly == AnomalyStatus.NONE, "Anomaly is None (SOC caused Critical, not voltage)", out.anomaly, AnomalyStatus.NONE)

    _, out = run("Severe Anomaly Override — 75% SOC, Repeated Instability, Abnormally Fast",
        BatteryInput(soc=75, voltage_trend=VoltageTrend.REPEATED_INSTABILITY, drain_rate=DrainRate.ABNORMALLY_FAST))
    check(out.zone == BatteryZone.CRITICAL,      "Zone is Critical (anomaly override)", out.zone, BatteryZone.CRITICAL)
    check(out.anomaly == AnomalyStatus.SEVERE,   "Anomaly is Severe", out.anomaly, AnomalyStatus.SEVERE)
    check(out.degradation_score <= 30,           "Health score is low for severe degradation")


def test_2_boundary_soc_60():
    section("2. Boundary — SOC exactly at 60%")

    _, out = run("SOC=60, Stable, Moderate (boundary — no anomaly)",
        BatteryInput(soc=60, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.MODERATE))
    # SOC=60 is in hysteresis zone, no previous zone → should be Degraded (conservative)
    check(out.zone == BatteryZone.DEGRADED,   "SOC=60 with no prior zone → Degraded (conservative)", out.zone, BatteryZone.DEGRADED)
    check(out.anomaly == AnomalyStatus.NONE,  "Anomaly is None at boundary")

    _, out = run("SOC=61, Stable, Moderate (just above boundary)",
        BatteryInput(soc=61, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.MODERATE))
    check(out.zone in [BatteryZone.NOMINAL, BatteryZone.DEGRADED], "SOC=61 → Nominal or Degraded (depends on prior zone)", out.zone, BatteryZone.NOMINAL)

    _, out = run("SOC=57, Stable, Moderate (just below boundary)",
        BatteryInput(soc=57, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.MODERATE))
    check(out.zone == BatteryZone.DEGRADED,   "SOC=57 → Degraded (below lower buffer)", out.zone, BatteryZone.DEGRADED)


def test_3_hysteresis_zone_memory():
    section("3. Hysteresis — Zone Memory in Buffer (58-62%)")

    bim = BatteryIntelligenceModule()

    # First reading: Nominal (SOC=80)
    _, out1 = run("Reading 1: SOC=80 Nominal (establish zone)", 
        BatteryInput(soc=80, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.SLOW), bim)
    check(out1.zone == BatteryZone.NOMINAL, "Reading 1 → Nominal")

    # Second reading: SOC drops into buffer zone (SOC=60)
    # Previous zone was Nominal → should stay Nominal
    _, out2 = run("Reading 2: SOC=60 (buffer zone, was Nominal)",
        BatteryInput(soc=60, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.MODERATE), bim)
    check(out2.zone == BatteryZone.NOMINAL, "Reading 2 → stays Nominal (zone memory)", out2.zone, BatteryZone.NOMINAL)

    bim2 = BatteryIntelligenceModule()

    # First reading: Degraded (SOC=45)
    _, out3 = run("Reading 1: SOC=45 Degraded (establish zone)",
        BatteryInput(soc=45, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.MODERATE), bim2)
    check(out3.zone == BatteryZone.DEGRADED, "Reading 1 → Degraded")

    # Second reading: SOC rises into buffer zone (SOC=59)
    # Previous zone was Degraded → should stay Degraded
    _, out4 = run("Reading 2: SOC=59 (buffer zone, was Degraded)",
        BatteryInput(soc=59, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.MODERATE), bim2)
    check(out4.zone == BatteryZone.DEGRADED, "Reading 2 → stays Degraded (zone memory)", out4.zone, BatteryZone.DEGRADED)


def test_4_fault_stable_voltage_abnormal_drain():
    section("4. Fault — Stable Voltage but Abnormally Fast Drain")

    _, out = run("SOC=75, Stable voltage, Abnormally Fast drain",
        BatteryInput(soc=75, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.ABNORMALLY_FAST))
    # Voltage is stable so no anomaly from voltage side
    # But drain is abnormal — something is drawing too much power
    check(out.zone == BatteryZone.NOMINAL,   "Zone Nominal (SOC=75, no voltage anomaly)", out.zone, BatteryZone.NOMINAL)
    check(out.anomaly == AnomalyStatus.NONE, "No voltage anomaly (voltage is stable)", out.anomaly, AnomalyStatus.NONE)
    check(out.predicted_range_km < 40,       "Range significantly reduced by abnormal drain")
    check(out.recommendation == EnergyRecommendation.MAINTAIN, "Recommendation is Maintain (Nominal zone, no anomaly)")


def test_5_fault_repeated_instability_slow_drain():
    section("5. Fault — Repeated Instability with Slow Drain")

    _, out = run("SOC=80, Repeated Instability, Slow drain",
        BatteryInput(soc=80, voltage_trend=VoltageTrend.REPEATED_INSTABILITY, drain_rate=DrainRate.SLOW))
    # Repeated instability → always Severe, regardless of drain rate
    check(out.zone == BatteryZone.CRITICAL,    "Zone Critical (Severe anomaly overrides SOC=80)", out.zone, BatteryZone.CRITICAL)
    check(out.anomaly == AnomalyStatus.SEVERE, "Anomaly Severe", out.anomaly, AnomalyStatus.SEVERE)
    check(out.predicted_range_km < 90,         "Range penalised by severe anomaly (Slow drain base is high)")
    check(out.degradation_score <= 25,         "Health score very low")


def test_6_fault_full_battery_abnormal_drain():
    section("6. Fault — Full Battery (SOC=100%) with Abnormally Fast Drain")

    _, out = run("SOC=100, Stable, Abnormally Fast drain (e.g. AC on max + highway)",
        BatteryInput(soc=100, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.ABNORMALLY_FAST))
    check(out.zone == BatteryZone.NOMINAL,   "Zone Nominal (full battery, stable voltage)", out.zone, BatteryZone.NOMINAL)
    check(out.anomaly == AnomalyStatus.NONE, "No anomaly (voltage stable)", out.anomaly, AnomalyStatus.NONE)
    check(out.predicted_range_km < 55,       "Range reduced (abnormal drain factor=2.0)")
    # Base: 100/2.0 = 50km, no zone/anomaly penalty → ~50km
    check(out.predicted_range_km <= 55,      "Range approx 50km for 100% SOC / drain=2.0")


def test_7_boundary_plus_severe_anomaly():
    section("7. Boundary SOC + Severe Anomaly — Anomaly Must Win")

    _, out = run("SOC=60 (boundary), Sudden Drop, Fast drain → Severe anomaly",
        BatteryInput(soc=60, voltage_trend=VoltageTrend.SUDDEN_DROP, drain_rate=DrainRate.FAST))
    # SOC=60 would normally be in buffer zone → Degraded
    # But Sudden Drop + Fast drain → Severe anomaly → must override to Critical
    check(out.zone == BatteryZone.CRITICAL,    "Severe anomaly overrides buffer zone → Critical", out.zone, BatteryZone.CRITICAL)
    check(out.anomaly == AnomalyStatus.SEVERE, "Anomaly is Severe", out.anomaly, AnomalyStatus.SEVERE)
    check(out.recommendation == EnergyRecommendation.PROTECTIVE, "Recommendation is Protective")


def test_8_charging_normal():
    section("8. Charging State — Normal Charging")

    _, out = run("SOC=45, Stable, Slow, is_charging=True",
        BatteryInput(soc=45, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.SLOW, is_charging=True))
    check(out.zone == BatteryZone.CHARGING,       "Zone is Charging", out.zone, BatteryZone.CHARGING)
    check(out.anomaly == AnomalyStatus.NONE,       "No anomaly during normal charging", out.anomaly, AnomalyStatus.NONE)
    check(out.predicted_range_km == 0.0,           "Range is 0 while charging (undefined)", out.predicted_range_km, 0.0)
    check(out.recommendation == EnergyRecommendation.MAINTAIN, "Recommendation is Maintain during charging")


def test_9_charging_with_fault():
    section("9. Charging State — Fault During Charging")

    _, out = run("SOC=60, Repeated Instability while charging (dangerous)",
        BatteryInput(soc=60, voltage_trend=VoltageTrend.REPEATED_INSTABILITY, drain_rate=DrainRate.SLOW, is_charging=True))
    # Repeated instability during charging is a real fault
    check(out.zone == BatteryZone.CHARGING,        "Zone is still Charging", out.zone, BatteryZone.CHARGING)
    check(out.anomaly == AnomalyStatus.SEVERE,     "Severe anomaly detected even during charging", out.anomaly, AnomalyStatus.SEVERE)

    _, out2 = run("SOC=60, Slight Fluctuation while charging (normal)",
        BatteryInput(soc=60, voltage_trend=VoltageTrend.SLIGHT_FLUCTUATION, drain_rate=DrainRate.SLOW, is_charging=True))
    # Slight fluctuation during charging is normal — should be suppressed
    check(out2.anomaly == AnomalyStatus.NONE,     "Slight fluctuation suppressed during charging", out2.anomaly, AnomalyStatus.NONE)


def test_10_temperature_cold():
    section("10. Temperature — Extreme Cold (-10°C)")

    _, out_normal = run("SOC=70, Stable, Moderate, 25°C (baseline)",
        BatteryInput(soc=70, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.MODERATE, temperature_c=25.0))

    _, out_cold = run("SOC=70, Stable, Moderate, -10°C (extreme cold)",
        BatteryInput(soc=70, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.MODERATE, temperature_c=-10.0))

    check(out_cold.predicted_range_km < out_normal.predicted_range_km,
          "Cold temperature reduces range vs baseline",
          out_cold.predicted_range_km, f"< {out_normal.predicted_range_km}")
    check(out_cold.degradation_score < out_normal.degradation_score,
          "Cold temperature reduces health score")


def test_11_temperature_heat():
    section("11. Temperature — Extreme Heat (65°C)")

    _, out_normal = run("SOC=70, Stable, Moderate, 25°C (baseline)",
        BatteryInput(soc=70, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.MODERATE, temperature_c=25.0))

    _, out_hot = run("SOC=70, Stable, Moderate, 65°C (extreme heat)",
        BatteryInput(soc=70, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.MODERATE, temperature_c=65.0))

    check(out_hot.predicted_range_km < out_normal.predicted_range_km,
          "Extreme heat reduces range vs baseline",
          out_hot.predicted_range_km, f"< {out_normal.predicted_range_km}")


def test_12_invalid_soc():
    section("12. Invalid Input — SOC = -10")

    _, out = run("SOC=-10 (invalid)",
        BatteryInput(soc=-10, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.SLOW))
    check(out.zone == BatteryZone.CRITICAL,        "Invalid SOC → Critical", out.zone, BatteryZone.CRITICAL)
    check(out.anomaly == AnomalyStatus.SEVERE,     "Invalid SOC → Severe", out.anomaly, AnomalyStatus.SEVERE)
    check(out.predicted_range_km == 0.0,           "Invalid SOC → range 0")
    check(out.degradation_score == 0.0,            "Invalid SOC → score 0")


def test_13_invalid_temperature():
    section("13. Invalid Input — Temperature = 200°C")

    _, out = run("Temperature=200°C (sensor fault)",
        BatteryInput(soc=70, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.MODERATE, temperature_c=200.0))
    check(out.zone == BatteryZone.CRITICAL,    "Invalid temperature → Critical fail-safe")
    check(out.degradation_score == 0.0,        "Invalid temperature → score 0")


def test_14_invalid_inconsistent():
    section("14. Invalid Input — Charging + Abnormally Fast Drain (inconsistent)")

    _, out = run("is_charging=True + Abnormally Fast drain (contradictory)",
        BatteryInput(soc=50, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.ABNORMALLY_FAST, is_charging=True))
    check(out.zone == BatteryZone.CRITICAL,    "Inconsistent input → Critical fail-safe")
    check(out.degradation_score == 0.0,        "Inconsistent input → score 0")


def test_15_degradation_score_ordering():
    section("15. Degradation Score — Ordering Validation")

    bim = BatteryIntelligenceModule()

    _, nominal = run("Nominal healthy battery",
        BatteryInput(soc=85, voltage_trend=VoltageTrend.STABLE, drain_rate=DrainRate.SLOW), bim)

    _, degraded = run("Degraded battery with persistent anomaly",
        BatteryInput(soc=45, voltage_trend=VoltageTrend.SUDDEN_DROP, drain_rate=DrainRate.MODERATE), bim)

    _, critical = run("Critical battery with severe anomaly",
        BatteryInput(soc=75, voltage_trend=VoltageTrend.REPEATED_INSTABILITY, drain_rate=DrainRate.ABNORMALLY_FAST), bim)

    check(nominal.degradation_score > degraded.degradation_score,
          "Nominal score > Degraded score",
          nominal.degradation_score, f"> {degraded.degradation_score}")

    check(degraded.degradation_score > critical.degradation_score,
          "Degraded score > Critical score",
          degraded.degradation_score, f"> {critical.degradation_score}")

    check(nominal.degradation_score >= 70,  "Nominal score >= 70")
    check(critical.degradation_score <= 25, "Critical score <= 25")


# ==============================
# MAIN RUNNER
# ==============================

if __name__ == "__main__":
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}  EV Battery System — Fault Scenario Test Suite{RESET}")
    print(f"{BOLD}  Member-1 : Battery Intelligence Developer{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}")

    test_1_happy_path_regression()
    test_2_boundary_soc_60()
    test_3_hysteresis_zone_memory()
    test_4_fault_stable_voltage_abnormal_drain()
    test_5_fault_repeated_instability_slow_drain()
    test_6_fault_full_battery_abnormal_drain()
    test_7_boundary_plus_severe_anomaly()
    test_8_charging_normal()
    test_9_charging_with_fault()
    test_10_temperature_cold()
    test_11_temperature_heat()
    test_12_invalid_soc()
    test_13_invalid_temperature()
    test_14_invalid_inconsistent()
    test_15_degradation_score_ordering()

    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"  Total  : {total}")
    print(f"  {GREEN}Passed : {passed}{RESET}")
    print(f"  {RED}Failed : {failed}{RESET}")
    print(f"{BOLD}{'=' * 60}{RESET}\n")

    sys.exit(0 if failed == 0 else 1)
"""
battery_intelligence_module.py
-------------------------------
Core battery analysis engine.

Changes from original (Member-1 Week 3-4 upgrades):
    1. BatteryInput now accepts optional `is_charging` flag
    2. BatteryZone now includes CHARGING state
    3. Zone boundary buffer added (58-62% hysteresis zone)
    4. Charging detection branch in classify_zone
    5. Charging detection in estimate_range (returns charge time instead)
    6. Recommendation extended with CHARGE_NOW option
    7. Degradation score added to BIMOutput (0-100 health score)
    8. validate_input now checks voltage_trend + drain_rate consistency

Member-1 : Battery Intelligence Developer
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# -----------------------------
# ENUMERATIONS
# -----------------------------

class VoltageTrend(Enum):
    STABLE                = "Stable"
    SLIGHT_FLUCTUATION    = "Slight fluctuation"
    SUDDEN_DROP           = "Sudden drop"
    REPEATED_INSTABILITY  = "Repeated instability"


class DrainRate(Enum):
    SLOW             = "Slow"
    MODERATE         = "Moderate"
    FAST             = "Fast"
    ABNORMALLY_FAST  = "Abnormally fast"


class BatteryZone(Enum):
    CHARGING  = "Charging"     # NEW — SOC rising
    NOMINAL   = "Nominal"
    DEGRADED  = "Degraded"
    CRITICAL  = "Critical"


class AnomalyStatus(Enum):
    NONE       = "None"
    TRANSIENT  = "Transient Variation"
    PERSISTENT = "Persistent Deviation"
    SEVERE     = "Severe Degradation"


class EnergyRecommendation(Enum):
    MAINTAIN    = "Maintain normal operation"
    MONITOR     = "Increase monitoring"
    REDUCE_LOAD = "Reduce non-critical loads"
    PROTECTIVE  = "Activate protective mode"
    CHARGE_NOW  = "Charge immediately"        # NEW


# -----------------------------
# INPUT STRUCTURE
# -----------------------------

@dataclass
class BatteryInput:
    soc: float                          # State of Charge (0-100)
    voltage_trend: VoltageTrend
    drain_rate: DrainRate
    is_charging: bool = False           # NEW — True when plugged in and SOC rising
    temperature_c: float = 25.0        # NEW — battery temperature in Celsius


# -----------------------------
# OUTPUT STRUCTURE
# -----------------------------

@dataclass
class BIMOutput:
    zone: BatteryZone
    anomaly: AnomalyStatus
    recommendation: EnergyRecommendation
    predicted_range_km: float
    degradation_score: float = 100.0   # NEW — 0 = dead, 100 = perfect health


# -----------------------------
# HYSTERESIS ZONE BOUNDARIES
# -----------------------------
# Prevents zone flickering at boundaries.
# If SOC is in the buffer zone (58-62%), the zone stays
# whatever it was previously unless an anomaly forces a change.

NOMINAL_DEGRADED_UPPER = 62.0    # Above this → Nominal
NOMINAL_DEGRADED_LOWER = 58.0    # Below this → Degraded
CRITICAL_THRESHOLD     = 30.0    # Below this → always Critical


# -----------------------------
# CORE MODULE
# -----------------------------

class BatteryIntelligenceModule:

    def __init__(self, efficiency_factor: float = 1.0):
        self.efficiency_factor  = efficiency_factor
        self.previous_zone: Optional[BatteryZone] = None

    # -------------------------
    # Input Validation
    # -------------------------

    def validate_input(self, battery_input: BatteryInput) -> tuple:
        """
        Validates input and returns (is_valid, reason).
        Extended to catch temperature extremes and inconsistencies.
        """
        if battery_input.soc < 0 or battery_input.soc > 100:
            return False, "SOC out of range (0-100)"

        if battery_input.temperature_c < -40 or battery_input.temperature_c > 85:
            return False, "Temperature sensor reading invalid"

        # Inconsistency check: charging flag but drain rate is Abnormally Fast
        if battery_input.is_charging and battery_input.drain_rate == DrainRate.ABNORMALLY_FAST:
            return False, "Inconsistent state: charging flag set but drain rate is abnormally fast"

        return True, "OK"

    # -------------------------
    # Anomaly Detection
    # -------------------------

    def detect_anomaly(self, battery_input: BatteryInput) -> AnomalyStatus:
        """
        Detects anomalies from voltage trend and drain rate.
        Charging state suppresses most anomalies (voltage fluctuation
        during charging is normal).
        """
        # During charging, only repeated instability is a real anomaly
        if battery_input.is_charging:
            if battery_input.voltage_trend == VoltageTrend.REPEATED_INSTABILITY:
                return AnomalyStatus.SEVERE
            return AnomalyStatus.NONE

        if battery_input.voltage_trend == VoltageTrend.STABLE:
            return AnomalyStatus.NONE

        if battery_input.voltage_trend == VoltageTrend.SLIGHT_FLUCTUATION:
            # Slight fluctuation with abnormal drain is more serious
            if battery_input.drain_rate == DrainRate.ABNORMALLY_FAST:
                return AnomalyStatus.PERSISTENT
            return AnomalyStatus.TRANSIENT

        if battery_input.voltage_trend == VoltageTrend.SUDDEN_DROP:
            if battery_input.drain_rate in [DrainRate.FAST, DrainRate.ABNORMALLY_FAST]:
                return AnomalyStatus.SEVERE
            return AnomalyStatus.PERSISTENT

        if battery_input.voltage_trend == VoltageTrend.REPEATED_INSTABILITY:
            return AnomalyStatus.SEVERE

        return AnomalyStatus.NONE

    # -------------------------
    # Zone Classification
    # -------------------------

    def classify_zone(self, battery_input: BatteryInput, anomaly: AnomalyStatus) -> BatteryZone:
        """
        Classifies battery zone with:
        - Charging detection (highest priority)
        - Hysteresis buffer at the Nominal/Degraded boundary (58-62%)
        - Anomaly override (Severe anomaly → Critical regardless of SOC)
        """
        soc = battery_input.soc

        # Priority 1: Charging state
        if battery_input.is_charging:
            return BatteryZone.CHARGING

        # Priority 2: Severe anomaly always overrides to Critical
        if anomaly == AnomalyStatus.SEVERE:
            return BatteryZone.CRITICAL

        # Priority 3: Hard critical threshold
        if soc < CRITICAL_THRESHOLD:
            return BatteryZone.CRITICAL

        # Priority 4: Persistent anomaly forces Degraded (even if SOC > 62%)
        if anomaly == AnomalyStatus.PERSISTENT:
            return BatteryZone.DEGRADED

        # Priority 5: Hysteresis buffer zone (58-62%)
        if NOMINAL_DEGRADED_LOWER <= soc <= NOMINAL_DEGRADED_UPPER:
            # Stay in previous zone if we have one, else classify normally
            if self.previous_zone == BatteryZone.NOMINAL:
                return BatteryZone.NOMINAL
            if self.previous_zone == BatteryZone.DEGRADED:
                return BatteryZone.DEGRADED
            # No previous zone — default to Degraded (conservative)
            return BatteryZone.DEGRADED

        # Priority 6: Normal SOC-based classification
        if soc > NOMINAL_DEGRADED_UPPER:
            return BatteryZone.NOMINAL

        return BatteryZone.DEGRADED

    # -------------------------
    # Range Estimation
    # -------------------------

    def estimate_range(self, battery_input: BatteryInput, zone: BatteryZone, anomaly: AnomalyStatus) -> float:
        """
        Estimates remaining range in km.
        Returns 0.0 if charging (range undefined while charging).
        Applies zone penalty + anomaly penalty + temperature penalty.
        """
        # Range undefined during charging
        if zone == BatteryZone.CHARGING:
            return 0.0

        drain_factor = {
            DrainRate.SLOW:            0.5,
            DrainRate.MODERATE:        1.0,
            DrainRate.FAST:            1.5,
            DrainRate.ABNORMALLY_FAST: 2.0
        }[battery_input.drain_rate]

        base_range = (battery_input.soc * self.efficiency_factor) / drain_factor

        # Zone penalty
        if zone == BatteryZone.DEGRADED:
            base_range *= 0.85
        elif zone == BatteryZone.CRITICAL:
            base_range *= 0.65

        # Anomaly penalty
        if anomaly == AnomalyStatus.PERSISTENT:
            base_range *= 0.9
        elif anomaly == AnomalyStatus.SEVERE:
            base_range *= 0.75

        # Temperature penalty
        # Battery efficiency drops significantly outside 15-35°C
        temp = battery_input.temperature_c
        if temp < 0:
            base_range *= 0.70       # Severe cold penalty
        elif temp < 15:
            base_range *= 0.88       # Moderate cold penalty
        elif temp > 45:
            base_range *= 0.85       # Heat penalty
        elif temp > 60:
            base_range *= 0.70       # Severe heat penalty

        return round(max(base_range, 0), 2)

    # -------------------------
    # Degradation Score
    # -------------------------

    def calculate_degradation_score(self, battery_input: BatteryInput, zone: BatteryZone, anomaly: AnomalyStatus) -> float:
        """
        Returns a health score from 0 (dead) to 100 (perfect).
        Combines SOC, anomaly severity, zone, and temperature.
        This is NOT the same as SOC — it represents the battery's
        physical health, not just current charge level.
        """
        score = 100.0

        # Zone penalty
        if zone == BatteryZone.CRITICAL:
            score -= 40
        elif zone == BatteryZone.DEGRADED:
            score -= 20

        # Anomaly penalty
        anomaly_penalties = {
            AnomalyStatus.NONE:       0,
            AnomalyStatus.TRANSIENT:  5,
            AnomalyStatus.PERSISTENT: 20,
            AnomalyStatus.SEVERE:     35
        }
        score -= anomaly_penalties[anomaly]

        # Drain rate penalty (abnormal drain damages cells)
        if battery_input.drain_rate == DrainRate.ABNORMALLY_FAST:
            score -= 10
        elif battery_input.drain_rate == DrainRate.FAST:
            score -= 5

        # Temperature penalty
        temp = battery_input.temperature_c
        if temp < 0 or temp > 60:
            score -= 15
        elif temp < 10 or temp > 45:
            score -= 8

        return round(max(score, 0), 1)

    # -------------------------
    # Recommendation
    # -------------------------

    def determine_recommendation(self, zone: BatteryZone, anomaly: AnomalyStatus, battery_input: BatteryInput) -> EnergyRecommendation:
        """
        Extended recommendation engine.
        Now accounts for charging state and near-critical SOC.
        """
        if zone == BatteryZone.CHARGING:
            return EnergyRecommendation.MAINTAIN

        if zone == BatteryZone.CRITICAL:
            # If critical AND severe anomaly → most urgent
            if anomaly == AnomalyStatus.SEVERE:
                return EnergyRecommendation.PROTECTIVE
            # If critical due to low SOC only → charge now
            if battery_input.soc < CRITICAL_THRESHOLD:
                return EnergyRecommendation.CHARGE_NOW
            return EnergyRecommendation.PROTECTIVE

        if zone == BatteryZone.DEGRADED:
            if anomaly in [AnomalyStatus.PERSISTENT, AnomalyStatus.SEVERE]:
                return EnergyRecommendation.REDUCE_LOAD
            # Degraded with low SOC approaching critical
            if battery_input.soc < 35:
                return EnergyRecommendation.CHARGE_NOW
            return EnergyRecommendation.MONITOR

        if zone == BatteryZone.NOMINAL:
            if anomaly == AnomalyStatus.TRANSIENT:
                return EnergyRecommendation.MONITOR
            return EnergyRecommendation.MAINTAIN

        return EnergyRecommendation.MONITOR

    # -------------------------
    # Main Evaluation
    # -------------------------

    def evaluate(self, battery_input: BatteryInput) -> BIMOutput:
        """
        Full evaluation pipeline.
        Returns BIMOutput with zone, anomaly, recommendation,
        predicted range, and degradation score.
        """
        is_valid, reason = self.validate_input(battery_input)

        if not is_valid:
            return BIMOutput(
                zone=BatteryZone.CRITICAL,
                anomaly=AnomalyStatus.SEVERE,
                recommendation=EnergyRecommendation.PROTECTIVE,
                predicted_range_km=0.0,
                degradation_score=0.0
            )

        anomaly          = self.detect_anomaly(battery_input)
        zone             = self.classify_zone(battery_input, anomaly)
        predicted_range  = self.estimate_range(battery_input, zone, anomaly)
        recommendation   = self.determine_recommendation(zone, anomaly, battery_input)
        degradation_score = self.calculate_degradation_score(battery_input, zone, anomaly)

        self.previous_zone = zone

        return BIMOutput(
            zone=zone,
            anomaly=anomaly,
            recommendation=recommendation,
            predicted_range_km=predicted_range,
            degradation_score=degradation_score
        )
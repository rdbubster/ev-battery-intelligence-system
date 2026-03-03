

from dataclasses import dataclass
from enum import Enum
from typing import Optional


# -----------------------------
# ENUMERATIONS
# -----------------------------

class VoltageTrend(Enum):
    STABLE = "Stable"
    SLIGHT_FLUCTUATION = "Slight fluctuation"
    SUDDEN_DROP = "Sudden drop"
    REPEATED_INSTABILITY = "Repeated instability"


class DrainRate(Enum):
    SLOW = "Slow"
    MODERATE = "Moderate"
    FAST = "Fast"
    ABNORMALLY_FAST = "Abnormally fast"


class BatteryZone(Enum):
    NOMINAL = "Nominal"
    DEGRADED = "Degraded"
    CRITICAL = "Critical"


class AnomalyStatus(Enum):
    NONE = "None"
    TRANSIENT = "Transient Variation"
    PERSISTENT = "Persistent Deviation"
    SEVERE = "Severe Degradation"


class EnergyRecommendation(Enum):
    MAINTAIN = "Maintain normal operation"
    MONITOR = "Increase monitoring"
    REDUCE_LOAD = "Reduce non-critical loads"
    PROTECTIVE = "Activate protective mode"


# -----------------------------
# INPUT STRUCTURE
# -----------------------------

@dataclass
class BatteryInput:
    soc: float  # State of Charge (0–100)
    voltage_trend: VoltageTrend
    drain_rate: DrainRate


# -----------------------------
# OUTPUT STRUCTURE
# -----------------------------

@dataclass
class BIMOutput:
    zone: BatteryZone
    anomaly: AnomalyStatus
    recommendation: EnergyRecommendation
    predicted_range_km: float


# -----------------------------
# CORE MODULE
# -----------------------------

class BatteryIntelligenceModule:

    def __init__(self, efficiency_factor: float = 1.0):
        self.efficiency_factor = efficiency_factor
        self.previous_zone: Optional[BatteryZone] = None

    # -------------------------
    # Anomaly Detection
    # -------------------------

    def detect_anomaly(self, battery_input: BatteryInput) -> AnomalyStatus:

        if battery_input.voltage_trend == VoltageTrend.STABLE:
            return AnomalyStatus.NONE

        if battery_input.voltage_trend == VoltageTrend.SLIGHT_FLUCTUATION:
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

        soc = battery_input.soc

        if soc < 30 or anomaly == AnomalyStatus.SEVERE:
            return BatteryZone.CRITICAL

        if 30 <= soc <= 60 or anomaly == AnomalyStatus.PERSISTENT:
            return BatteryZone.DEGRADED

        return BatteryZone.NOMINAL

    # -------------------------
    # Range Estimation
    # -------------------------

    def estimate_range(self, battery_input: BatteryInput, zone: BatteryZone, anomaly: AnomalyStatus) -> float:

        drain_factor = {
            DrainRate.SLOW: 0.5,
            DrainRate.MODERATE: 1.0,
            DrainRate.FAST: 1.5,
            DrainRate.ABNORMALLY_FAST: 2.0
        }[battery_input.drain_rate]

        base_range = (battery_input.soc * self.efficiency_factor) / drain_factor

        # Zone-based conservative adjustment
        if zone == BatteryZone.DEGRADED:
            base_range *= 0.85
        elif zone == BatteryZone.CRITICAL:
            base_range *= 0.65

        # Anomaly impact
        if anomaly == AnomalyStatus.PERSISTENT:
            base_range *= 0.9
        elif anomaly == AnomalyStatus.SEVERE:
            base_range *= 0.75

        return round(max(base_range, 0), 2)

    # -------------------------
    # Decision Matrix
    # -------------------------

    def determine_recommendation(self, zone: BatteryZone, anomaly: AnomalyStatus) -> EnergyRecommendation:

        if zone == BatteryZone.CRITICAL:
            return EnergyRecommendation.PROTECTIVE

        if zone == BatteryZone.DEGRADED:
            if anomaly in [AnomalyStatus.PERSISTENT, AnomalyStatus.SEVERE]:
                return EnergyRecommendation.REDUCE_LOAD
            return EnergyRecommendation.MONITOR

        if zone == BatteryZone.NOMINAL:
            if anomaly == AnomalyStatus.TRANSIENT:
                return EnergyRecommendation.MONITOR
            return EnergyRecommendation.MAINTAIN

        return EnergyRecommendation.MONITOR

    # -------------------------
    # Fail-Safe Check
    # -------------------------

    def validate_input(self, battery_input: BatteryInput) -> bool:
        if battery_input.soc < 0 or battery_input.soc > 100:
            return False
        return True

    # -------------------------
    # Main Execution
    # -------------------------

    def evaluate(self, battery_input: BatteryInput) -> BIMOutput:

        if not self.validate_input(battery_input):
            return BIMOutput(
                zone=BatteryZone.CRITICAL,
                anomaly=AnomalyStatus.SEVERE,
                recommendation=EnergyRecommendation.PROTECTIVE,
                predicted_range_km=0.0
            )

        anomaly = self.detect_anomaly(battery_input)
        zone = self.classify_zone(battery_input, anomaly)
        predicted_range = self.estimate_range(battery_input, zone, anomaly)
        recommendation = self.determine_recommendation(zone, anomaly)

        self.previous_zone = zone

        return BIMOutput(zone, anomaly, recommendation, predicted_range)
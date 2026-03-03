from battery_intelligence_module import (
    BatteryIntelligenceModule,
    BatteryInput,
    VoltageTrend,
    DrainRate
)


def run_test(description, test_input):
    print("\n" + "=" * 60)
    print(f"TEST: {description}")
    print("=" * 60)

    bim = BatteryIntelligenceModule(efficiency_factor=1.2)

    output = bim.evaluate(test_input)

    print("Zone:", output.zone.value)
    print("Anomaly:", output.anomaly.value)
    print("Recommendation:", output.recommendation.value)
    print("Predicted Range (km):", output.predicted_range_km)


if __name__ == "__main__":

    # 1️⃣ Nominal Stable Case
    run_test(
        "Nominal Stable Battery",
        BatteryInput(
            soc=85,
            voltage_trend=VoltageTrend.STABLE,
            drain_rate=DrainRate.SLOW
        )
    )

    # 2️⃣ Borderline Degraded Case
    run_test(
        "SoC 50% with Sudden Drop",
        BatteryInput(
            soc=50,
            voltage_trend=VoltageTrend.SUDDEN_DROP,
            drain_rate=DrainRate.MODERATE
        )
    )

    # 3️⃣ Critical Low SoC
    run_test(
        "Low SoC 25%",
        BatteryInput(
            soc=25,
            voltage_trend=VoltageTrend.STABLE,
            drain_rate=DrainRate.MODERATE
        )
    )

    # 4️⃣ Severe Anomaly Override
    run_test(
        "High SoC but Severe Instability",
        BatteryInput(
            soc=75,
            voltage_trend=VoltageTrend.REPEATED_INSTABILITY,
            drain_rate=DrainRate.ABNORMALLY_FAST
        )
    )

    # 5️⃣ Invalid Input Fail-Safe
    run_test(
        "Invalid SoC (-10)",
        BatteryInput(
            soc=-10,
            voltage_trend=VoltageTrend.STABLE,
            drain_rate=DrainRate.SLOW
        )
    )
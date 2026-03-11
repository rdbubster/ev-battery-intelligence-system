from main import BatteryIntelligenceModule


def get_battery_report(soc, drain_rate, drop_percent, repeated):
    
    result = BatteryIntelligenceModule.analyze_battery(
        soc,
        drain_rate,
        drop_percent,
        repeated
    )

    report = {
        "battery_zone": result["zone"],
        "battery_issue": result["anomaly"],
        "driver_recommendation": result["recommended_action"],
        "estimated_range_km": result["predicted_range_km"]
    }

    return report


if __name__ == "__main__":

    report = get_battery_report(
        soc=65,
        drain_rate="fast",
        drop_percent=4,
        repeated=True
    )

    print("Battery Report")
    print(report)
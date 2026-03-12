import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import BatteryIntelligenceModule


def run_scenarios():

    scenarios = [

        {"name": "Normal Operation", "soc": 90, "drain_rate": "moderate", "drop": 0, "repeat": False},

        {"name": "Transient Voltage Drop", "soc": 75, "drain_rate": "moderate", "drop": 4, "repeat": False},

        {"name": "Persistent Drop", "soc": 70, "drain_rate": "moderate", "drop": 4, "repeat": True},

        {"name": "Severe Battery Drop", "soc": 80, "drain_rate": "fast", "drop": 12, "repeat": False},

        {"name": "Highway Driving", "soc": 80, "drain_rate": "moderate", "drop": 0, "repeat": False},

        {"name": "City Traffic", "soc": 70, "drain_rate": "moderate", "drop": 0, "repeat": False},

        {"name": "Uphill Driving", "soc": 65, "drain_rate": "fast", "drop": 0, "repeat": False},

        {"name": "Cold Weather", "soc": 75, "drain_rate": "moderate", "drop": 2, "repeat": False},

        {"name": "Boundary Nominal", "soc": 60, "drain_rate": "moderate", "drop": 0, "repeat": False},

        {"name": "Boundary Critical", "soc": 30, "drain_rate": "moderate", "drop": 0, "repeat": False},

        {"name": "Extreme Drain", "soc": 75, "drain_rate": "fast", "drop": 15, "repeat": False}

    ]

    print("\nRunning Scenario Tests\n")

    for scenario in scenarios:

        result = BatteryIntelligenceModule.analyze_battery(
            soc=scenario["soc"],
            drain_rate=scenario["drain_rate"],
            drop_percent=scenario["drop"],
            repeated=scenario["repeat"]
        )

        print(f"Scenario: {scenario['name']}")
        print(result)
        print("-" * 40)


if __name__ == "__main__":
    run_scenarios()
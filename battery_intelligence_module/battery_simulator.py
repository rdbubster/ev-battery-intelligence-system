import random
import time
from main import BatteryIntelligenceModule

print("EV Battery Simulator Running")
print("--------------------------------")

while True:

    soc = random.randint(20, 100)

    drain_rate = random.choice([
        "slow",
        "moderate",
        "fast"
    ])

    drop_percent = random.choice([
        0,
        2,
        4,
        6,
        10,
        12
    ])

    repeated = random.choice([
        True,
        False
    ])

    result = BatteryIntelligenceModule.analyze_battery(
        soc,
        drain_rate,
        drop_percent,
        repeated
    )

    print("Simulated Input:")
    print("SOC:", soc)
    print("Drain Rate:", drain_rate)
    print("Drop %:", drop_percent)
    print("Repeated:", repeated)

    print("\nBattery Result:")
    print(result)

    print("--------------------------------")

    time.sleep(5)
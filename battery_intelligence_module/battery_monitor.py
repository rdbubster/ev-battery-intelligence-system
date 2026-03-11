import time
import random
from battery_report import get_battery_report

print("Battery Monitoring System Started")
print("----------------------------------")

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
        10
    ])

    repeated = random.choice([
        True,
        False
    ])

    report = get_battery_report(
        soc,
        drain_rate,
        drop_percent,
        repeated
    )

    print("Battery Report Generated:")
    print(report)

    print("----------------------------------")

    time.sleep(5)
from main import BatteryIntelligenceModule

print("EV Battery Intelligence Interactive Demo")
print("---------------------------------------")

while True:

    try:
        soc = float(input("Enter Battery SoC (0-100): "))
        drain_rate = input("Enter drain rate (slow/moderate/fast): ")
        drop_percent = float(input("Enter sudden drop percentage: "))
        repeated_input = input("Repeated anomaly? (yes/no): ")

        repeated = repeated_input.lower() == "yes"

        result = BatteryIntelligenceModule.analyze_battery(
            soc,
            drain_rate,
            drop_percent,
            repeated
        )

        print("\nBattery Analysis Result")
        print(result)
        print("---------------------------------------")

    except Exception as e:
        print("Error:", e)

    again = input("Run another test? (yes/no): ")

    if again.lower() != "yes":
        break
class BatteryStateClassifier:
    """
    Determines battery operating zone based on State of Charge (SoC)
    """

    NOMINAL_THRESHOLD = 60
    CRITICAL_THRESHOLD = 30

    @staticmethod
    def classify_zone(soc):
        if soc > BatteryStateClassifier.NOMINAL_THRESHOLD:
            return "Nominal"

        elif BatteryStateClassifier.CRITICAL_THRESHOLD < soc <= BatteryStateClassifier.NOMINAL_THRESHOLD:
            return "Degraded"

        else:
            return "Critical"
from battery_state import BatteryStateClassifier
from anomaly_detection import AnomalyDetector
from range_estimator import RangeEstimator
from decision_engine import DecisionEngine


class BatteryIntelligenceModule:
    """
    BatteryIntelligenceModule integrates all battery analysis components
    to evaluate battery condition and generate system recommendations.
    """

    @staticmethod
    def analyze_battery(soc, drain_rate, drop_percent=0, repeated=False):
        """
        Perform full battery analysis.

        Parameters
        ----------
        soc : float
            State of Charge (0-100)

        drain_rate : str
            'slow', 'moderate', or 'fast'

        drop_percent : float
            Observed sudden SoC drop percentage

        repeated : bool
            Whether anomaly repeated within observation window

        Returns
        -------
        dict
            Battery analysis results
        """

        # Step 1: Determine operating zone
        zone = BatteryStateClassifier.classify_zone(soc)

        # Step 2: Detect anomaly
        anomaly = AnomalyDetector.detect_anomaly(drop_percent, repeated)

        # Step 3: Estimate remaining range
        predicted_range = RangeEstimator.estimate_range(soc, drain_rate, zone)

        # Step 4: Determine system action
        action = DecisionEngine.decide_action(zone, anomaly)

        return {
            "zone": zone,
            "anomaly": anomaly,
            "recommended_action": action,
            "predicted_range_km": predicted_range
        }


# Example run (for testing)
if __name__ == "__main__":

    result = BatteryIntelligenceModule.analyze_battery(
        soc=65,
        drain_rate="fast",
        drop_percent=4,
        repeated=True
    )

    print("Battery Analysis Result:")
    print(result)
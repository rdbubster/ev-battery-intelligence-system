class AnomalyDetector:
    """
    AnomalyDetector classifies battery anomalies based on
    voltage drop magnitude and repetition behavior.
    """

    TRANSIENT_MIN_DROP = 3
    TRANSIENT_MAX_DROP = 5
    SEVERE_DROP = 10

    @staticmethod
    def detect_anomaly(drop_percent: float, repeated: bool = False) -> str:
        """
        Detect anomaly type based on percentage drop.

        Parameters
        ----------
        drop_percent : float
            Observed sudden drop in battery percentage.

        repeated : bool
            Whether the anomaly occurred repeatedly
            within the observation window.

        Returns
        -------
        str
            'None', 'Transient Variation', 'Persistent Deviation',
            or 'Severe Degradation'
        """

        # Severe anomaly
        if drop_percent >= AnomalyDetector.SEVERE_DROP:
            return "Severe Degradation"

        # Persistent anomaly
        elif (
            AnomalyDetector.TRANSIENT_MIN_DROP
            <= drop_percent
            <= AnomalyDetector.TRANSIENT_MAX_DROP
            and repeated
        ):
            return "Persistent Deviation"

        # Transient anomaly
        elif (
            AnomalyDetector.TRANSIENT_MIN_DROP
            <= drop_percent
            <= AnomalyDetector.TRANSIENT_MAX_DROP
        ):
            return "Transient Variation"

        # No anomaly
        else:
            return "None"
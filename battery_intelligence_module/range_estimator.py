class RangeEstimator:
    """
    RangeEstimator estimates remaining driving range
    based on battery SoC, drain rate, and operating zone.
    """

    BASE_RANGE_FACTOR = 2.0  # km per 1% battery (assumed baseline)

    @staticmethod
    def estimate_range(soc: float, drain_rate: str, zone: str) -> float:
        """
        Estimate remaining driving range.

        Parameters
        ----------
        soc : float
            State of Charge percentage.

        drain_rate : str
            'slow', 'moderate', or 'fast'

        zone : str
            Battery operating zone ('Nominal', 'Degraded', 'Critical')

        Returns
        -------
        float
            Estimated remaining range in kilometers.
        """

        # Base range estimation
        base_range = soc * RangeEstimator.BASE_RANGE_FACTOR

        # Drain rate adjustment
        if drain_rate == "fast":
            base_range *= 0.75
        elif drain_rate == "moderate":
            base_range *= 0.90
        elif drain_rate == "slow":
            base_range *= 1.0

        # Zone-based safety adjustment
        if zone == "Degraded":
            base_range *= 0.85
        elif zone == "Critical":
            base_range *= 0.65

        return round(base_range, 2)
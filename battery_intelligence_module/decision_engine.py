class DecisionEngine:
    """
    DecisionEngine determines the recommended system action
    based on battery operating zone and anomaly status.
    """

    @staticmethod
    def decide_action(zone: str, anomaly: str) -> str:
        """
        Determine recommended action.

        Parameters
        ----------
        zone : str
            Battery operating zone.

        anomaly : str
            Detected anomaly status.

        Returns
        -------
        str
            Recommended system action.
        """

        # Nominal zone behavior
        if zone == "Nominal":

            if anomaly == "None":
                return "Maintain normal operation"

            elif anomaly == "Transient Variation":
                return "Increase monitoring"

            elif anomaly == "Persistent Deviation":
                return "Escalate monitoring and prepare degraded mode"

            elif anomaly == "Severe Degradation":
                return "Escalate to Critical Zone"

        # Degraded zone behavior
        elif zone == "Degraded":

            if anomaly == "None":
                return "Recommend energy saving"

            elif anomaly == "Transient Variation":
                return "Increase monitoring"

            elif anomaly == "Persistent Deviation":
                return "Reduce non-critical loads"

            elif anomaly == "Severe Degradation":
                return "Escalate to Critical Zone"

        # Critical zone behavior
        elif zone == "Critical":

            return "Activate protective mode and restrict non-essential systems"

        # Fallback safety
        return "Increase monitoring due to uncertain state"
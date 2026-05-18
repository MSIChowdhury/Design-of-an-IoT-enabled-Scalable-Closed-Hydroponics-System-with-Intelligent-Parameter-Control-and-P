from enum import Enum


class SensorState(str, Enum):
    NORMAL = "normal"
    SUSPECT_TRANSIENT = "suspect_transient"
    PERSISTENT_DEVIATION = "persistent_deviation"
    ACCEPTED_REGIME_SHIFT = "accepted_regime_shift"
    FAULT_ALERT = "fault_alert"


# coding=utf-8
import numpy as np

time_units = {"sec", "min", "hour"}
angular_units = {"deg", "rad", "arcMin", "arcSec"}

time_conversions_to_sec = {"sec": 1.0, "min": 60.0, "hour": 3600.0}
time_conversions_from_sec = {name: 1 / value for name, value in time_conversions_to_sec.items()}

angle_conversions_to_deg = {"deg": 1.0, "rad": 180.0/np.pi, "arcMin": 0.01667, "arcSec": 2.778e-4}
angle_conversions_from_deg = {name: 1 / value for name, value in angle_conversions_to_deg.items()}


def convertTimeFromTo(value: float, unit_from: str, unit_to: str) -> float:
    """ Converts a time value from one unit to another.

    :param value: Input time value
    :param unit_from: Unit of input value
    :param unit_to: Unit of output value
    :return: Time value converted to different unit
    """
    if unit_from not in time_units:
        raise ValueError(f"{unit_from} is not a valid unit! Valid units are: {time_units}")
    if unit_to not in time_units:
        raise ValueError(f"{unit_to} is not a valid unit! Valid units are: {time_units}")
    if not isinstance(value, (float, int)):
        raise TypeError(f"Time value must be a real number.")
    # if units match, return unmodified
    if unit_from == unit_to:
        return value
    value_in_sec = value * time_conversions_to_sec[unit_from]
    value_output = value_in_sec * time_conversions_from_sec[unit_to]
    return value_output


def convertAngleFromTo(value: float, unit_from: str, unit_to: str) -> float:
    """ Converts an angular value from one unit to another.

    :param value: Input angular value
    :param unit_from: Unit of input value
    :param unit_to: Unit of output value
    :return: Angular value converted to different unit
    """
    if unit_from not in angular_units:
        raise ValueError(f"{unit_from} is not a valid unit! Valid units are: {angular_units}")
    if unit_to not in angular_units:
        raise ValueError(f"{unit_to} is not a valid unit! Valid units are: {angular_units}")
    if not isinstance(value, (float, int)):
        raise TypeError(f"Angular value must be a real number.")
    # if units match, return unmodified
    if unit_from == unit_to:
        return value
    value_in_deg = value * angle_conversions_to_deg[unit_from]
    value_output = value_in_deg * angle_conversions_from_deg[unit_to]
    return value_output

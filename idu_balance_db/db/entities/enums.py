"""Enumeration classes used in database entities are defined here."""
from enum import Enum


class CityDivisionType(Enum, str):
    """Type of city administrative division."""

    ADMIN_UNIT_PARENT = "ADMIN_UNIT_PARENT"
    MUNICIPALITY_PARENT = "MUNICIPALITY_PARENT"
    NO_PARENT = "NO_PARENT"


class ForecastScenario(Enum, str):
    """Forecast scenario."""

    neg = "neg"  # pylint: disable=invalid-name
    mod = "mod"  # pylint: disable=invalid-name
    pos = "pos"  # pylint: disable=invalid-name

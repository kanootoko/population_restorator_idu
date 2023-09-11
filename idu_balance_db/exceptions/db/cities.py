"""Cities exceptions are defined here."""
from .base import DatabaseLayerError


class CityNotFoundError(DatabaseLayerError):
    """Raised when city is not found by name, code or id"""

    def __init__(self, city: str):
        super().__init__()
        self.city = city

    def __str__(self) -> str:
        return f"City '{self.city}' is not found"

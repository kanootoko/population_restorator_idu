"""Cities operations are defined here."""
from sqlalchemy import Connection, String, select

from idu_balance_db.db.entities import t_cities
from idu_balance_db.exceptions.db.cities import CityNotFoundError


def get_city_id(conn: Connection, city: str) -> int:
    """Get city id by name, code or id.

    Raise CityNotFoundError if city is not found.
    """
    statement = select(t_cities.c.id).where(
        (t_cities.c.name == city) | (t_cities.c.code == city) | (t_cities.c.id.cast(String) == city)
    )
    city_id = conn.execute(statement).scalar_one_or_none()
    if city_id is None:
        raise CityNotFoundError(city)
    return city_id

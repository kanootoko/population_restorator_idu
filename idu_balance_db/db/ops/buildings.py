"""Database buildings operations are defined here."""
import pandas as pd
from sqlalchemy import Connection, select, update

from idu_balance_db.db.entities import t_buildings, t_physical_objects


def get_buildings_administrative_unit(conn: Connection, administrative_unit_id) -> pd.DataFrame:
    """Return pandas DataFrame with buildings of a given administrative unit containing column `living_area`
    and `id` as index.
    """
    return pd.DataFrame(
        conn.execute(
            select(t_buildings.c.id, t_buildings.c.living_area)
            .select_from(t_buildings)
            .join(t_physical_objects, t_buildings.c.physical_object_id == t_physical_objects.c.id)
            .where(
                (t_physical_objects.c.administrative_unit_id == administrative_unit_id)
                & (t_buildings.c.is_living == True)  # pylint: disable=singleton-comparison
                & (t_buildings.c.living_area > 0)
            )
        ),
        columns=["id", "living_area"],
    )


def get_buildings_municipality(conn: Connection, municipality_id) -> pd.DataFrame:
    """Return pandas DataFrame with buildings of a given administrative unit containing column `living_area`
    and `id` as index.
    """
    return pd.DataFrame(
        conn.execute(
            select(t_buildings.c.id, t_buildings.c.living_area)
            .select_from(t_buildings)
            .join(t_physical_objects, t_buildings.c.physical_object_id == t_physical_objects.c.id)
            .where(
                (t_physical_objects.c.municipality_id == municipality_id)
                & (t_buildings.c.is_living == True)  # pylint: disable=singleton-comparison
                & (t_buildings.c.living_area > 0)
            )
        ),
        columns=["id", "living_area"],
    )


def update_house_population(conn: Connection, house_id: int, population: int) -> None:
    """Update house population"""
    conn.execute(update(t_buildings).values(population_balanced=population).where(t_buildings.c.id == house_id))

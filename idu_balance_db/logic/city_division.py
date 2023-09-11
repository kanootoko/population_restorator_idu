"""City division obtaining logic is defined here."""

from typing import Callable

from population_restorator.models import Territory
from sqlalchemy import Connection, func, select

from idu_balance_db.db.ops.buildings import get_buildings_administrative_unit, get_buildings_municipality


func: Callable

from idu_balance_db.db.entities import (
    t_administrative_units,
    t_cities,
    t_municipalities,
)
from idu_balance_db.db.entities.enums import CityDivisionType


def _get_city_as_territory_adms(conn: Connection, city_id: int) -> Territory:
    """Return city with administrative units as outer territories and municipalities as inner territories."""
    aus = []
    for au_id, au_population in conn.execute(
        select(t_administrative_units.c.id, t_administrative_units.c.population).where(
            t_administrative_units.c.city_id == city_id
        )
    ).fetchall():
        mos = []
        for mo_id, mo_population in conn.execute(
            select(t_municipalities.c.id, t_municipalities.c.population).where(
                t_municipalities.c.admin_unit_parent_id == au_id
            )
        ).fetchall():
            buildings = get_buildings_municipality(conn, mo_id)
            municipality = Territory(str(mo_id), mo_population, houses=buildings)
            mos.append(municipality)
        administrative_unit = Territory(str(au_id), au_population, mos)
        aus.append(administrative_unit)
    return Territory(
        f"City id={city_id} au_mo",
        conn.execute(select(t_cities.c.population).where(t_cities.c.id == city_id)).scalar_one(),
        aus,
    )


def _get_city_as_territory_mos(conn: Connection, city_id: int) -> Territory:
    """Return city with municipalities as outer territories and administrative units as inner territories."""
    mos = []
    for mo_id, au_population in conn.execute(
        select(t_municipalities.c.id, t_municipalities.c.population).where(t_municipalities.c.city_id == city_id)
    ).fetchall():
        aus = []
        for au_id, mo_population in conn.execute(
            select(t_administrative_units.c.id, t_administrative_units.c.population).where(
                t_administrative_units.c.municipality_parent == mo_id
            )
        ).fetchall():
            buildings = get_buildings_administrative_unit(conn, au_id)
            administrative_unit = Territory(str(au_id), mo_population, houses=buildings)
            aus.append(administrative_unit)
        administrative_unit = Territory(str(mo_id), au_population, aus)
        mos.append(administrative_unit)
    return Territory(
        f"City id={city_id} mo_au",
        conn.execute(select(t_cities.c.population).where(t_cities.c.id == city_id)).scalar_one(),
        mos,
    )


def _get_city_as_territory_flat(conn: Connection, city_id: int) -> Territory:
    """Return city with administrative units or municipalities (depending on population availability) as outer
    AND inner territories.
    """
    city_population = conn.execute(select(t_cities.c.population).where(t_cities.c.id == city_id)).scalar_one()
    adms_population = (
        conn.execute(
            select(func.sum(t_administrative_units.c.population)).where(t_administrative_units.c.id == city_id)
        ).scalar_one()
        or 0
    )
    mos_population = (
        conn.execute(
            select(func.sum(t_municipalities.c.population)).where(t_municipalities.c.id == city_id)
        ).scalar_one()
        or 0
    )
    if abs(adms_population - city_population) <= abs(mos_population - city_population):
        # au-au
        aus = []
        for au_id, au_population in conn.execute(
            select(t_administrative_units.c.id, t_administrative_units.c.population).where(
                t_administrative_units.c.city_id == city_id
            )
        ).fetchall():
            buildings = get_buildings_administrative_unit(conn, au_id)
            administrative_unit = Territory(
                str(au_id), au_population, [Territory(str(au_id), au_population, houses=buildings)]
            )
            aus.append(administrative_unit)
        return Territory(f"City id={city_id} au_au", city_population, aus)

    # mo-mo
    mos = []
    for mo_id, mo_population in conn.execute(
        select(t_municipalities.c.id, t_municipalities.c.population).where(t_municipalities.c.city_id == city_id)
    ).fetchall():
        buildings = get_buildings_municipality(conn, mo_id)
        municipality = Territory(str(mo_id), mo_population, [Territory(str(mo_id), mo_population, houses=buildings)])
        mos.append(municipality)
    return Territory(f"City id={city_id} au_au", city_population, mos)


def get_city_as_territory(conn: Connection, city_id: int) -> Territory:
    """Return city as a territory with outer and inner layers, each containing living buildings."""
    division_type = conn.execute(select(t_cities.c.city_division_type).where(t_cities.c.id == city_id)).scalar_one()
    if division_type == CityDivisionType.ADMIN_UNIT_PARENT:
        return _get_city_as_territory_adms(conn, city_id)
    if division_type == CityDivisionType.MUNICIPALITY_PARENT:
        return _get_city_as_territory_mos(conn, city_id)
    return _get_city_as_territory_flat(conn, city_id)

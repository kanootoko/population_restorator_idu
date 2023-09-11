"""Balancing logic is defined here"""
from typing import Literal

import pandas as pd
from loguru import logger
from population_restorator.balancer import balance_houses, balance_territories
from population_restorator.models import Territory
from sqlalchemy import Connection

from idu_balance_db.db.ops.buildings import update_house_population
from idu_balance_db.db.ops.territories import (
    syncronize_administrative_unit_population,
    syncronize_municipality_population,
)


def _syncronize_outer_territory(
    conn: Connection, division_type: Literal["mo_au", "au_mo", "mo_mo", "au_au"], territory_id: int, population: int
) -> None:
    """Update given outer territory if the population value does not match."""
    if division_type.startswith("au"):
        syncronize_administrative_unit_population(conn, territory_id, population)
    else:
        syncronize_municipality_population(conn, territory_id, population)


def _syncronize_inner_territory(
    conn: Connection, division_type: Literal["mo_au", "au_mo", "mo_mo", "au_au"], territory_id: int, population: int
) -> None:
    """Update given inner territory if the population value does not match."""
    if division_type.endswith("au"):
        syncronize_administrative_unit_population(conn, territory_id, population)
    else:
        syncronize_municipality_population(conn, territory_id, population)


def balance_houses_from_territory(conn: Connection, city_territory: Territory) -> pd.DataFrame:
    """Balance territories and houses and save updated data to the database."""
    logger.info("Balancing city territories")
    balance_territories(city_territory)

    for outer_territory in city_territory.inner_territories:
        _syncronize_outer_territory(
            conn, city_territory.name[-5:], int(outer_territory.name), outer_territory.population
        )
        for inner_territory in outer_territory.inner_territories:
            _syncronize_inner_territory(
                conn, city_territory.name[-5:], int(inner_territory.name), inner_territory.population
            )

    logger.info("Balancing city houses")
    balance_houses(city_territory)

    houses_df = city_territory.get_all_houses()

    for house_id, population in houses_df[["id", "population"]].set_index("id")["population"].items():
        update_house_population(conn, int(house_id), int(population))

    return houses_df

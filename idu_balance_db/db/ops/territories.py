"""Operations with administrative units and municipalities are defined here."""
from loguru import logger
from sqlalchemy import Connection, select, update

from idu_balance_db.db.entities import t_administrative_units, t_municipalities


def syncronize_administrative_unit_population(conn: Connection, administrative_unit_id: int, population: int) -> None:
    """Update given administrative_unit if the population value does not match."""
    current_population = conn.execute(
        select(t_administrative_units.c.population).where(t_administrative_units.c.id == administrative_unit_id)
    ).scalar_one()
    if current_population != population:
        logger.info(
            "Updating administrative unit id={} population: {} -> {}",
            administrative_unit_id,
            current_population,
            population,
        )
        conn.execute(
            update(t_administrative_units)
            .where(t_administrative_units.c.id == administrative_unit_id)
            .values(population=population)
        )


def syncronize_municipality_population(conn: Connection, municipality_id: int, population: int) -> None:
    """Update given municipality if the population value does not match."""
    current_population = conn.execute(
        select(t_municipalities.c.population).where(t_municipalities.c.id == municipality_id)
    ).scalar_one()
    if current_population != population:
        logger.info("Updating municipality id={} population: {} -> {}", municipality_id, current_population, population)
        conn.execute(
            update(t_municipalities).where(t_municipalities.c.id == municipality_id).values(population=population)
        )

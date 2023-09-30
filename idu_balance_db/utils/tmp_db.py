"""Temporary database related utilities are defined here."""
from population_restorator.db.entities import (
    t_houses_tmp,
    t_population_divided,
    t_social_groups_distribution,
    t_social_groups_probabilities,
)
from sqlalchemy import Connection, delete
from sqlalchemy.schema import DropTable


def clear_tmp_db(conn: Connection, start_year: int) -> None:
    """Clear `population_divided` table of all entries except `start_year` year."""
    conn.execute(delete(t_population_divided).where(t_population_divided.c.year != start_year))
    conn.commit()


def fully_clear_tmp_db(conn: Connection) -> None:
    """Drop tables in temporary database."""
    conn.execute(DropTable(t_population_divided, if_exists=True))
    conn.execute(DropTable(t_social_groups_distribution, if_exists=True))
    conn.execute(DropTable(t_social_groups_probabilities, if_exists=True))
    conn.execute(DropTable(t_houses_tmp, if_exists=True))
    conn.commit()

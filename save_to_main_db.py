"""Additional script to save missing years if the calculations have been finished, but saving process was aborted."""
import click
from sqlalchemy import create_engine, select
from population_restorator.db.entities import t_houses_tmp

from idu_balance_db import __version__
from idu_balance_db.db.entities.enums import ForecastScenario
from idu_balance_db.logic.saving import save_year_to_database


@click.command("copy-year-data")
@click.option(
    "--dsn",
    "-m",
    envvar="DB_DSN",
    default="postgresql://postgres:postgres@localhost:5432/city_db_final",
    help="PostgreSQL DBMS DSN (format: postgresql://user:password@host:port/db_name)",
    show_default=True,
    show_envvar=True,
)
@click.option(
    "--year-dsn",
    "-t",
    envvar="TEMPORARY_DSN_TEMPLATE",
    default="postgresql://postgres:postgres@localhost:5432/temporary",
    help="PostgreSQL DBMS DSN (format: postgresql://user:password@host:port/db_name)",
    show_default=True,
    show_envvar=True,
)
@click.option("--scenario", "-s", type=ForecastScenario, help="Forecasting scenario")
@click.option("--year", "-y", type=int, help="Year")
def main(dsn: str, year_dsn: str, year: int, scenario: ForecastScenario):
    """Save given year from temporary database to the main database."""
    if "?" not in dsn:
        dsn += f"?application_name=idu_balance_db v{__version__}"
    year_engine = create_engine(year_dsn)
    main_db_engine = create_engine(dsn)
    with main_db_engine.connect() as main_db_conn, year_engine.connect() as year_conn:
        houses_ids: list[int] = list(year_conn.execute(select(t_houses_tmp.c.id.distinct())).scalars().all())
        save_year_to_database(main_db_conn, year_conn, year, scenario, houses_ids)
        main_db_conn.commit()


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter

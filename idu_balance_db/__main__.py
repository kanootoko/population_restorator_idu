"""Executable file of idu-balance-db."""
import sys
import traceback
from pathlib import Path

import click
import pandas as pd
from loguru import logger
from population_restorator.divider import divide_houses, save_houses_distribution_to_db
from population_restorator.models.parse import read_coefficients
from sqlalchemy import create_engine, select, text

from idu_balance_db import __version__
from idu_balance_db.db.ops.cities import get_city_id
from idu_balance_db.exceptions.base import IduBalanceDbError
from idu_balance_db.logic.balancing import balance_houses_from_territory
from idu_balance_db.logic.city_division import get_city_as_territory
from idu_balance_db.logic.forecast import forecast_people_scenarios_saving_to_db
from idu_balance_db.logic.social import get_social_groups_distribution_from_db_and_excel
from idu_balance_db.utils.dotenv import try_read_envfile


try_read_envfile()


@click.command("balance-db")
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
    "--temporary-dsn-template",
    "-t",
    envvar="TEMPORARY_DSN_TEMPLATE",
    default="sqlite:///file:mem_year_{year}?mode=memory&uri=True",
    help="Temporary database DSN template (format: driver://user:password@host:port/db_name, 'year'"
    " will be replaced with year value)",
    show_default=True,
    show_envvar=True,
)
@click.option(
    "--distribution_file",
    "-d",
    envvar="DISTRIBUTION_FILE",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default="sex-age-social_groups-distribution.xlsx",
    help="Path to sex-age-social_groups distribution excel file",
)
@click.option(
    "--survivability_coefficients_file",
    "-s",
    envvar="SURVIVABILITY_COEFFICIENTS_FILE",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default="survivability-coefficients.json",
    help="Path to survivability coefficients file",
)
@click.option(
    "--year_begin",
    "-b",
    type=int,
    help="Year of the given data sample ('current year' for the calculations)",
    default=None,
    show_default="<current year>",
)
@click.option("--verbose", "-v", envvar="VERBOSE", count=True, help="Enable debug mode", show_envvar=True)
@click.argument("city")
def balance_db(  # pylint: disable=too-many-arguments,too-many-locals
    dsn: str,
    temporary_dsn_template: str,
    distribution_file: Path,
    survivability_coefficients_file: Path,
    year_begin: int,
    verbose: int,
    city: str,
) -> None:
    """Read the population, outer and inner bounds and houses of the given city and perform a population restoration.

    City can be given by name, code or id.
    """
    if verbose == 0:
        logger.remove()
        logger.add(sys.stderr, level="INFO", enqueue=True)
    else:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG", enqueue=True)

    if "?" not in dsn:
        dsn += f"?application_name=idu_balance_db v{__version__}"

    try:
        engine = create_engine(dsn)
        temporary_db_dsn = temporary_dsn_template.format(year=year_begin)
        temporary_db = create_engine(temporary_db_dsn)

        with temporary_db.connect() as test_conn:
            assert test_conn.execute(select(text("1"))).scalar_one() == 1

        with engine.connect() as conn:
            city_id = get_city_id(conn, city)
            city_territory = get_city_as_territory(conn, city_id)

            logger.info("City as territory: {}", city_territory)
            if verbose >= 2:
                from rich import print as rich_print  # pylint: disable=import-outside-toplevel

                rich_print("[i]City model information before balancing:[/i]")
                rich_print(city_territory.deep_info())

            houses_df = balance_houses_from_territory(conn, city_territory).set_index("id")

            sgs_distribution = get_social_groups_distribution_from_db_and_excel(conn, str(distribution_file))

            distribution_series = pd.Series(
                divide_houses(houses_df["population"].astype(int).to_list(), sgs_distribution),
                index=houses_df.index,
            )
            print(f"Totally {houses_df.shape[0]} houses")

            save_houses_distribution_to_db(
                temporary_db.connect(),
                distribution_series,
                houses_df["living_area"] if "living_area" in houses_df.columns else houses_df["population"],
                sgs_distribution,
                year_begin,
                verbose,
            )

            survivability_coefficients = read_coefficients(str(survivability_coefficients_file))
            forecast_people_scenarios_saving_to_db(
                dsn, temporary_db_dsn, temporary_dsn_template, survivability_coefficients, year_begin
            )

            conn.commit()

    except IduBalanceDbError as exc:
        print(f"Application error: {exc}")
        if verbose:
            traceback.print_exc()
        sys.exit(1)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Error: {exc!r}")
        if verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    balance_db()  # pylint: disable=no-value-for-parameter

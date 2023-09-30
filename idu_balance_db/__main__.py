"""Executable file of idu-balance-db."""
import datetime
import itertools
import sys
import traceback
from pathlib import Path
from typing import Literal

import click
import pandas as pd
from loguru import logger
from population_restorator.divider import divide_houses, save_houses_distribution_to_db
from population_restorator.models.parse import read_coefficients
from sqlalchemy import create_engine, select, text

from idu_balance_db import __version__
from idu_balance_db.db.entities.enums import ForecastScenario
from idu_balance_db.db.ops.cities import get_city_id
from idu_balance_db.exceptions.base import IduBalanceDbError
from idu_balance_db.logic.balancing import balance_houses_from_territory
from idu_balance_db.logic.city_division import get_city_as_territory
from idu_balance_db.logic.forecast import forecast_people_scenarios_saving_to_db
from idu_balance_db.logic.social import get_social_groups_distribution_from_db_and_excel
from idu_balance_db.utils.dotenv import try_read_envfile
from idu_balance_db.utils.tmp_db import fully_clear_tmp_db


try_read_envfile()

LogLevel = Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR"]


def logger_from_str(logger_text: str) -> list[tuple[LogLevel, str]]:
    """
    Helper function to deconstruct string input argument(s) to logger configuration.

    Examples:
        logger_from_str("ERROR,errors.log") -> [("ERROR", "errors.log)]
        logger_from_str("ERROR,errors.log;INFO,info.log") -> [("ERROR", "errors.log), ("INFO", "info.log")]
    """
    res = []
    for item in logger_text.split(";"):
        assert "," in item, f'logger text must be in format "LEVEL,filename" - current value is "{logger_text}"'
        level, filename = item.split(",", 1)
        level = level.upper()
        res.append((level, filename))  # type: ignore
    return res


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
    help="Path to sex-age-social_groups distribution excel file",
    show_envvar=True,
)
@click.option(
    "--survivability_coefficients_file",
    "-s",
    envvar="SURVIVABILITY_COEFFICIENTS_FILE",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to survivability coefficients file",
    show_envvar=True,
)
@click.option(
    "--year_begin",
    "-b",
    type=int,
    help="Year of the given data sample ('current year' for the calculations)",
    default=None,
    show_default="<current year>",
)
@click.option(
    "--years",
    "-y",
    envvar="YEARS",
    type=int,
    help="Number of years to forecast",
    default=10,
    show_default=True,
    show_envvar=True,
)
@click.option(
    "--scenario",
    "scenarios",
    envvar="SCENARIO",
    type=click.Choice(["neg", "pos", "mod"]),
    multiple=True,
    default=["neg", "mod", "pos"],
    help="Scenario to forecast people for.",
    show_default=True,
)
@click.option(
    "--threads",
    "-t",
    envvar="THREADS",
    type=int,
    help="Enable multiprocessing forecasting mode (not recommended to use with SQLite)",
    default=1,
    show_default=True,
    show_envvar=True,
)
@click.option("--skip-clear-tmp-db", "-stc", is_flag=True, help="Skip deletion of previously used temporary data")
@click.option(
    "--verbose", "-v", envvar="VERBOSE", count=True, help="Verbosity level (set by number of -v's)", show_envvar=True
)
@click.option(
    "--add_logger",
    "-l",
    "additional_loggers",
    type=logger_from_str,
    envvar="ADDITIONAL_LOGGERS",
    multiple=True,
    default=[],
    show_default="[]",
    show_envvar=True,
    help="Add logger in format LEVEL,path/to/logfile",
)
@click.argument("city")
def balance_db(  # pylint: disable=too-many-arguments,too-many-locals,too-many-branches,too-many-statements
    dsn: str,
    temporary_dsn_template: str,
    distribution_file: Path,
    survivability_coefficients_file: Path,
    year_begin: int | None,
    years: int,
    scenarios: list[Literal["neg", "mod", "pos"]],
    threads: int,
    skip_clear_tmp_db: bool,
    verbose: int,
    additional_loggers: list[tuple[LogLevel, str]],
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
    additional_loggers = list(itertools.chain.from_iterable(additional_loggers))
    for log_level, filename in additional_loggers:
        logger.add(filename, level=log_level)

    forecast_scenarios = [ForecastScenario(sc) for sc in set(scenarios)]
    logger.info("Forecasting population for scenarios: {}", ", ".join(sc.value for sc in forecast_scenarios))

    if year_begin is None:
        year_begin = datetime.datetime.now().year

    if "?" not in dsn:
        dsn += f"?application_name=idu_balance_db v{__version__}"

    try:
        if not skip_clear_tmp_db:
            for year in range(year_begin, year_begin + years + 1):
                tmp_engine = create_engine(temporary_dsn_template.format(year=year))
                with tmp_engine.connect() as tmp_conn:
                    fully_clear_tmp_db(tmp_conn)
        engine = create_engine(dsn)
        first_year_tmp_db_dsn = temporary_dsn_template.format(year=year_begin)
        first_year_tmp_db = create_engine(first_year_tmp_db_dsn)

        with first_year_tmp_db.connect() as test_conn:
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
            logger.info(f"Totally {houses_df.shape[0]} houses")

            save_houses_distribution_to_db(
                first_year_tmp_db.connect(),
                distribution_series,
                houses_df["living_area"] if "living_area" in houses_df.columns else houses_df["population"],
                sgs_distribution,
                year_begin,
                verbose,
            )

            survivability_coefficients = read_coefficients(str(survivability_coefficients_file))
            forecast_people_scenarios_saving_to_db(
                dsn,
                first_year_tmp_db_dsn,
                temporary_dsn_template,
                survivability_coefficients,
                year_begin,
                years=years,
                skip_clear_tmp_db=skip_clear_tmp_db,
                threads=threads,
                scenarios=scenarios,
            )

            conn.commit()

    except IduBalanceDbError as exc:
        logger.error(f"Application error: {exc}")
        if verbose:
            traceback.print_exc()
        sys.exit(1)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error(f"Error: {exc!r}")
        if verbose:
            traceback.print_exc()
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Exiting by Ctrl+C hit")


if __name__ == "__main__":
    balance_db()  # pylint: disable=no-value-for-parameter

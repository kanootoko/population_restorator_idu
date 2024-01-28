"""Forecasting-related methods are located here."""
import multiprocessing as mp
import time

import numpy as np
from loguru import logger
from population_restorator.forecaster import forecast_ages, forecast_people
from population_restorator.models import SurvivabilityCoefficients
from sqlalchemy import create_engine, text

from idu_balance_db.db.entities.enums import ForecastScenario
from idu_balance_db.utils.tmp_db import clear_tmp_db_except_start

from .saving import save_year_to_database


def db_saver_process(main_db_dsn: str, queue: mp.Queue) -> None:
    """Process function which calls save_year_to_database as the year is ready and parameters are sent to the queue.

    Stops when `None` is sent to the pipe and previous years are saved."""
    while True:
        value = queue.get()
        if value is None:
            break
        year_dsn, year, scenario, houses_ids = value
        year_engine = create_engine(year_dsn)
        main_db_engine = create_engine(main_db_dsn)
        while True:
            try:
                with main_db_engine.connect() as main_db_conn, year_engine.connect() as year_conn:
                    save_year_to_database(main_db_conn, year_conn, year, scenario, houses_ids)
                    main_db_conn.commit()
                break
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("Got exception on saving data: {!r} of year {}. Trying again in 20 seconds", exc, year)
                time.sleep(20)


def forecast_people_scenarios_with_transfering_to_db(  # pylint: disable=too-many-arguments,too-many-locals
    main_db_dsn: str,
    start_db_dsn: str,
    year_db_dsn_template: str,
    base_survivability_coefficients: SurvivabilityCoefficients,
    year_begin: int,
    houses_ids: list[int],
    skip_clear_tmp_db: bool = False,
    years: int = 10,
    scenarios: list[ForecastScenario] = ...,
    base_fertility: float = 0.07,
    negative_scenario_multiplier: float = 0.9,
    positive_scenario_multiplier: float = 1.1,
    threads: int = 1,
) -> None:
    """Forecast people with a given base `survivability_coefficients` to multiply by `negative_scenario_multiplier` or
    `positive_scenario_multiplier` and save to `conn` PosgreSQL database connection.
    """
    if scenarios is ...:
        scenarios = list(ForecastScenario)

    boys_to_girls = 1.05
    fertility_begin = 20
    fertility_end = 39

    try:
        for scenario in scenarios:
            saving_queue = mp.Queue()
            saving_process = mp.Process(target=db_saver_process, args=(main_db_dsn, saving_queue))
            saving_process.start()

            saving_queue.put_nowait((start_db_dsn, year_begin, scenario, houses_ids))
            multiplier = (
                negative_scenario_multiplier
                if scenario == ForecastScenario.neg
                else positive_scenario_multiplier
                if scenario == ForecastScenario.pos
                else 1.0
            )
            logger.info("Using multiplier for scenario {}: {}", scenario.value, multiplier)

            def save_results(
                year_dsn: str, year: int, scenario: ForecastScenario = scenario, saving_queue: mp.Queue = saving_queue
            ) -> None:
                """Save results from the temporary year database to PostgreSQL main DB."""
                saving_queue.put_nowait((year_dsn, year, scenario, houses_ids))

            start_year_engine = create_engine(start_db_dsn)

            databases = [
                year_db_dsn_template.format(year=year) for year in range(year_begin + 1, year_begin + years + 1)
            ]

            if not skip_clear_tmp_db:
                for dsn in databases:
                    tmp_engine = create_engine(dsn)
                    with tmp_engine.connect() as tmp_conn:
                        clear_tmp_db_except_start(tmp_conn, year_begin)
                        tmp_conn.commit()

            if years > 0:
                fertility_coefficient = base_fertility * multiplier
                current_coeffs = SurvivabilityCoefficients(
                    (np.array(base_survivability_coefficients.men) * multiplier).tolist(),
                    (np.array(base_survivability_coefficients.women) * multiplier).tolist(),
                )
                forecasted_ages = forecast_ages(
                    start_year_engine,
                    year_begin,
                    year_begin + years,
                    boys_to_girls,
                    current_coeffs,
                    fertility_coefficient,
                    fertility_begin,
                    fertility_end,
                    houses_ids=houses_ids,
                )

                logger.success("Starting forecast for scenario '{}'", scenario.value)
                start_year_db = create_engine(start_db_dsn)
                forecast_people(
                    start_year_db,
                    forecasted_ages,
                    databases,
                    year_begin,
                    houses_ids,
                    callback=save_results,
                    threads=threads,
                )
                logger.success("Finished forecast for scenario '{}'", scenario.value)

            saving_queue.put(None)
            logger.success("Waiting for the saving process to be finished")
            saving_process.join()
    finally:
        if saving_process.is_alive():
            logger.info("Waiting until saving process is properly killed")
            saving_process.kill()
            saving_process.join()

    logger.info("Refreshing materialized views")
    main_db_engine = create_engine(main_db_dsn)
    social_matviews = [
        "calculated_sex_age_houses",  # to be removed
        "calculated_sex_age_buildings",
        "calculated_people_houses",  # to be removed
        "calculated_people_buildings",
        "calculated_social_people_buildings",
        "calculated_sex_age_social_administrative_units",
        "calculated_sex_age_social_municipalities",
        "calculated_sex_age_administrative_units",
        "calculated_sex_age_municipalities",
    ]
    with main_db_engine.connect() as conn:
        for matview_name in social_matviews:
            exists = conn.execute(
                text("SELECT EXISTS(SELECT 1 FROM pg_matviews WHERE schemaname = :schema AND matviewname = :name)"),
                {"schema": "social_stats", "name": matview_name},
            ).scalar_one()
            if not exists:
                logger.warning("Materialized view '{}.{}' is missing, skipping refresh", "social_stats", matview_name)
                continue
            logger.debug("Refreshing social_stats.{}", matview_name)
            conn.execute(text(f"refresh materialized view social_stats.{matview_name}"))
        conn.commit()
    logger.info("Done refreshing materialized views.")

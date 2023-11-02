"""Services demands update logic is defined here."""
import pandas as pd
from loguru import logger
from numpy import isnan, nan
from sqlalchemy import Engine, text
from tqdm import tqdm, trange

from idu_balance_db.db.entities.enums import ForecastScenario


def update_demands_table(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    engine: Engine, city_id: int, start_year: int, years: int, scenario: ForecastScenario = ForecastScenario.mod
) -> None:
    """Update services-buildings demands table for the given city."""
    scenario_name = scenario.value
    with engine.connect() as conn:
        logger.debug("Creating temporary buildings table")
        conn.execute(
            text(
                "CREATE TEMPORARY TABLE city_buildings AS ("
                "   SELECT b.id"
                "   FROM buildings b"
                "       JOIN physical_objects p ON b.physical_object_id = p.id"
                "   WHERE p.city_id = :city_id"
                ")"
            ),
            {"city_id": city_id},
        )
        logger.debug("Selecting city buildings")
        city_buildings = (
            conn.execute(
                text(
                    " SELECT DISTINCT building_id"
                    " FROM social_stats.sex_age_social_houses"
                    " WHERE building_id in (SELECT id FROM city_buildings)"
                    " ORDER BY 1"
                ),
                {"city_id": city_id},
            )
            .scalars()
            .all()
        )
        houses = pd.DataFrame([[h] for h in city_buildings], columns=["building_id"]).set_index("building_id")

        services_normatives: dict[str, float] = {
            service: norm / 1000
            for service, norm in conn.execute(
                text(
                    "SELECT st.code, normative FROM provision.normatives"
                    " JOIN city_service_types st ON city_service_type_id = st.id"
                )
            )
        }

        men_column = "(" + "+".join(f"men_{i}" for i in range(101)) + ")"
        women_column = "(" + "+".join(f"women_{i}" for i in range(101)) + ")"

        houses_year = houses.copy()
        city_df = pd.DataFrame()
        logger.info("Calculating demands")
        for year in trange(start_year, start_year + years + 1, desc="years"):
            logger.debug("Calculating demands for year {}", year)
            if "year" in city_df.columns and year in city_df["year"].unique().tolist():
                continue
            if (
                "year" not in houses_year.columns
                or houses_year["year"].nunique() != 1
                or year not in houses_year["year"].unique()
            ):
                houses_year = houses.copy()
                houses_year["year"] = year
            if "year_population_sgs" not in houses_year.columns:
                res = conn.execute(
                    text(
                        "SELECT house_id, people"
                        " FROM social_stats.calculated_people_houses"
                        " WHERE year = :year"
                        "   AND scenario = :scenario"
                        "   AND house_id in (SELECT id FROM city_buildings)"
                        " ORDER BY house_id"
                    ),
                    ({"city_id": city_id, "year": year, "scenario": scenario_name}),
                ).all()
                if len(res) == 0:
                    logger.error(
                        "Year {} data for city with id={} is missing social groups population data"
                        " in calculated_people_houses!",
                        year,
                        city_id,
                    )
                    continue
                idxs, values = map(list, zip(*res))
                houses_year = houses_year.join(pd.Series(values, idxs, name="year_population_sgs"))
            if "year_population" not in houses_year.columns:
                res = conn.execute(
                    text(
                        "SELECT house_id, people"
                        " FROM social_stats.calculated_people_houses"
                        " WHERE year = :year"
                        "   AND scenario = :scenario"
                        "   AND house_id in (SELECT id FROM city_buildings)"
                        " ORDER BY house_id"
                    ),
                    ({"city_id": city_id, "year": year, "scenario": scenario_name}),
                ).all()
                if len(res) == 0:
                    logger.error(
                        "Year {} data for city with id={} is missing basic people population data"
                        " in social_stats.calculated_people_houses!",
                        year,
                        city_id,
                    )
                    continue
                idxs, values = map(list, zip(*res))
                houses_year = houses_year.join(pd.Series(values, idxs, name="year_population"))
            service_types = conn.execute(
                text(
                    "SELECT DISTINCT st.id as city_service_type_id, st.code as city_service_type"
                    " FROM maintenance.social_groups_city_service_types"
                    "   JOIN city_service_types st ON city_service_type_id = st.id"
                    " ORDER BY 1"
                )
            ).all()
            for (
                city_service_type_id,
                service_type,
            ) in tqdm(service_types, desc=f"model@{year}", leave=False):
                if f"{service_type}_service_demand_value_model" in houses_year.columns:
                    continue
                social_groups = tuple(
                    conn.execute(
                        text(
                            "SELECT social_group_id FROM maintenance.social_groups_city_service_types"
                            " WHERE city_service_type_id = :city_service_type_id"
                        ),
                        {"city_service_type_id": city_service_type_id},
                    )
                    .scalars()
                    .all()
                )
                res = conn.execute(
                    text(
                        f" SELECT building_id, sum({men_column} + {women_column})::integer"
                        " FROM social_stats.sex_age_social_houses"
                        " WHERE year = :year AND scenario = :scenario"
                        "   AND social_group_id IN :social_groups AND building_id in (SELECT id FROM city_buildings)"
                        " GROUP BY building_id ORDER BY building_id"
                    ),
                    {"year": year, "scenario": scenario_name, "social_groups": social_groups},
                ).all()
                if len(res) == 0:
                    logger.warning(
                        "No data for year={}, scenario={}, social_groups={} in social_stats.sex_age_social_houses",
                        year,
                        scenario.value,
                        social_groups,
                    )
                    continue
                idxs, values = map(list, zip(*res))
                houses_year = houses_year.join(
                    pd.Series(values, index=idxs, name=f"{service_type}_service_demand_value_model"), how="left"
                )

            for service_type in tqdm(services_normatives, desc=f"normative@{year}", leave=False):
                if f"{service_type}_service_demand_value_normative" in houses_year.columns:
                    continue
                houses_year[f"{service_type}_service_demand_value_normative"] = (
                    houses_year["year_population"] * services_normatives[service_type]
                ).apply(lambda x: round(x) if not isnan(x) else nan)
            city_df = pd.concat((city_df, houses_year.reset_index())).reset_index(drop=True)

        columns = city_df.columns.tolist()
        query = text(
            f"INSERT INTO provision.buildings_load_future ({', '.join(columns)})"
            f" VALUES ({', '.join(':' + column for column in columns)}) ON CONFLICT DO NOTHING"
        )
        creation_text = text(
            "CREATE TABLE IF NOT EXISTS provision.buildings_load_future ("
            "   building_id integer NOT NULL,"
            "   year smallint NOT NULL,"
            "   year_population_sgs integer NOT NULL,"
            "   year_population integer NOT NULL,"
            + ",\n".join(f"{column} smallint" for column in columns[4:])
            + "   , PRIMARY KEY (building_id, year)"
            + ")"
        )
        logger.info("Creating/modifying provision.buildings_load_future table")
        conn.execute(creation_text)
        table_columns = (
            conn.execute(
                text(
                    "SELECT column_name"
                    " FROM information_schema.columns"
                    " WHERE table_schema = 'provision' AND table_name = 'buildings_load_future'"
                )
            )
            .scalars()
            .all()
        )
        additional_columns = set(columns) - set(table_columns)
        to_remove = set(table_columns) - set(columns)
        for column in additional_columns:
            logger.warning("Adding column '{}' to provision.buildings_load_future", column)
            conn.execute(text(f"ALTER TABLE provision.buildings_load_future ADD COLUMN {column} smallint"))
        for column in to_remove:
            logger.warning("Removing column '{}' from provision.buildings_load_future", column)
            conn.execute(text(f"ALTER TABLE provision.buildings_load_future DROP COLUMN {column}"))
        conn.execute(
            text("DELETE FROM provision.buildings_load_future WHERE building_id IN (SELECT id FROM city_buildings)")
        )

        logger.info("Saving demands")
        for _, row in tqdm(city_df.fillna(0).iterrows(), total=city_df.shape[0], desc="Uploading demands"):
            conn.execute(
                query,
                dict(row.to_dict()),
            )
        conn.commit()

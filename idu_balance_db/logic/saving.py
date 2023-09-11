"""Functionality of saving data to main DB is defined here."""
from loguru import logger
from population_restorator.db.entities import t_population_divided, t_social_groups_probabilities
from sqlalchemy import Connection, delete, distinct, select, true
from sqlalchemy.dialects.postgresql import insert
from tqdm import tqdm

from idu_balance_db.db.entities.enums import ForecastScenario
from idu_balance_db.db.entities.social_stats import t_sex_age_social_houses


def save_year_to_database(  # pylint: disable=too-many-locals
    conn: Connection, year_conn: Connection, year: int, scenario: ForecastScenario, houses_ids: list[int] | None
) -> None:
    """Migrate year data from temporary database `year_db` with a data for a single year to a
    `t_sex_age_social_houses` table at `conn` PostgreSQL database connection.
    """
    logger.info("Inserting year {} forecasted data to the database", year)
    base_population = {f"men_{i}": 0 for i in range(101)} | {f"women_{i}": 0 for i in range(101)}
    social_groups = [
        (sg_id, int(sg_name))
        for sg_id, sg_name in year_conn.execute(
            select(t_social_groups_probabilities.c.id, t_social_groups_probabilities.c.name)
            .select_from(t_population_divided)
            .join(
                t_social_groups_probabilities,
                t_population_divided.c.social_group_id == t_social_groups_probabilities.c.id,
            )
            .where((t_population_divided.c.men > 0) | (t_population_divided.c.women > 0))
            .distinct()
            .order_by(t_social_groups_probabilities.c.name)
        )
    ]
    conn.execute(
        delete(t_sex_age_social_houses).where(
            t_sex_age_social_houses.c.scenario == scenario,
            t_sex_age_social_houses.c.year == year,
            (t_sex_age_social_houses.c.house_id.in_(houses_ids) if houses_ids is not None else true()),
        )
    )
    for house_id in tqdm(
        year_conn.execute(select(distinct(t_population_divided.c.house_id)).order_by(t_population_divided.c.house_id))
        .scalars()
        .all(),
        desc=f"{year} Temporary->PostgreSQL",
        leave=False,
    ):
        for (
            tmp_sg_id,
            social_group_id,
        ) in social_groups:
            house_people = year_conn.execute(
                select(t_population_divided.c.age, t_population_divided.c.men, t_population_divided.c.women).where(
                    t_population_divided.c.year == year,
                    t_population_divided.c.house_id == house_id,
                    t_population_divided.c.social_group_id == tmp_sg_id,
                    (t_population_divided.c.men > 0) | (t_population_divided.c.women > 0),
                )
            ).all()
            if len(house_people) == 0:
                continue

            house_population = base_population.copy()
            for age, men, women in house_people:
                house_population[f"men_{age}"] = men
                house_population[f"women_{age}"] = women
            conn.execute(
                insert(t_sex_age_social_houses).values(
                    year=year,
                    scenario=scenario,
                    house_id=house_id,
                    social_group_id=social_group_id,
                    **house_population,
                )
            )

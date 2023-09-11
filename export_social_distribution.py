"""Executable script to export sex-age-social distribution for further edit and usage."""

from pathlib import Path
from typing import Callable

import click
import pandas as pd
from population_restorator.models import SocialGroupsDistribution
from sqlalchemy import create_engine, desc, func, select


func: Callable

from idu_balance_db.db.entities import (
    t_age_sex_social_stat_administrative_units,
    t_social_groups,
)


@click.command("balance-db")
@click.option(
    "--db_host",
    "-h",
    envvar="DB_HOST",
    default="localhost",
    help="PostgreSQL DBMS host address",
    show_default=True,
    show_envvar=True,
)
@click.option(
    "--db_port",
    "-p",
    envvar="DB_PORT",
    type=int,
    default=5432,
    help="PosgreSQL DBMS port",
    show_default=True,
    show_envvar=True,
)
@click.option(
    "--db_name",
    "-D",
    envvar="DB_NAME",
    default="city_db_final",
    help="PostgreSQL database name",
    show_default=True,
    show_envvar=True,
)
@click.option(
    "--db_user",
    "-U",
    envvar="DB_USER",
    default="postgres",
    help="PostgreSQL user name",
    show_default=True,
    show_envvar=True,
)
@click.option(
    "--db_pass",
    "-W",
    envvar="DB_PASS",
    default="postgres",
    help="PostgreSQL user password",
    show_default=True,
    show_envvar=True,
)
@click.option(
    "--distribution_file",
    "-d",
    envvar="DISTRIBUTION_FILE",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default="sex-age-social_groups-distribution.xlsx",
    help="Path to save sex-age-social_groups distribution excel file",
)
def get_social_groups_distribution_from_db(  # pylint: disable=too-many-arguments
    db_host: str,
    db_port: int,
    db_name: str,
    db_user: str,
    db_pass: str,
    distribution_file: Path,
) -> SocialGroupsDistribution:
    """Form a social groups distribution using `age_distribution`, `sex_distribution` and `social_group_distribution`
    tables of `social_stats` schema`
    """
    engine = create_engine(f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}")
    with engine.connect() as conn:
        primary_sgs_ids: list[int] = list(
            conn.execute(
                select(t_social_groups.c.id).where(
                    t_social_groups.c.name.like("%)")
                    & t_social_groups.c.name.not_like("%т)")
                    & t_social_groups.c.name.not_like("%а)")
                )
            )
            .scalars()
            .all()
        )
        if len(primary_sgs_ids) == 0:
            raise RuntimeError("Database is missing primary social groups")
        year = conn.execute(
            select(t_age_sex_social_stat_administrative_units.c.year.distinct()).order_by(
                desc(t_age_sex_social_stat_administrative_units.c.year)
            )
        ).scalar_one()

        distribution = pd.DataFrame(
            conn.execute(
                select(
                    t_age_sex_social_stat_administrative_units.c.social_group_id,
                    t_age_sex_social_stat_administrative_units.c.age,
                    select(t_social_groups.c.name)
                    .where(t_social_groups.c.id == t_age_sex_social_stat_administrative_units.c.social_group_id)
                    .scalar_subquery()
                    .label("social_group"),
                    func.sum(t_age_sex_social_stat_administrative_units.c.men).label("men"),
                    func.sum(t_age_sex_social_stat_administrative_units.c.women).label("women"),
                )
                .where(t_age_sex_social_stat_administrative_units.c.year == year)
                .group_by(
                    t_age_sex_social_stat_administrative_units.c.social_group_id,
                    t_age_sex_social_stat_administrative_units.c.age,
                )
                .order_by(
                    t_age_sex_social_stat_administrative_units.c.social_group_id,
                    t_age_sex_social_stat_administrative_units.c.age,
                )
            )
        )
        print(distribution)

        social_groups = pd.DataFrame(
            conn.execute(
                select(t_social_groups.c.id.label("social_group_id"), t_social_groups.c.name.label("social_group"))
                .where(t_social_groups.c.parent_id != None)  # pylint: disable=singleton-comparison
                .order_by(t_social_groups.c.id)
            )
        )

        social_groups = social_groups.merge(
            distribution.groupby(["social_group_id", "social_group"])
            .sum()
            .drop("age", axis=1)
            .reset_index()
            .sort_values("social_group_id"),
            how="left",
            on=["social_group_id", "social_group"],
        ).reset_index(drop=True)
        social_groups["is_primary"] = social_groups["social_group_id"].apply(lambda x: x in primary_sgs_ids)

        print(social_groups)

        with pd.ExcelWriter(str(distribution_file)) as writer:  # pylint: disable=abstract-class-instantiated
            pd.DataFrame(
                [
                    "Only 'distribution' sheet is used.",
                    "Columns 'social_group_id', 'men' and 'women'.",
                    "Values are normalized, so it does not matter if they sum up to 1.0",
                ],
                columns=["help"],
            ).to_excel(writer, "help", index=False)
            distribution.to_excel(writer, "distribution", index=False)
            social_groups.to_excel(writer, "social_groups", index=False)


if __name__ == "__main__":
    get_social_groups_distribution_from_db()  # pylint: disable=no-value-for-parameter

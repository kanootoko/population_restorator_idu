"""Social groups related methods are defined here."""
from typing import BinaryIO, Callable
from loguru import logger

import pandas as pd
from population_restorator.models import SocialGroupsDistribution, SocialGroupWithProbability
from sqlalchemy import Connection, select


func: Callable

from idu_balance_db.db.entities import t_social_groups


DEFAULT_MAX_AGE = 100


def get_social_groups_distribution_from_db_and_excel(  # pylint: disable=too-many-locals
    conn: Connection, excel_file: str | BinaryIO, max_age: int = DEFAULT_MAX_AGE
) -> SocialGroupsDistribution:
    """Form a social groups distribution using excel file with distribution exported by export_social_distribution.py"""
    distribution: pd.DataFrame = pd.read_excel(excel_file, sheet_name="distribution")[
        ["social_group", "age", "men", "women"]
    ]

    names_ids_mapping: dict[str, int] = dict(conn.execute(select(t_social_groups.c.name, t_social_groups.c.id)).all())
    try:
        distribution["social_group_id"] = distribution["social_group"].apply(lambda name: names_ids_mapping[name])
    except KeyError as exc:
        logger.error("Social group '{}' is not found in the database by name", exc.args[0])
        logger.info("Available social groups: {}", ", ".join(names_ids_mapping.keys()))
        raise ValueError(  # pylint: disable=raise-missing-from
            f"Could not find social_group '{exc.args[0]}' in the database"
        )

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

    distribution["is_primary"] = distribution["social_group_id"].apply(lambda x: x in primary_sgs_ids)
    primary_sgs_total = (
        distribution[distribution["is_primary"]]["men"] + distribution[distribution["is_primary"]]["women"]
    ).sum()

    primaries: list[SocialGroupWithProbability] = []
    additionals: list[SocialGroupWithProbability] = []

    for sg_id, sg_df in distribution.groupby("social_group_id"):
        men = [0] * (max_age + 1)
        women = [0] * (max_age + 1)
        for _, (age, men_count, women_count) in sg_df[["age", "men", "women"]].iterrows():
            if age > max_age or age < 0:
                logger.warning(
                    "Ignoring {} + {} people of age {} as max_age is set to {}", men_count, women_count, age, max_age
                )
                continue
            men[int(age)] = men_count
            women[int(age)] = women_count
        (primaries if sg_id in primary_sgs_ids else additionals).append(
            SocialGroupWithProbability.from_values(
                str(sg_id), (sg_df["men"] + sg_df["women"]).sum() / primary_sgs_total, men, women
            )
        )

    return SocialGroupsDistribution(primaries, additionals)

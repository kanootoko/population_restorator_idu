"""Sex-age-social_groups-houses people distribution table definition is defined here."""
from typing import Callable

from sqlalchemy import Column, Enum, ForeignKey, Index, Sequence, SmallInteger, Table

from idu_balance_db.db import metadata
from idu_balance_db.db.entities.enums import ForecastScenario


func: Callable

sex_age_social_houses_id_seq = Sequence("sex_age_social_houses_id_seq", schema="social_stats")

t_sex_age_social_houses = Table(
    "sex_age_social_houses",
    metadata,
    Column("year", SmallInteger, primary_key=True, nullable=False),
    Column("scenario", Enum(ForecastScenario, name="social_stats_scenario"), primary_key=True, nullable=False),
    Column("building_id", ForeignKey("buildings.id"), primary_key=True, nullable=False),
    Column("social_group_id", ForeignKey("social_groups.id"), primary_key=True, nullable=False),
    *(Column(f"men_{i}", SmallInteger, nullable=False) for i in range(101)),
    *(Column(f"women_{i}", SmallInteger, nullable=False) for i in range(101)),
    Index(
        "sex_age_social_houses_year_scenario_building_id_social_group_id",
        "year",
        "scenario",
        "building_id",
        "social_group_id",
        unique=True,
    ),
    schema="social_stats",
)
"""sex-age-social_groups people distribution.

Balanced data goed to this table after the third step.

Columns:
- `year` - year of distribution, integer
- `scenario` - forecasting scenario, ForecastScenario enum
- `building_id` - identifier of a building, integer
- `social_group_id` - identifier of a social_group, integer
- `men_{0, 1, ..., 100} - number of men of a given age and social_group for the year.
- `women_{0, 1, ..., 100} - number of women of a given age and social_group for the year.
"""

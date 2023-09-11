"""age-sex-social-stat-administrative_units table schema is defined here."""
from sqlalchemy import Column, ForeignKey, Integer, Table, SmallInteger

from idu_balance_db.db import metadata

t_age_sex_social_stat_administrative_units = Table(
    "age_sex_social_stat_administrative_units",
    metadata,
    Column("year", SmallInteger, primary_key=True, nullable=False),
    Column("administrative_unit_id", ForeignKey("administrative_units.id"), primary_key=True, nullable=False),
    Column("social_group_id", ForeignKey("social_groups.id"), primary_key=True, nullable=False),
    Column("age", SmallInteger, primary_key=True, nullable=False),
    Column("men", Integer),
    Column("women", Integer),
)
"""Age-sex statistic for municipalities per year.

This table does not belong to public schema and should be (re)moved.

Columns:
- `year` - year of the statistic, smallint
- `administrative_unit_id` - identifier of an administrative unit, int
- `social_group_id` - identifier of a social group, integer
- `age` - age of a person, smallint
- `men` - total number of men with a given age and social group in a given administrative unit at the given year.
- `women` - total number of women with a given age and social group in a given administrative unit at the given year.
"""

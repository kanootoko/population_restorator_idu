"""age-sex-stat-municipalities table schema is defined here."""
from sqlalchemy import Column, ForeignKey, Integer, SmallInteger, Table

from idu_balance_db.db import metadata


t_age_sex_stat_municipalities = Table(
    "age_sex_stat_municipalities",
    metadata,
    Column("year", SmallInteger, primary_key=True, nullable=False),
    Column("municipality_id", ForeignKey("municipalities.id"), primary_key=True, nullable=False),
    Column("age", SmallInteger, primary_key=True, nullable=False),
    Column("men", Integer),
    Column("women", Integer),
)
"""Age-sex statistic for municipalities per year.

This table does not belong to public schema and should be (re)moved.

Columns:
- `year` - year of the statistic, smallint
- `municipality_id` - identifier of a municipality, int
- `age` - age of a person, smallint
- `men` - total number of men with a given age in a given municipality at the given year.
- `women` - total number of women with a given age in a given municipality at the given year.
"""

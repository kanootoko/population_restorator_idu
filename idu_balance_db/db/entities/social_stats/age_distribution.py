"""age_distribution table schema is defined here."""
from sqlalchemy import Column, Float, ForeignKey, SmallInteger, Table

from idu_balance_db.db import metadata


t_age_distribution = Table(
    "age_distribution",
    metadata,
    Column("city_id", ForeignKey("cities.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column("age", SmallInteger, primary_key=True, nullable=False),
    Column("men", Float(53), nullable=False),
    Column("women", Float(53), nullable=False),
    schema="social_stats",
)
"""Probability distribution of ages.

Columns:
- `city_id` - identifier of city, int
- `age` - age of a person, smallint
- `men` - probability for a man to have a given age, float
- `women` - probability for a woman to have a given age, float
"""

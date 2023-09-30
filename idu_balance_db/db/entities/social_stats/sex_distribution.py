"""sex_distribution table schema is defined here."""
from sqlalchemy import Column, Float, ForeignKey, Table

from idu_balance_db.db import metadata


t_sex_distribution = Table(
    "sex_distribution",
    metadata,
    Column("city_id", ForeignKey("cities.id", ondelete="CASCADE"), primary_key=True),
    Column("men", Float(53), nullable=False),
    Column("women", Float(53), nullable=False),
    schema="social_stats",
)
"""Probability distribution of genders.

Columns:
- `city_id` - identifier of city, int
- `men` - probability for a person to be a men, float
- `women` - probability for a person to be a women, float
"""

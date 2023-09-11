"""social_group_distribution table schema is defined here."""
from sqlalchemy import Column, Float, ForeignKey, Table

from idu_balance_db.db import metadata

t_social_group_distribution = Table(
    "social_group_distribution",
    metadata,
    Column("city_id", ForeignKey("cities.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column("social_group_id", ForeignKey("social_groups.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column("men", Float(53), nullable=False),
    Column("women", Float(53), nullable=False),
    schema="social_stats",
)
"""Probability distribution of social groups.

Columns:
- `city_id` - identifier of city, int
- `social_group_id` - identifier of social_group, int
- `men` - probability for a man to be in a given social group, float
- `women` - probability for a woman to be in a given social group, float
"""

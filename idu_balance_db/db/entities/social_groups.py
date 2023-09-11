"""Social groups table scehma is defined here."""
from typing import Callable

from sqlalchemy import Column, Float, ForeignKey, Integer, Sequence, String, Table

from idu_balance_db.db import metadata


func: Callable

social_groups_id_seq = Sequence("social_groups_id_seq")

t_social_groups = Table(
    "social_groups",
    metadata,
    Column("id", Integer, primary_key=True, server_default=social_groups_id_seq.next_value()),
    Column("name", String, nullable=False, unique=True),
    Column("code", String, nullable=False, unique=True),
    Column("parent_id", ForeignKey("social_groups.id", deferrable=True, initially="DEFERRED")),
    Column("social_group_value", Float(53)),
)
"""social_groups.

Columns:
- `id` - identitier, integer
- `name` - social group name in Russian, varchar(50)
- `code` - social group name in English, varchar(50)
- `parent_id` - social_group parent identifier, integer nullable
- `social_group_value` - value that indicates how much people appreciate being in a given social_group, float
"""

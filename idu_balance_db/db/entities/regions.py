"""Regions table schema is defined here."""
from typing import Callable

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Integer, Sequence, String, Table, func

from idu_balance_db.db import metadata


func: Callable


regions_id_seq = Sequence("regions_id_seq")

t_regions = Table(
    "regions",
    metadata,
    Column("id", Integer, primary_key=True, server_default=regions_id_seq.next_value()),
    Column("name", String(50), nullable=False, unique=True),
    Column("code", String(50), nullable=False, unique=True),
    Column(
        "geometry",
        Geometry(srid=4326, spatial_index=False, from_text="ST_GeomFromEWKT", name="geometry", nullable=False),
        nullable=False,
    ),
    Column(
        "center",
        Geometry("POINT", 4326, spatial_index=False, from_text="ST_GeomFromEWKT", name="geometry", nullable=False),
        nullable=False,
    ),
    Column("created_at", DateTime(True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(True), nullable=False, server_default=func.now()),
)
"""Regions (administrative division above cities).

Columns:
- `id` - identitier, integer
- `name` - region name in Russian, varchar(50)
- `code` - region name in English, varchar(50)
- `geometry` - geometry(4326)
- `center` - geometry(point, 4326)
- `created_at` - time of insertion, DateTimeTz
- `updated_at` - time of last edit, DateTimeTz
"""

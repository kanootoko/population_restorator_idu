"""Blocks table schema is defined here."""
from typing import Callable

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Sequence, Table, func

from idu_balance_db.db import metadata


func: Callable

blocks_id_seq = Sequence("blocks_id_seq")

t_blocks = Table(
    "blocks",
    metadata,
    Column("id", Integer, primary_key=True, server_default=blocks_id_seq.next_value()),
    Column("city_id", ForeignKey("cities.id")),
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
    Column("population", Integer),
    Column("created_at", DateTime(True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(True), nullable=False, server_default=func.now()),
    Column("municipality_id", ForeignKey("municipalities.id")),
    Column("administrative_unit_id", ForeignKey("administrative_units.id")),
    Column("area", Float(53)),
)
"""Blocks as a lower administrative division unit.

Columns:
- `id` - identitier, integer
- `city_id` - identifier of city, int
- `type_id` - identifier of administrative_unit_type, int
- `name` - name of administrative unit, varchar(50)
- `geometry` - geometry(4326)
- `center` - geometry(point, 4326)
- `population` - total population, integer
- `created_at` - time of insertion, DateTimeTz
- `updated_at` - time of last edit, DateTimeTz
- `municipality_id` - identifier of municipality as parent, int nullable
- `administrative_unit_id` - identifier of administrative unit parent (unused mostly), int nullable
- `area` - area of block, float
"""

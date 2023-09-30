"""Municipalities table schema is defined here."""
from typing import Callable

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Sequence, String, Table, func

from idu_balance_db.db import metadata


func: Callable

municipalities_id_seq = Sequence("municipalities_id_seq")

municipality_types_id_seq = Sequence("municipality_types_id_seq")

t_municipality_types = Table(
    "municipality_types",
    metadata,
    Column("id", Integer, primary_key=True, server_default=municipality_types_id_seq.next_value()),
    Column("full_name", String(50), nullable=False, unique=True),
    Column("short_name", String(10), nullable=False, unique=True),
)
"""Types of municipalities.

Columns:
- `id` - identitier, integer
- `full_name` - full name of type, varchar(50)
- `short_name` - short name of type, varchar(10)
"""

t_municipalities = Table(
    "municipalities",
    metadata,
    Column("id", Integer, primary_key=True, server_default=municipalities_id_seq.next_value()),
    Column("parent_id", ForeignKey("municipalities.id")),
    Column("city_id", ForeignKey("cities.id"), nullable=False),
    Column("type_id", ForeignKey("municipality_types.id"), nullable=False),
    Column("name", String(50), nullable=False),
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
    Column("admin_unit_parent_id", Integer),
)
"""municipalities (city inner or outer division unit).

Columns:
- `id` - identitier, integer
- `parent_id` - identifier of municipality as a parent (unused mostly), int nullable
- `city_id` - identifier of city, int
- `type_id` - identifier of municipality_type, int
- `name` - name of municipality, varchar(50)
- `geometry` - geometry(4326)
- `center` - geometry(point, 4326)
- `population` - total population, integer nullable
- `created_at` - time of insertion, DateTimeTz
- `updated_at` - time of last edit, DateTimeTz
- `admin_unit_parent_id` - identifier of administrative_unit as a parent
(available if city division type is ADMINISTRATIVE_UNIT_PARENT), int nullable
"""

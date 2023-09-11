"""Administrative units table schema is defined here."""
from typing import Callable

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Sequence, String, Table, func

from idu_balance_db.db import metadata


func: Callable

administrative_units_id_seq = Sequence("administrative_units_id_seq")

administrative_unit_types_id_seq = Sequence("administrative_unit_types_id_seq")

t_administrative_unit_types = Table(
    "administrative_unit_types",
    metadata,
    Column("id", Integer, primary_key=True, server_default=administrative_unit_types_id_seq.next_value()),
    Column("full_name", String(50), nullable=False, unique=True),
    Column("short_name", String(10), nullable=False, unique=True),
)
"""Types of administrative units.

Columns:
- `id` - identitier, integer
- `full_name` - full name of type, varchar(50)
- `short_name` - short name of type, varchar(10)
"""

t_administrative_units = Table(
    "administrative_units",
    metadata,
    Column("id", Integer, primary_key=True, server_default=administrative_units_id_seq.next_value()),
    Column("parent_id", ForeignKey("administrative_units.id")),
    Column("city_id", ForeignKey("cities.id"), nullable=False),
    Column("type_id", ForeignKey("administrative_unit_types.id"), nullable=False),
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
    Column("municipality_parent_id", Integer),
)
"""Administrative units (city inner or outer division unit).

Columns:
- `id` - identitier, integer
- `parent_id` - identifier of administrative unit as a parent (unused mostly), int nullable
- `city_id` - identifier of city, int
- `type_id` - identifier of administrative_unit_type, int
- `name` - name of administrative unit, varchar(50)
- `geometry` - geometry(4326)
- `center` - geometry(point, 4326)
- `population` - total population, integer
- `created_at` - time of insertion, DateTimeTz
- `updated_at` - time of last edit, DateTimeTz
- `municipality_parent_id` - identifier of municipality as a parent (available if city division type is MUNICIPALITY_PARENT), int nullable
"""

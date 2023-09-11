"""Cities table schema is defined here."""
from typing import Callable

from geoalchemy2.types import Geometry
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Sequence, String, Table, func

from idu_balance_db.db import metadata

from .enums import CityDivisionType


func: Callable

cities_id_seq = Sequence("cities_id_seq")

t_cities = Table(
    "cities",
    metadata,
    Column("id", Integer, primary_key=True, server_default=cities_id_seq.next_value()),
    Column("name", String(50), nullable=False, unique=True),
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
    Column(
        "city_division_type",
        Enum(CityDivisionType, name="city_division_type"),
        nullable=False,
    ),
    Column("local_crs", Integer),
    Column("code", String(50)),
    Column("region_id", ForeignKey("regions.id")),
)
"""Cities.

Columns:
- `id` - identitier, integer
- `name` - city name in Russian, varchar(50)
- `geometry` - geometry(4326)
- `center` - geometry(point, 4326)
- `population` - total population, integer
- `created_at` - time of insertion, DateTimeTz
- `updated_at` - time of last edit, DateTimeTz
- `city_division_type` - type of division, CityDividionType
- `local_crs` - local coordinate system identifier, integer nullable
- `code` - city name in Englisg, varchar(50) nullable
- `region_id` - identifier of region, integer nullable
"""

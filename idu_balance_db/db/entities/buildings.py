"""Buildings table schema is defined here."""
from typing import Callable

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, Sequence, SmallInteger, String, Table, Text, text
from sqlalchemy.dialects.postgresql import JSONB

from idu_balance_db.db import metadata


func: Callable

buildings_id_seq = Sequence("buildings_id_seq")

t_buildings = Table(
    "buildings",
    metadata,
    Column("id", Integer, primary_key=True, server_default=buildings_id_seq.next_value()),
    Column("physical_object_id", ForeignKey("physical_objects.id"), unique=True),
    Column("address", String(200)),
    Column("project_type", String(100)),
    Column("building_date", String(50)),
    Column("building_area", Float),
    Column("living_area", Float),
    Column("storeys_count", SmallInteger),
    Column("resident_number", SmallInteger),
    Column("central_heating", Boolean),
    Column("central_hotwater", Boolean),
    Column("central_electro", Boolean),
    Column("central_gas", Boolean),
    Column("refusechute", Boolean),
    Column("ukname", String(100)),
    Column("failure", Boolean),
    Column("lift_count", SmallInteger),
    Column("repair_years", String(100)),
    Column("is_living", Boolean),
    Column("population_balanced", SmallInteger, server_default=text("0")),
    Column("central_water", Boolean),
    Column("modeled", JSONB(astext_type=Text()), nullable=False, server_default=text("'{}'::jsonb")),
    Column("building_year", SmallInteger),
    Column("properties", JSONB(astext_type=Text()), nullable=False, server_default=text("'{}'::jsonb")),
)
"""builldings.

Columns:
- `id` - identitier, integer
- `physical_object_id` - identifier of a physical object building is linked to, integer
- `address` - address, varchar(200) nullable
- `project_type` - project type name, varchar(100) nullable
- `building_area` - area of the building single floor in square meters, float nullable
- `living_area` - total living area of all floors in square meters, float nullable
- `storeys_count` - number of floors, integer nullable
- `resident_number` - number of people living in the building from open data, int nullable
- `central_heating` - indicates whether centralized heating is present, bool nullable
- `central_hotwater` - indicates whether centralized hot water is present, bool nullable
- `central_electro` - indicates whether centralized electricity is present, bool nullable
- `central_gas` - indicates whether centralized gas is present, bool nullable
- `refusechute` - indicates whether refuse chute is present, bool nullable
- `ukname` - name of a management company, varchar(100) nullable
- `failure` - indicates whether building is in failing state, bool nullable
- `lift_count` - total numbe of elevators, int nullable
- `repair_years` - years of repairement procedures joined by ';', varchar(100) nullable
- `is_living` - indicates whether people live in the building, bool nullable
- `population_balanced` - balanced population, integer nullable
- `central_water` - indicates whether centralized cold water is present, bool nullable
- `modeled` - modeled parameters in format {"name": 1}, jsonb
- `building_year` - year of construction, integer nullable
- `properties` - additional building properties, jsonb
"""

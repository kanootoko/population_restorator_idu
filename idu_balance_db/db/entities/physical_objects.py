"""Physical objects table schema is defined here."""
from typing import Callable

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Sequence, String, Table, func

from idu_balance_db.db import metadata


func: Callable

physical_objects_id_seq = Sequence("physical_objects_id_seq")

t_physical_objects = Table(
    "physical_objects",
    metadata,
    Column("id", Integer, primary_key=True, server_default=physical_objects_id_seq.next_value()),
    Column("osm_id", String(50)),
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
    Column("city_id", ForeignKey("cities.id"), nullable=False),
    Column("municipality_id", ForeignKey("municipalities.id")),
    Column("administrative_unit_id", ForeignKey("administrative_units.id")),
    Column("block_id", ForeignKey("blocks.id")),
    Column("created_at", DateTime(True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(True), nullable=False, server_default=func.now()),
)

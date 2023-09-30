"""Database-related stuff is located here."""
from sqlalchemy import MetaData


__all__ = [
    "metadata",
]

metadata = MetaData()

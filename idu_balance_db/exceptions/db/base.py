"""Base exception of database layer is defined here."""

from idu_balance_db.exceptions.base import IduBalanceDbError


class DatabaseLayerError(IduBalanceDbError):
    """Base exception on the database layer of the balancer to inherit from."""

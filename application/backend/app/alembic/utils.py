# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Shared utilities for Alembic migrations."""

from collections.abc import Iterator
from contextlib import contextmanager

from alembic import op
from sqlalchemy.engine import Connection


def _check_foreign_keys(bind: Connection, message: str) -> None:
    violation = bind.exec_driver_sql("PRAGMA foreign_key_check").first()
    if violation is not None:
        table, rowid, parent, constraint = violation
        raise RuntimeError(f"{message}: table={table!r}, rowid={rowid!r}, parent={parent!r}, constraint={constraint}.")


@contextmanager
def sqlite_batch_rebuild() -> Iterator[None]:
    """Protect SQLite table rebuilds from foreign-key cascades.

    Check for existing violations before changing enforcement, disable it outside
    the transaction, and protect schema and data changes with a savepoint.
    Check integrity again before releasing the savepoint and restore the original
    enforcement setting on both success and failure.

    Autocommit blocks commit preceding work, so keep the protected scope narrow.
    Use this helper only within an online SQLite migration.

    Yields:
        Control to the migration's batch operations.

    Raises:
        RuntimeError: The migration is offline, uses another database dialect,
            or the database has foreign-key violations before or after the rebuild.
    """
    bind = op.get_bind()
    context = op.get_context()
    if context.as_sql or bind.dialect.name != "sqlite":
        raise RuntimeError("sqlite_batch_rebuild requires an online SQLite migration.")

    _check_foreign_keys(bind, "Database already violates foreign-key integrity")
    foreign_keys = bind.exec_driver_sql("PRAGMA foreign_keys").scalar_one()
    with context.autocommit_block():
        bind.exec_driver_sql("PRAGMA foreign_keys=OFF")
    try:
        with bind.begin_nested():
            yield
            _check_foreign_keys(bind, "Migration would violate foreign-key integrity")
    finally:
        with context.autocommit_block():
            bind.exec_driver_sql("PRAGMA foreign_keys=ON" if foreign_keys else "PRAGMA foreign_keys=OFF")

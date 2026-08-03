# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Defer side effects until a database session successfully commits.

Cross-process consumers (e.g. the ``StreamLoader``) react to events by re-reading the affected
entity from the database in their own session/process. Emitting such an event while the writing
transaction is still open lets that reload race the commit and read *stale* data (e.g. the previous
``video_path`` of a source). Registering the emission as an ``after_commit`` hook guarantees the new
data is durably visible before any consumer is notified.

Callbacks are scheduled per :class:`~sqlalchemy.orm.Session` via :func:`run_after_commit` and are
executed by the module-level ``after_commit`` listener. Callbacks scheduled on a transaction that is
rolled back are discarded.
"""

from collections.abc import Callable

from loguru import logger
from sqlalchemy import event
from sqlalchemy.orm import Session

# Key under which the pending callbacks are stored in ``Session.info`` (a per-session dict that is
# reset for every new Session instance, so callbacks never leak across requests).
_CALLBACKS_KEY = "after_commit_callbacks"


def run_after_commit(session: Session, callback: Callable[[], None]) -> None:
    """Schedule ``callback`` to run once ``session`` successfully commits.

    Callbacks registered for a transaction that is later rolled back are discarded.
    """
    session.info.setdefault(_CALLBACKS_KEY, []).append(callback)


@event.listens_for(Session, "after_commit")
def _run_after_commit_callbacks(session: Session) -> None:
    """Run and clear the callbacks scheduled for ``session`` once its transaction has committed."""
    callbacks: list[Callable[[], None]] = session.info.pop(_CALLBACKS_KEY, [])
    for callback in callbacks:
        try:
            callback()
        except Exception:
            # A misbehaving callback must not prevent the remaining callbacks from running.
            logger.exception("after-commit callback raised an exception; continuing")


@event.listens_for(Session, "after_rollback")
def _discard_after_commit_callbacks(session: Session) -> None:
    """Drop any callbacks scheduled for ``session`` when its transaction is rolled back."""
    session.info.pop(_CALLBACKS_KEY, None)

# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session_hooks import run_after_commit


@pytest.fixture
def session() -> Generator[Session]:
    """A real (in-memory) SQLAlchemy session to exercise the commit/rollback lifecycle."""
    engine = create_engine("sqlite://", poolclass=StaticPool)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


class TestRunAfterCommit:
    def test_callback_runs_after_commit(self, session: Session) -> None:
        """The scheduled callback runs only once the session commits, not before."""
        callback = MagicMock()
        # Ensure a transaction is active so commit actually fires the after_commit event.
        session.begin()

        run_after_commit(session, callback)
        callback.assert_not_called()

        session.commit()

        callback.assert_called_once_with()

    def test_callback_discarded_on_rollback(self, session: Session) -> None:
        """A callback scheduled on a rolled-back transaction is never run, even after a later commit."""
        callback = MagicMock()
        session.begin()

        run_after_commit(session, callback)
        session.rollback()

        callback.assert_not_called()

        # A subsequent, unrelated commit must not resurrect the discarded callback.
        session.begin()
        session.commit()
        callback.assert_not_called()

    def test_multiple_callbacks_run_in_order(self, session: Session) -> None:
        """All callbacks scheduled for a transaction run, in registration order, on commit."""
        calls: list[str] = []
        session.begin()

        run_after_commit(session, lambda: calls.append("first"))
        run_after_commit(session, lambda: calls.append("second"))
        session.commit()

        assert calls == ["first", "second"]

    def test_failing_callback_does_not_block_others(self, session: Session) -> None:
        """A raising callback is isolated so the remaining callbacks still run."""
        ok_callback = MagicMock()
        session.begin()

        run_after_commit(session, MagicMock(side_effect=RuntimeError("boom")))
        run_after_commit(session, ok_callback)
        # Must not raise despite the first callback failing.
        session.commit()

        ok_callback.assert_called_once_with()

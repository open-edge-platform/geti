# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""SQLite migration, backup, and revision-status regression tests."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script.revision import ResolutionError
from sqlalchemy import MetaData, Table, create_engine, inspect, select

from app.alembic.utils import sqlite_batch_rebuild
from app.db.migration import MigrationManager, RevisionNotFoundError


def _manager(tmp_path: Path) -> MigrationManager:
    settings = SimpleNamespace(data_dir=tmp_path, database_file="geti.db")
    return MigrationManager(settings)  # type: ignore[arg-type]


def _create_db(path: Path, value: str) -> None:
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("CREATE TABLE t (v TEXT)")
        conn.execute("INSERT INTO t (v) VALUES (?)", (value,))
        conn.commit()
    finally:
        conn.close()


@contextmanager
def _mock_connect():
    yield MagicMock()


def _read_value(path: Path) -> str:
    conn = sqlite3.connect(str(path))
    try:
        return conn.execute("SELECT v FROM t").fetchone()[0]
    finally:
        conn.close()


def _mock_migration_script(current_head: str, known_revisions: set[str]) -> MagicMock:
    script = MagicMock()
    script.get_current_head.return_value = current_head

    def _get_revision(rev_id: str) -> MagicMock:
        if rev_id not in known_revisions:
            raise ResolutionError("Can't locate revision", rev_id)
        return MagicMock()

    script.get_revision.side_effect = _get_revision
    return script


class TestBackupDatabase:
    def test_returns_none_on_fresh_install(self, tmp_path: Path) -> None:
        assert _manager(tmp_path)._backup_database() is None

    def test_creates_consistent_backup(self, tmp_path: Path) -> None:
        manager = _manager(tmp_path)
        _create_db(manager.database_path, "original")

        backup = manager._backup_database()

        assert backup is not None
        assert backup.exists()
        assert _read_value(backup) == "original"


class TestCheckMigrationStatus:
    def test_intermediate_revision_is_recognized(self, tmp_path: Path) -> None:
        """Regression test for #7355: an intermediate (non-head, non-base) revision
        must not be mistaken for an unrecognized schema revision."""
        manager = _manager(tmp_path)
        script = _mock_migration_script(current_head="head_rev", known_revisions={"base_rev", "mid_rev", "head_rev"})

        with (
            patch.object(manager, "get_alembic_config", return_value=MagicMock()),
            patch("app.db.migration.ScriptDirectory.from_config", return_value=script),
            patch("app.db.migration.db_engine.connect", side_effect=_mock_connect),
            patch("app.db.migration.migration.MigrationContext.configure") as mock_configure,
        ):
            mock_configure.return_value.get_current_revision.return_value = "mid_rev"

            needs_migration, status = manager.check_migration_status()

        assert needs_migration is True
        assert "mid_rev" in status

    def test_unknown_revision_raises(self, tmp_path: Path) -> None:
        manager = _manager(tmp_path)
        script = _mock_migration_script(current_head="head_rev", known_revisions={"base_rev", "head_rev"})

        with (
            patch.object(manager, "get_alembic_config", return_value=MagicMock()),
            patch("app.db.migration.ScriptDirectory.from_config", return_value=script),
            patch("app.db.migration.db_engine.connect", side_effect=_mock_connect),
            patch("app.db.migration.migration.MigrationContext.configure") as mock_configure,
        ):
            mock_configure.return_value.get_current_revision.return_value = "unknown_rev"

            with pytest.raises(RevisionNotFoundError):
                manager.check_migration_status()


def test_ome_schema_migration_preserves_video_frames_and_dependents(tmp_path: Path) -> None:
    """Verify OME upgrade, downgrade, and re-upgrade preserve existing video data.

    Seed the pre-OME schema with a video, an annotated frame, a label link, and
    dataset-view membership. Assert that media table rebuilds retain these rows,
    preserve frame indexing, and leave foreign-key integrity intact. Upgrades
    must also create the unique OME plane coordinate index.

    Args:
        tmp_path: Temporary directory for the isolated SQLite database.
    """
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parents[3] / "app" / "alembic"))
    url = f"sqlite:///{tmp_path / 'migration.db'}"
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "b7e2d94a1f3c")
    engine = create_engine(url)
    try:
        with engine.begin() as connection:
            metadata = MetaData()
            projects = Table("projects", metadata, autoload_with=connection)
            media = Table("media", metadata, autoload_with=connection)
            items = Table("dataset_items", metadata, autoload_with=connection)
            labels = Table("labels", metadata, autoload_with=connection)
            item_labels = Table("dataset_items_labels", metadata, autoload_with=connection)
            views = Table("dataset_views", metadata, autoload_with=connection)
            view_items = Table("dataset_view_items", metadata, autoload_with=connection)
            connection.execute(
                projects.insert().values(id="project", name="migration", task_type="detection", exclusive_labels=False)
            )
            common = {"project_id": "project", "width": 10, "height": 8, "size": 1}
            connection.execute(
                media.insert().values(
                    **common, id="video", name="video", type="video", format="mp4", frame_count=2, fps=1
                )
            )
            connection.execute(
                media.insert().values(
                    **common,
                    id="frame",
                    name="frame",
                    type="video_frame",
                    format="jpg",
                    video_id="video",
                    frame_index=1,
                )
            )
            annotation_data = [{"labels": [{"id": "label"}], "shape": {"type": "full_image"}}]
            connection.execute(
                items.insert().values(
                    id="frame",
                    project_id="project",
                    subset="training",
                    user_reviewed=True,
                    annotation_data=annotation_data,
                )
            )
            connection.execute(labels.insert().values(id="label", project_id="project", name="cell", color="#FFFFFF"))
            connection.execute(item_labels.insert().values(dataset_item_id="frame", label_id="label"))
            connection.execute(views.insert().values(id="view", project_id="project", name="all"))
            connection.execute(view_items.insert().values(dataset_view_id="view", media_id="video"))

        for target, parent_column in [
            ("head", "parent_id"),
            ("b7e2d94a1f3c", "video_id"),
            ("head", "parent_id"),
        ]:
            if target == "head":
                command.upgrade(config, target)
            else:
                command.downgrade(config, target)
            with engine.connect() as connection:
                media = Table("media", MetaData(), autoload_with=connection)
                row = connection.execute(select(media).where(media.c.id == "frame")).mappings().one()
                assert row[parent_column] == "video"
                assert row["frame_index"] == 1
                assert connection.execute(select(media.c.id).order_by(media.c.id)).scalars().all() == ["frame", "video"]
                assert connection.execute(select(items.c.annotation_data)).scalar_one() == annotation_data
                assert connection.execute(select(items.c.subset)).scalar_one() == "training"
                assert connection.execute(select(items.c.user_reviewed)).scalar_one() is True
                assert connection.execute(select(item_labels.c.dataset_item_id)).scalar_one() == "frame"
                assert connection.execute(select(view_items.c.media_id)).scalar_one() == "video"
                assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
                assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
                if target == "head":
                    index = next(
                        item
                        for item in inspect(connection).get_indexes("media")
                        if item["name"] == "uq_parent_id_z_index_t_index"
                    )
                    assert index["unique"]
                    assert index["column_names"] == ["parent_id", "z_index", "t_index"]
    finally:
        engine.dispose()


@pytest.mark.parametrize("foreign_keys", [0, 1])
@pytest.mark.parametrize("failure", ["exception", "foreign_key"])
def test_sqlite_batch_rebuild_rolls_back_and_restores_foreign_keys(
    tmp_path: Path, foreign_keys: int, failure: str
) -> None:
    """Verify failed rebuilds roll back schema and data changes and restore enforcement.

    Exercise both an explicit exception and a failed referential-integrity check
    with foreign-key enforcement initially enabled or disabled. The savepoint
    must restore the deleted parent, retain its child, remove the temporary
    table, and restore the original enforcement setting.

    Args:
        tmp_path: Temporary directory for the isolated SQLite database.
        foreign_keys: Initial SQLite enforcement setting, either 0 or 1.
        failure: Failure mode, either "exception" or "foreign_key".
    """
    engine = create_engine(f"sqlite:///{tmp_path / 'rollback.db'}")
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("CREATE TABLE parent (id INTEGER PRIMARY KEY)")
            connection.exec_driver_sql("CREATE TABLE child (parent_id INTEGER REFERENCES parent(id) ON DELETE CASCADE)")
            connection.exec_driver_sql("INSERT INTO parent VALUES (1)")
            connection.exec_driver_sql("INSERT INTO child VALUES (1)")
            connection.commit()
            connection.exec_driver_sql(f"PRAGMA foreign_keys={foreign_keys}")
            connection.commit()
            context = MigrationContext.configure(connection)
            with context.begin_transaction(_per_migration=True), Operations.context(context):
                message = "forced rebuild failure" if failure == "exception" else "foreign-key integrity"
                with pytest.raises(RuntimeError, match=message) as error, sqlite_batch_rebuild():
                    assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 0
                    connection.exec_driver_sql("CREATE TABLE temporary_rebuild (id INTEGER)")
                    connection.exec_driver_sql("DELETE FROM parent")
                    if failure == "exception":
                        raise RuntimeError("forced rebuild failure")
                if failure == "foreign_key":
                    assert "table='child', rowid=1, parent='parent', constraint=0" in str(error.value)
                assert connection.exec_driver_sql("SELECT id FROM parent").scalar_one() == 1
                assert connection.exec_driver_sql("SELECT parent_id FROM child").scalar_one() == 1
                assert not inspect(connection).has_table("temporary_rebuild")
                assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
                assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == foreign_keys
    finally:
        engine.dispose()


@pytest.mark.parametrize(("as_sql", "dialect"), [(True, "sqlite"), (False, "postgresql")])
def test_sqlite_batch_rebuild_rejects_unsupported_contexts(as_sql: bool, dialect: str) -> None:
    """Reject offline and non-SQLite migrations before modifying database state."""
    with patch("app.alembic.utils.op") as operations:
        operations.get_context.return_value.as_sql = as_sql
        operations.get_bind.return_value.dialect.name = dialect
        with pytest.raises(RuntimeError, match="requires an online SQLite migration"), sqlite_batch_rebuild():
            pytest.fail("An unsupported migration context must not enter the rebuild scope.")
        operations.get_bind.return_value.exec_driver_sql.assert_not_called()

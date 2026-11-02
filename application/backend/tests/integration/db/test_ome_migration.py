# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import sqlite3
from collections.abc import Callable
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

import app

PREVIOUS_REVISION = "b7e2d94a1f3c"
OME_REVISION = "3e9f1c7a2b64"


@pytest.fixture
def fxt_alembic(tmp_path: Path) -> tuple[Config, Callable[[], sqlite3.Connection]]:
    database = tmp_path / "geti.db"
    config = Config()
    config.set_main_option("script_location", str(Path(app.__file__).parent / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")

    def _connect() -> sqlite3.Connection:
        connection = sqlite3.connect(database)
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    return config, _connect


def _seed_video_with_annotated_frame(connection: sqlite3.Connection) -> None:
    connection.execute("INSERT INTO projects (id, name, task_type, exclusive_labels) VALUES ('p', 'p', 'detection', 0)")
    connection.execute(
        "INSERT INTO media (id, project_id, type, name, format, width, height, frame_count, fps, size) "
        "VALUES ('v', 'p', 'video', 'v', 'mp4', 8, 8, 10, 1.0, 100)"
    )
    connection.execute(
        "INSERT INTO media (id, project_id, type, name, format, width, height, video_id, frame_index, size) "
        "VALUES ('f', 'p', 'video_frame', 'f', 'jpg', 8, 8, 'v', 3, 10)"
    )
    connection.execute(
        "INSERT INTO dataset_items (id, project_id, user_reviewed, subset) VALUES ('f', 'p', 1, 'training')"
    )
    connection.commit()


class TestOmeMigration:
    def test_upgrade_preserves_video_frames(self, fxt_alembic):
        config, connect = fxt_alembic
        command.upgrade(config, PREVIOUS_REVISION)
        with connect() as connection:
            _seed_video_with_annotated_frame(connection)

        command.upgrade(config, OME_REVISION)

        with connect() as connection:
            assert connection.execute("SELECT id, parent_id, frame_index FROM media ORDER BY id").fetchall() == [
                ("f", "v", 3),
                ("v", None, None),
            ]
            assert connection.execute("SELECT id FROM dataset_items").fetchall() == [("f",)]
            foreign_keys = connection.execute("PRAGMA foreign_key_list(media)").fetchall()
            assert any(fk[2] == "media" and fk[3] == "parent_id" and fk[6] == "CASCADE" for fk in foreign_keys)
            with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
                connection.execute(
                    "INSERT INTO media (id, project_id, type, name, format, width, height, parent_id, frame_index, "
                    "size) VALUES ('f2', 'p', 'video_frame', 'f2', 'jpg', 8, 8, 'v', 3, 10)"
                )
            # Deleting the parent still cascades to its frames and their dataset items
            connection.execute("DELETE FROM media WHERE id = 'v'")
            assert connection.execute("SELECT COUNT(*) FROM media").fetchone() == (0,)
            assert connection.execute("SELECT COUNT(*) FROM dataset_items").fetchone() == (0,)
            connection.rollback()

    def test_downgrade_restores_video_id(self, fxt_alembic):
        config, connect = fxt_alembic
        command.upgrade(config, PREVIOUS_REVISION)
        with connect() as connection:
            _seed_video_with_annotated_frame(connection)
        command.upgrade(config, OME_REVISION)

        command.downgrade(config, PREVIOUS_REVISION)

        with connect() as connection:
            columns = [row[1] for row in connection.execute("PRAGMA table_info(media)")]
            assert "video_id" in columns
            assert {"parent_id", "z_index", "t_index"}.isdisjoint(columns)
            assert connection.execute("SELECT id, video_id FROM media ORDER BY id").fetchall() == [
                ("f", "v"),
                ("v", None),
            ]
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            assert {"ome_images", "ome_channel_views"}.isdisjoint(tables)

    def test_downgrade_refuses_to_drop_ome_media(self, fxt_alembic):
        config, connect = fxt_alembic
        command.upgrade(config, OME_REVISION)
        with connect() as connection:
            connection.execute(
                "INSERT INTO projects (id, name, task_type, exclusive_labels) VALUES ('p', 'p', 'detection', 0)"
            )
            connection.execute(
                "INSERT INTO media (id, project_id, type, name, format, width, height, frame_count, size) "
                "VALUES ('o', 'p', 'ome_image', 'o', 'ome.tiff', 8, 8, 4, 100)"
            )
            connection.commit()

        with pytest.raises(RuntimeError, match="OME media exist"):
            command.downgrade(config, PREVIOUS_REVISION)

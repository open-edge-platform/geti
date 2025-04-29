# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
from functools import lru_cache

import psycopg2
from geti_logger_tools.logger_config import initialize_logger
from psycopg2 import sql

logger = initialize_logger(__name__)


class PostgreSQLConnection:
    """
    Provides connection to SpiceDB PostgreSQL db.
    """

    conn: psycopg2.extensions.connection = None
    host: str = os.environ.get("POSTGRES_HOST", "impt-postgresql")
    port: int = int(os.environ.get("POSTGRES_PORT", "5432"))
    database: str = os.environ.get("POSTGRES_DB", "spicedb")
    user: str = os.environ.get("SPICEDB_POSTGRES_USER", "")
    password: str = os.environ.get("SPICEDB_POSTGRES_PASSWORD", "")

    def __init__(self) -> None:
        self.psql_conn = self.get_connection()
        self.cursor = self.psql_conn.cursor()

    @classmethod
    def get_connection(cls) -> psycopg2.extensions.connection:
        if cls.conn is not None:
            logger.info("PostgreSQLConnection already initialized.")
            return cls.conn
        try:
            logger.info(f"Initializing PostgreSQLConnection: {cls.host}:{cls.port}")
            cls.conn = psycopg2.connect(
                host=cls.host, port=cls.port, dbname=cls.database, user=cls.user, password=cls.password
            )
            cls.conn.autocommit = True
            return cls.conn
        except Exception:
            logger.exception("Failed to initialize %s", cls.__name__)
            raise

    @classmethod
    def close(cls) -> None:
        logger.info("Closed connection to Postgresql.")
        cls.conn.close()

    def update_userset_object_id(self, mail: str, uid: str) -> None:
        query = sql.SQL("UPDATE relation_tuple SET userset_object_id = (%s) WHERE userset_object_id = (%s)")
        self.cursor.execute(query, (uid, mail))
        logger.info("Updated uid for roles.")

    def update_workspace_object_id(self, workspace_id: str) -> None:
        query = sql.SQL("UPDATE relation_tuple SET object_id = (%s) WHERE namespace = 'workspace'")
        self.cursor.execute(query, (workspace_id,))
        query = sql.SQL(
            "UPDATE relation_tuple SET userset_object_id = (%s) WHERE namespace = 'project' "
            "and userset_namespace='workspace'"
        )
        self.cursor.execute(query, (workspace_id,))
        logger.info("Workspace Id updated.")

    @lru_cache
    def get_userset_object_ids(self) -> list[str]:
        query = sql.SQL("SELECT DISTINCT userset_object_id FROM relation_tuple WHERE userset_namespace='user'")
        self.cursor.execute(query)
        list_uids = self.cursor.fetchall()
        prepared_list = [uid[0] for uid in list_uids]
        logger.info("Received list of user id's from spicedb.")
        return prepared_list

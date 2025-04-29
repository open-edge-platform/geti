# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from utils.env import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_RO_HOST, DB_USER

logger = logging.getLogger(__name__)

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
RO_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_RO_HOST}:{DB_PORT}/{DB_NAME}"

logger.debug(f"Creating engine using following conn string: {DATABASE_URL}")
# DEFAULTS: pool_size=5, max_overflow=10, timeout=30s
# refreshing connections each 15 min
engine = create_engine(url=DATABASE_URL, pool_recycle=900)

logger.debug(f"Creating read-only engine using following conn string: {RO_DATABASE_URL}")
read_only_engine = create_engine(url=RO_DATABASE_URL, pool_recycle=900)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
ReadOnlySessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=read_only_engine)


def get_session() -> Generator[Session, None, None]:
    """Creates and returns synchronous database connection session"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_read_only_session() -> Generator[Session, None, None]:
    """Creates and returns synchronous read-only database connection session"""

    session = ReadOnlySessionLocal()
    try:
        yield session
    finally:
        session.close()

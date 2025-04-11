# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os

DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_RO_HOST = os.environ.get("POSTGRES_RO_HOST", "localhost")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
DB_NAME = os.environ.get("POSTGRES_DB_NAME", "creditsystem")

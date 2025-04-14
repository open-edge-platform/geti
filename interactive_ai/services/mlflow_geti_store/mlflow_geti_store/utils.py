# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa

ARTIFACT_ROOT_URI_PREFIX = "mlflow-artifacts:/"
PRESIGNED_URL_SUFFIX = ".presigned_url"


@dataclass(frozen=True)
class Identifier:
    organization_id: str
    workspace_id: str
    project_id: str
    job_id: str

    @classmethod
    def from_config_file(cls) -> Identifier:
        config_path = os.environ.get("IDENTIFIER_PATH", "/identifier.json")

        with open(config_path) as fp:
            config = json.load(fp)

        return cls(
            organization_id=config["organization_id"],
            workspace_id=config["workspace_id"],
            project_id=config["project_id"],
            job_id=config["job_id"],
        )

    @classmethod
    def from_env_var(cls) -> Identifier:
        config_json = os.environ.get("IDENTIFIER_JSON", "")

        config = json.loads(config_json)

        return cls(
            organization_id=config["organization_id"],
            workspace_id=config["workspace_id"],
            project_id=config["project_id"],
            job_id=config["job_id"],
        )

    def to_path(self) -> Path:
        return Path(
            "organizations",
            self.organization_id,
            "workspaces",
            self.workspace_id,
            "projects",
            self.project_id,
            "jobs",
            self.job_id,
        )


class TimeStampMapper:
    @staticmethod
    def forward(dtimestamp: datetime, multiplier: float = 1000.0) -> int:
        """Convert Python datetime to POSIX integer timestamp (milliseconds)"""
        return round(dtimestamp.timestamp() * multiplier)

    @staticmethod
    def backward(timestamp: int, denominator: float = 1000.0) -> datetime:
        """Convert POSIX integer timestamp (milliseconds) to Python datetime"""
        return datetime.fromtimestamp(timestamp / denominator, tz=timezone.utc)


PYARROW_SCHEMA: pa.Schema = pa.schema(
    [
        ("key", pa.string()),
        ("value", pa.float32()),
        ("timestamp", pa.timestamp(unit="ms", tz="utc")),
        ("step", pa.uint32()),
    ]
)

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines methods and wrappers to work with secrets in Flyte tasks"""

import os
from dataclasses import dataclass
from datetime import datetime
from functools import wraps

from flytekit import Secret, current_context
from geti_types import CTX_SESSION_VAR, ID, RequestSource, make_session
from iai_core.utils.time_utils import now

SECRETS = [
    Secret(
        group="impt-mongodb",
        key="jobs-mongodb-username",
        mount_requirement=Secret.MountType.ENV_VAR,
    ),
    Secret(
        group="impt-mongodb",
        key="jobs-mongodb-password",
        mount_requirement=Secret.MountType.ENV_VAR,
    ),
    Secret(
        group="impt-kafka-jaas-flyte",
        key="user",
        mount_requirement=Secret.MountType.ENV_VAR,
    ),
    Secret(
        group="impt-kafka-jaas-flyte",
        key="password",
        mount_requirement=Secret.MountType.ENV_VAR,
    ),
    Secret(
        group="impt-spice-db",
        key="SPICEDB_GRPC_PRESHARED_KEY",
        mount_requirement=Secret.MountType.ENV_VAR,
    ),
    Secret(
        group="impt-seaweed-fs",
        key="flyte_workflows_access_key",
        mount_requirement=Secret.MountType.ENV_VAR,
    ),
    Secret(
        group="impt-seaweed-fs",
        key="flyte_workflows_secret_key",
        mount_requirement=Secret.MountType.ENV_VAR,
    ),
    Secret(
        group="impt-seaweed-fs",
        key="flyte_workflows_s3_presigned_url_access_key",
        mount_requirement=Secret.MountType.ENV_VAR,
    ),
    Secret(
        group="impt-seaweed-fs",
        key="flyte_workflows_s3_presigned_url_secret_key",
        mount_requirement=Secret.MountType.ENV_VAR,
    ),
]


def set_env_vars() -> None:
    """
    Sets environment variables based on Flyte context
    """
    os.environ["KAFKA_USERNAME"] = current_context().secrets.get("impt-kafka-jaas-flyte", "user")
    os.environ["KAFKA_PASSWORD"] = current_context().secrets.get("impt-kafka-jaas-flyte", "password")
    os.environ["SPICEDB_TOKEN"] = current_context().secrets.get("impt-spice-db", "SPICEDB_GRPC_PRESHARED_KEY")
    if os.getenv("S3_CREDENTIALS_PROVIDER") == "local":
        os.environ["S3_ACCESS_KEY"] = current_context().secrets.get("impt-seaweed-fs", "flyte_workflows_access_key")
        os.environ["S3_SECRET_KEY"] = current_context().secrets.get("impt-seaweed-fs", "flyte_workflows_secret_key")
        os.environ["S3_PRESIGNED_URL_ACCESS_KEY"] = current_context().secrets.get(
            "impt-seaweed-fs", "flyte_workflows_s3_presigned_url_access_key"
        )
        os.environ["S3_PRESIGNED_URL_SECRET_KEY"] = current_context().secrets.get(
            "impt-seaweed-fs", "flyte_workflows_s3_presigned_url_secret_key"
        )
    if os.getenv("MONGODB_CREDENTIALS_PROVIDER") == "local":
        os.environ["DATABASE_USERNAME"] = current_context().secrets.get("impt-mongodb", "jobs-mongodb-username")
        os.environ["DATABASE_PASSWORD"] = current_context().secrets.get("impt-mongodb", "jobs-mongodb-password")


def _get_mandatory_env_variable(key: str) -> str:
    """
    Returns environment variable value, throws ValueError if it's not defined
    :param key: environment variable key
    :return str: environment variable value if it's not defined, throws ValueError otherwise
    """
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Environment variable {key} is not set")
    return value


def setup_session_from_env() -> None:
    """
    Makes a session and sets it in the current context variable
    """
    organization_id = ID(_get_mandatory_env_variable("SESSION_ORGANIZATION_ID"))
    workspace_id = ID(_get_mandatory_env_variable("SESSION_WORKSPACE_ID"))
    CTX_SESSION_VAR.set(
        make_session(
            organization_id=organization_id,
            workspace_id=workspace_id,
            source=RequestSource.INTERNAL,
        )
    )


def env_vars(fn):  # noqa: ANN001, ANN201
    """
    Decorator to set task environment variables for MongoDB, Kafka and SpiceDB
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        set_env_vars()
        setup_session_from_env()
        return fn(*args, **kwargs)

    return wrapper


@dataclass
class JobMetadata:
    """Metadata propagated from the job microservice.

    Attributes:
        id: ID of the job
        type: Type of the job
        name: Name of the job (human readable)
        author: ID of the author who created this job
        start_time: Date time when this job was started by the job microservice.
            Sometimes, the job microserivce can submit start_time with None (="null").
            In this case, start_time is assigned with `iai_core.utils.time_utils.now()`.
    """

    id: ID
    type: str
    name: str
    author: ID
    start_time: datetime

    @classmethod
    def from_env_vars(cls) -> "JobMetadata":
        id = os.environ["JOB_METADATA_ID"]
        type = os.environ["JOB_METADATA_TYPE"]
        name = os.environ["JOB_METADATA_NAME"]
        author = os.environ["JOB_METADATA_AUTHOR"]
        start_time = os.environ["JOB_METADATA_START_TIME"]
        return cls(
            id=ID(id),
            type=type,
            name=name,
            author=ID(author),
            start_time=(datetime.fromisoformat(start_time) if start_time != "null" else now()),
        )

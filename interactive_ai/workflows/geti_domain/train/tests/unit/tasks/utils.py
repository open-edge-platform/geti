# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from functools import wraps

TEST_ENV_VARS = {
    "_FSEC_IMPT-MONGODB_JOBS-MONGODB-USERNAME": "username",
    "_FSEC_IMPT-MONGODB_JOBS-MONGODB-PASSWORD": "password",
    "_FSEC_IMPT-KAFKA-JAAS-FLYTE_USER": "username",
    "_FSEC_IMPT-KAFKA-JAAS-FLYTE_PASSWORD": "password",
    "_FSEC_IMPT-SPICE-DB_SPICEDB_GRPC_PRESHARED_KEY": "token",
    "_FSEC_IMPT-SEAWEED-FS_FLYTE_WORKFLOWS_ACCESS_KEY": "access_key",
    "_FSEC_IMPT-SEAWEED-FS_FLYTE_WORKFLOWS_SECRET_KEY": "secret_key",
    "_FSEC_IMPT-SEAWEED-FS_FLYTE_WORKFLOWS_S3_PRESIGNED_URL_ACCESS_KEY": "presigned_url_access_key",
    "_FSEC_IMPT-SEAWEED-FS_FLYTE_WORKFLOWS_S3_PRESIGNED_URL_SECRET_KEY": "presigned_url_secret_key",
    "SESSION_ORGANIZATION_ID": "organization_id",
    "SESSION_WORKSPACE_ID": "workspace_id",
    "S3_HOST": "localhost:8333",
    "S3_CREDENTIALS_PROVIDER": "local",
    "REPORT_RESOURCES_CONSUMPTION": "true",
}


def return_none(*args, **kwargs) -> None:
    return None


def mock_decorator(*args, **kwargs):
    """Decorate by doing nothing."""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)

        return decorated_function

    return decorator

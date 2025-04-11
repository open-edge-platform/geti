# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
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

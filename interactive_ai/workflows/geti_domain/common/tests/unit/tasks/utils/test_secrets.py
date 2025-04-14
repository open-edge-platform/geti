# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
from unittest.mock import MagicMock, call, patch

import pytest
from geti_types import ID, RequestSource

from jobs_common.tasks.utils.secrets import JobMetadata, env_vars, set_env_vars


@pytest.mark.JobsComponent
class TestSecrets:
    @patch("jobs_common.tasks.utils.secrets.current_context")
    def test_set_env_vars(self, mock_current_context) -> None:
        # Arrange
        context = MagicMock()
        secrets = MagicMock()
        secrets_get = MagicMock()

        context.secrets = secrets
        context.secrets.get = secrets_get
        secrets_get.return_value = "secret_value"
        mock_current_context.return_value = context
        os.environ["S3_CREDENTIALS_PROVIDER"] = "local"
        os.environ["MONGODB_CREDENTIALS_PROVIDER"] = "local"
        # Act
        set_env_vars()

        # Assert
        secrets_get.assert_has_calls(
            [
                call("impt-kafka-jaas-flyte", "user"),
                call("impt-kafka-jaas-flyte", "password"),
                call("impt-spice-db", "SPICEDB_GRPC_PRESHARED_KEY"),
                call("impt-seaweed-fs", "flyte_workflows_access_key"),
                call("impt-seaweed-fs", "flyte_workflows_secret_key"),
                call("impt-seaweed-fs", "flyte_workflows_s3_presigned_url_access_key"),
                call("impt-seaweed-fs", "flyte_workflows_s3_presigned_url_secret_key"),
                call("impt-mongodb", "jobs-mongodb-username"),
                call("impt-mongodb", "jobs-mongodb-password"),
            ]
        )
        assert (
            os.environ.get("DATABASE_USERNAME") == "secret_value"
            and os.environ.get("DATABASE_PASSWORD") == "secret_value"
            and os.environ.get("KAFKA_USERNAME") == "secret_value"
            and os.environ.get("KAFKA_PASSWORD") == "secret_value"
            and os.environ.get("SPICEDB_TOKEN") == "secret_value"
        )

    @patch("jobs_common.tasks.utils.secrets.current_context")
    def test_set_env_vars_eks(self, mock_current_context) -> None:
        # Arrange
        context = MagicMock()
        secrets = MagicMock()
        secrets_get = MagicMock()

        context.secrets = secrets
        context.secrets.get = secrets_get
        secrets_get.return_value = "secret_value"
        mock_current_context.return_value = context
        # Act
        set_env_vars()

        # Assert
        secrets_get.assert_has_calls(
            [
                call("impt-kafka-jaas-flyte", "user"),
                call("impt-kafka-jaas-flyte", "password"),
                call("impt-spice-db", "SPICEDB_GRPC_PRESHARED_KEY"),
            ]
        )
        assert (
            os.environ.get("KAFKA_USERNAME") == "secret_value"
            and os.environ.get("KAFKA_PASSWORD") == "secret_value"
            and os.environ.get("SPICEDB_TOKEN") == "secret_value"
        )

    @patch("jobs_common.tasks.utils.secrets.make_session")
    @patch("jobs_common.tasks.utils.secrets.set_env_vars")
    def test_env_vars(self, mock_set_env_vars, mock_make_session) -> None:
        # Arrange
        session_env_vars = {
            "SESSION_ORGANIZATION_ID": "organization_id",
            "SESSION_WORKSPACE_ID": "workspace_id",
        }

        @env_vars
        def test_function():
            pass

        # Act

        with patch.dict(os.environ, session_env_vars):
            test_function()

        # Assert
        mock_set_env_vars.assert_called_once_with()
        mock_make_session.assert_called_once_with(
            organization_id=ID("organization_id"),
            workspace_id=ID("workspace_id"),
            source=RequestSource.INTERNAL,
        )

    def test_job_metadata(self, fxt_job_metadata) -> None:
        # Act
        job_metadata = JobMetadata.from_env_vars()

        # Assert
        assert job_metadata.id == fxt_job_metadata.id
        assert job_metadata.type == fxt_job_metadata.type
        assert job_metadata.name == fxt_job_metadata.name
        assert job_metadata.author == fxt_job_metadata.author
        assert job_metadata.start_time == fxt_job_metadata.start_time

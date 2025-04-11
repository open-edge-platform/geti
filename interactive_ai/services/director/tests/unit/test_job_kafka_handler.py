# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call, patch

import pytest
from tests.unit.mocked_method_helpers import return_none

from communication.kafka_handler import JobKafkaHandler
from service.job_submission.job_creation_helpers import JobType
from service.project_service import ProjectService

from geti_kafka_tools import KafkaRawMessage
from geti_types import ID, ProjectIdentifier
from sc_sdk.entities.model import Model
from sc_sdk.entities.model_storage import ModelStorage
from sc_sdk.repos import AnnotationSceneRepo, ModelRepo, ModelTestResultRepo
from sc_sdk.utils.deletion_helpers import DeletionHelpers

WORKSPACE_ID = "63b183d00000000000000001"


@pytest.fixture
def fxt_consumer_record_maker(fxt_workspace_id):
    def _make_record(value):
        return KafkaRawMessage(
            topic="fxt_consumer_record",
            partition=0,
            offset=0,
            timestamp=int(datetime.now().timestamp()),
            timestamp_type=0,
            key=b"job_id",
            value=value,
            headers=[
                ("organization_id", b"000000000000000000000001"),
                ("workspace_id", WORKSPACE_ID.encode("utf-8")),
                ("source", b"browser"),
            ],
        )

    yield _make_record


@pytest.fixture
def patched_repo():
    with patch.object(AnnotationSceneRepo, "__init__", return_value=None):
        yield

    AnnotationSceneRepo._instances = {}


@pytest.fixture
def fxt_job_kafka_handler():
    with patch.object(JobKafkaHandler, "__init__", new=return_none):
        job_kafka_handler = JobKafkaHandler()
        yield job_kafka_handler


class TestJobKafkaHandler:
    @patch.object(ModelRepo, "get_by_id")
    @patch.object(Model, "get_base_model")
    @patch.object(ModelRepo, "get_optimized_models_by_base_model_id")
    @patch.object(ModelRepo, "update_training_job_duration")
    def test_on_training_finished(
        self,
        mocked_update_job_duration,
        mocked_get_optimized_models,
        mocked_get_base_model,
        mocked_get_model_by_id,
        fxt_model,
        fxt_job_kafka_handler,
        fxt_consumer_record_maker,
    ):
        # Arrange
        job_type = JobType.TRAIN.value
        end_time = datetime.now(tz=timezone.utc)
        start_time = end_time - timedelta(minutes=5)
        project_id = ID("project_id")
        task_id = ID("task_id")
        model_storage_id = ID("model_storage_id")
        model_id = ID("model_id")
        mocked_get_model_by_id.return_value = fxt_model

        MagicMock(spec=ModelStorage)
        mock_base_model = MagicMock(spec=Model)
        mock_optimized_models = [MagicMock(spec=Model) for _ in range(5)]

        mocked_get_base_model.return_value = mock_base_model
        mocked_get_optimized_models.return_value = mock_optimized_models

        # Act
        with patch.object(ProjectService, "unlock") as mock_unlock_project:
            fxt_job_kafka_handler.on_job_finished(
                fxt_consumer_record_maker(
                    {
                        "job_type": job_type,
                        "workspace_id": ID("workspace_id"),
                        "job_payload": {
                            "project_id": project_id,
                            "task_id": task_id,
                        },
                        "job_metadata": {
                            "trained_model": {
                                "model_storage_id": model_storage_id,
                                "model_id": model_id,
                            }
                        },
                        "start_time": str(start_time),
                        "end_time": str(end_time),
                    }
                )
            )

        # Assert
        mock_unlock_project.assert_called_once_with(job_type=job_type, project_id=project_id)
        mocked_get_model_by_id.assert_called_with(model_id)
        mocked_get_base_model.assert_called_with()
        mocked_get_optimized_models.assert_called_with(mock_base_model.id_)
        mocked_update_job_duration.assert_any_call(
            model=mock_base_model,
            training_job_duration=(end_time - start_time).total_seconds(),
        )

    @patch.object(DeletionHelpers, "delete_models_by_base_model_id")
    def test_on_training_cancelled(
        self,
        mock_model_delete,
        fxt_job_kafka_handler,
        fxt_consumer_record_maker,
    ):
        # Arrange
        job_type = JobType.TRAIN.value
        project_id = ID("project_id")
        task_id = ID("task_id")
        model_storage_id = ID("model_storage_id")
        model_id = ID("model_id")
        end_time = datetime.now(tz=timezone.utc)
        start_time = end_time - timedelta(minutes=5)

        # Act
        with patch.object(ProjectService, "unlock") as mock_unlock_project:
            fxt_job_kafka_handler.on_job_cancelled(
                fxt_consumer_record_maker(
                    {
                        "job_type": job_type,
                        "workspace_id": ID("workspace_id"),
                        "job_payload": {
                            "project_id": project_id,
                            "task_id": task_id,
                        },
                        "job_metadata": {
                            "trained_model": {
                                "model_storage_id": model_storage_id,
                                "model_id": model_id,
                            },
                            "task": {
                                "model_template_id": "model_architecture_1",
                            },
                        },
                        "start_time": str(start_time),
                        "cancel_time": str(end_time),
                    }
                )
            )

        # Assert
        mock_unlock_project.assert_called_once_with(job_type=job_type, project_id=project_id)
        mock_model_delete.assert_called_once_with(
            project_id=project_id,
            model_storage_id=model_storage_id,
            base_model_id=model_id,
        )

    @patch.object(DeletionHelpers, "delete_models_by_base_model_id")
    def test_on_training_failed_model_not_activated(
        self,
        mock_model_delete,
        fxt_job_kafka_handler,
        fxt_consumer_record_maker,
    ):
        # Arrange
        job_type = JobType.TRAIN.value
        project_id = ID("project_id")
        task_id = ID("task_id")
        model_storage_id = ID("model_storage_id")
        model_id = ID("model_id")
        end_time = datetime.now(tz=timezone.utc)
        start_time = end_time - timedelta(minutes=5)

        # Act
        with patch.object(ProjectService, "unlock") as mock_unlock_project:
            fxt_job_kafka_handler.on_job_failed(
                fxt_consumer_record_maker(
                    {
                        "job_type": job_type,
                        "workspace_id": ID("workspace_id"),
                        "job_payload": {
                            "project_id": project_id,
                            "task_id": task_id,
                        },
                        "job_metadata": {
                            "trained_model": {
                                "model_storage_id": model_storage_id,
                                "model_id": model_id,
                                "model_activated": False,
                            },
                            "task": {
                                "model_template_id": "model_architecture_1",
                            },
                        },
                        "start_time": str(start_time),
                        "end_time": str(end_time),
                    }
                )
            )

        # Assert
        mock_unlock_project.assert_called_once_with(job_type=job_type, project_id=project_id)
        mock_model_delete.assert_called_once_with(
            project_id=project_id,
            model_storage_id=model_storage_id,
            base_model_id=model_id,
        )

    @patch.dict(os.environ, {"KEEP_FAILED_MODELS": "true"})
    @patch.object(DeletionHelpers, "delete_models_by_base_model_id")
    def test_on_training_failed_model_not_activated_keep_models(
        self,
        mock_model_delete,
        fxt_job_kafka_handler,
        fxt_consumer_record_maker,
    ):
        # Arrange
        job_type = JobType.TRAIN.value
        project_id = ID("project_id")
        task_id = ID("task_id")
        model_storage_id = ID("model_storage_id")
        model_id = ID("model_id")
        end_time = datetime.now(tz=timezone.utc)
        start_time = end_time - timedelta(minutes=5)

        # Act
        with patch.object(ProjectService, "unlock") as mock_unlock_project:
            fxt_job_kafka_handler.on_job_failed(
                fxt_consumer_record_maker(
                    {
                        "job_type": job_type,
                        "workspace_id": ID("workspace_id"),
                        "job_payload": {
                            "project_id": project_id,
                            "task_id": task_id,
                        },
                        "job_metadata": {
                            "trained_model": {
                                "model_storage_id": model_storage_id,
                                "model_id": model_id,
                                "model_activated": False,
                            },
                            "task": {
                                "model_template_id": "model_architecture_1",
                            },
                        },
                        "start_time": str(start_time),
                        "end_time": str(end_time),
                    }
                )
            )

        # Assert
        mock_unlock_project.assert_called_once_with(job_type=job_type, project_id=project_id)
        mock_model_delete.assert_not_called()

    @patch.object(DeletionHelpers, "delete_models_by_base_model_id")
    def test_on_training_failed_model_activated(
        self,
        mock_model_delete,
        fxt_job_kafka_handler,
        fxt_consumer_record_maker,
    ):
        # Arrange
        job_type = JobType.TRAIN.value
        project_id = ID("project_id")
        task_id = ID("task_id")
        model_storage_id = ID("model_storage_id")
        model_id = ID("model_id")
        end_time = datetime.now(tz=timezone.utc)
        start_time = end_time - timedelta(minutes=5)

        # Act
        with patch.object(ProjectService, "unlock") as mock_unlock_project:
            fxt_job_kafka_handler.on_job_failed(
                fxt_consumer_record_maker(
                    {
                        "job_type": job_type,
                        "workspace_id": ID("workspace_id"),
                        "job_payload": {
                            "project_id": project_id,
                            "task_id": task_id,
                        },
                        "job_metadata": {
                            "trained_model": {
                                "model_storage_id": model_storage_id,
                                "model_id": model_id,
                                "model_activated": True,
                            },
                            "task": {
                                "model_template_id": "model_architecture_1",
                            },
                        },
                        "start_time": str(start_time),
                        "end_time": str(end_time),
                    }
                )
            )

        # Assert
        mock_unlock_project.assert_called_once_with(job_type=job_type, project_id=project_id)
        mock_model_delete.assert_not_called()

    def test_on_model_test_job_failed(
        self,
        fxt_model_test_result,
        fxt_job_kafka_handler,
        fxt_consumer_record_maker,
    ):
        # Arrange
        job_type = JobType.MODEL_TEST.value
        project_id = ID("project_id")
        model_test_result_id = ID("model_test_result_id")

        # Act
        with (
            patch.object(
                ModelTestResultRepo, "get_by_id", return_value=fxt_model_test_result
            ) as mock_model_test_result,
            patch.object(
                ModelTestResultRepo,
                "save",
            ) as mock_save,
            patch.object(ProjectService, "unlock") as mock_unlock_project,
        ):
            fxt_job_kafka_handler.on_job_failed(
                fxt_consumer_record_maker(
                    {
                        "job_type": job_type,
                        "workspace_id": ID("workspace_id"),
                        "job_payload": {
                            "project_id": project_id,
                            "model_test_result_id": model_test_result_id,
                        },
                        "job_metadata": {},
                    }
                )
            )

        # Assert
        mock_unlock_project(job_type=job_type, project_id=project_id)
        mock_model_test_result.assert_called_with(model_test_result_id)
        mock_save.assert_called_with(fxt_model_test_result)

    def test_on_model_test_job_cancelled(
        self,
        fxt_model_test_result,
        fxt_job_kafka_handler,
        fxt_consumer_record_maker,
    ):
        # Arrange
        project_identifier = ProjectIdentifier(
            workspace_id=ID(WORKSPACE_ID),
            project_id=fxt_model_test_result.project_identifier.project_id,
        )
        job_type = JobType.MODEL_TEST.value
        model_test_result_id = ID("model_test_result_id")

        # Act
        with (
            patch.object(
                ModelTestResultRepo, "get_by_id", return_value=fxt_model_test_result
            ) as mock_model_test_result,
            patch.object(
                DeletionHelpers,
                "delete_model_test_result",
            ) as mock_delete,
            patch.object(ProjectService, "unlock") as mock_unlock_project,
        ):
            fxt_job_kafka_handler.on_job_cancelled(
                fxt_consumer_record_maker(
                    {
                        "job_type": job_type,
                        "workspace_id": project_identifier.workspace_id,
                        "job_payload": {
                            "project_id": project_identifier.project_id,
                            "model_test_result_id": model_test_result_id,
                        },
                        "job_metadata": {},
                    }
                )
            )

        # Assert
        mock_unlock_project(job_type=job_type, project_id=project_identifier.project_id)
        mock_model_test_result.assert_called_with(model_test_result_id)
        mock_delete.assert_called_with(project_identifier=project_identifier, model_test_result=fxt_model_test_result)

    def test_on_optimize_job_cancelled(
        self,
        fxt_job_kafka_handler,
        fxt_consumer_record_maker,
    ):
        # Arrange
        job_type = JobType.OPTIMIZE_POT.value
        workspace_id = ID("workspace_id")
        project_id = ID("project_id")
        model_storage_id = ID("model_storage_id")
        mock_model = MagicMock()
        mock_model.id_ = ID("optimized_model_id")
        mock_model.previous_revision_id = ID("previous_revision_id")

        # Act
        with (
            patch.object(
                ModelRepo,
                "__init__",
                new=return_none,
            ),
            patch.object(ModelRepo, "get_by_id", return_value=mock_model) as mock_get_model_by_id,
            patch.object(ModelRepo, "delete_by_id") as mock_delete,
            patch.object(ProjectService, "unlock") as mock_unlock_project,
        ):
            fxt_job_kafka_handler.on_job_cancelled(
                fxt_consumer_record_maker(
                    {
                        "job_type": job_type,
                        "workspace_id": workspace_id,
                        "job_payload": {
                            "project_id": project_id,
                        },
                        "job_metadata": {
                            "model_storage_id": model_storage_id,
                            "optimized_model_id": mock_model.id_,
                        },
                    }
                )
            )

        # Assert
        mock_unlock_project(job_type=job_type, project_id=project_id)
        mock_get_model_by_id.assert_called_once_with(mock_model.id_)
        mock_delete.assert_has_calls([call(mock_model.previous_revision_id), call(mock_model.id_)])

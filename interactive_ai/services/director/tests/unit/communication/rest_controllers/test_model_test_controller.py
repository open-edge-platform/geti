# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from testfixtures import compare

from communication.controllers.model_test_controller import ModelTestController
from communication.exceptions import (
    DatasetStorageHasNoAnnotationsException,
    DeprecatedModelTestException,
    UnsupportedFormatForModelTestingException,
)
from communication.views.job_rest_views import JobRestViews
from communication.views.model_test_result_rest_views import ModelTestResultRestViews
from communication.views.prediction_rest_views import PredictionRESTViews
from service.job_submission import ModelTestingJobSubmitter
from service.label_schema_service import LabelSchemaService

from geti_fastapi_tools.responses import success_response_rest
from geti_types import ID
from grpc_interfaces.job_submission.client import CommunicationError
from iai_core.entities.model import ModelFormat
from iai_core.entities.project import Project
from iai_core.repos import (
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    DatasetRepo,
    DatasetStorageRepo,
    ModelRepo,
    ModelTestResultRepo,
    ProjectRepo,
)
from iai_core.utils.deletion_helpers import DeletionHelpers

if TYPE_CHECKING:
    from iai_core.entities.model_test_result import ModelTestResult

DUMMY_USER = ID("dummy_user")


class TestModelTestRESTController:
    def test_get_all_model_test_results(
        self,
        fxt_project,
        fxt_model_test_result,
        fxt_model_test_results_rest,
    ) -> None:
        # Arrange
        workspace_id = fxt_project.workspace_id
        project_id = fxt_project.id_
        model_test_results = [fxt_model_test_result, fxt_model_test_result]
        dummy_dataset_counts = {
            "n_images": 1,
            "n_frames": 2,
            "n_samples": 3,
        }
        dataset_storages = fxt_model_test_result.get_dataset_storages()
        datasets_counts = {dataset_storage.id_: dummy_dataset_counts for dataset_storage in dataset_storages}
        datasets_counts_per_model_test = {fxt_model_test_result.id_: datasets_counts}

        # Act
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project),
            patch.object(
                ModelTestResultRepo,
                "get_all",
                return_value=model_test_results,
            ) as mock_get_model_test_results,
            patch.object(
                ModelTestResultRestViews,
                "model_test_results_to_rest",
                return_value=fxt_model_test_results_rest,
            ) as mock_model_results_rest_view,
            patch.object(
                DatasetRepo, "count_per_media_type", return_value=dummy_dataset_counts
            ) as mock_get_counts_in_dataset,
        ):
            result = ModelTestController().get_all_model_test_results(workspace_id=workspace_id, project_id=project_id)

        # Assert
        mock_get_counts_in_dataset.assert_called()
        mock_get_model_test_results.assert_called_once_with()
        mock_model_results_rest_view.assert_called_once_with(
            model_test_results=model_test_results,
            datasets_counts_per_model_test=datasets_counts_per_model_test,
        )
        compare(result, fxt_model_test_results_rest, ignore_eq=True)

    def test_get_model_test_result(
        self,
        fxt_project,
        fxt_model_test_result,
        fxt_model_test_result_rest,
    ) -> None:
        # Arrange
        project = fxt_project
        workspace_id = project.workspace_id
        project_id = project.id_
        model_test_result_id = fxt_model_test_result.id_
        dummy_dataset_counts = {
            "n_images": 1,
            "n_frames": 2,
            "n_samples": 3,
        }
        dataset_storages = fxt_model_test_result.get_dataset_storages()
        datasets_counts = {dataset_storage.id_: dummy_dataset_counts for dataset_storage in dataset_storages}

        # Act
        with (
            patch.object(
                ModelTestResultRepo,
                "get_by_id",
                return_value=fxt_model_test_result,
            ) as mock_get_model_test_result,
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=project,
            ) as mock_get_project_by_id,
            patch.object(
                ModelTestResultRestViews,
                "model_test_result_to_rest",
                return_value=fxt_model_test_result_rest,
            ) as mock_model_result_rest_view,
            patch.object(
                DatasetRepo, "count_per_media_type", return_value=dummy_dataset_counts
            ) as mock_get_counts_in_dataset,
        ):
            result = ModelTestController().get_model_test_result(
                workspace_id=workspace_id,
                project_id=project_id,
                model_test_result_id=model_test_result_id,
            )

        # Assert
        mock_get_counts_in_dataset.assert_called()
        mock_get_model_test_result.assert_called_once_with(model_test_result_id)
        mock_get_project_by_id.assert_called_once_with(project_id)
        mock_model_result_rest_view.assert_called_once_with(
            model_test_result=fxt_model_test_result,
            datasets_counts=datasets_counts,
        )
        compare(result, fxt_model_test_result_rest, ignore_eq=True)

    def test_get_model_test_result_anomaly_reduction(
        self,
        fxt_project_with_anomaly_classification_task,
        fxt_model_test_result_with_accuracy_metric,
        fxt_model_test_result_with_accuracy_metric_rest,
    ) -> None:
        # Arrange
        project = fxt_project_with_anomaly_classification_task
        workspace_id = project.workspace_id
        project_id = project.id_
        model_test_result_id = fxt_model_test_result_with_accuracy_metric.id_
        dummy_dataset_counts = {
            "n_images": 1,
            "n_frames": 2,
            "n_samples": 3,
        }
        dataset_storages = fxt_model_test_result_with_accuracy_metric.get_dataset_storages()
        datasets_counts = {dataset_storage.id_: dummy_dataset_counts for dataset_storage in dataset_storages}

        # Act
        with (
            patch.object(
                ModelTestResultRepo,
                "get_by_id",
                return_value=fxt_model_test_result_with_accuracy_metric,
            ) as mock_get_model_test_result,
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=project,
            ) as mock_get_project_by_id,
            patch.object(
                ModelTestResultRestViews,
                "model_test_result_to_rest",
                return_value=fxt_model_test_result_with_accuracy_metric_rest,
            ) as mock_model_result_rest_view,
            patch.object(
                DatasetRepo, "count_per_media_type", return_value=dummy_dataset_counts
            ) as mock_get_counts_in_dataset,
        ):
            result = ModelTestController().get_model_test_result(
                workspace_id=workspace_id,
                project_id=project_id,
                model_test_result_id=model_test_result_id,
            )

        # Assert
        mock_get_counts_in_dataset.assert_called()
        mock_get_model_test_result.assert_called_once_with(model_test_result_id)
        mock_get_project_by_id.assert_called_once_with(project_id)
        mock_model_result_rest_view.assert_called_once_with(
            model_test_result=fxt_model_test_result_with_accuracy_metric,
            datasets_counts=datasets_counts,
        )
        compare(result, fxt_model_test_result_with_accuracy_metric_rest, ignore_eq=True)

    def test_get_model_test_result_anomaly_reduction_deprecated(
        self,
        fxt_project_with_anomaly_detection_task,
        fxt_model_test_result,
    ) -> None:
        # Arrange
        project = fxt_project_with_anomaly_detection_task
        workspace_id = project.workspace_id
        project_id = project.id_
        model_test_result_id = fxt_model_test_result.id_

        # Act
        with (
            patch.object(
                ModelTestResultRepo,
                "get_by_id",
                return_value=fxt_model_test_result,
            ) as mock_get_model_test_result,
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=project,
            ) as mock_get_project_by_id,
            pytest.raises(DeprecatedModelTestException),
        ):
            _ = ModelTestController().get_model_test_result(
                workspace_id=workspace_id,
                project_id=project_id,
                model_test_result_id=model_test_result_id,
            )

        # Assert
        mock_get_model_test_result.assert_called_once_with(model_test_result_id)
        mock_get_project_by_id.assert_called_once_with(project_id)

    def test_delete_model_test_result(self, fxt_project, fxt_model_test_result) -> None:
        # Arrange
        workspace_id = fxt_project.workspace_id
        project_id = fxt_project.id_
        model_test_result_id = fxt_model_test_result.id_

        # Act
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project),
            patch.object(ModelTestResultRepo, "get_by_id", return_value=fxt_model_test_result),
            patch.object(
                DeletionHelpers,
                "delete_model_test_result",
            ) as mock_delete_model_result,
        ):
            result = ModelTestController().delete_model_test_result(
                workspace_id=workspace_id,
                project_id=project_id,
                model_test_result_id=model_test_result_id,
            )

        # Assert
        mock_delete_model_result.assert_called_once_with(
            project_identifier=fxt_project.identifier,
            model_test_result=fxt_model_test_result,
        )
        compare(result, success_response_rest(), ignore_eq=True)

    def test_create_and_submit_job(
        self,
        fxt_project,
        fxt_model,
        fxt_mongo_id,
        fxt_model_test_result,
        fxt_ote_id,
    ) -> None:
        # Arrange
        project = fxt_project
        workspace_id = project.workspace_id
        project_id = project.id_
        model_id = fxt_mongo_id(1)
        dataset_storage = project.get_training_dataset_storage()
        dataset_storage_id = dataset_storage.id_
        dummy_data = {
            "name": "dummy_data",
            "model_group_id": fxt_mongo_id(0),
            "model_id": model_id,
            "dataset_ids": [dataset_storage_id],
        }

        model_test_result: ModelTestResult | None = None

        def mock_save(instance):
            nonlocal model_test_result
            model_test_result = instance

        # Act
        with (
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=project,
            ) as mock_get_project,
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model) as mock_get_model,
            patch.object(
                DatasetStorageRepo,
                "get_by_id",
                return_value=dataset_storage,
            ) as mock_get_dataset_storage,
            patch.object(
                AnnotationSceneStateRepo,
                "count_images_state_for_task",
                return_value=1,
            ) as mock_count_images,
            patch.object(ModelTestingJobSubmitter, "execute", return_value=fxt_ote_id()) as mock_testing_job_submit,
            patch.object(
                JobRestViews,
                "job_id_to_rest",
                return_value={},
            ) as mock_job_rest_view,
            patch.object(
                Project,
                "get_trainable_task_node_by_id",
                return_value=project.tasks[-1],
            ),
            patch.object(ModelTestResultRepo, "save", side_effect=mock_save),
        ):
            ModelTestController().create_and_submit_job(
                workspace_id=workspace_id,
                project_id=project_id,
                data=dummy_data,
                author=DUMMY_USER,
            )

        # Assert
        assert mock_get_project.called_once_with(project_id)
        assert mock_get_model.called_once()
        assert mock_get_dataset_storage.called_once_with(dataset_storage_id)
        assert mock_count_images.called_once()
        assert mock_testing_job_submit.called_once_with(
            model_test_result=fxt_model_test_result,
            project=fxt_project,
            author=DUMMY_USER,
        )
        assert model_test_result is not None
        assert model_test_result.job_id == fxt_ote_id()
        assert mock_job_rest_view.called_once_with(job_ids=[fxt_ote_id()])

    def test_create_and_submit_job_anomaly_task_no_metric(
        self,
        fxt_project_with_anomaly_detection_task,
        fxt_model,
        fxt_model_storage_anomaly_detection,
        fxt_mongo_id,
        fxt_model_test_result,
        fxt_ote_id,
    ) -> None:
        # Arrange
        project = fxt_project_with_anomaly_detection_task
        model = fxt_model
        model.model_storage = fxt_model_storage_anomaly_detection
        workspace_id = project.workspace_id
        project_id = project.id_
        dataset_storage = project.get_training_dataset_storage()
        dataset_storage_id = dataset_storage.id_

        # Testing when the REST payload data does not contain any metric
        dummy_data = {
            "name": "dummy_data",
            "model_group_id": fxt_mongo_id(0),
            "model_id": str(model.id_),
            "dataset_ids": [dataset_storage_id],
        }

        model_test_result: ModelTestResult | None = None

        def mock_save(instance):
            nonlocal model_test_result
            model_test_result = instance

        # Act and Assert
        with (
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=project,
            ) as mock_get_project,
            patch.object(ModelRepo, "get_by_id", return_value=model) as mock_get_model,
            patch.object(
                DatasetStorageRepo,
                "get_by_id",
                return_value=dataset_storage,
            ) as mock_get_dataset_storage,
            patch.object(
                AnnotationSceneStateRepo,
                "count_images_state_for_task",
                return_value=1,
            ) as mock_count_images,
            patch.object(ModelTestingJobSubmitter, "execute", return_value=fxt_ote_id()) as mock_testing_job_submit,
            patch.object(
                JobRestViews,
                "job_id_to_rest",
                return_value={},
            ) as mock_job_rest_view,
            patch.object(
                Project,
                "get_trainable_task_node_by_id",
                return_value=project.tasks[-1],
            ),
            patch.object(ModelTestResultRepo, "save", side_effect=mock_save),
        ):
            ModelTestController().create_and_submit_job(
                workspace_id=workspace_id,
                project_id=project_id,
                data=dummy_data,
                author=DUMMY_USER,
            )

        # Assert
        assert mock_get_project.called_once_with(project_id)
        assert mock_get_model.called_once()
        assert mock_get_dataset_storage.called_once_with(dataset_storage_id)
        assert mock_count_images.called_once()
        assert mock_testing_job_submit.called_once_with(
            model_test_result=fxt_model_test_result,
            project=fxt_project_with_anomaly_detection_task,
            author=DUMMY_USER,
        )
        assert model_test_result is not None
        assert model_test_result.job_id == fxt_ote_id()
        assert mock_job_rest_view.called_once_with(job_ids=[fxt_ote_id()])

    def test_create_and_submit_job_with_no_annotations(
        self, fxt_project, fxt_model, fxt_mongo_id, fxt_dataset_task
    ) -> None:
        # Arrange
        workspace_id = fxt_project.workspace_id
        project_id = fxt_project.id_
        dataset_storage = fxt_project.get_training_dataset_storage()
        dataset_storage_id = dataset_storage.id_

        dummy_data = {
            "name": "dummy_data",
            "model_group_id": fxt_mongo_id(0),
            "model_id": str(fxt_model.id_),
            "dataset_ids": [dataset_storage_id],
        }

        # Act and Assert
        with (
            pytest.raises(DatasetStorageHasNoAnnotationsException),
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=fxt_project,
            ) as mock_get_project,
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model) as mock_get_model,
            patch.object(Project, "get_trainable_task_node_by_id", return_value=fxt_dataset_task),
            patch.object(
                DatasetStorageRepo,
                "get_by_id",
                return_value=dataset_storage,
            ) as mock_get_dataset_storage,
        ):
            ModelTestController().create_and_submit_job(
                workspace_id=workspace_id,
                project_id=project_id,
                data=dummy_data,
                author=DUMMY_USER,
            )

        # Assert
        assert mock_get_project.called_once_with(project_id)
        assert mock_get_model.called_once()
        assert mock_get_dataset_storage.called_once_with(fxt_project, dataset_storage_id)

    @pytest.mark.parametrize("model_format", [ModelFormat.BASE_FRAMEWORK, ModelFormat.ONNX])
    def test_create_and_submit_unsupported_model_format(
        self,
        model_format,
        fxt_project,
        fxt_model,
        fxt_mongo_id,
    ) -> None:
        # Arrange
        fxt_model.model_format = model_format
        workspace_id = fxt_project.identifier.workspace_id
        project_id = fxt_project.id_
        dataset_storage = fxt_project.get_training_dataset_storage()
        dataset_storage_id = dataset_storage.id_

        dummy_data = {
            "name": "dummy_data",
            "model_group_id": fxt_mongo_id(0),
            "model_id": str(fxt_model.id_),
            "dataset_ids": [dataset_storage_id],
        }

        # Act and Assert
        with (
            pytest.raises(UnsupportedFormatForModelTestingException),
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=fxt_project,
            ) as mock_get_project,
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model) as mock_get_model,
            patch.object(
                DatasetStorageRepo,
                "get_by_id",
                return_value=dataset_storage,
            ) as mock_get_dataset_storage,
        ):
            ModelTestController().create_and_submit_job(
                workspace_id=workspace_id,
                project_id=project_id,
                data=dummy_data,
                author=DUMMY_USER,
            )

        # Assert
        assert mock_get_project.called_once_with(project_id)
        assert mock_get_model.called_once()
        assert mock_get_dataset_storage.called_once_with(fxt_project, dataset_storage_id)

    def test_create_and_submit_job_grpc_error(
        self,
        fxt_project,
        fxt_model,
        fxt_mongo_id,
        fxt_model_test_result,
        fxt_ote_id,
    ) -> None:
        # Arrange
        project = fxt_project
        workspace_id = project.workspace_id
        project_id = project.id_
        model_id = fxt_mongo_id(1)
        dataset_storage = project.get_training_dataset_storage()
        dataset_storage_id = dataset_storage.id_
        dummy_data = {
            "name": "dummy_data",
            "model_group_id": fxt_mongo_id(0),
            "model_id": model_id,
            "dataset_ids": [dataset_storage_id],
        }

        model_test_result: ModelTestResult | None = None

        def mock_save(instance):
            nonlocal model_test_result
            model_test_result = instance

        # Act
        with (
            pytest.raises(CommunicationError),
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=project,
            ) as mock_get_project,
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model) as mock_get_model,
            patch.object(
                DatasetStorageRepo,
                "get_by_id",
                return_value=dataset_storage,
            ) as mock_get_dataset_storage,
            patch.object(
                AnnotationSceneStateRepo,
                "count_images_state_for_task",
                return_value=1,
            ) as mock_count_images,
            patch.object(
                ModelTestingJobSubmitter, "execute", side_effect=CommunicationError
            ) as mock_testing_job_submit,
            patch.object(
                JobRestViews,
                "job_id_to_rest",
                return_value={},
            ) as mock_job_rest_view,
            patch.object(
                Project,
                "get_trainable_task_node_by_id",
                return_value=project.tasks[-1],
            ),
            patch.object(ModelTestResultRepo, "save", side_effect=mock_save),
            patch.object(DeletionHelpers, "delete_model_test_result") as mock_delete_model_test_result,
        ):
            ModelTestController().create_and_submit_job(
                workspace_id=workspace_id,
                project_id=project_id,
                data=dummy_data,
                author=DUMMY_USER,
            )

        # Assert
        assert mock_get_project.called_once_with(workspace_id=workspace_id, project_id=project_id)
        assert mock_get_model.called_once()
        assert mock_get_dataset_storage.called_once_with(project, dataset_storage_id)
        assert mock_count_images.called_once()
        assert mock_testing_job_submit.called_once()
        assert mock_job_rest_view.not_called()
        assert mock_delete_model_test_result.called_once_with(
            project=project, model_test_result_id=fxt_model_test_result.id_
        )

    def test_get_prediction(
        self,
        fxt_project,
        fxt_model_test_result,
        fxt_annotation_scene,
        fxt_annotation_scene_rest_response,
        fxt_label_schema,
        fxt_model_test_result_rest,
    ) -> None:
        # Arrange
        project = fxt_project
        workspace_id = project.workspace_id
        project_id = project.id_
        model_test_result_id = fxt_model_test_result.id_

        # Act
        with (
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=project,
            ) as mock_get_project_by_id,
            patch.object(
                ModelTestResultRepo,
                "get_by_id",
                return_value=fxt_model_test_result,
            ) as mock_get_model_test_result,
            patch.object(
                AnnotationSceneRepo,
                "__init__",
                return_value=None,
            ),
            patch.object(
                AnnotationSceneRepo,
                "get_by_id",
                return_value=fxt_annotation_scene,
            ) as mock_annotation_scene_repo,
            patch.object(
                LabelSchemaService,
                "get_latest_label_schema_for_project",
                return_value=fxt_label_schema,
            ) as mock_get_latest_label_schema,
            patch.object(
                PredictionRESTViews,
                "media_2d_prediction_to_rest",
                return_value=fxt_annotation_scene_rest_response,
            ) as mock_prediction_to_rest,
        ):
            result = ModelTestController().get_model_test_prediction(
                workspace_id=workspace_id,
                project_id=project_id,
                model_test_result_id=model_test_result_id,
                prediction_id=fxt_annotation_scene.id_,
            )

        # Assert
        mock_get_project_by_id.assert_called_once_with(project_id)
        mock_get_model_test_result.assert_called_once_with(model_test_result_id)
        mock_annotation_scene_repo.assert_called_once_with(fxt_annotation_scene.id_)
        mock_get_latest_label_schema.assert_called_once_with(project.identifier)
        mock_prediction_to_rest.assert_called_once_with(
            prediction=fxt_annotation_scene,
            project=project,
            label_schema=fxt_label_schema,
            update_response_for_inference_gateway=True,
        )
        compare(result, fxt_annotation_scene_rest_response, ignore_eq=True)

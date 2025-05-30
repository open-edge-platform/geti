# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the ModelTestController"""

import logging
from typing import Any

from communication.data_validator import ModelTestRestValidator
from communication.exceptions import (
    DatasetStorageHasNoAnnotationsException,
    DeprecatedModelTestException,
    ModelTestResultNotFoundException,
    PredictionNotFoundException,
    PurgedModelException,
    UnsupportedFormatForModelTestingException,
)
from communication.jobs_client import JobsClient
from communication.views.job_rest_views import JobRestViews
from communication.views.model_test_result_rest_views import ModelTestResultRestViews
from communication.views.prediction_rest_views import PredictionRESTViews
from service.job_submission import ModelTestingJobSubmitter
from service.label_schema_service import LabelSchemaService

from geti_fastapi_tools.exceptions import (
    DatasetStorageNotFoundException,
    ModelNotFoundException,
    ProjectNotFoundException,
)
from geti_fastapi_tools.responses import success_response_rest
from geti_telemetry_tools import unified_tracing
from geti_types import ID, DatasetStorageIdentifier
from grpc_interfaces.job_submission.client import CommunicationError
from iai_core.entities.annotation import NullAnnotationScene
from iai_core.entities.annotation_scene_state import AnnotationState
from iai_core.entities.dataset_storage import NullDatasetStorage
from iai_core.entities.model import Model, ModelFormat, NullModel
from iai_core.entities.model_storage import ModelStorageIdentifier
from iai_core.entities.model_test_result import ModelTestResult, NullModelTestResult
from iai_core.entities.project import NullProject
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

logger = logging.getLogger(__name__)


class ModelTestController:
    """
    Controller for model testing
    """

    @staticmethod
    @unified_tracing
    def get_all_model_test_results(workspace_id: ID, project_id: ID) -> dict[str, Any]:
        """
        Get all model test results REST view

        :param workspace_id: Workspace id
        :param project_id: Project id
        :return: REST representation of list of model test results in project
        """
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)

        model_test_results = list(ModelTestResultRepo(project.identifier).get_all())
        # Count the number of media per type in each model test
        datasets_counts_per_model_test = {}
        for model_test_result in model_test_results:
            datasets_counts: dict[ID, dict] = {}
            if model_test_result.ground_truth_dataset_id is not None:
                for dataset_storage in model_test_result.get_dataset_storages():
                    dataset_repo = DatasetRepo(dataset_storage.identifier)
                    gt_dataset_id = model_test_result.ground_truth_dataset_id
                    counts_per_type = dataset_repo.count_per_media_type(gt_dataset_id)
                    datasets_counts[dataset_storage.id_] = counts_per_type
            datasets_counts_per_model_test[model_test_result.id_] = datasets_counts

        return ModelTestResultRestViews.model_test_results_to_rest(
            model_test_results=model_test_results,
            datasets_counts_per_model_test=datasets_counts_per_model_test,
        )

    @staticmethod
    @unified_tracing
    def get_model_test_result(workspace_id: ID, project_id: ID, model_test_result_id: ID) -> dict[str, Any]:
        """
        Get model test result REST view

        :param workspace_id: Workspace id
        :param project_id: Project id
        :param model_test_result_id: Model test result id
        :return: REST representation of model test result in project with id
        """
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)
        model_test_result = ModelTestResultRepo(project.identifier).get_by_id(model_test_result_id)
        if isinstance(model_test_result, NullModelTestResult):
            raise ModelTestResultNotFoundException(model_test_result_id)

        is_anomaly_task = [node for node in project.get_trainable_task_nodes() if node.task_properties.is_anomaly]
        is_local_test = [score for score in model_test_result.performance.scores if score.name != "Accuracy"]
        if is_anomaly_task and is_local_test:
            raise DeprecatedModelTestException(model_test_id=model_test_result_id)

        # Count the number of media per type in each dataset storage of the model test
        datasets_counts: dict[ID, dict] = {}
        if model_test_result.ground_truth_dataset_id is not None:
            for dataset_storage in model_test_result.get_dataset_storages():
                dataset_repo = DatasetRepo(dataset_storage.identifier)
                gt_dataset_id = model_test_result.ground_truth_dataset_id
                counts_per_type = dataset_repo.count_per_media_type(gt_dataset_id)
                datasets_counts[dataset_storage.id_] = counts_per_type

        return ModelTestResultRestViews.model_test_result_to_rest(
            model_test_result=model_test_result, datasets_counts=datasets_counts
        )

    @staticmethod
    @unified_tracing
    def delete_model_test_result(workspace_id: ID, project_id: ID, model_test_result_id: ID) -> dict[str, Any]:
        """
        Delete all the information relative to a model test result

        :param workspace_id: ID of the workspace containing the project
        :param project_id: ID of the project where the test was performed
        :param model_test_result_id: ID of the test to delete
        :return: Success or failure REST response
        """
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)
        model_test_result = ModelTestResultRepo(project.identifier).get_by_id(model_test_result_id)
        DeletionHelpers.delete_model_test_result(
            project_identifier=project.identifier, model_test_result=model_test_result
        )
        return success_response_rest()

    @unified_tracing
    def create_and_submit_job(
        self,
        workspace_id: ID,
        project_id: ID,
        data: dict,
        author: ID,
    ) -> dict[str, Any]:
        """
        Create and submit model testing job

        :param workspace_id: ID of the workspace containing the project
        :param project_id: ID of the project where to start the job
        :param data: Dict containing the info relative to the job to start
        :param author: ID of the user submitting the job
        :return: REST representation of the job
        """
        ModelTestRestValidator().validate_model_test_params(data)
        name = data["name"]
        model_storage_id = ID(data["model_group_id"])
        model_id = ID(data["model_id"])
        dataset_storage_id = ID(data["dataset_ids"][0])
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
        )
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)
        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            model_storage_id=model_storage_id,
        )
        model = ModelRepo(model_storage_identifier).get_by_id(model_id)
        if isinstance(model, NullModel):
            raise ModelNotFoundException(model_id=model_id)
        self._validate_model(model=model)
        task_node = project.get_trainable_task_node_by_id(model.model_storage.task_node_id)
        if task_node is None:
            raise Exception(f"Task node {model.model_storage.task_node_id} not found in project {project_id}")

        dataset_storage = DatasetStorageRepo(project.identifier).get_by_id(dataset_storage_id)
        if isinstance(dataset_storage, NullDatasetStorage):
            raise DatasetStorageNotFoundException(dataset_storage_id)
        ann_scene_state_repo = AnnotationSceneStateRepo(dataset_storage_identifier)

        annotation_states = [
            AnnotationState.ANNOTATED,
            AnnotationState.PARTIALLY_ANNOTATED,
        ]
        annotated_image_count = ann_scene_state_repo.count_images_state_for_task(annotation_states, task_node.id_)
        annotated_video_frame_count = ann_scene_state_repo.count_video_frames_state_for_task(
            annotation_states, task_node.id_
        )
        if annotated_image_count == 0 and annotated_video_frame_count == 0:
            raise DatasetStorageHasNoAnnotationsException(dataset_name=dataset_storage.name)

        model_test_result = ModelTestResult(
            id_=ModelTestResultRepo.generate_id(),
            name=name,
            project_identifier=project.identifier,
            model_storage_id=model.model_storage.id_,
            model_id=model.id_,
            dataset_storage_ids=[dataset_storage.id_],
        )
        ModelTestResultRepo(project.identifier).save(model_test_result)

        job_submitter = ModelTestingJobSubmitter(JobsClient().jobs_client)
        try:
            job_id = job_submitter.execute(
                model_test_result=model_test_result,
                project=project,
                author=author,
            )
            model_test_result.job_id = job_id
            ModelTestResultRepo(project.identifier).save(model_test_result)
        except CommunicationError as ex:
            logger.error(
                f"Error occurred while submitting model test job, deleting model test result {model_test_result.id_}"
            )
            DeletionHelpers.delete_model_test_result(project.identifier, model_test_result)
            raise ex
        return JobRestViews.job_id_to_rest(job_id=job_id)

    @unified_tracing
    def get_model_test_prediction(
        self,
        workspace_id: ID,
        project_id: ID,
        model_test_result_id: ID,
        prediction_id: ID,
    ) -> dict[str, Any]:
        """
        Get a prediction and result media by prediction id

        :param workspace_id: ID of the workspace the project belongs to
        :param project_id: ID of project the model test result belongs to
        :param model_test_result_id: ID of the model test result
        :param prediction_id: ID of requested prediction
        :return: REST View
        """
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)
        model_test_result = ModelTestResultRepo(project.identifier).get_by_id(model_test_result_id)
        if isinstance(model_test_result, NullModelTestResult):
            raise ModelTestResultNotFoundException(model_test_result_id)
        dataset_storage = model_test_result.get_dataset_storages()[0]
        annotation_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
        prediction = annotation_scene_repo.get_by_id(prediction_id)
        if isinstance(prediction, NullAnnotationScene):
            raise PredictionNotFoundException(
                f"The requested prediction could not be found in project {project.name} "
                f"and dataset {dataset_storage.name}. "
                f"Project ID: `{project_id}`, "
                f"ModelTestResult ID: `{model_test_result_id}`, "
                f"Prediction ID: `{prediction_id}`."
            )

        label_schema = LabelSchemaService.get_latest_label_schema_for_project(project.identifier)

        return PredictionRESTViews.media_2d_prediction_to_rest(
            prediction=prediction,
            project=project,
            label_schema=label_schema,
            update_response_for_inference_gateway=True,
        )

    @staticmethod
    def _validate_model(model: Model) -> None:
        """
        Validates the model used for model testing.

        :param model: the model to validate
        :raises UnsupportedFormatForModelTestingException: if the model format is not supported
        :raises PurgedModelException: if the model has been purged
        """
        if model.model_format is not ModelFormat.OPENVINO:
            raise UnsupportedFormatForModelTestingException(model_format=model.model_format.name)
        if model.purge_info.is_purged:
            raise PurgedModelException("Can not run a model test with an archived model since its weights are deleted.")

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from service.job_submission.base import JobParams, ModelJobSubmitter
from service.job_submission.job_creation_helpers import MODEL_TEST_JOB_PRIORITY, JobDuplicatePolicy, ModelTestJobData

from geti_types import ID
from sc_sdk.configuration.elements.component_parameters import ComponentType
from sc_sdk.configuration.elements.dataset_manager_parameters import DatasetManagementConfig
from sc_sdk.entities.model_test_result import ModelTestResult
from sc_sdk.entities.project import Project
from sc_sdk.repos import ConfigurableParametersRepo


class ModelTestingJobSubmitter(ModelJobSubmitter):
    def prepare_data(  # type: ignore
        self, model_test_result: ModelTestResult, project: Project, author: ID, is_local_anomaly_test: bool = False
    ) -> JobParams:
        """
        Prepares data for a model testing job submission

        :param project: project containing model and dataset storage
        :param model_test_result: model test result
        :param author: ID of the user submitting the job
        :param is_local_anomaly_test: set to True if the model test is for local metric of local anomaly task
        :return: ID of the model test job that has been submitted to the jobs client
        """
        model = model_test_result.get_model()
        config_repo = ConfigurableParametersRepo(project.identifier)
        dataset_manager_config = config_repo.get_or_create_component_parameters(
            data_instance_of=DatasetManagementConfig,
            component=ComponentType.PIPELINE_DATASET_MANAGER,
        )
        min_annotation_size = (
            None
            if dataset_manager_config.minimum_annotation_size == -1
            else dataset_manager_config.minimum_annotation_size
        )
        max_number_of_annotations = (
            None
            if dataset_manager_config.maximum_number_of_annotations == -1
            else dataset_manager_config.maximum_number_of_annotations
        )
        model_testing_job_data = ModelTestJobData(
            model_test_result=model_test_result,
            model=model,
            model_storage=model.model_storage,
            is_local_anomaly_test=is_local_anomaly_test,
            project=project,
            workspace_id=project.workspace_id,
            dataset_storage=model_test_result.get_dataset_storages()[0],
            task_node=next(
                task for task in project.get_trainable_task_nodes() if task.id_ == model.model_storage.task_node_id
            ),
            min_annotation_size=min_annotation_size,
            max_number_of_annotations=max_number_of_annotations,
        )

        return JobParams(
            priority=MODEL_TEST_JOB_PRIORITY,
            job_name=model_testing_job_data.job_name,
            job_type=model_testing_job_data.job_type,
            key=model_testing_job_data.create_key(),
            payload=model_testing_job_data.create_payload(),
            metadata=model_testing_job_data.create_metadata(),
            duplicate_policy=JobDuplicatePolicy.REJECT.name.lower(),
            author=author,
            project_id=project.id_,
            cancellable=True,
        )

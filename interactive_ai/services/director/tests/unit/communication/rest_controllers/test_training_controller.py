# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import MagicMock, patch

import pytest
from jsonschema.exceptions import ValidationError

from communication.controllers.training_controller import TrainingController
from communication.data_validator import TrainingRestValidator
from communication.exceptions import (
    NotEnoughDatasetItemsException,
    NotEnoughSpaceHTTPException,
    NotReadyForTrainingException,
    ObsoleteTrainingAlgorithmException,
)
from entities import TrainingConfig
from features.feature_flag import FeatureFlag
from service.job_submission import ModelTrainingJobSubmitter
from service.project_service import ProjectService

from geti_fastapi_tools.exceptions import BadRequestException
from geti_types import ID, ImageIdentifier
from iai_core.algorithms import ModelTemplateList
from iai_core.entities.annotation_scene_state import AnnotationSceneState, AnnotationState
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.datasets import Dataset
from iai_core.entities.model_storage import ModelStorage
from iai_core.entities.task_node import TaskNode
from iai_core.repos import AnnotationSceneStateRepo, DatasetRepo, ModelStorageRepo, TaskNodeRepo
from iai_core.repos.dataset_entity_repo import PipelineDatasetRepo
from iai_core.services import ModelService

DUMMY_USER = ID("dummy_user")


class TestTrainingController:
    def test_train_task(self, fxt_project, fxt_model_template_detection, fxt_ote_id) -> None:
        job_id = fxt_ote_id(101)
        raw_train_config = {"key1": "val1"}
        train_config = MagicMock(spec=TrainingConfig)
        train_config.model_template_id = fxt_model_template_detection.model_template_id
        with (
            patch.object(TrainingRestValidator, "validate_train_request") as mock_schema_validation,
            patch.object(ProjectService, "get_by_id", return_value=fxt_project) as mock_get_project,
            patch(
                "communication.controllers.training_controller.check_free_space_for_operation"
            ) as mock_check_free_space,
            patch.object(
                TrainingConfig, "generate_training_config", return_value=train_config
            ) as mock_parse_train_config,
            patch.object(
                TrainingController,
                "_is_task_ready_for_manual_training",
                return_value=(True, None),
            ) as mock_is_task_ready,
            patch.object(
                TrainingController,
                "get_annotations_and_dataset_items",
                return_value=(20, 20),
            ),
            patch.object(TrainingController, "_submit_train_job", return_value=job_id) as mock_submit_job,
        ):
            train_response_json = TrainingController.train_task(
                project_id=fxt_project.id_,
                author=DUMMY_USER,
                raw_train_config=raw_train_config,
            )

        mock_schema_validation.assert_called_once_with(raw_train_config)
        mock_get_project.assert_called_once()
        mock_check_free_space.assert_called_once()
        mock_parse_train_config.assert_called_once_with(project=fxt_project, train_config_dict=raw_train_config)
        mock_is_task_ready.assert_called_once_with(task_train_config=train_config, project=fxt_project)
        mock_submit_job.assert_called_once_with(
            project=fxt_project, task_training_config=train_config, author=DUMMY_USER
        )
        assert train_response_json == {"job_id": str(job_id)}

    def test_train_task_invalid_json(self, fxt_project) -> None:
        raw_train_config = {"key1": "val1"}
        with (
            patch.object(
                TrainingRestValidator,
                "validate_train_request",
                side_effect=ValidationError("test"),
            ),
            pytest.raises(ValidationError),
        ):
            TrainingController.train_task(
                project_id=fxt_project.id_,
                author=DUMMY_USER,
                raw_train_config=raw_train_config,
            )

    def test_train_task_chain_without_task_id(self, fxt_detection_segmentation_chain_project) -> None:
        project = fxt_detection_segmentation_chain_project
        raw_train_config = {"key1": "val1"}
        with (
            patch.object(TrainingRestValidator, "validate_train_request"),
            patch.object(ProjectService, "get_by_id", return_value=project),
            pytest.raises(BadRequestException),
        ):
            TrainingController.train_task(
                project_id=project.id_,
                author=DUMMY_USER,
                raw_train_config=raw_train_config,
            )

    def test_train_task_non_existing_task(self, fxt_project) -> None:
        raw_train_config = {"task_id": "non_existing_task_id"}
        with (
            patch.object(TrainingRestValidator, "validate_train_request"),
            patch.object(ProjectService, "get_by_id", return_value=fxt_project),
            pytest.raises(BadRequestException),
        ):
            TrainingController.train_task(
                project_id=fxt_project.id_,
                author=DUMMY_USER,
                raw_train_config=raw_train_config,
            )

    def test_train_task_no_disk_space(self, fxt_project) -> None:
        raw_train_config = {"key1": "val1"}
        with (
            patch.object(TrainingRestValidator, "validate_train_request"),
            patch.object(ProjectService, "get_by_id", return_value=fxt_project),
            patch(
                "communication.controllers.training_controller.check_free_space_for_operation",
                side_effect=NotEnoughSpaceHTTPException("test"),
            ),
            pytest.raises(NotEnoughSpaceHTTPException),
        ):
            TrainingController.train_task(
                project_id=fxt_project.id_,
                author=DUMMY_USER,
                raw_train_config=raw_train_config,
            )

    def test_train_task_obsolete_algorithm(self, fxt_project, fxt_model_template_obsolete) -> None:
        raw_train_config = {"key1": "val1"}
        train_config = MagicMock(spec=TrainingConfig)
        train_config.model_template_id = fxt_model_template_obsolete.model_template_id
        ModelTemplateList().register_model_template(fxt_model_template_obsolete)
        assert fxt_model_template_obsolete.model_template_id in ModelTemplateList().obsolete_model_template_ids
        with (
            patch.object(TrainingRestValidator, "validate_train_request"),
            patch.object(ProjectService, "get_by_id", return_value=fxt_project),
            patch(
                "communication.controllers.training_controller.check_free_space_for_operation",
            ),
            patch.object(TrainingConfig, "generate_training_config", return_value=train_config),
            pytest.raises(ObsoleteTrainingAlgorithmException),
        ):
            TrainingController.train_task(
                project_id=fxt_project.id_,
                author=DUMMY_USER,
                raw_train_config=raw_train_config,
            )

    def test_train_task_not_enough_annotations(self, fxt_project) -> None:
        raw_train_config = {"key1": "val1"}
        train_config = MagicMock(spec=TrainingConfig)
        train_config.model_template_id = "model_template_id"
        with (
            patch.object(TrainingRestValidator, "validate_train_request"),
            patch.object(ProjectService, "get_by_id", return_value=fxt_project),
            patch(
                "communication.controllers.training_controller.check_free_space_for_operation",
            ),
            patch.object(TrainingConfig, "generate_training_config", return_value=train_config),
            patch.object(
                TrainingController,
                "_is_task_ready_for_manual_training",
                return_value=(False, "test"),
            ),
            pytest.raises(NotReadyForTrainingException),
        ):
            TrainingController.train_task(
                project_id=fxt_project.id_,
                author=DUMMY_USER,
                raw_train_config=raw_train_config,
            )

    def test_train_task_not_enough_dataset_items(self, fxt_project, fxt_enable_feature_flag_name) -> None:
        fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_CREDIT_SYSTEM.name)
        raw_train_config = {"key1": "val1"}
        train_config = MagicMock(spec=TrainingConfig)
        train_config.model_template_id = "model_template_id"
        train_config.task = MagicMock(spec=TaskNode)
        train_config.task.id_ = "task_id"
        with (
            patch.object(TrainingRestValidator, "validate_train_request"),
            patch.object(ProjectService, "get_by_id", return_value=fxt_project),
            patch(
                "communication.controllers.training_controller.check_free_space_for_operation",
            ),
            patch.object(TrainingConfig, "generate_training_config", return_value=train_config),
            patch.object(
                TrainingController,
                "_is_task_ready_for_manual_training",
                return_value=(True, None),
            ),
            patch.object(
                TrainingController,
                "get_annotations_and_dataset_items",
                return_value=(20, 0),
            ),
            pytest.raises(NotEnoughDatasetItemsException),
        ):
            TrainingController.train_task(
                project_id=fxt_project.id_,
                author=DUMMY_USER,
                raw_train_config=raw_train_config,
            )

    def test_submit_train_jobs_model_storage_exists(
        self,
        fxt_project,
        fxt_detection_task,
        fxt_model_storage_detection,
        fxt_ote_id,
    ) -> None:
        # Arrange
        model_template_id = fxt_model_storage_detection.model_template.model_template_id
        fxt_model_storage_detection._task_node_id = fxt_detection_task.id_
        hyper_parameters = MagicMock(id_=fxt_ote_id(11), ephemeral=False)
        train_from_scratch = False
        training_config = TrainingConfig(
            model_template_id=model_template_id,
            task=fxt_detection_task,
            train_from_scratch=train_from_scratch,
            hyper_parameters=hyper_parameters,
        )

        # Act
        with (
            patch.object(
                ModelStorageRepo,
                "get_by_task_node_id",
                return_value=[fxt_model_storage_detection],
            ) as patched_get_by_task_node_id,
            patch.object(ModelTrainingJobSubmitter, "execute", return_value=fxt_ote_id()) as mock_training_job_submit,
        ):
            train_jobs_per_task = TrainingController._submit_train_job(
                project=fxt_project,
                task_training_config=training_config,
                author=DUMMY_USER,
            )

        # Assert
        mock_training_job_submit.assert_called_once_with(
            project=fxt_project,
            task_node=training_config.task,
            model_storage=fxt_model_storage_detection,
            from_scratch=training_config.train_from_scratch,
            activate_model_storage=True,
            hyper_parameters_id=fxt_ote_id(11),
            author=DUMMY_USER,
            max_training_dataset_size=training_config.max_training_dataset_size,
            reshuffle_subsets=False,
        )
        patched_get_by_task_node_id.assert_called_once_with(task_node_id=fxt_detection_task.id_)
        assert train_jobs_per_task == fxt_ote_id()

    @patch("iai_core.entities.model_storage.now", return_value="now")
    def test_submit_train_jobs_new_model_storage(
        self,
        fxt_project,
        fxt_detection_task,
        fxt_model_template_detection,
        fxt_ote_id,
    ) -> None:
        # Arrange
        model_template_id = fxt_model_template_detection.model_template_id
        hyper_parameters = MagicMock(id_=fxt_ote_id(11), ephemeral=False)
        train_from_scratch = False
        training_config = TrainingConfig(
            model_template_id=model_template_id,
            task=fxt_detection_task,
            hyper_parameters=hyper_parameters,
            train_from_scratch=train_from_scratch,
        )

        expected_model_storage = ModelStorage(
            id_=ModelStorageRepo.generate_id(),
            project_id=fxt_project.id_,
            task_node_id=fxt_detection_task.id_,
            model_template=fxt_model_template_detection,
        )

        # Act
        with (
            patch.object(
                ModelService,
                "get_or_create_model_storage",
                return_value=expected_model_storage,
            ) as patched_get_model_storage,
            patch.object(ModelTrainingJobSubmitter, "execute", return_value=fxt_ote_id()) as mock_training_job_submit,
        ):
            train_jobs_per_task = TrainingController._submit_train_job(
                project=fxt_project,
                task_training_config=training_config,
                author=DUMMY_USER,
            )

        # Assert
        patched_get_model_storage.assert_called_once_with(
            task_node=fxt_detection_task,
            model_template_id=fxt_model_template_detection.model_template_id,
            project_identifier=fxt_project.identifier,
        )
        mock_training_job_submit.assert_called_once_with(
            project=fxt_project,
            task_node=fxt_detection_task,
            model_storage=expected_model_storage,
            from_scratch=train_from_scratch,
            activate_model_storage=True,
            max_training_dataset_size=None,
            hyper_parameters_id=hyper_parameters.id_,
            author=DUMMY_USER,
            reshuffle_subsets=False,
        )
        assert train_jobs_per_task == fxt_ote_id()

    def test_get_annotations_and_dataset_items(
        self, request, fxt_project, fxt_mongo_id, fxt_annotation_scene, fxt_image_entity
    ) -> None:
        task_id = fxt_project.task_graph.ordered_tasks[1].id_
        # Create and save some annotated and unannotated annotation scene states
        annotation_scene_state_1 = AnnotationSceneState(
            id_=fxt_mongo_id(10),
            media_identifier=ImageIdentifier(fxt_mongo_id(0)),
            annotation_scene_id=fxt_mongo_id(11),
            annotation_state_per_task={task_id: AnnotationState.ANNOTATED},
            unannotated_rois={},
        )
        annotation_scene_state_2 = AnnotationSceneState(
            id_=fxt_mongo_id(20),
            media_identifier=ImageIdentifier(fxt_mongo_id(1)),
            annotation_scene_id=fxt_mongo_id(21),
            annotation_state_per_task={task_id: AnnotationState.ANNOTATED},
            unannotated_rois={},
        )
        annotation_scene_state_3 = AnnotationSceneState(
            id_=fxt_mongo_id(30),
            media_identifier=ImageIdentifier(fxt_mongo_id(2)),
            annotation_scene_id=fxt_mongo_id(31),
            annotation_state_per_task={task_id: AnnotationState.NONE},
            unannotated_rois={},
        )
        ds_storage = fxt_project.get_training_dataset_storage()
        AnnotationSceneStateRepo(ds_storage.identifier).save_many(
            [
                annotation_scene_state_1,
                annotation_scene_state_2,
                annotation_scene_state_3,
            ]
        )

        with patch.object(TaskNodeRepo, "get_trainable_task_ids", return_value=[task_id]):
            pipeline_dataset = PipelineDatasetRepo.get_or_create(ds_storage.identifier)
            request.addfinalizer(lambda: PipelineDatasetRepo(ds_storage.identifier).delete_all())
            task_dataset_entity = pipeline_dataset.task_datasets[task_id]

            # Create and save dataset item
            ds_item_1 = DatasetItem(
                id_=DatasetRepo.generate_id(),
                media=fxt_image_entity,
                annotation_scene=fxt_annotation_scene,
            )
            dataset = Dataset(id=task_dataset_entity.dataset_id, items=[ds_item_1])
            dataset_repo = DatasetRepo(ds_storage.identifier)
            dataset_repo.save_deep(dataset)
            request.addfinalizer(lambda: dataset_repo.delete_all())

            num_annotations, num_ds_items = TrainingController.get_annotations_and_dataset_items(fxt_project, task_id)
        assert num_annotations == 2
        assert num_ds_items == 1

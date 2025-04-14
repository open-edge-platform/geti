# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from copy import copy
from typing import cast
from unittest.mock import call, patch

import numpy as np
import pytest

from sc_sdk.configuration.enums import ComponentType
from sc_sdk.entities.active_model_state import NullActiveModelState
from sc_sdk.entities.annotation import NullAnnotationScene
from sc_sdk.entities.annotation_scene_state import AnnotationSceneState
from sc_sdk.entities.dataset_entities import PipelineDataset
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.dataset_storage import NullDatasetStorage
from sc_sdk.entities.datasets import Dataset
from sc_sdk.entities.image import Image, NullImage
from sc_sdk.entities.media_score import NullMediaScore
from sc_sdk.entities.metadata import MetadataItem
from sc_sdk.entities.model import Model, ModelFormat, ModelOptimizationType
from sc_sdk.entities.model_test_result import ModelTestResult, NullModelTestResult
from sc_sdk.entities.project import NullProject, Project
from sc_sdk.entities.tensor import Tensor
from sc_sdk.entities.video import NullVideo
from sc_sdk.repos import (
    ActiveModelStateRepo,
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    ConfigurableParametersRepo,
    DatasetRepo,
    DatasetStorageRepo,
    ImageRepo,
    LabelSchemaRepo,
    MediaScoreRepo,
    MetadataRepo,
    ModelRepo,
    ModelStorageRepo,
    ModelTestResultRepo,
    ProjectRepo,
    TaskNodeRepo,
    VideoRepo,
)
from sc_sdk.repos.dataset_entity_repo import PipelineDatasetRepo
from sc_sdk.utils.deletion_helpers import DeletionHelpers
from tests.configuration.dummy_config import DatasetManagerConfig
from tests.test_helpers import TestProject

from geti_types import ID, DatasetStorageIdentifier, ProjectIdentifier


@pytest.mark.ScSdkComponent
class TestDeletionHelpers:
    def test_delete_image_entity(self, project_with_data: TestProject) -> None:
        """
        <b>Description:</b>
        Tests that an image can be removed entirely from a project

        <b>Input data:</b>
        A project with loaded dataset

        <b>Expected results:</b>
        The test passes if the image and its annotations are deleted

        <b>Steps</b>
        1. Obtain an image from the dataset
        3. Remove image from project
        4. Check that the image was completely removed
        """
        project = project_with_data.project
        dataset_storage = project.get_training_dataset_storage()
        dataset: Dataset = project_with_data.circle_dataset
        image_repo = ImageRepo(dataset_storage.identifier)
        ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
        first_item = dataset[0]
        if isinstance(first_item.media, Image):
            media_id = first_item.media.media_identifier.media_id
            assert image_repo.get_by_id(media_id) != NullImage()
            DeletionHelpers.delete_image_entity(dataset_storage=dataset_storage, image=first_item.media)
            assert image_repo.get_by_id(media_id) == NullImage()
            assert ann_scene_repo.get_by_id(media_id) == NullAnnotationScene()

    def test_delete_video_entity(self, sample_project: Project, fxt_random_annotated_video_factory) -> None:
        """
        <b>Description:</b>
        Tests that video can be removed entirely from a project

        <b>Input data:</b>
        A sample project
        A randomly annotated video

        <b>Expected results:</b>
        The test passes if the video and its annotations are deleted.

        <b>Steps</b>
        1. Generate video with annotations
        3. Remove video from project
        4. Check that the video and the annotations were removed
        """
        dataset_storage = sample_project.get_training_dataset_storage()
        video, _, _, _, _, _, _ = fxt_random_annotated_video_factory(sample_project)
        video_repo = VideoRepo(dataset_storage.identifier)
        assert video_repo.get_by_id(video.id_) != NullVideo()
        DeletionHelpers.delete_video_entity(dataset_storage=dataset_storage, video=video)
        assert video_repo.get_by_id(video.id_) == NullVideo()
        assert AnnotationSceneRepo(dataset_storage.identifier).get_by_id(video.id_) == NullAnnotationScene()

    def test_delete_project_by_id(self, project_with_data: TestProject, fxt_random_annotated_video_factory) -> None:
        """
        <b>Description:</b>
        Tests that a project can be deleted

        <b>Input data:</b>
        A sample project

        <b>Expected results:</b>
        The test passes if the project and all the relative entities are deleted

        <b>Steps</b>
        1. Check that Project is saved in the DB
        2. Delete the project
        3. Check that the Project has been deleted
        4. Check that images, videos, datasets and annotations relative to the project
           are deleted too.
        5. Check that deleting a non-existing project does not throw errors
        """
        # Step 1
        project: Project = project_with_data.project
        dataset_storage = project.get_training_dataset_storage()
        dataset_storage_repo = DatasetStorageRepo(project.identifier)
        project_repo: ProjectRepo = ProjectRepo()
        image_repo = ImageRepo(dataset_storage.identifier)
        video_repo = VideoRepo(dataset_storage.identifier)
        model_storage_repo = ModelStorageRepo(project.identifier)
        active_model_state_repo = ActiveModelStateRepo(project.identifier)
        assert not isinstance(project_repo.get_by_id(project.id_), NullProject)

        # Save Dataset
        dataset_repo = DatasetRepo(dataset_storage.identifier)
        dataset_repo.save_deep(project_with_data.circle_dataset)
        # Save image
        dataset_item: DatasetItem = project_with_data.circle_dataset[0]
        image_repo.save(cast(Image, dataset_item.media))
        # Save video
        fxt_random_annotated_video_factory(project)
        # Save annotation scene
        image_annotation = dataset_item.annotation_scene
        AnnotationSceneRepo(dataset_storage.identifier).save(image_annotation)
        annotation_scene_state = AnnotationSceneState(
            media_identifier=dataset_item.media_identifier,
            annotation_scene_id=image_annotation.id_,
            annotation_state_per_task={},
            unannotated_rois={},
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        AnnotationSceneStateRepo(dataset_storage.identifier).save(annotation_scene_state)
        tensor = Tensor(name="test_tensor", numpy=np.eye(2))
        metadata = MetadataItem(
            data=tensor,
            dataset_item_id=MetadataRepo.generate_id(),
            media_identifier=dataset_item.media_identifier,
            id=MetadataRepo.generate_id(),
        )
        metadata_repo = MetadataRepo(dataset_storage.identifier)
        metadata_repo.save(metadata)
        # Save model
        model: Model = project_with_data.segmentation_model
        model_repo = ModelRepo(model.model_storage_identifier)
        model_repo.save(model)
        # Save configurable parameters
        config_repo = ConfigurableParametersRepo(project.identifier)
        config = config_repo.get_or_create_component_parameters(
            data_instance_of=DatasetManagerConfig,
            component=ComponentType.DATASET_COUNTER,
        )
        config_repo.save(config)
        # Save model tests
        model_test_repo = ModelTestResultRepo(project.identifier)
        model_test = ModelTestResult(
            id_=ModelTestResultRepo.generate_id(),
            name="test",
            project_identifier=project.identifier,
            model_storage_id=model.model_storage.id_,
            model_id=model.id_,
            dataset_storage_ids=[dataset_storage.id_],
        )
        model_test_repo.save(model_test)
        # Save pipeline dataset entity
        pipeline_dataset_entity_repo = PipelineDatasetRepo(dataset_storage.identifier)
        pipeline_dataset_entity = PipelineDataset(
            project_id=project.id_,
            task_datasets={},
            dataset_storage_id=dataset_storage.id_,
        )
        pipeline_dataset_entity_repo.save(pipeline_dataset_entity)

        assert list(LabelSchemaRepo(project.identifier).get_all())
        assert list(TaskNodeRepo(project.identifier).get_all())
        assert list(image_repo.get_all())
        assert list(video_repo.get_all())
        assert list(AnnotationSceneRepo(dataset_storage.identifier).get_all())
        assert list(AnnotationSceneStateRepo(dataset_storage.identifier).get_all())
        assert list(metadata_repo.get_all())
        assert list(dataset_repo.get_all())
        assert list(model_repo.get_all())
        assert list(model_test_repo.get_all())
        assert list(pipeline_dataset_entity_repo.get_all())

        # Step 2
        task_node_ids = [task_node.id_ for task_node in project.tasks]
        DeletionHelpers.delete_project_by_id(project_id=project.id_)

        # Step 3
        assert isinstance(project_repo.get_by_id(project.id_), NullProject)

        # Step 4
        assert not list(LabelSchemaRepo(project.identifier).get_all())
        assert not list(TaskNodeRepo(project.identifier).get_all())
        assert not list(image_repo.get_all())
        assert not list(video_repo.get_all())
        assert not list(AnnotationSceneRepo(dataset_storage.identifier).get_all())
        assert not list(AnnotationSceneStateRepo(dataset_storage.identifier).get_all())
        assert not list(metadata_repo.get_all())
        assert not list(dataset_repo.get_all())
        assert not list(model_repo.get_all())
        assert isinstance(dataset_storage_repo.get_by_id(dataset_storage.id_), NullDatasetStorage)
        for task_node_id in task_node_ids:
            assert isinstance(
                active_model_state_repo.get_by_task_node_id(task_node_id),
                NullActiveModelState,
            )
            assert not list(model_storage_repo.get_by_task_node_id(task_node_id))
        assert not list(config_repo.get_all())
        assert not list(TaskNodeRepo(project.identifier).get_all())
        assert not list(model_test_repo.get_all())
        assert not list(pipeline_dataset_entity_repo.get_all())

        # Step 5
        DeletionHelpers.delete_project_by_id(project_id=ID("bad1"))

    @pytest.mark.parametrize("fxt_filled_dataset_storage", [50], indirect=True)
    def test_delete_dataset_storage_by_id(self, fxt_filled_dataset_storage, fxt_mongo_id):
        """
        <b>Description:</b>
        Tests that a dataset storage and its child items can be removed entirely from db

        <b>Input data:</b>
        A filled dataset storage with 50 images, annotation scenes, annotation scene states

        <b>Expected results:</b>
        The test passes if the dataset storage is deleted along with its child irems

        <b>Steps</b>
        1. Obtain an images, ann scenes and states in dataset storage from db
        3. Remove dataset storage
        4. Check that the dataset storage, images, ann scenes, and states were completely removed
        """
        # Arrange
        image_repo = ImageRepo(fxt_filled_dataset_storage.identifier)
        annotation_repo = AnnotationSceneRepo(fxt_filled_dataset_storage.identifier)
        annotation_state_repo = AnnotationSceneStateRepo(fxt_filled_dataset_storage.identifier)
        project_identifier = ProjectIdentifier(
            workspace_id=fxt_filled_dataset_storage.workspace_id,
            project_id=fxt_filled_dataset_storage.project_id,
        )

        images_before = len(list(image_repo.get_all()))
        annotation_scenes_before = len(list(annotation_repo.get_all()))
        annotation_states_before = len(list(annotation_state_repo.get_all()))

        # Act
        DeletionHelpers.delete_dataset_storage_by_id(fxt_filled_dataset_storage.identifier)

        images_after = list(image_repo.get_all())
        annotation_scenes_after = list(annotation_repo.get_all())
        annotation_states_after = list(annotation_state_repo.get_all())

        # Assert
        assert isinstance(
            DatasetStorageRepo(project_identifier).get_by_id(fxt_filled_dataset_storage.id_),
            NullDatasetStorage,
        )

        assert images_before == 50
        assert annotation_scenes_before == 50
        assert annotation_states_before == 50

        assert len(images_after) == 0
        assert len(annotation_scenes_after) == 0
        assert len(annotation_states_after) == 0

    def test_delete_all_entities_in_project(
        self,
        fxt_multi_dataset_storages_project,
        fxt_dataset_storage,
        fxt_testing_dataset_storage,
        fxt_model_storage_classification,
        fxt_label_schema_factory,
    ) -> None:
        """
        <b>Description:</b>
        Tests that all entities in a project can be deleted

        <b>Input data:</b>
        A sample project with multiple dataset storages

        <b>Expected results:</b>
        The test passes if all delete methods are called

        <b>Steps</b>
        1. Delete entities in project
        2. Check that all deletion methods are called
        """
        # TODO CVS-83526: deletion not implemented yet for operation repos
        project = fxt_multi_dataset_storages_project
        project.dataset_storages = [fxt_dataset_storage, fxt_testing_dataset_storage]
        dummy_task_model_storages = [fxt_model_storage_classification]

        with (
            patch.object(
                ModelStorageRepo,
                "get_by_task_node_id",
                return_value=dummy_task_model_storages,
            ) as mock_get_model_storage,
            patch.object(DeletionHelpers, "delete_all_entities_in_model_storage") as mock_delete_all_in_model_storage,
            patch.object(
                DeletionHelpers, "delete_all_model_test_results_by_project"
            ) as mock_delete_all_model_test_results,
            patch.object(
                ModelStorageRepo,
                "delete_by_id",
            ) as mock_model_storage_delete,
            patch.object(DeletionHelpers, "delete_dataset_storage_by_id") as mock_delete_dataset_storage,
            patch.object(
                DeletionHelpers, "delete_all_active_model_states_by_project"
            ) as mock_delete_active_model_states,
            patch.object(DeletionHelpers, "delete_all_label_schema_by_project") as mock_delete_label_schemas,
            patch.object(
                DeletionHelpers,
                "delete_all_task_nodes_by_project",
            ) as mock_delete_task_nodes,
            patch.object(
                DeletionHelpers,
                "delete_all_configurable_parameters_by_project",
            ) as mock_delete_config_params,
            patch.object(
                DeletionHelpers,
                "delete_evaluation_result_entities_by_project",
            ) as mock_delete_evaluation_results,
        ):
            DeletionHelpers.delete_all_entities_in_project(project)

        mock_get_model_storage.assert_called()
        mock_model_storage_delete.assert_called()
        mock_delete_all_model_test_results.assert_called()
        mock_delete_all_in_model_storage.assert_called()
        mock_delete_dataset_storage.assert_has_calls([call(ds.identifier) for ds in project.dataset_storages])
        mock_delete_active_model_states.assert_called_with(project=project)
        mock_delete_label_schemas.assert_called_with(project.identifier)
        mock_delete_task_nodes.assert_called_with(project.identifier)
        mock_delete_config_params.assert_called_with(project=project)
        mock_delete_evaluation_results.assert_called_with(project=project)

    def test_media_score_deletion(
        self,
        request,
        fxt_media_score,
        fxt_model_test_result,
        fxt_empty_project,
        fxt_image_identifier,
    ) -> None:
        """
        <b>Description:</b>
        Check that DeletionHelpers delete media scores properly

        <b>Input data:</b>
        MediaScore instance

        <b>Expected results:</b>
        Test succeeds if user test can be inserted in the database, retrieved and deleted.

        <b>Steps</b>
        1. Create Input data
        2. Add MediaScore to the project
        3. Retrieve the MediaScore and check that it is the right one
        3. Delete the MediaScore by media and check that it is deleted
        4. Add MediaScore back to the project
        3. Delete the MediaScore by dataset storage and check that it is deleted
        """
        dataset_storage = fxt_empty_project.get_training_dataset_storage()
        dataset_storage.project_id = fxt_empty_project.id_
        dataset_storage.identifier = DatasetStorageIdentifier(
            workspace_id=dataset_storage.workspace_id,
            project_id=dataset_storage.project_id,
            dataset_storage_id=dataset_storage.id_,
        )
        fxt_model_test_result.id_ = fxt_media_score.model_test_result_id

        model_test_result_repo = ModelTestResultRepo(fxt_empty_project.identifier)
        media_score_repo = MediaScoreRepo(dataset_storage.identifier)
        project_repo = ProjectRepo()
        dataset_storage_repo = DatasetStorageRepo(fxt_empty_project.identifier)

        request.addfinalizer(lambda: model_test_result_repo.delete_by_id(fxt_model_test_result.id_))
        request.addfinalizer(lambda: dataset_storage_repo.delete_by_id(dataset_storage.id_))
        request.addfinalizer(lambda: project_repo.delete_by_id(fxt_empty_project.id_))
        request.addfinalizer(lambda: media_score_repo.delete_by_id(fxt_media_score.id_))

        project_repo.save(fxt_empty_project)
        dataset_storage_repo.save(dataset_storage)
        media_score_repo.save(fxt_media_score)
        model_test_result_repo.save(fxt_model_test_result)

        assert media_score_repo.get_by_id(fxt_media_score.id_) == fxt_media_score

        DeletionHelpers.delete_media_score_entities_by_media_id(dataset_storage, fxt_image_identifier.media_id)

        assert media_score_repo.get_by_id(fxt_media_score.id_) == NullMediaScore()

        media_score_repo.save(fxt_media_score)

        with patch.object(
            ModelTestResultRepo,
            "get_all",
            return_value=[fxt_model_test_result],
        ):
            DeletionHelpers.delete_media_scores_by_dataset_storage(dataset_storage=dataset_storage)

        assert media_score_repo.get_by_id(fxt_media_score.id_) == NullMediaScore()

        media_score_repo.save(fxt_media_score)

        assert model_test_result_repo.get_by_id(fxt_model_test_result.id_) == fxt_model_test_result

        DeletionHelpers.delete_model_test_result(fxt_empty_project.identifier, fxt_model_test_result)

        assert model_test_result_repo.get_by_id(fxt_model_test_result.id_) == NullModelTestResult()
        assert media_score_repo.get_by_id(fxt_media_score.id_) == NullMediaScore()

    def test_delete_models_by_base_model_id(
        self,
        request,
        fxt_model,
    ):
        # Arrange
        model_storage_identifier = fxt_model.model_storage_identifier
        model_repo = ModelRepo(model_storage_identifier)
        fxt_model.id_ = ID("model_1")
        fxt_model.model_format = ModelFormat.BASE_FRAMEWORK
        model_2 = copy(fxt_model)
        model_2.id_ = ID("model_2")
        model_2.optimization_type = ModelOptimizationType.MO
        model_2.model_format = ModelFormat.OPENVINO
        model_2.set_previous_trained_revision(fxt_model)
        model_3 = copy(fxt_model)
        model_3.id_ = ID("model_3")
        model_3.set_previous_trained_revision(fxt_model)
        model_3.optimization_type = ModelOptimizationType.ONNX
        model_3.model_format = ModelFormat.ONNX

        model_repo.save(fxt_model)
        model_repo.save(model_2)
        model_repo.save(model_3)

        request.addfinalizer(lambda: model_repo.delete_by_id(fxt_model.id_))
        request.addfinalizer(lambda: model_repo.delete_by_id(model_2.id_))
        request.addfinalizer(lambda: model_repo.delete_by_id(model_3.id_))

        query = {"_id": {"$in": [fxt_model.id_, model_2.id_, model_3.id_]}}
        assert len(list(model_repo.get_all_ids(extra_filter=query))) == 3

        # Act
        DeletionHelpers.delete_models_by_base_model_id(
            project_id=model_storage_identifier.project_id,
            model_storage_id=model_storage_identifier.model_storage_id,
            base_model_id=fxt_model.id_,
        )

        # Assert
        assert len(list(model_repo.get_all_ids(extra_filter=query))) == 0

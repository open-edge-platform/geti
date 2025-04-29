# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains utilities for cascade deletion of entities"""

import logging

from sc_sdk.entities.dataset_storage import DatasetStorage, NullDatasetStorage
from sc_sdk.entities.datasets import DatasetIdentifier
from sc_sdk.entities.image import Image
from sc_sdk.entities.model_storage import ModelStorage, ModelStorageIdentifier
from sc_sdk.entities.model_test_result import ModelTestResult
from sc_sdk.entities.project import NullProject, Project
from sc_sdk.entities.video import Video
from sc_sdk.repos import (
    ActiveModelStateRepo,
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    CompiledDatasetShardsRepo,
    ConfigurableParametersRepo,
    DatasetRepo,
    DatasetStorageRepo,
    EvaluationResultRepo,
    ImageRepo,
    LabelRepo,
    LabelSchemaRepo,
    MediaScoreRepo,
    MetadataRepo,
    ModelRepo,
    ModelStorageRepo,
    ModelTestResultRepo,
    ProjectRepo,
    TaskNodeRepo,
    VideoAnnotationRangeRepo,
    VideoRepo,
)
from sc_sdk.repos.dataset_entity_repo import PipelineDatasetRepo
from sc_sdk.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo
from sc_sdk.repos.training_revision_filter_repo import _TrainingRevisionFilterRepo

from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier, MediaIdentifierEntity, ProjectIdentifier

logger = logging.getLogger(__name__)


class DeletionHelpers:
    """Helper methods for cascade deletion of entities"""

    ####################################
    # Dataset storage related entities #
    ####################################

    @staticmethod
    def delete_metadata_items_by_media(
        dataset_storage: DatasetStorage,
        media_identifier: MediaIdentifierEntity,
    ) -> None:
        """
        Delete all the metadata items (including tensors and result media) for a media.

        :param dataset_storage: Dataset storage where the metadata items are stored
        :param media_identifier: Identifier of the media whose metadata items are to be deleted
        """
        logger.debug("Deleting metadata items of media `%s`", media_identifier)
        metadata_repo = MetadataRepo(dataset_storage.identifier)
        metadata_repo.delete_all_by_media_identifier(media_identifier=media_identifier)

    @staticmethod
    def delete_dataset_items_by_media(
        dataset_storage: DatasetStorage,
        media_identifier: MediaIdentifierEntity,
    ) -> None:
        """
        Delete all the dataset items relative to a media, and other related entities.

        Cascades to:
         - Metadata
         - Tensors
         - Result media

        :param dataset_storage: Dataset storage where the dataset items are stored
        :param media_identifier: Identifier of the media whose dataset items are to be deleted
        """
        logger.debug("Deleting dataset items of media `%s`", media_identifier)

        DeletionHelpers.delete_metadata_items_by_media(
            dataset_storage=dataset_storage, media_identifier=media_identifier
        )

    @staticmethod
    def delete_dataset_items_by_dataset_storage(dataset_storage: DatasetStorage) -> None:
        """
        Delete all the dataset items in a dataset storage, and other related entities.

        Cascades to:
         - Metadata (including tensors and result media)

        :param dataset_storage: Dataset storage where the dataset items are stored
        """
        logger.debug("Deleting all dataset items in storage `%s`", dataset_storage.id_)

        MetadataRepo(dataset_storage.identifier).delete_all()

        dataset_repo = DatasetRepo(dataset_storage.identifier)
        for dataset in dataset_repo.get_all():
            dataset_identifier = DatasetIdentifier.from_ds_identifier(dataset_storage.identifier, dataset.id_)
            _TrainingRevisionFilterRepo(dataset_identifier).delete_all()
            dataset_repo.delete_items_by_dataset(dataset_id=dataset.id_)

    @staticmethod
    def delete_datasets_by_dataset_storage(dataset_storage: DatasetStorage) -> None:
        """
        Delete all the datasets stored in a dataset storage.

        Note: this method does not cascade to the items.

        :param dataset_storage: Dataset storage where the datasets are stored
        """
        logger.debug("Deleting datasets of storage `%s`", dataset_storage.id_)

        DatasetRepo(dataset_storage.identifier).delete_all()

    @staticmethod
    def delete_annotation_entities_by_media(
        dataset_storage: DatasetStorage,
        media_id: ID,
        media_identifier: MediaIdentifierEntity,
    ) -> None:
        """
        Delete an annotation scene, its annotation and other related entities.

        Cascades to:
         - Dataset items

        :param dataset_storage: Dataset storage where the media is stored
        :param media_id: ID of the media whose annotations should be deleted
        :param media_identifier: Media identifier of the media
        """
        logger.debug("Deleting annotations of media `%s`", media_id)

        DeletionHelpers.delete_dataset_items_by_media(
            dataset_storage=dataset_storage,
            media_identifier=media_identifier,
        )

        AnnotationSceneRepo(dataset_storage.identifier).delete_all_by_media_id(media_id)
        AnnotationSceneStateRepo(dataset_storage.identifier).delete_all_by_media_id(media_id)

    @staticmethod
    def delete_annotation_entities_by_dataset_storage(dataset_storage: DatasetStorage) -> None:
        """
        Delete all the annotation scenes, their annotations and other related entities.

        Includes:
         - Annotation scenes
         - Annotation scene states

        :param dataset_storage: Dataset storage containing the annotation scenes
        """
        logger.debug("Deleting all annotation scenes of storage `%s`", dataset_storage.identifier)

        AnnotationSceneRepo(dataset_storage.identifier).delete_all()
        AnnotationSceneStateRepo(dataset_storage.identifier).delete_all()

    @staticmethod
    def delete_media_score_entities_by_media_id(dataset_storage: DatasetStorage, media_id: ID) -> None:
        """
        Delete media score entities related to image with given identifier

        :param dataset_storage: DatasetStorage containing the media
        :param media_id: Media id of media being deleted
        """
        logger.debug("Deleting media score entities of media %s", media_id)
        media_score_repo = MediaScoreRepo(dataset_storage.identifier)
        media_score_repo.delete_all_by_media_id(media_id)

    @staticmethod
    def delete_image_entity(dataset_storage: DatasetStorage, image: Image) -> None:
        """
        Delete an image entity and other related entities.

        Cascades to:
         - Annotation scenes
         - Dataset items

        :param dataset_storage: Dataset storage containing the image
        :param image: Image entity to delete
        """
        logger.debug("Deleting image `%s`", image)

        DeletionHelpers.delete_annotation_entities_by_media(
            dataset_storage=dataset_storage,
            media_id=image.id_,
            media_identifier=image.media_identifier,
        )
        DeletionHelpers.delete_media_score_entities_by_media_id(dataset_storage=dataset_storage, media_id=image.id_)
        DatasetStorageFilterRepo(dataset_storage.identifier).delete_all_by_media_id(media_id=image.id_)
        ImageRepo(dataset_storage.identifier).delete_by_id(image.id_)

    @staticmethod
    def delete_video_entity(dataset_storage: DatasetStorage, video: Video) -> None:
        """
        Delete a video entity and other related entities.

        Cascades to:
         - Annotation scenes
         - Dataset items

        :param dataset_storage: Dataset storage containing the video
        :param video: Video entity to delete
        """
        logger.debug("Deleting video `%s`", video)

        DeletionHelpers.delete_annotation_entities_by_media(
            dataset_storage=dataset_storage,
            media_id=video.id_,
            media_identifier=video.media_identifier,
        )
        VideoAnnotationRangeRepo(dataset_storage.identifier).delete_all_by_video_id(video_id=video.id_)
        DeletionHelpers.delete_media_score_entities_by_media_id(dataset_storage=dataset_storage, media_id=video.id_)
        DatasetStorageFilterRepo(dataset_storage.identifier).delete_all_by_media_id(media_id=video.id_)
        VideoRepo(dataset_storage.identifier).delete_by_id(video.id_)

    @staticmethod
    def delete_model_test_result(project_identifier: ProjectIdentifier, model_test_result: ModelTestResult) -> None:
        """
        Delete a model test result from the database

        Cascades to:
         - MediaScore

        :param project_identifier: Identifier of the project containing the model test result
        :param model_test_result: Model test result
        """
        for dataset_storage in model_test_result.get_dataset_storages():
            MediaScoreRepo(dataset_storage.identifier).delete_all_by_model_test_result_id(model_test_result.id_)

        ModelTestResultRepo(project_identifier).delete_by_id(model_test_result.id_)

    @staticmethod
    def delete_media_scores_by_dataset_storage(dataset_storage: DatasetStorage) -> None:
        """
        Delete all media score entities related to dataset storage

        Includes:
         - Media scores

        :param dataset_storage: Dataset storage to delete entities for
        """
        logger.debug("Deleting test related entities of dataset storage %s", dataset_storage.id_)

        project_repo = ProjectRepo()
        project = project_repo.get_by_dataset_storage_id(dataset_storage.id_)
        if not isinstance(project, NullProject):  # often tests pass a dataset storage with no saved project
            model_test_result_repo = ModelTestResultRepo(project.identifier)
            media_score_repo = MediaScoreRepo(dataset_storage.identifier)

            model_test_results = model_test_result_repo.get_all_by_dataset_storage_id(dataset_storage.id_)

            for model_test_result in model_test_results:
                media_score_repo.delete_all_by_model_test_result_id(model_test_result.id_)

    @staticmethod
    def delete_media_entities_by_dataset_storage(dataset_storage: DatasetStorage) -> None:
        """
        Delete all the media entities stored in a dataset storage.

        Cascades to:
         - Annotation scenes
         - Dataset items
         - Media scores

        :param dataset_storage: Dataset storage where the media are stored
        """
        logger.debug("Deleting media of storage `%s`", dataset_storage.id_)

        DeletionHelpers.delete_annotation_entities_by_dataset_storage(dataset_storage=dataset_storage)
        DeletionHelpers.delete_dataset_items_by_dataset_storage(dataset_storage=dataset_storage)
        DeletionHelpers.delete_media_scores_by_dataset_storage(dataset_storage=dataset_storage)

        DatasetStorageFilterRepo(dataset_storage.identifier).delete_all()
        ImageRepo(dataset_storage.identifier).delete_all()
        VideoRepo(dataset_storage.identifier).delete_all()

    @staticmethod
    def delete_evaluation_result_entities_by_project(project: Project) -> None:
        """
        Delete all evaluation result entities by project.

        :param project: project containing the result sets
        """
        logger.debug("Deleting all evaluation results of project `%s`", project.id_)

        EvaluationResultRepo(project.identifier).delete_all()

    @staticmethod
    def delete_pipeline_dataset_entities_by_dataset_storage(dataset_storage: DatasetStorage) -> None:
        """
        Delete all pipeline dataset entities by dataset storage.

        :param dataset_storage: Dataset storage containing the pipeline dataset entities
        """
        logger.debug("Deleting all pipeline dataset entities of storage `%s`", dataset_storage.id_)

        PipelineDatasetRepo(dataset_storage.identifier).delete_all()

    @staticmethod
    def delete_compiled_dataset_shards_by_dataset_storage(dataset_storage: DatasetStorage) -> None:
        """
        Delete all compiled dataset shards by dataset storage.

        :param dataset_storage: Dataset storage containing the compiled dataset shards
        """
        logger.debug("Deleting all compiled dataset shards of storage `%s`", dataset_storage.id_)

        CompiledDatasetShardsRepo(dataset_storage.identifier).delete_all()

    @staticmethod
    def delete_all_entities_in_dataset_storage(dataset_storage: DatasetStorage) -> None:
        """
        Delete all the entities in a dataset storage.

        Includes:
         - Media
         - Datasets
         - Result sets
         - Pipeline
         - Compiled dataset shard
        and their related entities.

        :param dataset_storage: Dataset storage to delete
        """
        logger.debug("Deleting all entities in storage `%s`", dataset_storage.id_)

        DeletionHelpers.delete_media_entities_by_dataset_storage(dataset_storage=dataset_storage)
        DeletionHelpers.delete_pipeline_dataset_entities_by_dataset_storage(dataset_storage=dataset_storage)
        DeletionHelpers.delete_compiled_dataset_shards_by_dataset_storage(dataset_storage=dataset_storage)
        DeletionHelpers.delete_datasets_by_dataset_storage(dataset_storage=dataset_storage)

    ##################################
    # Model storage related entities #
    ##################################

    @staticmethod
    def delete_all_hyperparameters_by_model_storage(project: Project, model_storage_id: ID) -> None:
        """
        Delete all the hyperparameters in a model storage.

        :param project: The project with the hyperparameters to delete
        :param model_storage_id: ID of the model storage to delete
        """
        logger.debug("Deleting all hyper-parameters of model storage `%s`", model_storage_id)

        ConfigurableParametersRepo(project.identifier).delete_all_by_model_storage_id(model_storage_id)

    @staticmethod
    def delete_all_models_by_model_storage(model_storage_identifier: ModelStorageIdentifier) -> None:
        """
        Delete all the models in a model storage.

        :param model_storage_identifier: Identifier of the model storage containing the models to delete
        """
        logger.debug("Deleting all models of model storage `%s`", model_storage_identifier)

        ModelRepo(model_storage_identifier).delete_all()

    @staticmethod
    def delete_all_entities_in_model_storage(project: Project, model_storage: ModelStorage) -> None:
        """
        Delete all the entities in a model storage.

        Includes:
         - Models
         - Hyper-parameters
        and their related entities.

        :param project: The project with the model storage to delete
        :param model_storage: Model storage to delete
        """
        logger.debug("Deleting all entities in model storage `%s`", model_storage.id_)

        DeletionHelpers.delete_all_hyperparameters_by_model_storage(project=project, model_storage_id=model_storage.id_)
        DeletionHelpers.delete_all_models_by_model_storage(model_storage_identifier=model_storage.identifier)

    ######################################
    # Workspace storage related entities #
    ######################################

    @staticmethod
    def delete_all_label_schema_by_project(project_identifier: ProjectIdentifier) -> None:
        """
        Delete all the label schemas relative to a project.

        Cascades to:
         - Labels

        :param project_identifier: Identifier of the project relative to the label schemas to delete
        """
        logger.debug("Deleting all label schemas of project `%s`", project_identifier)

        label_schema_repo = LabelSchemaRepo(project_identifier)
        label_repo = LabelRepo(project_identifier)
        label_schemas = list(label_schema_repo.get_all())
        for schema in label_schemas:
            for label in schema.get_labels(include_empty=True):
                label_repo.delete_by_id(label.id_)
            label_schema_repo.delete_by_id(schema.id_)

    @staticmethod
    def delete_all_task_nodes_by_project(project_identifier: ProjectIdentifier) -> None:
        """
        Delete all the task nodes relative to a project.

        :param project_identifier: Identifier of the project with the tasks to delete
        """
        logger.debug("Deleting all task nodes of project `%s`", project_identifier)

        TaskNodeRepo(project_identifier).delete_all()

    @staticmethod
    def delete_all_active_model_states_by_project(project: Project) -> None:
        """
        Delete all the active model states relative to a project.

        :param project: Project whose active model states are to be deleted
        """
        logger.debug("Deleting all active model states of project `%s`", project.id_)

        active_model_state_repo = ActiveModelStateRepo(project.identifier)
        for task_node in project.tasks:
            active_model_state_repo.delete_by_task_node_id(task_node.id_)

    @staticmethod
    def delete_all_configurable_parameters_by_project(project: Project) -> None:
        """
        Delete all the configurable parameters relative to a project.

        :param project: Project whose configurable parameters are to be deleted
        """
        logger.debug("Deleting all configurable params of project `%s`", project.id_)

        ConfigurableParametersRepo(project.identifier).delete_all()

    @staticmethod
    def delete_all_model_test_results_by_project(project: Project, dataset_storage: DatasetStorage) -> None:
        """
        Delete all the model test results relative to a project.

        :param project: Project whose model test results are to be deleted
        :param dataset_storage: Dataset Storage which holds the test results
        """
        logger.debug("Deleting all model test results of project `%s`", project.id_)

        model_test_results = ModelTestResultRepo(project.identifier).get_all_by_dataset_storage_id(dataset_storage.id_)
        for model_test_result in model_test_results:
            DeletionHelpers.delete_model_test_result(
                project_identifier=project.identifier, model_test_result=model_test_result
            )

    @staticmethod
    def delete_all_entities_in_project(project: Project) -> None:
        """
        Delete all the entities in a project.

        Includes:
         - Dataset storage
         - Model storages
         - Active model states
         - Label schemas
         - Task nodes
         - Operations
         - Component parameters
         - Model test results
         - Evaluation result
        and their related entities.

        :param project: Project whose entities are to be deleted
        """
        logger.debug("Deleting all entities in project `%s`", project.id_)

        model_storage_repo = ModelStorageRepo(project.identifier)
        for task_node in project.tasks:
            task_model_storages = model_storage_repo.get_by_task_node_id(task_node.id_)
            for model_storage in task_model_storages:
                DeletionHelpers.delete_all_entities_in_model_storage(project=project, model_storage=model_storage)
                model_storage_repo.delete_by_id(model_storage.id_)

        for dataset_storage in project.get_dataset_storages():
            DeletionHelpers.delete_all_model_test_results_by_project(project=project, dataset_storage=dataset_storage)
            DeletionHelpers.delete_dataset_storage_by_id(dataset_storage.identifier)

        DeletionHelpers.delete_all_active_model_states_by_project(project=project)
        DeletionHelpers.delete_all_label_schema_by_project(project.identifier)
        DeletionHelpers.delete_all_task_nodes_by_project(project.identifier)
        DeletionHelpers.delete_all_configurable_parameters_by_project(project=project)
        DeletionHelpers.delete_evaluation_result_entities_by_project(project=project)

    @staticmethod
    def delete_project_by_id(project_id: ID) -> None:
        """
        Delete a project with all related entities and binaries.

        :param project_id: ID of project to delete
        """
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            return

        DeletionHelpers.delete_all_entities_in_project(project=project)
        ProjectRepo().delete_by_id(project.id_)

    @staticmethod
    def delete_dataset_storage_by_id(dataset_storage_identifier: DatasetStorageIdentifier) -> None:
        """
        Delete dataset storage with all related entities and binaries

        :param dataset_storage_identifier: Identifier of dataset storage to delete
        """
        project_identifier = ProjectIdentifier(
            workspace_id=dataset_storage_identifier.workspace_id,
            project_id=dataset_storage_identifier.project_id,
        )
        ds_repo = DatasetStorageRepo(project_identifier)
        dataset_storage = ds_repo.get_by_id(dataset_storage_identifier.dataset_storage_id)
        if isinstance(dataset_storage, NullDatasetStorage):
            logger.warning(
                f"Dataset storage with id '{dataset_storage_identifier}' not found.Dataset storage deletion skipped."
            )
            return

        DeletionHelpers.delete_all_entities_in_dataset_storage(dataset_storage=dataset_storage)
        ds_repo.delete_by_id(dataset_storage_identifier.dataset_storage_id)

    @staticmethod
    def delete_models_by_base_model_id(
        project_id: ID,
        model_storage_id: ID,
        base_model_id: ID,
    ) -> None:
        """
        Deletes the all models based on the trained revision model ID (aka the base model ID).

        :param project_id: The ID of the project
        :param model_storage_id: The ID of the model storage
        :param base_model_id: The ID of the trained base model
        """
        workspace_id = CTX_SESSION_VAR.get().workspace_id
        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=workspace_id,
            project_id=project_id,
            model_storage_id=model_storage_id,
        )
        model_repo = ModelRepo(model_storage_identifier)
        base_model = model_repo.get_by_id(base_model_id)
        all_model_ids = model_repo.get_all_equivalent_model_ids(base_model)
        for model_id in all_model_ids:
            model_repo.delete_by_id(model_id)
        logger.info("Deleted models: %s.", all_model_ids)

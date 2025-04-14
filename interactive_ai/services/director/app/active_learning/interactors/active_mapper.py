# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the 'mapper' component for Active Learning"""

import contextvars
import logging
from collections.abc import Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from typing import cast

import numpy as np

from active_learning.entities.active_manager import PipelineActiveManager
from active_learning.utils.exceptions import (
    ActiveLearningDatasetNotFound,
    ActiveLearningModelNotFound,
    FeatureVectorsNotFound,
    IncorrectDatasetUsage,
    InvalidFeatureVectors,
)

from geti_telemetry_tools import unified_tracing
from geti_types import ID, DatasetStorageIdentifier, MediaIdentifierEntity, ProjectIdentifier, Singleton
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.datasets import Dataset, NullDataset
from sc_sdk.entities.metadata import FloatMetadata
from sc_sdk.entities.model import Model, NullModel
from sc_sdk.entities.model_storage import ModelStorageIdentifier
from sc_sdk.entities.subset import Subset
from sc_sdk.entities.tensor import Tensor
from sc_sdk.repos import DatasetRepo, MetadataRepo, ModelRepo

logger = logging.getLogger(__name__)


# NOTE: only 1 worker enabled at the moment to prevent race conditions between the
#  creation/update/deletion operations on active learning entities. More workers are
#  allowed provided that a per-project locking mechanism is added.
#  Another option is to implement multi-threading at the event consumer level.
DEFAULT_ACTIVE_MAPPER_WORKERS = 1

# This is the hard-coded name that OTX tasks assign to 'representation vector' Tensor
REPRESENTATION_VECTOR_TENSOR_NAME = "representation_vector"

# Data loading is constrained by sampling training dataset items to prevent out-of-memory issues with large datasets.
# There is research efforts in improving the sampling methods as part of CVS-121862.
MAX_DATASET_SAMPLE_SIZE = 1000


class ActiveMapper(metaclass=Singleton):
    """
    The Active Mapper orchestrates the (re-)computation of active scores in
    an end-to-end fashion and commits the updated values to the database.

    It is designed to be a worker class whose routine is carried out in a
    dedicated thread/process, so to run asynchronously w.r.t. the other workflows
    without blocking them.

    The mapper exploits the methods exposed by
    :func:`active_learning.entities.active_manager.TaskActiveManager` and
    :func:`active_learning.entities.active_manager.PipelineActiveManager`
    """

    def __init__(self, num_workers: int = DEFAULT_ACTIVE_MAPPER_WORKERS) -> None:
        # TODO after upgrading to Python 3.9+, set flag 'cancel_futures=True'
        self._executor = ThreadPoolExecutor(
            max_workers=num_workers,
            thread_name_prefix="active_mapper_worker",
        )

    @staticmethod
    @unified_tracing
    def _get_active_manager(workspace_id: ID, project_id: ID, dataset_storage_id: ID) -> PipelineActiveManager:
        return PipelineActiveManager(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
        )

    @staticmethod
    @unified_tracing
    def _load_model(project_identifier: ProjectIdentifier, model_storage_id: ID, model_id: ID) -> Model:
        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=project_identifier.workspace_id,
            project_id=project_identifier.project_id,
            model_storage_id=model_storage_id,
        )
        model_repo = ModelRepo(model_storage_identifier)
        model = model_repo.get_by_id(model_id)
        if isinstance(model, NullModel):
            logger.error("Missing active learning model `%s`", model_id)
            raise ActiveLearningModelNotFound(model_id=model_id)
        return model

    @staticmethod
    @unified_tracing
    def __load_dataset(dataset_storage_identifier: DatasetStorageIdentifier, dataset_id: ID) -> Dataset:
        dataset_repo = DatasetRepo(dataset_storage_identifier)
        dataset = dataset_repo.get_by_id(dataset_id)
        if isinstance(dataset, NullDataset):
            logger.error("Missing active learning dataset `%s`", dataset_id)
            raise ActiveLearningDatasetNotFound(dataset_id=dataset_id)
        return dataset

    @staticmethod
    @unified_tracing
    def _load_unseen_datasets_and_metadata(
        dataset_storage_identifier: DatasetStorageIdentifier,
        unannotated_dataset_with_predictions_id: ID,
    ) -> tuple[Dataset, np.ndarray]:
        """
        :return: Tuple (unseen dataset with predictions, feature vectors of unseen dataset)
        """
        unseen_dataset_with_predictions = ActiveMapper.__load_dataset(
            dataset_storage_identifier, unannotated_dataset_with_predictions_id
        )
        unseen_features = ActiveMapper._extract_features_from_dataset(
            dataset_items=tuple(unseen_dataset_with_predictions)
        )

        # There must be one feature vector for each item
        if len(unseen_dataset_with_predictions) != len(unseen_features):
            logger.error(
                "Mismatching length between dataset (ID=`%s`, len=%d) and its feature vectors (len=%d)",
                unseen_dataset_with_predictions.id_,
                len(unseen_dataset_with_predictions),
                len(unseen_features),
            )
            raise InvalidFeatureVectors

        # Feature vectors must not contain NaN values
        if np.isnan(unseen_features).any():
            logger.error(f"Feature vectors contain NaN values: {unseen_features}")
            raise InvalidFeatureVectors

        # Features must not be all duplicates (check only a few items for efficiency)
        if len(unseen_features) > 1:  # more than 1 sample
            all_duplicates: bool = (unseen_features[:10, :] == unseen_features[0]).all()
            if all_duplicates:
                logger.error(f"Embeddings are all the same: {unseen_features}")
                raise InvalidFeatureVectors

        return unseen_dataset_with_predictions, unseen_features

    @staticmethod
    @unified_tracing
    def _load_seen_datasets_and_metadata(
        dataset_storage_identifier: DatasetStorageIdentifier,
        annotated_dataset_id: ID,
        train_dataset_with_predictions_id: ID,
    ) -> tuple[tuple[DatasetItem, ...], tuple[DatasetItem, ...], np.ndarray]:
        """
        :return: Tuple (
            seen dataset items with annotations,
            seen dataset items with predictions,
            feature vectors of seen dataset
        )
        """
        dataset_repo = DatasetRepo(dataset_storage_identifier)
        # Bound the dataset size by sampling a constant number of items
        annotation_dataset_items = dataset_repo.sample(
            dataset_id=annotated_dataset_id, size=MAX_DATASET_SAMPLE_SIZE, subset=Subset.TRAINING
        )
        media_identifiers = [item.media_identifier for item in annotation_dataset_items]

        prediction_dataset_items = tuple(
            dataset_repo.get_items_by_dataset_and_media_identifiers(
                dataset_id=train_dataset_with_predictions_id, media_identifiers=media_identifiers
            )
        )
        seen_features = ActiveMapper._extract_features_from_dataset(dataset_items=prediction_dataset_items)

        # The datasets with annotations and predictions must have the same length
        if len(annotation_dataset_items) != len(prediction_dataset_items):
            logger.error(
                "Mismatching length between the seen dataset with predictions "
                "(len=%d, sampled from dataset with ID=`%s`) and its equivalent annotated one "
                "(len=%d, sampled from dataset with ID=`%s`)",
                len(prediction_dataset_items),
                train_dataset_with_predictions_id,
                len(annotation_dataset_items),
                annotated_dataset_id,
            )
            raise IncorrectDatasetUsage

        # There must be one feature vector for each item
        if len(prediction_dataset_items) != len(seen_features):
            logger.error(
                "Mismatching length between dataset (len=%d, sampled from dataset with ID=`%s`) "
                "and its feature vectors (len=%d)",
                len(prediction_dataset_items),
                train_dataset_with_predictions_id,
                len(seen_features),
            )
            raise InvalidFeatureVectors

        # Feature vectors must not contain NaN values
        if np.isnan(seen_features).any():
            logger.error(f"Feature vectors contain NaN values: {seen_features}")
            raise InvalidFeatureVectors

        return (
            annotation_dataset_items,
            prediction_dataset_items,
            seen_features,
        )

    @staticmethod
    def _extract_feature_vector_from_dataset_item(item: DatasetItem) -> np.ndarray:
        try:
            repr_vector_metadata_item = next(
                m for m in item.get_metadata() if m.data.name == REPRESENTATION_VECTOR_TENSOR_NAME
            )
        except StopIteration as e:
            logger.error("Missing feature vector for dataset item `%s`", item.id_)
            raise FeatureVectorsNotFound from e

        repr_vector_tensor = cast("Tensor", repr_vector_metadata_item.data)
        return repr_vector_tensor.numpy

    @staticmethod
    @unified_tracing
    def _extract_features_from_dataset(dataset_items: Sequence[DatasetItem]) -> np.ndarray:
        """
        Given a dataset of N items, each associated to an M-sized feature vector
        ('representation_vector' metadata), extract the NxM numpy array of features.

        It supports representation vectors of different shapes. Indeed, there can be
        discrepancies in how the OTX inference tasks extract and reduce the last
        convolutional block with shape [B,C,H,W].
        Note that B=1 (batch size) since a metadata item is relative to a single image.
        On the contrary, H,W != 1 in any realistic setting.
        Examples:
         - 1D: task squeezed B, avg-pooled over [H,W] and squeezed again
         - 2D: task avg-pooled over [H,W] and squeezed one dimension
         - 3D: task avg-pooled over [H,W] but did not squeeze
         - 4D: task did not avg-pool or squeeze
        :param dataset_items: Dataset items for which to get representation matrix
        :raises: AttributeError if no metadata item with name 'representation_vector'
            is found in any items of the dataset
        :return: NxM array containing a feature vector for each item
        """
        feature_vectors = [ActiveMapper._extract_feature_vector_from_dataset_item(item) for item in dataset_items]
        if any(v.ndim > 4 for v in feature_vectors):
            raise NotImplementedError("Can't interpret feature vectors with 4+ dims")

        pre_squeezed = [v.squeeze() for v in feature_vectors]
        if any(v.ndim > 1 for v in pre_squeezed):
            logger.warning(
                "Some feature vectors have 2+ axes with length greater than one; "
                "this could be a symptom that the inference task does not average pool "
                "on the spatial dims. Applying avg-pool on the last 2 dims as fallback."
            )
            # assume the spatial dims (H,W) last
            averaged = [v.mean(axis=(-2, -1)) if v.ndim >= 2 else v for v in pre_squeezed]
            post_squeezed = [v.squeeze() for v in averaged]
        else:
            post_squeezed = pre_squeezed

        return np.vstack(post_squeezed)

    @staticmethod
    @unified_tracing
    def init_active_scores(
        workspace_id: ID,
        project_id: ID,
        dataset_storage_id: ID,
        media_identifiers: Sequence[MediaIdentifierEntity],
    ) -> None:
        """
        Given a list of media identifiers in a project, create and save default
        ActiveScore entities for them unless already existing.

        This method guarantees that the ActiveScore objects are created before
        it returns, but it can be slow especially if the list of identifiers is long.
        Check :func:`~init_active_scores_async` for an asynchronous non-blocking
        version of this function.

        :param workspace_id: ID of the workspace containing the project
        :param project_id: ID of the project containing the media
        :param dataset_storage_id: ID of the dataset storage containing the media
        :param media_identifiers: Identifiers of the media to create the scores for
        """
        active_manager = ActiveMapper._get_active_manager(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
        )
        active_manager.init_scores(media_identifiers=media_identifiers)

    def init_active_scores_async(
        self,
        workspace_id: ID,
        project_id: ID,
        dataset_storage_id: ID,
        media_identifiers: Sequence[MediaIdentifierEntity],
    ) -> Future:
        """
        Asynchronous (non-blocking) version of :func:`~init_active_scores`.

        This method is relatively fast, but it does not guarantee that the
        ActiveScore objects are created before it returns.

        :param workspace_id: ID of the workspace containing the project
        :param project_id: ID of the project containing the media
        :param dataset_storage_id: ID of the dataset storage containing the media
        :param media_identifiers: Identifiers of the media to create the scores for
        :return: Future object associated to the execution of the wrapped method
        """
        current_context = contextvars.copy_context()
        return self._executor.submit(
            current_context.run,
            ActiveMapper.init_active_scores,
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            media_identifiers=media_identifiers,  # type: ignore
        )

    @staticmethod
    def __update_active_scores(  # noqa: PLR0913
        workspace_id: ID,
        project_id: ID,
        dataset_storage_id: ID,
        task_node_id: ID,
        model_storage_id: ID,
        model_id: ID,
        annotated_dataset_id: ID,
        train_dataset_with_predictions_id: ID,
        unannotated_dataset_with_predictions_id: ID,
    ) -> None:
        """See ActiveMapper.update_active_scores for documentation"""

        # Load the active manager
        active_manager = ActiveMapper._get_active_manager(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
        )

        # Load the model
        model = ActiveMapper._load_model(
            project_identifier=active_manager.project_identifier,
            model_storage_id=model_storage_id,
            model_id=model_id,
        )

        # Load the unseen datasets and metadata
        (
            unseen_dataset_with_predictions,
            unseen_features,
        ) = ActiveMapper._load_unseen_datasets_and_metadata(
            dataset_storage_identifier=active_manager.dataset_storage_identifier,
            unannotated_dataset_with_predictions_id=unannotated_dataset_with_predictions_id,
        )

        # Load the seen datasets and metadata
        (
            seen_dataset_items_with_annotations,
            seen_dataset_items_with_predictions,
            seen_features,
        ) = ActiveMapper._load_seen_datasets_and_metadata(
            dataset_storage_identifier=active_manager.dataset_storage_identifier,
            annotated_dataset_id=annotated_dataset_id,
            train_dataset_with_predictions_id=train_dataset_with_predictions_id,
        )

        # Find the affected media (all the ones in the unannotated datasets)
        affected_media_identifiers = {item.media_identifier for item in unseen_dataset_with_predictions}

        # Fetch the current active scores for the affected media
        active_scores = tuple(
            active_manager.get_scores_by_media_identifiers(
                media_identifiers=affected_media_identifiers,
            ).values()
        )

        # Recompute and save the active scores
        active_manager.update_scores(
            scores=active_scores,
            unseen_dataset_with_predictions_by_task={task_node_id: unseen_dataset_with_predictions},
            seen_dataset_items_with_predictions_by_task={task_node_id: seen_dataset_items_with_predictions},
            seen_dataset_items_with_annotations_by_task={task_node_id: seen_dataset_items_with_annotations},
            unseen_dataset_features_by_task={task_node_id: unseen_features},
            seen_dataset_features_by_task={task_node_id: seen_features},
            model_by_task={task_node_id: model},
            save=True,
        )

    @staticmethod
    @unified_tracing
    def update_active_scores(  # noqa: PLR0913
        workspace_id: ID,
        project_id: ID,
        dataset_storage_id: ID,
        task_node_id: ID,
        model_storage_id: ID,
        model_id: ID,
        annotated_dataset_id: ID,
        train_dataset_with_predictions_id: ID,
        unannotated_dataset_with_predictions_id: ID,
    ) -> None:
        """
        Update the active scores for the media of an inferred unannotated dataset,
        based on the metadata generated during inference for this dataset and the
        annotated one too.

        The active scores are pulled from and saved to the database.

        This method guarantees that the ActiveScore objects are updated before
        it returns, but it can be slow especially if the datasets are large.
        Check :func:`~update_active_scores_async` for an asynchronous version
        of this function.

        :param workspace_id: ID of the workspace containing the project
        :param project_id: ID of the project containing the datasets
        :param dataset_storage_id: ID of the dataset storage containing the media
        :param task_node_id: ID of the task node on which inference was executed
        :param model_storage_id: ID of the storage containing the model used
            to generate the predictions
        :param model_id: IDs of the model used to generate the predictions
        :param annotated_dataset_id: ID of the user annotated dataset on which
            the task was trained
        :param train_dataset_with_predictions_id: ID of the dataset containing
            predictions generated by the trained model on the training dataset
            (training subset only)
        :param unannotated_dataset_with_predictions_id: ID of the dataset containing
            predictions generated by the trained model on unlabeled data
        """
        try:
            ActiveMapper.__update_active_scores(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                task_node_id=task_node_id,
                model_storage_id=model_storage_id,
                model_id=model_id,
                annotated_dataset_id=annotated_dataset_id,
                train_dataset_with_predictions_id=train_dataset_with_predictions_id,
                unannotated_dataset_with_predictions_id=unannotated_dataset_with_predictions_id,
            )
        except Exception:
            logger.exception("Error while updating the active scores")
        finally:
            # Delete the AL metadata after consuming it.
            # Assumption: AL scores are recomputed faster than a training cycle, so
            # it is safe to delete all tensors from all datasets in the storage because
            # there are no queued requests to recompute AL scores on this storage when
            # this handler instance completes.
            # Note: this is an optimization because deleting all binaries at a specific
            # location of the object storage is much faster than deleting them
            # one-by-one after filtering by dataset id.
            ActiveMapper.delete_active_learning_metadata_by_dataset_storage(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
            )

    def update_active_scores_async(  # noqa: PLR0913
        self,
        workspace_id: ID,
        project_id: ID,
        dataset_storage_id: ID,
        task_node_id: ID,
        model_storage_id: ID,
        model_id: ID,
        annotated_dataset_id: ID,
        train_dataset_with_predictions_id: ID,
        unannotated_dataset_with_predictions_id: ID,
    ) -> Future:
        """
        Asynchronous (non-blocking) version of :func:`~update_active_scores`.

        This method is relatively fast, but it does not guarantee that the
        ActiveScore objects are updated before it returns.

        :param workspace_id: ID of the workspace containing the project
        :param project_id: ID of the project containing the datasets
        :param dataset_storage_id: ID of the dataset storage containing the media
        :param task_node_id: ID of the task node on which inference was executed
        :param model_storage_id: ID of the storage containing the model used
            to generate the predictions
        :param model_id: IDs of the model used to generate the predictions
        :param annotated_dataset_id: ID of the user annotated dataset on which
            the task was trained
        :param train_dataset_with_predictions_id: ID of the dataset containing
            predictions generated by the trained model on the training dataset
            (training subset only)
        :param unannotated_dataset_with_predictions_id: ID of the dataset containing
            predictions generated by the trained model on unlabeled data
        :return: Future object associated to the execution of the wrapped method
        """
        current_context = contextvars.copy_context()
        return self._executor.submit(
            current_context.run,
            ActiveMapper.update_active_scores,
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            task_node_id=task_node_id,
            model_storage_id=model_storage_id,
            model_id=model_id,
            annotated_dataset_id=annotated_dataset_id,
            train_dataset_with_predictions_id=train_dataset_with_predictions_id,
            unannotated_dataset_with_predictions_id=unannotated_dataset_with_predictions_id,
        )

    @staticmethod
    @unified_tracing
    def remove_media(
        workspace_id: ID,
        project_id: ID,
        dataset_storage_id: ID,
        media_identifiers: Sequence[MediaIdentifierEntity] | None = None,
    ) -> None:
        """
        Remove one or more media from the scope of active learning.
        The removed media will no longer be suggested nor play any role in the
        computation of active scores and future suggestions.

        :param workspace_id: ID of the workspace containing the project
        :param project_id: ID of the project containing the media
        :param dataset_storage_id: ID of the dataset storage containing the media
        :param media_identifiers: Identifiers of the media to remove;
            if None, all the media in the dataset storage are selected
        """
        active_manager = ActiveMapper._get_active_manager(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
        )
        active_manager.remove_media(media_identifiers=media_identifiers)

    def remove_media_async(
        self,
        workspace_id: ID,
        project_id: ID,
        dataset_storage_id: ID,
        media_identifiers: Sequence[MediaIdentifierEntity] | None = None,
    ) -> Future:
        """
        Asynchronous (non-blocking) version of :func:`~remove_media`.

        This method is relatively fast, but it does not guarantee that the
        ActiveScore and ActiveSuggestion objects are removed before it returns.

        :param workspace_id: ID of the workspace containing the project
        :param project_id: ID of the project containing the media
        :param dataset_storage_id: ID of the dataset storage containing the media
        :param media_identifiers: Identifiers of the media to remove;
            if None, all the media in the dataset storage are selected
        :return: Future object associated to the execution of the wrapped method
        """
        current_context = contextvars.copy_context()
        return self._executor.submit(
            current_context.run,
            ActiveMapper.remove_media,
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            media_identifiers=media_identifiers,  # type: ignore
        )

    @staticmethod
    def delete_active_learning_metadata_by_dataset_storage(
        workspace_id: ID,
        project_id: ID,
        dataset_storage_id: ID,
    ) -> None:
        """
        Delete all the active learning metadata in a given dataset storage

        The metadata includes:
         - probabilities (Tensor)
         - representation vectors (Tensor)
         - active score floats (FloatMetadata)

        :param workspace_id: ID of the workspace containing the project
        :param project_id: ID of the project containing the dataset storage
        :param dataset_storage_id: ID of the dataset storage containing the tensors
        """
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
        )
        metadata_repo = MetadataRepo(dataset_storage_identifier)
        # Delete tensors: representation vectors and probabilities
        metadata_repo.delete_all_by_type(metadata_type=Tensor)
        # Delete active score floats
        metadata_repo.delete_all_by_type(metadata_type=FloatMetadata)

    def stop(self) -> None:
        """
        Stop the active mapper.

        When stopped, the active mapper will reject new workload requests.
        """
        self._executor.shutdown(wait=False)

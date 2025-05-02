# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the BaseActiveManager"""

import abc
import logging
from collections.abc import Callable, Iterator, Sequence
from functools import partial
from queue import PriorityQueue
from typing import Generic

import numpy as np

from active_learning.entities import ActiveScore, ActiveScoreSuggestionInfo, ActiveSuggestion
from active_learning.entities.active_learning_config import ActiveScoreReductionFunction, TActiveLearningConfig
from active_learning.storage.repos import ActiveScoreRepo, ActiveSuggestionRepo

from geti_fastapi_tools.exceptions import DatasetStorageNotFoundException, ProjectNotFoundException
from geti_telemetry_tools import unified_tracing
from geti_types import (
    ID,
    DatasetStorageIdentifier,
    ImageIdentifier,
    MediaIdentifierEntity,
    ProjectIdentifier,
    VideoFrameIdentifier,
    VideoIdentifier,
)
from iai_core_py.entities.dataset_storage import DatasetStorage, NullDatasetStorage
from iai_core_py.entities.project import NullProject, Project
from iai_core_py.entities.task_node import TaskNode
from iai_core_py.repos import DatasetStorageRepo, ProjectRepo, VideoRepo
from iai_core_py.services import ModelService
from iai_core_py.utils.iteration import grouper
from iai_core_py.utils.type_helpers import SequenceOrSet

logger = logging.getLogger(__name__)


class BaseActiveManager(Generic[TActiveLearningConfig], metaclass=abc.ABCMeta):  # type: ignore[misc]
    """
    Abstract base class for the active manager.

    It contains common functionalities for the active managers and abstract methods too.

    The active manager is designed to be stateless across requests: this class
    (actually, its concrete implementation) should be instantiated for each
    create/update operation and destroyed at the end. No state must persist in-memory
    after each request is served.

    :param workspace_id: ID of the workspace containing the project
    :param project_id: ID of the project containing the dataset storage
    :param dataset_storage_id: ID of the dataset storage containing the media
    """

    def __init__(
        self,
        workspace_id: ID,
        project_id: ID,
        dataset_storage_id: ID,
    ) -> None:
        self.workspace_id = workspace_id
        self.project_id = project_id
        self.dataset_storage_id = dataset_storage_id

        # Entities are loaded lazily when needed for performance reasons.
        # They are then cached per-request (same lifetime of the active manager)
        self.__project: Project | None = None
        self.__dataset_storage: DatasetStorage | None = None

    @property
    def project_identifier(self) -> ProjectIdentifier:
        return ProjectIdentifier(workspace_id=self.workspace_id, project_id=self.project_id)

    @property
    def dataset_storage_identifier(self) -> DatasetStorageIdentifier:
        return DatasetStorageIdentifier(
            workspace_id=self.workspace_id,
            project_id=self.project_id,
            dataset_storage_id=self.dataset_storage_id,
        )

    def get_project(self) -> Project:
        """
        Get the Project entity relative to the active manager.
        If not already cached, it is loaded from the repo.

        :return: Project
        :raises: ProjectNotFoundException if the project cannot be found
        """
        if self.__project is None:
            project_repo: ProjectRepo = ProjectRepo()
            project = project_repo.get_by_id(self.project_id)
            if isinstance(project, NullProject):
                raise ProjectNotFoundException(self.project_id)
            self.__project = project
        return self.__project

    def get_dataset_storage(self) -> DatasetStorage:
        """
        Get the DatasetStorage entity relative to the active manager.
        If not already cached, it is loaded from the repo.

        :return: DatasetStorage
        :raises: DatasetStorageNotFoundException if the dataset storage cannot be found
        """
        if self.__dataset_storage is None:
            dataset_storage_repo = DatasetStorageRepo(self.project_identifier)
            dataset_storage = dataset_storage_repo.get_by_id(self.dataset_storage_id)
            if isinstance(dataset_storage, NullDatasetStorage):
                raise DatasetStorageNotFoundException(self.dataset_storage_id)
            self.__dataset_storage = dataset_storage
        return self.__dataset_storage

    def get_trainable_task_nodes(self) -> tuple[TaskNode, ...]:
        """
        Get the trainable TaskNode entities relative to the active manager project.
        If the project is not already cached, it is loaded from the repo.

        :return: Tuple of TaskNode
        """
        return tuple(self.get_project().get_trainable_task_nodes())

    @abc.abstractmethod
    def get_configuration(self) -> TActiveLearningConfig:
        """
        Get the configurable parameters for the active manager
        If not already cached, it is loaded from the repo.

        :return: ActiveLearningConfig
        """

    @staticmethod
    def reduce_fn_enum_to_callable(
        reduce_fn_enum: ActiveScoreReductionFunction,
    ) -> Callable[[Sequence[float]], float]:
        """
        Get the reduction function (callable) given its name

        :param reduce_fn_enum: ActiveScoreReductionFunction to map
        :return: Function to reduce a sequence of floats to a single one
        :raises: ValueError if the function is not recognized
        """

        def reduce_fn_template(values: Sequence[float], fn: Callable) -> float:
            if not values:
                return 1.0
            return fn(values)

        if reduce_fn_enum == ActiveScoreReductionFunction.MIN:
            return partial(reduce_fn_template, fn=np.nanmin)
        if reduce_fn_enum == ActiveScoreReductionFunction.MEAN:
            return partial(reduce_fn_template, fn=np.nanmean)
        if reduce_fn_enum == ActiveScoreReductionFunction.MAX:
            return partial(reduce_fn_template, fn=np.nanmax)
        raise ValueError(f"Unsupported intra-task reduce function {reduce_fn_enum}")

    @unified_tracing
    def _get_previously_suggested_media(self) -> tuple[MediaIdentifierEntity, ...]:
        """
        Get the list of media that have been already suggested to the user by the
        active manager, to avoid suggesting them twice.
        :return: Tuple containing the identifiers of the suggested media
        """
        repo = ActiveSuggestionRepo(
            dataset_storage_identifier=self.dataset_storage_identifier,
        )
        return repo.get_all_media_identifiers()

    @abc.abstractmethod
    def _get_unannotated_media_identifiers(self) -> list[MediaIdentifierEntity]:
        """
        Find unannotated media (at project/task level, depending on the active manager).

        :return: Tuple containing the identifiers of the unannotated media.
        """

    @unified_tracing
    def _get_unannotated_non_suggested_media_identifiers(
        self,
    ) -> Iterator[MediaIdentifierEntity]:
        """
        Find the unannotated non-suggested media.
        :return: Tuple containing the identifiers of the unannotated non-suggested media
        """
        suggested_media = set(self._get_previously_suggested_media())
        unannotated_media = self._get_unannotated_media_identifiers()
        unannotated_media_chunks = grouper(unannotated_media)
        for unannotated_media_chunk in unannotated_media_chunks:
            unannotated_non_suggested_media = set(unannotated_media_chunk) - suggested_media
            yield from unannotated_non_suggested_media

    @unified_tracing
    def _get_best_candidates_impl(
        self,
        candidates: Sequence[MediaIdentifierEntity],
        size: int,
        task_node_id: ID | None = None,
        models_ids: Sequence[ID] | None = None,
        inferred_only: bool = False,
    ) -> tuple[ActiveScoreSuggestionInfo, ...]:
        """
        Implementation of _get_best_candidates, shared between the active managers.
        The 'task_node_id' parameter differentiates between per-project and per-task AL.
        :param candidates: Identifiers of the media to sample the best candidates from
        :param size: Maximum size of the output candidates pool
        :param task_node_id: Optional, task node whose active scores should be used
        :param models_ids: Optional, if specified prioritize the media inferred by
            one of the models in the list.
        :param inferred_only: If True, exclude the media with a default active score
            (i.e. not updated based on the results of an inference).
        :return: Tuple of at most 'size' elements, where each element is an
            ActiveScoreSuggestionInfo corresponding to the selected media.
            The list is sorted by score (better/lower score first).
        """
        active_score_repo = ActiveScoreRepo(self.dataset_storage_identifier)
        # Find the top-K candidates based on the active score (per-task or per-project)
        return active_score_repo.find_best_candidates(
            candidate_media=candidates,
            size=size,
            task_node_id=task_node_id,
            models_ids=models_ids,
            inferred_only=inferred_only,
        )

    @abc.abstractmethod
    def _get_best_candidates(
        self,
        candidates: Sequence[MediaIdentifierEntity],
        size: int,
        models_ids: Sequence[ID] | None = None,
    ) -> tuple[ActiveScoreSuggestionInfo, ...]:
        """
        Get a pool of media that are the best candidates to be suggested.

        Specifically, this method builds a pool of at most 'size' elements chosen among
        the not-already-suggested unannotated media.
        Items with the lowest aggregate active score are prioritized.

        :param candidates: Identifiers of the media to sample the best candidates from
        :param size: Maximum size of the output candidates pool
        :param models_ids: Optional, if specified prioritize the media inferred by
            one of the models in the list.
        :return: Tuple of at most 'size' elements, where each element is an
            ActiveScoreSuggestionInfo corresponding to the selected media.
            The list is sorted by score (better/lower score first).
        """

    @unified_tracing
    def reset_suggestions(self) -> None:
        """
        Reset the state of previous suggestions so that the media can be suggested again
        """
        logger.info(
            "Resetting the active suggestions of project `%s` in workspace `%s`",
            self.project_id,
            self.workspace_id,
        )
        ActiveSuggestionRepo(self.dataset_storage_identifier).delete_all()

    @unified_tracing
    def get_suggestions(self, size: int) -> tuple[ActiveScoreSuggestionInfo, ...]:
        """
        Get suggestions from the active manager, i.e. a new active set.
        The suggestions include the best media (presumably) that are unannotated
        and have not been previously suggested. Priority is given to media whose active
        scores have been actually computed over the ones with default values.
        Note: this function does not record the new suggestions (it is up to the caller)
        so calling it twice in a row will generally output the same active set.

        :param size: Maximum size of the output candidates pool
        :return: Active set as tuple of at most 'size' elements, where each element
            is an ActiveScoreSuggestionInfo corresponding to the selected media.
        """
        active_model_id_per_task = {
            task_node.id_: ModelService.get_inference_active_model_id(
                project_identifier=self.project_identifier,
                task_node_id=task_node.id_,
            )
            for task_node in self.get_trainable_task_nodes()
        }
        active_models_ids = [model_id for model_id in active_model_id_per_task.values() if model_id != ID()]

        # Pick the best non-suggested media
        candidates_iter = self._get_unannotated_non_suggested_media_identifiers()
        candidates_chunks = grouper(candidates_iter)
        # store top k candidates with a priority queue
        pq: PriorityQueue = PriorityQueue()
        for candidates_chunk in candidates_chunks:
            best_from_list = self._get_best_candidates(
                candidates=candidates_chunk,
                size=size,
                models_ids=active_models_ids,
            )
            for candidate_info in best_from_list:
                if pq.qsize() >= size:
                    _, worst_candidate = pq.get()
                    candidate_info = min([worst_candidate, candidate_info], key=lambda x: x.score)  # noqa: PLW2901
                # score negated because we want to keep the best candidates (lowest score)
                pq.put((-candidate_info.score, candidate_info))

        candidates_info = [info for _, info in pq.queue]

        num_non_inferred_candidates = sum(c.score == 1.0 for c in candidates_info)
        num_inferred_candidates = len(candidates_info) - num_non_inferred_candidates
        logger.debug(
            "Detail of active suggestions for project `%s`: %d requested, %d inferred, %d non-inferred",
            self.project_id,
            size,
            num_inferred_candidates,
            num_non_inferred_candidates,
        )
        return tuple(candidates_info)

    @unified_tracing
    def init_scores(self, media_identifiers: Sequence[MediaIdentifierEntity]) -> None:
        """
        Create default active scores for the given media.

        For videos, active scores are created for its frames at 1 fps.

        :param media_identifiers: Media identifiers to create the scores for
        """
        active_score_repo = ActiveScoreRepo(self.dataset_storage_identifier)
        video_repo = VideoRepo(self.dataset_storage_identifier)

        # Normalize the request by replacing videos with the respective frames
        media_identifiers_resolved: set[MediaIdentifierEntity] = set()
        for media_identifier in media_identifiers:
            if isinstance(media_identifier, ImageIdentifier | VideoFrameIdentifier):
                media_identifiers_resolved.add(media_identifier)
            elif isinstance(media_identifier, VideoIdentifier):
                # for videos, consider one frame per second
                video = video_repo.get_by_id(media_identifier.media_id)
                for frame_index in range(0, video.total_frames, video.stride):
                    frame_identifier = VideoFrameIdentifier(video_id=video.id_, frame_index=frame_index)
                    media_identifiers_resolved.add(frame_identifier)
            else:
                raise ValueError(f"Unsupported media identifier `{media_identifier.media_type.value}`")

        # Create an active score for every resolved media identifier
        new_scores = [
            ActiveScore.make_default(
                id_=ActiveScoreRepo.generate_id(),
                media_identifier=media_identifier,
            )
            for media_identifier in media_identifiers_resolved
        ]
        active_score_repo.save_many(new_scores)

    @unified_tracing
    def get_scores_by_media_identifiers(
        self, media_identifiers: SequenceOrSet[MediaIdentifierEntity]
    ) -> dict[MediaIdentifierEntity, ActiveScore]:
        """
        Get the ActiveScore entities corresponding to the given media identifiers.

        Note: the output dict will not contain any entry for non-existing scores.

        :param media_identifiers: Media identifiers to get the scores for
        :return: Dict mapping each media identifier to the relative ActiveScore object
        """
        active_score_repo = ActiveScoreRepo(self.dataset_storage_identifier)
        return active_score_repo.get_by_media_identifiers(media_identifiers)

    @unified_tracing
    def mark_as_suggested(
        self, suggested_media_info: Sequence[ActiveScoreSuggestionInfo], user_id: str, reason: str = ""
    ) -> None:
        """
        Mark a set of media as suggested to the user.

        :param suggested_media_info: Sequence containing information about the
            suggested media, including their media identifiers, scores and models.
        :param user_id: ID of the user to which the suggestions were presented
        :param reason: Reason why such items were chosen to be suggested
        """
        repo = ActiveSuggestionRepo(
            dataset_storage_identifier=self.dataset_storage_identifier,
        )
        suggestions = [
            ActiveSuggestion(
                id_=repo.generate_id(),
                media_identifier=media_info.media_identifier,
                score=media_info.score,
                models=media_info.models_ids,
                user=user_id,
                reason=reason,
            )
            for media_info in suggested_media_info
        ]
        repo.save_many(suggestions)

    @unified_tracing
    def remove_media(self, media_identifiers: Sequence[MediaIdentifierEntity] | None = None) -> None:
        """
        Remove one or more media from the scope of the active manager.
        The removed media will no longer be suggested nor play any role in the
        computation of active scores and future suggestions.

        For videos, delete all its frames.

        :param media_identifiers: Identifiers of the media to remove;
            if None, all the media in the dataset storage are selected
        """
        active_score_repo = ActiveScoreRepo(self.dataset_storage_identifier)
        active_suggestion_repo = ActiveSuggestionRepo(
            dataset_storage_identifier=self.dataset_storage_identifier,
        )
        if media_identifiers is not None:  # explicitly provided list of media
            for media_identifier in media_identifiers:
                active_score_repo.delete_by_media_identifier(media_identifier)
                active_suggestion_repo.delete_by_media_identifier(media_identifier)
        else:
            active_score_repo.delete_all()
            active_suggestion_repo.delete_all()

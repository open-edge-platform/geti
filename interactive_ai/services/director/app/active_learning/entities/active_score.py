# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

"""This module implements the ActiveScore entity and its related business logic"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from geti_types import ID, MediaIdentifierEntity, NullMediaIdentifier
from sc_sdk.entities.persistent_entity import PersistentEntity


class TaskActiveScore:
    """
    Active score aggregated at task node level.

    Lower active score values correspond to "more interesting" media from the AL PoV.
    In other words, media with lower scores are suggested first.

    :param score: Score value (float [0,1]) at task level
    :param model_id: ID of the model used to generate the score
    :param extractors_scores: Raw (before aggregation) scores from the extractors.
        Specifically, the dict maps an extractor name to its float [0,1] score.
    """

    def __init__(
        self,
        score: float = 1.0,
        model_id: ID = ID(),
        extractors_scores: dict[str, float] | None = None,
    ) -> None:
        self.score = score
        self.model_id = model_id
        self.extractors_scores: dict[str, float]
        if extractors_scores is not None:
            self.extractors_scores = extractors_scores
        else:
            self.extractors_scores = {}

    def __eq__(self, other: object):
        if not isinstance(other, TaskActiveScore):
            return False
        return (
            self.score == other.score
            and self.model_id == other.model_id
            and self.extractors_scores == other.extractors_scores
        )

    def __repr__(self) -> str:
        return (
            f"TaskActiveScore({self.score:.3f}, model_id={self.model_id}, extractors_scores={self.extractors_scores})"
        )

    def __str__(self) -> str:
        return f"{self.score:.3f}"


class ActiveScore(PersistentEntity):
    """
    Active score aggregated at pipeline level.

    Lower active score values correspond to "more interesting" media from the AL PoV.
    In other words, media with lower scores are suggested first.

    ActiveScore is meant to be unique per-media identifier; the entity ID is
    automatically determined through hashing from the media identifier.

    :param media_identifier: Media identifier the score refers to
    :param pipeline_score: Score value (float [0,1]) at pipeline level
    :param tasks_scores: Raw (before aggregation) scores from the tasks.
        Specifically, the dict maps each task node ID to its float [0,1] score.
    """

    def __init__(
        self,
        media_identifier: MediaIdentifierEntity,
        pipeline_score: float = 1.0,
        tasks_scores: dict[ID, TaskActiveScore] | None = None,
        ephemeral: bool = True,
    ) -> None:
        super().__init__(id_=media_identifier.as_id(), ephemeral=ephemeral)
        self.__media_identifier = media_identifier  # read-only because it affects id_
        self.pipeline_score = pipeline_score
        self.tasks_scores: dict[ID, TaskActiveScore]
        if tasks_scores is not None:
            self.tasks_scores = tasks_scores
        else:
            self.tasks_scores = {}

    @property
    def media_identifier(self) -> MediaIdentifierEntity:
        """Identifier of the media associated with this active score"""
        return self.__media_identifier

    def __eq__(self, other: object):
        # Value object: don't compare the ID
        if not isinstance(other, ActiveScore):
            return False
        return (
            self.media_identifier == other.media_identifier
            and self.pipeline_score == other.pipeline_score
            and self.tasks_scores == other.tasks_scores
        )

    def __str__(self) -> str:
        return f"{self.pipeline_score:.3f}, {self.media_identifier}"

    def __repr__(self) -> str:
        task_scores_repr = str({task_id: repr(task_score) for task_id, task_score in self.tasks_scores.items()})
        return (
            f"ActiveScore({self.pipeline_score:.3f}, media_identifier={self.media_identifier}, "
            f"tasks_scores={task_scores_repr})"
        )

    def refresh_tasks_scores(
        self,
        reduce_fns: dict[ID, Callable[[Sequence[float]], float]],
    ) -> None:
        """
        Recompute the per-task active scores by reducing the per-extractor scores.

        :param reduce_fns: Dict mapping task node IDs to the respective function
            to use for reducing the scores from its extractors.
            The scores will not be updated for the tasks that are not mapped.
        """
        for task_node_id, task_score in self.tasks_scores.items():
            if task_node_id not in reduce_fns:
                continue
            reduce_fn = reduce_fns[task_node_id]
            task_score.score = reduce_fn(tuple(task_score.extractors_scores.values()))

    def refresh_pipeline_score(
        self,
        reduce_fn: Callable[[Sequence[float]], float],
        refresh_tasks_scores: bool = True,
        tasks_reduce_fns: dict[ID, Callable[[Sequence[float]], float]] | None = None,
    ) -> None:
        """
        Recompute the pipeline (project) active score by reducing the per-task scores.

        :param reduce_fn: Function to use to reduce the scores from each task node
        :param refresh_tasks_scores: If True, it also recomputes the per-task scores
            before refreshing the pipeline one.
        :param tasks_reduce_fns: If 'refresh_task_score', mapping from the task node IDs
            to the respective reduction functions.
        """
        if refresh_tasks_scores:
            if tasks_reduce_fns is None:
                raise ValueError(
                    "The task aggregation function must be provided if the task scores are to be refreshed too."
                )
            self.refresh_tasks_scores(reduce_fns=tasks_reduce_fns)
        self.pipeline_score = reduce_fn([ts.score for ts in self.tasks_scores.values()])

    @staticmethod
    def make_default(
        id_: ID,  # noqa: ARG004
        media_identifier: MediaIdentifierEntity,
        task_nodes_ids: Sequence[ID] | None = None,
    ) -> "ActiveScore":
        """
        Factory method to create an ActiveScore with default values.

        :param id_: ID to assign to the new entity object
        :param media_identifier: Media identifier the score refers to
        :param task_nodes_ids: Optional, IDs of task nodes in the project; if provided,
            it will be used to initialize explicitly default task active scores.
        """
        tasks_scores: dict[ID, TaskActiveScore] = {}
        if task_nodes_ids is not None:
            tasks_scores = {task_node_id: TaskActiveScore() for task_node_id in task_nodes_ids}
        return ActiveScore(media_identifier=media_identifier, tasks_scores=tasks_scores)


class NullActiveScore(ActiveScore):
    """Representation of a not found ActiveScore"""

    def __init__(self) -> None:
        super().__init__(
            media_identifier=NullMediaIdentifier(),
            ephemeral=False,
        )

    def __str__(self) -> str:
        return "NullActiveScore()"

    def __repr__(self) -> str:
        return str(self)


@dataclass(order=True)
class ActiveScoreSuggestionInfo:
    """
    Restricted view of :class:`~ActiveScore` that includes only the information
    strictly needed to initialize a
    :class:`~active_learning.entities.ActiveSuggestion`

    This class is a convenient container of information, but it is not a first-class
    entity, and it cannot be persisted to the DB. The ordered property is useful since
    it makes this class compatible with standard sorting algorithms.

    :var media_identifier: Media identifier the score refers to
    :var score: Active score value used to determine the suggestion
    :var models_ids: Models involved in the determination of the score
    """

    media_identifier: MediaIdentifierEntity = field(compare=False)
    score: float
    models_ids: tuple[ID, ...] = field(compare=False)

"""This module implements the MediaScore entity"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from iai_core.entities.metrics import ScoreMetric
from iai_core.entities.persistent_entity import PersistentEntity

from geti_types import ID, MediaIdentifierEntity, NullMediaIdentifier


class MediaScore(PersistentEntity):
    """
    Entity used to represent score per-media and score per-media per-label

    :param id_: ID of the media score
    :param model_test_result_id: id of test result containing this media score
    :param media_identifier: media identifier of the media
    :param scores: set of score values
    :param annotated_label_ids: (optional) IDs of the user annotated labels for the media.
        - If empty set, the media does not have any user annotated labels
        - If None, existence of user annotated labels are unknown to this entity
    """

    def __init__(
        self,
        id_: ID,
        model_test_result_id: ID,
        media_identifier: MediaIdentifierEntity,
        scores: set[ScoreMetric],
        annotated_label_ids: set[ID] | None = None,
        ephemeral: bool = True,
    ) -> None:
        super().__init__(id_=id_, ephemeral=ephemeral)
        self._model_test_result_id = model_test_result_id
        self._media_identifier = media_identifier
        self._scores = scores
        self.annotated_label_ids = annotated_label_ids

    @property
    def model_test_result_id(self) -> ID:
        return self._model_test_result_id

    @property
    def media_identifier(self) -> MediaIdentifierEntity:
        return self._media_identifier

    @property
    def scores(self) -> set[ScoreMetric]:
        return self._scores

    def append_score(self, score: ScoreMetric) -> None:
        self._scores.add(score)

    def __repr__(self) -> str:
        return (
            f"MediaScore({self.id_}, test_result='{self.model_test_result_id}', "
            f"media_identifier='{self.media_identifier}', scores='{self.scores}', "
            f"annotated_label_ids='{self.annotated_label_ids}')"
        )


class NullMediaScore(MediaScore):
    """Representation of a 'MediaScore not found'"""

    def __init__(self) -> None:
        super().__init__(
            id_=ID(),
            model_test_result_id=ID(),
            media_identifier=NullMediaIdentifier(),
            scores=set(),
            ephemeral=False,
        )

    def __repr__(self) -> str:
        return "NullMediaScore()"

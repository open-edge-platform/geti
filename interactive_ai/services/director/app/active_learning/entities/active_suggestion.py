# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the ActiveSuggestion entity and its related business logic"""

from collections.abc import Sequence

from geti_types import ID, MediaIdentifierEntity, NullMediaIdentifier, PersistentEntity


class ActiveSuggestion(PersistentEntity):
    """
    Media suggestion made by the active learning engine.

    :param id_: ID of the suggestion
    :param media_identifier: Identifier of the suggested media
    :param score: Active score value that determined this suggestion
    :param models: List of models that generated the suggestion
    :param user: User to whom the suggestion was made
    :param reason: Description of the reason why the suggestion was made
    """

    def __init__(
        self,
        id_: ID,
        media_identifier: MediaIdentifierEntity,
        score: float,
        models: Sequence[ID],
        user: str,
        reason: str = "",
        ephemeral: bool = True,
    ) -> None:
        super().__init__(id_=id_, ephemeral=ephemeral)
        self.media_identifier = media_identifier
        self.score = score
        self.reason = reason
        self.models = models
        self.user = user

    def __eq__(self, other: object):
        if not isinstance(other, ActiveSuggestion):
            return False
        return self.id_ == other.id_

    def __repr__(self) -> str:
        return (
            f"ActiveSuggestion(id={self.id_}, "
            f"media_identifier={self.media_identifier}, "
            f"score={self.score}, "
            f"models={self.models}, "
            f"user={self.user}, "
            f"reason={self.reason})"
        )

    def __str__(self) -> str:
        return f"ActiveSuggestion(media_identifier={self.media_identifier})"


class NullActiveSuggestion(ActiveSuggestion):
    """
    Null active suggestion.
    """

    def __init__(self) -> None:
        super().__init__(
            id_=ID(),
            media_identifier=NullMediaIdentifier(),
            score=1.0,
            models=[],
            user="",
            reason="",
            ephemeral=False,
        )

    def __str__(self) -> str:
        return "NullActiveSuggestion()"

    def __repr__(self) -> str:
        return str(self)

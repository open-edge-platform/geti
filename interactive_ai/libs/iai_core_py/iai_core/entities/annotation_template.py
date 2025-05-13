# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the Annotation Template entity"""

import datetime

from iai_core.entities.persistent_entity import PersistentEntity
from iai_core.utils.time_utils import now

from geti_types import ID


class AnnotationTemplate(PersistentEntity):
    """
    This class represents a user annotation template.

    Annotation template values are provided by the UI in string format. This value is maintained by the UI.

    :param id_: ID of the AnnotationTemplate
    :param name: name of the AnnotationTemplate
    :param value: The value of the AnnotationTemplate represented as a string
    :param creation_date: Creation date of the AnnotationTemplate
    """

    def __init__(
        self,
        id_: ID,
        name: str,
        value: str,
        creation_date: datetime.datetime | None = None,
        ephemeral: bool = True,
    ) -> None:
        PersistentEntity.__init__(self, id_=id_, ephemeral=ephemeral)

        self.name = name
        self.value = value
        self.creation_date = now() if creation_date is None else creation_date

    def __eq__(self, other: object):
        if not isinstance(other, AnnotationTemplate):
            return False
        return self.id_ == other.id_ and self.name == other.name and self.value == other.value

    def __hash__(self):
        return hash(str(self))

    def __repr__(self) -> str:
        return f"AnnotationTemplate({self.id_}, name={self.name}, value={self.value}"


class NullAnnotationTemplate(AnnotationTemplate):
    """Represents 'AnnotationTemplate not found'"""

    def __init__(self) -> None:
        super().__init__(
            id_=ID(),
            name="",
            value="",
            creation_date=datetime.datetime.min,
            ephemeral=False,
        )

    def __repr__(self) -> str:
        return "NullAnnotationTemplate()"

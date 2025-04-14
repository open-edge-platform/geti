# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines the class SuspendedAnnotationScenesDescriptor"""

from collections.abc import Sequence

from sc_sdk.entities.persistent_entity import PersistentEntity

from geti_types import ID


class SuspendedAnnotationScenesDescriptor(PersistentEntity):
    """
    This class holds the list of the IDs of the annotation scene that became suspended
    (i.e. were marked as 'to revisit') following a change in the label schema.

    NOTE: This is meant as a temporary workaround, until the stateless design of the
    dataset manager is implemented.

    :param project_id: ID of the project containing the dataset storage
    :param dataset_storage_id: ID of the dataset storage containing the scenes
    :param scenes_ids: IDs of the suspended annotation scenes
    :param id_: ID of the SuspendedAnnotationScenesDescriptor
    """

    def __init__(
        self,
        id_: ID,
        project_id: ID,
        dataset_storage_id: ID,
        scenes_ids: Sequence[ID],
        ephemeral: bool = True,
    ) -> None:
        super().__init__(id_=id_, ephemeral=ephemeral)
        self.project_id = project_id
        self.dataset_storage_id = dataset_storage_id
        self.scenes_ids = tuple(scenes_ids)


class NullSuspendedAnnotationScenesDescriptor(SuspendedAnnotationScenesDescriptor):
    """This class represents an empty SuspendedAnnotationScenesDescriptor"""

    def __init__(self) -> None:
        super().__init__(
            id_=ID(),
            project_id=ID(),
            dataset_storage_id=ID(),
            scenes_ids=(),
        )

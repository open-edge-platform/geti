# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the Model Storage entity"""

import datetime
from dataclasses import dataclass

from iai_core.entities.model_template import ModelTemplate, NullModelTemplate
from iai_core.utils.time_utils import now

from geti_types import CTX_SESSION_VAR, ID, ProjectIdentifier, PersistentEntity


class ModelStorage(PersistentEntity):
    """
    A Model storage contains the history of a model.

    :param id_: ID of the model storage
    :param project_id: ID of the project containing the storage
    :param task_node_id: ID of the TaskNode
    :param model_template: The model template used by this model storage
    :param creation_date: Creation date; current time if not specified
    :param ephemeral: True if the ModelStorage instance exists only in memory, False
        if it is backed up by the database
    """

    def __init__(
        self,
        id_: ID,
        project_id: ID,
        task_node_id: ID,
        model_template: ModelTemplate,
        creation_date: datetime.datetime | None = None,
        ephemeral: bool = True,
    ) -> None:
        super().__init__(id_=id_, ephemeral=ephemeral)
        self.workspace_id = CTX_SESSION_VAR.get().workspace_id if id_ != ID() else ID()
        self.project_id = project_id
        self.identifier = ModelStorageIdentifier(
            workspace_id=self.workspace_id,
            project_id=project_id,
            model_storage_id=id_,
        )
        self._task_node_id = task_node_id
        self._model_template = model_template
        self._creation_date = now() if creation_date is None else creation_date

    @property
    def project_identifier(self) -> ProjectIdentifier:
        """Identifier of the project containing the model storage"""
        return ProjectIdentifier(workspace_id=self.workspace_id, project_id=self.project_id)

    @property
    def task_node_id(self) -> ID:
        """Get the TaskNode id of the model storage."""
        return self._task_node_id

    @property
    def model_template(self) -> ModelTemplate:
        """Get the model template of the model storage."""
        return self._model_template

    @property
    def creation_date(self) -> datetime.datetime:
        """Get the creation data of the model storage."""
        return self._creation_date

    @property
    def name(self) -> str:
        """Get the name of the model template in the storage"""
        return self.model_template.name

    def __eq__(self, other: object):
        if not isinstance(other, ModelStorage):
            return False
        return self.id_ == other.id_

    def __repr__(self) -> str:
        return (
            f"ModelStorage(id_={self.id_}, task_node_id={self.task_node_id}, "
            f"name={self.name}, creation_date={self.creation_date})"
        )

    def __hash__(self):
        return hash(str(self))


class NullModelStorage(ModelStorage):
    """Representation of a model storage not found'"""

    def __init__(self) -> None:
        super().__init__(
            id_=ID(),
            project_id=ID(),
            task_node_id=ID(),
            model_template=NullModelTemplate(),
            creation_date=datetime.datetime.min,
            ephemeral=False,
        )

    def __repr__(self) -> str:
        return "NullModelStorage()"


@dataclass(frozen=True, eq=True)
class ModelStorageIdentifier:
    """IDs necessary to uniquely identify a ModelStorage"""

    workspace_id: ID
    project_id: ID
    model_storage_id: ID

    @property
    def project_identifier(self) -> ProjectIdentifier:
        return ProjectIdentifier(workspace_id=self.workspace_id, project_id=self.project_id)

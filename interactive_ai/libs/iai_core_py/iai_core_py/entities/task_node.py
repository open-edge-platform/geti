# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This file defines the TaskNode class"""

import logging
from dataclasses import dataclass

from iai_core_py.entities.model_template import ModelTemplate, TaskFamily, TaskType
from iai_core_py.entities.persistent_entity import PersistentEntity

from geti_types import ID

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TaskProperties:
    """
    Task properties collect properties of a task that should remain stable.

    All associated model storages / model templates of a task node should satisfy these
    properties.

    :param task_type: TaskType of the task.
    :param task_family: TaskFamily of the task.
    :param is_trainable: bool indicating if task is trainable.
    :param is_global: bool indicating if task outputs are always relative to the whole
        media/ROI
    :param is_anomaly: bool indicating if task is an anomaly task
    """

    task_type: TaskType
    task_family: TaskFamily
    is_trainable: bool
    is_global: bool
    is_anomaly: bool

    @classmethod
    def from_model_template(cls, model_template: ModelTemplate) -> "TaskProperties":
        """Create TaskProperties from a model template.

        :param model_template: ModelTemplate that contains the desired task properties
        :returns: TaskProperties
        """
        return cls(
            task_type=model_template.task_type,
            task_family=model_template.task_family,
            is_trainable=model_template.is_trainable,
            is_global=model_template.task_type.is_global,
            is_anomaly=model_template.task_type.is_anomaly,
        )


class TaskNode(PersistentEntity):
    """
    Represents the configuration of a task in a TaskGraph.

    The implementation of the task, where the actual computations are done, is performed
    by a class that implements the `ITask` interface. The TaskNode refers to this
    implementation through `model_template` and registration of the ITask in the tasks
    register.  When working in a task chain the TaskNode should be used instead of
    working with the task implementation directly so that SC can do all the necessary
    logic to connect tasks and run them in the correct order.

    :param id_: ID of the task. Set to ID() so that a new unique ID will be assigned upon
        saving.  If the argument is None, it will be set to ID()
    :param title: title for the task, can be anything
    :param project_id: ID of the project to which the tasks belongs
    :param ephemeral: Boolean to mark whether the TaskNode instance has been persisted
        in the database or not
    """

    _project_id: ID
    _title: str
    _task_properties: TaskProperties

    def __init__(
        self,
        title: str,
        project_id: ID,
        id_: ID,
        task_properties: TaskProperties,
        ephemeral: bool = True,
    ) -> None:
        super().__init__(id_=id_, ephemeral=ephemeral)
        self._title = title
        self._task_properties = task_properties
        self._project_id = project_id

    @property
    def title(self) -> str:
        """Gets or sets the title of the TaskNode"""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = value

    @property
    def task_properties(self) -> TaskProperties:
        """Gets or sets the task_type of the TaskNode"""
        return self._task_properties

    @property
    def project_id(self) -> ID:
        """Gets or sets the Project ID of the TaskNode"""
        return self._project_id

    def __repr__(self) -> str:
        # this should return immutable fields of the task node,
        # otherwise it will pose an error in some task graph book keeping (vertex comparison)
        return (
            f"TaskNode(id_={self.id_}, project_id={self.project_id}, "
            f"task_properties={self.task_properties}, title={self.title})"
        )


class NullTaskNode(TaskNode):
    """Representation of a 'TaskNode not found'"""

    def __init__(self) -> None:
        task_properties = TaskProperties(
            task_type=TaskType.NULL,
            task_family=TaskFamily.DATASET,
            is_trainable=False,
            is_global=False,
            is_anomaly=False,
        )
        super().__init__(
            id_=ID(),
            title="",
            task_properties=task_properties,
            project_id=ID(),
            ephemeral=True,
        )

    def __repr__(self) -> str:
        return "NullTaskNode()"

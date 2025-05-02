"""This module implements the Project entity"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

# Conflict with Isort

import abc
import datetime
from typing import TYPE_CHECKING, Optional

from iai_core_py.adapters.adapter import IAdapter, ReferenceAdapter
from iai_core_py.entities.dataset_storage import DatasetStorage, NullDatasetStorage
from iai_core_py.entities.task_graph import NullTaskGraph, TaskGraph
from iai_core_py.utils.constants import DEFAULT_USER_NAME
from iai_core_py.utils.time_utils import now

from .keypoint_structure import KeypointStructure, NullKeypointStructure
from .persistent_entity import PersistentEntity
from .project_performance import ProjectPerformance, TaskPerformance
from geti_types import CTX_SESSION_VAR, ID, ProjectIdentifier

if TYPE_CHECKING:
    from iai_core_py.entities.interfaces.task_graph_adapter_interface import TaskGraphAdapterInterface
    from iai_core_py.entities.task_node import TaskNode


class ProjectEntity(PersistentEntity, metaclass=abc.ABCMeta):
    """
    Base entity for Project
    """

    def __init__(  # noqa: PLR0913
        self,
        id: ID,
        creator_id: str,
        name: str,
        description: str,
        user_names: list[str],
        task_graph: TaskGraph | None,
        dataset_storages: list[DatasetStorage],
        creation_date: datetime.datetime,
        keypoint_structure: KeypointStructure | None = None,
        ephemeral: bool = True,
    ) -> None:
        super().__init__(id_=id, ephemeral=ephemeral)
        self.workspace_id = CTX_SESSION_VAR.get().workspace_id if id != ID() else ID()
        self.name = name
        self.creator_id = creator_id
        self.description = description
        self.user_names = user_names
        self._task_graph = task_graph
        self.creation_date = creation_date
        self.dataset_storage_adapters: list[IAdapter[DatasetStorage]] = [
            ReferenceAdapter(dataset_storage) for dataset_storage in dataset_storages
        ]
        # the training dataset storage adapter will be initialized lazily
        self._training_dataset_storage_adapter: IAdapter | None = None
        self.keypoint_structure = keypoint_structure

    @property
    def training_dataset_storage_adapter(self) -> IAdapter:
        """
        Retrieve training dataset storage from list of dataset storages

        :return: Adapter for the training dataset storage
        :raises: RuntimeError if the number of training storages is not exactly one.
        """
        if self._training_dataset_storage_adapter is None:  # not initialized yet
            training_dataset_storages = [
                dataset_storage for dataset_storage in self.get_dataset_storages() if dataset_storage.use_for_training
            ]
            if len(training_dataset_storages) != 1:
                raise RuntimeError(
                    f"Found {len(training_dataset_storages)} in the project, but only"
                    f"one is currently allowed by the system."
                )
            training_dataset_storage = training_dataset_storages[0]
            self._training_dataset_storage_adapter = ReferenceAdapter(training_dataset_storage)

        return self._training_dataset_storage_adapter

    def get_dataset_storages(self) -> tuple[DatasetStorage, ...]:
        """
        Get all the dataset storages associated with the project

        :return: Tuple of dataset storages
        """
        return tuple(adapter.get() for adapter in self.dataset_storage_adapters)

    def get_dataset_storage_by_id(self, dataset_storage_id: ID) -> DatasetStorage:
        """
        Return dataset storage with id if exists in project, else return NullDatasetStorage

        :param dataset_storage_id: id of dataset storage in project
        :return: dataset storage entity if found in project, else NullDatasetStorage
        """
        for adapter in self.dataset_storage_adapters:
            if adapter.id_ == dataset_storage_id:
                return adapter.get()
        return NullDatasetStorage()

    @property
    def dataset_storage_ids(self) -> list[ID]:
        """
        Returns list of ids of dataset storages associated with the project
        """
        return [adapter.id_ for adapter in self.dataset_storage_adapters]

    @property
    def dataset_storage_count(self) -> int:
        """
        Returns the count of dataset storages associated with the project
        """
        return len(self.dataset_storage_adapters)

    def get_training_dataset_storage(self) -> DatasetStorage:
        """
        Returns the training dataset storage associated with the project
        """
        return self.training_dataset_storage_adapter.get()

    @property
    def training_dataset_storage_id(self) -> ID:
        """
        Returns the ID of the dataset storage associated with the project
        """
        return self.training_dataset_storage_adapter.id_

    @property
    def task_graph(self):  # noqa: ANN201
        """
        Returns the TaskGraph for the project
        """
        return self._task_graph

    @task_graph.setter
    def task_graph(self, value: TaskGraph):
        self._task_graph = value

    @property
    def tasks(self) -> tuple["TaskNode", ...]:
        """
        Read-only property that returns an ordered tuple (based on task sequence in the graph)
        of the tasks in the project.

        :return: Ordered tuple of TaskNode entities
        """
        return self.task_graph.ordered_tasks

    @property
    def task_ids(self) -> list[ID]:
        """
        Returns IDs of all the TaskNodes inside the project.

        :return: a list of ID of all tasks inside the project. Not ordered.
        """
        return self.task_graph.task_ids


class Project(ProjectEntity):
    """
    The project entity describes a Project in SC.
    It defines user interaction, such as name, description, creation date and user access.
    The Project also defines the Tasks and the relations between the Tasks in the TaskGraph.
    For more information about the task graph, check out :class:`TaskGraph`.
    The project can have one or more label schemas, but the association is loose and
    not stored inside this entity.
    For more information about the label schema, check out :class:`LabelSchema`.

    The Project entity can be instantiated in two ways.
    With the TaskGraph entity, or with a TaskGraphAdapter.
    Please mind that the Project entity can not be instantiated with both.

    .. rubric:: With TaskGraph

    This way assumes the TaskGraph and its tasks are constructed before the Project entity is made.

    >>> from iai_core_py.algorithms import ModelTemplateList
    >>> from iai_core_py.entities.task_node import TaskType
    >>> model_template = ModelTemplateList().get_by_id("detection")
    >>> task = TaskNode(title="Empty TaskNode",
    ...     task_properties=TaskProperties.from_model_template(model_template),
    ...     project_id=ID(),
    >>> task_graph = TaskGraph()
    >>> task_graph.add_node(task)
    >>> project = Project(name="Example project", description="-",
    ...                   dataset_storage=NullDatasetStorage(),
    ...                   user_names=[], task_graph=task_graph)
    >>> project
    Project(name='Example project', description='-', user_names=[])

    .. rubric:: With a TaskGraphAdapter

    Instead of providing the items directly, the Dataset entity can also be instantiated with an adapter.
    The adapter provides the tools to fetch the TaskGraph lazily.

    >>> from iai_core_py.adapters.task_graph_adapter import TaskGraphAdapter
    >>> from iai_core_py.repos.mappers.mongodb_mappers.task_graph_mapper import TaskGraphToMongo
    >>> task_graph_adapter = TaskGraphAdapter(mapper=TaskGraphToMongo,
    ...                                       workspace=workspace, data={})
    >>> Project(name="Example project", description="-",
    ...         dataset_storage=NullDatasetStorage(), user_names=[],
    ...         task_graph_adapter=task_graph_adapter)
    Project(name='Example project', description='-', user_names=[])

    .. rubric:: Get tasks in project

    :param id: ID of project
    :param name: Name (title) of project for User
    :param description: Description of project for User
    :param dataset_storages: Dataset storage to be associated with this project
    :param user_names: [Optional] names of Users that have access to the project
    :param creation_date:  [Optional] Set the creation date of the project. If None, the datetime will be automatically
    set to the timestamp of instantiating the entity.
    :param task_graph: [Method 1]: The TaskGraph entity to create project with
    :param task_graph_adapter: [Method 2]: An adapter for the Project to fetch its TaskGraph with.
    :param keypoint_structure: The keypoint structure of the project (relevant for Keypoint Detection)
    :param hidden: Whether to mark this project as hidden (e.g. to exclude it from the views)
    :param ephemeral: Boolean to mark whether the project has been persisted in the
        database or not
    """

    def __init__(  # noqa: PLR0913
        self,
        id: ID,
        name: str,
        creator_id: str,
        description: str,
        dataset_storages: list[DatasetStorage],
        task_graph: TaskGraph | None = None,
        user_names: list[str] | None = None,
        creation_date: datetime.datetime | None = None,
        project_performance: ProjectPerformance | None = None,
        task_graph_adapter: Optional["TaskGraphAdapterInterface"] = None,
        keypoint_structure: KeypointStructure | None = None,
        hidden: bool = False,
        ephemeral: bool = True,
    ) -> None:
        user_names = user_names if user_names is not None else [DEFAULT_USER_NAME]
        creation_date = now() if creation_date is None else creation_date
        task_graph = TaskGraph() if task_graph is None and task_graph_adapter is None else task_graph

        super().__init__(
            id=id,
            creator_id=creator_id,
            name=name,
            description=description,
            user_names=user_names,
            task_graph=task_graph,
            dataset_storages=dataset_storages,
            creation_date=creation_date,
            keypoint_structure=keypoint_structure,
            ephemeral=ephemeral,
        )

        self.task_graph_adapter = task_graph_adapter
        self.hidden = hidden

        if project_performance is None:
            project_performance = ProjectPerformance(
                task_performances=[TaskPerformance(task_node_id=task.id_) for task in self.get_trainable_task_nodes()]
            )
        self._performance = project_performance

    @classmethod
    def with_adapters(  # noqa: PLR0913
        cls,
        training_dataset_storage_adapter: IAdapter[DatasetStorage],
        dataset_storage_adapters: list[IAdapter[DatasetStorage]],
        name: str,
        id: ID,
        creator_id: str,
        description: str,
        task_graph: TaskGraph | None = None,
        user_names: list[str] | None = None,
        creation_date: datetime.datetime | None = None,
        project_performance: ProjectPerformance | None = None,
        task_graph_adapter: Optional["TaskGraphAdapterInterface"] = None,
        keypoint_structure: KeypointStructure | None = None,
        hidden: bool = False,
        ephemeral: bool = True,
    ):
        """
        Instantiate the Project with adapters

        :raises: RuntimeError if an empty list of dataset storage adapters is provided.
        """
        # The class is initially created without a proper dataset storage, then
        # immediately patched by overriding the dataset storage adapters.
        if len(dataset_storage_adapters) == 0:
            raise RuntimeError("Can't create a project with no dataset storage adapters")
        inst = cls(
            dataset_storages=[NullDatasetStorage()],
            id=id,
            creator_id=creator_id,
            name=name,
            description=description,
            user_names=user_names,
            task_graph=task_graph,
            project_performance=project_performance,
            creation_date=creation_date,
            task_graph_adapter=task_graph_adapter,
            keypoint_structure=keypoint_structure,
            hidden=hidden,
            ephemeral=ephemeral,
        )
        inst._training_dataset_storage_adapter = training_dataset_storage_adapter
        inst.dataset_storage_adapters = dataset_storage_adapters
        return inst

    def __repr__(self) -> str:
        return (
            f"Project({self.id_}, name='{self.name}', description='{self.description}', user_names={self.user_names})"
        )

    def __eq__(self, other: object):
        if not isinstance(other, Project):
            return False
        return (
            self.id_ == other.id_
            and self.name == other.name
            and self.description == other.description
            and self.user_names == other.user_names
            and self.task_graph == other.task_graph
            and self.keypoint_structure == other.keypoint_structure
        )

    @property
    def identifier(self) -> "ProjectIdentifier":
        """
        Get the ProjectIdentifier of the project

        :return: ProjectIdentifier
        """
        return ProjectIdentifier(workspace_id=self.workspace_id, project_id=self.id_)

    @property
    def task_graph(self):  # noqa: ANN201
        """
        Returns the TaskGraph for the project. Fetches it from the adapter, or returns the assigned entity.

        :return: TaskGraph
        """
        if self.task_graph_adapter is not None:
            return self.task_graph_adapter.graph
        if self._task_graph is not None:
            return self._task_graph
        raise RuntimeError(
            "Project is corrupted and does not contain any task graph. "
            "Either the task graph or an adapter has to be defined."
        )

    @task_graph.setter
    def task_graph(self, value: TaskGraph):
        """
        Set the TaskGraph for the project. Automatically uncouples the adapter if this was assigned.

        :param value:

        :return:
        """
        self.task_graph_adapter = None
        self._task_graph = value

    @property
    def pipeline_representation(self) -> str:
        """
        Returns the readable pipeline representation.
        Cached by the task_graph_adapter.

        :return: the readable pipeline string representation
        """
        if self.task_graph_adapter is not None:
            return self.task_graph_adapter.pipeline_representation
        return self.task_graph.pipeline_representation

    def get_project_type(self) -> str:
        """
        Returns the project type (trainable task types joined by →)
        """
        return " → ".join(task_node.task_properties.task_type.name for task_node in self.get_trainable_task_nodes())

    def __hash__(self):
        return hash(str(self))

    def get_trainable_task_nodes(self) -> list["TaskNode"]:
        """
        Returns a list of task nodes which are trainable (can produce models).

        :return: a list of trainable task nodes
        """
        return [task for task in self.tasks if task.task_properties.is_trainable]

    def get_trainable_task_node_by_id(self, task_id: ID) -> Optional["TaskNode"]:
        """
        Get the trainable task of this project with the given ID

        :param task_id: ID of the task to find
        :return: Task if found and trainable, None otherwise
        """
        for task in self.tasks:
            if task.task_properties.is_trainable and task.id_ == task_id:
                return task
        return None

    @property
    def performance(self) -> ProjectPerformance:
        """
        Returns the project performance
        """
        return self._performance


class NullProject(Project):
    """Representation of an 'project not found'"""

    def __init__(self) -> None:
        super().__init__(
            id=ID(),
            name="",
            creator_id="",
            description="",
            dataset_storages=[NullDatasetStorage()],
            task_graph=NullTaskGraph(),
            user_names=[],
            creation_date=datetime.datetime.min,
            keypoint_structure=NullKeypointStructure(),
            ephemeral=False,
        )

    def get_training_dataset_storage(self) -> DatasetStorage:
        raise ValueError("NullProject does not have a training dataset storage")

    @property
    def training_dataset_storage_id(self) -> ID:
        raise ValueError("NullProject does not have a training dataset storage")

    def __repr__(self) -> str:
        return "NullProject()"

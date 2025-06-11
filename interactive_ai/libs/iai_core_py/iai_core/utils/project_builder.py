# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module defines the project builder
"""

import logging
from collections import defaultdict
from collections.abc import Sequence

from iai_core.algorithms import ModelTemplateList
from iai_core.entities.active_model_state import ActiveModelState
from iai_core.entities.annotation import AnnotationSceneKind
from iai_core.entities.color import Color
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.keypoint_structure import KeypointEdge, KeypointPosition, KeypointStructure
from iai_core.entities.label import Domain, Label
from iai_core.entities.label_schema import (
    LabelGroup,
    LabelGroupType,
    LabelSchema,
    LabelSchemaView,
    LabelTree,
    NullLabelSchema,
)
from iai_core.entities.model_storage import ModelStorage
from iai_core.entities.model_template import ModelTemplate, NullModelTemplate, TaskType
from iai_core.entities.project import Project
from iai_core.entities.task_graph import TaskEdge, TaskGraph
from iai_core.entities.task_node import NullTaskNode, TaskNode, TaskProperties
from iai_core.factories.project_parser import (
    DOMAIN_TO_EMPTY_LABEL_NAME,
    DOMAINS_WITH_EMPTY_LABEL,
    ProjectParser,
    ProjectUpdateParser,
)
from iai_core.factories.project_validator import ProjectCreationValidator, ProjectUpdateValidator
from iai_core.repos import (
    ActiveModelStateRepo,
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    DatasetStorageRepo,
    LabelRepo,
    LabelSchemaRepo,
    ModelStorageRepo,
    ProjectRepo,
    TaskNodeRepo,
)
from iai_core.utils.annotation_scene_state_helper import AnnotationSceneStateHelper
from iai_core.utils.feature_flags import FeatureFlagProvider

from geti_types import CTX_SESSION_VAR, ID, ProjectIdentifier

logger = logging.getLogger(__name__)

FEATURE_FLAG_KEYPOINT_DETECTION = "FEATURE_FLAG_KEYPOINT_DETECTION"


class ProjectBuilder:
    """
    Project builder class
    """

    @staticmethod
    def get_default_model_template_by_task_type(task_type: TaskType) -> ModelTemplate:
        """
        Get the default ModelTemplate which belongs to the task type.

        :param task_type: the task type which requires a model template
        :return: the ModelTemplate associated with the task type
        """
        if task_type in [TaskType.DATASET, TaskType.CROP]:
            default_model_template = ModelTemplateList().get_by_id(task_type.name.lower())
        else:
            default_model_template = next(
                (
                    model_template
                    for model_template in ModelTemplateList().get_all()
                    if model_template.task_type == task_type and model_template.is_default_for_task
                ),
                NullModelTemplate(),
            )

        if isinstance(default_model_template, NullModelTemplate):
            raise ModelTemplateError("A NullModelTemplate was created.")
        if default_model_template.task_type != task_type:
            raise ModelTemplateError(
                f"Bad algorithm found. Searching for '{task_type}', but found "
                f"'{default_model_template.task_type}' with ID({default_model_template.model_template_id})"
            )
        return default_model_template

    @staticmethod
    def _build_task_node(
        project_id: ID,
        task_name: str,
        model_template: ModelTemplate,
    ) -> TaskNode:
        """
        Build a TaskNode with title task_name, and properties taken from the model template.

        :param project_id: the ID of the project the task node belongs to
        :param task_name: the name of the task for the task node
        :param model_template: the model template whose properties will be used to create the task node
        :return: the TaskNode created from the model template
        """
        return TaskNode(
            title=task_name,
            task_properties=TaskProperties.from_model_template(model_template),
            project_id=project_id,
            id_=TaskNodeRepo.generate_id(),
        )

    @classmethod
    def _build_model_storage(
        cls,
        project_identifier: ProjectIdentifier,
        task_node: TaskNode,
        model_template: ModelTemplate,
    ) -> ModelStorage:
        """
        Build a ModelStorage.

        :param project_identifier: identifier of the project
        :param task_node: the TaskNode for the ModelStorage
        :param model_template: the ModelTemplate for the ModelStorage
        :return: the ModelStorage
        """
        return ModelStorage(
            id_=ModelStorageRepo.generate_id(),
            project_id=project_identifier.project_id,
            task_node_id=task_node.id_,
            model_template=model_template,
        )

    @classmethod
    def _build_active_model_state(
        cls,
        model_storage: ModelStorage,
        task_node_id: ID,
    ) -> ActiveModelState:
        """
        Build an active model state.

        :param model_storage: the ModelStorage
        :param task_node_id: the TaskNode ID
        :return: the ActiveModelState
        """
        return ActiveModelState(
            task_node_id=task_node_id,
            active_model_storage=model_storage,
        )

    @classmethod
    def _build_dataset_storage(
        cls,
        project_identifier: ProjectIdentifier,
        name: str,
        creator: str,
        use_for_training: bool,
    ) -> DatasetStorage:
        """
        Build a DatasetStorage.

        :param project_identifier: Identifier of the project containing the dataset storage
        :param name: the name of the DatasetStorage
        :param creator: the creator of the DatasetStorage
        :param use_for_training: True if the DatasetStorage will be used for training, otherwise False.
        :return: the DatasetStorage
        """
        return DatasetStorage(
            name=name,
            project_id=project_identifier.project_id,
            use_for_training=use_for_training,
            creator_name=creator,
            _id=DatasetStorageRepo.generate_id(),
        )

    @classmethod
    def _build_task_graph(
        cls,
        task_nodes: Sequence[TaskNode],
        connections: Sequence[tuple[str, str]],
    ) -> TaskGraph:
        """
        Build a TaskGraph which sorts out all the connections between the task_nodes.

        :param task_nodes: the TaskNodes in the TaskGraph
        :param connections: the connections as task_name_1 to task_name_2 between two task_nodes
        :return: a TaskGraph containing the TaskNodes and the relations between them as TaskEdges
        """
        task_graph = TaskGraph()
        from_task_node = None
        to_task_node = None
        for from_connection, to_connection in connections:
            for task_node in task_nodes:
                if task_node.title == from_connection:
                    from_task_node = task_node
                if task_node.title == to_connection:
                    to_task_node = task_node
            if not from_task_node or not to_task_node:
                raise ProjectBuildError(
                    "Error building the task graph. One of the TaskNodes is None in the "
                    "connection. Please check the titles of your connections."
                )
            task_graph.add_node(from_task_node)
            task_graph.add_node(to_task_node)
            task_edge = TaskEdge(from_task=from_task_node, to_task=to_task_node)
            task_graph.add_task_edge(task_edge)

        return task_graph

    @classmethod
    def _build_project(
        cls,
        project_id: ID,
        task_graph: TaskGraph,
        project_name: str,
        description: str,
        creator_id: str,
        keypoint_structure: KeypointStructure | None,
    ) -> Project:
        """
        Build the Project with is dataset storage.

        :param project_id: the ID of the project
        :param task_graph: the TaskGraph of the project
        :param project_name:  the name of the project
        :param description: the description of the project
        :param creator_id: the creator of the project
        :param keypoint_structure: the keypoint structure of the project
        :return: the Project
        """
        workspace_id = CTX_SESSION_VAR.get().workspace_id
        dataset_storage = cls._build_dataset_storage(
            project_identifier=ProjectIdentifier(workspace_id=workspace_id, project_id=project_id),
            name="Dataset",
            creator=creator_id,
            use_for_training=True,
        )
        return Project(
            id=project_id,
            name=project_name,
            creator_id=creator_id,
            description=description,
            user_names=["Geti"],
            dataset_storages=[dataset_storage],
            task_graph=task_graph,
            hidden=False,
            keypoint_structure=keypoint_structure,
        )

    @staticmethod
    def _build_anomaly_labels(
        domain: Domain,
        task_label_by_group_name: dict[str, list[Label]],
    ) -> tuple[list[LabelGroup], list[Label]]:
        """
        Specifically builds only the anomaly label groups and labels for the project.
        If labels are provided in task_label_by_group_name, they will be used instead of
        creating new labels.

        :param domain: domain of the task to build the labels for
        :param task_label_by_group_name: a mapping of group name to a list of labels
        :return: The label groups and the labels relevant to the domain
        """
        anomalous_task_labels = []
        anomalous_task_groups = []
        if not task_label_by_group_name:
            # create the default labels for anomaly task
            normal_label = Label(
                name="Normal",
                domain=domain,
                color=Color(red=139, green=174, blue=70),
                id_=LabelRepo.generate_id(),
                is_anomalous=False,
            )
            anomalous_label = Label(
                name="Anomalous",
                domain=domain,
                color=Color(red=255, green=86, blue=98),
                id_=LabelRepo.generate_id(),
                is_anomalous=True,
            )
            labels = [normal_label, anomalous_label]

            label_group = LabelGroup(
                name=f"default - {domain.name.lower()}",
                labels=labels,
                group_type=LabelGroupType.EXCLUSIVE,
            )
            anomalous_task_labels.extend(labels)
            anomalous_task_groups.append(label_group)
        else:
            for group_name, labels in task_label_by_group_name.items():
                label_group = LabelGroup(
                    name=group_name,
                    labels=labels,
                    group_type=LabelGroupType.EXCLUSIVE,
                )
                anomalous_task_labels.extend(labels)
                anomalous_task_groups.append(label_group)
        return anomalous_task_groups, anomalous_task_labels

    @staticmethod
    def _build_groups_and_empty_labels(
        domain: Domain,
        task_labels_by_group_name: dict[str, list[Label]],
        child_to_parent_id: dict[Label, str | ID],
    ) -> tuple[list[LabelGroup], list[Label]]:
        """
        Build label groups and insert empty labels, if necessary.

        The method assumes that custom Label entities have been previously created;
        they are provided through the task_labels_by_group_name parameter, which also
        associates labels to the respective groups (to create).

        If the domain requires any empty labels to be created and they are not provided
        as input, this method builds them and their groups as well.

        :param domain: domain of the task to build the labels for
        :param task_labels_by_group_name: a mapping of group name to a list of labels
        :param child_to_parent_id: a dict mapping a label to its parent's name or ID
        :return: The label groups and the labels relevant to the domain
        """
        empty_label_created = False
        custom_labels = []
        custom_label_groups = []
        top_level_multiclass_classification_groups_found = False
        task_label_names: set[str] = {
            label.name for group_labels in task_labels_by_group_name.values() for label in group_labels
        }
        task_label_ids: set[ID] = {
            label.id_ for group_labels in task_labels_by_group_name.values() for label in group_labels
        }

        # Build label groups and analyze their layout
        for group_name, labels in task_labels_by_group_name.items():
            group_has_empty_label: bool = any(label.is_empty for label in labels)
            if group_has_empty_label:  # empty label provided along with custom labels
                if len(labels) > 1:
                    logger.error(
                        "Found empty label in a group '%s' with more than 1 label: %s",
                        group_name,
                        labels,
                    )
                    raise ValueError("Invalid group for empty label")
                empty_label_created = True
            label_group = LabelGroup(
                name=group_name,
                labels=labels,
                group_type=(LabelGroupType.EMPTY_LABEL if group_has_empty_label else LabelGroupType.EXCLUSIVE),
            )
            custom_labels.extend(labels)
            custom_label_groups.extend([label_group])
            if domain is Domain.CLASSIFICATION and len(labels) >= 2:
                # assumption: all labels in a group have the same parents
                group_parent = child_to_parent_id.get(labels[0], None)
                if group_parent is None or group_parent not in (
                    task_label_names | task_label_ids
                ):  # no parent or parent in another task
                    top_level_multiclass_classification_groups_found = True

        # Determine if it is necessary to create an empty label
        add_empty_label: bool = (
            not empty_label_created
            and domain in DOMAINS_WITH_EMPTY_LABEL
            and not top_level_multiclass_classification_groups_found
        )

        # Create the empty label and its group
        if add_empty_label:
            empty_label = Label(
                name=DOMAIN_TO_EMPTY_LABEL_NAME[domain],
                domain=domain,
                color=Color(red=0, green=0, blue=0),
                is_empty=True,
                id_=LabelRepo.generate_id(),
            )
            label_group = LabelGroup(
                name=empty_label.name,
                labels=[empty_label],
                group_type=LabelGroupType.EMPTY_LABEL,
            )
            custom_labels.extend([empty_label])
            custom_label_groups.extend([label_group])

        return custom_label_groups, custom_labels

    @staticmethod
    def _build_default_labels_and_groups_for_task(
        domain: Domain,
        task_node: TaskNode,
        labels: list[Label],
        group_name_by_label: dict[ID, str],
        child_to_parent_id: dict[Label, str | ID],
    ) -> tuple[list[LabelGroup], list[Label]]:
        """
        Builds all the needed LabelGroups and Labels for the task.

        :param domain: determines which domain to build the task labels for
        :param task_node: the TaskNode for the labels
        :param labels: a list of labels relevant to the task
        :param group_name_by_label: a dictionary mapping a label ID to a group name
        :param child_to_parent_id: a dict mapping a label to its parent's name or ID
        :return: The LabelGroups and a list of Labels for the task.
        """
        task_groups: list[LabelGroup]
        task_labels: list[Label]
        task_labels_by_group_name: defaultdict[str, list[Label]] = defaultdict(list)
        # Determine which group name has which task label. The group names are dependent
        # on the task. For example multi-label classification can have multiple groups
        # for a single task.
        for label in labels:
            group_name = group_name_by_label.get(label.id_, label.name)
            task_labels_by_group_name[group_name].append(label)

        if task_node.task_properties.is_anomaly:
            # Build anomaly labels and their groups
            task_groups, task_labels = ProjectBuilder._build_anomaly_labels(
                domain=domain, task_label_by_group_name=task_labels_by_group_name
            )
        else:
            # Build label groups and insert empty labels, if necessary
            task_groups, task_labels = ProjectBuilder._build_groups_and_empty_labels(
                domain=domain,
                task_labels_by_group_name=task_labels_by_group_name,
                child_to_parent_id=child_to_parent_id,
            )

        return task_groups, task_labels

    @staticmethod
    def _build_label_tree(
        current_labels: list[Label],
        child_to_parent_id: dict[Label, str | ID],
    ) -> LabelTree:
        label_tree = LabelTree()
        for child_label, parent_id in child_to_parent_id.items():
            for parent_label in current_labels:
                if parent_id in [parent_label.name, parent_label.id_]:
                    label_tree.add_child(parent_label, child_label)
                    break
        return label_tree

    @classmethod
    def _build_label_schema(
        cls,
        project: Project,
        labels_by_task: dict[ID, list[Label]],
        group_name_by_label_id: dict[ID, str],
        child_to_parent_id: dict[Label, str | ID],
        previous_schema_revision_id: ID | None = None,
        previous_task_id_to_schema_revision_id: dict[ID, ID] | None = None,
    ) -> tuple[LabelSchema, dict[str, LabelSchemaView]]:
        """
        Build the LabelSchema for the project, and the LabelSchemaView for each task.

        A project  LabelSchema is built, and then gets LabelGroups added to it per task.

        The label relations between the tasks are determined by the ordered list of tasks
        returned by project.task_graph.ordered_tasks().

        :param project: the project which is associated to the label schema
        :param labels_by_task: a dictionary mapping the task ID to a set of labels
        :param group_name_by_label_id: a dictionary mapping a label ID/name to a group name
        :param child_to_parent_id: a dictionary mapping a label to its parent's ID
        :param previous_schema_revision_id: the ID of the project's previous LabelSchema
        :param previous_task_id_to_schema_revision_id: a dictionary mapping a task ID to a LabelSchema ID
        :return: the LabelSchema, and a dictionary mapping task title to LabelSchemaView
        """
        label_schema = LabelSchema(
            id_=LabelSchemaRepo.generate_id(),
            previous_schema_revision_id=previous_schema_revision_id,
            project_id=project.id_,
        )
        task_title_to_label_schema: dict[str, LabelSchemaView] = {}
        ordered_tasks: tuple[TaskNode, ...] = project.task_graph.ordered_tasks
        previous_task_labels: list[Label] = []
        previous_task: TaskNode | NullTaskNode = NullTaskNode()
        for task in ordered_tasks:
            if not task.task_properties.is_trainable:
                continue
            current_domain = task.task_properties.task_type.domain
            current_task_labels = list(labels_by_task[task.id_])
            (
                current_task_groups,
                current_task_labels,
            ) = cls._build_default_labels_and_groups_for_task(
                domain=current_domain,
                task_node=task,
                labels=current_task_labels,
                group_name_by_label=group_name_by_label_id,
                child_to_parent_id=child_to_parent_id,
            )
            label_tree = cls._build_label_tree(
                current_labels=current_task_labels,
                child_to_parent_id=child_to_parent_id,
            )
            label_schema.add_groups_for_task(label_groups=current_task_groups)
            label_schema.label_tree = label_tree
            task_to_schema_revision_id = None
            if previous_task_id_to_schema_revision_id is not None:
                task_to_schema_revision_id = previous_task_id_to_schema_revision_id.get(task.id_, None)
            task_label_schema = LabelSchemaView.from_parent(
                parent_schema=label_schema,
                labels=current_task_labels,
                task_node_id=task.id_,
                id_=LabelSchemaRepo.generate_id(),
                previous_schema_revision_id=task_to_schema_revision_id,
            )
            task_title_to_label_schema[task.title] = task_label_schema

            if previous_task.task_properties.task_type.is_trainable:
                add_previous_task_label_as_parent = (
                    task.task_properties.task_type.is_global and previous_task.task_properties.task_type.is_local
                )
                label_schema.add_label_relations_for_task(
                    child_to_parent_id=child_to_parent_id,
                    task_labels=current_task_labels,
                    previous_trainable_task_labels=previous_task_labels,
                    add_previous_task_label_as_parent=add_previous_task_label_as_parent,
                )
            previous_task_labels = current_task_labels
            previous_task = task

        return label_schema, task_title_to_label_schema

    @classmethod
    def build_full_project(
        cls,
        creator_id: str,
        parser_class: type[ProjectParser],
        parser_kwargs: dict,
    ) -> tuple[Project, LabelSchema, dict[str, LabelSchemaView]]:
        """
        This does NOT save anything to the database.
        Builds the complete project by creating the following entities:
            - project (with dataset storage)
            - task graph
            - model storage
            - active model state
            - labels
            - label schema
            - keypoint structure

        To save the entities, please call PersistedProjectBuilder.build_full_project()
        which makes use of overriding ProjectBuilder classes to save.

        :param creator_id: the ID of who created the project
        :param parser_class: a parser which will be used to get relevant information from the REST response
        :param parser_kwargs: arguments to pass to the parser for initialization
        :return: the project, the label schema, and a mapping of task to label schema view
        """
        is_keypoint_detection_enabled = FeatureFlagProvider.is_enabled(FEATURE_FLAG_KEYPOINT_DETECTION)
        parser = parser_class(**parser_kwargs)
        ProjectCreationValidator().validate(parser=parser)
        project_name = parser.get_project_name()
        connections = parser.get_connections()
        tasks_names = parser.get_tasks_names()

        # Generate project ID first as it is needed to for the TaskGraph.
        project_id = ProjectRepo.generate_id()
        workspace_id = CTX_SESSION_VAR.get().workspace_id
        project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=project_id)

        task_nodes = []
        project_labels = []
        labels_by_task: dict[ID, list[Label]] = {}
        group_name_by_label_id: dict[ID, str] = {}
        child_to_parent_id: dict[Label, str] = {}
        keypoint_structure: KeypointStructure | None = None
        for task_name in tasks_names:
            task_type = parser.get_task_type_by_name(task_name=task_name)
            custom_labels_names = parser.get_custom_labels_names_by_task(
                task_name=task_name,
            )
            model_template = cls.get_default_model_template_by_task_type(task_type=task_type)
            task_node = cls._build_task_node(
                project_id=project_id,
                task_name=task_name,
                model_template=model_template,
            )
            model_storage = cls._build_model_storage(
                project_identifier=project_identifier,
                task_node=task_node,
                model_template=model_template,
            )
            cls._build_active_model_state(
                model_storage=model_storage,
                task_node_id=task_node.id_,
            )
            task_nodes.append(task_node)
            labels_by_task[task_node.id_] = []
            labels_by_task_list = []
            for label_name in custom_labels_names:
                label_group = parser.get_label_group_by_name(
                    task_name=task_name,
                    label_name=label_name,
                )
                label_hotkey = parser.get_label_hotkey_by_name(
                    task_name=task_name,
                    label_name=label_name,
                )
                label_color = parser.get_label_color_by_name(
                    task_name=task_name,
                    label_name=label_name,
                )
                label_parent = parser.get_label_parent_by_name(
                    task_name=task_name,
                    label_name=label_name,
                )
                label = Label(
                    name=label_name,
                    domain=task_type.domain,
                    color=Color.from_hex_str(label_color),
                    hotkey=label_hotkey,
                    id_=LabelRepo.generate_id(),
                    is_anomalous=False,
                )
                project_labels.append(label)
                if label_parent:
                    child_to_parent_id[label] = label_parent
                labels_by_task_list.append(label)
                labels_by_task[task_node.id_] = labels_by_task_list
                group_name_by_label_id[label.id_] = label_group

            if is_keypoint_detection_enabled and task_type == TaskType.KEYPOINT_DETECTION:
                keypoint_structure_data = parser.get_keypoint_structure_data(task_name=task_name)
                keypoint_structure = cls._build_keypoint_structure(
                    keypoint_structure_data=keypoint_structure_data,
                    labels=labels_by_task_list,
                )

        # Build the task graph
        task_graph = cls._build_task_graph(
            task_nodes=task_nodes,
            connections=connections,
        )

        # Build the project
        project = cls._build_project(
            project_id=project_id,
            task_graph=task_graph,
            project_name=project_name,
            description="",
            creator_id=creator_id,
            keypoint_structure=keypoint_structure,
        )
        logger.info(f"Created a project with name {project.name} with task graph {task_graph}")

        # Build the LabelSchema and the mapping of task to LabelSchemaView
        label_schema, task_to_label_schema_view = cls._build_label_schema(
            project=project,
            labels_by_task=labels_by_task,
            group_name_by_label_id=group_name_by_label_id,
            child_to_parent_id=child_to_parent_id,
        )

        return project, label_schema, task_to_label_schema_view

    @classmethod
    def _edit_label(
        cls,
        project_identifier: ProjectIdentifier,  # noqa: ARG003
        label: Label,
        label_name: str,
        label_color_hex_str: str,
        label_hotkey: str,
    ) -> Label:
        """
        Edits the values of a label

        :param project_identifier: identifier of the project where the label is defined
        :param label: the label to be edited
        :param label_name: the label's new name
        :param label_color_hex_str: the label's new color represented as a hex string
        :param label_hotkey: the label's new hotkey
        :return: The edited label
        """
        label.name = label_name
        label.color = Color.from_hex_str(label_color_hex_str)
        label.hotkey = label_hotkey
        return label

    @classmethod
    def edit_labels(
        cls,
        project_identifier: ProjectIdentifier,
        parser: ProjectUpdateParser,
        task_name: str,
        old_labels: list[Label],
        old_groups: list[LabelGroup],
    ) -> tuple[list[Label], bool]:
        """
        Method to determine which EXISTING label in a project needs to be edited.
        Does not edit any empty labels, only user defined labels.

        :param project_identifier: identifier of the project where the label is defined
        :param parser: the parser to use to get the info from the REST data
        :param task_name: the task which will have its labels edited
        :param old_labels: the list of all the old labels for the task
        :param old_groups: the list of the label groups for the task
        :return: a list of edited labels, and a bool which indicates if an edit happened
        """
        any_label_edited = False
        old_label_names = [label.name for label in old_labels]
        new_label_names = parser.get_custom_labels_names_by_task(task_name=task_name)
        for label_name in new_label_names:
            label_id = parser.get_label_id_by_name(
                task_name=task_name,
                label_name=label_name,
            )
            if not label_id and label_name not in old_label_names:
                # The label exists only in the REST data and not in the project,
                # this means that the label is to be added, and not to be edited
                continue
            label_color_hex_str = parser.get_label_color_by_name(
                task_name=task_name,
                label_name=label_name,
            )
            label_hotkey = parser.get_label_hotkey_by_name(
                task_name=task_name,
                label_name=label_name,
            )
            label_group_name = parser.get_label_group_by_name(
                task_name=task_name,
                label_name=label_name,
            )
            for old_group in old_groups:
                group_label_ids = [label.id_ for label in old_group.labels]
                if label_id in group_label_ids and label_group_name != old_group.name:
                    raise ProjectUpdateError(
                        f"Changing the group of a label is not allowed. Attempted to "
                        f"change label '{label_name}' from group '{old_group.name}' "
                        f"to group '{label_group_name}'"
                    )
            for old_label in old_labels:
                if old_label.id_ == label_id and (
                    old_label.name,
                    old_label.color.hex_str.lower(),
                    old_label.hotkey,
                ) != (
                    label_name,
                    label_color_hex_str.lower(),
                    label_hotkey,
                ):
                    cls._edit_label(
                        project_identifier=project_identifier,
                        label=old_label,
                        label_name=label_name,
                        label_color_hex_str=label_color_hex_str,
                        label_hotkey=label_hotkey,
                    )
                    any_label_edited = True
                    break
        return old_labels, any_label_edited

    @staticmethod
    def _remove_label_from_project(project: Project, label: Label) -> dict[ID, set[ID]]:
        """
        Removes the labels from the project. First saves the label with a DELETED name,
        then the label will be removed from any annotation scene it is present in.

        :param project: the project to check the annotation scene of
        :param label: the label to remove for the annotation scene
        :return: For each dataset storage, a set of annotation scene IDs for annotation scenes that were modified by
        this method
        """
        modified_scene_ids_by_storage: dict[ID, set[ID]] = {}
        label.name += f"_DELETED_{str(label.id_)}"
        LabelRepo(project.identifier).save(label)
        dataset_storages = project.get_dataset_storages()
        for dataset_storage in dataset_storages:
            modified_scene_ids_by_storage[dataset_storage.id_] = set()
            ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
            ann_scene_state_repo = AnnotationSceneStateRepo(dataset_storage.identifier)
            annotation_scenes = ann_scene_repo.get_all_by_kind_and_labels(
                kind=AnnotationSceneKind.ANNOTATION, label_ids=[label.id_]
            )
            for annotation_scene in annotation_scenes:
                updated_annotations = []
                for annotation in annotation_scene.annotations:
                    annotation_labels = annotation.get_labels(include_empty=True)
                    for annotation_label in annotation_labels:
                        if annotation_label.id_ == label.id_:
                            modified_scene_ids_by_storage[dataset_storage.id_].add(annotation_scene.id_)
                            annotation_labels.remove(annotation_label)
                    if len(annotation_labels) > 0:  # Filter out any annotation that no longer has a label
                        annotation.set_labels(annotation_labels)
                        updated_annotations.append(annotation)
                annotation_scene.annotations = updated_annotations
                annotation_scene_state = AnnotationSceneStateHelper.compute_annotation_scene_state(
                    annotation_scene=annotation_scene,
                    project=project,
                )
                ann_scene_state_repo.save(annotation_scene_state)
                ann_scene_repo.save(annotation_scene)
        return modified_scene_ids_by_storage

    @classmethod
    def _build_keypoint_structure(
        cls, keypoint_structure_data: dict[str, list], labels: list[Label]
    ) -> KeypointStructure:
        """
        Builds the keypoint structure for the project

        :param keypoint_structure_data: the keypoint structure data
        :param labels: the labels of the project
        :return: the KeypointStructure
        """
        label_name_to_id: dict[str, ID] = {label.name: label.id_ for label in labels}
        label_ids = [label.id_ for label in labels]
        edges = []
        for edge in keypoint_structure_data["edges"]:
            node_1 = ID(edge["nodes"][0]) if ID(edge["nodes"][0]) in label_ids else label_name_to_id[edge["nodes"][0]]
            node_2 = ID(edge["nodes"][1]) if ID(edge["nodes"][1]) in label_ids else label_name_to_id[edge["nodes"][1]]
            edges.append(KeypointEdge(node_1=node_1, node_2=node_2))

        positions = []
        for position in keypoint_structure_data["positions"]:
            node = ID(position["label"]) if ID(position["label"]) in label_ids else label_name_to_id[position["label"]]
            x = position["x"]
            y = position["y"]
            positions.append(KeypointPosition(node=node, x=x, y=y))

        return KeypointStructure(edges=edges, positions=positions)

    @classmethod
    def edit_existing_project(  # noqa: C901, PLR0912, PLR0915
        cls,
        project: Project,
        class_parser: type[ProjectUpdateParser],
        parser_kwargs: dict,
    ) -> tuple[Project, LabelSchema, dict[str, LabelSchemaView], tuple[str, ...], dict[ID, set[ID]], bool]:
        """
        Updates an existing project by editing the following:
            - project's name
            - labels
            - label schema

        The labels update process will happen in this order:
            1. edit any existing labels
            2. remove any labels
            3. add any labels
        Throughout the label update process, the list 'updated_labels' will contain all
        the changes from the steps above. The "modified_annotation_scene_ids" set tracks all the IDs for all
        annotation scenes that were meaningfully modified (this excludes setting revisit state).

        Unlike ProjectBuilder.build_full_project(), this method does access and save to
        the database, making the edits to the database in place.

        :param project: the project to be edited
        :param class_parser: a parser which will be used to get relevant information from the REST response
        :param parser_kwargs: arguments to pass to the parser for initialization
        :return: tuple containing:
           - the updated project
           - the updated project label schema
           - a dict mapping each task to its updated label schema view
           - a tuple of labels to revisit,
           - a dict mapping each dataset storage ID to the set of the modified annotation scenes
           - a bool to communicate whether the labels structure changed (e.g. labels were added or removed)
        """
        parser = class_parser(**parser_kwargs)
        ProjectUpdateValidator().validate(parser=parser)
        project_repo = ProjectRepo()
        label_schema_repo = LabelSchemaRepo(project.identifier)

        # Update project details
        project.name = parser.get_project_name()

        label_schema = label_schema_repo.get_latest()

        task_graph = project.task_graph
        ordered_trainable_tasks = [task for task in task_graph.ordered_tasks if task.task_properties.is_trainable]

        child_to_parent_id = {}
        labels_by_task = {}
        group_name_by_label = {}
        task_to_label_schema_view: dict[str, LabelSchemaView] = {}
        task_id_to_schema_revision_id = {}
        labels_structure_changed = False  # will be set to 'True' if there is any change in the labels topology
        labels_to_revisit = []
        modified_scene_ids_by_storage: dict[ID, set[ID]] = {
            storage.id_: set() for storage in project.get_dataset_storages()
        }
        is_keypoint_detection_enabled = FeatureFlagProvider.is_enabled(FEATURE_FLAG_KEYPOINT_DETECTION)
        for task_node in ordered_trainable_tasks:
            task_name = task_node.title
            label_schema_view = label_schema_repo.get_latest_view_by_task(task_node_id=task_node.id_)
            if isinstance(label_schema_view, NullLabelSchema):
                raise ProjectUpdateError(f"Cannot find the label schema view for task with ID '{task_node.id_}'")
            task_to_label_schema_view[task_name] = label_schema_view
            task_id_to_schema_revision_id[task_node.id_] = label_schema_view.id_
            # old_labels contains ALL labels for the task, even empty ones
            old_labels = label_schema_view.get_labels(include_empty=True)
            old_label_names = [label.name for label in old_labels]
            old_groups = label_schema.get_groups(include_empty=True)
            updated_labels, any_label_edited = PersistedProjectBuilder.edit_labels(
                project_identifier=project.identifier,
                parser=parser,
                task_name=task_name,
                old_labels=old_labels,  # type: ignore[arg-type]
                old_groups=old_groups,
            )
            added_label_names = parser.get_added_labels_names_by_task(task_name=task_name)
            removed_label_names = parser.get_deleted_labels_names_by_task(task_name=task_name)
            if removed_label_names or added_label_names:
                labels_structure_changed = True
            # Remove the removed labels from the edited_labels first, as there is no need to
            # check through any newly added labels
            for removed_label_name in removed_label_names:
                for label in updated_labels:
                    if label.name == removed_label_name:
                        modified_scene_ids_by_storage_for_label = ProjectBuilder._remove_label_from_project(
                            project=project, label=label
                        )
                        # Update the sets of modified scenes and list of updated labels
                        for (
                            storage_id,
                            scene_ids,
                        ) in modified_scene_ids_by_storage_for_label.items():
                            modified_scene_ids_by_storage[storage_id].update(scene_ids)
                        updated_labels.remove(label)
                        break
            # Create and add the new labels to the edited_labels
            for added_label_name in added_label_names:
                if added_label_name in old_label_names:
                    continue
                label_hotkey = parser.get_label_hotkey_by_name(
                    task_name=task_name,
                    label_name=added_label_name,
                )
                label_color = parser.get_label_color_by_name(
                    task_name=task_name,
                    label_name=added_label_name,
                )
                project_label = Label(
                    name=added_label_name,
                    domain=task_node.task_properties.task_type.domain,
                    color=Color.from_hex_str(label_color),
                    hotkey=label_hotkey,
                    id_=LabelRepo.generate_id(),
                    is_anomalous=task_node.task_properties.is_anomaly,
                )
                revisit = parser.get_revisit_state_by_label_name(
                    task_name=task_name,
                    label_name=added_label_name,
                )
                if revisit:
                    labels_to_revisit.append(added_label_name)
                updated_labels.append(project_label)
            # Make the LabelGroup and child->parent mapping with the new list of labels
            for label in updated_labels:
                if label.is_empty:
                    continue
                label_group = parser.get_label_group_by_name(
                    task_name=task_name,
                    label_name=label.name,
                )
                label_parent = parser.get_label_parent_by_name(
                    task_name=task_name,
                    label_name=label.name,
                )
                if label_parent:
                    child_to_parent_id[label] = label_parent
                group_name_by_label[label.id_] = label_group
            labels_by_task[task_node.id_] = updated_labels

            if is_keypoint_detection_enabled and task_node.task_properties.task_type == TaskType.KEYPOINT_DETECTION:
                keypoint_structure_data = parser.get_keypoint_structure_data(task_name=task_name)
                keypoint_structure = cls._build_keypoint_structure(
                    keypoint_structure_data=keypoint_structure_data,
                    labels=updated_labels,
                )
                project.keypoint_structure = keypoint_structure

        if labels_structure_changed:
            # Labels structure changed, so the label_schema and task_to_label_schema_view are recomputed from scratch.
            (
                label_schema,
                task_to_label_schema_view,
            ) = ProjectBuilder._build_label_schema(  # type: ignore[assignment]
                project=project,
                labels_by_task=labels_by_task,
                group_name_by_label_id=group_name_by_label,
                child_to_parent_id=child_to_parent_id,  # type: ignore
                previous_schema_revision_id=label_schema.id_,
                previous_task_id_to_schema_revision_id=task_id_to_schema_revision_id,
            )
            label_schema_repo.save(instance=label_schema)
            for _, task_label_schema in task_to_label_schema_view.items():
                label_schema_repo.save(instance=task_label_schema)

        project_repo.save(instance=project)
        return (
            project,
            label_schema,
            task_to_label_schema_view,
            tuple(labels_to_revisit),
            modified_scene_ids_by_storage,
            labels_structure_changed,
        )


class PersistedProjectBuilder(ProjectBuilder):
    """
    PersistedProjectBuilder which extends ProjectBuilder class

    The class will save the entities to the database
    """

    @classmethod
    def build_full_project(
        cls, creator_id: str, parser_class: type[ProjectParser], parser_kwargs: dict
    ) -> tuple[Project, LabelSchema, dict[str, LabelSchemaView]]:
        """
        Overrides the method from the super ProjectBuilder

        Calls ProjectBuilder.build_full_project() and saves the entities to the database.

        :param creator_id: the ID of who created the project
        :param parser_class: a parser which will be used to get relevant information from the REST response
        :param parser_kwargs: arguments to pass to the parser for initialization
        :return: the project, the label schema, and a mapping of task to label schema view
        """
        (
            project,
            label_schema,
            task_to_label_schema_view,
        ) = super().build_full_project(creator_id=creator_id, parser_class=parser_class, parser_kwargs=parser_kwargs)
        return project, label_schema, task_to_label_schema_view

    @classmethod
    def _build_model_storage(
        cls,
        project_identifier: ProjectIdentifier,
        task_node: TaskNode,
        model_template: ModelTemplate,
    ) -> ModelStorage:
        """
        Build a ModelStorage.

        :param project_identifier: identifier of the project
        :param task_node: the TaskNode for the ModelStorage
        :param model_template: the ModelTemplate for the ModelStorage
        :return: the ModelStorage
        """
        model_storage_repo = ModelStorageRepo(project_identifier)
        model_storage = super()._build_model_storage(
            project_identifier=project_identifier,
            task_node=task_node,
            model_template=model_template,
        )
        model_storage_repo.save(instance=model_storage)
        return model_storage

    @classmethod
    def _build_active_model_state(
        cls,
        model_storage: ModelStorage,
        task_node_id: ID,
    ) -> ActiveModelState:
        """
        Build an active model state.

        :param model_storage: the ModelStorage
        :param task_node_id: the TaskNode ID
        :return: the ActiveModelState
        """
        active_model_repo = ActiveModelStateRepo(model_storage.project_identifier)
        active_model_state = super()._build_active_model_state(
            model_storage=model_storage,
            task_node_id=task_node_id,
        )
        active_model_repo.save(instance=active_model_state)
        return active_model_state

    @classmethod
    def _build_dataset_storage(
        cls,
        project_identifier: ProjectIdentifier,
        name: str,
        creator: str,
        use_for_training: bool,
    ) -> DatasetStorage:
        """
        Build a DatasetStorage.

        :param project_identifier: Identifier of the project containing the dataset storage
        :param name: the name of the DatasetStorage
        :param creator: the creator of the DatasetStorage
        :param use_for_training: True if the DatasetStorage will be used for training, otherwise False.
        :return: the DatasetStorage
        """
        dataset_storage_repo = DatasetStorageRepo(project_identifier)
        dataset_storage = super()._build_dataset_storage(
            project_identifier=project_identifier,
            name=name,
            creator=creator,
            use_for_training=use_for_training,
        )
        dataset_storage_repo.save(instance=dataset_storage)
        return dataset_storage

    @classmethod
    def _build_task_graph(
        cls,
        task_nodes: Sequence[TaskNode],
        connections: Sequence[tuple[str, str]],
    ) -> TaskGraph:
        """
        Build a TaskGraph which sorts out all the connections between the task_nodes.

        :param task_nodes: the TaskNodes in the TaskGraph
        :param connections: the connections as task_name_1 to task_name_2 between two task_nodes
        :return: a TaskGraph containing the TaskNodes and the relations between them as TaskEdges
        """
        workspace_id = CTX_SESSION_VAR.get().workspace_id
        if len(task_nodes) == 0:
            raise ValueError("Cannot build TaskGraph with 0 nodes")
        project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=task_nodes[0].project_id)
        task_node_repo = TaskNodeRepo(project_identifier)
        task_graph = super()._build_task_graph(
            task_nodes=task_nodes,
            connections=connections,
        )
        for task_node in task_graph.tasks:
            task_node_repo.save(instance=task_node)
        return task_graph

    @classmethod
    def _build_project(
        cls,
        project_id: ID,
        task_graph: TaskGraph,
        project_name: str,
        description: str,
        creator_id: str,
        keypoint_structure: KeypointStructure | None,
    ) -> Project:
        """
        Build the Project with is dataset storage.

        :param task_graph: the TaskGraph of the project
        :param project_name:  the name of the project
        :param description: the description of the project
        :param creator_id: the creator of the project
        :param keypoint_structure: the keypoint structure of the project
        :return: the Project
        """
        project_repo = ProjectRepo()
        project = super()._build_project(
            project_id=project_id,
            task_graph=task_graph,
            project_name=project_name,
            description=description,
            creator_id=creator_id,
            keypoint_structure=keypoint_structure,
        )
        project_repo.save(instance=project)
        return project

    @classmethod
    def _edit_label(
        cls,
        project_identifier: ProjectIdentifier,
        label: Label,
        label_name: str,
        label_color_hex_str: str,
        label_hotkey: str,
    ) -> Label:
        """
        Edits the values of a label

        :param project_identifier: identifier of the project where the label is defined
        :param label: the label to be edited
        :param label_name: the label's new name
        :param label_color_hex_str: the label's new color
        :param label_hotkey: the label's new hotkey
        :return: The edited label
        """
        label_repo = LabelRepo(project_identifier)
        label = super()._edit_label(
            project_identifier=project_identifier,
            label=label,
            label_name=label_name,
            label_color_hex_str=label_color_hex_str,
            label_hotkey=label_hotkey,
        )
        label_repo.save(label)
        return label

    @classmethod
    def _build_label_schema(
        cls,
        project: Project,
        labels_by_task: dict[ID, list[Label]],
        group_name_by_label_id: dict[ID, str],
        child_to_parent_id: dict[Label, str | ID],
        previous_schema_revision_id: ID | None = None,
        previous_task_id_to_schema_revision_id: dict[ID, ID] | None = None,
    ) -> tuple[LabelSchema, dict[str, LabelSchemaView]]:
        """
        Build the LabelSchema for the project, and the LabelSchemaView for each task.

        A project  LabelSchema is built, and then gets LabelGroups added to it per task.

        The label relations between the tasks are determined by the ordered list of tasks
        returned by project.task_graph.ordered_tasks().

        :param project: the project which is associated to the label schema
        :param labels_by_task: a dictionary mapping the task ID to a set of labels
        :param group_name_by_label_id: a dictionary mapping a label ID/name to a group name
        :param child_to_parent_id: a dictionary mapping a label to its parent's ID
        :param previous_schema_revision_id: the ID of the project's previous LabelSchema
        :param previous_task_id_to_schema_revision_id: a dictionary mapping a task ID to a LabelSchema ID
        :return: the LabelSchema, and a dictionary mapping task title to LabelSchemaView
        """
        label_schema_repo = LabelSchemaRepo(project.identifier)
        label_schema, task_title_to_label_schema = super()._build_label_schema(
            project=project,
            labels_by_task=labels_by_task,
            group_name_by_label_id=group_name_by_label_id,
            child_to_parent_id=child_to_parent_id,
            previous_schema_revision_id=previous_schema_revision_id,
            previous_task_id_to_schema_revision_id=previous_task_id_to_schema_revision_id,
        )
        label_schema_repo.save(instance=label_schema)
        for _, task_label_schema in task_title_to_label_schema.items():
            label_schema_repo.save(instance=task_label_schema)
        return label_schema, task_title_to_label_schema


class ModelTemplateError(ValueError):
    """
    Represents error in creating model templates
    """


class ProjectBuildError(ValueError):
    """
    Represents error in building a project
    """


class ProjectUpdateError(ValueError):
    """
    Represents error in updating a project
    """

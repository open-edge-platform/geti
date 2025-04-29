# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module defines the project factory
"""

import logging
from typing import cast
from warnings import warn

from sc_sdk.algorithms import ModelTemplateList
from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.configuration.elements.hyper_parameters import HyperParameters
from sc_sdk.entities.active_model_state import ActiveModelState
from sc_sdk.entities.color import Color
from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.keypoint_structure import KeypointEdge, KeypointPosition, KeypointStructure
from sc_sdk.entities.label import Domain, Label
from sc_sdk.entities.label_schema import LabelGroup, LabelGroupType, LabelSchema, LabelSchemaView, LabelTree
from sc_sdk.entities.model_storage import ModelStorage
from sc_sdk.entities.model_template import ModelTemplate, NullModelTemplate
from sc_sdk.entities.project import Project
from sc_sdk.entities.task_graph import TaskEdge, TaskGraph
from sc_sdk.entities.task_node import TaskNode, TaskProperties
from sc_sdk.repos import (
    ActiveModelStateRepo,
    ConfigurableParametersRepo,
    DatasetStorageRepo,
    LabelRepo,
    LabelSchemaRepo,
    ModelStorageRepo,
    ProjectRepo,
    TaskNodeRepo,
)
from sc_sdk.services.model_service import ModelService
from sc_sdk.utils.constants import DEFAULT_USER_NAME
from sc_sdk.utils.deletion_helpers import DeletionHelpers
from sc_sdk.utils.feature_flags import FeatureFlagProvider

from geti_types import CTX_SESSION_VAR, ID, ProjectIdentifier

logger = logging.getLogger(__name__)

FEATURE_FLAG_KEYPOINT_DETECTION = "FEATURE_FLAG_KEYPOINT_DETECTION"


class ProjectFactory:
    """
    Project factory class
    """

    warn(
        "ProjectFactory is deprecated and shall not be used for production code; use ProjectBuilder instead",
        DeprecationWarning,
        2,
    )

    @staticmethod
    def save_pipeline_to_project(
        task_graph: TaskGraph, model_templates: list[ModelTemplate], project: Project
    ) -> Project:
        """
        Save/update entries in a TaskGraph. It saves the TaskNodes, ModelStorages, and
        ActiveModelStates and sets the correct Project/TaskNode id to the applicable entity.

        Saves the task graph to the project and reloads the project to return the correct task graph.

        :param task_graph: TaskGraph with entities to save
        :param model_templates: List of model templates to create the model storages for each task
        :param project: Project where TaskGraph belongs to
        :return: Project with updated task graph
        """
        # save dataset storage
        dataset_storage = project.get_training_dataset_storage()
        DatasetStorageRepo(project.identifier).save(dataset_storage)
        # Create nodes
        for i, task in enumerate(task_graph.tasks):
            # Update task node
            task._project_id = project.id_
            TaskNodeRepo(project.identifier).save(instance=task)

            model_template = model_templates[i]
            active_model_storage = ModelStorage(
                id_=ModelStorageRepo.generate_id(),
                project_id=project.id_,
                task_node_id=task.id_,
                model_template=model_template,
            )
            ModelStorageRepo(project.identifier).save(instance=active_model_storage)

            active_model_state = ActiveModelState(
                task_node_id=task.id_,
                active_model_storage=active_model_storage,
            )
            ActiveModelStateRepo(project.identifier).save(instance=active_model_state)

        project.task_graph = task_graph
        ProjectRepo().save(instance=project)
        return ProjectRepo().get_by_id(project.id_)  # todo: rebuild the graph to save DB connection

    @staticmethod
    def create_project_with_task_graph(  # noqa: PLR0913
        name: str,
        creator_id: str,
        description: str,
        task_graph: TaskGraph,
        model_templates: list[ModelTemplate],
        project_id: ID | None = None,
        user_names: list[str] | None = None,
        hidden: bool = False,
    ) -> Project:
        """
        Create a project given a task graph

        :param name: Name of the project
        :param creator_id: ID of the user who created the project
        :param project_id: Optional ID of the project to create: If not specified, a
            new ID will be generated
        :param description: Description of the project
        :param task_graph: Task graph
        :param model_templates: List of model templates to create the model storages for each task
        :param user_names: User names to assign to the project
        :param hidden: Whether to keep the project as hidden after creation
        :return: created project
        """
        if project_id is None:
            project_id = ProjectRepo.generate_id()
        workspace_id = CTX_SESSION_VAR.get().workspace_id
        project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=project_id)

        # Repos
        project_repo = ProjectRepo()

        logger.info(f"Create a project with name {name} with task graph {task_graph}")

        # Check user names
        user_names = user_names if user_names is not None and len(user_names) != 0 else [DEFAULT_USER_NAME]

        # Create dataset storage
        dataset_storage = DatasetStorage(
            name="Dataset",
            project_id=project_id,
            use_for_training=True,
            creator_name=user_names[0],
            _id=DatasetStorageRepo.generate_id(),
        )
        DatasetStorageRepo(project_identifier).save(dataset_storage)
        keypoint_structure = None
        if FeatureFlagProvider.is_enabled(FEATURE_FLAG_KEYPOINT_DETECTION):
            keypoint_structure = KeypointStructure(
                edges=[KeypointEdge(node_1=ID("node_1"), node_2=ID("node_2"))],
                positions=[
                    KeypointPosition(node=ID("node_1"), x=0.123, y=0.123),
                    KeypointPosition(node=ID("node_2"), x=1, y=1),
                ],
            )
        # Create graph with one task
        project = Project(
            id=project_id,
            name=name,
            creator_id=creator_id,
            description=description,
            user_names=user_names,
            dataset_storages=[dataset_storage],
            task_graph=task_graph,
            keypoint_structure=keypoint_structure,
            hidden=True,  # hide until creation is complete
        )
        project_repo.save(project)

        try:
            project = ProjectFactory.save_pipeline_to_project(
                task_graph=task_graph, model_templates=model_templates, project=project
            )
            if not hidden:
                project = project_repo.unhide(project)
        except Exception as ex:
            DeletionHelpers.delete_project_by_id(project_id=project.id_)
            raise PipelineError(f"Unable to set task graph of project: {str(ex)}. Cleaning up.") from ex

        return project

    @staticmethod
    def generate_label_tree(
        labelname_to_parent: dict[str, str] | None = None,
        labelname_to_label: dict[str, Label] | None = None,
    ) -> LabelTree:
        """
        :param labelname_to_parent: Optional. label tree structure
        :param labelname_to_label: Optional. mapping labelname to Label
        :return: Created LabelTee
        """
        label_tree = LabelTree()
        if labelname_to_parent is not None and labelname_to_label is not None:
            for child_name, parent_name in labelname_to_parent.items():
                if len(parent_name) == 0:
                    continue

                if child_name not in labelname_to_label or parent_name not in labelname_to_label:
                    continue

                child_node = labelname_to_label[child_name]
                parent_node = labelname_to_label[parent_name]

                label_tree.add_child(parent_node, child_node)
        return label_tree

    @staticmethod
    def convert_to_sc_label_groups(
        label_groups: list[dict[str, str]] | None = None,
        labelname_to_label: dict[str, Label] | None = None,
    ) -> tuple[list[LabelGroup], set[str]]:
        """
        generate LabelGroup for SC
        :param label_groups: Optional. label group metadata
        :param labelname_to_label: Optional. mapping labelname to Label
        :return: Created SC Label Groups and set of grouped label names
        """
        sc_label_groups = []
        grouped_label_names: set[str] = set()

        if label_groups is not None and labelname_to_label is not None:
            for group_info in label_groups:
                group_name = group_info["name"]
                group_type = (
                    LabelGroupType.EXCLUSIVE if group_info["group_type"] == "exclusive" else LabelGroupType.EMPTY_LABEL
                )
                group_labels = []
                for label_name in group_info["labels"]:
                    if label_name not in labelname_to_label:
                        continue
                    label = labelname_to_label[label_name]
                    group_labels.append(label)
                    grouped_label_names.add(label_name)

                sc_label_groups.append(LabelGroup(name=group_name, labels=group_labels, group_type=group_type))
        return sc_label_groups, grouped_label_names

    @staticmethod
    def create_project_single_task(  # noqa: PLR0915, PLR0913
        name: str,
        description: str,
        creator_id: str,
        labels: list[dict],
        model_template_id: str | ModelTemplate,
        user_names: list[str] | None = None,
        label_schema: LabelSchema | None = None,
        label_groups: list[dict[str, str]] | None = None,
        labelname_to_parent: dict[str, str] | None = None,
        configurable_parameters: ConfigurableParameters | None = None,
        empty_label_name: str | None = None,
        is_multi_label_classification: bool | None = False,
        hidden: bool = False,
    ) -> Project:
        """
        Create a project with one task in the pipeline.

        :param name: Name (title) of the project
        :param description: Description of the project
        :param creator_id: ID of the user who created the project
        :param labels: Labels to create in a dict-like representation.
            Each dict supports the following keys
                - name -> name of the label
                - color -> UI color of the label as hex string
                - is_anomalous -> (optional) whether the label is anomalous; default False.
            This attribute is ignored when label_schema is provided.
        :param model_template_id: Model template for the project
            (either the model template ID or the model template itself)
        :param user_names: User names to assign to the project
        :param configurable_parameters: Optional, configurable parameters to assign
            to the task node in the Project.
        :param workspace: Optional, workspace
        :param label_schema: Optional, label schema relative to the project.
            If provided, then label_names is ignored
            If unspecified, the default workspace is used.
        :param empty_label_name: Optional. If an empty label needs to be created,
            this parameter is used to customize its name.
        :param is_multi_label_classification: Optional. True if created project is multi-label classification
        :param hidden: Whether to keep the project as hidden after creation.
        :param label_groups: Optional. label group metadata
        :param labelname_to_parent: Optional. label tree structure
        :return: Created project
        """
        logger.warning("Method `create_project_single_task` is deprecated.")

        user_names = user_names if user_names is not None else [DEFAULT_USER_NAME]
        if isinstance(model_template_id, ModelTemplate):
            model_template = model_template_id
        else:
            model_template = ModelTemplateList().get_by_id(model_template_id)

        if isinstance(model_template, NullModelTemplate):
            raise ModelTemplateError("A NullModelTemplate was created.")

        CTX_SESSION_VAR.get().workspace_id
        project_id = ProjectRepo.generate_id()
        dataset_template = ModelTemplateList().get_by_id("dataset")
        task_node_id = TaskNodeRepo.generate_id()
        image_dataset_task_node = TaskNode(
            title="Dataset",
            task_properties=TaskProperties.from_model_template(dataset_template),
            project_id=project_id,
            id_=task_node_id,
        )

        task_title = f"{model_template.task_type.name.lower().capitalize()} task"

        task_node_id_2 = TaskNodeRepo.generate_id()
        task_node = TaskNode(
            title=task_title,
            task_properties=TaskProperties.from_model_template(model_template),
            project_id=project_id,
            id_=task_node_id_2,
        )

        task_graph = TaskGraph()
        task_graph.add_node(image_dataset_task_node)
        task_graph.add_node(task_node)

        model_templates = [dataset_template, model_template]

        task_edge = TaskEdge(from_task=image_dataset_task_node, to_task=task_node)
        task_graph.add_task_edge(task_edge)

        project = ProjectFactory.create_project_with_task_graph(
            project_id=project_id,
            name=name,
            creator_id=creator_id,
            description=description,
            user_names=user_names,
            task_graph=task_graph,
            model_templates=model_templates,
            hidden=hidden,
        )

        project_labels: list[Label]
        if label_schema is None:
            label_domain = model_template.task_type.domain
            add_empty_label = label_domain in (
                Domain.DETECTION,
                Domain.SEGMENTATION,
                Domain.INSTANCE_SEGMENTATION,
                Domain.ROTATED_DETECTION,
            )
            # multi-label classification should have an empty label
            if label_domain == Domain.CLASSIFICATION and is_multi_label_classification:
                add_empty_label = True

            project_labels = [
                Label(
                    name=label["name"],
                    domain=label_domain,
                    color=Color.from_hex_str(label["color"]),
                    hotkey=label.get("hotkey", ""),
                    id_=LabelRepo.generate_id(),
                    is_anomalous=label.get("is_anomalous", False),
                )
                for label in labels
            ]

            # generate LabelTree
            labelname_to_label = {label.name: label for label in project_labels}
            label_tree = ProjectFactory.generate_label_tree(
                labelname_to_parent=labelname_to_parent,
                labelname_to_label=labelname_to_label,
            )

            # generate LabelGroup for SC
            (
                sc_label_groups,
                grouped_label_names,
            ) = ProjectFactory.convert_to_sc_label_groups(
                label_groups=label_groups, labelname_to_label=labelname_to_label
            )

            # labels not have an explicite grouping should be included to an exclusive_group
            ungrouped_label_names = [label for label in project_labels if label.name not in grouped_label_names]
            exclusive_group = LabelGroup(
                name="labels",
                labels=ungrouped_label_names,
                group_type=LabelGroupType.EXCLUSIVE,
            )
            sc_label_groups.append(exclusive_group)

            if add_empty_label:
                if empty_label_name is None:
                    empty_label_name = f"Empty {label_domain.name.lower()} label"
                emptylabel = Label(
                    name=empty_label_name,
                    domain=label_domain,
                    color=Color(42, 43, 46),
                    is_empty=True,
                    id_=LabelRepo.generate_id(),
                )
                empty_group = LabelGroup(
                    name="empty",
                    labels=[emptylabel],
                    group_type=LabelGroupType.EMPTY_LABEL,
                )
                sc_label_groups.append(empty_group)
                project_labels.append(emptylabel)

            label_schema = LabelSchema(
                id_=LabelSchemaRepo.generate_id(),
                label_tree=label_tree,
                label_groups=sc_label_groups,
                project_id=project.id_,
            )
        else:
            project_labels = cast("list[Label]", label_schema.get_labels(include_empty=True))
            label_schema._project_id = project.id_

        label_schema_repo = LabelSchemaRepo(project.identifier)
        label_schema_repo.save(label_schema)
        image_dataset_task_node_label_schema = LabelSchemaView.from_parent(
            parent_schema=label_schema,
            labels=project_labels,
            task_node_id=image_dataset_task_node.id_,
            id_=LabelSchemaRepo.generate_id(),
        )
        task_node_label_schema = LabelSchemaView.from_parent(
            parent_schema=label_schema,
            labels=project_labels,
            task_node_id=task_node.id_,
            id_=LabelSchemaRepo.generate_id(),
        )
        label_schema_repo.save(image_dataset_task_node_label_schema)
        label_schema_repo.save(task_node_label_schema)

        if configurable_parameters is not None:
            if task_node.task_properties.is_trainable:
                model_storage = ModelService.get_active_model_storage(
                    project_identifier=project.identifier, task_node_id=task_node.id_
                )
                model_storage_id = model_storage.id_
            else:
                raise ValueError("Unable to set configurable parameters for a non-trainable task.")
            hparams: HyperParameters[ConfigurableParameters] = HyperParameters(
                workspace_id=project.workspace_id,
                project_id=project_id,
                model_storage_id=model_storage_id,
                id_=ConfigurableParametersRepo.generate_id(),
                data=configurable_parameters,
            )
            ConfigurableParametersRepo(project.identifier).save(hparams)

        return project


class PipelineError(ValueError):
    """
    Represents error in project pipeline
    """


class ModelTemplateError(ValueError):
    """
    Represents error in creating model templates
    """

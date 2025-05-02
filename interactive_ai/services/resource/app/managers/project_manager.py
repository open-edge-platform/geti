# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import cast

from geti_spicedb_tools import Permissions, SpiceDB

from communication.exceptions import DatasetStorageNotInProjectException, LabelNotFoundException, ProjectLockedException
from managers.annotation_manager import AnnotationManager

from geti_fastapi_tools.exceptions import BadRequestException, ProjectNotFoundException
from geti_kafka_tools import publish_event
from geti_telemetry_tools import unified_tracing
from geti_types import CTX_SESSION_VAR, ID
from iai_core.adapters.adapter import ReferenceAdapter
from iai_core.entities.dataset_storage import DatasetStorage, NullDatasetStorage
from iai_core.entities.label import Domain, Label
from iai_core.entities.label_schema import LabelSchema, LabelSchemaView, NullLabelSchema
from iai_core.entities.model_template import TaskFamily, TaskType
from iai_core.entities.project import NullProject, Project
from iai_core.entities.task_graph import TaskGraph
from iai_core.factories import ProjectParser, ProjectUpdateParser
from iai_core.repos import ProjectRepo
from iai_core.repos.project_repo_helpers import ProjectQueryData
from iai_core.utils.deletion_helpers import DeletionHelpers
from iai_core.utils.project_builder import PersistedProjectBuilder, ProjectUpdateError

CONNECTIONS = "connections"
FROM = "from"
GROUP = "group"
ID_ = "id"
IS_DELETED = "is_deleted"
LABELS = "labels"
NAME = "name"
PARENT_ID = "parent_id"
REVISIT_AFFECTED_ANNOTATIONS = "revisit_affected_annotations"
TASK_TYPE = "task_type"
TASKS = "tasks"
TITLE = "title"
TO = "to"

logger = logging.getLogger(__name__)


@dataclass
class LabelsAffectedBySchemaChange:
    """
    Container for the labels affected by a change in the label schema

    :var global_old_groups: Labels of global tasks, whose group existed before the schema change
    :var global_new_groups: Labels of global tasks, whose group did NOT exist before the schema change
    :var local: Labels of local tasks
    """

    global_old_groups: tuple[Label, ...]
    global_new_groups: tuple[Label, ...]
    local: tuple[Label, ...]


class ProjectManager:
    @staticmethod
    @unified_tracing
    def create_project(
        creator_id: str,
        workspace_id: ID,
        project_parser: type[ProjectParser],
        parser_kwargs: dict,
    ) -> tuple[Project, LabelSchema, dict[str, LabelSchemaView]]:
        """
        Create a project given a workspace and project rest data.

        :param creator_id: The ID of the user who created the project
        :param workspace_id: id of the workspace this project belongs to.
        :param project_parser: Parser for the project data
        :param parser_kwargs: Input data for the project parser
        :return: Created Project entity, project schema entity,
        and dictionary mapping each task node title to its schema
        """
        (
            project,
            project_schema,
            tasks_schema,
        ) = PersistedProjectBuilder.build_full_project(
            creator_id=creator_id,
            parser_class=project_parser,
            parser_kwargs=parser_kwargs,
        )

        # TODO: CVS-89772 call spicedb before storing a project in database
        SpiceDB().create_project(
            workspace_id=str(workspace_id),
            project_id=str(project.id_),
            creator=creator_id,
        )
        publish_event(
            topic="project_creations",
            body={
                "workspace_id": str(project.workspace_id),
                "project_id": str(project.id_),
            },
            key=str(project.id_).encode(),
            headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
        )

        return project, project_schema, tasks_schema

    @staticmethod
    def compute_labels_affected_by_schema_change(  # noqa: C901
        new_project_label_schema: LabelSchema,
        new_tasks_label_schemas: Mapping[str, LabelSchema],
        new_labels: Sequence[Label],
        labels_names_flagged_to_revisit: Sequence[str],
        task_graph: TaskGraph,
    ) -> LabelsAffectedBySchemaChange:
        """
        Compute the full list of labels that are affected by changes in the label schema.
        The annotations containing these labels will eventually need to be revisited by the user.

        :param new_project_label_schema: Post-update labelSchema relative to the project
        :param new_tasks_label_schemas: Dictionary mapping each task name to its
            relative post-update label schema view
        :param new_labels: Newly added labels
        :param labels_names_flagged_to_revisit: Names of the labels flagged by the user
            as 'to revisit' when editing the schema
        :param task_graph: Task graph of the project
        :return: Three tuples containing:
            - the affected labels of global tasks, belonging to old groups
            - the affected labels of global tasks, belonging to new groups
            - the affected labels of local tasks
        """
        new_labels_names_set: set[str] = {label.name for label in new_labels}

        def _is_label_in_new_group(label: Label) -> bool:
            """Check whether the new label is in a newly created group"""
            siblings = new_project_label_schema.get_siblings_in_group(label=label)
            return all(sibling.name in new_labels_names_set for sibling in siblings)

        affected_labels_global_old_groups: list[Label] = []
        affected_labels_global_new_groups: list[Label] = []
        affected_labels_local: list[Label] = []
        label_name_to_task_id = {
            label.name: task_node.id_
            for task_node in task_graph.tasks
            for label in new_tasks_label_schemas.get(task_node.title, NullLabelSchema()).get_labels(True)
        }

        for name_of_label_to_revisit in labels_names_flagged_to_revisit:
            label = new_project_label_schema.get_label_by_name(label_name=name_of_label_to_revisit)
            if label is None:
                raise LabelNotFoundException(label_name=name_of_label_to_revisit)
            label_task_id = label_name_to_task_id[label.name]
            is_new: bool = name_of_label_to_revisit in new_labels_names_set
            # TODO use task_type.is_local once added CVS-82933
            is_local: bool = label.domain not in [
                task.domain for task in TaskType if task.is_global and task.is_trainable
            ]
            if is_local:
                # Note: multi-label local tasks do not exist in SC.
                affected_labels_local.append(label)
                # All the labels of the other local tasks are affected too, because there may be missing shapes
                for other_task in task_graph.tasks:
                    if (
                        other_task.id_ != label_task_id
                        and other_task.task_properties.task_family == TaskFamily.VISION
                        and not other_task.task_properties.is_global
                    ):
                        other_task_schema = new_tasks_label_schemas[other_task.title]
                        other_task_labels = cast(
                            "list[Label]",
                            other_task_schema.get_labels(include_empty=False),
                        )
                        affected_labels_local.extend(other_task_labels)
            else:  # global
                if is_new:
                    # If the label is added to an existing group, e.g. multi-class addition, then no action
                    # is required because the old labels in that group are not uncertain.
                    # Vice versa, if the group is new, then the shapes must be revisited for that group
                    # because no information about the group is already present in the annotations.
                    if _is_label_in_new_group(label=label):
                        affected_labels_global_new_groups.append(label)
                else:  # old
                    # Existing labels explicitly marked as 'to revisit' are affected, regardless of their exclusivity
                    affected_labels_global_old_groups.append(label)
                # In case of task chain, it's necessary to revisit the local parents too (if any)
                # because there may be missing shapes (ROIs).
                label_pointer = label
                while (
                    parent := cast(
                        "Label",
                        new_project_label_schema.get_parent(label=label_pointer),
                    )
                ) is not None:
                    if parent.domain != Domain.CLASSIFICATION:
                        affected_labels_local.append(cast("Label", parent))
                    label_pointer = parent

        # Remove duplicates and freeze
        return LabelsAffectedBySchemaChange(
            local=tuple(set(affected_labels_local)),
            global_old_groups=tuple(set(affected_labels_global_old_groups)),
            global_new_groups=tuple(set(affected_labels_global_new_groups)),
        )

    @staticmethod
    def _verify_project_update_ready(project: Project):  # noqa: ANN205
        """
        This function checks if the project can be updated. The project can't be locked if it is to be updated.
        Does not raise an error if the project is persisted in the database.

        :param project: Project to check
        """
        try:
            if ProjectRepo().read_lock(project_id=project.id_):
                logger.info(
                    "Rejecting request to update project `%s` (ID %s) because it is locked.",
                    project.name,
                    project.id_,
                )
                raise ProjectLockedException(name=project.name)
        except ValueError:
            logger.exception("Cannot read lock for project with ID '%s'", project.id_)

    @staticmethod
    @unified_tracing
    def update_project(
        project: Project,
        project_update_parser: type[ProjectUpdateParser],
        parser_kwargs: dict,
    ) -> tuple[Project, LabelSchema, dict[str, LabelSchemaView]]:
        """
        Update a project from request data, including name, label names and colors.

        :param project: project to be updated.
        :param project_update_parser: Parser for project update data
        :param parser_kwargs: Input data for the project update parser
        """
        ProjectManager._verify_project_update_ready(project=project)

        try:
            (
                project,
                label_schema,
                tasks_schemas,
                labels_to_revisit,
                modified_scene_ids_by_storage,
                labels_structure_changed,
            ) = PersistedProjectBuilder.edit_existing_project(
                project=project,
                class_parser=project_update_parser,
                parser_kwargs=parser_kwargs,
            )
        except ProjectUpdateError as raised_error:
            raise BadRequestException(raised_error.args[0])

        if labels_structure_changed:
            # If the label schema changed, then it is necessary to revisit the annotations affected by it
            new_labels = label_schema.get_labels(include_empty=True)
            logger.info(
                "Label structure changed in project with ID %s: %s",
                project.id_,
                new_labels,
            )
            affected_labels = ProjectManager.compute_labels_affected_by_schema_change(
                new_project_label_schema=label_schema,
                new_tasks_label_schemas=tasks_schemas,
                new_labels=new_labels,
                labels_names_flagged_to_revisit=labels_to_revisit,
                task_graph=project.task_graph,
            )
            scenes_to_revisit_ids_by_storage = AnnotationManager.suspend_annotations_by_labels(
                project=project,
                global_labels_to_revisit_if_present=affected_labels.global_old_groups,
                global_labels_to_revisit_unconditionally=affected_labels.global_new_groups,
                local_labels_to_revisit=affected_labels.local,
            )

            # Notify the other microservices about new annotations to revisit
            any_scene_to_revisit = any(scenes_to_revisit_ids_by_storage.values())
            if any_scene_to_revisit:
                AnnotationManager.publish_annotation_scenes_to_revisit(
                    project_id=project.id_,
                    scenes_to_revisit_ids_by_storage=scenes_to_revisit_ids_by_storage,
                )

            # Notify the other microservice about modified annotation scenes
            for dataset_storage_id, scene_ids in modified_scene_ids_by_storage.items():
                for scene_id in scene_ids:
                    AnnotationManager.publish_annotation_scene(
                        annotation_scene_id=scene_id,
                        project_id=project.id_,
                        workspace_id=project.workspace_id,
                        dataset_storage_id=dataset_storage_id,
                    )

        # Notify the other microservices about changes in the project
        publish_event(
            topic="project_updates",
            body={
                "project_id": str(project.id_),
                "workspace_id": str(project.workspace_id),
            },
            key=str(project.id_).encode(),
            headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
        )

        return project, label_schema, tasks_schemas

    @staticmethod
    @unified_tracing
    def delete_project(project_id: ID):  # noqa: ANN205
        """
        Delete a project by ID.

        :param project_id: ID of the project to remove
        :raises: ProjectNotFoundException if the project does not exist
        """
        project = ProjectManager.get_project_by_id(project_id=project_id)

        if ProjectRepo().read_lock(project_id=project.id_):
            raise ProjectLockedException(name=project.name)

        # This is a workaround and should be fixed
        # CVS-86033
        project_repo = ProjectRepo()
        project_repo.hide(project)

        DeletionHelpers.delete_project_by_id(project_id=project_id)
        SpiceDB().delete_project(project_id)

        publish_event(
            topic="project_deletions",
            body={
                "workspace_id": str(project.workspace_id),
                "project_id": str(project_id),
                "training_dataset_storage_id": str(project.training_dataset_storage_id),
            },
            key=str(project.id_).encode(),
            headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
        )

    @staticmethod
    @unified_tracing
    def get_project_by_id(project_id: ID) -> Project:
        """
        Get a project given its ID.

        :param project_id: ID of the project
        :return: Project
        :raises: ProjectNotFoundException if the project is not found
        """
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)
        return project

    @staticmethod
    @unified_tracing
    def get_projects_names(user_uid: str) -> dict[ID, str]:
        """
        Returns projects names.

        :param user_uid: caller user's uid
        :return: all ID's of projects found (accessible for the caller) with their names
        """
        permitted_projects = SpiceDB().get_user_projects(user_id=user_uid, permission=Permissions.VIEW_PROJECT)
        permitted_project_ids = tuple(ID(project_id) for project_id in permitted_projects)
        return ProjectRepo().get_names(permitted_project_ids)

    @staticmethod
    @unified_tracing
    def get_projects_and_count_all(
        user_uid: str,
        query_data: ProjectQueryData,
        include_hidden: bool = True,
    ) -> tuple[list[Project], int]:
        """
        Get a list of projects in a workspace with pagination.

        :param user_uid: caller user's uid
        :param query_data: ProjectQueryData object with request params for filtering and pagination
        :param include_hidden: Whether to include hidden (not fully created) projects
        :return: list of Project in the workspace with filtering and pagination and count of all projects in workspace
        """
        permitted_projects = SpiceDB().get_user_projects(user_id=user_uid, permission=Permissions.VIEW_PROJECT)
        permitted_project_ids = tuple(ID(project_id) for project_id in permitted_projects)
        project_repo = ProjectRepo()
        projects = project_repo.get_by_page(
            query_data=query_data,
            include_hidden=include_hidden,
            permitted_projects=permitted_project_ids,
        )
        count = project_repo.count_all(include_hidden=include_hidden, permitted_projects=permitted_project_ids)
        return projects, count

    @staticmethod
    @unified_tracing
    def add_dataset_storage(project, dataset_storage: DatasetStorage) -> Project:  # noqa: ANN001
        """
        Add new dataset storage to project

        :param project: project to add DS to
        :param dataset_storage: dataset storage to add in project
        :return: updated project entity
        """
        if dataset_storage.workspace_id != project.workspace_id:
            raise BadRequestException(
                f"Dataset storage must be added to a project in the same workspace. "
                f"Dataset Storage's Workspace ID: {dataset_storage.workspace_id}; "
                f"Project's Workspace ID: {project.workspace_id}"
            )
        if dataset_storage.id_ in project.dataset_storage_ids:
            raise BadRequestException(
                f"Attempting to add dataset storage `{dataset_storage.name}` to project "
                f"`{project.name}`, but it already exists in the project. "
                f"Dataset Storage ID `{dataset_storage.id_}`, Project ID: `{project.id_}`."
            )
        project.dataset_storage_adapters.append(ReferenceAdapter(dataset_storage))
        ProjectRepo().save(project)
        return project

    @staticmethod
    @unified_tracing
    def get_dataset_storage_by_id(project: Project, dataset_storage_id: ID) -> DatasetStorage:
        """
        Return dataset storage with given id if exists in project, otherwise raise exception

        :param project: Project including dataset_storage
        :param dataset_storage_id: ID of dataset storage
        :return: dataset storage entity
        """
        dataset_storage = project.get_dataset_storage_by_id(dataset_storage_id)
        if isinstance(dataset_storage, NullDatasetStorage):
            raise DatasetStorageNotInProjectException(project=project, dataset_storage_id=dataset_storage_id)
        return dataset_storage

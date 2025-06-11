# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

from communication.exceptions import NotEnoughSpaceException
from communication.limit_check_helpers import check_max_number_of_projects
from communication.rest_data_validator import ProjectRestValidator
from communication.rest_parsers import RestProjectParser, RestProjectUpdateParser
from communication.rest_views.project_rest_views import ProjectRESTViews
from managers.project_manager import ProjectManager
from service.label_schema_service import LabelSchemaService

from geti_fastapi_tools.responses import success_response_rest
from geti_telemetry_tools import unified_tracing
from geti_types import ID
from iai_core.entities.label_schema import LabelSchemaView
from iai_core.entities.project import Project
from iai_core.repos.project_repo_helpers import ProjectQueryData
from iai_core.utils.filesystem import check_free_space_for_operation, compute_project_size

DESCRIPTION = "description"
NAME = "name"
PIPELINE = "pipeline"


class ProjectRESTController:
    @staticmethod
    def create_project(
        data: dict,
        organization_id: ID,
        creator_id: str,
        workspace_id: ID,
    ) -> dict[str, Any]:
        """
        Create a new project.

        :param data: Dict containing the information needed to create the project
        :param organization_id: ID of the organization who created the project
        :param creator_id: ID of the user who created the project
        :param workspace_id: ID of the workspace to attach the project to.
        :return: success or error REST response
        """
        check_max_number_of_projects()
        check_free_space_for_operation(operation="Project creation", exception_type=NotEnoughSpaceException)

        ProjectRestValidator().validate_creation_data_statically(data)

        project, _, tasks_schema = ProjectManager.create_project(
            creator_id=creator_id,
            workspace_id=workspace_id,
            project_parser=RestProjectParser,
            parser_kwargs={"rest_data": data},
        )

        label_schema_per_task: dict[ID, LabelSchemaView] = {
            task_node.id_: tasks_schema[task_node.title] for task_node in project.get_trainable_task_nodes()
        }

        return ProjectRESTViews.project_to_rest(
            organization_id=organization_id,
            project=project,
            label_schema_per_task=label_schema_per_task,
            storage_info={},
        )

    @staticmethod
    def update_project(organization_id: ID, project_id: ID, data: dict) -> dict[str, Any]:
        """
        Update an existing project.

        One can change properties like the project name, description, edit the labels
        and even add new ones.

        :param organization_id: ID of the organization
        :param project_id: ID of the project to update
        :param data: Dict containing the new information to update the project
        :return: Project REST view or error response
        :raises: ProjectNotFoundException if the project is not found
        """
        project = ProjectManager.get_project_by_id(project_id=project_id)
        ProjectRestValidator().validate_update_data_statically(data)

        project, _, tasks_schema = ProjectManager.update_project(
            project=project,
            project_update_parser=RestProjectUpdateParser,
            parser_kwargs={"rest_data": data},
        )

        label_schema_per_task: dict[ID, LabelSchemaView] = {
            task_node.id_: tasks_schema[task_node.title] for task_node in project.get_trainable_task_nodes()
        }

        return ProjectRESTViews.project_to_rest(
            organization_id=organization_id,
            project=project,
            label_schema_per_task=label_schema_per_task,
            storage_info={},
        )

    @staticmethod
    def delete_project(project_id: ID) -> dict[str, Any]:
        """
        Delete an existing project.

        :param project_id: ID of the project to delete
        :return: success or error REST response
        """
        ProjectManager.delete_project(project_id=project_id)

        return success_response_rest()

    @staticmethod
    def get_project(
        organization_id: ID,
        project_id: ID,
        with_size: bool = False,
        include_deleted_labels: bool = False,
    ) -> dict[str, Any]:
        """
        Get a REST view of a project by ID.

        :param organization_id: ID of the organization
        :param project_id: ID of the project to get
        :param with_size: If the rest representation should include the size of the project
        :param include_deleted_labels: If the rest representation should include labels
        that have been deleted
        :return: Project REST view or error response
        """
        project = ProjectManager.get_project_by_id(project_id=project_id)
        label_schema_per_task = ProjectRESTController._get_label_schema_per_task(project=project)
        storage_info = {}
        if with_size:
            storage_info = {"size": compute_project_size(project=project)}
        return ProjectRESTViews.project_to_rest(
            organization_id=organization_id,
            project=project,
            label_schema_per_task=label_schema_per_task,
            include_deleted_labels=include_deleted_labels,
            storage_info=storage_info,
        )

    @staticmethod
    @unified_tracing
    def get_projects_names(user_id: ID) -> dict[str, list[dict[str, str]]]:
        """
        Returns projects names.

        :param user_id: ID of the user who requests projects names
        :return: all ID's of permitted projects found with their names
        """
        projects_names = ProjectManager.get_projects_names(user_uid=user_id)
        return ProjectRESTViews.projects_names_to_rest(projects_names)

    @staticmethod
    @unified_tracing
    def get_projects(
        user_id: ID,
        organization_id: ID,
        query_data: ProjectQueryData,
        url: str,
        include_hidden: bool = True,
    ) -> dict[str, Any]:
        """
        Get the list of existing REST projects.

        :param user_id: ID of the user to requested the projects
        :param organization_id: ID of the organization
        :param query_data: ProjectQueryData object with request params
        :param url: url taken from request params
        :param include_hidden: Whether to include hidden (not fully created) projects
        :return: List of projects REST view or error response
        """
        projects, project_counts = ProjectManager.get_projects_and_count_all(
            user_uid=user_id, query_data=query_data, include_hidden=include_hidden
        )
        next_page = ""
        if len(projects) > 0:
            next_page = ProjectRESTController.get_next_page(url=url, skip=query_data.skip + len(projects))
        label_schema_per_task_per_project = []
        storage_info_per_project = []
        for project in projects:
            label_schema_per_task_per_project.append(ProjectRESTController._get_label_schema_per_task(project=project))
            if query_data.with_size:
                storage_info_per_project.append({"size": compute_project_size(project=project)})
            else:
                storage_info_per_project.append({})
        return ProjectRESTViews.projects_to_rest(
            organization_id=organization_id,
            projects=projects,
            label_schema_per_task_per_project=label_schema_per_task_per_project,
            project_counts=project_counts,
            next_page=next_page,
            storage_info_per_project=storage_info_per_project,
        )

    @staticmethod
    def get_next_page(url: str, skip: int) -> str:
        parsed_url = urlparse(url)
        path = parsed_url.path
        query = parsed_url.query
        query_params = parse_qs(query)
        query_params["skip"] = [str(skip)]
        updated_query = urlencode(query_params, doseq=True)
        return f"{path}?{updated_query}"

    @staticmethod
    def _get_label_schema_per_task(
        project: Project,
    ) -> dict[ID, LabelSchemaView]:
        label_schema_per_task: dict[ID, LabelSchemaView] = {
            task_node.id_: LabelSchemaService.get_latest_label_schema_for_task(
                project_identifier=project.identifier,
                task_node_id=task_node.id_,
            )
            for task_node in project.task_graph.tasks
            if task_node.task_properties.is_trainable
        }
        return label_schema_per_task

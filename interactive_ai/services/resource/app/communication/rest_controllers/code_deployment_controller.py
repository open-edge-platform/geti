# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import contextvars
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from communication.exceptions import NotEnoughSpaceException
from communication.rest_data_validator import CodeDeploymentRESTValidator
from communication.rest_views.code_deployment_rest_views import CodeDeploymentRestViews
from communication.rest_views.project_rest_views import ProjectRESTViews
from entities.deployment import CodeDeployment, ModelIdentifier
from managers.project_manager import ProjectManager
from repos.code_deployment_repo import CodeDeploymentRepo
from resource_management.code_deployment_manager import DEPLOYMENT_FILENAME_TEMPLATE, CodeDeploymentManager
from service.label_schema_service import LabelSchemaService

from geti_telemetry_tools import unified_tracing
from geti_types import ID, ProjectIdentifier
from iai_core.entities.label_schema import LabelSchemaView
from iai_core.entities.project import Project
from iai_core.utils.filesystem import check_free_space_for_operation
from iai_core.utils.naming_helpers import slugify

export_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="Code_deployment_worker")
logger = logging.getLogger(__name__)


class CodeDeploymentRESTController:
    @staticmethod
    @unified_tracing
    def prepare_for_code_deployment(
        organization_id: ID,
        workspace_id: ID,
        project_id: ID,
        model_list_rest: dict,
        user_id: ID,
    ) -> dict:
        """
        Collects the models to be included in the code deployment
        Triggers the asynchronous zip file preparation
        Returns code deployment entity REST view as a response

        :param organization_id: the ID of the organization
        :param workspace_id: the ID of the workspace of the models
        :param project_id: the ID of the project of the models
        :param model_list_rest: the REST request containing the models to export
        :param user_id: ID of the user who made the request
        :return: REST View of code deployment or error responses
        """
        check_free_space_for_operation(operation="Code deployment", exception_type=NotEnoughSpaceException)

        project_identifier = ProjectIdentifier(
            workspace_id=workspace_id,
            project_id=project_id,
        )

        # validate code deployment
        CodeDeploymentRESTValidator().validate_code_deployment(model_list_rest)

        # load the models
        model_identifiers = []
        for model_dict in model_list_rest["models"]:
            model_identifiers.append(
                ModelIdentifier(
                    model_storage_id=ID(model_dict["model_group_id"]),
                    model_id=ID(model_dict["model_id"]),
                )
            )

        # create code deployment entity and trigger export async function
        project = ProjectManager.get_project_by_id(project_id)
        code_deployment_repo = CodeDeploymentRepo(project_identifier=project_identifier)
        code_deployment = CodeDeployment(
            creator_id=user_id,
            id_=code_deployment_repo.generate_id(),
            model_identifiers=model_identifiers,
        )
        # TODO: this is workaround, clean up how we generate the project JSON representation. CVS-89317
        label_schema_per_task = CodeDeploymentRESTController._get_label_schema_per_task(project)
        project_rest_view = ProjectRESTViews.project_to_rest(
            organization_id=organization_id,
            project=project,
            label_schema_per_task=label_schema_per_task,
            storage_info={},
        )

        code_deployment_repo.save(code_deployment)
        logger.info("Starting zip file preparation in a separate thread.")
        current_context = contextvars.copy_context()
        export_executor.submit(
            current_context.run,  # type: ignore[arg-type]
            CodeDeploymentManager.prepare_zip_file,
            project=project,
            project_rest_view=project_rest_view,
            code_deployment=code_deployment,
        )

        # return code deployment rest view
        return CodeDeploymentRestViews.to_rest(code_deployment)

    @staticmethod
    def get_code_deployment_detail(project_identifier: ProjectIdentifier, code_deployment_id: ID) -> dict:
        """
        Returns the REST representation of a code deployment object.

        :param project_identifier: the identifier of the project relative to the code deployment
        :param code_deployment_id: the ID of the code deployment to be retrieved
        :return: REST View of code deployment entity or error responses
        """
        code_deployment = CodeDeploymentManager.get_deployment_by_id(
            project_identifier=project_identifier, code_deployment_id=code_deployment_id
        )
        return CodeDeploymentRestViews.to_rest(code_deployment)

    @staticmethod
    def delete_code_deployment(project_identifier: ProjectIdentifier, code_deployment_id: ID) -> None:
        """
        Deletes the code deployment (Mongo doc and zip file).

        :param project_identifier: Identifier of the project relative to the code deployment
        :param code_deployment_id: the ID of the code deployment to be deleted
        """
        CodeDeploymentManager.delete_deployment_by_id(
            project_identifier=project_identifier,
            code_deployment_id=code_deployment_id,
        )

    @staticmethod
    def get_filepath_by_deployment_id(
        project_identifier: ProjectIdentifier,
        code_deployment_id: ID,
        check_ready: bool = True,
    ) -> tuple[Path | str, str]:
        """
        Returns the filepath or presigned URL for the code deployment and the desired filename for the downloaded file.

        :param project_identifier: Identifier of the project relative to the code deployment
        :param code_deployment_id: the ID of the code deployment to be returned
        :param check_ready: set to True to check the readiness of CodeDeployment.
            If this is set to True and code deployment is not ready, CodeDeploymentFileIsNotReadyException is raised.
        :return Tuple: file path or presigned URL and file name
        """
        project = ProjectManager.get_project_by_id(project_id=project_identifier.project_id)
        filename = f"{DEPLOYMENT_FILENAME_TEMPLATE % slugify(project.name)}.zip"
        return (
            CodeDeploymentManager.get_code_deployment_path_or_presigned_url(
                project_identifier=project_identifier,
                code_deployment_id=code_deployment_id,
                check_ready=check_ready,
                filename=filename,
            ),
            filename,
        )

    @staticmethod
    def _get_label_schema_per_task(
        project: Project,
    ) -> dict[ID, LabelSchemaView]:
        # TODO: this is a workaround. This is a duplicate of a project controller function. CVS-89317
        # TODO: The Project REST view is rather difficult to use at the moment outside the project controller.
        label_schema_per_task: dict[ID, LabelSchemaView] = {
            task_node.id_: LabelSchemaService.get_latest_label_schema_for_task(
                project_identifier=project.identifier,
                task_node_id=task_node.id_,
            )
            for task_node in project.task_graph.tasks
            if task_node.task_properties.is_trainable
        }
        return label_schema_per_task

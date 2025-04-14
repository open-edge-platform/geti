# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import io
import json
import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy

from communication.exceptions import (
    CodeDeploymentCorruptException,
    CodeDeploymentFileIsNotReadyException,
    CodeDeploymentNotFoundException,
    ExportableCodeNotInitializedException,
    IncompatibleModelFormatException,
    NoMediaInProjectException,
    TaskNotFoundException,
)
from communication.rest_views.model_rest_views import ModelRESTViews
from communication.rest_views.pipeline import PipelineRESTViews
from entities.deployment import CodeDeployment, DeploymentState, NullCodeDeployment
from repos.code_deployment_repo import CodeDeploymentRepo
from resource_management.media_manager import MediaManager
from usecases.statistics import StatisticsUseCase

from geti_fastapi_tools.exceptions import GetiBaseException, ModelNotFoundException
from geti_telemetry_tools import unified_tracing
from geti_types import ID, ProjectIdentifier
from media_utils import get_media_numpy
from sc_sdk.entities.model import ModelFormat, NullModel
from sc_sdk.entities.model_storage import ModelStorageIdentifier
from sc_sdk.entities.project import Project
from sc_sdk.entities.video import Video, VideoFrame
from sc_sdk.repos import ModelRepo
from sc_sdk.repos.storage.binary_repos import CodeDeploymentBinaryRepo

if TYPE_CHECKING:
    from sc_sdk.entities.image import Image

logger = logging.getLogger(__name__)

DEPLOYMENT_FILENAME_TEMPLATE = "Deployment-%s"
PATH_TO_DEPLOYMENT_COLLATERALS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "code_deployment")


class CodeDeploymentManager:
    @staticmethod
    @unified_tracing
    def prepare_zip_file(  # noqa: PLR0915, PLR0912, C901
        project: Project,
        project_rest_view: dict,
        code_deployment: CodeDeployment,
    ) -> None:
        """
        Prepare the code deployment zip file for a code_deployment.
        The resulting zip file will be committed to the binary repo and the code_deployment object will be updated.

        :param project: the project of the requested code deployment
        :param project_rest_view: the rest view of the project
        :param code_deployment: the code deployment object which contains the info of the models to be deployed.
        """
        project_identifier = ProjectIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
        )
        code_deployment_repo = CodeDeploymentRepo(project_identifier=project_identifier)
        cd_binary_repo = CodeDeploymentBinaryRepo(project_identifier)
        try:
            # setup progress step, reserve last 10% for book keeping
            model_identifiers = code_deployment.model_identifiers
            progress_step = (100 - 10) / len(model_identifiers)

            with tempfile.TemporaryDirectory() as tmp_dir:
                # setup tmp folder
                deployment_name = DEPLOYMENT_FILENAME_TEMPLATE % project.name
                unzip_target_dir = os.path.join(tmp_dir, deployment_name)
                deployment_target_dir = os.path.join(unzip_target_dir, "deployment")
                os.makedirs(deployment_target_dir, exist_ok=True)

                # extract all models
                for model_identifier in model_identifiers:
                    model_storage_identifier = ModelStorageIdentifier(
                        workspace_id=project.workspace_id,
                        project_id=project.id_,
                        model_storage_id=model_identifier.model_storage_id,
                    )
                    model = ModelRepo(model_storage_identifier).get_by_id(model_identifier.model_id)
                    if isinstance(model, NullModel):
                        raise ModelNotFoundException(model_id=model_identifier.model_id)
                    task_node = next(
                        (
                            task
                            for task in project.get_trainable_task_nodes()
                            if task.id_ == model.model_storage.task_node_id
                        ),
                        None,
                    )
                    if not task_node:
                        raise TaskNotFoundException(task_id=model.model_storage.task_node_id)
                    task_node_rest = PipelineRESTViews.task_node_to_rest(task_node)
                    per_model_path = os.path.join(deployment_target_dir, task_node_rest["title"])
                    os.makedirs(per_model_path, exist_ok=True)

                    if model.model_format != ModelFormat.OPENVINO:
                        raise IncompatibleModelFormatException(model_identifier.model_id)

                    exportable_code = model.exportable_code
                    if exportable_code is None:
                        raise ExportableCodeNotInitializedException(model.id_)
                    exp_code = zipfile.ZipFile(io.BytesIO(exportable_code))
                    exp_code.extractall(path=per_model_path)

                    # put model REST representation to the model directory
                    model_performance = StatisticsUseCase.get_model_performance(
                        model=model,
                        project_identifier=project.identifier,
                    )
                    model_rest_view = ModelRESTViews.optimized_model_to_rest(
                        optimized_model=model,
                        performance=model_performance,
                    )
                    with open(os.path.join(per_model_path, "model.json"), "w") as model_json_file:
                        json.dump(model_rest_view, model_json_file, indent=3)

                    code_deployment.progress += progress_step
                    code_deployment_repo.save(code_deployment)

                # put additional file (project.json) to the deployment dir
                with open(os.path.join(deployment_target_dir, "project.json"), "w") as project_json_file:
                    json.dump(project_rest_view, project_json_file, indent=3)

                # put additional deployment files to the target dir
                for filename in os.listdir(PATH_TO_DEPLOYMENT_COLLATERALS):
                    source_path = os.path.join(PATH_TO_DEPLOYMENT_COLLATERALS, filename)
                    dest_path = os.path.join(unzip_target_dir, filename)
                    if os.path.isdir(source_path):
                        shutil.copytree(src=source_path, dst=dest_path)
                    else:
                        shutil.copyfile(src=source_path, dst=dest_path)

                # pick a random sample image or video frame from the project
                media_numpy = CodeDeploymentManager._get_random_2d_numpy_from_project(project=project)
                cv2.imwrite(
                    filename=os.path.join(unzip_target_dir, "sample_image.jpg"),
                    img=cv2.cvtColor(media_numpy, cv2.COLOR_RGB2BGR),
                )

                # zip the target dir and load it as bytes
                tmp_zip_file_path = os.path.join(tmp_dir, deployment_name + ".zip")
                with zipfile.ZipFile(tmp_zip_file_path, "w", zipfile.ZIP_DEFLATED) as output_zip_file:
                    target_dir_as_path = Path(unzip_target_dir)
                    for entry in target_dir_as_path.rglob("*"):
                        output_zip_file.write(entry, entry.relative_to(target_dir_as_path))
                logger.info("Created temporary zip file for code deployment.")
                # put it to our binary repo
                code_deployment.binary_filename = cd_binary_repo.save(data_source=tmp_zip_file_path, make_unique=True)
                logger.info("Saved code deployment zip file to storage system.")

            code_deployment.progress = 100
            code_deployment.state = DeploymentState.DONE
            code_deployment.message = "Code deployment preparation successful."
            logger.info(
                f"Code deployment succeeded and committed in the binary repo with filename: "
                f"{code_deployment.binary_filename}"
            )
        except Exception as ex:
            if isinstance(ex, GetiBaseException):
                message = f"Code deployment failed. Reason: {ex.message}"
            else:
                message = f"Code deployment failed due to unknown reason. {ex}"
            logger.exception(message)
            code_deployment.message = message
            code_deployment.state = DeploymentState.FAILED
        finally:
            code_deployment_repo.save(code_deployment)

    @staticmethod
    @unified_tracing
    def get_deployment_by_id(
        project_identifier: ProjectIdentifier,
        code_deployment_id: ID,
        check_binary_when_done: bool = False,
    ) -> CodeDeployment:
        """
        Retrieves the code deployment from the repo by code_deployment_id

        :param project_identifier: identifier of the project relative to the code deployment
        :param code_deployment_id: the ID of the code deployment to be returned
        :param check_binary_when_done: set to True to check whether the binary_name is set properly
            when the code_deployment state is DONE
        :return CodeDeployment: requested code deployment entity
        :raises CodeDeploymentNotFoundError: if code deployment is not found.
        :raises CodeDeploymentCorruptException: if check_binary_when_done is True, the code deployment state is done,
            but the binary_name is not set properly
        """
        code_deployment_repo = CodeDeploymentRepo(project_identifier=project_identifier)
        code_deployment = code_deployment_repo.get_by_id(id_=code_deployment_id)
        if isinstance(code_deployment, NullCodeDeployment):
            raise CodeDeploymentNotFoundException(code_deployment_id)
        if (
            check_binary_when_done
            and code_deployment.state is DeploymentState.DONE
            and code_deployment.binary_filename is None
        ):
            raise CodeDeploymentCorruptException(code_deployment_id, code_deployment.state.name)
        return code_deployment

    @staticmethod
    @unified_tracing
    def delete_deployment_by_id(
        project_identifier: ProjectIdentifier,
        code_deployment_id: ID,
    ) -> None:
        """
        TODO CVS-90187 Design and implement when to delete the code deployment entity.

        Deletes the code deployment (Mongo doc and zip file).

        :param project_identifier: Identifier of the project relative to the code deployment
        :param code_deployment_id: the ID of the code deployment to be deleted
        """
        code_deployment_repo = CodeDeploymentRepo(project_identifier=project_identifier)
        code_deployment = CodeDeploymentManager.get_deployment_by_id(
            project_identifier=project_identifier,
            code_deployment_id=code_deployment_id,
            check_binary_when_done=True,
        )
        if code_deployment.binary_filename is not None:
            CodeDeploymentBinaryRepo(project_identifier).delete_by_filename(filename=code_deployment.binary_filename)
        code_deployment_repo.delete_by_id(code_deployment_id)

    @staticmethod
    @unified_tracing
    def get_code_deployment_path_or_presigned_url(
        project_identifier: ProjectIdentifier,
        code_deployment_id: ID,
        filename: str,
        check_ready: bool = True,
    ) -> Path | str:
        """
        Returns the filepath of the code deployment.

        :param project_identifier: Identifier of the project relative to the code deployment
        :param code_deployment_id: the ID of the code deployment to be returned
        :param filename: Preset filename for the file that will be downloaded. In case of a presigned URL download,
         the header for the download that specifies the filename is set here.
        :param check_ready: set to True to check the readiness of CodeDeployment.
        :return: Path or presigned URL pointing to the binary file
        :raises: CodeDeploymentFileIsNotReadyException if 'check_ready' is set to True
                    and code deployment is not ready.
        """
        code_deployment = CodeDeploymentManager.get_deployment_by_id(
            project_identifier=project_identifier,
            code_deployment_id=code_deployment_id,
            check_binary_when_done=check_ready,
        )
        if check_ready and code_deployment.state is not DeploymentState.DONE:
            raise CodeDeploymentFileIsNotReadyException(code_deployment_id, code_deployment.state.name)
        if code_deployment.binary_filename is None:
            raise CodeDeploymentCorruptException(code_deployment_id, code_deployment.state.name)
        binary_repo = CodeDeploymentBinaryRepo(project_identifier)
        return binary_repo.get_path_or_presigned_url(
            filename=code_deployment.binary_filename,
            preset_headers={"response-content-disposition": f'attachment; filename="{filename}"'},
        )

    @staticmethod
    @unified_tracing
    def _get_random_2d_numpy_from_project(project: Project) -> numpy.ndarray:
        """
        Returns a random 2D numpy from the project.

        :param project: Project to return a media numpy for
        :return: 2d numpy
        """
        dataset_storage = project.get_training_dataset_storage()
        media_item = MediaManager.get_first_media(dataset_storage.identifier)
        if media_item is None:
            raise NoMediaInProjectException(
                f"No media exists in project. Project ID: {project.id_}, DatasetStorage ID: {dataset_storage.id_}."
            )

        media: Image | VideoFrame = (
            VideoFrame(video=media_item, frame_index=int(media_item.total_frames / 2))
            if isinstance(media_item, Video)
            else media_item
        )
        return get_media_numpy(dataset_storage_identifier=dataset_storage.identifier, media=media)

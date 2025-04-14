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
    ExportableCodeNotInitializedException,
    IncompatibleModelFormatException,
    NoMediaInProjectException,
)
from communication.rest_views.model_rest_views import ModelRESTViews
from entities.deployment import ModelIdentifier
from resource_management.media_manager import MediaManager
from usecases.statistics import StatisticsUseCase

from geti_fastapi_tools.exceptions import BadRequestException, ModelNotFoundException
from geti_telemetry_tools import unified_tracing
from media_utils import get_media_numpy
from sc_sdk.entities.model import ModelFormat, NullModel
from sc_sdk.entities.model_storage import ModelStorageIdentifier
from sc_sdk.entities.project import Project
from sc_sdk.entities.video import Video, VideoFrame
from sc_sdk.repos import ModelRepo

if TYPE_CHECKING:
    from sc_sdk.entities.image import Image

logger = logging.getLogger(__name__)

DEPLOYMENT_FILENAME_TEMPLATE = "Deployment-%s"
PATH_TO_DEPLOYMENT_COLLATERALS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "code_deployment")


class DeploymentPackageManager:
    @staticmethod
    @unified_tracing
    def prepare_geti_sdk_package(
        project: Project, project_rest_view: dict, model_identifiers: list[ModelIdentifier]
    ) -> Path:
        """
        Prepare the code deployment zip file including models and code_deployment.

        :param project: the project of the models
        :param project_rest_view: the REST view of the project
        :param model_identifiers: the list of model identifiers

        :return: the path to the zip file
        """

        tmp_dir = tempfile.mkdtemp()

        deployment_name = DEPLOYMENT_FILENAME_TEMPLATE % f"{project.name}"
        unzip_target_dir = os.path.join(tmp_dir, deployment_name)
        deployment_target_dir = os.path.join(unzip_target_dir, "deployment")
        os.makedirs(deployment_target_dir, exist_ok=True)

        # extract models
        for model_identifier in model_identifiers:
            model_storage_identifier = ModelStorageIdentifier(
                workspace_id=project.workspace_id,
                project_id=project.id_,
                model_storage_id=model_identifier.model_storage_id,
            )
            model = ModelRepo(model_storage_identifier).get_by_id(model_identifier.model_id)
            if isinstance(model, NullModel):
                raise ModelNotFoundException(model_id=model_identifier.model_id)
            task_node = project.get_trainable_task_node_by_id(model.model_storage.task_node_id)
            if task_node is None:
                raise BadRequestException(
                    f"Model storage `{model.model_storage.name}` is not "
                    f"connected to any task in project `{project.name}`."
                    f"Model Storage ID: `{model.model_storage.id_}`, Project ID `{project.id_}`."
                )
            per_model_path = os.path.join(deployment_target_dir, task_node.title)
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
        cv2.imwrite(
            filename=os.path.join(unzip_target_dir, "sample_image.jpg"),
            img=DeploymentPackageManager._get_random_image_from_project(project=project),
        )

        # zip the target dir and load it as bytes
        tmp_zip_file_path = os.path.join(tmp_dir, deployment_name + ".zip")
        with zipfile.ZipFile(tmp_zip_file_path, "w", zipfile.ZIP_DEFLATED) as output_zip_file:
            target_dir_as_path = Path(unzip_target_dir)
            for entry in target_dir_as_path.rglob("*"):
                output_zip_file.write(entry, entry.relative_to(target_dir_as_path))
        logger.info(
            "Created temporary zip file for code deployment for project %s and models %s",
            project.id_,
            model_identifiers,
        )

        return Path(tmp_zip_file_path)

    @staticmethod
    @unified_tracing
    def _get_random_image_from_project(project: Project) -> numpy.ndarray:
        """
        Returns a random image from the project.

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
        raw_image = get_media_numpy(dataset_storage_identifier=dataset_storage.identifier, media=media)
        return cv2.cvtColor(raw_image, cv2.COLOR_RGB2BGR)

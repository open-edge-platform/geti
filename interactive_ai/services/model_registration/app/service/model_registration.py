# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import asyncio
import logging
import os
import pathlib
import shutil
import sys
from collections.abc import AsyncGenerator
from zipfile import BadZipFile

import aiofiles
import grpc
from botocore.exceptions import ClientError
from grpc_interfaces.model_registration.pb.service_pb2 import (
    ActiveRequest,
    Chunk,
    DeregisterRequest,
    DownloadGraphRequest,
    Error,
    ErrorCode,
    ListRequest,
    ListResponse,
    PurgeProjectRequest,
    PurgeProjectResponse,
    RecoverRequest,
    RecoverResponse,
    RegisterRequest,
    StatusResponse,
)
from grpc_interfaces.model_registration.pb.service_pb2_grpc import ModelRegistrationServicer
from kubernetes_asyncio.client.rest import ApiException

from service.config import MODELMESH_NAMESPACE, S3_BUCKETNAME, S3_STORAGE
from service.inference_manager import InferenceManager
from service.model_converter import GraphVariant, ModelConverter, UnsupportedModelType
from service.responses import Responses
from service.s3client import S3Client

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelRegistration(ModelRegistrationServicer):
    """
    This class is the main handler for ModelRegistration API calss
    """

    def __init__(self) -> None:
        self.s3 = S3Client()
        self.converter = ModelConverter(self.s3)
        super().__init__()

    def make_error(self, code: ErrorCode.ValueType) -> Error:
        messages = {
            ErrorCode.MODEL_ALREADY_REGISTERED: "Model is already registered.",
            ErrorCode.UNSUPPORTED_MODEL_TYPE: "Unsupported model type.",
            ErrorCode.INVALID_MODEL_ZIP_PACKAGE: "Invalid model zip package.",
            ErrorCode.INTERNAL_ERROR: "Internal error.",
            ErrorCode.NOT_IMPLEMENTED: "Not implemented.",
        }
        message = messages.get(code, "Unknown error.")
        return Error(code=code, message=message)

    def handle_exception(self, error_code: ErrorCode.ValueType, message: str) -> StatusResponse:
        logger.exception(message)
        return StatusResponse(status=Responses.Failed, error=self.make_error(code=error_code))

    async def register_new_pipelines(
        self,
        req: RegisterRequest,
        context: grpc.aio.ServicerContext,  # noqa: ARG002
    ) -> StatusResponse:
        """
        Registers new pipeline
        """
        try:
            inference = InferenceManager()
            pipeline_name = (
                req.name
                if len(req.name) > 0
                else "{}_{}".format(req.project.id, "active" if len(req.model) > 1 else req.model[0].model_id)
            )
            pipeline = await inference.get_inference(name=pipeline_name, namespace=MODELMESH_NAMESPACE)
            if pipeline:
                if req.override:
                    logger.info(f"Override requested. Deregistering pipeline {pipeline_name}")
                    await asyncio.gather(
                        inference.remove_inference(name=pipeline_name, namespace=MODELMESH_NAMESPACE),
                        asyncio.get_event_loop().run_in_executor(
                            None, self.s3.delete_folder, S3_BUCKETNAME, pipeline_name
                        ),
                    )
                else:
                    logger.info(f"Model {pipeline_name} already registered")
                    return StatusResponse(
                        status=Responses.AlreadyRegistered,
                        error=self.make_error(code=ErrorCode.MODEL_ALREADY_REGISTERED),
                    )

            self.converter.process_model(name=pipeline_name, models=req.model, project=req.project)
            await inference.create_inference(
                name=pipeline_name,
                namespace=MODELMESH_NAMESPACE,
                storage_name=S3_STORAGE,
                path=pipeline_name,
            )
            response = StatusResponse(status=Responses.Created)
        except ApiException as api_err:
            if api_err.reason == "Conflict":
                logger.info(f"Model {pipeline_name} already registered")
                response = StatusResponse(
                    status=Responses.AlreadyRegistered, error=self.make_error(code=ErrorCode.MODEL_ALREADY_REGISTERED)
                )
            else:
                response = self.handle_exception(
                    ErrorCode.INTERNAL_ERROR,
                    f"The error {api_err.status} has been returned while creating pipeline {pipeline_name}",
                )
        except ClientError as s3_err:
            response = self.handle_exception(
                ErrorCode.INTERNAL_ERROR, f"Failed to create inference {pipeline_name}. S3 error: {s3_err}"
            )
        except BadZipFile as zip_err:
            response = self.handle_exception(
                ErrorCode.INVALID_MODEL_ZIP_PACKAGE,
                f"Failed to create inference {pipeline_name}. Invalid model zip package: {zip_err}",
            )
        except UnsupportedModelType as model_err:
            response = self.handle_exception(
                ErrorCode.UNSUPORTED_MODEL_TYPE,
                f"Failed to create inference {pipeline_name}. Unsupported model type: {model_err}",
            )
        except OSError as os_err:
            response = self.handle_exception(
                ErrorCode.INTERNAL_ERROR, f"Failed to create inference {pipeline_name}. Encountered OS error: {os_err}"
            )
        except RuntimeError as err:
            response = self.handle_exception(
                ErrorCode.INTERNAL_ERROR,
                f"Failed to create inference {pipeline_name}. Encountered runtime error: {err}",
            )

        return response

    async def download_graph(
        self,
        req: DownloadGraphRequest,
        context: grpc.aio.ServicerContext,
    ) -> AsyncGenerator[Chunk, None]:  # type: ignore
        """
        Download a graph for given models
        """
        graph_directory = None
        graph_archive_path = None
        try:
            graph_directory = pathlib.Path(
                self.converter.prepare_graph(
                    models=req.models, project=req.project, graph_variant=GraphVariant.OVMS_DEPLOYMENT
                )
            )
            graph_archive_path = graph_directory.parent.joinpath(f"{req.project.id}.zip")

            # Create archive with prepared graph
            # Due to shutil.make_archive intricacies, we have to change working dir manually
            # and create zip file in another directory
            cwd = os.getcwd()
            try:
                os.chdir(graph_directory)
                shutil.make_archive(
                    base_name=f"../{str(req.project.id)}",
                    root_dir=None,
                    base_dir=None,
                    format="zip",
                )
            finally:
                os.chdir(cwd)

            # Stream archived graph as a response
            async with aiofiles.open(graph_archive_path, "rb") as archive:
                while archive_chunk := await archive.read(1024 * 1024):
                    yield Chunk(buffer=archive_chunk)

        except (RuntimeError, ClientError) as err:
            error_message = f"Failed to create graph, {req.project=} {req.models=}. Encountered error: {err}"
            logger.exception(error_message)
            await context.abort(grpc.StatusCode.INTERNAL, details=error_message)
        finally:
            if graph_directory:
                self.converter._delete_dir(dir_path=str(graph_directory))
            if graph_archive_path:
                graph_archive_path.unlink(missing_ok=True)

    async def deregister_pipeline(
        self,
        request: DeregisterRequest,
        context: grpc.aio.ServicerContext,  # noqa: ARG002
    ) -> StatusResponse:
        """
        Deregisters existing pipeline
        """
        try:
            inference = InferenceManager()
            await inference.remove_inference(name=request.name, namespace=MODELMESH_NAMESPACE)
            self.s3.delete_folder(bucket_name=S3_BUCKETNAME, object_key=request.name)
            return StatusResponse(status=Responses.Removed)
        except ApiException as api_err:
            response = self.handle_exception(
                ErrorCode.INTERNAL_ERROR,
                f"Failed to remove inference {request.name}. Encountered API error: {api_err}",
            )
        except ClientError as s3_err:
            response = self.handle_exception(
                ErrorCode.INTERNAL_ERROR,
                f"Failed to remove inference {request.name}. Encountered S3 client error: {s3_err}",
            )
        except OSError as os_err:
            response = self.handle_exception(
                ErrorCode.INTERNAL_ERROR,
                f"Failed to remove inference {request.name}. Encountered OS error: {os_err}",
            )
        except RuntimeError as err:
            response = self.handle_exception(
                ErrorCode.INTERNAL_ERROR, f"Failed to remove inference {request.name}. Encountered runtime error: {err}"
            )
        return response

    async def register_active_pipeline(
        self,
        request: ActiveRequest,  # noqa: ARG002
        context: grpc.aio.ServicerContext,  # noqa: ARG002
    ) -> StatusResponse:
        return StatusResponse(status=Responses.NotImplemented, error=self.make_error(code=ErrorCode.NOT_IMPLEMENTED))

    async def list_pipelines(
        self,
        request: ListRequest,  # noqa: ARG002
        context: grpc.aio.ServicerContext,  # noqa: ARG002
    ) -> ListResponse:
        """
        List existing pipelines
        """
        try:
            inference = InferenceManager()
            pipelines = await inference.list_inference(namespace=MODELMESH_NAMESPACE)
            lines = [p.name for p in pipelines]
            return ListResponse(pipelines=lines)
        except ApiException as api_err:
            logger.error(f"The error {api_err.status} has been returned while listing pipelines")
            return ListResponse()

    async def recover_pipeline(
        self,
        request: RecoverRequest,
        context: grpc.aio.ServicerContext,  # noqa: ARG002
    ) -> RecoverResponse:
        """
        Re-register a pipeline from S3, if possible

        Checks if the folder with model artifacts exists on S3. If so, the model will
        be registered with ModelMesh and a success response is returned
        """
        inference = InferenceManager()
        pipelines = await inference.list_inference(namespace=MODELMESH_NAMESPACE)
        pipeline_name = request.name
        if pipeline_name in [p.name for p in pipelines]:
            logger.info(f"Model `{pipeline_name}` is already registered")
            return RecoverResponse(success=True)

        if self.s3.check_folder_exists(bucket_name=S3_BUCKETNAME, object_key=pipeline_name):
            await inference.create_inference(
                name=pipeline_name,
                namespace=MODELMESH_NAMESPACE,
                storage_name=S3_STORAGE,
                path=pipeline_name,
            )
            logger.info(f"Model `{pipeline_name}` recovered successfully")
            return RecoverResponse(success=True)
        logger.info(f"Unable to recover model `{pipeline_name}`")
        return RecoverResponse(success=False)

    async def delete_project_pipelines(
        self,
        request: PurgeProjectRequest,
        context: grpc.aio.ServicerContext,  # noqa: ARG002
    ) -> PurgeProjectResponse:
        """
        Remove all project inference pipelines and inference services.

        This endpoint does the following:
        - Delete all existing inference services for a project from the cluster
        - Remove all inference model artifacts for the project from S3

        If all pipelines and artifacts are deleted without errors, the endpoint
        returns a success response
        """
        project_prefix = request.project_id + "-"
        success = True

        # First, remove inference services for the project and delete the
        # corresponding folders on S3
        inference = InferenceManager()
        pipelines = await inference.list_inference(namespace=MODELMESH_NAMESPACE)
        project_pipelines = [p for p in pipelines if p.name.startswith(project_prefix)]
        logger.info(
            f"Deleting {len(project_pipelines)} registered inference pipelines related "
            f"to project with id: {request.project_id}"
        )
        for pipeline in project_pipelines:
            try:
                await inference.remove_inference(name=pipeline.name, namespace=MODELMESH_NAMESPACE)
                self.s3.delete_folder(bucket_name=S3_BUCKETNAME, object_key=pipeline.name)
                logger.info(
                    f"InferenceService {pipeline.name} removed. Inference model artifacts deleted from object storage."
                )
            except (RuntimeError, ClientError) as err:
                logger.error(f"Failed to remove inference pipeline {pipeline.name}. Encountered error: {err}")
                success = False

        # Then, find and delete any leftover inference model folders on S3 that are
        # owned by the project
        folder_names = self.s3.list_folders(bucket_name=S3_BUCKETNAME)
        project_folder_names = [n for n in folder_names if n.startswith(project_prefix)]
        logger.info(
            f"Deleting {len(project_folder_names)} inference model artifact folders "
            f"for project with id {request.project_id} from object storage. Folder "
            f"names: {project_folder_names}"
        )
        for folder_name in project_folder_names:
            try:
                self.s3.delete_folder(bucket_name=S3_BUCKETNAME, object_key=folder_name)
                logger.info(f"Inference model artifacts for pipeline {folder_name} deleted from object storage.")
            except ClientError as err:
                logger.error(
                    f"Failed to remove inference model artifact folder {folder_name}. S3 client returned error: {err}"
                )
                success = False
        return PurgeProjectResponse(success=success)

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

# ruff: noqa: ARG002

import logging
import os
from collections.abc import Iterable
from pathlib import Path

from mlflow.entities.file_info import FileInfo
from mlflow.exceptions import ALREADY_EXISTS, BAD_REQUEST, INTERNAL_ERROR, MlflowException
from mlflow.store.artifact.artifact_repo import ArtifactRepository

from mlflow_geti_store.artifact_model import DispatchingError, dispatch_artifact
from mlflow_geti_store.s3_object_storage_client import S3ObjectStorageClientSingleton
from mlflow_geti_store.utils import ARTIFACT_ROOT_URI_PREFIX, PRESIGNED_URL_SUFFIX

logger = logging.getLogger(__name__)


class GetiArtifactRepository(ArtifactRepository):
    def __init__(self, artifact_uri: str):
        super().__init__(artifact_uri)

        self.client = S3ObjectStorageClientSingleton.instance()
        self.identifier = self.client.identifier
        self.object_storage_root_dir = self.identifier.to_path()

    def log_artifact(self, local_file: str, artifact_path: str | None = None) -> None:
        """
        :param local_file: Local disk file path where the HTTP API handler stored the file content from the client.
        :param artifact_path: Request artifact path for the artifact file to be saved such as
            "organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}/jobs/{job_id}/{arbitrary-path}"
            For example, this could be
            "organizations/00000/workspaces/00000/projects/00000/jobs/00000/outputs/models/model_fp16_xai.pth"
        """
        object_storage_path: str = ""
        try:
            dispatched = dispatch_artifact(filepath=local_file)
            object_storage_path = dispatched.to_object_storage_path()
            self.client.save_file_from_local_disk(
                relative_path=object_storage_path,
                local_file_path=local_file,
                overwrite=True,
            )
            logger.info(f"Logged artifact (local_path={local_file}, remote_path={object_storage_path})")
        except DispatchingError as err:
            logger.exception(f"Could not find proper model to dispatch artifact (local_path={local_file})")
            raise MlflowException(message=err.msg, error_code=BAD_REQUEST) from err
        except FileExistsError as err:
            logger.exception(f"Failed to log artifact because it already exists (remote_path={object_storage_path})")
            raise MlflowException(message=err.strerror, error_code=ALREADY_EXISTS) from err
        except RuntimeError as err:
            logger.exception(f"Failed to log artifact (local_path={local_file}, remote_path={object_storage_path})")
            raise MlflowException(message=str(err), error_code=INTERNAL_ERROR) from err

    def log_artifacts(self, local_dir: str, artifact_path: str | None = None) -> None:
        """
        :param local_dir: Local disk directory path
            where the HTTP API handler stored the files received from the client.
        :param artifact_path: Request artifact path for the artifact file to be saved such as
            "organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}/jobs/{job_id}/{arbitrary-path}"
            For example, this could be
            "organizations/00000/workspaces/00000/projects/00000/jobs/00000/outputs/models/"
        """
        error_stack = []

        for root, dirs, files in os.walk(local_dir):
            for fname in files:
                local_file = os.path.join(root, fname)
                try:
                    self.log_artifact(local_file=local_file, artifact_path=artifact_path)
                except MlflowException as err:
                    logger.exception(f"Could not log artifact: local_file={local_file}, artifact_path={artifact_path}")
                    error_stack += [err]

        if error_stack:
            message = f"Some of artifacts cannot be logged. See {error_stack}."
            raise MlflowException(message=message, error_code=INTERNAL_ERROR)

    def list_artifacts(self, path: str) -> Iterable[FileInfo]:
        """
        :param path: Request artifact path such as
            "organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}/jobs/{job_id}"
        """
        relative_path = Path(path.removeprefix(ARTIFACT_ROOT_URI_PREFIX))
        relative_path = (
            relative_path.relative_to(self.object_storage_root_dir)
            if relative_path.is_relative_to(self.object_storage_root_dir)
            else relative_path
        )

        logger.info(f"Listing artifacts under relative path: {relative_path}")
        try:
            file_infos = []
            for obj_info in self.client.list_files(relative_path=relative_path):
                path = str(Path(obj_info.object_name).relative_to(self.object_storage_root_dir))
                file_info = FileInfo(path=path, is_dir=obj_info.is_dir, file_size=obj_info.size)
                file_infos += [file_info]
            return file_infos
        except RuntimeError as err:
            logger.exception(f"Failed to list artifacts under relative path: {relative_path}")
            raise MlflowException(message=str(err), error_code=INTERNAL_ERROR)

    def _download_file(self, remote_file_path: str, local_path: str):
        """
        :param remote_file_path: This is a relative path to the base artifact path.
            The base artifact path is
            "organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}/jobs/{job_id}".
            For example, if the query is
            "organizations/00000/workspaces/00000/projects/00000/jobs/00000/inputs/datum-0-of-10.arrow",
            `remote_file_path` will be "inputs/datum-0-of-10.arrow".
        :param local_path: Requested local disk path from the HTTP API handler to write the file content.
            We should modify it slightly to make it working. Please refer to the following NOTE comments for the reason.
        """
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        response = None
        logger.info(f"Downloading file from: {remote_file_path}")
        relative_path = Path(remote_file_path)
        if relative_path.is_relative_to(self.object_storage_root_dir):
            relative_path = relative_path.relative_to(self.object_storage_root_dir)

        if relative_path.suffix == PRESIGNED_URL_SUFFIX:
            relative_path = relative_path.with_suffix("")
            response = self.client.get_presigned_url(relative_path=relative_path)
            with open(local_path, "w") as fp:
                fp.write(response)
            logger.info(f"Wrote S3 presigned url for {relative_path} to local disk: {local_path} response: {response}")
            return

        try:
            response = self.client.get_by_filename(relative_path=relative_path)
            with open(local_path, "wb") as fp:
                for data in response.stream():
                    fp.write(data)
            logger.info(f"Wrote from S3 to local disk: {local_path}")
        finally:
            if response:
                response.close()
                response.release_conn()

    def delete_artifacts(self, artifact_path: str | None = None) -> None:
        if not artifact_path:
            return
        relative_path = Path(artifact_path.removeprefix(ARTIFACT_ROOT_URI_PREFIX)).relative_to(
            self.object_storage_root_dir
        )

        try:
            errors = self.client.delete_files(relative_path, recursive=True)
            if errors:
                messages = [f"Filename: {err.name}, Message: {err.message}" for err in errors]
                message = str(messages)
                raise MlflowException(message=f"Failed to delete: {message}")
        except RuntimeError as err:
            logger.exception("Failed to delete artifacts under relative path: %s", relative_path)
            raise MlflowException(message=str(err), error_code=INTERNAL_ERROR)

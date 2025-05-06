# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from behave import given, when
from behave.runner import Context
from file_management import download_file_from_remote_archive
from static_definitions import ProjectType, TrainerType

if TYPE_CHECKING:
    from geti_client import ProjectImportExportApi

TUS_UPLOAD_CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB

logger = logging.getLogger(__name__)


def _resolve_project_to_import(
    projects_dir: Path,
    project_type: ProjectType,
    trained: bool = False,
    trainer_type: TrainerType | None = None,
) -> Path:
    project_type_pattern = project_type.value.replace(" > ", "_").replace(" ", "_").lower()

    if trained:
        if trainer_type is None or trainer_type == TrainerType.OTX_2x:
            project_archive_name = f"{project_type_pattern}-trained.zip"
        else:
            trainer_type_pattern = trainer_type.value.replace(".", "").replace(" ", "_").lower()
            project_archive_name = f"{project_type_pattern}-trained-{trainer_type_pattern}.zip"
    else:
        project_archive_name = f"{project_type_pattern}-small.zip"

    logger.info(f"Resolved project archive name: {project_archive_name}")

    local_project_archive_path = projects_dir / project_archive_name
    if not local_project_archive_path.exists():
        remote_relative_path = Path(f"projects/{project_archive_name}")
        try:
            logger.info(f"Downloading project archive file from remote archive: {remote_relative_path}")
            download_file_from_remote_archive(
                remote_file_path=remote_relative_path,
                local_file_path=local_project_archive_path,
            )
        except Exception as exc:
            raise FileNotFoundError(
                f"Failed to download project archive file from remote archive: {remote_relative_path}"
            ) from exc
    return local_project_archive_path


@given("an exported project archive of type '{project_type}'")
def step_given_exported_project_archive(context: Context, project_type: str) -> None:
    context.project_to_import_path = _resolve_project_to_import(
        projects_dir=context.projects_dir, project_type=ProjectType(project_type)
    )


@given("an annotated project of type '{project_type}'")
def step_given_annotated_project(context: Context, project_type: str) -> None:
    context.execute_steps(f"""
        Given an exported project archive of type '{project_type}'
          When the user uploads the project archive to the platform to create a new project
          Then a job of type 'import_project' is scheduled
          And the job completes successfully within 3 minutes
          And a project of type '{project_type}' is created from 'import_project' job
    """)


@given("a trained exported project archive of type '{project_type}' trained with '{trainer}'")
def step_given_exported_project_archive_trainer(context: Context, project_type: str, trainer: str) -> None:
    context.project_to_import_path = _resolve_project_to_import(
        projects_dir=context.projects_dir,
        project_type=ProjectType(project_type),
        trained=True,
        trainer_type=TrainerType(trainer),
    )


@given("a trained project of type '{project_type}' trained with '{trainer}'")
def step_given_trained_project_with_trainer(context: Context, project_type: str, trainer: str) -> None:
    context.execute_steps(f"""
        Given a trained exported project archive of type '{project_type}' trained with '{trainer}'
          When the user uploads the project archive to the platform to create a new project
          Then a job of type 'import_project' is scheduled
          And the job completes successfully within 3 minutes
          And a project of type '{project_type}' is created from 'import_project' job
    """)


@given("a trained project of type '{project_type}'")
def step_given_trained_project(context: Context, project_type: str) -> None:
    step_given_trained_project_with_trainer(context, project_type=project_type, trainer=TrainerType.OTX_2x.value)


@when("the user uploads the project archive to the platform to create a new project")
def step_when_user_uploads_project_to_new_project(context: Context) -> None:
    project_ie_api: ProjectImportExportApi = context.project_import_export_api
    project_to_import_path = context.project_to_import_path

    # Create TUS upload
    create_tus_upload_response = project_ie_api.create_tus_project_upload_with_http_info(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        tus_resumable="1.0.0",
        upload_length=project_to_import_path.stat().st_size,
    )
    assert create_tus_upload_response.status_code == 201, (
        f"Failed to create TUS upload: {create_tus_upload_response.raw_data}"
    )
    response_headers = create_tus_upload_response.headers
    assert "location" in create_tus_upload_response.headers, (
        f"Missing 'location' header in TUS upload response; found headers: {response_headers}"
    )
    location_header = create_tus_upload_response.headers["location"]
    file_id = location_header.split("/")[-1]

    # Upload the file in chunks
    current_offset = 0
    with open(project_to_import_path, "rb") as file:
        while chunk := file.read(TUS_UPLOAD_CHUNK_SIZE):
            logger.debug(f"Uploading chunk of size {len(chunk)} bytes at offset {current_offset}")
            project_ie_api.tus_project_upload_patch(
                organization_id=context.organization_id,
                workspace_id=context.workspace_id,
                file_id=file_id,
                tus_resumable="1.0.0",
                upload_offset=current_offset,
                body=chunk,
            )
            current_offset += len(chunk)

    # Import to new project
    import_response = project_ie_api.import_project(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        import_project_request={"file_id": file_id},
    )
    context.job_id = import_response.job_id

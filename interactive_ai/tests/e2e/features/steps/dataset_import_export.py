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
import random
from pathlib import Path

from behave import given, then, when
from behave.runner import Context
from file_management import download_file_from_remote_archive
from geti_client import (
    DatasetImportExportApi,
    ImportProjectBody,
    ImportProjectBodyLabelsInner,
    MetadataOfPerformImportToNewProjectJob1,
    MetadataOfPrepareImportToNewProjectJobSupportedProjectTypesInnerPipeline,
)
from static_definitions import (
    PROJECT_TYPE_TO_DATASET_IE_PROJECT_TYPE_MAPPING,
    AnnotationType,
    DatasetIEProjectType,
    ExportedDatasetFormat,
    ProjectType,
)

TUS_UPLOAD_CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB

logger = logging.getLogger(__name__)


def _resolve_dataset_to_import(
    datasets_dir: Path,
    dataset_format: ExportedDatasetFormat,
    annotation_type: AnnotationType,
    dataset_size: str = "small",
) -> Path:
    dataset_name = (
        f"{annotation_type.value.lower().replace(' ', '_')}-{dataset_format.value.lower()}-{dataset_size}.zip"
    )
    local_dataset_path = datasets_dir / dataset_name
    if not local_dataset_path.exists():
        remote_relative_path = Path(f"datasets/{dataset_name}")
        try:
            logger.info(f"Downloading dataset file from remote archive: {remote_relative_path}")
            download_file_from_remote_archive(
                remote_file_path=remote_relative_path,
                local_file_path=local_dataset_path,
            )
        except Exception as exc:
            raise FileNotFoundError(
                f"Dataset file not available at '{local_dataset_path}', "
                f"could not download from remote at '{remote_relative_path}'"
            ) from exc
    return local_dataset_path


@given("a '{dataset_format}' dataset with '{annotation_type}'-like annotations")
def step_given_dataset_with_custom_format_and_annotations(
    context: Context, dataset_format: str, annotation_type: str
) -> None:
    context.dataset_format = ExportedDatasetFormat(dataset_format)
    context.annotation_type = AnnotationType(annotation_type)

    context.dataset_to_import_path = _resolve_dataset_to_import(
        datasets_dir=context.datasets_dir,
        dataset_format=context.dataset_format,
        annotation_type=context.annotation_type,
    )


@when("the user uploads the dataset to the platform to create a new project")
def step_when_user_uploads_dataset_to_new_project(context: Context) -> None:
    dataset_ie_api: DatasetImportExportApi = context.dataset_import_export_api

    # Create TUS upload
    create_tus_upload_response = dataset_ie_api.create_tus_dataset_upload_with_http_info(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        tus_resumable="1.0.0",
        upload_length=context.dataset_to_import_path.stat().st_size,
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
    with open(context.dataset_to_import_path, "rb") as file:
        while True:
            chunk = file.read(TUS_UPLOAD_CHUNK_SIZE)
            if not chunk:
                break
            logger.debug(f"Uploading chunk of size {len(chunk)} bytes at offset {current_offset}")
            dataset_ie_api.tus_dataset_upload_patch(
                organization_id=context.organization_id,
                workspace_id=context.workspace_id,
                file_id=file_id,
                tus_resumable="1.0.0",
                # content_type="application/offset+octet-stream",
                upload_offset=current_offset,
                body=chunk,
            )
            current_offset += len(chunk)

    # Prepare for import to new project
    prepare_for_import_response = dataset_ie_api.prepare_dataset_for_import(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        file_id=file_id,
    )
    context.job_id = prepare_for_import_response.job_id


@when("the user chooses '{project_type}' as the type of the new project to create via import")
def step_when_user_chooses_import_project_type(context: Context, project_type: str) -> None:
    dataset_ie_api: DatasetImportExportApi = context.dataset_import_export_api
    chosen_project_type = PROJECT_TYPE_TO_DATASET_IE_PROJECT_TYPE_MAPPING[ProjectType(project_type)]

    # Retrieve the labels from the response of the prepare-for-import job
    prepare_for_import_job_info: MetadataOfPerformImportToNewProjectJob1 = context.job_info.actual_instance
    pipeline_info: MetadataOfPrepareImportToNewProjectJobSupportedProjectTypesInnerPipeline = next(
        spt.pipeline
        for spt in prepare_for_import_job_info.metadata.supported_project_types
        if spt.project_type == chosen_project_type.value
    )
    labels_info = [label_info for task in pipeline_info.tasks if task.labels for label_info in task.labels]

    # Import to new project
    import_response = dataset_ie_api.import_project_from_dataset(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        import_project_body=ImportProjectBody(
            file_id=prepare_for_import_job_info.metadata.file_id,
            project_name=f"Project - {project_type} [imported from dataset]",
            task_type=chosen_project_type.value,
            labels=[
                ImportProjectBodyLabelsInner(
                    name=label_info.name,
                    color=f"#{random.randint(0, 0xFFFFFF):06x}",
                    group=label_info.group,
                )
                for label_info in labels_info
            ],
        ),
    )
    context.job_id = import_response.job_id


@then("'{project_type}' is recognized as one of the project types compatible with the dataset")
def step_then_import_type_recognized(context: Context, project_type: str) -> None:
    expected_supported_project_type = PROJECT_TYPE_TO_DATASET_IE_PROJECT_TYPE_MAPPING[ProjectType(project_type)]

    job_info: MetadataOfPerformImportToNewProjectJob1 = context.job_info.actual_instance
    supported_project_types = {
        DatasetIEProjectType(pt.project_type) for pt in job_info.metadata.supported_project_types
    }

    assert expected_supported_project_type in supported_project_types, (
        f"Expected project type {expected_supported_project_type} "
        f"not found in supported project types: {supported_project_types}"
    )

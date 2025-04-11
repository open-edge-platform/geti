# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

"""This module implements export workflow"""

from flytekit import workflow

from job.tasks.export_tasks.export_dataset_task import export_dataset_task


@workflow
def export_dataset_workflow(
    organization_id: str,
    project_id: str,
    dataset_storage_id: str,
    include_unannotated: bool,
    export_format: str,
    save_video_as_images: bool,
) -> None:
    """
    Export dataset storage from geti to zipped dataset workflow

    :param organization_id: ID of the organization
    :param project_id: ID of the project
    :param dataset_storage_id: ID of the dataset storage to export
    :param export_format: format to export dataset to
    :param include_unannotated: whether to include unannotated media in export
    :param save_video_as_images: Whether to export video as frame images or not.
        For formats that don't natively support videos (all except Datumaro),
        this parameter is implicitly overridden to true.
    """
    export_dataset_task(
        organization_id=organization_id,
        project_id=project_id,
        dataset_storage_id=dataset_storage_id,
        include_unannotated=include_unannotated,
        export_format=export_format,
        save_video_as_images=save_video_as_images,
    )

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements project export workflow"""

from flytekit import workflow

from job.tasks.export_project import export_project


@workflow
def export_project_workflow(
    project_id: str,
) -> None:
    """
    Flyte workflow for exporting geti projects to zip.

    :param project_id: ID of the project to export
    """
    export_project(
        project_id=project_id,
    )

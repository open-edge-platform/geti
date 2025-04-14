# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module tests import workflow"""

import pytest
from flytekit.core.testing import task_mock

from job.tasks.import_tasks.create_project_from_dataset import create_project_from_dataset
from job.tasks.import_tasks.import_dataset_to_project import import_dataset_to_project
from job.tasks.import_tasks.parse_dataset_existing_project import parse_dataset_for_import_to_existing_project
from job.tasks.import_tasks.parse_dataset_new_project import parse_dataset_for_import_to_new_project
from job.workflows.import_workflows import (
    create_project_from_dataset_workflow,
    import_dataset_to_project_workflow,
    prepare_import_existing_project_workflow,
    prepare_import_new_project_workflow,
)

WORKSPACE_ID = "workspace_id"
PROJECT_ID = "project_id"
DATASET_ID = "dataset_id"
DATASET_NAME = "dataset_name"
IMPORT_ID = "import_id"
PROJECT_NAME = "project_name"
PROJECT_TYPE = "project_type"
LABEL_NAMES = ["label1", "label2"]
COLOR_BY_LABEL = {"label1": "FFFFFF", "label2": "CCCCCC"}
LABELS_MAP = {"label1": "id_1", "label2": "id_2"}
KEYPOINT_STRUCTURE: dict = {"edges": [], "positions": []}
USER_ID = "user_id"


@pytest.mark.JobsComponent
class TestImportWorkflow:
    def test_prepare_import_new_project_workflow(self) -> None:
        with task_mock(parse_dataset_for_import_to_new_project) as mock_parse:
            prepare_import_new_project_workflow(import_id=IMPORT_ID)
        mock_parse.assert_called_once_with(import_id=IMPORT_ID)

    def test_prepare_import_existing_project_workflow(self) -> None:
        with task_mock(parse_dataset_for_import_to_existing_project) as mock_parse:
            prepare_import_existing_project_workflow(project_id=PROJECT_ID, import_id=IMPORT_ID)
        mock_parse.assert_called_once_with(project_id=PROJECT_ID, import_id=IMPORT_ID)

    def test_perform_import_new_project_workflow(self) -> None:
        with task_mock(create_project_from_dataset) as mock_create:
            create_project_from_dataset_workflow(
                import_id=IMPORT_ID,
                project_name=PROJECT_NAME,
                project_type=PROJECT_TYPE,
                label_names=LABEL_NAMES,
                color_by_label=COLOR_BY_LABEL,
                keypoint_structure=KEYPOINT_STRUCTURE,
                user_id=USER_ID,
            )
        assert mock_create.called_once_with(
            import_id=IMPORT_ID,
            name=PROJECT_NAME,
            project_type_str=PROJECT_TYPE,
            label_names=LABEL_NAMES,
            color_by_label=COLOR_BY_LABEL,
            keypoint_structure=KEYPOINT_STRUCTURE,
            user_id=USER_ID,
        )

    def test_perform_import_existing_project_workflow(self) -> None:
        with task_mock(import_dataset_to_project) as mock_import:
            import_dataset_to_project_workflow(
                import_id=IMPORT_ID,
                project_id=PROJECT_ID,
                dataset_storage_id=DATASET_ID,
                dataset_name=DATASET_NAME,
                labels_map=LABELS_MAP,
                user_id=USER_ID,
            )
        assert mock_import.called_once_with(
            import_id=IMPORT_ID,
            project_id=PROJECT_ID,
            dataset_storage_id=DATASET_ID,
            dataset_name=DATASET_NAME,
            label_ids_map=LABELS_MAP,
            user_id=USER_ID,
        )

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""Test export utils"""

from unittest.mock import MagicMock, patch

import pytest
from geti_types import ID
from iai_core.entities.color import Color
from iai_core.entities.label import Domain, Label
from iai_core.entities.label_schema import LabelSchemaView
from iai_core.entities.model_template import TaskType
from iai_core.entities.project import Project
from iai_core.entities.task_node import TaskNode, TaskProperties
from jobs_common_extras.datumaro_conversion.definitions import GetiProjectType

from job.utils.export_utils import ExportUtils


@pytest.mark.JobsComponent
class TestExportUtils:
    def test_create_voc_label_map_with_detection_labels(self):
        # Arrange
        label_schema = MagicMock()
        labels = [
            Label(name="label1", domain=Domain.DETECTION, color=Color(0, 0, 0), id_=ID()),
            Label(name="label2", domain=Domain.DETECTION, color=Color(0, 0, 0), id_=ID()),
            Label(
                name="label3",
                domain=Domain.CLASSIFICATION,
                color=Color(0, 0, 0),
                id_=ID(),
            ),
        ]
        label_schema.get_labels.return_value = labels

        # Act
        result = ExportUtils.create_voc_label_map(label_schema)

        # Assert
        expected_result = {
            "label1": [(0, 0, 0), [], ["label3"]],
            "label2": [(0, 0, 0), [], ["label3"]],
        }
        assert result == expected_result

    def test_create_voc_label_map_without_detection_labels(self):
        # Arrange
        label_schema = MagicMock()
        label1 = Label(name="label1", domain=Domain.CLASSIFICATION, color=Color(0, 0, 0), id_=ID())
        label2 = Label(
            name="label2",
            domain=Domain.CLASSIFICATION,
            color=Color(120, 120, 120),
            id_=ID(),
        )

        label_schema.get_labels.return_value = [label1, label2]

        # Act
        result = ExportUtils.create_voc_label_map(label_schema)

        # Assert
        expected_result = {
            "label1": [(0, 0, 0), [], []],
            "label2": [(120, 120, 120), [], []],
        }
        assert result == expected_result

    def test_determine_use_label_schema_with_supported_project_types(self):
        # Arrange
        supported_project_types = [
            GetiProjectType.CLASSIFICATION,
            GetiProjectType.ROTATED_DETECTION,
            GetiProjectType.ANOMALY_CLASSIFICATION,
            GetiProjectType.ANOMALY_DETECTION,
            GetiProjectType.ANOMALY_SEGMENTATION,
        ]

        # Act and Assert
        for project_type in supported_project_types:
            assert ExportUtils.determine_use_label_schema(project_type)

    def test_determine_use_label_schema_with_unsupported_project_type(self):
        # Arrange
        unsupported_project_type = GetiProjectType.UNKNOWN

        # Act and Assert
        assert not ExportUtils.determine_use_label_schema(unsupported_project_type)

    def test_get_task_type_with_labels(self):
        # Arrange
        label1 = MagicMock(spec=Label)
        label1.name = "Label1"
        label2 = MagicMock(spec=Label)
        label2.name = "Label2"

        label_schema_view = MagicMock(spec=LabelSchemaView)
        label_schema_view.get_labels.return_value = [label1, label2]

        task_node = MagicMock(spec=TaskNode)
        task_node.task_properties = MagicMock(spec=TaskProperties)
        task_node.task_properties.is_trainable = True
        task_node.task_properties.task_type = MagicMock(spec=TaskType)
        task_node.task_properties.task_type.name = "Classification"

        project = MagicMock(spec=Project)
        project.task_graph.tasks = [task_node]

        # Mock LabelSchemaRepo and its behavior
        with patch("job.utils.export_utils.LabelSchemaRepo") as mock_label_schema_repo:
            label_schema_repo_instance = mock_label_schema_repo.return_value
            label_schema_repo_instance.get_latest_view_by_task.return_value = label_schema_view

            # Act
            result = ExportUtils.get_task_type_with_labels(project)

            # Assert
            assert len(result) == 1
            assert result[0] == ["classification", ["Label1", "Label2"]]

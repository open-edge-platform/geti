# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import unittest
from unittest.mock import MagicMock, patch

import pytest

from communication.exceptions import DatasetStorageAlreadyExistsException, MaxNumberOfDatasetsException
from communication.rest_controllers import DatasetRESTController
from communication.rest_views.dataset_storage_rest_views import NAME, USE_FOR_TRAINING
from managers.project_manager import ProjectManager

from geti_fastapi_tools.exceptions import BadRequestException
from geti_types import ID
from iai_core.entities.project import Project
from iai_core.repos import DatasetStorageRepo


@pytest.fixture
def dataset_controller():
    return DatasetRESTController()


@pytest.fixture
def fxt_annotation_statistics_rest():
    yield {
        "annotated_frames": 2,
        "annotated_images": 4,
        "annotated_videos": 1,
        "images": 5,
        "images_and_frames_per_label": [
            {"color": "#b100ffff", "label": "circle", "value": 2},
            {"color": "#00147fff", "label": "square", "value": 3},
            {"color": "#00fffaff", "label": "rectangle", "value": 1},
            {
                "color": "#2a2b2eff",
                "label": "Empty torch_segmentation torch_segmentation",
                "value": 0,
            },
        ],
        "objects_per_label": [
            {"color": "#b100ffff", "label": "circle", "value": 2},
            {"color": "#00147fff", "label": "square", "value": 4},
            {"color": "#00fffaff", "label": "rectangle", "value": 1},
            {
                "color": "#2a2b2eff",
                "label": "Empty torch_segmentation torch_segmentation",
                "value": 0,
            },
        ],
        "score": 0,
        "videos": 1,
    }


@pytest.fixture
def fxt_annotation_statistics_response(fxt_annotation_statistics_rest):
    yield fxt_annotation_statistics_rest


class TestDatasetRESTController:
    def test_create_dataset_storage(
        self,
        fxt_empty_project_persisted,
    ) -> None:
        dummy_dataset_storage_name = "dummy_dataset_storage_new"
        with patch.object(DatasetStorageRepo, "save", return_value=None) as patched_save_ds:
            result = DatasetRESTController.create_dataset_storage(
                fxt_empty_project_persisted.id_, {NAME: dummy_dataset_storage_name}
            )
        patched_save_ds.assert_called()
        assert not result[USE_FOR_TRAINING]
        assert result[NAME] == dummy_dataset_storage_name

    def test_create_dataset_storage_error(
        self,
        fxt_project,
    ) -> None:
        training_ds = fxt_project.get_training_dataset_storage()

        with (
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project),
            pytest.raises(DatasetStorageAlreadyExistsException),
        ):
            DatasetRESTController.create_dataset_storage(fxt_project.id_, {NAME: training_ds.name})

    def test_create_dataset_storage_empty_error(
        self,
        fxt_project,
    ) -> None:
        with (
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project),
            pytest.raises(BadRequestException),
        ):
            DatasetRESTController.create_dataset_storage(fxt_project.id_, {})

    @patch(
        "communication.rest_controllers.dataset_controller.MAX_NUMBER_OF_DATASET_STORAGES",
        1,
    )
    def test_create_dataset_storage_max_error(
        self,
        fxt_project,
    ) -> None:
        with (
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project),
            patch.object(Project, "dataset_storage_count", 1000),
            pytest.raises(MaxNumberOfDatasetsException),
        ):
            _ = DatasetRESTController.create_dataset_storage(fxt_project.id_, {"name": "new_name"})


class TestDatasetRESTControllerUnit(unittest.TestCase):
    @patch("communication.rest_controllers.dataset_controller.ProjectManager.get_project_by_id")
    @patch("communication.rest_controllers.dataset_controller.DatasetStorageRepo")
    @patch("communication.rest_controllers.dataset_controller.StatisticsUseCase.get_dataset_storage_statistics")
    def test_get_dataset_storage_statistics_successful(self, mock_get_stats, mock_repo, mock_get_project):
        project_id = ID("project_id")
        dataset_storage_id = ID("dataset_storage_id")
        mock_project = MagicMock()
        mock_dataset_storage = MagicMock()
        mock_get_project.return_value = mock_project
        mock_repo.return_value.get_by_id.return_value = mock_dataset_storage
        mock_get_stats.return_value = {"stats": "data"}

        result = DatasetRESTController.get_dataset_storage_statistics(project_id, dataset_storage_id)

        self.assertEqual(result, {"stats": "data"})
        mock_get_project.assert_called_once_with(project_id=project_id)
        mock_repo.return_value.get_by_id.assert_called_once_with(dataset_storage_id)
        mock_get_stats.assert_called_once_with(project=mock_project, dataset_storage=mock_dataset_storage)

    @patch("communication.rest_controllers.dataset_controller.ProjectManager.get_project_by_id")
    @patch("communication.rest_controllers.dataset_controller.DatasetStorageRepo")
    @patch("communication.rest_controllers.dataset_controller.DatasetRepo")
    @patch("communication.rest_controllers.dataset_controller.StatisticsUseCase.get_dataset_statistics")
    def test_get_dataset_statistics_successful(
        self,
        mock_get_stats,
        mock_dataset_repo,
        mock_dataset_storage_repo,
        mock_get_project,
    ):
        project_id = ID("project_id")
        dataset_storage_id = ID("dataset_storage_id")
        dataset_id = ID("dataset_id")
        mock_project = MagicMock()
        mock_dataset_storage = MagicMock()
        mock_dataset = MagicMock()
        mock_get_project.return_value = mock_project
        mock_dataset_storage_repo.return_value.get_by_id.return_value = mock_dataset_storage
        mock_dataset_repo.return_value.get_by_id.return_value = mock_dataset
        mock_get_stats.return_value = {"dataset_stats": "data"}

        result = DatasetRESTController.get_dataset_statistics(project_id, dataset_storage_id, dataset_id)

        self.assertEqual(result, {"dataset_stats": "data"})
        mock_get_project.assert_called_once_with(project_id=project_id)
        mock_dataset_storage_repo.return_value.get_by_id.assert_called_once_with(dataset_storage_id)
        mock_dataset_repo.return_value.get_by_id.assert_called_once_with(dataset_id)
        mock_get_stats.assert_called_once_with(dataset_storage=mock_dataset_storage, dataset=mock_dataset)

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""Test import utils"""

import os.path as osp
from unittest.mock import ANY, MagicMock, patch

import datumaro as dm
import pytest
from datumaro.components.errors import (
    DatasetImportError,
    MultipleFormatsMatchError,
    NoMatchingFormatsError,
    UnknownFormatError,
)
from geti_types import ID
from iai_core_py.entities.label import NullLabel
from iai_core_py.entities.model_template import TaskType
from iai_core_py.entities.project import Project
from iai_core_py.entities.video import NullVideo

from job.utils.exceptions import (
    DatasetFormatException,
    DatasetLoadingException,
    DatasetStorageAlreadyExistsException,
    FileNotFoundException,
    InvalidLabelException,
    MaxDatasetStorageReachedException,
    MaxMediaReachedException,
)
from job.utils.import_utils import ImportUtils


@pytest.mark.JobsComponent
class TestImportUtils:
    @patch("job.utils.import_utils.publish_event")
    def test_publish_project_created_message(self, mock_publish_event):
        project = MagicMock()
        project.workspace_id = ID("workspace_123")
        project.id_ = ID("project_456")

        ImportUtils.publish_project_created_message(project)

        mock_publish_event.assert_called_once_with(
            topic="project_creations",
            body={
                "workspace_id": str(project.workspace_id),
                "project_id": str(project.id_),
            },
            key=str(project.id_).encode(),
            headers_getter=ANY,
        )

    def test_get_validated_task_type(self):
        # Arrange
        project = MagicMock()
        project.workspace_id = ID("workspace_123")
        project.id_ = ID("project_456")
        trainable_task = MagicMock()
        trainable_task.task_properties.task_type = TaskType.DETECTION
        project.get_trainable_task_nodes.return_value = [trainable_task]

        # Act
        result = ImportUtils.get_validated_task_type(project=project)

        # Assert
        assert result == TaskType.DETECTION

    @patch("job.utils.import_utils.LabelRepo")
    def test_get_validated_labels_map(self, mock_label_repo):
        # Arrange
        label_ids_map = {
            "label_1": "id_1",
            "label_2": "id_2",
            "label_3": "id_3",
        }
        project_identifier = MagicMock()
        mock_label_repo.return_value.get_by_id.side_effect = lambda label_id: f"label_{label_id}"

        # Act
        result = ImportUtils.get_validated_labels_map(label_ids_map, project_identifier)

        # Assert
        expected_result = {
            "label_1": "label_id_1",
            "label_2": "label_id_2",
            "label_3": "label_id_3",
        }
        assert result == expected_result

        # InvalidLabelException
        with pytest.raises(InvalidLabelException):
            mock_label_repo.return_value.get_by_id.side_effect = lambda _: NullLabel()
            ImportUtils.get_validated_labels_map(label_ids_map, project_identifier)

    def test_detect_format(self):
        # Arrange
        path = "path_to_dataset"
        patch_target = "jobs_common_extras.datumaro_conversion.import_utils.ImportUtils.detect_format"

        # Act
        with patch(patch_target, return_value="detection") as mock_detect_format:
            format = ImportUtils.detect_format(path)
            mock_detect_format.assert_called()

        # Assert
        assert format == "detection"

        # exception raised
        with patch(patch_target, side_effect=MultipleFormatsMatchError(["format1", "format2"])):
            with pytest.raises(DatasetFormatException):
                ImportUtils.detect_format(path)

        with patch(patch_target, side_effect=NoMatchingFormatsError):
            with pytest.raises(DatasetFormatException):
                ImportUtils.detect_format(path)

        with patch(patch_target, side_effect=KeyError):
            with pytest.raises(DatasetFormatException):
                ImportUtils.detect_format(path)

        with patch(patch_target, side_effect=ValueError):
            with pytest.raises(ValueError):
                ImportUtils.detect_format(path)

    def test_parse_dataset(self):
        # Arrange
        path = "path_to_dataset"
        fmt = "datumaro"
        patch_target = "jobs_common_extras.datumaro_conversion.import_utils.ImportUtils.parse_dataset"
        mock_dataset = MagicMock()
        mock_error_collector = MagicMock()

        # Act
        with patch(patch_target, return_value=(mock_dataset, mock_error_collector)) as mock_detect_format:
            dataset, error_collector = ImportUtils.parse_dataset(path, fmt)
            mock_detect_format.assert_called()

        # Assert
        assert dataset == mock_dataset
        assert error_collector == mock_error_collector

        # exception raised
        with patch(patch_target, side_effect=UnknownFormatError("unknown_format")):
            with pytest.raises(DatasetLoadingException):
                ImportUtils.parse_dataset(path, fmt)

        with patch(patch_target, side_effect=DatasetImportError) as patched:
            patched.side_effect.__cause__ = "Failure Reason"
            with pytest.raises(DatasetLoadingException) as exe_info:
                ImportUtils.parse_dataset(path, fmt)
            exception_message = str(exe_info.value)
            assert "Failure Reason" in exception_message

        with patch(patch_target, side_effect=DatasetImportError) as patched:
            patched.side_effect.__cause__ = "Failed to parse names file path from config"
            with pytest.raises(DatasetLoadingException) as exe_info:
                ImportUtils.parse_dataset(path, "yolo")
            exception_message = str(exe_info.value)
            assert "due to missing 'names' field in 'obj.data'" in exception_message

        with patch(patch_target, side_effect=KeyError):
            with pytest.raises(KeyError):
                ImportUtils.parse_dataset(path, fmt)

    @patch("job.utils.import_utils.MAX_NUMBER_OF_MEDIA_PER_PROJECT", 100000)
    def test_check_max_number_of_media(self):
        # Arrange
        mock_dataset = MagicMock()
        mock_project = MagicMock()
        mock_project.get_dataset_storages.return_value = [MagicMock()]

        # Act & Assert : No exceptions are raised
        with patch.object(ImportUtils, "_count_media_in_dm_dataset", side_effect=[10]) as mocked_func:
            ImportUtils.check_max_number_of_media(mock_dataset)
            mocked_func.assert_called()

        # Act & Assert: exception raised
        with (
            pytest.raises(MaxMediaReachedException),
            patch.object(ImportUtils, "_count_media_in_dm_dataset", side_effect=[100000]) as mocekd_func,
        ):
            ImportUtils.check_max_number_of_media(mock_dataset)
            mocekd_func.assert_called()

        with (
            pytest.raises(MaxMediaReachedException),
            patch.object(ImportUtils, "_count_media_in_dm_dataset", side_effect=[10000]) as mocked_func,
            patch("job.utils.import_utils.ImageRepo") as mocked_image_repo,
            patch("job.utils.import_utils.VideoRepo") as mocked_video_repo,
        ):
            image_repo = mocked_image_repo.return_value
            image_repo.count.return_value = 100000
            video_repo = mocked_video_repo.return_value
            video_repo.count.return_value = 0
            ImportUtils.check_max_number_of_media(mock_dataset, mock_project)
            mocked_func.assert_called()

    def _get_sample_dataset(self) -> dm.Dataset:
        dm_dataset = dm.Dataset.from_iterable(
            iterable=[
                dm.DatasetItem(
                    "image", media=dm.Image.from_file("image.jpg"), annotations=[dm.Bbox(1, 1, 5, 5, label=0)]
                ),
                dm.DatasetItem("video", media=dm.Video("video.mp4"), annotations=[dm.Label(label=2)]),
                dm.DatasetItem(
                    "video1_frame0", media=dm.VideoFrame(dm.Video("video1.mp4"), 0), annotations=[dm.Label(label=1)]
                ),
                dm.DatasetItem(
                    "video1_frame1",
                    media=dm.VideoFrame(dm.Video("video1.mp4"), 1),
                    annotations=[dm.Polygon([0, 0, 3, 3, 5, 4], label=2)],
                ),
                dm.DatasetItem(
                    "video2_frame0",
                    media=dm.VideoFrame(dm.Video("video2.mp4"), 0),
                    annotations=[dm.Ellipse(2, 3, 7, 7, label=3)],
                ),
                dm.DatasetItem(
                    "video3",
                    media=dm.Video("video3.mp4"),
                ),
                dm.DatasetItem("not_supported", media=dm.MediaElement(), annotations=[dm.Label(label=3)]),
            ],
            categories=["a", "b", "c", "d"],
            media_type=dm.MediaElement,
        )
        return dm_dataset

    def test__count_media_in_dm_dataset(self):
        # Arrange
        dm_dataset = self._get_sample_dataset()

        # Act
        num = ImportUtils._count_media_in_dm_dataset(dm_dataset)

        # Assert
        assert num == 4

    def test_create_dataset_storage(self, fxt_workspace_id):
        # Arrange
        project_id = ID("project_id")
        workspace_id = fxt_workspace_id
        project = Project(
            id=project_id,
            name="project",
            creator_id="dummy_user",
            description="dummy_project",
            dataset_storages=[],
        )
        test_dataset_name = "test_dataset"
        for dataset_name in [None, "test_dataset"]:
            with (
                patch("job.utils.import_utils.DatasetStorageRepo"),
                patch("job.utils.import_utils.ProjectRepo") as mocked_obj,
            ):
                ds = ImportUtils.create_dataset_storage(project=project, dataset_name=dataset_name)
                mocked_obj.assert_called_once()
            assert ds.workspace_id == workspace_id
            assert ds.project_id == project_id
            if dataset_name:
                ds.name == dataset_name

        with pytest.raises(DatasetStorageAlreadyExistsException):
            ImportUtils.create_dataset_storage(project=project, dataset_name=test_dataset_name)

        with (
            pytest.raises(MaxDatasetStorageReachedException),
            patch("job.utils.import_utils.MAX_NUMBER_OF_DATASET_STORAGES", len(project.dataset_storage_adapters)),
        ):
            ImportUtils.create_dataset_storage(project=project)

    @patch("job.utils.import_utils.AnnotationUploadManager")
    @patch("job.utils.import_utils.VideoUploadManager")
    @patch("job.utils.import_utils.ImageUploadManager")
    def test_populate_project_from_datumaro_dataset(
        self, patched_image_uploader, patched_video_uploader, patched_anns_uploader
    ):
        # Arrange
        image_uploader = patched_image_uploader.return_value
        video_uploader = patched_video_uploader.return_value
        anns_uploader = patched_anns_uploader.return_value

        video_uploader.upload.return_value = MagicMock(id_=ID("video_id"), width=32, height=32, total_frames=10)

        # Act
        with patch("job.utils.import_utils.VideoAnnotationRangeRepo") as mocked_obj:
            ImportUtils.populate_project_from_datumaro_dataset(
                project=MagicMock(),
                dataset_storage_identifier=MagicMock(),
                dm_dataset=self._get_sample_dataset(),
                label_schema=MagicMock(),
                get_sc_label=MagicMock(),
                user_id="user_id",
            )
            mocked_obj.assert_called_once()

        # Assert
        assert image_uploader.upload.call_count == 1
        assert video_uploader.upload.call_count == 4
        assert anns_uploader.upload.call_count == 4

    @patch("job.utils.import_utils.AnnotationUploadManager")
    @patch("job.utils.import_utils.VideoUploadManager")
    @patch("job.utils.import_utils.ImageUploadManager")
    def test_populate_project_from_datumaro_dataset_video_not_found(
        self, patched_image_uploader, patched_video_uploader, patched_anns_uploader
    ):
        # Arrange
        image_uploader = patched_image_uploader.return_value
        video_uploader = patched_video_uploader.return_value
        anns_uploader = patched_anns_uploader.return_value

        video_path = "/path/to/video.mp4"
        dm_dataset = dm.Dataset.from_iterable(
            iterable=[
                dm.DatasetItem(
                    "video1_frame0", media=dm.VideoFrame(dm.Video(video_path), 0), annotations=[dm.Label(label=1)]
                ),
            ],
            categories=["a", "b", "c", "d"],
            media_type=dm.MediaElement,
        )

        video_uploader.upload.return_value = NullVideo()

        # Act
        with pytest.raises(FileNotFoundException) as e:
            ImportUtils.populate_project_from_datumaro_dataset(
                project=MagicMock(),
                dataset_storage_identifier=MagicMock(),
                dm_dataset=dm_dataset,
                label_schema=MagicMock(),
                get_sc_label=MagicMock(),
                user_id="user_id",
            )

        # Assert
        assert str(e.value).startswith("The requested video could not be found in this dataset.")
        assert f"video_path: {osp.basename(video_path)}" in str(e.value)
        assert video_path not in str(e.value)

        assert image_uploader.upload.call_count == 0
        assert video_uploader.upload.call_count == 1
        assert anns_uploader.upload.call_count == 0

    @pytest.mark.parametrize(
        ("has_empty_label", "annotations", "expected"),
        [
            (True, [1], False),
            (True, [], False),
            (False, [1], False),
            (False, [], True),
        ],
    )
    def test_is_video_unannotated(self, has_empty_label, annotations, expected):
        # Arrange
        dm_item = MagicMock(
            attributes={"has_empty_label": has_empty_label},
            annotations=annotations,
        )

        # Action
        actual = ImportUtils.is_video_unannotated(dm_item)

        # Assert
        assert actual == expected

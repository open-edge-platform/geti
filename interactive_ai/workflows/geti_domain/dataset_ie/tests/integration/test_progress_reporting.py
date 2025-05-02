# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import sys
from unittest.mock import MagicMock, patch

import pytest
from geti_types import ID
from iai_core_py.entities.project import Project
from iai_core_py.utils.deletion_helpers import DeletionHelpers
from jobs_common_extras.datumaro_conversion.definitions import GetiProjectType

from job.tasks.export_tasks.export_dataset_task import STEPS_PROGRESS_RATIO as STEPS_RATIO_EXPORT
from job.tasks.export_tasks.export_dataset_task import export_dataset_task
from job.tasks.import_tasks.create_project_from_dataset import STEPS_PROGRESS_RATIO as STEPS_RATIO_NEW
from job.tasks.import_tasks.create_project_from_dataset import create_project_from_dataset
from job.tasks.import_tasks.import_dataset_to_project import STEPS_PROGRESS_RATIO as STEPS_RATIO_EXISTING
from job.tasks.import_tasks.import_dataset_to_project import import_dataset_to_project
from job.tasks.import_tasks.parse_dataset_existing_project import parse_dataset_for_import_to_existing_project
from job.tasks.import_tasks.parse_dataset_new_project import parse_dataset_for_import_to_new_project
from tests.test_helpers import get_label_maps, return_none


class ProgressChecker:
    def __init__(self, steps_count: int):
        self.steps_count = steps_count
        self.last_step_index = -1
        self.last_progress = -1.0
        self.call_count: list[int] = [0] * steps_count

    def _check_progress(self, total_progress: float, step_index: int):
        assert self.last_step_index <= step_index < self.steps_count
        if self.last_step_index != step_index:
            self.last_step_index = step_index

        assert 0 <= total_progress <= 100
        assert self.last_progress <= total_progress
        self.last_progress = total_progress

        self.call_count[step_index] += 1

    def check_progress_is_increased(
        self,
        **kwargs,
        # step_index: int, steps_count: int, step_progress: float, step_message: str | None = None
    ):
        step_index: int = kwargs["step_index"]
        steps_count: int = kwargs["steps_count"]
        step_progress: float = kwargs["step_progress"]

        assert steps_count == self.steps_count

        assert 0 <= step_progress <= 100
        progress = (step_index * 100 + step_progress) / steps_count

        self._check_progress(progress, step_index)

    def interval_in_percent(self, step_index: int) -> float:
        return float(self.steps_count)


class WeightedProgressChecker(ProgressChecker):
    def __init__(self, steps_ratio: list[float]):
        total = sum(steps_ratio)
        normalized_ratio: list[float] = []
        for ratio in steps_ratio:
            normalized_ratio.append(100.0 * ratio / total)
        self.steps_ratio = normalized_ratio

        super().__init__(steps_count=len(steps_ratio))

    def check_progress_is_increased(
        self,
        **kwargs,
        # progress: float, message: str | None = None, warning: str | None = None
    ):
        progress: float = kwargs["progress"]

        step_index = self.steps_count
        for i in range(self.steps_count):
            if progress <= sum(self.steps_ratio[: i + 1]):
                step_index = i
                break
        # check if new_step is started: (n+1)th start_step is called right after nth finish_step is called.
        if progress - self.last_progress < sys.float_info.epsilon:
            step_index += 1

        self._check_progress(progress, step_index)

    def interval_in_percent(self, step_index: int) -> float:
        return 100 / self.steps_ratio[step_index]


@pytest.mark.DatasetIEMsComponent
class TestProgressReporting:
    @staticmethod
    def _get_expected_iteration(n_items: int, interval_in_percent: float):
        for i in range(1, n_items):
            if 100 * i / n_items > interval_in_percent:
                return (n_items - 1) // i
        return 0

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    def test_import_dataset_to_new_project(self, fxt_import_data_repo, fxt_coco_dataset_id, request):
        progress_checker_prepare = ProgressChecker(3)
        progress_checker_perform = WeightedProgressChecker(STEPS_RATIO_NEW)
        assert len(STEPS_RATIO_NEW) == 3
        n_items = 11

        project_type = GetiProjectType.DETECTION
        label_names = ["person", "car"]
        color_by_labels = {"person": "#12345678", "car": "#87654321"}
        project_id = ""

        def _get_metadat(metadata: dict):
            nonlocal project_id
            project_id = metadata["project_id"]

        with (
            patch("job.tasks.import_tasks.parse_dataset_new_project.publish_metadata_update", new=MagicMock),
            patch("job.tasks.import_tasks.parse_dataset_new_project.ImportDataRepo", return_value=fxt_import_data_repo),
            patch("job.utils.progress_utils.MIN_INTERVAL_IN_SEC", 0),
            patch(
                "job.utils.progress_utils.report_task_step_progress",
                new=progress_checker_prepare.check_progress_is_increased,
            ),
        ):
            parse_dataset_for_import_to_new_project(import_id=str(fxt_coco_dataset_id))

            assert progress_checker_prepare.call_count[0] >= 2  # 1 start_step + 1 finish_step + unknown iteration
            for step_index in [1, 2]:
                assert (
                    progress_checker_prepare.call_count[step_index]
                    == self._get_expected_iteration(n_items, progress_checker_prepare.interval_in_percent(step_index))
                    + 1
                )  # iterations + 1 finish_step

        with (
            patch("job.tasks.import_tasks.create_project_from_dataset.publish_metadata_update", new=_get_metadat),
            patch(
                "job.tasks.import_tasks.create_project_from_dataset.ImportDataRepo", return_value=fxt_import_data_repo
            ),
            patch("job.utils.progress_utils.MIN_INTERVAL_IN_SEC", 0),
            patch("job.utils.progress_utils.report_progress", new=progress_checker_perform.check_progress_is_increased),
        ):
            create_project_from_dataset(
                import_id=str(fxt_coco_dataset_id),
                name="test_project",
                project_type_str=project_type.name,
                label_names=label_names,
                color_by_label=color_by_labels,
                keypoint_structure={"edges": [], "positions": []},
                user_id="dummy_user",
            )

            assert progress_checker_perform.call_count[0] >= 2  # 1 start_step + 1 finish_step + unknown iteration
            for step_index in [1, 2]:
                assert (
                    progress_checker_perform.call_count[step_index]
                    == self._get_expected_iteration(n_items, progress_checker_perform.interval_in_percent(step_index))
                    + 2
                )  # iterations + 1 start_step + 1 finish_step

        request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=ID(project_id)))

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    def test_import_dataset_to_existing_project(
        self,
        fxt_import_data_repo,
        fxt_coco_dataset_id,
        fxt_annotated_detection_project: Project,
    ):
        progress_checker_prepare = ProgressChecker(3)
        progress_checker_perform = WeightedProgressChecker(STEPS_RATIO_EXISTING)
        assert len(STEPS_RATIO_EXISTING) == 2
        n_items = 11
        label_names = ["person", "car"]

        with (
            patch("job.tasks.import_tasks.parse_dataset_existing_project.publish_metadata_update", new=MagicMock),
            patch(
                "job.tasks.import_tasks.parse_dataset_existing_project.ImportDataRepo",
                return_value=fxt_import_data_repo,
            ),
            patch("job.utils.progress_utils.MIN_INTERVAL_IN_SEC", 0),
            patch(
                "job.utils.progress_utils.report_task_step_progress",
                new=progress_checker_prepare.check_progress_is_increased,
            ),
        ):
            parse_dataset_for_import_to_existing_project(
                import_id=str(fxt_coco_dataset_id), project_id=str(fxt_annotated_detection_project.id_)
            )

            assert progress_checker_prepare.call_count[0] >= 2  # 1 start_step + 1 finish_step + unknown iteration
            for step_index in [1, 2]:
                assert (
                    progress_checker_prepare.call_count[step_index]
                    == self._get_expected_iteration(n_items, progress_checker_prepare.interval_in_percent(step_index))
                    + 1
                )  # iterations + 1 finish_step

        # Generate labels_map that maps from datumaro label_name to project Label
        labels_map = get_label_maps(project=fxt_annotated_detection_project, dm_label_names=label_names)
        labels_map_str = {key: str(label.id_) for key, label in labels_map.items()}

        dataset_storage = fxt_annotated_detection_project.get_training_dataset_storage()
        with (
            patch("job.tasks.import_tasks.import_dataset_to_project.publish_metadata_update", new=MagicMock),
            patch("job.tasks.import_tasks.import_dataset_to_project.ImportDataRepo", return_value=fxt_import_data_repo),
            patch("job.utils.progress_utils.MIN_INTERVAL_IN_SEC", 0),
            patch("job.utils.progress_utils.report_progress", new=progress_checker_perform.check_progress_is_increased),
        ):
            import_dataset_to_project(
                import_id=str(fxt_coco_dataset_id),
                project_id=str(fxt_annotated_detection_project.id_),
                label_ids_map=labels_map_str,
                dataset_storage_id=str(dataset_storage.id_),
                dataset_name="dataset_name",
                user_id="dummy_user",
            )
            assert progress_checker_perform.call_count[0] >= 2  # 1 start_step + 1 finish_step + unknown iteration
            assert (
                progress_checker_perform.call_count[1]
                == self._get_expected_iteration(n_items, progress_checker_perform.interval_in_percent(1)) + 2
            )  # iterations + 1 start_step + 1 finish_step

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @pytest.mark.parametrize(
        "export_format",
        [
            "coco",
            "datumaro",
            "voc",
            "yolo",
        ],
    )
    def test_export_dataset(
        self,
        export_format,
        fxt_annotated_segmentation_project,
        fxt_export_data_repo,
        fxt_organization_id,
    ):
        progress_checker = WeightedProgressChecker(STEPS_RATIO_EXPORT)
        assert len(STEPS_RATIO_EXPORT) == 3
        n_items = 12

        project: Project = fxt_annotated_segmentation_project
        dataset_storage = project.get_training_dataset_storage()
        with (
            patch(
                "job.tasks.export_tasks.export_dataset_task.publish_metadata_update", new=MagicMock()
            ) as mocked_publish,
            patch("job.tasks.export_tasks.export_dataset_task.ExportDataRepo", return_value=fxt_export_data_repo),
            patch("job.utils.progress_utils.MIN_INTERVAL_IN_SEC", 0),
            patch("job.utils.progress_utils.report_progress", new=progress_checker.check_progress_is_increased),
        ):
            _ = export_dataset_task(
                organization_id=str(fxt_organization_id),
                project_id=str(project.id_),
                dataset_storage_id=str(dataset_storage.id_),
                include_unannotated=True,
                export_format=export_format,
                save_video_as_images=True,
            )
            mocked_publish.assert_called()
            assert progress_checker.call_count[0] == 2  # 1 start_step + 1 finish_step
            # | format   | stream | iter_count |
            # |----------|--------|------------|
            # | coco     | o      | 1          |
            # | datumaro | o      | 2          |
            # | voc      | o      | 2          |
            # | yolo     | o      | 1          |
            # So we don't need to consider the case, stream=x
            iter_count = 1 if export_format in ["coco", "yolo"] else 2
            assert (
                progress_checker.call_count[1]
                == self._get_expected_iteration(n_items * iter_count, progress_checker.interval_in_percent(1)) + 2
            )  # iterations + 1 start_step + 1 finish_step
            assert progress_checker.call_count[2] == 3  # 1 start_step + 1   + 1 finish_step

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import TYPE_CHECKING, cast
from unittest.mock import patch

import pytest
from geti_spicedb_tools import Permissions, SpiceDB

from managers.project_manager import ProjectManager

from geti_fastapi_tools.exceptions import ProjectNotFoundException
from geti_types import ID
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.project import NullProject
from iai_core.repos import DatasetStorageRepo, ProjectRepo
from iai_core.repos.project_repo_helpers import ProjectQueryData, ProjectSortBy, ProjectSortDirection

if TYPE_CHECKING:
    from collections.abc import Mapping

    from iai_core.entities.label import Label
    from iai_core.entities.label_schema import LabelSchema


class TestProjectManagerGetProjects:
    def test_get_projects_names(self, fxt_project) -> None:
        user_uid = "admin"
        permitted_projects = (fxt_project.id_,)

        with (
            patch.object(ProjectRepo, "get_names", return_value={fxt_project.id_: "Test project"}) as pr_get_names,
            patch.object(SpiceDB, "get_user_projects", return_value=permitted_projects) as sdb_get_user_projects,
        ):
            result_names = ProjectManager().get_projects_names(user_uid=user_uid)

        assert result_names == {fxt_project.id_: "Test project"}, "Expected to return projects names from repo"
        sdb_get_user_projects.assert_called_once_with(user_id=user_uid, permission=Permissions.VIEW_PROJECT)
        pr_get_names.assert_called_once_with(permitted_projects)

    def test_get_projects_and_count_all(self, fxt_project) -> None:
        user_uid = "admin"
        permitted_projects = (fxt_project.id_,)
        query_data = ProjectQueryData(
            skip=0,
            limit=100,
            name="",
            sort_by=ProjectSortBy.CREATION_DATE,
            sort_direction=ProjectSortDirection.DSC,
            with_size=False,
        )

        with (
            patch.object(
                ProjectRepo,
                "get_by_page",
                return_value=[fxt_project],
            ) as pr_get_by_page,
            patch.object(
                ProjectRepo,
                "count_all",
                return_value=1,
            ) as pr_count_all,
            patch.object(SpiceDB, "get_user_projects", return_value=permitted_projects) as sdb_get_user_projects,
        ):
            result_projects, result_count = ProjectManager().get_projects_and_count_all(
                user_uid=user_uid, query_data=query_data
            )

        assert result_projects == [fxt_project], "Expected to return projects from repo"
        assert result_count == 1, "Expected to return projects count from repo"
        sdb_get_user_projects.assert_called_once_with(user_id=user_uid, permission=Permissions.VIEW_PROJECT)
        pr_get_by_page.assert_called_once_with(
            query_data=query_data,
            include_hidden=True,
            permitted_projects=permitted_projects,
        )
        pr_count_all.assert_called_once_with(include_hidden=True, permitted_projects=permitted_projects)


class TestProjectManager:
    def test_get_project_by_id(self, fxt_project) -> None:
        # Arrange

        PROJECT_ID = ID("project_id_123")

        # Act
        with (
            patch("iai_core.repos.project_repo.ProjectRepo.__init__", return_value=None) as patched_repo,
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as patched_get_by_id,
        ):
            result = ProjectManager().get_project_by_id(project_id=PROJECT_ID)

        # Assert
        patched_repo.assert_called_once()
        patched_get_by_id.assert_called_once_with(PROJECT_ID)
        assert result == fxt_project

    def test_manage_dataset_storages_in_project(self, fxt_project) -> None:
        # Arrange
        with patch.object(ProjectRepo, "save", return_value=None) as patched_save_project:
            dataset_storage_id = DatasetStorageRepo.generate_id()
            dataset_storage = DatasetStorage(
                name="Test dataset_storage",
                project_id=fxt_project.id_,
                _id=dataset_storage_id,
                use_for_training=False,
            )

            # Act
            updated_project = ProjectManager.add_dataset_storage(
                project=fxt_project,
                dataset_storage=dataset_storage,
            )
            ret_dataset_storage = ProjectManager.get_dataset_storage_by_id(
                project=fxt_project, dataset_storage_id=dataset_storage_id
            )

        # Assert
        patched_save_project.assert_called_once_with(updated_project)
        assert set(updated_project.dataset_storage_ids) == {
            updated_project.training_dataset_storage_id,
            dataset_storage.id_,
        }
        assert ret_dataset_storage == dataset_storage
        assert dataset_storage_id in updated_project.dataset_storage_ids

    def test_get_project_by_id_error(self) -> None:
        # Arrange

        PROJECT_ID = ID("project_id_124")

        # Act & Assert
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=NullProject()),
            pytest.raises(ProjectNotFoundException),
        ):
            ProjectManager().get_project_by_id(project_id=PROJECT_ID)

    # fmt: off
    @pytest.mark.parametrize(
        "task_scope, multilabel, hierarchical, lazyfxt_task_graph, lazyfxt_label_schema_factory",
        [
            ("global", False, False, "fxt_classification_task_graph", "fxt_classification_label_schema_factory"),
            ("global", True, False, "fxt_classification_task_graph", "fxt_classification_label_schema_factory"),
            ("global", False, True, "fxt_classification_task_graph", "fxt_classification_label_schema_factory"),
            ("global", True, True, "fxt_classification_task_graph", "fxt_classification_label_schema_factory"),
            ("local", False, False, "fxt_detection_task_graph", "fxt_detection_label_schema_factory"),
            ("local", False, False, "fxt_segmentation_task_graph", "fxt_segmentation_label_schema_factory"),
        ],
        ids=[
            "Classification (multi-class)",
            "Classification (multi-label)",
            "Classification (multi-class, hierarchical)",
            "Classification (multi-label, hierarchical)",
            "Detection",
            "Segmentation",
        ],
    )
    # fmt: on
    def test_compute_labels_affected_by_schema_change_addition_single_task(
        self,
        request,
        task_scope,
        multilabel,
        hierarchical,
        lazyfxt_task_graph,
        lazyfxt_label_schema_factory,
    ) -> None:
        """
        Test ProjectManager.compute_labels_affected_by_schema_change for
        label addition on both local and global tasks.

        Scenario:
          - the task is global or local
          - the old schema had 2 labels
          - the new schema has 3 labels
          - the new label is flagged as to be revisited

        Expected:
          - only the new label needs to be revisited
        """
        # Arrange
        task_graph = request.getfixturevalue(lazyfxt_task_graph)
        label_schema_factory = request.getfixturevalue(lazyfxt_label_schema_factory)
        extra_args = {
            "multilabel": multilabel,
            "hierarchical": hierarchical,
        }
        new_project_label_schema: LabelSchema = label_schema_factory(num_labels=3, **extra_args)
        new_tasks_label_schemas: Mapping[str, LabelSchema] = {task_graph.tasks[-1].title: new_project_label_schema}
        new_label: Label = cast("Label", new_project_label_schema.get_labels(False)[-1])
        labels_names_flagged_to_revisit = [new_label.name]

        # Act
        affected_labels = ProjectManager.compute_labels_affected_by_schema_change(
            new_project_label_schema=new_project_label_schema,
            new_tasks_label_schemas=new_tasks_label_schemas,
            new_labels=[new_label],
            labels_names_flagged_to_revisit=labels_names_flagged_to_revisit,
            task_graph=task_graph,
        )

        # Assert
        if task_scope == "global":
            assert not affected_labels.local
            if multilabel:
                assert not affected_labels.global_old_groups
                assert affected_labels.global_new_groups == (new_label,)
            else:  # multiclass
                assert not affected_labels.global_old_groups
                assert not affected_labels.global_new_groups
        elif task_scope == "local":
            assert not affected_labels.global_old_groups
            assert not affected_labels.global_new_groups
            assert affected_labels.local == (new_label,)
        else:
            raise ValueError(f"Unrecognized value for `task_scope`: `{task_scope}`")

    # fmt: off
    @pytest.mark.parametrize(
        "multilabel_cls, hierarchical_cls",
        [
            (False, False),
            (False, True),
            (True, False),
            (True, True),
        ],
        ids=[
            "Detection -> classification multi-class",
            "Detection -> classification multi-class hierarchical",
            "Detection -> classification multi-label",
            "Detection -> classification multi-label hierarchical",
        ],
    )
    # fmt: on
    def test_compute_labels_affected_by_schema_change_addition_det_cls_chain(
        self,
        multilabel_cls,
        hierarchical_cls,
        fxt_detection_classification_label_schema_factory,
        fxt_detection_label_schema_factory,
        fxt_classification_label_schema_factory,
        fxt_detection_classification_task_graph,
    ) -> None:
        """
        Test ProjectManager.compute_labels_affected_by_schema_change for
        label addition on a detection -> classification task chain

        Scenario:
          - the project is detection -> classification
          - the detection schema has 2 labels (one empty)
          - the old classification schema has 2 labels (multi-class)
          - the new classification schema has 3 labels (multi-class)
          - the new label is flagged as to be revisited

        Expected:
          - the detection label (parent of the new classification one) must be revisited
        """
        # Arrange
        new_det_label_schema = fxt_detection_label_schema_factory(num_labels=1)
        new_cls_label_schema = fxt_classification_label_schema_factory(
            num_labels=3, multilabel=multilabel_cls, hierarchical=hierarchical_cls
        )
        new_project_label_schema = fxt_detection_classification_label_schema_factory(
            num_det_labels=1,
            num_cls_labels=3,
            multilabel_cls=multilabel_cls,
            hierarchical_cls=hierarchical_cls,
        )
        task_graph = fxt_detection_classification_task_graph
        new_tasks_label_schemas = {
            task_graph.tasks[1].title: new_det_label_schema,
            task_graph.tasks[3].title: new_cls_label_schema,
        }
        det_label: Label = cast("Label", new_det_label_schema.get_labels(False)[0])
        new_label: Label = cast("Label", new_cls_label_schema.get_labels(False)[-1])
        labels_names_flagged_to_revisit = [new_label.name]

        # Act
        affected_labels = ProjectManager.compute_labels_affected_by_schema_change(
            new_project_label_schema=new_project_label_schema,
            new_tasks_label_schemas=new_tasks_label_schemas,
            new_labels=[new_label],
            labels_names_flagged_to_revisit=labels_names_flagged_to_revisit,
            task_graph=task_graph,
        )

        # Assert
        assert not affected_labels.global_old_groups
        if multilabel_cls:
            assert affected_labels.global_new_groups == (new_label,)
        else:
            assert not affected_labels.global_new_groups
        assert affected_labels.local == (det_label,)

    def test_compute_labels_affected_by_schema_change_addition_det_seg_chain(
        self,
        fxt_detection_segmentation_label_schema_factory,
        fxt_detection_label_schema_factory,
        fxt_segmentation_label_schema_factory,
        fxt_detection_segmentation_task_graph,
    ) -> None:
        """
        Test ProjectManager.compute_labels_affected_by_schema_change for
        label addition on a detection -> segmentation task chain

        Scenario:
          - the project is detection -> segmentation
          - the detection schema has 2 labels (one empty)
          - the old segmentation schema has 2 labels (multi-class)
          - the new segmentation schema has 3 labels (multi-class)
          - the new label is flagged as to be revisited

        Expected:
          - all the detection labels, plus the new segmentation one are affected
        """
        # Arrange
        det_label_schema = fxt_detection_label_schema_factory(num_labels=2)
        new_seg_label_schema = fxt_segmentation_label_schema_factory(num_labels=3)
        new_project_label_schema = fxt_detection_segmentation_label_schema_factory(num_det_labels=2, num_seg_labels=3)
        task_graph = fxt_detection_segmentation_task_graph
        new_tasks_label_schemas = {
            task_graph.tasks[1].title: det_label_schema,
            task_graph.tasks[3].title: new_seg_label_schema,
        }
        new_label: Label = cast("Label", new_seg_label_schema.get_labels(False)[-1])
        labels_names_flagged_to_revisit = [new_label.name]

        # Act
        affected_labels = ProjectManager.compute_labels_affected_by_schema_change(
            new_project_label_schema=new_project_label_schema,
            new_tasks_label_schemas=new_tasks_label_schemas,
            new_labels=[new_label],
            labels_names_flagged_to_revisit=labels_names_flagged_to_revisit,
            task_graph=task_graph,
        )

        # Assert
        assert not affected_labels.global_old_groups
        assert not affected_labels.global_new_groups
        expected_labels_affected_local = {new_label} | set(det_label_schema.get_labels(True))
        assert isinstance(affected_labels.local, tuple)
        assert set(affected_labels.local) == expected_labels_affected_local

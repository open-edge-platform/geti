# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import TYPE_CHECKING
from unittest import mock
from unittest.mock import patch

import pytest

from communication.rest_controllers import ProjectRESTController
from communication.rest_views.pipeline import PipelineRESTViews
from communication.rest_views.project_rest_views import (
    CREATION_TIME,
    DATASETS,
    ID_,
    NAME,
    PIPELINE,
    PROJECTS,
    THUMBNAIL,
    ProjectRESTViews,
)

from iai_core_py.repos import ModelRepo
from iai_core_py.services.model_service import ModelService

if TYPE_CHECKING:
    from geti_types import ID
    from iai_core_py.entities.label_schema import LabelSchemaView


class TestProjectRESTViews:
    @pytest.mark.parametrize(
        "include_dataset_storages",
        (True, False),
    )
    def test_project_to_rest(
        self,
        fxt_organization_id,
        fxt_project,
        fxt_project_rest,
        fxt_empty_label_schema,
        fxt_model,
        include_dataset_storages,
    ):
        keys_to_match_shallow = {PIPELINE}
        if include_dataset_storages:
            keys_to_match_shallow.add(DATASETS)
        keys_to_match_strict = {NAME, ID_, CREATION_TIME, THUMBNAIL}
        label_schema_per_task: dict[ID, LabelSchemaView | None] = {
            t.id_: fxt_empty_label_schema for t in fxt_project.task_graph.tasks if t.task_properties.is_trainable
        }

        with (
            patch.object(PipelineRESTViews, "task_graph_to_rest", return_value={}) as mock_graph_rest,
            patch.object(ModelService, "get_inference_active_model", return_value=fxt_model),
            patch.object(
                ProjectRESTController,
                "_get_label_schema_per_task",
                return_value=label_schema_per_task,
            ),
            patch.object(
                ModelRepo,
                "get_latest_model_for_inference",
                return_value=fxt_model,
            ),
            patch.object(
                ModelRepo,
                "get_all_equivalent_model_ids",
                return_value=[fxt_model.id_],
            ),
        ):
            result = ProjectRESTViews.project_to_rest(
                organization_id=fxt_organization_id,
                project=fxt_project,
                label_schema_per_task=label_schema_per_task,
                storage_info={},
                include_dataset_storages=include_dataset_storages,
            )

            mock_graph_rest.assert_called_once_with(
                graph=fxt_project.task_graph,
                label_schema_per_task={
                    t.id_: fxt_empty_label_schema
                    for t in fxt_project.task_graph.tasks
                    if t.task_properties.is_trainable
                },
                include_deleted_labels=False,
                keypoint_structure=None,
            )
        for k in keys_to_match_strict:
            assert result[k] == fxt_project_rest[k]
        for k in keys_to_match_shallow:
            assert k in result
            assert isinstance(result[k], type(fxt_project_rest[k]))

    def test_projects_to_rest(self, fxt_project, fxt_project_rest, fxt_organization_id, fxt_empty_label_schema) -> None:
        projects_list = [fxt_project]
        label_schema_per_task_per_project: list[dict[ID, LabelSchemaView | None]] = [
            {t.id_: fxt_empty_label_schema for t in project.task_graph.tasks if t.task_properties.is_trainable}
            for project in projects_list
        ]

        with patch.object(ProjectRESTViews, "project_to_rest", return_value={}) as mock_project_rest:
            result = ProjectRESTViews.projects_to_rest(
                organization_id=fxt_organization_id,
                projects=projects_list,
                label_schema_per_task_per_project=label_schema_per_task_per_project,
                project_counts=0,
                next_page="",
                storage_info_per_project=[{}],
            )

            mock_project_rest.assert_called()
        assert PROJECTS in result
        assert isinstance(result[PROJECTS], list)
        assert len(result[PROJECTS]) == len(projects_list)
        assert all(isinstance(item, dict) for item in result[PROJECTS])

    def test_projects_names_to_rest(self, fxt_project, fxt_project_rest, fxt_organization_id) -> None:
        result = ProjectRESTViews.projects_names_to_rest(projects_names={fxt_project.id_: fxt_project.name})

        assert PROJECTS in result
        assert result[PROJECTS] == [{"id": fxt_project.id_, "name": fxt_project.name}]

    def test_invalid_project_to_rest(self, fxt_project, fxt_organization_id, fxt_empty_label_schema):
        """
        Checks that an invalid project does not prevent rest mapping from failing
        """
        error_mock = mock.Mock()
        error_mock.side_effect = Exception

        with patch.object(ProjectRESTViews, "project_to_rest", error_mock) as mock_project_rest:
            result = ProjectRESTViews.projects_to_rest(
                organization_id=fxt_organization_id,
                projects=[fxt_project],
                label_schema_per_task_per_project=[fxt_empty_label_schema],
                project_counts=0,
                next_page="",
                storage_info_per_project=[{}],
            )

            mock_project_rest.assert_called()
        assert PROJECTS in result
        assert len(result[PROJECTS]) == 0

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from collections.abc import Sequence
from unittest.mock import patch

import pytest

from active_learning.entities import ActiveLearningProjectConfig, ActiveLearningTaskConfig, ActiveScore, TaskActiveScore
from active_learning.entities.active_manager import PipelineActiveManager, TaskActiveManager
from active_learning.interactors import ActiveMapper
from active_learning.storage.repos import ActiveScoreRepo, ActiveSuggestionRepo

from geti_types import ID, MediaIdentifierEntity


def do_nothing(*args, **kwargs):
    pass


@pytest.fixture
def fxt_active_score(fxt_ote_id, fxt_media_identifier):
    task_score_1 = TaskActiveScore(
        model_id=fxt_ote_id(1),
        score=0.1,
        extractors_scores={"extr_1": 0.2, "extr_2": 0.4},
    )
    task_score_2 = TaskActiveScore(
        model_id=fxt_ote_id(2),
        score=0.9,
        extractors_scores={"extr_1": 0.4, "extr_2": 0.6},
    )
    active_score = ActiveScore(
        media_identifier=fxt_media_identifier,
        pipeline_score=0.7,
        tasks_scores={
            fxt_ote_id(3): task_score_1,
            fxt_ote_id(4): task_score_2,
        },
    )
    yield active_score


@pytest.fixture
def fxt_active_score_factory(fxt_ote_id, fxt_media_identifier_factory):
    def _build_active_score(
        index: int,
        score: float = 1.0,
        task_node_id: ID | None = None,
        task_score: float = 0.1,
        model_ids: Sequence[ID] | None = None,
        media_identifier: MediaIdentifierEntity | None = None,
    ) -> ActiveScore:
        if model_ids is None:
            model_ids = [fxt_ote_id(101), fxt_ote_id(102)]
        if task_node_id is not None:
            task_active_score = TaskActiveScore(
                model_id=model_ids[0],
                score=task_score,
                extractors_scores={"extr_1": 0.2, "extr_2": 0.4},
            )
            tasks_scores = {task_node_id: task_active_score}
        else:
            task_active_score_1 = TaskActiveScore(
                model_id=model_ids[0],
                score=0.1,
                extractors_scores={"extr_1": 0.2, "extr_2": 0.4},
            )
            task_active_score_2 = TaskActiveScore(
                model_id=model_ids[-1],
                score=0.9,
                extractors_scores={"extr_1": 0.4, "extr_2": 0.6},
            )
            tasks_scores = {
                fxt_ote_id(201): task_active_score_1,
                fxt_ote_id(202): task_active_score_2,
            }
        if media_identifier is None:
            media_identifier = fxt_media_identifier_factory(index)
        return ActiveScore(
            media_identifier=media_identifier,
            pipeline_score=score,
            tasks_scores=tasks_scores,
        )

    return _build_active_score


@pytest.fixture
def fxt_task_active_manager(fxt_db_project_service):
    fxt_db_project_service.create_empty_project()
    project = fxt_db_project_service.project
    dataset_storage = fxt_db_project_service.dataset_storage
    model_storage = fxt_db_project_service.model_storage_1
    task_node = fxt_db_project_service.task_node_1
    with (
        patch.object(ActiveSuggestionRepo, "__init__", new=do_nothing),
        patch.object(ActiveScoreRepo, "__init__", new=do_nothing),
        patch.object(TaskActiveManager, "get_dataset_storage", return_value=dataset_storage),
        patch.object(TaskActiveManager, "get_model_storage", return_value=model_storage),
        patch.object(TaskActiveManager, "get_configuration", return_value=ActiveLearningTaskConfig()),
    ):
        task_active_manager = TaskActiveManager(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
            task_id=task_node.id_,
        )
        # load the caches
        task_active_manager.get_configuration()
        task_active_manager.get_dataset_storage()
        task_active_manager.get_model_storage(model_storage_id=model_storage.id_)
        yield task_active_manager


@pytest.fixture
def fxt_pipeline_active_manager(fxt_db_project_service):
    fxt_db_project_service.create_annotated_detection_classification_project()
    project = fxt_db_project_service.project
    dataset_storage = fxt_db_project_service.dataset_storage
    with (
        patch.object(ActiveSuggestionRepo, "__init__", new=do_nothing),
        patch.object(ActiveScoreRepo, "__init__", new=do_nothing),
        patch.object(PipelineActiveManager, "get_dataset_storage", return_value=dataset_storage),
        patch.object(
            PipelineActiveManager,
            "get_configuration",
            return_value=ActiveLearningProjectConfig(),
        ),
    ):
        pipeline_active_manager = PipelineActiveManager(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
        )
        # load the caches
        pipeline_active_manager.get_configuration()
        pipeline_active_manager.get_dataset_storage()
        yield pipeline_active_manager


@pytest.fixture
def fxt_active_mapper(fxt_pipeline_active_manager):
    with patch.object(ActiveMapper, "_get_active_manager", return_value=fxt_pipeline_active_manager):
        yield ActiveMapper(num_workers=2)
    ActiveMapper._instances = {}

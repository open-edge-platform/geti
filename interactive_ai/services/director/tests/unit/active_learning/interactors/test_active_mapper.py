# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from concurrent.futures import ALL_COMPLETED, wait
from copy import deepcopy
from unittest.mock import ANY, call, patch

import numpy as np

from active_learning.entities.active_manager import PipelineActiveManager
from active_learning.interactors import ActiveMapper

from iai_core.entities.metadata import FloatMetadata
from iai_core.entities.tensor import Tensor
from iai_core.repos import MetadataRepo


def do_nothing(*args, **kwargs):
    pass


class TestActiveMapper:
    def test_init_active_scores(
        self,
        fxt_active_mapper,
        fxt_pipeline_active_manager,
        fxt_ote_id,
        fxt_media_identifier_factory,
    ) -> None:
        active_mapper: ActiveMapper = fxt_active_mapper
        workspace_id = fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        media_identifiers = tuple(fxt_media_identifier_factory(i) for i in range(2))
        with patch.object(fxt_pipeline_active_manager, "init_scores", return_value=None) as mock_init_scores:
            active_mapper.init_active_scores(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                media_identifiers=media_identifiers,
            )

        mock_init_scores.assert_called_once_with(media_identifiers=media_identifiers)

    def test_init_active_scores_async(self, fxt_active_mapper, fxt_ote_id, fxt_media_identifier_factory) -> None:
        active_mapper: ActiveMapper = fxt_active_mapper
        workspace_id = fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        media_identifiers = tuple(fxt_media_identifier_factory(i) for i in range(2))
        with patch.object(ActiveMapper, "init_active_scores") as mock_init_scores:
            # submit 3 concurrent requests
            futures = [
                active_mapper.init_active_scores_async(
                    workspace_id=workspace_id,
                    project_id=project_id,
                    dataset_storage_id=dataset_storage_id,
                    media_identifiers=media_identifiers,
                )
                for _ in range(3)
            ]
            wait(futures, timeout=1, return_when=ALL_COMPLETED)

        assert mock_init_scores.call_count == 3

    def test_update_active_scores(
        self,
        fxt_active_mapper,
        fxt_project,
        fxt_dataset_storage,
        fxt_dataset,
        fxt_model_storage,
        fxt_model,
        fxt_active_score,
        fxt_media_identifier,
        fxt_ote_id,
    ) -> None:
        active_mapper: ActiveMapper = fxt_active_mapper
        workspace_id = fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        task_node_id = fxt_ote_id(4)
        unannotated_dataset_with_predictions = deepcopy(fxt_dataset)
        train_dataset_with_predictions = deepcopy(fxt_dataset)
        train_dataset_with_predictions.id_ = fxt_ote_id(5)
        unseen_features = np.random.rand(len(unannotated_dataset_with_predictions))
        seen_features = np.random.rand(len(train_dataset_with_predictions))
        annotated_dataset = fxt_dataset
        model = fxt_model

        with (
            patch.object(ActiveMapper, "_load_model", return_value=fxt_model) as mock_load_model,
            patch.object(
                ActiveMapper,
                "_load_unseen_datasets_and_metadata",
                return_value=(unannotated_dataset_with_predictions, unseen_features),
            ) as mock_load_unseen_data,
            patch.object(
                ActiveMapper,
                "_load_seen_datasets_and_metadata",
                return_value=(
                    annotated_dataset,
                    train_dataset_with_predictions,
                    seen_features,
                ),
            ) as mock_load_seen_data,
            patch.object(
                PipelineActiveManager,
                "get_scores_by_media_identifiers",
                return_value={fxt_media_identifier: fxt_active_score},
            ) as mock_get_scores_by_media,
            patch.object(PipelineActiveManager, "update_scores") as mock_update_scores,
            patch.object(ActiveMapper, "delete_active_learning_metadata_by_dataset_storage") as mock_delete_al_metadata,
        ):
            active_mapper.update_active_scores(
                workspace_id=workspace_id,
                project_id=project_id,
                task_node_id=task_node_id,
                dataset_storage_id=dataset_storage_id,
                model_storage_id=model.model_storage.id_,
                model_id=model.id_,
                annotated_dataset_id=annotated_dataset.id_,
                train_dataset_with_predictions_id=train_dataset_with_predictions.id_,
                unannotated_dataset_with_predictions_id=unannotated_dataset_with_predictions.id_,
            )

        mock_load_model.assert_called_once_with(
            project_identifier=ANY,
            model_storage_id=model.model_storage.id_,
            model_id=model.id_,
        )
        mock_load_unseen_data.assert_called_once_with(
            dataset_storage_identifier=ANY,
            unannotated_dataset_with_predictions_id=unannotated_dataset_with_predictions.id_,
        )
        mock_load_seen_data.assert_called_once_with(
            dataset_storage_identifier=ANY,
            annotated_dataset_id=annotated_dataset.id_,
            train_dataset_with_predictions_id=train_dataset_with_predictions.id_,
        )
        mock_get_scores_by_media.assert_called_once_with(
            media_identifiers={item.media_identifier for item in unannotated_dataset_with_predictions}
        )
        mock_update_scores.assert_called_once_with(
            scores=ANY,
            unseen_dataset_with_predictions_by_task={task_node_id: unannotated_dataset_with_predictions},
            seen_dataset_items_with_predictions_by_task={task_node_id: train_dataset_with_predictions},
            seen_dataset_items_with_annotations_by_task={task_node_id: annotated_dataset},
            unseen_dataset_features_by_task={task_node_id: unseen_features},
            seen_dataset_features_by_task={task_node_id: seen_features},
            model_by_task={task_node_id: model},
            save=True,
        )
        mock_delete_al_metadata.assert_called_once_with(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
        )

    def test_update_active_scores_async(self, fxt_active_mapper, fxt_dataset, fxt_model, fxt_ote_id) -> None:
        active_mapper: ActiveMapper = fxt_active_mapper
        workspace_id = fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        task_node_id = fxt_ote_id(4)
        unannotated_dataset_with_predictions = deepcopy(fxt_dataset)
        train_dataset_with_predictions = deepcopy(fxt_dataset)
        train_dataset_with_predictions.id_ = fxt_ote_id(5)
        annotated_dataset = fxt_dataset
        model = fxt_model

        with patch.object(ActiveMapper, "update_active_scores", return_value=None) as mock_update_active_scores:
            # submit 3 concurrent requests
            futures = [
                active_mapper.update_active_scores_async(
                    workspace_id=workspace_id,
                    project_id=project_id,
                    task_node_id=task_node_id,
                    dataset_storage_id=dataset_storage_id,
                    model_storage_id=model.model_storage.id_,
                    model_id=model.id_,
                    annotated_dataset_id=annotated_dataset.id_,
                    train_dataset_with_predictions_id=train_dataset_with_predictions.id_,
                    unannotated_dataset_with_predictions_id=unannotated_dataset_with_predictions.id_,
                )
                for _ in range(3)
            ]
            wait(futures, timeout=1, return_when=ALL_COMPLETED)

        assert mock_update_active_scores.call_count == 3

    def test_remove_media(self, fxt_active_mapper, fxt_media_identifier_factory, fxt_ote_id) -> None:
        active_mapper: ActiveMapper = fxt_active_mapper
        workspace_id = fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        media_identifiers = tuple(fxt_media_identifier_factory(i) for i in range(2))
        with patch.object(PipelineActiveManager, "remove_media") as mock_remove_media:
            active_mapper.remove_media(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                media_identifiers=media_identifiers,
            )

        mock_remove_media.assert_called_once_with(media_identifiers=media_identifiers)

    def test_remove_media_async(self, fxt_active_mapper, fxt_media_identifier_factory, fxt_ote_id) -> None:
        active_mapper: ActiveMapper = fxt_active_mapper
        workspace_id = fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        media_identifiers = tuple(fxt_media_identifier_factory(i) for i in range(2))
        with patch.object(PipelineActiveManager, "remove_media") as mock_remove_media:
            # submit 3 concurrent requests
            futures = [
                active_mapper.remove_media_async(
                    workspace_id=workspace_id,
                    project_id=project_id,
                    dataset_storage_id=dataset_storage_id,
                    media_identifiers=media_identifiers,
                )
                for _ in range(3)
            ]
            wait(futures, timeout=1, return_when=ALL_COMPLETED)

        assert mock_remove_media.call_count == 3

    def test_delete_all_representation_vectors_by_dataset_storage(self, fxt_active_mapper, fxt_ote_id) -> None:
        active_mapper: ActiveMapper = fxt_active_mapper
        workspace_id = fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        with patch.object(MetadataRepo, "delete_all_by_type") as mock_delete_all:
            active_mapper.delete_active_learning_metadata_by_dataset_storage(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
            )

        mock_delete_all.assert_has_calls(
            calls=[
                call(metadata_type=Tensor),
                call(metadata_type=FloatMetadata),
            ]
        )

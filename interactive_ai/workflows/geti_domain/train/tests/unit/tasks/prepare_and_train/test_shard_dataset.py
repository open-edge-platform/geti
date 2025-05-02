# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module tests commands to create task train dataset"""

from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest
from geti_types import make_session, session_context
from iai_core_py.repos import CompiledDatasetShardsRepo
from iai_core_py.repos.storage.binary_repo import StorageClientFactory
from iai_core_py.repos.storage.storage_client import BinaryObjectType
from media_utils import VideoFrameReader

from job.tasks.prepare_and_train.shard_dataset import shard_dataset_for_train
from job.utils.train_workflow_data import TrainWorkflowData


@pytest.mark.JobsComponent
class TestShardDatasetTasks:
    @pytest.fixture(params=("fxt_dataset_with_images", "fxt_dataset_with_video_frames"))
    def fxt_dataset(self, request):
        fxt_dataset_name = request.param
        return request.getfixturevalue(fxt_dataset_name)

    @pytest.fixture(params=({"organization_id": "good", "workspace_id": "good"},))
    def fxt_session_ctx(self, request):
        session = make_session(
            organization_id=request.param["organization_id"],
            workspace_id=request.param["workspace_id"],
        )
        with session_context(session=session):
            yield session

    @pytest.fixture
    def fxt_mocked_train_data(
        self,
        fxt_project,
        fxt_task_node,
        fxt_label_schema,
        fxt_dataset,
        fxt_train_data,
    ):
        with (
            patch.object(TrainWorkflowData, "get_common_entities") as mocked_get_entities,
            patch.object(TrainWorkflowData, "get_label_schema") as mocked_get_label_schema,
            patch.object(TrainWorkflowData, "get_dataset") as mocked_get_dataset,
        ):
            mocked_get_entities.return_value = fxt_project, fxt_task_node
            mocked_get_label_schema.return_value = fxt_label_schema
            mocked_get_dataset.return_value = fxt_dataset

            yield fxt_train_data()

    def test_shard_dataset(
        self,
        fxt_dataset,
        fxt_mocked_train_data,
        fxt_session_ctx,
    ) -> None:
        # Arrange
        max_shard_size = 2
        progress_callback = MagicMock()
        mock_storage_client = MagicMock()

        img = np.zeros([4, 4, 3], dtype=np.uint8)
        _, np_img_bytes = cv2.imencode(".png", img)
        img_bytes = bytes(np_img_bytes)

        # Act
        with (
            patch.object(
                StorageClientFactory, "acquire_storage_client", return_value=mock_storage_client
            ) as mock_acquire_storage_client,
            patch.object(VideoFrameReader, "get_frame_numpy", return_value=img),
            patch.object(CompiledDatasetShardsRepo, "save") as mock_db,
            patch("jobs_common_extras.datumaro_conversion.sc_extractor.get_image_bytes", return_value=img_bytes),
        ):
            compiled_dataset_shards_id = shard_dataset_for_train(
                train_data=fxt_mocked_train_data,
                dataset=fxt_dataset,
                max_shard_size=max_shard_size,
                progress_callback=progress_callback,
            )

        # Assert
        assert compiled_dataset_shards_id == fxt_dataset.id_

        # Saving compiled dataset shards entity to Mongo db
        mock_db.assert_called_once()

        # Saving shard files to BinaryRepo
        assert mock_storage_client.save_group.call_count >= 1
        project, _ = fxt_mocked_train_data.get_common_entities()

        # Acquire a storage client with the correct organization_id
        mock_acquire_storage_client.assert_called_with(
            identifier=project.identifier,
            object_type=BinaryObjectType.MLFLOW_EXPERIMENTS,
            organization_id=fxt_session_ctx.organization_id,
        )

# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
from unittest.mock import patch

import pytest
from geti_telemetry_tools.metrics.instruments import in_memory_metric_reader
from geti_types import ID
from opentelemetry.sdk.metrics.export import InMemoryMetricReader  # type: ignore
from sc_sdk.repos import ImageRepo, ProjectRepo, VideoRepo

from job.usecases import UpdateMetricsUseCase


@pytest.fixture
def fxt_metric_reader_for_testing() -> InMemoryMetricReader:
    if in_memory_metric_reader is None:
        raise RuntimeError("Test metric reader not initialized")
    return in_memory_metric_reader


@pytest.mark.ProjectIEMsComponent
class TestUpdateMetricsUseCase:
    def test_get_random_objectid_between_dates(
        self, fxt_ote_id, fxt_project_identifier, fxt_metric_reader_for_testing
    ) -> None:
        dataset_storage_id = fxt_ote_id(1)

        class MockProject:
            @property
            def dataset_storage_ids(self) -> list[ID]:
                return [dataset_storage_id]

        class MockImageVideo:
            def __init__(self, height: int, width: int, total_frames: int | None = None) -> None:
                self.height = height
                self.width = width
                if total_frames is not None:
                    self.total_frames = total_frames

        image = MockImageVideo(height=20, width=10)
        video = MockImageVideo(height=30, width=25, total_frames=100)

        original_len = 0
        if original_metrics_data := fxt_metric_reader_for_testing.get_metrics_data():
            try:
                original_metrics = next(
                    sm
                    for sm in original_metrics_data.resource_metrics[0].scope_metrics
                    if sm.scope.name == "geti.telemetry"
                ).metrics
                original_len = len(original_metrics)
            except StopIteration:
                pass

        with (
            patch.object(ProjectRepo, "get_by_id", return_value=MockProject()) as mock_get_by_id,
            patch.object(ImageRepo, "get_all", return_value=[image]) as mock_get_all_images,
            patch.object(VideoRepo, "get_all", return_value=[video]) as mock_get_all_videos,
        ):
            UpdateMetricsUseCase.update_metrics(project_identifier=fxt_project_identifier)

        # Verify the data
        metrics_data = fxt_metric_reader_for_testing.get_metrics_data()
        scope_metrics = next(
            sm for sm in metrics_data.resource_metrics[0].scope_metrics if sm.scope.name == "geti.telemetry"
        ).metrics
        assert len(scope_metrics) == original_len + 3
        names = {m.name for m in scope_metrics[-3:]}
        assert names == {
            "geti.application.media.size.videos.frames",
            "geti.application.media.size.videos.resolution",
            "geti.application.media.size.images.resolution",
        }
        mock_get_by_id.assert_called_once_with(id_=fxt_project_identifier.project_id)
        mock_get_all_images.assert_called_once_with()
        mock_get_all_videos.assert_called_once_with()

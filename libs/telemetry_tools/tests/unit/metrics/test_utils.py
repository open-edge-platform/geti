# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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
import os
from enum import Enum
from unittest.mock import MagicMock, call, patch

from opentelemetry.metrics import CallbackOptions, Observation

from geti_telemetry_tools.metrics.utils import convert_bytes, convert_pixels, if_elected_publisher_for_metric


class DummyTaskType(Enum):
    CLASSIFICATION = "classification"
    DETECTION = "detection"
    SEGMENTATION = "segmentation"
    ANOMALY_DETECTION = "anomaly_detection"


class MockElectionManager:
    stand_for_election = MagicMock()


class TestMetricsUtils:
    def test_if_elected_publisher_for_metric(self) -> None:
        with patch.dict(os.environ, {"HOSTNAME": "test_pod"}):

            @if_elected_publisher_for_metric(
                metric_name="test_metric", validity_in_seconds=10, election_manager_cls=MockElectionManager
            )
            def test_callback(callback_options: CallbackOptions) -> list[Observation]:  # type: ignore
                return [Observation(value=5)]

            MockElectionManager.stand_for_election.return_value = True
            result_1 = test_callback(CallbackOptions())

            MockElectionManager.stand_for_election.return_value = False
            result_2 = test_callback(CallbackOptions())

        MockElectionManager.stand_for_election.assert_has_calls(
            calls=[
                call(subject="test_pod", resource="test_metric", validity_in_seconds=10),
                call(subject="test_pod", resource="test_metric", validity_in_seconds=10),
            ]
        )
        assert result_1 == [Observation(value=5)]
        assert result_2 == []

    def test_convert_bytes(self) -> None:
        test_samples = (
            (1024, "B", 1024),
            (1024, "KB", 1),
            (1_073_741_824, "B", 1_073_741_824),
            (1_073_741_824, "KB", 1_048_576),
            (1_073_741_824, "MB", 1024),
            (1_073_741_824, "GB", 1),
        )

        for num_bytes, unit, expected_output in test_samples:
            output = convert_bytes(num_bytes=num_bytes, unit=unit)
            assert output == expected_output

    def test_convert_pixels(self) -> None:
        test_samples = (
            (1000, "P", 1000),
            (1000, "KP", 1),
            (10**9, "P", 10**9),
            (10**9, "KP", 10**6),
            (10**9, "MP", 1000),
            (10**9, "GP", 1),
        )

        for num_pixels, unit, expected_output in test_samples:
            output = convert_pixels(num_pixels=num_pixels, unit=unit)
            assert output == expected_output

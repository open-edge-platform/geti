# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

import datetime
from unittest.mock import MagicMock, patch

import pytest

from grpc_interfaces.job_update.client import JobUpdateClient
from grpc_interfaces.job_update.pb.job_update_service_pb2 import (
    Empty,
    Error,
    ErrorCode,
    JobUpdateRequest,
    JobUpdateResponse,
)


@pytest.fixture
def fxt_grpc_client():
    client = JobUpdateClient(metadata_getter=lambda: (("key", "value"),))
    client.job_update_service_stub = MagicMock()
    yield client


class TestJobUpdateClient:
    def test_job_update_no_updates(self, fxt_grpc_client) -> None:
        # Arrange
        with patch.object(fxt_grpc_client.job_update_service_stub, "job_update") as mocked_job_update:
            # Act
            fxt_grpc_client.job_update(execution_id="execution_id", metadata=None, cost=None, gpu=None)

        # Assert
        mocked_job_update.assert_not_called()

    def test_job_update(self, fxt_grpc_client) -> None:
        # Arrange
        expected_response = JobUpdateResponse(empty=Empty())
        expected_request = JobUpdateRequest(
            execution_id="execution_id",
            metadata='{"foo": "bar"}',
            cost=JobUpdateRequest.Cost(
                consumed=[
                    JobUpdateRequest.Cost.Consumed(
                        unit="images",
                        amount=100,
                        consuming_date=int(datetime.datetime.now().timestamp()),
                        service="training",
                    )
                ]
            ),
            gpu=JobUpdateRequest.Gpu(action=JobUpdateRequest.Gpu.RELEASE),
        )
        with patch.object(
            fxt_grpc_client.job_update_service_stub,
            "job_update",
            return_value=expected_response,
        ) as mocked_job_update:
            # Act
            fxt_grpc_client.job_update(
                execution_id="execution_id",
                metadata={"foo": "bar"},
                cost=JobUpdateRequest.Cost(
                    consumed=[
                        JobUpdateRequest.Cost.Consumed(
                            unit="images",
                            amount=100,
                            consuming_date=int(datetime.datetime.now().timestamp()),
                            service="training",
                        )
                    ]
                ),
                gpu=JobUpdateRequest.Gpu(action=JobUpdateRequest.Gpu.RELEASE),
            )

        # Assert
        mocked_job_update.assert_called_once_with(expected_request, metadata=(("key", "value"),), wait_for_ready=True)

    def test_job_update_invalid_metadata_update(self, fxt_grpc_client) -> None:
        # Arrange
        expected_response = JobUpdateResponse(error=Error(code=ErrorCode.INVALID_METADATA_UPDATE))
        expected_request = JobUpdateRequest(
            execution_id="execution_id",
            metadata='{"foo": "bar"}',
            cost=JobUpdateRequest.Cost(
                consumed=[
                    JobUpdateRequest.Cost.Consumed(
                        unit="images",
                        amount=100,
                        consuming_date=int(datetime.datetime.now().timestamp()),
                    )
                ]
            ),
            gpu=JobUpdateRequest.Gpu(action=JobUpdateRequest.Gpu.RELEASE),
        )
        with (
            patch.object(
                fxt_grpc_client.job_update_service_stub,
                "job_update",
                return_value=expected_response,
            ) as mocked_job_update,
            pytest.raises(RuntimeError),
        ):
            # Act
            fxt_grpc_client.job_update(
                execution_id="execution_id",
                metadata={"foo": "bar"},
                cost=JobUpdateRequest.Cost(
                    consumed=[
                        JobUpdateRequest.Cost.Consumed(
                            unit="images",
                            amount=100,
                            consuming_date=int(datetime.datetime.now().timestamp()),
                        )
                    ]
                ),
                gpu=JobUpdateRequest.Gpu(action=JobUpdateRequest.Gpu.RELEASE),
            )

        # Assert
        mocked_job_update.assert_called_once_with(expected_request, metadata=(("key", "value"),), wait_for_ready=True)

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

import pytest

from microservice.grpc_api.mappers.proto_mapper import JobToProto

from sc_sdk.utils.time_utils import now


class TestProtoMapper:
    def test_job_to_proto_forward(self, fxt_job, fxt_job_response) -> None:
        forward_result = JobToProto.forward(fxt_job)
        assert forward_result == fxt_job_response

    def test_job_to_proto_forward_non_serializable_payload(self, fxt_job) -> None:
        fxt_job.payload = {"datetime_object": now()}
        expected_error_msg = f"Unable to serialize job payload for job with ID `{str(fxt_job.id)}`."

        with pytest.raises(ValueError, match=expected_error_msg):
            JobToProto.forward(fxt_job)

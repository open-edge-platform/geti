# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from microservice.grpc_api.mappers.proto_mapper import JobToProto

from iai_core.utils.time_utils import now


class TestProtoMapper:
    def test_job_to_proto_forward(self, fxt_job, fxt_job_response) -> None:
        forward_result = JobToProto.forward(fxt_job)
        assert forward_result == fxt_job_response

    def test_job_to_proto_forward_non_serializable_payload(self, fxt_job) -> None:
        fxt_job.payload = {"datetime_object": now()}
        expected_error_msg = f"Unable to serialize job payload for job with ID `{str(fxt_job.id)}`."

        with pytest.raises(ValueError, match=expected_error_msg):
            JobToProto.forward(fxt_job)

# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

from retry.api import retry_call  # type: ignore[import-untyped]

from resource_management.resource_utils import health_check


class TestResourceUtils:
    def test_health_check(self):
        """
        <b>Description:</b>
        To check that the health check system works.

        <b>Input data:</b>
        health check function from resource ms utils

        <b>Expected results:</b>
        Test passes if it completes successfully.

        <b>Steps</b>
        1. Run the health check multiple times
           It may not work for the first few seconds, because the director takes some time
           to connect to Kafka.
        """

        retry_call(
            health_check,
            fkwargs={"mongodb_check": True, "kafka_check": True},
            tries=10,
            delay=1,
        )

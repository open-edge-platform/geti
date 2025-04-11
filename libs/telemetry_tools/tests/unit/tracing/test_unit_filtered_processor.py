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

from unittest.mock import MagicMock, patch

from opentelemetry.sdk.trace import ReadableSpan

from geti_telemetry_tools.tracing.export.processor import FilteredBatchSpanProcessor


class TestUnitFilteredBatchSpanProcessor:
    def test_on_end_blacklisted(self) -> None:
        """Test that span with blacklisted name is not added to a send queue by processor."""
        span_exporter = MagicMock()
        with patch("opentelemetry.sdk.trace.export.BatchSpanProcessor.on_end") as mocked_on_end:
            processor = FilteredBatchSpanProcessor(span_exporter=span_exporter, do_not_send_spans=["foo", "bar"])
            processor.on_end(ReadableSpan(name="foo"))
            processor.on_end(ReadableSpan(name="bar"))

            mocked_on_end.assert_not_called()

    def test_on_end_not_blacklisted(self) -> None:
        """Test that span with not blacklisted name is added to a send queue by processor."""
        span_exporter = MagicMock()
        with patch("opentelemetry.sdk.trace.export.BatchSpanProcessor.on_end") as mocked_on_end:
            processor = FilteredBatchSpanProcessor(span_exporter=span_exporter, do_not_send_spans=["foo", "bar"])
            span = ReadableSpan(name="baz")
            processor.on_end(span)

            mocked_on_end.assert_called_once_with(span)

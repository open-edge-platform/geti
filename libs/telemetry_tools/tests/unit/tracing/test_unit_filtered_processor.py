# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

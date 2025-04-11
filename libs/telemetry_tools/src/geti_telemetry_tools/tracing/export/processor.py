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

"""Batch spans processor supporting spans filtering by name"""

import logging
from collections.abc import Sequence

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter

logger = logging.getLogger(__name__)


class FilteredBatchSpanProcessor(BatchSpanProcessor):
    def __init__(
        self,
        span_exporter: SpanExporter,
        max_queue_size: int | None = None,
        schedule_delay_millis: float | None = None,
        max_export_batch_size: int | None = None,
        export_timeout_millis: float | None = None,
        do_not_send_spans: Sequence[str] | None = None,
    ) -> None:
        super().__init__(
            span_exporter=span_exporter,
            max_queue_size=max_queue_size,
            schedule_delay_millis=schedule_delay_millis,
            max_export_batch_size=max_export_batch_size,
            export_timeout_millis=export_timeout_millis,
        )

        self.do_not_send_spans = set(do_not_send_spans) if do_not_send_spans else set()
        if len(self.do_not_send_spans) > 0:
            logger.info(f"Ignoring spans with a name that begins with any of the following: {self.do_not_send_spans}")

    def on_end(self, span: ReadableSpan) -> None:
        if any(span.name.startswith(ptn) for ptn in self.do_not_send_spans if ptn):
            logger.debug(f"Span {span.name} is blacklisted, not sending")
            return
        super().on_end(span)

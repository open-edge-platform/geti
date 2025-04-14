# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Test utilities to process tracing headers in various formats"""

import re

# traceparent HTTP header format: {version}-{trace_id}-{span_id}-{trace_flags}
traceparent_regex = re.compile(r"00-[0-9a-fA-F]{32}-[0-9a-fA-F]{16}-[0-9a-fA-F]{2}")

# B3 HTTP headers format:
#  - X-B3-TraceId
#  - X-B3-SpanId
#  - X-B3-ParentSpanId (optional)
#  - X-B3-Sampled (optional)
x_b3_traceid_regex = re.compile(r"[0-9a-fA-F]{16}([0-9a-fA-F]{16})?")
x_b3_spanid_regex = re.compile(r"[0-9a-fA-F]{16}")
x_b3_sampled_regex = re.compile(r"[0-9a-fA-F]")

# Jaeger uber-trace-id HTTP header format:
# {trace_id}:{span_id}:{parent_span_id}:{flags}
uber_traceid_regex = re.compile(r"[0-9a-fA-F]{1,32}:[0-9a-fA-F]{1,16}:[0-9a-fA-F]{1,16}:[0-9a-fA-F]{1,2}")

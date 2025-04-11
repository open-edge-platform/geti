# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

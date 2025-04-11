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
import pytest

from usecases.query_builder import QueryResults


@pytest.fixture
def fxt_empty_query_results(fxt_dataset_filter) -> QueryResults:
    return QueryResults(
        media_query_results=[],
        skip=fxt_dataset_filter.skip + fxt_dataset_filter.limit,
        matching_images_count=0,
        matching_videos_count=0,
        matching_video_frames_count=0,
        total_images_count=0,
        total_videos_count=0,
    )

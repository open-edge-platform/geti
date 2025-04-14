# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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

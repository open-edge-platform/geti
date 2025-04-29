# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


import pytest
from testfixtures import compare

from communication.rest_views.media_identifier_rest_views import MediaIdentifierRESTViews


class TestSCMediaIdentifierRESTViews:
    @pytest.mark.parametrize(
        "lazyfxt_media_identifier, lazyfxt_media_identifier_rest",
        [
            ("fxt_image_identifier_1", "fxt_image_identifier_rest"),
            ("fxt_video_identifier", "fxt_video_identifier_rest"),
            ("fxt_video_frame_identifier", "fxt_video_frame_identifier_rest"),
        ],
    )
    def test_media_identifier_to_rest(self, lazyfxt_media_identifier, lazyfxt_media_identifier_rest, request):
        media_identifier_obj = request.getfixturevalue(lazyfxt_media_identifier)
        media_identifier_rest = request.getfixturevalue(lazyfxt_media_identifier_rest)

        result = MediaIdentifierRESTViews.media_identifier_to_rest(media_identifier=media_identifier_obj)

        compare(result, media_identifier_rest, ignore_eq=True)

    @pytest.mark.parametrize(
        "lazyfxt_media_identifier, lazyfxt_media_identifier_rest",
        [
            ("fxt_image_identifier_1", "fxt_image_identifier_rest"),
            ("fxt_video_identifier", "fxt_video_identifier_rest"),
            ("fxt_video_frame_identifier", "fxt_video_frame_identifier_rest"),
        ],
    )
    def test_media_identifier_from_rest(self, lazyfxt_media_identifier, lazyfxt_media_identifier_rest, request):
        media_identifier_obj = request.getfixturevalue(lazyfxt_media_identifier)
        media_identifier_rest = request.getfixturevalue(lazyfxt_media_identifier_rest)

        result = MediaIdentifierRESTViews.media_identifier_from_rest(data=media_identifier_rest)

        compare(result, media_identifier_obj, ignore_eq=True)

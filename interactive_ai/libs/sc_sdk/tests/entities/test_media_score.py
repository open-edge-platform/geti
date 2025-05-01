"""This module tests the MediaScore class"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from copy import deepcopy

from sc_sdk.entities.media_score import NullMediaScore


class TestMediaScore:
    def test_media_score_equality(self, fxt_media_score, fxt_ote_id) -> None:
        """
        <b>Description:</b>
        Check that MediaScore equality works correctly

        <b>Input data:</b>
        MediaScore instances

        <b>Expected results:</b>
        == and != operations work correctly for various inputs

        <b>Steps</b>
        1. Test MediaScore equality
        2. Test NullMediaScore equality
        """
        copied_media_score = deepcopy(fxt_media_score)

        second_media_score = deepcopy(fxt_media_score)
        second_media_score.id_ = fxt_ote_id(0)

        assert fxt_media_score == copied_media_score
        assert fxt_media_score != second_media_score
        assert NullMediaScore() != fxt_media_score
        assert fxt_media_score != NullMediaScore()
        assert NullMediaScore() == NullMediaScore()

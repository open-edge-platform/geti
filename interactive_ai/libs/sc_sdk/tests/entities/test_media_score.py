"""This module tests the MediaScore class"""

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
from copy import deepcopy

import pytest

from sc_sdk.entities.media_score import NullMediaScore


@pytest.mark.ScSdkComponent
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

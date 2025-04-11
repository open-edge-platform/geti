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
import copy

import pytest

from active_learning.entities import ActiveSuggestion


@pytest.fixture
def fxt_active_suggestion(fxt_ote_id, fxt_media_identifier):
    active_suggestion = ActiveSuggestion(
        id_=fxt_ote_id(1),
        media_identifier=fxt_media_identifier,
        score=0.7,
        models=[fxt_ote_id(2), fxt_ote_id(3)],
        user="user_1",
        reason="reason_1",
    )
    yield active_suggestion


class TestActiveSuggestion:
    def test_init(self, fxt_ote_id, fxt_active_suggestion, fxt_media_identifier) -> None:
        active_suggestion: ActiveSuggestion = fxt_active_suggestion
        models_ids = [fxt_ote_id(2), fxt_ote_id(3)]

        assert active_suggestion.id_ == fxt_ote_id(1)
        assert active_suggestion.media_identifier == fxt_media_identifier
        assert active_suggestion.score == 0.7
        assert active_suggestion.models == models_ids
        assert active_suggestion.user == "user_1"
        assert active_suggestion.reason == "reason_1"

    def test_eq(self, fxt_ote_id, fxt_active_suggestion, fxt_media_identifier_2) -> None:
        active_suggestion: ActiveSuggestion = fxt_active_suggestion

        # Test equality
        active_suggestion_copy = copy.deepcopy(active_suggestion)
        assert active_suggestion == active_suggestion_copy
        attr_new_values = {
            "media_identifier": fxt_media_identifier_2,
            "score": 0.99,
            "models": [],
            "user": "user_2",
            "reason": "reason_2",
        }
        for attr, new_value in attr_new_values.items():
            active_suggestion_copy = copy.deepcopy(active_suggestion)
            setattr(active_suggestion_copy, attr, new_value)
            assert active_suggestion_copy == active_suggestion

        # Test inequality
        active_suggestion_copy = copy.deepcopy(active_suggestion)
        active_suggestion_copy.id_ = fxt_ote_id(1234)
        assert active_suggestion_copy != active_suggestion

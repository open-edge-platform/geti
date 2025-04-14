# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from testfixtures import compare

from services.rest_views.scored_label_rest_views import ScoredLabelRESTViews


class TestSCScoredLabelRESTViews:
    def test_scored_label_to_rest(self, fxt_scored_label, fxt_scored_label_rest):
        result = ScoredLabelRESTViews.scored_label_to_rest(scored_label=fxt_scored_label)
        compare(result, fxt_scored_label_rest, ignore_eq=True)

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from testfixtures import compare

from communication.rest_views.scored_label_rest_views import ScoredLabelRESTViews


class TestSCScoredLabelRESTViews:
    def test_scored_label_to_rest(self, fxt_scored_label, fxt_scored_label_rest):
        result = ScoredLabelRESTViews.scored_label_to_rest(scored_label=fxt_scored_label)
        compare(result, fxt_scored_label_rest, ignore_eq=True)

    def test_scored_label_from_rest(
        self,
        fxt_label,
        fxt_scored_label,
        fxt_scored_label_rest,
        fxt_label_source,
    ):
        fxt_scored_label.probability = 1.0
        fxt_scored_label_rest["probability"] = 1.0

        result = ScoredLabelRESTViews.scored_label_from_rest(
            scored_label_data=fxt_scored_label_rest,
            label=fxt_label,
        )

        fxt_scored_label.label_source = fxt_label_source
        compare(result, fxt_scored_label, ignore_eq=True)

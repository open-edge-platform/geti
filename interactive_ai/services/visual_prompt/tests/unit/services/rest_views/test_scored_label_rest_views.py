# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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
from testfixtures import compare

from services.rest_views.scored_label_rest_views import ScoredLabelRESTViews


class TestSCScoredLabelRESTViews:
    def test_scored_label_to_rest(self, fxt_scored_label, fxt_scored_label_rest):
        result = ScoredLabelRESTViews.scored_label_to_rest(scored_label=fxt_scored_label)
        compare(result, fxt_scored_label_rest, ignore_eq=True)

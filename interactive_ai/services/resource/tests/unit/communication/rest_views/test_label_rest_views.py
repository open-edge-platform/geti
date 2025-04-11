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
from unittest.mock import patch

from testfixtures import compare

from communication.rest_views.label_rest_views import LabelRESTViews

from sc_sdk.entities.label_schema import LabelSchema


class TestSCLabelRESTViews:
    def test_label_to_rest(self, fxt_label, fxt_label_rest, fxt_mongo_id):
        with (
            patch.object(LabelSchema, "get_group_containing_label", return_value=None) as mock_get_group,
            patch.object(LabelSchema, "get_parent", return_value=None) as mock_get_parent,
        ):
            result = LabelRESTViews.label_to_rest(
                label=fxt_label,
                label_schema=LabelSchema(id_=fxt_mongo_id(1)),
            )

            mock_get_group.assert_called_once_with(fxt_label)
            mock_get_parent.assert_called_once_with(fxt_label)
        compare(result, fxt_label_rest, ignore_eq=True)

    def test_label_from_rest(self, fxt_label, fxt_label_rest):
        result = LabelRESTViews.label_from_rest(label_dict=fxt_label_rest, domain=fxt_label.domain)
        compare(result, fxt_label)

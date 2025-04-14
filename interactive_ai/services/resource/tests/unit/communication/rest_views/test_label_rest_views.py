# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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

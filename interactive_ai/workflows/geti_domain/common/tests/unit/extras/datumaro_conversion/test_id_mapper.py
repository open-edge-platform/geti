# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.
from unittest.mock import MagicMock

import pytest

from jobs_common_extras.datumaro_conversion.mappers.id_mapper import MediaNameIDMapper


@pytest.mark.CommonComponent
class TestIDMapper:
    def test_media_name_id_mapper(self):
        mapper = MediaNameIDMapper()

        # item.id_: [item_0, ..., item_5]
        # item.media.name: [a,a,a,a,a,b]
        mock_items = [MagicMock() for _ in range(6)]
        for idx, item in enumerate(mock_items):
            item.id_ = f"item_{idx}"
            if idx < 5:
                item.media.name = "a"
            else:
                item.media.name = "b"

        item_names = []
        for item in mock_items:
            item_names.append(mapper.forward(item))

        assert len(item_names) == len(mock_items)
        assert len(item_names) == len(set(item_names))

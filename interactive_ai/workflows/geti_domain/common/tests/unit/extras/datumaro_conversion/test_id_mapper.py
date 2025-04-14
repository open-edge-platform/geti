# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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

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

import pytest
from geti_types import ID


@pytest.fixture
def fxt_mongo_id():
    """
    Create a realistic MongoDB ID string for testing purposes.

    If you need multiple ones, call this fixture repeatedly with different arguments.
    """
    base_id: int = 0x60D31793D5F1FB7E6E3C1A4F

    def _build_id(offset: int = 0) -> str:
        return str(hex(base_id + offset))[2:]

    yield _build_id


@pytest.fixture
def fxt_ote_id(fxt_mongo_id):
    """
    Create a realistic OTE ID for testing purposes. Based on the fxt_mongo_id, but this
    fixture returns an actual ID entity instead of a string.
    """

    def _build_ote_id(offset: int = 0) -> ID:
        return ID(fxt_mongo_id(offset))

    yield _build_ote_id

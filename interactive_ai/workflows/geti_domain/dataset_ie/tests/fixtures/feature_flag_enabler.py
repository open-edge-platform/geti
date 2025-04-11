# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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
import os

import pytest


@pytest.fixture
def fxt_enable_feature_flag_name(request):
    """
    Yields a function to enable a feature, a finalizer is added to reset the feature
    flag to its previous state.
    """

    def _enable_feature(feature_str: str):
        value = os.environ.get(feature_str)
        os.environ[feature_str] = "true"

        def cleanup():
            nonlocal value
            if value:
                os.environ[feature_str] = value
            else:
                del os.environ[feature_str]

        request.addfinalizer(cleanup)

    yield _enable_feature

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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

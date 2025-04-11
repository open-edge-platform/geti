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
import pytest

from geti_types import ID
from sc_sdk.entities.annotation_template import AnnotationTemplate


@pytest.fixture
def fxt_annotation_template_1():
    yield AnnotationTemplate(
        id_=ID("test_id_1"),
        name="test_name_1",
        value="test_value_1",
    )


@pytest.fixture
def fxt_annotation_template_2():
    yield AnnotationTemplate(
        id_=ID("test_id_2"),
        name="test_name_2",
        value="test_value_2",
    )


@pytest.fixture
def fxt_annotation_template_1_mapped():
    yield {
        "id": "test_id_1",
        "name": "test_name_1",
        "value": "test_value_1",
    }


@pytest.fixture
def fxt_annotation_template_2_mapped():
    yield {
        "id": "test_id_2",
        "name": "test_name_2",
        "value": "test_value_2",
    }

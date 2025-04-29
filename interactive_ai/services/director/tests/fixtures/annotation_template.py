# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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

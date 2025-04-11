# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
from bson import ObjectId

from usecases.dataset_filter import DatasetFilter


@pytest.fixture
def fxt_dataset_filter_dict(fxt_mongo_id):
    return {
        "condition": "and",
        "rules": [
            {
                "field": "label_id",
                "operator": "in",
                "value": [str(fxt_mongo_id(1)), str(fxt_mongo_id(2))],
            },
            {
                "field": "media_width",
                "operator": "greater",
                "value": 10,
            },
        ],
    }


@pytest.fixture
def fxt_dataset_filter(fxt_dataset_filter_dict):
    return DatasetFilter.from_dict(query=fxt_dataset_filter_dict, limit=100)


@pytest.fixture
def fxt_dataset_filter_match_dict(fxt_mongo_id):
    return {
        "$match": {
            "$and": [
                {
                    "label_ids": {
                        "$exists": True,
                        "$in": [
                            ObjectId(str(fxt_mongo_id(1))),
                            ObjectId(str(fxt_mongo_id(2))),
                        ],
                    }
                },
                {"media_width": {"$exists": True, "$gt": 10}},
            ]
        }
    }


@pytest.fixture
def fxt_media_filter():
    return {
        "condition": "and",
        "rules": [
            {
                "field": "media_width",
                "operator": "greater",
                "value": 0,
            },
        ],
    }


@pytest.fixture
def fxt_annotation_filter():
    return {
        "condition": "and",
        "rules": [
            {
                "field": "annotation_creation_date",
                "operator": "greater",
                "value": "2022-03-08 11:10:58.625000+00:00",
            },
        ],
    }


@pytest.fixture
def fxt_annotation_and_media_filter():
    return {
        "condition": "and",
        "rules": [
            {
                "field": "media_upload_date",
                "operator": "greater",
                "value": "2022-03-08 11:10:58.625000+00:00",
            },
            {
                "field": "annotation_creation_date",
                "operator": "greater",
                "value": "2022-03-08 11:10:58.625000+00:00",
            },
        ],
    }


@pytest.fixture
def fxt_annotation_scene_state_filter():
    return {
        "condition": "and",
        "rules": [
            {
                "field": "annotation_scene_state",
                "operator": "in",
                "value": ["ANNOTATED", "PARTIALLY_ANNOTATED", "TO_REVISIT", "NONE"],
            }
        ],
    }


@pytest.fixture
def fxt_annotation_scene_state_rule():
    return {
        "field": "annotation_scene_state",
        "operator": "equal",
        "value": "ANNOTATED",
    }


@pytest.fixture
def fxt_broken_dataset_filter():
    return {
        "condition": "and",
        "rules": [
            {
                "field": "media_width",
                "operator": "startswith",
                "value": 10,
            },
        ],
    }


@pytest.fixture
def fxt_broken_dataset_filter_in_no_sequence():
    return {
        "condition": "and",
        "rules": [
            {
                "field": "annotation_scene_state",
                "operator": "in",
                "value": "ANNOTATED",
            },
        ],
    }


@pytest.fixture
def fxt_valid_media_score_query(fxt_mongo_id):
    return {
        "condition": "and",
        "rules": [
            {
                "field": "label_id",
                "operator": "equal",
                "value": str(fxt_mongo_id()),
            },
            {
                "field": "score",
                "operator": "greater",
                "value": 0.5,
            },
        ],
    }


@pytest.fixture
def fxt_valid_single_media_score_query(fxt_mongo_id):
    return {
        "condition": "and",
        "rules": [
            {
                "field": "label_id",
                "operator": "equal",
                "value": str(fxt_mongo_id()),
            },
        ],
    }


@pytest.fixture
def fxt_invalid_media_score_query(fxt_mongo_id):
    return {
        "condition": "and",
        "rules": [
            {
                "field": "label_id",
                "operator": "greater",
                "value": str(fxt_mongo_id()),
            },
            {
                "field": "score",
                "operator": "greater",
                "value": 0.5,
            },
        ],
    }


@pytest.fixture
def fxt_too_many_rules_media_score_query(fxt_mongo_id):
    return {
        "connection": "and",
        "rules": [
            {
                "field": "label_id",
                "operator": "equal",
                "value": str(fxt_mongo_id()),
            },
            {
                "field": "score",
                "operator": "greater",
                "value": 0.5,
            },
            {
                "field": "media_height",
                "operator": "greater",
                "value": 100,
            },
        ],
    }


@pytest.fixture
def fxt_unsupported_fields_media_score_query(fxt_mongo_id):
    return {
        "connection": "and",
        "rules": [
            {
                "field": "label",
                "operator": "equal",
                "value": str(fxt_mongo_id()),
            },
            {
                "field": "score_value",
                "operator": "greater",
                "value": 0.5,
            },
        ],
    }


@pytest.fixture
def fxt_nested_media_score_query(fxt_mongo_id):
    return {
        "connection": "and",
        "rules": [
            {
                "field": "label_id",
                "operator": "equal",
                "value": str(fxt_mongo_id()),
            },
            {
                "connection": "and",
                "rules": [
                    {
                        "field": "score",
                        "operator": "greater",
                        "value": 0.5,
                    },
                    {
                        "field": "score",
                        "operator": "less_or_equal",
                        "value": 0.9,
                    },
                ],
            },
        ],
    }


@pytest.fixture
def fxt_media_score_match_query():
    return {
        "$match": {
            "$and": [
                {"label_id": {"$eq": ObjectId("60d31793d5f1fb7e6e3c1a4f"), "$exists": True}},
                {"score": {"$exists": True, "$gt": 0.5}},
            ]
        }
    }


@pytest.fixture
def fxt_too_large_int_dataset_filter():
    return {
        "condition": "and",
        "rules": [
            {
                "field": "media_width",
                "operator": "greater",
                "value": 2**64,
            },
        ],
    }


@pytest.fixture
def fxt_contains_filter():
    return {
        "condition": "and",
        "rules": [
            {
                "field": "media_name",
                "operator": "contains",
                "value": "test(1)",
            },
        ],
    }


@pytest.fixture
def fxt_contains_query():
    return {
        "$match": {
            "$and": [
                {
                    "media_name": {
                        "$regex": "test\\(1\\)",
                        "$options": "i",
                    }
                }
            ]
        }
    }

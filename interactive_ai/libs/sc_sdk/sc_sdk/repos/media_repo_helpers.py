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

"""This module contains helpers for the media repo"""

from typing import Any

from sc_sdk.entities.image import Image, NullImage
from sc_sdk.entities.video import NullVideo, Video
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo

from geti_types import ID


def get_paginated_media_aggr_query(
    page_size: int,
    skip_token: ID,
    skip_object: Image | Video,
) -> Any:
    """
    Build a MongoDB aggregation pipeline to fetch media with pagination.

    The query does:
        - exclude elements before the skip object
        - sort the elements
        - limit to page size

    :param page_size: max number of elements to return
    :param skip_token: ID for pagination; only retrieve media with ID > skiptoken
    :param skip_object: object corresponding ot the skiptoken
    """
    match_dict = {}

    if not isinstance(skip_object, NullImage | NullVideo):
        skip_item = skip_object.name
        match_dict = {
            "$or": [
                # after skip item
                {"name": {"$gt": skip_item}},
                # same as skip item, but greater ID
                {
                    "$and": [
                        {"name": {"$eq": skip_item}},
                        {"_id": {"$gt": IDToMongo.forward(skip_token)}},
                    ]
                },
            ]
        }

    return [
        {"$match": match_dict},
        {"$sort": {"name": 1, "_id": 1}},
        {"$limit": page_size},
    ]

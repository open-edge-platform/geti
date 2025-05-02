# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module defines a query generator for a query aggregate to get a page from a list
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from iai_core_py.repos.mappers.mongodb_mappers.id_mapper import IDToMongo

from geti_types import ID


class ProjectSortBy(str, Enum):
    """
    Sort by field to sort projects
    """

    NAME = "name"
    CREATION_DATE = "creation_date"


class SortDirection(str, Enum):
    """
    Sort direction field to sort projects
    """

    ASC = "asc"
    DSC = "dsc"


class ProjectSortDirection(Enum):
    """
    Sort direction field to sort projects
    """

    ASC = 1
    DSC = -1


@dataclass
class ProjectQueryData:
    """
    A wrapper class to wrap query parameters which are often sent around as arguments.

    limit: how many projects to return for the page
    name: filter projects whose name contains the given string
    skip: number of items to skip
    sort_by: field to sort projects by, can be name or creation date
    sort_direction: sort direction to sort projects
    """

    limit: int
    name: str
    skip: int
    sort_by: ProjectSortBy
    sort_direction: ProjectSortDirection
    with_size: bool


def get_permitted_aggregation(
    permitted_projects: Sequence[ID] | None = None,
) -> list[dict[str, Any]]:
    """
    Get a query for permitted projects

    :param permitted_projects: a list of user permitted projects ID's
    :return: aggregate query with pagination
    """
    permitted_filter = get_permitted_filter(permitted_projects)
    if permitted_filter is None:
        return []
    return [{"$match": permitted_filter}]


def get_permitted_filter(
    permitted_projects: Sequence[ID] | None = None,
) -> dict[str, Any] | None:
    """
    Get a filter for permitted projects

    :param permitted_projects: a list of user permitted projects ID's
    :return: filter
    """
    if permitted_projects is None:
        return None
    ids = [IDToMongo.forward(id) for id in permitted_projects]
    return {"_id": {"$in": ids}}

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Parsers to create/update projects from REST representation"""

from .project_parser import RestProjectParser, RestProjectUpdateParser

__all__ = [
    "RestProjectParser",
    "RestProjectUpdateParser",
]

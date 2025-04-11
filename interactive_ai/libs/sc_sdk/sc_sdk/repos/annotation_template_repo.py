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

"""This module implements the MongoDB repos for the Annotation Template entity"""

from collections.abc import Callable

from pymongo import IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from sc_sdk.entities.annotation_template import AnnotationTemplate, NullAnnotationTemplate
from sc_sdk.repos.base import ProjectBasedSessionRepo
from sc_sdk.repos.mappers import CursorIterator
from sc_sdk.repos.mappers.mongodb_mappers.annotation_template_mapper import AnnotationTemplateToMongo

from geti_types import ProjectIdentifier, Session


class AnnotationTemplateRepo(ProjectBasedSessionRepo[AnnotationTemplate]):
    """
    Repository to persist AnnotationTemplate entities in the database.

    :param project_identifier: Identifier of the project
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(self, project_identifier: ProjectIdentifier, session: Session | None = None) -> None:
        super().__init__(
            collection_name="annotation_template",
            project_identifier=project_identifier,
            session=session,
        )

    @property
    def forward_map(self) -> Callable[[AnnotationTemplate], dict]:
        return AnnotationTemplateToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], AnnotationTemplate]:
        return AnnotationTemplateToMongo.backward

    @property
    def null_object(self) -> NullAnnotationTemplate:
        return NullAnnotationTemplate()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor, mapper=AnnotationTemplateToMongo, parameter=None
        )

    @property
    def indexes(self) -> list[IndexModel]:
        return super().indexes

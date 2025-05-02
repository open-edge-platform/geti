# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the MongoDB repos for labels and label schema entities"""

from collections.abc import Callable
from typing import Any, cast

from pymongo import DESCENDING, IndexModel
from pymongo.client_session import ClientSession
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core_py.entities.label import Label, NullLabel
from iai_core_py.entities.label_schema import LabelSchema, LabelSchemaView, NullLabelSchema
from iai_core_py.repos.base import ProjectBasedSessionRepo
from iai_core_py.repos.mappers import CursorIterator, IDToMongo, LabelSchemaToMongo, LabelToMongo
from iai_core_py.utils.type_helpers import SequenceOrSet

from geti_types import ID, ProjectIdentifier, Session


class LabelSchemaRepo(ProjectBasedSessionRepo[LabelSchema]):
    """
    Repository to persist LabelSchema entities in the database.

    :param project_identifier: Identifier of the project
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(self, project_identifier: ProjectIdentifier, session: Session | None = None) -> None:
        super().__init__(
            collection_name="label_schema",
            project_identifier=project_identifier,
            session=session,
        )

    @property
    def forward_map(self) -> Callable[[LabelSchema], dict]:
        return LabelSchemaToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], LabelSchema]:
        return LabelSchemaToMongo.backward

    @property
    def null_object(self) -> NullLabelSchema:
        return NullLabelSchema()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=LabelSchemaToMongo, parameter=None)

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [IndexModel([("task_node_id", DESCENDING)])]
        return super_indexes + new_indexes

    def save(
        self,
        instance: LabelSchema,
        mongodb_session: ClientSession | None = None,
    ) -> None:
        """
        Save a LabelSchema and its labels to the database.

        If a document with the same id already exists, it is overwritten.
        Otherwise, a new document is created.

        :param instance: Object to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        if mongodb_session is not None:
            raise ValueError("LabelSchemaRepo.save() does not support an external ClientSession")

        with self._mongo_client.start_session() as mongodb_session:  # noqa: PLR1704
            # TODO CVS-117126 use a transaction to save labels and schema atomically
            # Save the labels. Here, we loop through each group, then each label
            # in this group to ensure that they are saved in their creation order.
            labels_to_save: list[Label] = [
                cast("Label", label)  # cast from Label to Label
                for group in instance.get_groups(include_empty=True)
                for label in group.labels
            ]
            LabelRepo(self.identifier).save_many(instances=labels_to_save, mongodb_session=mongodb_session)
            # If the object is a view, save the full schema too.
            if isinstance(instance, LabelSchemaView):
                super().save(instance.parent_schema, mongodb_session=mongodb_session)
            # Save the schema
            super().save(instance, mongodb_session=mongodb_session)

    def get_latest(self, include_views: bool = False) -> LabelSchema:
        """
        Fetch the most recent LabelSchema for the project.

        :param include_views: Whether to include LabelSchemaView(s) in the search
        :return: LabelSchema, LabelSchemaView (if views included) or NullLabelSchema (if not found)
        """
        extra_filter: dict[str, Any] = {}
        if not include_views:
            extra_filter["label_schema_class"] = "label_schema"
        return self.get_one(extra_filter=extra_filter, latest=True)

    def get_deleted_label_ids(self) -> tuple[ID, ...]:
        """
        Get the IDs of the labels that were deleted from the project, based on the
        latest label schema for that project.

        :return: Tuple of deleted label ids
        """
        query = {"label_schema_class": "label_schema"}
        label_schema = self.get_one(extra_filter=query, latest=True)
        return label_schema.deleted_label_ids

    def get_latest_view_by_task(
        self,
        task_node_id: ID,
    ) -> LabelSchemaView | NullLabelSchema:
        """
        Fetch the most recent LabelSchemaView from the repository for a given task.

        :param task_node_id: ID of the task node
        :return: LabelSchemaView or NullLabelSchema (if not found)
        """
        query = {
            "task_node_id": IDToMongo.forward(task_node_id),
            "label_schema_class": "label_schema_view",
        }
        return self.get_one(extra_filter=query, latest=True)  # type: ignore


class LabelRepo(ProjectBasedSessionRepo[Label]):
    """
    Repository to persist Label entities in the database.

    :param project_identifier: Identifier of the project
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(self, project_identifier: ProjectIdentifier, session: Session | None = None) -> None:
        super().__init__(
            collection_name="label",
            project_identifier=project_identifier,
            session=session,
        )

    @property
    def forward_map(self) -> Callable[[Label], dict]:
        return LabelToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], Label]:
        return LabelToMongo.backward

    @property
    def null_object(self) -> NullLabel:
        return NullLabel()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=LabelToMongo, parameter=None)

    def get_by_ids(self, label_ids: SequenceOrSet[ID]) -> dict[ID, Label]:
        """
        Fetch multiple labels given their ids.

        :param label_ids: Sequence of Label IDs to fetch from the database
        :return: Dictionary with label.id_ as key and Label as value
        """
        label_ids_filter = {"_id": {"$in": [IDToMongo.forward(_id) for _id in label_ids]}}
        labels = self.get_all(extra_filter=label_ids_filter)
        return {label.id_: label for label in labels}

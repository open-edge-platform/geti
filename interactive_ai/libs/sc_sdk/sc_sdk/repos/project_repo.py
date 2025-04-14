# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the repository for project entities
"""

import datetime
import logging
import re
from collections.abc import Callable
from functools import partial

import pymongo
from pymongo import IndexModel
from pymongo.client_session import ClientSession
from pymongo.collation import Collation, CollationStrength
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from sc_sdk.entities.dataset_storage import NullDatasetStorage
from sc_sdk.entities.project import NullProject, Project
from sc_sdk.entities.project_performance import ProjectPerformance
from sc_sdk.repos.base import SessionBasedRepo
from sc_sdk.repos.base.session_repo import QueryAccessMode
from sc_sdk.repos.dataset_storage_repo import DatasetStorageRepo
from sc_sdk.repos.mappers import DatetimeToMongo, ProjectToMongo
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from sc_sdk.repos.mappers.mongodb_mappers.project_performance_mapper import ProjectPerformanceToMongo
from sc_sdk.repos.project_repo_helpers import ProjectQueryData, get_permitted_aggregation, get_permitted_filter
from sc_sdk.utils.time_utils import now

from geti_types import ID, Session

logger = logging.getLogger(__name__)


class ProjectRepo(SessionBasedRepo[Project]):
    """
    Repository to persist Project entities in the database.

    :param session: Session object; if not provided, it is loaded through get_session()
    """

    collection_name = "project"

    def __init__(self, session: Session | None = None) -> None:
        super().__init__(collection_name=ProjectRepo.collection_name, session=session)

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel([("name", pymongo.DESCENDING)]),
            IndexModel([("dataset_storage_ids", pymongo.DESCENDING)]),
            IndexModel(
                [
                    ("hidden", pymongo.ASCENDING),
                    ("project_type", pymongo.ASCENDING),
                ]
            ),
        ]
        return super_indexes + new_indexes

    @property
    def forward_map(self) -> Callable[[Project], dict]:
        return ProjectToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], Project]:
        return partial(
            ProjectToMongo.backward,
        )

    @property
    def null_object(self) -> Project:
        return NullProject()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=ProjectToMongo,
            parameter=None,
        )

    def save(self, instance: Project, mongodb_session: ClientSession | None = None) -> None:
        """
        Save a project to the database, including:
        - the dataset storages associated with it;

        :param instance: Project entity to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        for dataset_storage in instance.get_dataset_storages():
            if not isinstance(dataset_storage, NullDatasetStorage):
                DatasetStorageRepo(instance.identifier).save(dataset_storage)
        super().save(instance=instance, mongodb_session=mongodb_session)

    def delete_all(self, extra_filter: dict | None = None) -> bool:
        """
        Delete all projects in the database

        :raises: NotImplementedError()
        """
        raise NotImplementedError("Cannot delete all projects yet")

    def get_by_dataset_storage_id(self, dataset_storage_id: ID) -> Project:
        """
        Return the project which includes dataset storage with given id.

        :param dataset_storage_id: dataset storage id
        :return: project containing dataset storage, if found, otherwise NullProject
        """
        query = {"dataset_storage_ids": IDToMongo.forward(dataset_storage_id)}
        return super().get_one(extra_filter=query)

    def _update(
        self,
        query_filter: dict,
        update: dict | list[dict],
        mongodb_session: ClientSession | None = None,
    ) -> bool:
        """
        Updates a project document, doesn't create new document if it's not found by ID

        :param query_filter: query that matches the document to update
        :param update: job document update or a list of updates if aggregation pipeline should be used
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        :return: True if the job document is updated, False otherwise
        """
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        query.update(query_filter)
        result = self._collection.update_one(
            filter=query,
            update=update,
            upsert=False,
            session=mongodb_session,
        )
        return result.modified_count == 1

    def update_project_performance(self, project_id: ID, project_performance: ProjectPerformance) -> None:
        """
        Update the performance attribute of an existing project doc.

        :param project_id: ID of the project to update
        :param project_performance: the new ProjectPerformance of the project
        """
        self._update(
            query_filter={"_id": IDToMongo.forward(project_id)},
            update={"$set": {"performance": ProjectPerformanceToMongo.forward(project_performance)}},
        )

    def mark_locked(
        self, owner: str, project_id: ID, duration_seconds: int, mongodb_session: ClientSession | None = None
    ) -> None:
        """
        Lock a project, typically done when workload is applied to project.
        The project entity can not be deleted or modified while lock is active.

        :param owner: Name of the lock's owner
        :param project_id: ID of the project to lock
        :param duration_seconds: Duration to lock the project in seconds
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        :raises ValueError: If unable to lock the project or attempting to decrease the lock time
        """
        filter_query: dict = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        filter_query["_id"] = IDToMongo.forward(project_id)
        timestamp = now()
        locked_until = timestamp + datetime.timedelta(0, duration_seconds)
        lock_name = f"locked_until.{owner}"
        filter_query["$or"] = [{lock_name: {"$exists": False}}, {lock_name: {"$lte": timestamp}}]
        lock_query = {"$set": {lock_name: DatetimeToMongo.forward(locked_until)}}
        result = self._collection.update_one(
            filter=filter_query,
            update=lock_query,
            upsert=False,
            session=mongodb_session,
        )
        if result.matched_count != 1:
            raise ValueError(
                f"Failed to lock project with ID '{project_id}' and owner `{owner}`. "
                f"It may already be locked or does not exist."
            )

    def mark_unlocked(self, owner: str, project_id: ID, mongodb_session: ClientSession | None = None) -> None:
        """
        Unlock a project, typically done when workload is completed

        :param owner: Name of the lock's owner
        :param project_id: ID of the project to unlock
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        :raises ValueError: if project doesn't exist
        """
        filter_query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        filter_query["_id"] = IDToMongo.forward(project_id)
        unlock_query = {"$unset": {f"locked_until.{owner}": ""}}
        result = self._collection.update_one(
            filter=filter_query,
            update=unlock_query,
            upsert=False,
            session=mongodb_session,
        )
        if result.matched_count != 1:
            raise ValueError(f"Unable to unlock project. No project exist with ID '{project_id}'.")

    def read_lock(self, project_id: ID) -> bool:
        """
        Read the lock of a Project. Will return True if the lock is active,
        returns False if it does not exist or is expired

        :param project_id: ID of the project to read lock for
        :return: True if the project is locked, False otherwise.
        """
        filter_query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        filter_query["_id"] = IDToMongo.forward(project_id)
        doc = self._collection.find_one(filter_query, sort=[("_id", 1)])
        if doc is None:
            raise ValueError(f"Cannot read lock. Project with ID '{project_id}' does not exist.")
        locks = doc.get("locked_until", {})
        if not locks:
            return False
        locked_until = max([DatetimeToMongo.backward(lock) for _, lock in locks.items()])
        return locked_until > now()

    def hide(self, project: Project) -> Project:
        """
        Hide a Project, i.e. mark it as hidden

        :param project: Project
        :return: updated project
        """
        self._update(query_filter={"_id": IDToMongo.forward(project.id_)}, update={"$set": {"hidden": True}})
        project.hidden = True
        return project

    def unhide(self, project: Project) -> Project:
        """
        Make a Project visible, i.e. unmark it as hidden

        :param project: Project
        :return: updated project
        """
        self._update(query_filter={"_id": IDToMongo.forward(project.id_)}, update={"$set": {"hidden": False}})
        project.hidden = False
        return project

    def get_by_page(
        self,
        query_data: ProjectQueryData,
        include_hidden: bool = True,
        permitted_projects: tuple[ID, ...] | None = None,
    ) -> list[Project]:
        """
        Gets the paginated lists of projects stored in the database.

        :param query_data: ProjectQueryData object with request params
        :param include_hidden: Whether to include hidden projects
        :param permitted_projects: A list of user permitted projects ID's
        :return: list of projects within the current page
        """
        if permitted_projects is not None and len(permitted_projects) == 0:
            return []
        aggr_pipeline: list[dict] = []

        match_dict: dict = {}
        # Exclude hidden projects
        if not include_hidden:
            match_dict["hidden"] = {"$eq": False}
        # Filter by name
        if query_data.name:
            escaped_name = re.escape(query_data.name)
            match_dict["name"] = {"$regex": escaped_name, "$options": "i"}
        if match_dict:
            aggr_pipeline.append({"$match": match_dict})

        # Include only allowed projects
        aggr_pipeline.extend(get_permitted_aggregation(permitted_projects))
        # Sort projects
        aggr_pipeline.append(
            {
                "$sort": {
                    query_data.sort_by.value: query_data.sort_direction.value,
                    "_id": -1,  # sort by id to ensure the sort order is consistent if 'sort_by' contains duplicates
                }
            }
        )
        # Skip projects in previous pages
        aggr_pipeline.append(
            {"$skip": query_data.skip},
        )
        # Limit to page size
        aggr_pipeline.append(
            {"$limit": query_data.limit},
        )
        docs = self.aggregate_read(
            pipeline=aggr_pipeline,
            collation=Collation(locale="en", strength=CollationStrength.SECONDARY),
        )
        projects: list[Project] = []
        for doc in docs:
            try:
                projects.append(self.backward_map(doc))
            except Exception:
                logger.exception(f"Error while deserializing project with name `{doc['name']}`.")
        return projects

    def get_names(self, permitted_projects: tuple[ID, ...] | None = None) -> dict[ID, str]:
        """
        Returns projects names.
        If permitted_projects is None, then no authorization check is performed and all projects are queried,
        not only permitted.

        :param permitted_projects: A list of user permitted projects ID's
        :return: all ID's of permitted projects found with their names
        """
        if permitted_projects is not None and len(permitted_projects) == 0:
            return {}
        aggr_pipeline: list[dict] = []

        # Include only allowed projects
        aggr_pipeline.extend(get_permitted_aggregation(permitted_projects))
        # Returns only names
        aggr_pipeline.append({"$project": {"name": 1}})
        docs = self.aggregate_read(
            pipeline=aggr_pipeline,
            collation=Collation(locale="en", strength=CollationStrength.SECONDARY),
        )
        return {IDToMongo.backward(doc["_id"]): doc["name"] for doc in docs}

    def count_all(
        self,
        include_hidden: bool = True,
        permitted_projects: tuple[ID, ...] | None = None,
    ) -> int:
        """
        Counts the number of projects inside the workspace.

        :param include_hidden: Whether to include hidden (not fully created or deleted) projects
        :param permitted_projects: A list of user permitted projects ID's
        :return: number of projects inside the workspace
        """
        if permitted_projects is not None and len(permitted_projects) == 0:
            return 0
        filters = [] if include_hidden else [{"hidden": False}]
        permitted_filter = get_permitted_filter(permitted_projects)
        if permitted_filter is not None:
            filters.extend([permitted_filter])
        query = {"$and": filters} if len(filters) > 0 else {}
        return self.count(extra_filter=query)

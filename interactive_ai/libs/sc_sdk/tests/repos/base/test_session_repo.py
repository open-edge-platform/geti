# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import contextlib
from unittest.mock import patch

import pytest
from pymongo import UpdateOne
from pymongo.results import DeleteResult

from sc_sdk.entities.persistent_entity import PersistentEntity
from sc_sdk.repos.base.session_repo import QueryAccessMode
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo

from geti_types import ID, make_session
from geti_types.session import DEFAULT_ORGANIZATION_ID, DEFAULT_WORKSPACE_ID


class FakeCursor:
    """Object that behaves similarly to pymongo Cursor, for test purposes"""

    def __init__(self, collection) -> None:
        self.__collection = collection
        self.__index = 0

    @property
    def alive(self):
        return True

    def __iter__(self):
        return self

    def __next__(self):
        if self.__index >= len(self.__collection):
            raise StopIteration
        value = self.__collection[self.__index]
        self.__index += 1
        return value

    def next(self):
        return self.__next__()


class TestSessionBasedRepo:
    def test_preliminary_query_match_filter(self, fxt_session_repo) -> None:
        session_on_prem = make_session()
        session_regional = make_session()
        session_cloud = make_session()
        repo_on_prem = fxt_session_repo(session_on_prem)
        repo_regional = fxt_session_repo(session_regional)
        repo_cloud = fxt_session_repo(session_cloud)
        access_mode = QueryAccessMode.WRITE

        filter_on_prem = repo_on_prem.preliminary_query_match_filter(access_mode)
        filter_regional = repo_regional.preliminary_query_match_filter(access_mode)
        filter_cloud = repo_cloud.preliminary_query_match_filter(access_mode)

        assert filter_on_prem == {
            "organization_id": IDToMongo.forward(DEFAULT_ORGANIZATION_ID),
            "workspace_id": IDToMongo.forward(DEFAULT_WORKSPACE_ID),
        }
        assert filter_regional == {
            "organization_id": IDToMongo.forward(DEFAULT_ORGANIZATION_ID),
            "workspace_id": IDToMongo.forward(DEFAULT_WORKSPACE_ID),
        }
        assert filter_cloud == {
            "organization_id": IDToMongo.forward(DEFAULT_ORGANIZATION_ID),
            "workspace_id": IDToMongo.forward(DEFAULT_WORKSPACE_ID),
        }

    def test_preliminary_aggregation_match_stage(self, fxt_session_repo) -> None:
        session_on_prem = make_session()
        session_regional = make_session()
        session_cloud = make_session()
        repo_on_prem = fxt_session_repo(session_on_prem)
        repo_regional = fxt_session_repo(session_regional)
        repo_cloud = fxt_session_repo(session_cloud)
        access_mode = QueryAccessMode.WRITE

        match_stage_on_prem = repo_on_prem.preliminary_aggregation_match_stage(access_mode)
        match_stage_regional = repo_regional.preliminary_aggregation_match_stage(access_mode)
        match_stage_cloud = repo_cloud.preliminary_aggregation_match_stage(access_mode)

        assert match_stage_on_prem == {
            "$match": {
                "organization_id": IDToMongo.forward(DEFAULT_ORGANIZATION_ID),
                "workspace_id": IDToMongo.forward(DEFAULT_WORKSPACE_ID),
            }
        }
        assert match_stage_regional == {
            "$match": {
                "organization_id": IDToMongo.forward(DEFAULT_ORGANIZATION_ID),
                "workspace_id": IDToMongo.forward(DEFAULT_WORKSPACE_ID),
            }
        }
        assert match_stage_cloud == {
            "$match": {
                "organization_id": IDToMongo.forward(DEFAULT_ORGANIZATION_ID),
                "workspace_id": IDToMongo.forward(DEFAULT_WORKSPACE_ID),
            }
        }

    @pytest.mark.parametrize("use_mongodb_session", [False, True], ids=["without session", "with session"])
    def test_save(
        self,
        fxt_session_repo,
        fxt_mappable_object,
        fxt_mapper,
        use_mongodb_session,
    ) -> None:
        session = make_session()
        repo = fxt_session_repo(session)
        if use_mongodb_session:
            mongodb_session_ctx = repo._mongo_client.start_session(causal_consistency=True)
        else:
            mongodb_session_ctx = contextlib.nullcontext()
        instance = fxt_mappable_object(x=3)

        with (
            patch.object(repo, "preliminary_query_match_filter", return_value={}) as mock_match_filter,
            patch.object(repo._collection, "update_one") as mock_update_one,
            patch.object(instance, "mark_as_persisted") as mock_mark_as_persisted,
            mongodb_session_ctx as mongodb_session,
        ):
            repo.save(instance, mongodb_session=mongodb_session)

        mock_match_filter.assert_called_once_with(access_mode=QueryAccessMode.WRITE)
        mock_update_one.assert_called_once_with(
            {"_id": IDToMongo.forward(instance.id_)},
            {"$set": fxt_mapper.forward(instance)},
            upsert=True,
            session=mongodb_session,
        )
        mock_mark_as_persisted.assert_called_once()

    @pytest.mark.parametrize("use_mongodb_session", [False, True], ids=["without session", "with session"])
    def test_save_many(
        self,
        fxt_session_repo,
        fxt_mappable_object,
        fxt_mapper,
        use_mongodb_session,
    ) -> None:
        session = make_session()
        repo = fxt_session_repo(session)
        if use_mongodb_session:
            mongodb_session_ctx = repo._mongo_client.start_session(causal_consistency=True)
        else:
            mongodb_session_ctx = contextlib.nullcontext()
        instance_1 = fxt_mappable_object(x=1, id_=ID("foo1"))
        instance_2 = fxt_mappable_object(x=2, id_=ID("foo2"))
        instance_1_doc = fxt_mapper.forward(instance_1)
        instance_2_doc = fxt_mapper.forward(instance_2)

        with (
            patch.object(repo, "preliminary_query_match_filter", return_value={}) as mock_match_filter,
            patch.object(repo._collection, "bulk_write") as mock_bulk_write,
            patch.object(PersistentEntity, "mark_as_persisted") as mock_mark_as_persisted,
            mongodb_session_ctx as mongodb_session,
        ):
            repo.save_many([instance_1, instance_2], mongodb_session=mongodb_session)

        mock_match_filter.assert_called_once_with(access_mode=QueryAccessMode.WRITE)
        mock_bulk_write.assert_called_once_with(
            [
                UpdateOne({"_id": "foo1"}, {"$set": instance_1_doc}, upsert=True),
                UpdateOne({"_id": "foo2"}, {"$set": instance_2_doc}, upsert=True),
            ],
            session=mongodb_session,
        )
        assert mock_mark_as_persisted.call_count == 2

    def test_get_by_id(self, fxt_session_repo, fxt_mappable_object, fxt_mapper) -> None:
        session = make_session()
        repo = fxt_session_repo(session)
        instance = fxt_mappable_object(x=3)
        instance_doc = fxt_mapper.forward(instance)

        with (
            patch.object(repo, "preliminary_query_match_filter", return_value={}) as mock_match_filter,
            patch.object(repo._collection, "find_one", return_value=instance_doc) as mock_find_one,
        ):
            found_object = repo.get_by_id(instance.id_)

        mock_match_filter.assert_called_once_with(access_mode=QueryAccessMode.READ)
        mock_find_one.assert_called_once_with({"_id": str(instance.id_)})
        assert found_object == instance

    @pytest.mark.parametrize("latest", [False, True], ids=["sort by latest", "no sort"])
    def test_get_one(self, fxt_session_repo, fxt_mappable_object, fxt_mapper, latest) -> None:
        session = make_session()
        repo = fxt_session_repo(session)
        instance = fxt_mappable_object(x=3)
        instance_doc = fxt_mapper.forward(instance)
        extra_filter = {"mykey": "myvalue"}

        with (
            patch.object(repo, "preliminary_query_match_filter", return_value={}) as mock_match_filter,
            patch.object(repo._collection, "find_one", return_value=instance_doc) as mock_find_one,
        ):
            found_object = repo.get_one(extra_filter=extra_filter, latest=latest)

        mock_match_filter.assert_called_once_with(access_mode=QueryAccessMode.READ)
        expected_sort = [("_id", -1)] if latest else None
        mock_find_one.assert_called_once_with(extra_filter, sort=expected_sort)
        assert found_object == instance

    def test_get_all(self, fxt_session_repo, fxt_mappable_object, fxt_mapper) -> None:
        session = make_session()
        repo = fxt_session_repo(session)
        instance_1 = fxt_mappable_object(x=1)
        instance_2 = fxt_mappable_object(x=2)
        instance_1_doc = fxt_mapper.forward(instance_1)
        instance_2_doc = fxt_mapper.forward(instance_2)
        docs = [instance_1_doc, instance_2_doc]
        extra_filter = {"mykey": "myvalue"}

        with (
            patch.object(repo, "preliminary_query_match_filter", return_value={}) as mock_match_filter,
            patch.object(repo._collection, "find", return_value=FakeCursor(docs)) as mock_find,
        ):
            found_objects_cursor = repo.get_all(extra_filter=extra_filter)

        mock_match_filter.assert_called_once_with(access_mode=QueryAccessMode.READ)
        mock_find.assert_called_once_with(extra_filter, sort=None)

        assert isinstance(found_objects_cursor, CursorIterator)
        found_objects = set(found_objects_cursor)
        assert found_objects == {instance_1, instance_2}

    def test_get_all_ids(self, fxt_session_repo, fxt_mappable_object, fxt_mapper) -> None:
        session = make_session()
        repo = fxt_session_repo(session)
        instance_1 = fxt_mappable_object(x=1)
        instance_2 = fxt_mappable_object(x=2)
        id_docs = [
            {"_id": IDToMongo.forward(instance_1.id_)},
            {"_id": IDToMongo.forward(instance_2.id_)},
        ]
        extra_filter = {"mykey": "myvalue"}

        with (
            patch.object(repo, "preliminary_query_match_filter", return_value={}) as mock_match_filter,
            patch.object(repo._collection, "find", return_value=FakeCursor(id_docs)) as mock_find,
        ):
            found_ids = repo.get_all_ids(extra_filter=extra_filter)

        mock_match_filter.assert_called_once_with(access_mode=QueryAccessMode.READ)
        mock_find.assert_called_once_with(extra_filter, projection={"_id": 1})

        found_ids_set = set(found_ids)
        assert found_ids_set == {instance_1.id_, instance_2.id_}

    def test_aggregate_read(self, fxt_session_repo) -> None:
        session = make_session()
        repo = fxt_session_repo(session)
        pipeline = [{"$match": {"k1": "v1"}}]

        with (
            patch.object(
                repo,
                "preliminary_aggregation_match_stage",
                return_value={"$match": {"k2": "v2"}},
            ) as mock_match_stage,
            patch.object(repo._collection, "aggregate", return_value=[1, 2]) as mock_aggregate,
        ):
            result = repo.aggregate_read(pipeline=pipeline)

        mock_match_stage.assert_called_once_with(access_mode=QueryAccessMode.READ)
        expected_full_pipeline = [{"$match": {"k2": "v2"}}, {"$match": {"k1": "v1"}}]
        mock_aggregate.assert_called_once_with(expected_full_pipeline, allowDiskUse=True, collation=None)
        assert result == [1, 2]

    def test_aggregate_write(self, fxt_session_repo) -> None:
        session = make_session()
        repo = fxt_session_repo(session)
        pipeline = [{"$match": {"k1": "v1"}}]

        with (
            patch.object(
                repo,
                "preliminary_aggregation_match_stage",
                return_value={"$match": {"k2": "v2"}},
            ) as mock_match_stage,
            patch.object(repo._collection, "aggregate", return_value=[1, 2]) as mock_aggregate,
        ):
            result = repo.aggregate_write(pipeline=pipeline)

        mock_match_stage.assert_called_once_with(access_mode=QueryAccessMode.WRITE)
        expected_full_pipeline = [{"$match": {"k2": "v2"}}, {"$match": {"k1": "v1"}}]
        mock_aggregate.assert_called_once_with(expected_full_pipeline, allowDiskUse=True, collation=None)
        assert result == [1, 2]

    def test_distinct(self, fxt_session_repo) -> None:
        session = make_session()
        repo = fxt_session_repo(session)

        with (
            patch.object(repo, "preliminary_query_match_filter", return_value={}) as mock_match_filter,
            patch.object(repo._collection, "distinct", return_value=[1, 2]) as mock_distinct,
        ):
            unique_values = repo.distinct(key="x")

        mock_match_filter.assert_called_once_with(access_mode=QueryAccessMode.READ)
        mock_distinct.assert_called_once_with(key="x", filter={})
        assert unique_values == (1, 2)

    def test_count(self, fxt_session_repo) -> None:
        session = make_session()
        repo = fxt_session_repo(session)
        extra_filter = {"mykey": "myvalue"}

        with (
            patch.object(repo, "preliminary_query_match_filter", return_value={}) as mock_match_filter,
            patch.object(repo._collection, "count_documents", return_value=3) as mock_count,
        ):
            count = repo.count(extra_filter=extra_filter)

        mock_match_filter.assert_called_once_with(access_mode=QueryAccessMode.READ)
        mock_count.assert_called_once_with(filter=extra_filter)
        assert count == 3

    def test_delete_by_id(self, fxt_session_repo, fxt_mappable_object) -> None:
        session = make_session()
        repo = fxt_session_repo(session)
        instance = fxt_mappable_object(x=3)

        with (
            patch.object(repo, "preliminary_query_match_filter", return_value={}) as mock_match_filter,
            patch.object(repo._collection, "delete_one", return_value=DeleteResult({"n": 1}, True)) as mock_delete_one,
        ):
            deleted = repo.delete_by_id(instance.id_)

        mock_match_filter.assert_called_once_with(access_mode=QueryAccessMode.WRITE)
        mock_delete_one.assert_called_once_with({"_id": str(instance.id_)})
        assert deleted is True

    def test_delete_all(self, fxt_session_repo) -> None:
        session = make_session()
        repo = fxt_session_repo(session)
        extra_filter = {"mykey": "myvalue"}

        with (
            patch.object(repo, "preliminary_query_match_filter", return_value={}) as mock_match_filter,
            patch.object(
                repo._collection, "delete_many", return_value=DeleteResult({"n": 3}, True)
            ) as mock_delete_many,
        ):
            deleted = repo.delete_all(extra_filter=extra_filter)

        mock_match_filter.assert_called_once_with(access_mode=QueryAccessMode.WRITE)
        mock_delete_many.assert_called_once_with(extra_filter)
        assert deleted is True

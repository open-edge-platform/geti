# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

from datetime import datetime, timedelta

import pytest
from bson import ObjectId

from entities import NullAutoTrainActivationRequest

# Note: if your editor cannot recognize these relative imports, add 'service' to the interpreter paths (PYTHONPATH)
from mapper import AutoTrainActivationToMongo
from repo import SessionBasedAutoTrainActivationRepo

from sc_sdk.repos.mappers import DatetimeToMongo


@pytest.mark.AutoTrainControllerComponent
class TestAutoTrainActivationRepo:
    def test_auto_train_activation_repo(self) -> None:
        repo = SessionBasedAutoTrainActivationRepo()

        assert repo.backward_map == AutoTrainActivationToMongo.backward
        assert repo.null_object == NullAutoTrainActivationRequest()

    def test_get_one_ready(self, request, fxt_ote_id) -> None:
        repo = SessionBasedAutoTrainActivationRepo()
        request.addfinalizer(lambda: repo.delete_all())
        organization_id = fxt_ote_id(1)
        workspace_id = fxt_ote_id(2)
        project_id = fxt_ote_id(3)
        model_storage_id = fxt_ote_id(4)
        session_doc = {
            "organization_id": ObjectId(organization_id),
            "workspace_id": ObjectId(workspace_id),
        }

        # When the repo is empty, a null object should be returned
        found_activation_request = repo.get_one_ready(latest_timestamp=datetime.now())
        assert isinstance(found_activation_request, NullAutoTrainActivationRequest)

        # When no document matches, a null object should be returned
        repo._collection.insert_many(
            [
                {  # ready with recent timestamp
                    "_id": ObjectId(fxt_ote_id(5)),
                    "organization_id": ObjectId(organization_id),
                    "workspace_id": ObjectId(workspace_id),
                    "project_id": ObjectId(project_id),
                    "model_storage_id": ObjectId(model_storage_id),
                    "ready": True,
                    "request_time": DatetimeToMongo.forward(datetime.now()),
                    "session": session_doc,
                },
                {  # not ready with old timestamp
                    "_id": ObjectId(fxt_ote_id(6)),
                    "organization_id": ObjectId(organization_id),
                    "workspace_id": ObjectId(workspace_id),
                    "project_id": ObjectId(project_id),
                    "model_storage_id": ObjectId(model_storage_id),
                    "ready": False,
                    "request_time": DatetimeToMongo.forward(datetime.fromtimestamp(0)),
                    "session": session_doc,
                },
            ]
        )
        query_timestamp = datetime.now() - timedelta(seconds=10)
        found_activation_request = repo.get_one_ready(latest_timestamp=query_timestamp)
        assert isinstance(found_activation_request, NullAutoTrainActivationRequest)

        # When a document matches, the corresponding object should be returned
        query_timestamp = datetime.now() + timedelta(seconds=10)
        found_activation_request = repo.get_one_ready(latest_timestamp=query_timestamp)
        assert not isinstance(found_activation_request, NullAutoTrainActivationRequest)
        assert found_activation_request.id_ == fxt_ote_id(5)

        # If there is a ready document with 'bypass_debouncer', that should always be
        # returned even if the timestamp is recent
        repo._collection.insert_one(
            {  # ready with recent timestamp and 'bypass_debouncer' true
                "_id": ObjectId(fxt_ote_id(7)),
                "organization_id": ObjectId(organization_id),
                "workspace_id": ObjectId(workspace_id),
                "project_id": ObjectId(project_id),
                "model_storage_id": ObjectId(model_storage_id),
                "ready": True,
                "bypass_debouncer": True,
                "request_time": DatetimeToMongo.forward(datetime.now()),
                "session": session_doc,
            },
        )
        query_timestamp = datetime.now() - timedelta(seconds=10)
        found_activation_request = repo.get_one_ready(latest_timestamp=query_timestamp)
        assert not isinstance(found_activation_request, NullAutoTrainActivationRequest)
        assert found_activation_request.id_ == fxt_ote_id(7)

    def test_delete_by_task_node_id(self, request, fxt_ote_id) -> None:
        repo = SessionBasedAutoTrainActivationRepo()
        request.addfinalizer(lambda: repo.delete_all())
        organization_id = fxt_ote_id(1)
        workspace_id = fxt_ote_id(2)
        project_id = fxt_ote_id(3)
        model_storage_id = fxt_ote_id(4)
        task_node_id_1 = fxt_ote_id(5)
        task_node_id_2 = fxt_ote_id(6)
        session_doc = {
            "organization_id": ObjectId(organization_id),
            "workspace_id": ObjectId(workspace_id),
        }

        # Insert two documents for two different tasks
        repo._collection.insert_many(
            [
                {
                    "_id": ObjectId(task_node_id_1),
                    "organization_id": ObjectId(organization_id),
                    "workspace_id": ObjectId(workspace_id),
                    "project_id": ObjectId(project_id),
                    "model_storage_id": ObjectId(model_storage_id),
                    "ready": True,
                    "request_time": DatetimeToMongo.forward(datetime.fromtimestamp(0)),
                    "session": session_doc,
                },
                {  # old timestamp but not ready
                    "_id": ObjectId(task_node_id_2),
                    "organization_id": ObjectId(organization_id),
                    "workspace_id": ObjectId(workspace_id),
                    "project_id": ObjectId(project_id),
                    "model_storage_id": ObjectId(model_storage_id),
                    "ready": True,
                    "request_time": DatetimeToMongo.forward(datetime.fromtimestamp(0)),
                    "session": session_doc,
                },
            ]
        )

        # After deleting the document of one task, the doc of the other task should be still there
        repo.delete_by_task_node_id(task_node_id_1)
        found_activation_request = repo.get_one_ready(latest_timestamp=datetime.now())
        assert found_activation_request.id_ == task_node_id_2

        # After deleting the document of the other task too, nothing should be returned
        repo.delete_by_task_node_id(task_node_id_2)
        found_activation_request = repo.get_one_ready(latest_timestamp=datetime.now())
        assert isinstance(found_activation_request, NullAutoTrainActivationRequest)

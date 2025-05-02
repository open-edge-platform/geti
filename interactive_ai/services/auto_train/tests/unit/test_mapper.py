# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from datetime import datetime, timezone

import pytest
from bson import ObjectId

from mapper import AutoTrainActivationToMongo

from iai_core_py.repos.mappers import DatetimeToMongo


@pytest.mark.AutoTrainControllerComponent
class TestAutoTrainActivationToMongo:
    def test_backward(self, fxt_ote_id) -> None:
        organization_id = fxt_ote_id(1)
        workspace_id = fxt_ote_id(2)
        project_id = fxt_ote_id(3)
        model_storage_id = fxt_ote_id(4)
        entity_id = fxt_ote_id(5)
        req_time = datetime.now(tz=timezone.utc)
        session_doc = {
            "organization_id": ObjectId(organization_id),
            "workspace_id": ObjectId(workspace_id),
        }
        doc = {
            "_id": ObjectId(entity_id),
            "organization_id": ObjectId(organization_id),
            "workspace_id": ObjectId(workspace_id),
            "project_id": ObjectId(project_id),
            "model_storage_id": ObjectId(model_storage_id),
            "ready": True,
            "bypass_debouncer": True,
            "request_time": DatetimeToMongo.forward(req_time),
            "session": session_doc,
        }

        obj = AutoTrainActivationToMongo.backward(doc)

        assert obj.id_ == entity_id
        assert obj.project_id == project_id
        assert obj.model_storage_id == model_storage_id
        assert obj.ready is True
        assert obj.bypass_debouncer is True
        assert obj.timestamp == req_time

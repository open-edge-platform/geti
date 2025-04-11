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

from unittest.mock import patch
from uuid import UUID, uuid4

import mongomock
import pytest
from bson import ObjectId
from bson.binary import UUID_SUBTYPE, Binary, UuidRepresentation
from pymongo import MongoClient

from migration.scripts.adjust_hyper_params import AdjustHyperParamsMigration


@pytest.fixture
def fxt_organization_id():
    yield uuid4()


@pytest.fixture
def fxt_workspace_id():
    yield uuid4()


@pytest.fixture
def fxt_project_id():
    yield ObjectId()


@pytest.fixture
def fxt_doc_id():
    yield ObjectId()


@pytest.fixture
def fxt_configs_before_upgrade(fxt_doc_id, fxt_organization_id, fxt_workspace_id, fxt_project_id):
    """
    List of documents present in the database before upgrade
    """
    yield [
        {
            "_id": fxt_doc_id,
            "organization_id": fxt_organization_id,
            "workspace_id": fxt_workspace_id,
            "project_id": fxt_project_id,
            "entity_identifier": {"type": "HYPER_PARAMETERS"},
            "data": {
                "learning_parameters": {
                    "header": "Configuration for an image classification task",
                    "description": "Configuration for an image classification task",
                    "visible_in_ui": True,
                    "type": "CONFIGURABLE_PARAMETERS",
                    "learning_parameters": {
                        "header": "Learning Parameters",
                        "description": "Learning Parameters",
                        "visible_in_ui": True,
                        "type": "PARAMETER_GROUP",
                    },
                    "num_iters": {
                        "value": 90,
                        "default_value": 90,
                        "description": "Increasing this value causes the results to be more robust but training "
                        "time will be longer.",
                        "header": "Number of training iterations",
                        "type": "INTEGER",
                        "auto_hpo_state": "not_possible",
                        "auto_hpo_value": "",
                        "min_value": 1,
                        "max_value": 1000,
                    },
                    "auto_num_workers": {
                        "value": True,
                        "default_value": False,
                        "description": "Adapt num_workers according to current hardware status automatically.",
                        "header": "Enable auto adaptive num_workers",
                        "warning": "",
                        "editable": True,
                        "visible_in_ui": True,
                        "affects_outcome_of": "TRAINING",
                        "ui_rules": {"operator": "AND", "action": "DISABLE_EDITING", "type": "UI_RULES", "rules": []},
                        "type": "BOOLEAN",
                        "auto_hpo_state": "not_possible",
                        "auto_hpo_value": "",
                    },
                    "early_stop_iteration_patience": {
                        "value": 0,
                        "default_value": 0,
                        "description": "Training will stop if the model does not improve within the number of "
                        "iterations of patience. This ensures the model is trained enough with the number of "
                        "iterations of patience before early stopping.",
                        "header": "Iteration patience for early stopping",
                        "warning": "This is applied exclusively when early stopping is enabled.",
                        "editable": True,
                        "visible_in_ui": True,
                        "affects_outcome_of": "TRAINING",
                    },
                },
            },
        }
    ]


@pytest.fixture
def fxt_configs_after_upgrade(fxt_doc_id, fxt_organization_id, fxt_workspace_id, fxt_project_id):
    """
    List of documents present in the database after upgrade
    """
    yield [
        {
            "_id": fxt_doc_id,
            "organization_id": fxt_organization_id,
            "workspace_id": fxt_workspace_id,
            "project_id": fxt_project_id,
            "entity_identifier": {"type": "HYPER_PARAMETERS"},
            "data": {
                "learning_parameters": {
                    "header": "Configuration for an image classification task",
                    "description": "Configuration for an image classification task",
                    "visible_in_ui": True,
                    "type": "CONFIGURABLE_PARAMETERS",
                    "learning_parameters": {
                        "header": "Learning Parameters",
                        "description": "Learning Parameters",
                        "visible_in_ui": True,
                        "type": "PARAMETER_GROUP",
                    },
                    "num_iters": {
                        "value": 90,
                        "default_value": 90,
                        "description": "Maximum number of epochs to train a model. "
                        "Increasing this value may result in longer "
                        "training, but potentially in a more robust model. Note, if the early stopping is enabled"
                        ", the actual number of epochs may be less than this value.",
                        "header": "Number of training epochs",
                        "type": "INTEGER",
                        "auto_hpo_state": "not_possible",
                        "auto_hpo_value": "",
                        "min_value": 1,
                        "max_value": 1000,
                    },
                    "auto_num_workers": {
                        "value": True,
                        "default_value": False,
                        "description": "Adapt number of workers according to current hardware status automatically.",
                        "header": "Enable auto adaptive num_workers",
                        "warning": "",
                        "editable": True,
                        "visible_in_ui": True,
                        "affects_outcome_of": "TRAINING",
                        "ui_rules": {"operator": "AND", "action": "DISABLE_EDITING", "type": "UI_RULES", "rules": []},
                        "type": "BOOLEAN",
                        "auto_hpo_state": "not_possible",
                        "auto_hpo_value": "",
                    },
                },
            },
        }
    ]


@pytest.fixture(autouse=True)
def fxt_mongo_uuid(monkeypatch):
    def side_effect_mongo_mock_from_uuid(uuid: UUID, uuid_representation=UuidRepresentation.STANDARD):
        """Override (Mock) the bson.binary.Binary.from_uuid function to work for mongomock
        Code is copy pasted from the original function,
        but `uuid_representation` is ignored and only code parts as if
        uuid_representation == UuidRepresentation.STANDARD are used
        """
        if not isinstance(uuid, UUID):
            raise TypeError("uuid must be an instance of uuid.UUID")

        subtype = UUID_SUBTYPE
        payload = uuid.bytes

        return Binary(payload, subtype)

    with patch.object(Binary, "from_uuid", side_effect=side_effect_mongo_mock_from_uuid):
        yield


class TestAdjustHyperParamsMigration:
    def test_adjust_hyper_params_upgrade(
        self,
        fxt_organization_id,
        fxt_workspace_id,
        fxt_project_id,
        fxt_configs_before_upgrade,
        fxt_configs_after_upgrade,
    ) -> None:
        mock_db = mongomock.MongoClient(uuidRepresentation="standard").db
        config_params_collection = mock_db.create_collection("configurable_parameters")

        config_params_collection.insert_many(fxt_configs_before_upgrade)

        with patch.object(MongoClient, "get_database", return_value=mock_db):
            AdjustHyperParamsMigration.upgrade_project(
                organization_id=str(fxt_organization_id),
                workspace_id=str(fxt_workspace_id),
                project_id=str(fxt_project_id),
            )

        actual_configs_after_upgrade = list(config_params_collection.find())

        assert actual_configs_after_upgrade == fxt_configs_after_upgrade

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from datetime import datetime
from unittest.mock import MagicMock, patch

import mongomock
import pytest
from bson import ObjectId
from pymongo import MongoClient
from pymongo.database import Database

from migration.scripts.introduce_evaluation_result import IntroduceEvaluationResultMigration

ORGANIZATION_ID = ObjectId("962c1c6b3a1df3291394b147")
WORKSPACE_ID = ObjectId("722c1c6b321af3321392f189")
PROJECT_ID = ObjectId("662c1c6b3a3df3291394b158")


def mock_preliminary_filter_query(organization_id: str, workspace_id: str, project_id: str) -> dict:
    # Note: mongomock does not support UUID.
    # For testing purposes we will use ObjectId for organization_id and workspace_id instead of UUID.
    return {
        "organization_id": ObjectId(organization_id),
        "workspace_id": ObjectId(workspace_id),
        "project_id": ObjectId(project_id),
    }


@pytest.fixture
def fxt_performance_evaluation_result():
    yield {
        "score": {
            "name": "Accuracy",
            "value": 1,
            "type": "score",
            "label_id": None,
        },
        "dashboard_metrics": [],
        "type": "Performance",
    }


@pytest.fixture
def fxt_performance_model_test_result():
    yield {
        "score": {
            "primary_score": {
                "name": "Dice",
                "value": 0.2701208595955509,
                "type": "score",
                "label_id": None,
            },
            "additional_scores": [
                {
                    "name": "Dice",
                    "value": 0.2701208595955509,
                    "type": "score",
                    "label_id": ObjectId("66292bf88a01cf637c7e60ea"),
                }
            ],
        },
        "dashboard_metrics": [],
        "type": "MultiScorePerformance",
    }


@pytest.fixture
def fxt_deprecated_scores():
    yield [
        {
            "metric": "DICE",
            "score": 0.2701208595955509,
            "label_id": None,
        },
        {
            "metric": "DICE",
            "score": 0.2701208595955509,
            "label_id": ObjectId("66292bf88a01cf637c7e60ea"),
        },
    ]


@pytest.fixture
def fxt_upgraded_scores():
    yield [
        {
            "name": "Dice",
            "type": "score",
            "value": 0.2701208595955509,
            "label_id": None,
        },
        {
            "name": "Dice",
            "type": "score",
            "value": 0.2701208595955509,
            "label_id": ObjectId("66292bf88a01cf637c7e60ea"),
        },
    ]


@pytest.fixture
def fxt_result_set(fxt_performance_evaluation_result):
    yield {
        "_id": ObjectId("662c1d3460b6aa248e48148a"),
        "creation_date": datetime(2024, 1, 1),
        "dataset_storage_id": ObjectId("662c1c6b3a3df3291394b15c"),
        "ground_truth_dataset_id": ObjectId("662c1d2b60b6aa248e481434"),
        "model_id": ObjectId("662c1cc59f0a71a90ba66656"),
        "model_storage_id": ObjectId("662c1c6b3a3df3291394b15c"),
        "organization_id": ORGANIZATION_ID,
        "performance": fxt_performance_evaluation_result,
        "prediction_dataset_id": ObjectId("662c1d2c60b6aa248e481476"),
        "project_id": PROJECT_ID,
        "purpose": "EVALUATION",
        "workspace_id": WORKSPACE_ID,
    }


@pytest.fixture
def fxt_evaluation_result_validation(fxt_result_set):
    evaluation_result_validation = fxt_result_set.copy()
    evaluation_result_validation["purpose"] = "VALIDATION"
    yield evaluation_result_validation


@pytest.fixture
def fxt_model_test(fxt_deprecated_scores):
    yield {
        "_id": ObjectId("662c13e8f8041483b2f96b6c"),
        "creation_date": datetime(2024, 1, 2),
        "dataset_storage_ids": [ObjectId("66292bf88a01cf637c7e60eb")],
        "ground_truth_dataset_id": "662c1408b2c86b4a1ee0c4d6",
        "model_id": ObjectId("662a29e02ff79b338a5d4563"),
        "model_storage_id": ObjectId("66292bf88a01cf637c7e60e9"),
        "name": "model_test",
        "organization_id": ORGANIZATION_ID,
        "scores": fxt_deprecated_scores,
        "prediction_dataset_id": "662c1d2c60b6aa248e481476",
        "project_id": PROJECT_ID,
        "workspace_id": WORKSPACE_ID,
        "job_id": "65a0c1241644951b7b271afd",
        "state": "DONE",
    }


@pytest.fixture
def fxt_model_test_failed(fxt_model_test):
    model_test_failed = fxt_model_test.copy()
    model_test_failed["_id"] = ObjectId("662c13e8f8041483b219636d")
    model_test_failed["ground_truth_dataset_id"] = ""
    model_test_failed["prediction_dataset_id"] = ""
    model_test_failed["state"] = "FAILED"
    yield model_test_failed


@pytest.fixture
def fxt_evaluation_result_model_test(fxt_model_test, fxt_performance_model_test_result):
    evaluation_result_model_test = fxt_model_test.copy()
    # convert to object id
    evaluation_result_model_test["job_id"] = ObjectId(fxt_model_test["job_id"])
    evaluation_result_model_test["ground_truth_dataset_id"] = ObjectId(fxt_model_test["ground_truth_dataset_id"])
    evaluation_result_model_test["prediction_dataset_id"] = ObjectId(fxt_model_test["prediction_dataset_id"])

    # Add missing fields
    evaluation_result_model_test["dataset_storage_id"] = ObjectId("66292bf88a01cf637c7e60eb")
    evaluation_result_model_test["purpose"] = "MODEL_TEST"
    evaluation_result_model_test["performance"] = fxt_performance_model_test_result
    del evaluation_result_model_test["scores"]
    yield evaluation_result_model_test


@pytest.fixture
def fxt_evaluation_result_model_test_failed(fxt_model_test_failed, fxt_performance_model_test_result):
    evaluation_result_model_test_failed = fxt_model_test_failed.copy()
    # convert to object id
    evaluation_result_model_test_failed["job_id"] = ObjectId(fxt_model_test_failed["job_id"])
    # ground_truth_dataset_id and prediction_dataset_id are still kept as empty strings

    # Add missing fields
    evaluation_result_model_test_failed["dataset_storage_id"] = ObjectId("66292bf88a01cf637c7e60eb")
    evaluation_result_model_test_failed["purpose"] = "MODEL_TEST"
    evaluation_result_model_test_failed["performance"] = fxt_performance_model_test_result
    del evaluation_result_model_test_failed["scores"]
    yield evaluation_result_model_test_failed


class TestEvaluationResultMigration:
    def test_upgrade_project(self) -> None:
        mock_evaluation_result_collection = MagicMock()
        mock_result_set_collection = MagicMock()
        mock_model_test_result_collection = MagicMock()

        with (
            patch.object(
                Database,
                "get_collection",
                side_effect=[
                    mock_evaluation_result_collection,
                    mock_result_set_collection,
                    mock_model_test_result_collection,
                ],
            ),
            patch.object(IntroduceEvaluationResultMigration, "_upgrade_result_set") as mock_upgrade_result_set,
            patch.object(
                IntroduceEvaluationResultMigration, "_upgrade_model_test_result"
            ) as mock_upgrade_model_test_result,
        ):
            IntroduceEvaluationResultMigration.upgrade_project(
                organization_id=str(ORGANIZATION_ID), workspace_id=str(WORKSPACE_ID), project_id=str(PROJECT_ID)
            )

        mock_upgrade_result_set.assert_called_once_with(
            organization_id=str(ORGANIZATION_ID),
            workspace_id=str(WORKSPACE_ID),
            project_id=str(PROJECT_ID),
            result_set_collection=mock_result_set_collection,
            evaluation_result_collection=mock_evaluation_result_collection,
        )
        mock_upgrade_model_test_result.assert_called_once_with(
            organization_id=str(ORGANIZATION_ID),
            workspace_id=str(WORKSPACE_ID),
            project_id=str(PROJECT_ID),
            model_test_result_collection=mock_model_test_result_collection,
            evaluation_result_collection=mock_evaluation_result_collection,
        )

    def test_downgrade_project(self) -> None:
        mock_evaluation_result_collection = MagicMock()
        mock_result_set_collection = MagicMock()
        mock_model_test_result_collection = MagicMock()
        mock_media_score_collection = MagicMock()

        with (
            patch.object(
                Database,
                "get_collection",
                side_effect=[
                    mock_evaluation_result_collection,
                    mock_result_set_collection,
                    mock_model_test_result_collection,
                    mock_media_score_collection,
                ],
            ),
            patch.object(
                IntroduceEvaluationResultMigration, "_downgrade_evaluation_result"
            ) as mock_downgrade_evaluation_result,
        ):
            IntroduceEvaluationResultMigration.downgrade_project(
                organization_id=str(ORGANIZATION_ID), workspace_id=str(WORKSPACE_ID), project_id=str(PROJECT_ID)
            )

        mock_downgrade_evaluation_result.assert_called_once_with(
            organization_id=str(ORGANIZATION_ID),
            workspace_id=str(WORKSPACE_ID),
            project_id=str(PROJECT_ID),
            evaluation_result_collection=mock_evaluation_result_collection,
        )

    @patch.object(
        IntroduceEvaluationResultMigration, "_preliminary_project_query_filter", new=mock_preliminary_filter_query
    )
    def test_upgrade_downgrade_equality(
        self,
        fxt_result_set,
        fxt_evaluation_result_validation,
        fxt_model_test,
        fxt_evaluation_result_model_test,
    ) -> None:
        # Arrange
        mock_db = mongomock.MongoClient().db
        result_set_collection = mock_db.result_set
        evaluation_result_collection = mock_db.evaluation_result
        model_test_result_collection = mock_db.model_test_result

        result_set_collection.insert_one(fxt_result_set)
        model_test_result_collection.insert_one(fxt_model_test)

        # Act
        with patch.object(MongoClient, "get_database", return_value=mock_db):
            IntroduceEvaluationResultMigration.upgrade_project(
                organization_id=str(ORGANIZATION_ID), workspace_id=str(WORKSPACE_ID), project_id=str(PROJECT_ID)
            )

            # Assert - docs upgraded
            assert evaluation_result_collection.find_one({"purpose": "VALIDATION"}) == fxt_evaluation_result_validation
            assert evaluation_result_collection.find_one({"purpose": "MODEL_TEST"}) == fxt_evaluation_result_model_test

            IntroduceEvaluationResultMigration.downgrade_project(
                organization_id=str(ORGANIZATION_ID), workspace_id=str(WORKSPACE_ID), project_id=str(PROJECT_ID)
            )

            # Assert - docs downgraded
            assert result_set_collection.find_one() == fxt_result_set
            assert model_test_result_collection.find_one() == fxt_model_test

    @patch.object(
        IntroduceEvaluationResultMigration, "_preliminary_project_query_filter", new=mock_preliminary_filter_query
    )
    def test_upgrade_result_set(
        self,
        fxt_result_set,
        fxt_evaluation_result_validation,
    ) -> None:
        # Arrange
        mock_db = mongomock.MongoClient().db
        result_set_collection = mock_db.result_set
        evaluation_result_collection = mock_db.evaluation_result
        result_set_collection.insert_one(fxt_result_set)

        # Act
        IntroduceEvaluationResultMigration._upgrade_result_set(
            organization_id=str(ORGANIZATION_ID),
            workspace_id=str(WORKSPACE_ID),
            project_id=str(PROJECT_ID),
            result_set_collection=result_set_collection,
            evaluation_result_collection=evaluation_result_collection,
        )

        # Assert
        assert result_set_collection.find_one() == fxt_result_set
        assert evaluation_result_collection.find_one() == fxt_evaluation_result_validation

    @patch.object(
        IntroduceEvaluationResultMigration, "_preliminary_project_query_filter", new=mock_preliminary_filter_query
    )
    def test_downgrade_evaluation_result(
        self,
        fxt_result_set,
        fxt_evaluation_result_validation,
    ) -> None:
        # Arrange
        mock_db = mongomock.MongoClient().db

        result_set_collection = mock_db.result_set
        evaluation_result_collection = mock_db.evaluation_result
        result_set_collection.insert_one(fxt_result_set)
        evaluation_result_collection.insert_one(fxt_evaluation_result_validation)

        # Act
        IntroduceEvaluationResultMigration._downgrade_evaluation_result(
            organization_id=str(ORGANIZATION_ID),
            workspace_id=str(WORKSPACE_ID),
            project_id=str(PROJECT_ID),
            evaluation_result_collection=evaluation_result_collection,
        )

        # Assert
        assert evaluation_result_collection.find_one() is None
        assert result_set_collection.find_one() == fxt_result_set

    @patch.object(
        IntroduceEvaluationResultMigration, "_preliminary_project_query_filter", new=mock_preliminary_filter_query
    )
    def test_upgrade_model_test_result(
        self,
        fxt_model_test,
        fxt_model_test_failed,
        fxt_evaluation_result_model_test,
        fxt_evaluation_result_model_test_failed,
    ) -> None:
        # Arrange
        mock_db = mongomock.MongoClient().db
        model_test_result_collection = mock_db.model_test_result
        evaluation_result_collection = mock_db.evaluation_result
        model_test_result_collection.insert_one(fxt_model_test)
        model_test_result_collection.insert_one(fxt_model_test_failed)

        # Act
        IntroduceEvaluationResultMigration._upgrade_model_test_result(
            organization_id=str(ORGANIZATION_ID),
            workspace_id=str(WORKSPACE_ID),
            project_id=str(PROJECT_ID),
            model_test_result_collection=model_test_result_collection,
            evaluation_result_collection=evaluation_result_collection,
        )

        # Assert
        assert model_test_result_collection.count_documents({}) == 2
        assert model_test_result_collection.find_one({"_id": fxt_model_test["_id"]}) == fxt_model_test
        assert model_test_result_collection.find_one({"_id": fxt_model_test_failed["_id"]}) == fxt_model_test_failed

        assert evaluation_result_collection.count_documents({"purpose": "MODEL_TEST"}) == 2
        assert evaluation_result_collection.find_one({"_id": fxt_model_test["_id"]}) == fxt_evaluation_result_model_test
        assert (
            evaluation_result_collection.find_one({"_id": fxt_model_test_failed["_id"]})
            == fxt_evaluation_result_model_test_failed
        )

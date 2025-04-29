# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from uuid import UUID

from bson import ObjectId
from pymongo import DESCENDING, IndexModel
from pymongo.collection import Collection

from migration.utils import IMigrationScript, MongoDBConnection

EVALUATION_RESULT = "evaluation_result"
RESULT_SET = "result_set"
MODEL_TEST_RESULT = "model_test_result"

logger = logging.getLogger(__name__)


class IntroduceEvaluationResultMigration(IMigrationScript):
    """
    This script is used to copy MongoDB documents from the 'result_set' and 'model_test_result' collections
    into the unified new collection: 'evaluation_result'.

    Note: this migration script does not delete any existing documents from the database.

    Summary of changes per collection:
        copy 'result_set' to 'evaluation_result':
            Modified fields:
                - 'purpose': 'EVALUATION' -> 'VALIDATION'

        copy 'model_test_result' to 'evaluation_result':
            New fields:
                - 'dataset_storage_id': 'dataset_storage_ids'[0]
                - 'purpose': 'MODEL_TEST'
                - 'performance': converted from 'scores'
            Modified fields:
                - 'job_id': ObjectId(job_id)
                - 'ground_truth_dataset_id': ObjectId(gt_dataset_id)
                - 'prediction_dataset_id': ObjectId(pred_dataset_id)
            Removed fields:
                - 'scores'
    """

    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        db = MongoDBConnection().geti_db
        evaluation_result_collection = db.get_collection(name=EVALUATION_RESULT)
        collection_indices = [
            IndexModel([("model_id", DESCENDING), ("purpose", DESCENDING)]),
            IndexModel([("dataset_storage_ids", DESCENDING), ("purpose", DESCENDING)]),
        ]
        evaluation_result_collection.create_indexes(cls.__project_based_collection_indices() + collection_indices)

        cls._upgrade_result_set(
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            result_set_collection=db.get_collection(name=RESULT_SET),
            evaluation_result_collection=evaluation_result_collection,
        )
        cls._upgrade_model_test_result(
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            model_test_result_collection=db.get_collection(name=MODEL_TEST_RESULT),
            evaluation_result_collection=evaluation_result_collection,
        )
        logger.info("Upgrade of project ID `%s` for evaluation_result collection completed.", project_id)

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        db = MongoDBConnection().geti_db
        evaluation_result_collection = db.get_collection(name=EVALUATION_RESULT)

        cls._downgrade_evaluation_result(
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            evaluation_result_collection=evaluation_result_collection,
        )
        logger.info("Downgrade of project ID `%s` for evaluation_result collection completed.", project_id)

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass

    @staticmethod
    def _preliminary_project_query_filter(organization_id: str, workspace_id: str, project_id: str) -> dict:
        return {
            "organization_id": UUID(organization_id),
            "workspace_id": UUID(workspace_id),
            "project_id": ObjectId(project_id),
        }

    @staticmethod
    def _delete_collection_if_empty(collection: Collection) -> None:
        if collection.find_one() is None:
            collection.drop()
            logger.info(f"Collection '{collection.name}' has been deleted because it is empty.")

    @classmethod
    def _upgrade_result_set(
        cls,
        organization_id: str,
        workspace_id: str,
        project_id: str,
        result_set_collection: Collection,
        evaluation_result_collection: Collection,
    ) -> None:
        logger.info("Copying result_set collection into evaluation_result...")
        preliminary_filter_query = cls._preliminary_project_query_filter(
            organization_id=organization_id, workspace_id=workspace_id, project_id=project_id
        )
        result_set_docs = result_set_collection.find(preliminary_filter_query)
        update_docs = 0
        for doc in result_set_docs:
            # Modified fields:
            # backward compatibility fix: make sure that purpose is always present with "VALIDATION" as default
            if doc.get("purpose", "EVALUATION").upper() == "EVALUATION":
                doc["purpose"] = "VALIDATION"

            evaluation_result_collection.replace_one({"_id": doc["_id"]}, doc, upsert=True)
            update_docs += 1
        logger.info(f"Number of docs updated: {update_docs}")

    @classmethod
    def _downgrade_evaluation_result(
        cls,
        organization_id: str,
        workspace_id: str,
        project_id: str,
        evaluation_result_collection: Collection,
    ) -> None:
        logger.info("Downgrading evaluation_result collection...")
        preliminary_filter_query = cls._preliminary_project_query_filter(
            organization_id=organization_id, workspace_id=workspace_id, project_id=project_id
        )
        # Also removes MODEL_TEST documents
        result = evaluation_result_collection.delete_many(filter=preliminary_filter_query)
        logger.info(f"Number of docs removed from evaluation_result collection: {result.deleted_count}")
        cls._delete_collection_if_empty(evaluation_result_collection)

    @classmethod
    def _upgrade_model_test_result(
        cls,
        organization_id: str,
        workspace_id: str,
        project_id: str,
        model_test_result_collection: Collection,
        evaluation_result_collection: Collection,
    ) -> None:
        logger.info("Upgrading model_test_result collection...")
        collection_indices = [
            IndexModel([("model_id", DESCENDING), ("purpose", DESCENDING)]),
            IndexModel([("dataset_storage_ids", DESCENDING), ("purpose", DESCENDING)]),
        ]
        model_test_result_collection.create_indexes(cls.__project_based_collection_indices() + collection_indices)

        preliminary_filter_query = cls._preliminary_project_query_filter(
            organization_id=organization_id, workspace_id=workspace_id, project_id=project_id
        )
        model_test_result_docs = model_test_result_collection.find(preliminary_filter_query)
        update_docs = 0
        for doc in model_test_result_docs:
            # New fields:
            doc["dataset_storage_id"] = doc["dataset_storage_ids"][0]
            doc["purpose"] = "MODEL_TEST"
            doc["performance"] = cls._convert_scores_to_performance(doc["scores"])

            # Modified fields:
            if job_id := doc.get("job_id"):
                doc["job_id"] = ObjectId(job_id)
            if gt_dataset_id := doc.get("ground_truth_dataset_id"):
                doc["ground_truth_dataset_id"] = ObjectId(gt_dataset_id)
            if pred_dataset_id := doc.get("prediction_dataset_id"):
                doc["prediction_dataset_id"] = ObjectId(pred_dataset_id)

            # Removed fields:
            del doc["scores"]

            # Update collections
            evaluation_result_collection.replace_one({"_id": doc["_id"]}, doc, upsert=True)
            update_docs += 1
        logger.info(f"Number of docs updated: {update_docs}")

    @staticmethod
    def _convert_scores_to_performance(scores: list[dict]) -> dict:
        # Use null_score as default
        primary_score = {
            "name": "NullScoreMetric",
            "value": 0,
            "type": "null_score",
            "label_id": None,
        }
        additional_scores = []
        for score in scores:
            # primary score is the score without label_id information
            if not score["label_id"] and primary_score["type"] == "null_score":
                primary_score = {
                    "name": score["metric"].title(),
                    "value": score["score"],
                    "type": "score",
                    "label_id": None,
                }
            else:
                additional_scores.append(
                    {
                        "name": score["metric"].title(),
                        "value": score["score"],
                        "type": "score",
                        "label_id": score["label_id"],
                    }
                )
        return {
            "score": {
                "primary_score": primary_score,
                "additional_scores": additional_scores,
            },
            "dashboard_metrics": [],
            "type": "MultiScorePerformance",
        }

    @staticmethod
    def __project_based_collection_indices() -> list[IndexModel]:
        return [
            IndexModel([("organization_id", DESCENDING), ("location", DESCENDING)]),
            IndexModel([("workspace_id", DESCENDING)]),
            IndexModel([("project_id", DESCENDING)]),
        ]

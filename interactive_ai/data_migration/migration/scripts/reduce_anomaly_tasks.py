# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from uuid import UUID

from bson import ObjectId

from migration.utils import IMigrationScript, MongoDBConnection

logger = logging.getLogger(__name__)

ANOM_STRINGS_MAPPING = {
    "ANOMALY_CLASSIFICATION": "ANOMALY",
    "ANOMALY_DETECTION": "ANOMALY",
    "ANOMALY_SEGMENTATION": "ANOMALY",
    "anomaly_classification": "anomaly",
    "anomaly_detection": "anomaly",
    "anomaly_segmentation": "anomaly",
    "Anomaly classification": "Anomaly",
    "Anomaly detection": "Anomaly",
    "Anomaly segmentation": "Anomaly",
    "Anomaly Classification": "Anomaly",
    "Anomaly Detection": "Anomaly",
    "Anomaly Segmentation": "Anomaly",
    "anomaly classification": "anomaly",
    "anomaly detection": "anomaly",
    "anomaly segmentation": "anomaly",
}


class ReduceAnomalyTasksMigration(IMigrationScript):
    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """
        Reduce all forms of ANOM_STRINGS_MAPPING in the project, label, and task_node collections.
        Then it updates the performance of the project by removing the global_score and local_score fields, and changing
        the metric to accuracy.
        Updating the performance must happen after the reduction of the ANOM_STRINGS_MAPPING, due to it relying on the
        project type to be ANOMALY.
        """
        for collection_name in ["project", "label", "task_node"]:
            cls._reduce(
                collection_name=collection_name,
                organization_id=organization_id,
                workspace_id=workspace_id,
                project_id=project_id,
            )

        cls._update_performance(organization_id=organization_id, workspace_id=workspace_id, project_id=project_id)

    @classmethod
    def _reduce(cls, collection_name: str, organization_id: str, workspace_id: str, project_id: str) -> None:
        filter = cls.get_preliminary_filter(
            collection_name=collection_name,
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
        )
        db = MongoDBConnection().geti_db
        collection = db.get_collection(collection_name)

        def update_nested_fields(document: dict, fields_to_update: dict, parent_key: str = "") -> None:
            for key, value in document.items():
                full_key = f"{parent_key}.{key}" if parent_key else key
                if isinstance(value, dict):
                    update_nested_fields(value, fields_to_update, full_key)
                elif isinstance(value, str):
                    for bad, good in ANOM_STRINGS_MAPPING.items():
                        if value.find(bad) != -1:
                            fields_to_update[full_key] = value.replace(bad, good)

        documents = collection.find(filter)
        for doc in documents:
            fields_to_update: dict = {}
            update_nested_fields(document=doc, fields_to_update=fields_to_update)
            if fields_to_update:
                collection.update_one({"_id": doc["_id"]}, {"$set": fields_to_update})
                logger.debug(f"Performed anomaly reduction for {collection_name} document with with _id: {doc['_id']}")

    @classmethod
    def _update_performance(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        filter = cls.get_preliminary_filter(
            collection_name="project", organization_id=organization_id, workspace_id=workspace_id, project_id=project_id
        )
        db = MongoDBConnection().geti_db
        collection = db.get_collection("project")

        documents = collection.find(filter)
        for doc in documents:
            if doc["performance"]["score"] and doc["project_type"] == "ANOMALY":
                for task_performance in doc["performance"]["task_performances"]:
                    task_performance.pop("global_score", None)
                    task_performance.pop("local_score", None)
                    task_performance["score"]["metric_type"] = "accuracy"
                update = {"$set": {"performance.task_performances": doc["performance"]["task_performances"]}}
                collection.update_one(filter=filter, update=update)
                logger.debug(f"Performed anomaly performance reduction for document with with _id: {doc['_id']}")

    @staticmethod
    def get_preliminary_filter(collection_name: str, organization_id: str, workspace_id: str, project_id: str) -> dict:
        project_key = "_id" if collection_name == "project" else "project_id"
        return {
            "organization_id": UUID(organization_id),
            "workspace_id": UUID(workspace_id),
            project_key: ObjectId(project_id),
        }

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """No action is possible since the original anomaly task type cannot be known"""

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        """No action required, indexes are automatically recreated by the repos"""

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        """No action required, indexes are automatically recreated by the repos"""

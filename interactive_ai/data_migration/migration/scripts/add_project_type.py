# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import Any
from uuid import UUID

from bson import ObjectId
from pymongo.errors import OperationFailure

from migration.utils import IMigrationScript, MongoDBConnection


class AddProjectTypeMigration(IMigrationScript):
    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """
        Add project_type to project docs representing the task type of trainable task nodes

        This field is necessary to count the number of projects per project type
        """
        db = MongoDBConnection().geti_db
        project_collection = db.get_collection("project")

        pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "_id": ObjectId(project_id),
                    "workspace_id": UUID(workspace_id),
                    "organization_id": UUID(organization_id),
                },
            },
            {
                "$lookup": {
                    "from": "task_node",
                    "localField": "task_graph.nodes",
                    "foreignField": "_id",
                    "as": "task_types",
                    "pipeline": [
                        {
                            "$match": {
                                "is_trainable": True,
                            },
                        },
                        {
                            "$project": {
                                "_id": "$task_type",
                            },
                        },
                    ],
                },
            },
            {
                "$project": {
                    "_id": "$_id",
                    "project_type": {
                        "$reduce": {
                            "input": "$task_types",
                            "initialValue": "",
                            "in": {
                                "$concat": [
                                    "$$value",
                                    {
                                        "$cond": [
                                            {
                                                "$eq": ["$$value", ""],
                                            },
                                            "",
                                            " → ",
                                        ],
                                    },
                                    "$$this._id",
                                ],
                            },
                        },
                    },
                },
            },
        ]
        docs = project_collection.aggregate(pipeline=pipeline)
        result = {doc["_id"]: doc["project_type"] for doc in docs}
        if len(result) == 1 and ObjectId(project_id) in result:
            project_collection.find_one_and_update(
                {
                    "_id": ObjectId(project_id),
                    "workspace_id": UUID(workspace_id),
                    "organization_id": UUID(organization_id),
                },
                [{"$set": {"project_type": result[ObjectId(project_id)]}}],
            )
        else:
            raise ValueError(
                f"Could not fetch a valid project type for the following project: "
                f"project_id: {project_id}, "
                f"workspace_id: {workspace_id}, "
                f"organization_id: {organization_id}."
            )

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """No action necessary because an extra field in the project doc does not hinder the backwards mapper"""

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        """
        Remove old and now redundant index

        Old index was necessary for a complex lookup routine to get the project type on the fly. With project type
        added to the project doc, we can now directly count projects per project type without a lookup to the task
        node collection.
        """
        db = MongoDBConnection().geti_db
        project_collection = db.get_collection("project")
        try:
            project_collection.drop_index("hidden_1_task_graph.pipeline_representation_1__id_1")
        except OperationFailure:
            pass

        task_node_collection = db.get_collection("task_node")
        try:
            task_node_collection.drop_index("project_id_1_is_trainable_1_task_type_1")
        except OperationFailure:
            pass

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        """No action required, indexes are automatically recreated by the repos"""

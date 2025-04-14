# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from uuid import UUID

from bson import ObjectId

from migration.utils import IMigrationScript, MongoDBConnection

logger = logging.getLogger(__name__)


class UpdateMediaScoreMigration(IMigrationScript):
    """
    Script to update the score objects in "media_score" documents:
        - add subfield "type" = "score"
        - rename subfield "score" -> "value"
        - rename subfield "metric" -> "name"
    """

    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        db = MongoDBConnection().geti_db
        media_score_collection = db.get_collection("media_score")
        res = media_score_collection.update_many(
            {
                "organization_id": UUID(organization_id),
                "workspace_id": UUID(workspace_id),
                "project_id": ObjectId(project_id),
            },
            [
                {
                    "$set": {
                        "scores": {
                            "$map": {
                                "input": "$scores",
                                "as": "score",
                                "in": {
                                    "$mergeObjects": [
                                        {
                                            # Rename "metric" -> "name" and "score" -> "value"
                                            "name": "$$score.metric",
                                            "value": "$$score.score",
                                            "type": "score",
                                            "label_id": "$$score.label_id",
                                        },
                                        {
                                            # Keep existing fields like "name", "value", and "type" if they exist
                                            "name": "$$score.name",
                                            "value": "$$score.value",
                                            "type": {"$ifNull": ["$$score.type", "score"]},
                                            "label_id": "$$score.label_id",
                                        },
                                    ]
                                },
                            }
                        }
                    }
                },
            ],
        )
        logger.info(f"Total upgraded count: {res.modified_count}")

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        db = MongoDBConnection().geti_db
        media_score_collection = db.get_collection("media_score")
        res = media_score_collection.update_many(
            {
                "organization_id": UUID(organization_id),
                "workspace_id": UUID(workspace_id),
                "project_id": ObjectId(project_id),
            },
            [
                {
                    "$set": {
                        "scores": {
                            "$map": {
                                "input": "$scores",
                                "as": "score",
                                "in": {
                                    "$mergeObjects": [
                                        {
                                            # Rename for downgrade "name" -> "metric" and "value" -> "score"
                                            "metric": "$$score.name",
                                            "score": "$$score.value",
                                            "label_id": "$$score.label_id",
                                        },
                                        {
                                            # Keep existing fields like "metric", "value" if they exist
                                            "metric": "$$score.metric",
                                            "score": "$$score.score",
                                            "label_id": "$$score.label_id",
                                        },
                                    ]
                                },
                            }
                        }
                    },
                }
            ],
        )
        logger.info(f"Total downgraded count: {res.modified_count}")

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        pass

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from uuid import UUID

from bson import ObjectId

from migration.utils import IMigrationScript, MongoDBConnection


class RemoveEmptyAnnotationSceneMigrationScript(IMigrationScript):
    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """
        Removes first annotation scene sorted on creation date, if annotations list is empty.
        Also removes corresponding annotation scene state doc if annotation scene doc is removed.
        """
        organization_uuid = UUID(organization_id)
        workspace_uuid = UUID(workspace_id)
        project_objectid = ObjectId(project_id)

        db = MongoDBConnection().geti_db
        annotation_collection = db.get_collection("annotation_scene")
        annotation_state_collection = db.get_collection("annotation_scene_state")

        pipeline = [
            {
                "$match": cls._preliminary_project_query_filter(
                    organization_id=organization_uuid, workspace_id=workspace_uuid, project_id=project_objectid
                ),
            },
            {"$sort": {"creation_date": 1}},
            {
                "$group": {
                    "_id": "$media_identifier",
                    "annotation_scene_id": {"$first": "$_id"},
                    "annotations": {"$first": "$annotations"},
                },
            },
            {
                "$match": {
                    "annotations": [],
                },
            },
        ]

        docs = annotation_collection.aggregate(pipeline, allowDiskUse=True)
        annotation_scene_ids = [doc["annotation_scene_id"] for doc in docs]
        for batch in range(0, len(annotation_scene_ids), 100):
            annotation_filter = cls._preliminary_project_query_filter(
                organization_id=organization_uuid, workspace_id=workspace_uuid, project_id=project_objectid
            )
            annotation_filter["_id"] = {"$in": annotation_scene_ids[batch : batch + 100]}
            annotation_collection.delete_many(annotation_filter)

            state_filter = cls._preliminary_project_query_filter(
                organization_id=organization_uuid, workspace_id=workspace_uuid, project_id=project_objectid
            )
            state_filter["annotation_scene_id"] = {"$in": annotation_scene_ids[batch : batch + 100]}
            annotation_state_collection.delete_many(state_filter)

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """Restoring deleted docs not necessary as empty annotation scenes were already not necessary in Geti 2.0"""

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        """This script only deals with project data"""

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        """This script only deals with project data"""

    @staticmethod
    def _preliminary_project_query_filter(organization_id: UUID, workspace_id: UUID, project_id: ObjectId) -> dict:
        return {
            "organization_id": organization_id,
            "workspace_id": workspace_id,
            "project_id": project_id,
        }

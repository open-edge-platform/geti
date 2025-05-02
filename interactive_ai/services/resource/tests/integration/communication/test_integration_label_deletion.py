# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from copy import deepcopy
from http import HTTPStatus
from typing import Any
from unittest.mock import ANY, patch

from iai_core.algorithms import ModelTemplateList

DETECTION_PROJECT_DATA: dict[str, Any] = {
    "connections": [
        {
            "from": "dataset",
            "to": "detection task",
        },
    ],
    "tasks": [
        {"task_type": "dataset", "title": "dataset"},
        {
            "task_type": "detection",
            "title": "detection task",
            "labels": [
                {"name": "label1", "group": "grp", "color": "#01234567"},
                {"name": "label2", "group": "grp", "color": "#89abcdef"},
            ],
        },
    ],
}


class TestLabelDeletionEndpoint:
    def test_label_deletion(
        self,
        fxt_resource_rest,
        fxt_organization_id,
        fxt_db_project_service,
    ) -> None:
        """
        Test label deletion on a project with 2 normal labels and 1 empty label.

        Steps:
        1. Create a project with 2 normal labels and 1 empty label.
        2. Annotate one image with both normal labels
        3. Delete one of the normal labels
        4. Verify deletion works as expected and that the image remains annotated with just one label
        5. Verify that the remaining label can't be deleted.
        """

        # Hooks for event publishing
        patch_publish_event_project = patch(
            "managers.project_manager.publish_event",
            return_value=None,
        )
        model_templates = [
            ModelTemplateList().get_by_id("dataset"),
            ModelTemplateList().get_by_id("detection"),
        ]
        # Create project, image and annotation with 1 shape with 2 labels
        project = fxt_db_project_service.create_empty_project(
            name="test_label_deletion",
            pipeline_data=DETECTION_PROJECT_DATA,
            model_templates=model_templates,
        )
        initial_project_labels = fxt_db_project_service.label_schema.get_labels(include_empty=True)
        assert len(initial_project_labels) == 2
        image = fxt_db_project_service.create_and_save_random_image("image 1")

        fxt_db_project_service.create_and_save_random_annotation_scene(
            image=image,
            labels=[initial_project_labels[0], initial_project_labels[1]],
            full_size_rectangle=True,
        )

        # Update pipeline data for label deletion
        updated_pipeline_data = deepcopy(DETECTION_PROJECT_DATA)
        updated_pipeline_data["tasks"][0]["id"] = project.tasks[0].id_
        updated_pipeline_data["tasks"][1]["id"] = project.tasks[1].id_
        for label_data in updated_pipeline_data["tasks"][1]["labels"]:
            label_id = next(label.id_ for label in initial_project_labels if label.name == label_data["name"])
            label_data["id"] = label_id
        updated_pipeline_data["tasks"][1]["labels"][0]["is_deleted"] = True
        updated_pipeline_data["tasks"][1]["labels"][0]["id"] = str(initial_project_labels[0].id_)
        updated_pipeline_data["connections"][0]["from"] = project.tasks[0].id_
        updated_pipeline_data["connections"][0]["to"] = project.tasks[1].id_

        # Update project with new pipeline data
        project_update_request_body = {
            "name": project.name,
            "id": str(project.id_),
            "pipeline": updated_pipeline_data,
        }
        project_update_endpoint = (
            f"/api/v1/organizations/{fxt_organization_id}/workspaces/{project.workspace_id}/projects/{project.id_}"
        )
        with patch_publish_event_project as patched_pub_proj:
            project_update_response = fxt_resource_rest.put(project_update_endpoint, json=project_update_request_body)
        assert project_update_response.status_code == HTTPStatus.OK

        fxt_db_project_service.reload_label_schema()
        project_labels = fxt_db_project_service.label_schema.get_labels(include_empty=True)
        assert len(project_labels) == 1

        # Check that the expected Kafka message is sent
        patched_pub_proj.assert_called_once_with(
            topic="project_updates",
            body={
                "workspace_id": project.workspace_id,
                "project_id": str(project.id_),
            },
            key=str(project.id_).encode(),
            headers_getter=ANY,
        )

        # Check that the annotation returns only the shape with the non-deleted label
        annotation_get_endpoint = (
            f"/api/v1/organizations/{fxt_organization_id}/workspaces/{project.workspace_id}/projects/{project.id_}"
            f"/datasets/{project.training_dataset_storage_id}/media/images/{image.id_}/annotations/latest"
        )
        annotation_get_response = fxt_resource_rest.get(
            annotation_get_endpoint,
            headers={"x-auth-request-access-token": "testing"},
        )

        annotation_get_response_body = annotation_get_response.json()
        assert len(annotation_get_response_body["annotations"][0]["labels"]) == 1

        # Try deleting the other label and check that it fails with a BadRequest
        project_update_request_body["pipeline"]["tasks"][1]["labels"][1]["is_deleted"] = True
        project_update_request_body["pipeline"]["tasks"][1]["labels"][1]["id"] = str(initial_project_labels[1].id_)
        response = fxt_resource_rest.put(
            project_update_endpoint,
            json=project_update_request_body,
            headers={"x-auth-request-access-token": "testing"},
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

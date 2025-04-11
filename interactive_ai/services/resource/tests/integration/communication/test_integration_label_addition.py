# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
import logging
from copy import deepcopy
from http import HTTPStatus
from typing import Any
from unittest.mock import ANY, patch

from geti_spicedb_tools import SpiceDB

from geti_kafka_tools import publish_event
from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier
from sc_sdk.algorithms import ModelTemplateList
from sc_sdk.repos import SuspendedAnnotationScenesRepo

logger = logging.getLogger(__name__)

MULTICLASS_CLASSIFICATION_PROJECT_DATA: dict[str, Any] = {
    "connections": [
        {
            "from": "dataset",
            "to": "classification task",
        },
    ],
    "tasks": [
        {"task_type": "dataset", "title": "dataset"},
        {
            "task_type": "classification",
            "title": "classification task",
            "labels": [
                {"name": "label1", "group": "grp", "color": "#eebbccdd"},
                {"name": "label2", "group": "grp", "color": "#aabbccdd"},
            ],
        },
    ],
}

MULTILABEL_CLASSIFICATION_PROJECT_DATA: dict[str, Any] = {
    "connections": [
        {
            "from": "dataset",
            "to": "classification task",
        },
    ],
    "tasks": [
        {"task_type": "dataset", "title": "dataset"},
        {
            "task_type": "classification",
            "title": "classification task",
            "labels": [
                {"name": "label1", "group": "grp1", "color": "#eebbccdd"},
                {"name": "label2", "group": "grp2", "color": "#aabbccdd"},
            ],
        },
    ],
}

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
                {"name": "label1", "group": "grp", "color": "#aabbccdd"},
            ],
        },
    ],
}

PATCHED_SPICEDB_CREATE_PROJECT = patch.object(
    SpiceDB,
    "create_project",
)


class TestLabelAdditionRestEndpoint:
    def test_label_addition_multiclass_classification(
        self,
        fxt_resource_rest,
        fxt_db_project_service,
    ):
        """
        <b>Description:</b>
        Test label addition on a multi-class classification project through the
        project and annotations endpoints

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        The project and annotation endpoints work as expected on label addition

        <b>Steps</b>
        1. Create a multi-label classification project with two labels
        2. Add 3 images
        3. Annotate the images:
          - first one with first label
          - second one with second label
          - third one with no label
        4. Add a third exclusive label
        5. Verify that the project contains the new label
        6. Verify that the correct event (Kafka message) are generated
        7. Verify that all and only the images with annotations are 'to revisit'
           for the new label.
        """
        session = CTX_SESSION_VAR.get()
        # Hooks for event publishing
        patch_publish_event_project = patch(
            "managers.project_manager.publish_event",
            side_effect=publish_event,
        )
        patch_publish_event_annotation = patch(
            "managers.annotation_manager.publish_event",
            side_effect=publish_event,
        )

        # Step 1: create project
        logger.info("Creating project with data: %s", MULTICLASS_CLASSIFICATION_PROJECT_DATA)
        model_templates = [
            ModelTemplateList().get_by_id("dataset"),
            ModelTemplateList().get_by_id("classification"),
        ]
        project_name = "test_project_label_addition_multiclass_classification"
        project = fxt_db_project_service.create_empty_project(
            name=project_name,
            pipeline_data=MULTICLASS_CLASSIFICATION_PROJECT_DATA,
            model_templates=model_templates,
        )
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=session.workspace_id,
            project_id=project.id_,
            dataset_storage_id=project.training_dataset_storage_id,
        )
        project_labels = fxt_db_project_service.label_schema.get_labels(include_empty=True)
        assert len(project_labels) == 2

        # Step 2: add images
        logger.info("Creating and saving 3 images")
        images = [fxt_db_project_service.create_and_save_random_image(f"image {i}") for i in range(3)]

        # Step 3: annotate
        images_and_labels = zip(
            images,
            (
                (project_labels[0],),
                (project_labels[1],),
                (),
            ),
        )
        scenes_ids: list[ID] = []
        for image, image_labels in images_and_labels:
            if image_labels:
                logger.info("Creating annotation for %s", image.name)
                scene = fxt_db_project_service.create_and_save_random_annotation_scene(
                    image=image, labels=image_labels, full_size_rectangle=True
                )
                scenes_ids.append(scene.id_)

        # Step 4: add a new label
        new_label_data = {
            "name": "label3",
            "group": "grp",
            "color": "#bbbbccdd",
            "revisit_affected_annotations": True,
        }
        updated_pipeline_data = deepcopy(MULTICLASS_CLASSIFICATION_PROJECT_DATA)
        updated_pipeline_data["tasks"][0]["id"] = project.tasks[0].id_
        updated_pipeline_data["tasks"][1]["id"] = project.tasks[1].id_
        for label_data in updated_pipeline_data["tasks"][1]["labels"]:
            label_id = next(label.id_ for label in project_labels if label.name == label_data["name"])
            label_data["id"] = label_id
            label_data["revisit_affected_annotations"] = True
        updated_pipeline_data["tasks"][1]["labels"].append(new_label_data)
        updated_pipeline_data["connections"][0]["from"] = project.tasks[0].id_
        updated_pipeline_data["connections"][0]["to"] = project.tasks[1].id_
        project_update_request_body = {
            "name": project.name,
            "id": str(project.id_),
            "pipeline": updated_pipeline_data,
        }
        project_update_endpoint = (
            f"/api/v1/organizations/{str(session.organization_id)}/workspaces/{str(session.workspace_id)}"
            "/projects/{project.id_}"
        )
        logger.info("Adding new label with data: %s", new_label_data)
        with (
            patch_publish_event_project as patched_pub_proj,
            patch_publish_event_annotation as patched_pub_ann,
            PATCHED_SPICEDB_CREATE_PROJECT,
        ):
            project_update_response = fxt_resource_rest.put(
                project_update_endpoint,
                json=project_update_request_body,
                headers={"x-auth-request-access-token": "testing"},
            )
        assert project_update_response.status_code == HTTPStatus.OK

        # Step 5: verify that the project contains the new label
        logger.info("Checking the presence of the new label in the project REST view")
        project_update_response_body = project_update_response.json()
        assert len(project_update_response_body["pipeline"]["tasks"][1]["labels"]) == 3
        fxt_db_project_service.reload_label_schema()
        project_labels = fxt_db_project_service.label_schema.get_labels(include_empty=True)
        assert len(project_labels) == 3
        # Step 6: check that the expected Kafka message is sent
        patched_pub_proj.assert_called_once_with(
            topic="project_updates",
            body={
                "workspace_id": session.workspace_id,
                "project_id": str(project.id_),
            },
            key=str(project.id_).encode(),
            headers_getter=ANY,
        )
        susp_ann_scene_repo = SuspendedAnnotationScenesRepo(dataset_storage_identifier)
        latest_suspended_scene = susp_ann_scene_repo.get_one(latest=True)
        patched_pub_ann.assert_called_once_with(
            topic="annotation_scenes_to_revisit",
            body={
                "workspace_id": session.workspace_id,
                "project_id": project.id_,
                "dataset_storage_id": project.training_dataset_storage_id,
                "suspended_scenes_descriptor_id": str(latest_suspended_scene.id_),
            },
            key=str(latest_suspended_scene.id_).encode(),
            headers_getter=ANY,
        )

        # Step 7: check that the images with annotations are 'to revisit'
        for i, image in enumerate(images):
            # TODO CVS-88275 re-enable check after fixing the response code
            # assert annotation_get_response.status_code == HTTPStatus.NO_CONTENT
            if i != 2:  # unannotated image
                logger.info("Pulling the annotation scene of %s", image.name)
                annotation_get_endpoint = (
                    f"/api/v1/organizations/{str(session.organization_id)}/workspaces/{str(session.workspace_id)}/projects/{project.id_}"
                    f"/datasets/{project.training_dataset_storage_id}/media/images/{image.id_}/annotations/latest"
                )
                with PATCHED_SPICEDB_CREATE_PROJECT:
                    annotation_get_response = fxt_resource_rest.get(
                        annotation_get_endpoint,
                    )
                assert annotation_get_response.status_code == HTTPStatus.OK
                logger.info("Verifying the state of the annotation scene of %s", image.name)
                annotation_get_response_body = annotation_get_response.json()
                task_annotation_state = annotation_get_response_body["annotation_state_per_task"][0]["state"]
                labels_to_revisit_full_scene = annotation_get_response_body["labels_to_revisit_full_scene"]
                labels_to_revisit_annotation = annotation_get_response_body["annotations"][0]["labels_to_revisit"]
                assert task_annotation_state == "to_revisit"
                assert not labels_to_revisit_full_scene
                assert labels_to_revisit_annotation

    def test_label_addition_multilabel_classification(
        self,
        fxt_resource_rest,
        fxt_db_project_service,
    ):
        """
        <b>Description:</b>
        Test label addition on a multi-label classification project through the
        project and annotations endpoints

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        The project and annotation endpoints work as expected on label addition

        <b>Steps</b>
        1. Create a multi-label classification project with two labels
        2. Add 4 images
        3. Annotate the images:
          - first one with both labels
          - second one with one label
          - third one with no label
        4. Add a third non-exclusive label
        5. Verify that the project contains the new label
        6. Verify that the correct event (Kafka message) are generated
        7. Verify that all and only the images with annotations are 'to revisit'
           for the new label.
        """
        session = CTX_SESSION_VAR.get()
        # Hooks for event publishing
        patch_publish_event_project = patch(
            "managers.project_manager.publish_event",
            side_effect=publish_event,
        )
        patch_publish_event_annotation = patch(
            "managers.annotation_manager.publish_event",
            side_effect=publish_event,
        )

        # Step 1: create project
        logger.info("Creating project with data: %s", MULTILABEL_CLASSIFICATION_PROJECT_DATA)
        project_name = "test_project_label_addition_multilabel_classification"
        model_templates = [
            ModelTemplateList().get_by_id("dataset"),
            ModelTemplateList().get_by_id("classification"),
        ]
        project = fxt_db_project_service.create_empty_project(
            name=project_name,
            pipeline_data=MULTILABEL_CLASSIFICATION_PROJECT_DATA,
            model_templates=model_templates,
        )
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=session.workspace_id,
            project_id=project.id_,
            dataset_storage_id=project.training_dataset_storage_id,
        )
        project_labels = fxt_db_project_service.label_schema.get_labels(include_empty=True)
        assert len(project_labels) == 3
        assert project_labels[2].is_empty
        empty_label = project_labels[2]

        # Step 2: add images
        logger.info("Creating and saving 4 images")
        images = [fxt_db_project_service.create_and_save_random_image(f"image {i}") for i in range(4)]

        # Step 3: annotate
        images_and_labels = zip(
            images,
            (
                (project_labels[0], project_labels[1]),
                (project_labels[0],),
                (empty_label,),
                (),
            ),
        )
        scenes_ids: list[ID] = []
        for image, image_labels in images_and_labels:
            if image_labels:
                logger.info("Creating annotation for %s", image.name)
                scene = fxt_db_project_service.create_and_save_random_annotation_scene(
                    image=image, labels=image_labels, full_size_rectangle=True
                )
                scenes_ids.append(scene.id_)

        # Step 4: add a new label
        new_label_data = {
            "name": "label3",
            "group": "grp3",
            "color": "#bbbbccdd",
            "revisit_affected_annotations": True,
        }
        updated_pipeline_data = deepcopy(MULTILABEL_CLASSIFICATION_PROJECT_DATA)
        updated_pipeline_data["tasks"][0]["id"] = project.tasks[0].id_
        updated_pipeline_data["tasks"][1]["id"] = project.tasks[1].id_
        for label_data in updated_pipeline_data["tasks"][1]["labels"]:
            label_id = next(label.id_ for label in project_labels if label.name == label_data["name"])
            label_data["id"] = label_id
        updated_pipeline_data["tasks"][1]["labels"].append(new_label_data)
        updated_pipeline_data["connections"][0]["from"] = project.tasks[0].id_
        updated_pipeline_data["connections"][0]["to"] = project.tasks[1].id_
        project_update_request_body = {
            "name": project.name,
            "id": str(project.id_),
            "pipeline": updated_pipeline_data,
        }
        project_update_endpoint = (
            f"/api/v1/organizations/{str(session.organization_id)}/workspaces/{str(session.workspace_id)}"
            f"/projects/{project.id_}"
        )
        logger.info("Adding new label with data: %s", new_label_data)
        with (
            patch_publish_event_project as patched_pub_proj,
            patch_publish_event_annotation as patched_pub_ann,
            PATCHED_SPICEDB_CREATE_PROJECT,
        ):
            project_update_response = fxt_resource_rest.put(
                project_update_endpoint,
                json=project_update_request_body,
                headers={"x-auth-request-access-token": "testing"},
            )
        assert project_update_response.status_code == HTTPStatus.OK

        # Step 5: verify that the project contains the new label
        logger.info("Checking the presence of the new label in the project REST view")
        project_update_response_body = project_update_response.json()
        assert len(project_update_response_body["pipeline"]["tasks"][1]["labels"]) == 4
        fxt_db_project_service.reload_label_schema()
        project_labels = fxt_db_project_service.label_schema.get_labels(include_empty=True)
        assert len(project_labels) == 4

        # Step 6: check that the expected Kafka message is sent
        patched_pub_proj.assert_called_once_with(
            topic="project_updates",
            body={
                "workspace_id": session.workspace_id,
                "project_id": str(project.id_),
            },
            key=str(project.id_).encode(),
            headers_getter=ANY,
        )
        patched_pub_ann.assert_called_once_with(
            topic="annotation_scenes_to_revisit",
            body={
                "workspace_id": session.workspace_id,
                "project_id": project.id_,
                "dataset_storage_id": project.training_dataset_storage_id,
                "suspended_scenes_descriptor_id": ANY,
            },
            key=ANY,
            headers_getter=ANY,
        )
        descriptor_id = ID(patched_pub_ann.call_args.kwargs["key"].decode())
        desc_repo = SuspendedAnnotationScenesRepo(dataset_storage_identifier)
        descriptor = desc_repo.get_by_id(descriptor_id)
        assert set(descriptor.scenes_ids) == set(scenes_ids)

        # Step 7: check that the images with annotations are 'to revisit'
        for i, image in enumerate(images):
            # TODO CVS-88275 re-enable check after fixing the response code
            # assert annotation_get_response.status_code == HTTPStatus.NO_CONTENT
            if i != 3:  # unannotated image
                logger.info("Pulling the annotation scene of %s", image.name)
                annotation_get_endpoint = (
                    f"/api/v1/organizations/{str(session.organization_id)}/workspaces/{str(session.workspace_id)}/projects/{project.id_}"
                    f"/datasets/{project.training_dataset_storage_id}/media/images/{image.id_}/annotations/latest"
                )
                with PATCHED_SPICEDB_CREATE_PROJECT:
                    annotation_get_response = fxt_resource_rest.get(
                        annotation_get_endpoint,
                        headers={"x-auth-request-access-token": "testing"},
                    )
                assert annotation_get_response.status_code == HTTPStatus.OK
                logger.info("Verifying the state of the annotation scene of %s", image.name)
                annotation_get_response_body = annotation_get_response.json()
                task_annotation_state = annotation_get_response_body["annotation_state_per_task"][0]["state"]
                labels_to_revisit_full_scene = annotation_get_response_body["labels_to_revisit_full_scene"]
                labels_to_revisit_annotation = annotation_get_response_body["annotations"][0]["labels_to_revisit"]
                assert task_annotation_state == "to_revisit"
                assert not labels_to_revisit_full_scene
                assert labels_to_revisit_annotation == [project_labels[-1].id_]

    def test_label_addition_detection(
        self,
        fxt_resource_rest,
        fxt_db_project_service,
    ):
        """
        <b>Description:</b>
        Test label addition on a detection project through the project and annotations endpoints

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        The project and annotation endpoints work as expected on label addition

        <b>Steps</b>
        1. Create a detection project with one labels
        2. Add 3 images
        3. Annotate the images:
          - first one with one annotation with the first label
          - second one with the empty label
          - third one with no label
        4. Add a third non-exclusive label
        5. Verify that the project contains the new label
        6. Verify that the correct event (Kafka message) are generated
        7. Verify that all and only the images with annotations are 'to revisit'
           for the new label.
        """
        session = CTX_SESSION_VAR.get()
        # Hooks for event publishing
        patch_publish_event_project = patch(
            "managers.project_manager.publish_event",
            side_effect=publish_event,
        )
        patch_publish_event_annotation = patch(
            "managers.annotation_manager.publish_event",
            side_effect=publish_event,
        )

        # Step 1: create project
        logger.info("Creating project with data: %s", DETECTION_PROJECT_DATA)
        project_name = "test_project_label_addition_detection"
        model_templates = [
            ModelTemplateList().get_by_id("dataset"),
            ModelTemplateList().get_by_id("detection"),
        ]
        project = fxt_db_project_service.create_empty_project(
            name=project_name,
            pipeline_data=DETECTION_PROJECT_DATA,
            model_templates=model_templates,
        )
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=session.workspace_id,
            project_id=project.id_,
            dataset_storage_id=project.training_dataset_storage_id,
        )
        project_labels = fxt_db_project_service.label_schema.get_labels(include_empty=True)
        assert len(project_labels) == 2
        assert project_labels[1].is_empty
        empty_label = project_labels[1]

        # Step 2: add images
        logger.info("Creating and saving 3 images")
        images = [fxt_db_project_service.create_and_save_random_image(f"image {i}") for i in range(3)]

        # Step 3: annotate
        images_and_labels = zip(
            images,
            (
                (project_labels[0],),
                (empty_label,),
                (),
            ),
        )
        scenes_ids: list[ID] = []
        for image, image_labels in images_and_labels:
            if image_labels:
                logger.info("Creating annotation for %s", image.name)
                scene = fxt_db_project_service.create_and_save_random_annotation_scene(image=image, labels=image_labels)
                scenes_ids.append(scene.id_)

        # Step 4: add a new label
        new_label_data = {
            "name": "label2",
            "group": "grp",
            "color": "#ccbbccdd",
            "revisit_affected_annotations": True,
        }
        updated_pipeline_data = deepcopy(DETECTION_PROJECT_DATA)
        updated_pipeline_data["tasks"][0]["id"] = project.tasks[0].id_
        updated_pipeline_data["tasks"][1]["id"] = project.tasks[1].id_
        for label_data in updated_pipeline_data["tasks"][1]["labels"]:
            label_id = next(label.id_ for label in project_labels if label.name == label_data["name"])
            label_data["id"] = label_id
        updated_pipeline_data["tasks"][1]["labels"].append(new_label_data)
        updated_pipeline_data["connections"][0]["from"] = project.tasks[0].id_
        updated_pipeline_data["connections"][0]["to"] = project.tasks[1].id_
        project_update_request_body = {
            "name": project.name,
            "id": str(project.id_),
            "pipeline": updated_pipeline_data,
        }
        project_update_endpoint = (
            f"/api/v1/organizations/{str(session.organization_id)}/workspaces/{str(session.workspace_id)}"
            f"/projects/{project.id_}"
        )
        logger.info("Adding new label with data: %s", new_label_data)
        with (
            patch_publish_event_project as patched_pub_proj,
            patch_publish_event_annotation as patched_pub_ann,
            PATCHED_SPICEDB_CREATE_PROJECT,
        ):
            project_update_response = fxt_resource_rest.put(
                project_update_endpoint,
                json=project_update_request_body,
                headers={"x-auth-request-access-token": "testing"},
            )
        assert project_update_response.status_code == HTTPStatus.OK

        # Step 5: verify that the project contains the new label
        logger.info("Checking the presence of the new label in the project REST view")
        project_update_response_body = project_update_response.json()
        assert len(project_update_response_body["pipeline"]["tasks"][1]["labels"]) == 3
        fxt_db_project_service.reload_label_schema()
        project_labels = fxt_db_project_service.label_schema.get_labels(include_empty=True)
        assert len(project_labels) == 3

        # Step 6: check that the expected Kafka message is sent
        patched_pub_proj.assert_called_once_with(
            topic="project_updates",
            body={
                "workspace_id": session.workspace_id,
                "project_id": str(project.id_),
            },
            key=str(project.id_).encode(),
            headers_getter=ANY,
        )
        patched_pub_ann.assert_called_once_with(
            topic="annotation_scenes_to_revisit",
            body={
                "workspace_id": session.workspace_id,
                "project_id": project.id_,
                "dataset_storage_id": project.training_dataset_storage_id,
                "suspended_scenes_descriptor_id": ANY,
            },
            key=ANY,
            headers_getter=ANY,
        )
        descriptor_id = ID(patched_pub_ann.call_args.kwargs["key"].decode())
        desc_repo = SuspendedAnnotationScenesRepo(dataset_storage_identifier)
        descriptor = desc_repo.get_by_id(descriptor_id)
        assert set(descriptor.scenes_ids) == set(scenes_ids)

        # Step 7: check that the images with annotations are 'to revisit'
        for i, image in enumerate(images):
            # TODO CVS-88275 re-enable check after fixing the response code
            # assert annotation_get_response.status_code == HTTPStatus.NO_CONTENT
            if i != 2:  # unannotated image
                logger.info("Pulling the annotation scene of %s", image.name)
                annotation_get_endpoint = (
                    f"/api/v1/organizations/{str(session.organization_id)}/workspaces/{str(session.workspace_id)}/projects/{project.id_}"
                    f"/datasets/{project.training_dataset_storage_id}/media/images/{image.id_}/annotations/latest"
                )
                with PATCHED_SPICEDB_CREATE_PROJECT:
                    annotation_get_response = fxt_resource_rest.get(
                        annotation_get_endpoint,
                        headers={"x-auth-request-access-token": "testing"},
                    )

                assert annotation_get_response.status_code == HTTPStatus.OK
                logger.info("Verifying the state of the annotation scene of %s", image.name)
                annotation_get_response_body = annotation_get_response.json()
                task_annotation_state = annotation_get_response_body["annotation_state_per_task"][0]["state"]
                labels_to_revisit_full_scene = annotation_get_response_body["labels_to_revisit_full_scene"]
                labels_to_revisit_annotation = annotation_get_response_body["annotations"][0]["labels_to_revisit"]
                assert task_annotation_state == "to_revisit"
                assert labels_to_revisit_full_scene == [project_labels[-1].id_]
                assert not labels_to_revisit_annotation

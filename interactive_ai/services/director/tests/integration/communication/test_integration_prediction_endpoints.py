# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import json
from http import HTTPStatus
from unittest.mock import patch

import pytest
from testfixtures.comparison import compare

from communication.exceptions import NoModelTrainedException
from service.project_service import ProjectService

from geti_types import ID, VideoFrameIdentifier
from iai_core.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core.entities.label import Label
from iai_core.entities.model import NullModel
from iai_core.entities.scored_label import LabelSource, ScoredLabel
from iai_core.repos import AnnotationSceneRepo
from iai_core.services import ModelService


@pytest.fixture
def fxt_annotation_with_model_id(fxt_rectangle_annotation, fxt_ote_id):
    """
    Creates an annotation with a scored label that has a label source with the given
    model ID.
    """

    def _build_annotation(label: Label, model_id: ID = fxt_ote_id(999)) -> Annotation:
        return Annotation(
            shape=fxt_rectangle_annotation.shape,
            labels=[
                ScoredLabel(
                    label_id=label.id_,
                    is_empty=label.is_empty,
                    label_source=LabelSource(model_id=model_id),
                )
            ],
            id_=AnnotationSceneRepo.generate_id(),
        )

    yield _build_annotation


class TestPredictionEndpoints:
    def test_image_prediction_endpoint_no_model_trained_error(
        self,
        fxt_director_app,
        fxt_organization_id,
        fxt_project_with_detection_task,
        fxt_dataset_storage,
        fxt_media_identifier,
    ) -> None:
        project = fxt_project_with_detection_task
        workspace_id = project.workspace_id
        dataset_storage_id = fxt_dataset_storage.id_
        dummy_prediction_type = "latest"
        endpoint = (
            f"/api/v1/organizations/{fxt_organization_id}/workspaces/{workspace_id}/projects/{project.id_}/datasets/"
            f"{dataset_storage_id}/media/images/{fxt_media_identifier.media_id}/"
            f"predictions/{dummy_prediction_type}"
        )

        with (
            patch.object(ProjectService, "get_by_id", return_value=project),
            patch.object(
                ProjectService,
                "get_dataset_storage_by_id",
                return_value=fxt_dataset_storage,
            ),
            patch.object(ModelService, "get_inference_active_model", return_value=NullModel()),
        ):
            response = fxt_director_app.get(endpoint)
        assert response.status_code == NoModelTrainedException().http_status

    def test_video_frame_prediction_endpoint_no_model_trained_error(
        self,
        fxt_director_app,
        fxt_organization_id,
        fxt_project_with_detection_task,
        fxt_dataset_storage,
        fxt_media_identifier,
    ) -> None:
        project = fxt_project_with_detection_task
        workspace_id = project.workspace_id
        dataset_storage_id = fxt_dataset_storage.id_
        dummy_prediction_type = "latest"
        dummy_frame_id = 1
        endpoint = (
            f"/api/v1/organizations/{fxt_organization_id}/workspaces/{workspace_id}/projects/{project.id_}/datasets/"
            f"{dataset_storage_id}/media/videos/{fxt_media_identifier.media_id}/frames/"
            f"{dummy_frame_id}/predictions/{dummy_prediction_type}"
        )

        with (
            patch.object(ProjectService, "get_by_id", return_value=project),
            patch.object(
                ProjectService,
                "get_dataset_storage_by_id",
                return_value=fxt_dataset_storage,
            ),
            patch.object(ModelService, "get_inference_active_model", return_value=NullModel()),
        ):
            response = fxt_director_app.get(endpoint)

        assert response.status_code == NoModelTrainedException().http_status

    @pytest.mark.parametrize("frameskip", (5, None))
    @patch(
        "service.prediction_service.MAX_N_ANNOTATIONS_RETURNED",
        new=3,
        autospec=False,
    )
    def test_video_prediction_endpoint(
        self,
        fxt_director_app,
        fxt_organization_id,
        fxt_db_project_service,
        fxt_label,
        fxt_annotation_with_model_id,
        frameskip,
    ) -> None:
        """
        <b>Description:</b>
        Check that the video prediction endpoint returns the expected predictions and
        with the pagination.

        <b>Input data:</b>
        Detection project with predictions for the following video frame indices:
        [1, 10, 20, 30, 60, 85, 95, 120, 150]

        <b>Expected results:</b>
        Test passes if the correct video frames predictions are returned (fist page):
            - Predictions with frameskip=5 -> [10, 20, 30]
            - Predictions with frameskip=None (frameskip=fps instead) -> [30, 60, 120]

        <b>Steps</b>
        1. Create a project
        2. Create and save a video and predictions for a number of video frames
        4. Checks that "auto" and "online" mode are disabled
        5. Checks that the returned predictions are correct
        6. Checks that pagination properties are correct
        """
        project = fxt_db_project_service.create_annotated_detection_project(num_images_per_label=1)
        workspace_id = project.workspace_id
        dataset_storage = project.get_training_dataset_storage()
        total_frames = 180
        video = fxt_db_project_service.create_and_save_random_video(name="test_video", number_of_frames=total_frames)
        ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
        sample_annotation = next(iter(ann_scene_repo.get_all()))
        fxt_db_project_service.create_and_save_model()
        task_node = project.get_trainable_task_nodes()[0]
        inference_model = ModelService.get_inference_active_model(
            project_identifier=project.identifier,
            task_node_id=task_node.id_,
        )
        annotation_with_model_id = fxt_annotation_with_model_id(label=fxt_label, model_id=inference_model.id_)

        start_frame = 10
        end_frame = 150
        pagination_query = f"?start_frame={start_frame}&end_frame={end_frame}"
        expected_next_page = (
            f"/api/v1/organizations/{fxt_organization_id}/workspaces/{workspace_id}/projects/{project.id_}"
            f"/datasets/{dataset_storage.id_}/media/videos/{video.id_}"
            f"/predictions/latest?label_only=false"
        )
        if frameskip is not None:
            pagination_query += f"&frameskip={frameskip}"
            expected_next_page += f"&start_frame={30 + frameskip}&end_frame={end_frame}&frameskip={frameskip}"
        else:
            expected_next_page += f"&start_frame={int(120 + video.fps)}&end_frame={end_frame}"

        # Save predictions for some frames
        expected_prediction_ids = []
        for i in [1, 10, 20, 30, 60, 85, 95, 120, 150]:
            prediction = AnnotationScene(
                kind=AnnotationSceneKind.PREDICTION,
                media_identifier=VideoFrameIdentifier(video.id_, i),
                media_height=sample_annotation.media_height,
                media_width=sample_annotation.media_width,
                id_=AnnotationSceneRepo.generate_id(),
                annotations=[annotation_with_model_id],
            )
            skip = frameskip if frameskip is not None else video.fps
            if start_frame <= i <= end_frame and i % skip == 0:
                expected_prediction_ids.append(prediction.id_)
            fxt_db_project_service.save_annotation_scene_and_state(prediction)

        endpoint = (
            f"/api/v1/organizations/{fxt_organization_id}/workspaces/{workspace_id}/projects/{project.id_}/datasets/"
            f"{dataset_storage.id_}/media/videos/{video.id_}/predictions"
        )

        # Check that "latest" returns predictions
        result = fxt_director_app.get(f"{endpoint}/latest{pagination_query}")

        assert result.status_code == HTTPStatus.OK
        result_data = json.loads(result.content)
        result_predictions_ids = {ID(pred["id"]) for pred in result_data["video_predictions"]}
        assert result_predictions_ids == set(expected_prediction_ids[:3])
        compare(
            result_data["next_page"],
            expected_next_page,
        )

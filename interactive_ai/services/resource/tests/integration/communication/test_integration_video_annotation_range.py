# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

from iai_core_py.repos import (
    AnnotationSceneRepo,
    LabelRepo,
    LabelSchemaRepo,
    ProjectRepo,
    VideoAnnotationRangeRepo,
    VideoRepo,
)


class TestVideoAnnotationRangeIntegration:
    def test_create_and_update_range(
        self,
        request,
        fxt_resource_rest,
        fxt_session_ctx,
        fxt_project_with_classification_task,
        fxt_classification_label_schema,
        fxt_video_entity,
    ) -> None:
        """
        The test verifies the correctness of the video annotation ranges and annotations
        after updating a whole range of frames.

        Steps:
          1. Initialize a project with a video
          2. POST /range_annotation to annotate some video frames
          3. GET /range_annotation to check that the video annotation range is correctly returned
          4. GET /annotations/latest on a frame within the annotation range
          5. GET /annotations/latest on a frame outside the annotation range
          6. POST /range_annotation to update the range
          7. GET /range_annotation to check that the video annotation range info is consistent with the update
          8. GET /annotations/latest on a frame within the new annotation range, but outside the old one
          9. GET /annotations/latest on a frame outside the new annotation range, but within the old one
        """
        request.addfinalizer(
            lambda: AnnotationSceneRepo(
                fxt_project_with_classification_task.get_training_dataset_storage().identifier
            ).delete_all()
        )
        request.addfinalizer(
            lambda: VideoAnnotationRangeRepo(
                fxt_project_with_classification_task.get_training_dataset_storage().identifier
            ).delete_all()
        )
        label_0, label_1 = fxt_classification_label_schema.get_labels(include_empty=True)[:2]
        get_range_ann_endpoint = (
            f"/api/v1/organizations/{fxt_session_ctx.organization_id}"
            f"/workspaces/{str(fxt_session_ctx.workspace_id)}"
            f"/projects/{str(fxt_project_with_classification_task.id_)}"
            f"/datasets/{str(fxt_project_with_classification_task.training_dataset_storage_id)}"
            f"/media/videos/{str(fxt_video_entity.id_)}/range_annotation"
        )
        post_range_ann_endpoint = get_range_ann_endpoint + "?skip_frame=1"
        get_ann_endpoint = (
            f"/api/v1/organizations/{fxt_session_ctx.organization_id}"
            f"/workspaces/{str(fxt_session_ctx.workspace_id)}"
            f"/projects/{str(fxt_project_with_classification_task.id_)}"
            f"/datasets/{str(fxt_project_with_classification_task.training_dataset_storage_id)}"
            f"/media/videos/{str(fxt_video_entity.id_)}"
        ) + "/frames/{frame_index}/annotations/latest"

        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project_with_classification_task),
            patch.object(VideoRepo, "get_by_id", return_value=fxt_video_entity),
            patch.object(LabelSchemaRepo, "get_latest", return_value=fxt_classification_label_schema),
            patch.object(LabelSchemaRepo, "get_latest_view_by_task", return_value=fxt_classification_label_schema),
        ):
            # POST /range_annotation to annotate frames [1-3]
            range_data_1 = {"range_labels": [{"start_frame": 1, "end_frame": 3, "label_ids": [str(label_0.id_)]}]}
            post_result = fxt_resource_rest.post(post_range_ann_endpoint, json=range_data_1)
            assert post_result.status_code == 200

            # GET /range_annotation
            get_result = fxt_resource_rest.get(get_range_ann_endpoint)
            assert get_result.status_code == 200
            assert get_result.json()["range_labels"] == range_data_1["range_labels"]

            # GET /annotations -> expect frame 2 (within range) to be annotated, and frame 4 (outside range) unannotated
            get_result = fxt_resource_rest.get(get_ann_endpoint.format(frame_index=2))
            assert get_result.status_code == 200
            assert get_result.json()["annotations"]
            get_result = fxt_resource_rest.get(get_ann_endpoint.format(frame_index=4))
            assert get_result.status_code == 204

            # POST /range_annotation to annotate frames [3-5]
            range_data_2 = {"range_labels": [{"start_frame": 3, "end_frame": 5, "label_ids": [str(label_1.id_)]}]}
            post_result = fxt_resource_rest.post(post_range_ann_endpoint, json=range_data_2)
            assert post_result.status_code == 200

            # GET /range_annotation
            get_result = fxt_resource_rest.get(get_range_ann_endpoint)
            assert get_result.status_code == 200
            assert get_result.json()["range_labels"] == range_data_2["range_labels"]

            # GET /annotations -> expect frame 4 (within range) to be annotated, and frame 2 (outside range) unannotated
            get_result = fxt_resource_rest.get(get_ann_endpoint.format(frame_index=2))
            assert get_result.status_code == 204
            get_result = fxt_resource_rest.get(get_ann_endpoint.format(frame_index=4))
            assert get_result.status_code == 200
            assert get_result.json()["annotations"]

    def test_create_range_and_update_single_frames(
        self,
        request,
        fxt_resource_rest,
        fxt_session_ctx,
        fxt_project_with_classification_task,
        fxt_classification_label_schema,
        fxt_video_entity,
        fxt_mongo_id,
    ) -> None:
        """
        The test verifies the correctness of the video annotation ranges and annotations
        after updating individual frames.

        1. Initialize a project with a video
        2. POST /range_annotation to annotate some video frames
        3. POST /annotations to annotate a frame within the annotation range
        4. POST /annotations to annotate a frame outside the annotation range
        5. POST /annotations to unannotate (i.e. remove existing labels from) a frame within the annotation range
        6. GET /range_annotation to check that the video annotation range info is consistent with the update
        """
        request.addfinalizer(
            lambda: AnnotationSceneRepo(
                fxt_project_with_classification_task.get_training_dataset_storage().identifier
            ).delete_all()
        )
        request.addfinalizer(
            lambda: VideoAnnotationRangeRepo(
                fxt_project_with_classification_task.get_training_dataset_storage().identifier
            ).delete_all()
        )
        label_0, label_1 = fxt_classification_label_schema.get_labels(include_empty=True)[:2]
        get_range_ann_endpoint = (
            f"/api/v1/organizations/{fxt_session_ctx.organization_id}"
            f"/workspaces/{str(fxt_session_ctx.workspace_id)}"
            f"/projects/{str(fxt_project_with_classification_task.id_)}"
            f"/datasets/{str(fxt_project_with_classification_task.training_dataset_storage_id)}"
            f"/media/videos/{str(fxt_video_entity.id_)}/range_annotation"
        )
        post_range_ann_endpoint = get_range_ann_endpoint + "?skip_frame=1"
        post_ann_endpoint = (
            f"/api/v1/organizations/{fxt_session_ctx.organization_id}"
            f"/workspaces/{str(fxt_session_ctx.workspace_id)}"
            f"/projects/{str(fxt_project_with_classification_task.id_)}"
            f"/datasets/{str(fxt_project_with_classification_task.training_dataset_storage_id)}"
            f"/media/videos/{str(fxt_video_entity.id_)}"
        ) + "/frames/{frame_index}/annotations"

        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project_with_classification_task),
            patch.object(VideoRepo, "get_by_id", return_value=fxt_video_entity),
            patch.object(LabelSchemaRepo, "get_latest", return_value=fxt_classification_label_schema),
            patch.object(LabelSchemaRepo, "get_latest_view_by_task", return_value=fxt_classification_label_schema),
        ):
            # POST /range_annotation to annotate frames [0-3] with label 0
            range_data_1 = {"range_labels": [{"start_frame": 0, "end_frame": 3, "label_ids": [str(label_0.id_)]}]}
            post_result = fxt_resource_rest.post(post_range_ann_endpoint, json=range_data_1)
            assert post_result.status_code == 200

            # POST /annotations to annotate frame 3 with label 1
            full_box_data = {
                "type": "RECTANGLE",
                "x": 0,
                "y": 0,
                "width": fxt_video_entity.width,
                "height": fxt_video_entity.height,
            }
            ann_data_frame_3 = {
                "media_identifier": {"type": "video_frame", "video_id": str(fxt_video_entity.id_), "frame_index": 3},
                "annotations": [
                    {
                        "id": str(fxt_mongo_id(10)),
                        "shape": full_box_data,
                        "labels": [{"id": str(label_1.id_)}],
                    }
                ],
            }
            post_result = fxt_resource_rest.post(post_ann_endpoint.format(frame_index=3), json=ann_data_frame_3)
            assert post_result.status_code == 200

            # POST /annotations to annotate frame 4 with label 0
            ann_data_frame_4 = {
                "media_identifier": {"type": "video_frame", "video_id": str(fxt_video_entity.id_), "frame_index": 4},
                "annotations": [
                    {
                        "id": str(fxt_mongo_id(11)),
                        "shape": full_box_data,
                        "labels": [{"id": str(label_0.id_)}],
                    }
                ],
            }
            post_result = fxt_resource_rest.post(post_ann_endpoint.format(frame_index=4), json=ann_data_frame_4)
            assert post_result.status_code == 200

            # POST /annotations to unannotate frame 2
            ann_data_frame_2 = {
                "media_identifier": {"type": "video_frame", "video_id": str(fxt_video_entity.id_), "frame_index": 2},
                "annotations": [],
            }
            post_result = fxt_resource_rest.post(post_ann_endpoint.format(frame_index=2), json=ann_data_frame_2)
            assert post_result.status_code == 200

            # GET /range_annotation
            get_result = fxt_resource_rest.get(get_range_ann_endpoint)
            assert get_result.status_code == 200
            assert get_result.json()["range_labels"] == [
                {"start_frame": 0, "end_frame": 1, "label_ids": [str(label_0.id_)]},
                {"start_frame": 3, "end_frame": 3, "label_ids": [str(label_1.id_)]},
                {"start_frame": 4, "end_frame": 4, "label_ids": [str(label_0.id_)]},
            ]

    def test_update_range_over_non_key_frames(
        self,
        request,
        fxt_resource_rest,
        fxt_session_ctx,
        fxt_project_with_classification_task,
        fxt_classification_label_schema,
        fxt_video_entity,
        fxt_mongo_id,
    ) -> None:
        """
        The test verifies the correctness of the video annotation ranges and annotations
        after creating individual annotations at non-key frames (non-multiple of fps) and
        overriding them with ranges.

        1. Initialize a project with a video
        2. POST /annotations to annotate a frame
        3. POST /range_annotation to annotate a range of frames such that the previously annotated frame
           is included in the range, without being one of its key-frames though.
        """
        request.addfinalizer(
            lambda: AnnotationSceneRepo(
                fxt_project_with_classification_task.get_training_dataset_storage().identifier
            ).delete_all()
        )
        request.addfinalizer(
            lambda: VideoAnnotationRangeRepo(
                fxt_project_with_classification_task.get_training_dataset_storage().identifier
            ).delete_all()
        )
        label_0, label_1 = fxt_classification_label_schema.get_labels(include_empty=True)[:2]
        get_range_ann_endpoint = (
            f"/api/v1/organizations/{fxt_session_ctx.organization_id}"
            f"/workspaces/{str(fxt_session_ctx.workspace_id)}"
            f"/projects/{str(fxt_project_with_classification_task.id_)}"
            f"/datasets/{str(fxt_project_with_classification_task.training_dataset_storage_id)}"
            f"/media/videos/{str(fxt_video_entity.id_)}/range_annotation"
        )
        post_range_ann_endpoint = get_range_ann_endpoint + "?skip_frame=3"  # note: create ann every 3 frames
        post_ann_endpoint = (
            f"/api/v1/organizations/{fxt_session_ctx.organization_id}"
            f"/workspaces/{str(fxt_session_ctx.workspace_id)}"
            f"/projects/{str(fxt_project_with_classification_task.id_)}"
            f"/datasets/{str(fxt_project_with_classification_task.training_dataset_storage_id)}"
            f"/media/videos/{str(fxt_video_entity.id_)}"
        ) + "/frames/{frame_index}/annotations"
        get_ann_endpoint = post_ann_endpoint + "/latest"

        def _new_labelrepo_get_by_id(_self, id_):
            if id_ == label_0.id_:
                return label_0
            if id_ == label_1.id_:
                return label_1
            raise ValueError(f"unrecognized label id {id_}")

        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project_with_classification_task),
            patch.object(VideoRepo, "get_by_id", return_value=fxt_video_entity),
            patch.object(LabelSchemaRepo, "get_latest", return_value=fxt_classification_label_schema),
            patch.object(LabelSchemaRepo, "get_latest_view_by_task", return_value=fxt_classification_label_schema),
            patch.object(LabelRepo, "get_by_id", new=_new_labelrepo_get_by_id),
        ):
            # POST /annotations to annotate frame 4 with label 0
            full_box_data = {
                "type": "RECTANGLE",
                "x": 0,
                "y": 0,
                "width": fxt_video_entity.width,
                "height": fxt_video_entity.height,
            }
            ann_data_frame_4 = {
                "media_identifier": {"type": "video_frame", "video_id": str(fxt_video_entity.id_), "frame_index": 4},
                "annotations": [
                    {
                        "id": str(fxt_mongo_id(11)),
                        "shape": full_box_data,
                        "labels": [{"id": str(label_0.id_)}],
                    }
                ],
            }
            post_result = fxt_resource_rest.post(post_ann_endpoint.format(frame_index=4), json=ann_data_frame_4)
            assert post_result.status_code == 200

            # POST /range_annotation to annotate frames [3-7] with label 1
            range_data_1 = {"range_labels": [{"start_frame": 3, "end_frame": 7, "label_ids": [str(label_1.id_)]}]}
            post_result = fxt_resource_rest.post(post_range_ann_endpoint, json=range_data_1)
            assert post_result.status_code == 200

            # GET /annotations at frame 4 -> expect label 1
            get_result = fxt_resource_rest.get(get_ann_endpoint.format(frame_index=4))
            assert get_result.status_code == 200
            frame_4_annotations = get_result.json()["annotations"]
            assert len(frame_4_annotations) == 1
            assert len(frame_4_annotations[0]["labels"]) == 1
            frame_4_label = frame_4_annotations[0]["labels"][0]
            assert frame_4_label["id"] == label_1.id_

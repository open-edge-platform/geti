# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from http import HTTPStatus
from unittest.mock import patch

import pytest

from managers.project_manager import ProjectManager

from iai_core.repos import DatasetRepo, VideoRepo


class TestMediaFilterRESTEndpoint:
    @pytest.mark.parametrize("fxt_filled_image_dataset_storage", [99], indirect=True)
    def test_media_filter_endpoint_images(
        self,
        fxt_organization_id,
        fxt_resource_rest,
        fxt_filled_image_dataset_storage,
        fxt_project,
    ):
        """
        Tests the media filter endpoint.

        A dataset storage filled with 99 images is used along with an empty filter which
        matches all images. The test then requests all results for this filter with a
        limit of 10 items per page and asserts that it iterates over 10 pages.
        """
        with (
            patch.object(
                ProjectManager,
                "get_project_by_id",
                return_value=fxt_project,
            ),
            patch.object(
                ProjectManager,
                "get_dataset_storage_by_id",
                return_value=fxt_filled_image_dataset_storage,
            ),
        ):
            data = {
                "next_page": f"/api/v1/organizations/{str(fxt_organization_id)}"
                f"/workspaces/{str(fxt_filled_image_dataset_storage.workspace_id)}"
                f"/projects/{fxt_project.id_}/datasets/{fxt_filled_image_dataset_storage.id_}/media:query?limit=10&"
                "sort_by=media_upload_date"
            }

            for _ in range(10):
                result = fxt_resource_rest.post(data["next_page"], json={})
                assert result.status_code == HTTPStatus.OK
                data = result.json()

            # Check that the final page does not include a url to a next page
            assert not data.__contains__("next_page")
            # Check that the last page contains the final 9 items
            assert len(data["media"]) == 9
            # Check that the last item is the last image in the dataset storage
            assert data["media"][8]["name"] == "image 99"

            assert data["total_matched_images"] == 99
            assert data["total_images"] == 99
            assert data["total_matched_videos"] == 0
            assert data["total_matched_video_frames"] == 0
            assert data["total_videos"] == 0

    @pytest.mark.parametrize("fxt_filled_video_dataset_storage", [1], indirect=True)
    def test_media_filter_endpoint_videos(
        self,
        fxt_organization_id,
        fxt_resource_rest,
        fxt_filled_video_dataset_storage,
        fxt_project,
    ) -> None:
        """
        Tests the dataset filter endpoint on a dataset storage filled with 1 video
        with 4 frames. An annotation based filter is passed that matches 2 of the 4
        frames. This is asserted at the end of the test.
        """
        with (
            patch.object(
                ProjectManager,
                "get_project_by_id",
                return_value=fxt_project,
            ),
            patch.object(
                ProjectManager,
                "get_dataset_storage_by_id",
                return_value=fxt_filled_video_dataset_storage,
            ),
        ):
            url = (
                f"/api/v1/organizations/{str(fxt_organization_id)}/workspaces/{str(fxt_project.workspace_id)}"
                f"/projects/{fxt_project.id_}/datasets/{fxt_filled_video_dataset_storage.id_}/media:query"
            )

            result = fxt_resource_rest.post(
                url,
                json={
                    "rules": [
                        {
                            "field": "label_id",
                            "operator": "not_equal",
                            "value": "01234567890123456789abcd",
                        },
                    ]
                },
            )
            assert result.status_code == HTTPStatus.OK

            assert result.json()["media"][0]["matched_frames"] == 2

    @pytest.mark.parametrize("fxt_filled_video_dataset_storage", [1], indirect=True)
    def test_media_video_frames_filter_endpoint(
        self,
        fxt_organization_id,
        fxt_resource_rest,
        fxt_filled_video_dataset_storage,
        fxt_project,
    ) -> None:
        """
        Tests the video frame filter endpoint on a dataset storage filled with 1 video
        with 4 frames. An annotation based filter is passed that matches 2 of the 4
        frames. This is asserted at the end of the test.
        """
        ds_identifier = fxt_filled_video_dataset_storage.identifier
        video = next(iter(VideoRepo(ds_identifier).get_all()))
        with (
            patch.object(
                ProjectManager,
                "get_project_by_id",
                return_value=fxt_project,
            ),
            patch.object(
                ProjectManager,
                "get_dataset_storage_by_id",
                return_value=fxt_filled_video_dataset_storage,
            ),
        ):
            url = (
                f"/api/v1/organizations/{str(fxt_organization_id)}/workspaces/{str(fxt_project.workspace_id)}"
                f"/projects/{fxt_project.id_}/datasets/{fxt_filled_video_dataset_storage.id_}/"
                f"media/videos/{video.id_}:query"
            )

            result = fxt_resource_rest.post(url, json={})
            assert result.status_code == HTTPStatus.OK

            assert result.json()["total_matched_video_frames"] == 2

    @pytest.mark.parametrize("fxt_filled_image_dataset_storage", [99], indirect=True)
    def test_dataset_media_filter_endpoint_images(
        self,
        fxt_organization_id,
        fxt_resource_rest,
        fxt_filled_image_dataset_storage,
        fxt_project,
    ):
        """
        Tests the dataset media filter endpoint.

        A dataset storage filled with 99 images is used along with an empty filter which
        matches all images. The test then requests all results for this filter with a
        limit of 10 items per page and asserts that it iterates over 10 pages.
        """
        dataset_repo = DatasetRepo(fxt_filled_image_dataset_storage.identifier)
        dataset = next(iter(dataset_repo.get_all()))
        with (
            patch.object(
                ProjectManager,
                "get_project_by_id",
                return_value=fxt_project,
            ),
            patch.object(
                ProjectManager,
                "get_dataset_storage_by_id",
                return_value=fxt_filled_image_dataset_storage,
            ),
        ):
            data = {
                "next_page": f"/api/v1/organizations/{str(fxt_organization_id)}"
                f"/workspaces/{str(fxt_project.workspace_id)}"
                f"/projects/{fxt_project.id_}/datasets/{fxt_filled_image_dataset_storage.id_}/"
                f"training_revisions/{dataset.id_}/media:query?limit=10"
            }

            for _ in range(10):
                result = fxt_resource_rest.post(data["next_page"], json={})
                assert result.status_code == HTTPStatus.OK
                data = result.json()

            # Check that the final page does not include a url to a next page
            assert not data.__contains__("next_page")
            # Check that the last page contains the final 9 items
            assert len(data["media"]) == 9
            # Check that the last item is the last image in the dataset storage
            assert data["media"][8]["name"] == "image 99"

            assert data["total_matched_images"] == 99
            assert data["total_images"] == 99
            assert data["total_matched_videos"] == 0
            assert data["total_matched_video_frames"] == 0
            assert data["total_videos"] == 0

    @pytest.mark.parametrize("fxt_filled_video_dataset_storage", [1], indirect=True)
    def test_media_video_frame_filter_in_dataset_endpoint(
        self,
        fxt_organization_id,
        fxt_resource_rest,
        fxt_filled_video_dataset_storage,
        fxt_project,
    ) -> None:
        """
        Tests the dataset video frame filter endpoint on a dataset storage filled with
        1 video with 4 frames. An annotation based filter is passed that matches all
        frames
        """
        ds_identifier = fxt_filled_video_dataset_storage.identifier
        video = next(iter(VideoRepo(ds_identifier).get_all()))
        dataset = next(iter(DatasetRepo(ds_identifier).get_all()))
        with (
            patch.object(
                ProjectManager,
                "get_project_by_id",
                return_value=fxt_project,
            ),
            patch.object(
                ProjectManager,
                "get_dataset_storage_by_id",
                return_value=fxt_filled_video_dataset_storage,
            ),
        ):
            url = (
                f"/api/v1/organizations/{str(fxt_organization_id)}/workspaces/{str(fxt_project.workspace_id)}"
                f"/projects/{fxt_project.id_}/datasets/{fxt_filled_video_dataset_storage.id_}/"
                f"training_revisions/{dataset.id_}/"
                f"media/videos/{video.id_}:query"
            )

            result = fxt_resource_rest.post(
                url,
                json={
                    "rules": [
                        {
                            "field": "label_id",
                            "operator": "not_equal",
                            "value": "01234567890123456789abcd",
                        },
                    ]
                },
            )
            assert result.status_code == HTTPStatus.OK

            assert result.json()["total_matched_video_frames"] == 4

    @pytest.mark.parametrize("fxt_filled_video_dataset_storage", [1], indirect=True)
    def test_media_video_filter_endpoint(
        self,
        fxt_organization_id,
        fxt_resource_rest,
        fxt_filled_video_dataset_storage,
        fxt_project,
    ) -> None:
        """
        Integration test to verify video filter endpoint returns videos
        """
        with (
            patch.object(
                ProjectManager,
                "get_project_by_id",
                return_value=fxt_project,
            ),
            patch.object(
                ProjectManager,
                "get_dataset_storage_by_id",
                return_value=fxt_filled_video_dataset_storage,
            ),
        ):
            url = (
                f"/api/v1/organizations/{str(fxt_organization_id)}/workspaces/{str(fxt_project.workspace_id)}"
                f"/projects/{fxt_project.id_}/datasets/{fxt_filled_video_dataset_storage.id_}/"
                f"media:query"
            )

            result = fxt_resource_rest.post(
                url,
                json={
                    "rules": [
                        {
                            "field": "media_name",
                            "operator": "not_equal",
                            "value": "test_name",
                        },
                    ]
                },
            )
            assert result.status_code == HTTPStatus.OK

            assert result.json()["total_matched_videos"] == 1

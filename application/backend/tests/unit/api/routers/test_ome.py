# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import status

from app.api.dependencies import (
    get_dataset_service,
    get_inference_media_limit,
    get_media_prediction_service,
    get_media_service,
    get_ome_service,
)
from app.api.schemas.media import SetMediaAnnotations
from app.models import DatasetItem, DatasetItemAnnotation, DatasetItemSubset, LabelReference, Rectangle
from app.models.media import (
    IndexRange,
    MediaListPredictionRequest,
    MediaPredictionRequest,
    MediaType,
    OmeFormat,
    OmeImage,
    OmePlane,
    PlaneRange,
)
from app.models.ome import ChannelMapping, OmeChannel, OmeChannelView, OmeContainerFormat, OmeImageInfo, RgbTarget
from app.services import (
    DatasetService,
    MediaPredictionService,
    MediaService,
    OmeService,
    ResourceNotFoundError,
    ResourceType,
)
from app.services.media_service import InvalidImageError
from app.services.ome.rendering import InvalidChannelSettingsError
from app.services.ome_service import OmePlaneOutOfRangeError


@pytest.fixture
def fxt_media_service(fxt_app) -> MagicMock:
    media_service = MagicMock(spec=MediaService)
    fxt_app.dependency_overrides[get_media_service] = lambda: media_service
    return media_service


@pytest.fixture
def fxt_ome_service(fxt_app) -> MagicMock:
    ome_service = MagicMock(spec=OmeService)
    fxt_app.dependency_overrides[get_ome_service] = lambda: ome_service
    return ome_service


@pytest.fixture
def fxt_dataset_service(fxt_app) -> MagicMock:
    dataset_service = MagicMock(spec=DatasetService)
    fxt_app.dependency_overrides[get_dataset_service] = lambda: dataset_service
    return dataset_service


@pytest.fixture
def fxt_ome_image() -> OmeImage:
    return OmeImage(
        id=uuid4(),
        type=MediaType.OME_IMAGE,
        project_id=uuid4(),
        name="plate_A01",
        format=OmeFormat.OME_TIFF,
        width=48,
        height=32,
        size=4096,
        plane_count=6,
        source_id=None,
    )


@pytest.fixture
def fxt_ome_plane(fxt_ome_image) -> OmePlane:
    return OmePlane(
        id=uuid4(),
        type=MediaType.OME_PLANE,
        project_id=fxt_ome_image.project_id,
        name="plate_A01_z2_t1",
        format="png",  # type: ignore[arg-type]
        width=48,
        height=32,
        size=1024,
        ome_image_id=fxt_ome_image.id,
        z_index=2,
        t_index=1,
        source_id=None,
    )


@pytest.fixture
def fxt_annotations() -> list[DatasetItemAnnotation]:
    return [
        DatasetItemAnnotation(
            labels=[LabelReference(id=uuid4())], shape=Rectangle(type="rectangle", x=0, y=0, width=10, height=10)
        )
    ]


def _media_url(media_id) -> str:
    return f"/api/projects/{uuid4()}/dataset/media/{media_id}"


class TestOmeMediaEndpoints:
    @pytest.mark.parametrize("file_name, ome_format", [("plate.ome.tiff", OmeFormat.OME_TIFF), ("x.OME.TIF", None)])
    def test_add_ome_image(
        self,
        fxt_get_project,
        fxt_media_service,
        fxt_ome_service,
        fxt_dataset_service,
        fxt_ome_image,
        fxt_client,
        file_name,
        ome_format,
    ):
        fxt_ome_service.create_ome_image.return_value = fxt_ome_image

        response = fxt_client.post(
            f"/api/projects/{uuid4()}/dataset/media",
            files={"file": (file_name, BytesIO(b"123"), "image/tiff")},
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["type"] == "ome_image"
        assert response.json()["plane_count"] == 6
        kwargs = fxt_ome_service.create_ome_image.call_args.kwargs
        assert kwargs["name"] == file_name.split(".")[0]
        assert kwargs["ome_format"] == (ome_format or OmeFormat.OME_TIF)
        fxt_media_service.create_image.assert_not_called()
        fxt_dataset_service.create_dataset_item.assert_not_called()

    def test_add_invalid_ome_image(self, fxt_get_project, fxt_ome_service, fxt_dataset_service, fxt_client):
        fxt_ome_service.create_ome_image.side_effect = InvalidImageError("The file is not an OME-TIFF image.")

        response = fxt_client.post(
            f"/api/projects/{uuid4()}/dataset/media",
            files={"file": ("plate.ome.tiff", BytesIO(b"123"), "image/tiff")},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert "not an OME-TIFF" in response.json()["detail"]

    def test_annotate_unannotated_plane_creates_it(
        self,
        fxt_get_project,
        fxt_media_service,
        fxt_ome_service,
        fxt_dataset_service,
        fxt_ome_image,
        fxt_ome_plane,
        fxt_annotations,
        fxt_client,
    ):
        fxt_media_service.get_media_by_id.return_value = fxt_ome_image
        fxt_ome_service.get_plane.return_value = None
        fxt_ome_service.create_plane.return_value = fxt_ome_plane
        fxt_dataset_service.set_dataset_item_annotations.return_value = MagicMock(
            spec=DatasetItem,
            annotation_data=fxt_annotations,
            user_reviewed=True,
            prediction_model_id=None,
            subset=DatasetItemSubset.UNASSIGNED,
        )

        response = fxt_client.post(
            f"{_media_url(fxt_ome_image.id)}/annotations?z=2&t=1",
            json=SetMediaAnnotations(annotations=fxt_annotations).model_dump(mode="json"),
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["media_id"] == str(fxt_ome_plane.id)
        fxt_ome_service.get_plane.assert_called_once_with(project=fxt_get_project, ome_image=fxt_ome_image, z=2, t=1)
        fxt_ome_service.create_plane.assert_called_once_with(project=fxt_get_project, ome_image=fxt_ome_image, z=2, t=1)
        fxt_dataset_service.create_dataset_item.assert_called_once_with(
            project_id=fxt_get_project.id, task=fxt_get_project.task, media=fxt_ome_plane, user_reviewed=True
        )
        assert fxt_dataset_service.set_dataset_item_annotations.call_args.kwargs["dataset_item_id"] == fxt_ome_plane.id

    def test_annotate_existing_plane_reuses_it(
        self,
        fxt_get_project,
        fxt_media_service,
        fxt_ome_service,
        fxt_dataset_service,
        fxt_ome_image,
        fxt_ome_plane,
        fxt_annotations,
        fxt_client,
    ):
        fxt_media_service.get_media_by_id.return_value = fxt_ome_image
        fxt_ome_service.get_plane.return_value = fxt_ome_plane
        fxt_dataset_service.set_dataset_item_annotations.return_value = MagicMock(
            spec=DatasetItem,
            annotation_data=fxt_annotations,
            user_reviewed=True,
            prediction_model_id=None,
            subset=DatasetItemSubset.UNASSIGNED,
        )

        response = fxt_client.post(
            f"{_media_url(fxt_ome_image.id)}/annotations?z=2&t=1",
            json=SetMediaAnnotations(annotations=fxt_annotations).model_dump(mode="json"),
        )

        assert response.status_code == status.HTTP_201_CREATED
        fxt_ome_service.create_plane.assert_not_called()
        fxt_dataset_service.create_dataset_item.assert_not_called()

    def test_annotate_ome_image_without_plane_coordinates(
        self, fxt_get_project, fxt_media_service, fxt_ome_service, fxt_ome_image, fxt_annotations, fxt_client
    ):
        fxt_media_service.get_media_by_id.return_value = fxt_ome_image

        response = fxt_client.post(
            f"{_media_url(fxt_ome_image.id)}/annotations",
            json=SetMediaAnnotations(annotations=fxt_annotations).model_dump(mode="json"),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        fxt_ome_service.create_plane.assert_not_called()

    def test_annotate_plane_out_of_range(
        self, fxt_get_project, fxt_media_service, fxt_ome_service, fxt_ome_image, fxt_annotations, fxt_client
    ):
        fxt_media_service.get_media_by_id.return_value = fxt_ome_image
        fxt_ome_service.get_plane.side_effect = OmePlaneOutOfRangeError("Z index 9 is out of range")

        response = fxt_client.post(
            f"{_media_url(fxt_ome_image.id)}/annotations?z=9",
            json=SetMediaAnnotations(annotations=fxt_annotations).model_dump(mode="json"),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "out of range" in response.json()["detail"]

    @pytest.mark.parametrize("method", ["get", "delete"])
    def test_unannotated_plane_annotations_not_found(
        self,
        fxt_get_project,
        fxt_media_service,
        fxt_ome_service,
        fxt_dataset_service,
        fxt_ome_image,
        fxt_client,
        method,
    ):
        fxt_media_service.get_media_by_id.return_value = fxt_ome_image
        fxt_ome_service.get_plane.return_value = None

        response = getattr(fxt_client, method)(f"{_media_url(fxt_ome_image.id)}/annotations?t=0")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        fxt_dataset_service.delete_dataset_item_annotations.assert_not_called()


@pytest.fixture
def fxt_ome_info() -> OmeImageInfo:
    return OmeImageInfo(
        container_format=OmeContainerFormat.OME_TIFF,
        size_x=48,
        size_y=32,
        size_z=3,
        size_c=2,
        size_t=2,
        dimension_order="XYZCT",
        pixel_type="uint16",
        channels=[OmeChannel(index=0, name="DAPI"), OmeChannel(index=1, name="GFP")],
        channel_mapping=[ChannelMapping(channel=0, target=RgbTarget.RED, window_min=0, window_max=65535)],
        pyramid_levels=[],
    )


class TestOmePlanePrediction:
    def test_plane_range_counts_against_inference_limit(self, fxt_app, fxt_get_project, fxt_client):
        prediction_service = MagicMock(spec=MediaPredictionService)
        fxt_app.dependency_overrides[get_media_prediction_service] = lambda: prediction_service
        fxt_app.dependency_overrides[get_inference_media_limit] = lambda: 5
        plane_range = PlaneRange(z=IndexRange(start=0, end=2), t=IndexRange(start=0, end=1))
        request = MediaListPredictionRequest(
            model_id=uuid4(),
            media=[MediaPredictionRequest(media_id=uuid4(), range=None, plane_range=plane_range)],
            device="AUTO",
        )

        response = fxt_client.post(
            f"/api/projects/{uuid4()}/dataset/media:predict", json=request.model_dump(mode="json")
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "requested number is 6" in response.json()["detail"]
        prediction_service.predict_media.assert_not_called()


class TestOmeEndpoints:
    def test_get_ome_image_info(self, fxt_get_project, fxt_ome_service, fxt_ome_info, fxt_client):
        fxt_ome_service.get_info.return_value = fxt_ome_info

        response = fxt_client.get(f"{_media_url(uuid4())}/ome")

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert (body["size_z"], body["size_c"], body["size_t"]) == (3, 2, 2)
        assert [c["name"] for c in body["channels"]] == ["DAPI", "GFP"]
        assert "channel_mapping" not in body

    def test_get_ome_image_info_not_ome(self, fxt_get_project, fxt_ome_service, fxt_client):
        media_id = uuid4()
        fxt_ome_service.get_info.side_effect = ResourceNotFoundError(ResourceType.MEDIA, str(media_id))

        response = fxt_client.get(f"{_media_url(media_id)}/ome")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_channel_view(self, fxt_get_project, fxt_ome_service, fxt_client):
        fxt_ome_service.get_channel_view.return_value = OmeChannelView(settings=[], is_default=True)

        response = fxt_client.get(f"{_media_url(uuid4())}/channel-view")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"settings": [], "is_default": True}

    def test_set_channel_view(self, fxt_get_project, fxt_ome_service, fxt_client):
        setting = {"channel": 1, "target": "green", "enabled": True, "window_min": 10.0, "window_max": 500.0}
        fxt_ome_service.set_channel_view.side_effect = lambda project_id, media_id, settings: OmeChannelView(
            settings=settings, is_default=False
        )

        response = fxt_client.put(f"{_media_url(uuid4())}/channel-view", json={"settings": [setting]})

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"settings": [setting], "is_default": False}

    @pytest.mark.parametrize(
        "setting",
        [
            pytest.param({"channel": 0, "target": "red", "window_min": 5, "window_max": 5}, id="empty_window"),
            pytest.param({"channel": 0, "target": "purple", "window_min": 0, "window_max": 5}, id="unknown_target"),
        ],
    )
    def test_set_invalid_channel_view_payload(self, fxt_get_project, fxt_ome_service, fxt_client, setting):
        response = fxt_client.put(f"{_media_url(uuid4())}/channel-view", json={"settings": [setting]})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        fxt_ome_service.set_channel_view.assert_not_called()

    def test_set_channel_view_inconsistent_with_image(self, fxt_get_project, fxt_ome_service, fxt_client):
        fxt_ome_service.set_channel_view.side_effect = InvalidChannelSettingsError("Channel 9 does not exist")

        response = fxt_client.put(
            f"{_media_url(uuid4())}/channel-view",
            json={"settings": [{"channel": 9, "target": "red", "window_min": 0, "window_max": 5}]},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert "does not exist" in response.json()["detail"]

    def test_render_plane_with_etag(self, fxt_get_project, fxt_ome_service, fxt_client, tmp_path: Path):
        rendered = tmp_path / "render.png"
        rendered.write_bytes(b"png")
        fxt_ome_service.render_plane.return_value = (rendered, "abc123")
        url = f"{_media_url(uuid4())}/render?z=1&t=1&level=0"

        response = fxt_client.get(url)
        not_modified = fxt_client.get(url, headers={"If-None-Match": '"abc123"'})

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["etag"] == '"abc123"'
        assert response.content == b"png"
        assert not_modified.status_code == status.HTTP_304_NOT_MODIFIED

    def test_render_plane_out_of_range(self, fxt_get_project, fxt_ome_service, fxt_client):
        fxt_ome_service.render_plane.side_effect = OmePlaneOutOfRangeError("T index 5 is out of range")

        response = fxt_client.get(f"{_media_url(uuid4())}/render?t=5")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_annotated_planes(self, fxt_get_project, fxt_ome_service, fxt_ome_image, fxt_ome_plane, fxt_client):
        fxt_ome_service.get_ome_image.return_value = fxt_ome_image
        fxt_ome_service.list_annotated_planes.return_value = [fxt_ome_plane]

        response = fxt_client.get(f"{_media_url(fxt_ome_image.id)}/planes")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [{"media_id": str(fxt_ome_plane.id), "z_index": 2, "t_index": 1}]

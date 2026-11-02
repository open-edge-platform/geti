# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import numpy as np
import pytest
from PIL import Image as PILImage
from sqlalchemy.orm import Session

from app.models import BatchInferenceMedia, DatasetItemAnnotation, Project
from app.models.media import (
    Image,
    IndexRange,
    MediaListPredictionRequest,
    MediaPredictionRequest,
    MediaType,
    NotAnnotatedOmePlane,
    OmeFormat,
    OmeImage,
    OmePlane,
    PlaneRange,
    VideoRange,
)
from app.models.ome import OmeChannel, OmeContainerFormat, OmeImageInfo
from app.models.system import DeviceInfo, DeviceType
from app.services import LabelService, MediaPredictionService, MediaService, OmeService
from app.services.inference import InferenceServer
from app.services.media_numpy_loader import MediaNumpyLoader
from app.services.media_prediction_service import VideoRangeError
from app.services.ome_service import OmePlaneOutOfRangeError
from app.services.sam import MediaSegmentService

DEVICE = DeviceInfo(type=DeviceType.CPU, name="CPU", memory=None, index=None)


@pytest.fixture
def fxt_ome_image() -> OmeImage:
    return OmeImage(
        id=uuid4(),
        type=MediaType.OME_IMAGE,
        project_id=uuid4(),
        name="plate",
        format=OmeFormat.OME_TIFF,
        width=8,
        height=4,
        size=100,
        plane_count=6,
        source_id=None,
    )


@pytest.fixture
def fxt_ome_info() -> OmeImageInfo:
    return OmeImageInfo(
        container_format=OmeContainerFormat.OME_TIFF,
        size_x=8,
        size_y=4,
        size_z=3,
        size_c=1,
        size_t=2,
        dimension_order="XYZCT",
        pixel_type="uint8",
        channels=[OmeChannel(index=0)],
        channel_mapping=[],
        pyramid_levels=[],
    )


@pytest.fixture
def fxt_services(fxt_ome_image, fxt_ome_info):
    media_service = MagicMock(spec=MediaService)
    media_service.get_media_by_ids.return_value = [fxt_ome_image]
    ome_service = MagicMock(spec=OmeService)
    ome_service.get_info.return_value = fxt_ome_info
    ome_service.get_plane.return_value = None
    ome_service.render_training_plane.return_value = PILImage.new("RGB", (8, 4))
    inference_server = MagicMock(spec=InferenceServer)
    numpy_loader = MagicMock(spec=MediaNumpyLoader)
    service = MediaPredictionService(
        label_service=MagicMock(spec=LabelService),
        media_service=media_service,
        inference_server=inference_server,
        inference_keyframe_stride=1,
        media_numpy_loader=numpy_loader,
        ome_service=ome_service,
        db_session=MagicMock(spec=Session),
    )
    return service, ome_service, inference_server, numpy_loader


def _request(media_id, range=None, plane_range=None) -> MediaListPredictionRequest:
    return MediaListPredictionRequest(
        model_id=uuid4(),
        device="cpu",
        confidence_threshold=None,
        media=[MediaPredictionRequest(media_id=media_id, range=range, plane_range=plane_range)],
    )


class TestOmePlanePrediction:
    def test_predict_plane_range(self, fxt_services, fxt_ome_image):
        service, ome_service, inference_server, numpy_loader = fxt_services
        annotated_plane = MagicMock(spec=OmePlane, id=uuid4())
        # Plane (z=1, t=1) is already annotated: its stored binary is used instead of rendering it again
        ome_service.get_plane.side_effect = lambda project, ome_image, z, t: (
            annotated_plane if (z, t) == (1, 1) else None
        )
        numpy_loader.load_media_binary.return_value = np.zeros((4, 8, 3), np.uint8)
        prediction = [MagicMock(spec=DatasetItemAnnotation)]
        inference_server.infer_batch.side_effect = lambda inputs, **_: {
            (i.media_id, i.frame_index): prediction for i in inputs
        }
        plane_range = PlaneRange(z=IndexRange(start=0, end=2, stride=1), t=IndexRange(start=1, end=1))

        result = service.predict_media(
            project=MagicMock(spec=Project, id=uuid4()),
            request=_request(fxt_ome_image.id, plane_range=plane_range),
            device=DEVICE,
        )

        assert [p.media for p in result.predictions] == [
            BatchInferenceMedia(id=fxt_ome_image.id, frame_index=3),
            BatchInferenceMedia(id=fxt_ome_image.id, frame_index=4),
            BatchInferenceMedia(id=fxt_ome_image.id, frame_index=5),
        ]
        inputs = inference_server.infer_batch.call_args.kwargs["inputs"]
        assert [(i.media_id, i.frame_index, i.data.shape) for i in inputs] == [
            (fxt_ome_image.id, 3, (4, 8, 3)),
            (fxt_ome_image.id, 4, (4, 8, 3)),
            (fxt_ome_image.id, 5, (4, 8, 3)),
        ]
        assert ome_service.render_training_plane.call_count == 2
        numpy_loader.load_media_binary.assert_called_once()

    def test_predict_ome_image_without_plane_range(self, fxt_services, fxt_ome_image):
        service, *_ = fxt_services

        with pytest.raises(VideoRangeError, match="plane range"):
            service.predict_media(
                project=MagicMock(spec=Project, id=uuid4()), request=_request(fxt_ome_image.id), device=DEVICE
            )

    @pytest.mark.parametrize("with_video_range", [True, False])
    def test_plane_range_only_for_ome_images(self, fxt_services, fxt_ome_image, with_video_range):
        service, _, _, _ = fxt_services
        if not with_video_range:
            image = MagicMock(spec=Image, id=fxt_ome_image.id, type=MediaType.IMAGE)
            service._media_service.get_media_by_ids.return_value = [image]
        request = _request(
            fxt_ome_image.id,
            range=VideoRange(start_frame=0, end_frame=0, stride=1) if with_video_range else None,
            plane_range=PlaneRange(),
        )

        with pytest.raises(VideoRangeError, match="only for OME images"):
            service.predict_media(project=MagicMock(spec=Project, id=uuid4()), request=request, device=DEVICE)

    def test_plane_out_of_range(self, fxt_services, fxt_ome_image):
        service, ome_service, _, _ = fxt_services
        ome_service.get_plane.side_effect = OmePlaneOutOfRangeError("Z index 7 is out of range")

        with pytest.raises(VideoRangeError, match="out of range"):
            service.predict_media(
                project=MagicMock(spec=Project, id=uuid4()),
                request=_request(fxt_ome_image.id, plane_range=PlaneRange(z=IndexRange(start=7, end=7))),
                device=DEVICE,
            )

    def test_index_range_validation(self):
        with pytest.raises(ValueError, match="must be >="):
            IndexRange(start=3, end=1)
        assert PlaneRange(z=IndexRange(start=0, end=4, stride=2), t=IndexRange(start=0, end=1)).count == 6


class TestOmePlaneSegmentation:
    def test_encode_not_annotated_plane_renders_it(self, fxt_ome_image):
        ome_service = MagicMock(spec=OmeService)
        ome_service.render_training_plane.return_value = PILImage.new("RGB", (8, 4))
        service = MediaSegmentService(
            media_service=MagicMock(spec=MediaService),
            media_numpy_loader=MagicMock(spec=MediaNumpyLoader),
            model_xml_path=Path("mobile_sam.encoder.xml"),
            db_session=MagicMock(spec=Session),
            ome_service=ome_service,
        )
        project = MagicMock(spec=Project, id=uuid4())
        model = MagicMock(return_value=np.zeros((1, 256, 64, 64), np.float32))

        with patch.object(service, "_load_model", return_value=model):
            service.encode_media(
                project=project,
                media=NotAnnotatedOmePlane(ome_image=fxt_ome_image, z_index=2, t_index=1),
                device=DEVICE,
            )

        ome_service.render_training_plane.assert_called_once_with(
            project_id=project.id, ome_image=fxt_ome_image, z=2, t=1
        )
        assert model.call_args.args[0].shape == (4, 8, 3)

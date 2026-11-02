# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import bisect
from dataclasses import dataclass, field
from uuid import UUID

import numpy as np
from loguru import logger
from sqlalchemy.orm import Session

from app.models import (
    BatchInferenceInput,
    BatchInferenceMedia,
    BatchInferencePrediction,
    BatchInferenceResult,
    DatasetItemAnnotation,
    Image,
    Project,
    VideoFrame,
)
from app.models.media import (
    Media,
    MediaListPredictionRequest,
    MediaType,
    OmeImage,
    OmePlane,
    PlaneRange,
    Video,
    VideoRange,
)
from app.models.system import DeviceInfo

from .base import BaseSessionManagedService, ResourceError, ResourceNotFoundError, ResourceType
from .inference import InferenceServer
from .label_service import LabelService
from .media_numpy_loader import MediaNumpyLoader
from .media_service import MediaService
from .ome_service import OmePlaneOutOfRangeError, OmeService


@dataclass(frozen=True)
class Frame:
    frame_index: int
    skip: bool
    annotated_frame: VideoFrame | None = None


class VideoRangeError(ResourceError):
    def __init__(self, resource_id: str, message: str):
        super().__init__(ResourceType.MEDIA, resource_id, message)


@dataclass(frozen=True)
class OmePlaneTarget:
    ome_image: OmeImage
    z_index: int
    t_index: int
    plane_index: int
    annotated_plane: OmePlane | None = None


@dataclass(frozen=True)
class LoadedMedia:
    single_media: list[Image | VideoFrame | OmePlane]
    video_frames: dict[Video, list[Frame]]
    ome_planes: list[OmePlaneTarget] = field(default_factory=list)


class MediaPredictionService(BaseSessionManagedService):
    def __init__(
        self,
        label_service: LabelService,
        media_service: MediaService,
        inference_server: InferenceServer,
        inference_keyframe_stride: int,
        media_numpy_loader: MediaNumpyLoader,
        ome_service: OmeService | None = None,
        db_session: Session | None = None,
    ) -> None:
        super().__init__(db_session)
        self._ome_service = ome_service
        self._label_service = label_service
        self._media_service = media_service
        self._inference_server = inference_server
        self._inference_keyframe_stride = inference_keyframe_stride
        self._media_numpy_loader = media_numpy_loader

    @staticmethod
    def _is_frame_index_to_infer(index: int, frame_indexes: list[int], inference_keyframe_stride: int) -> bool:
        return index == 0 or index == len(frame_indexes) - 1 or index % inference_keyframe_stride == 0

    @staticmethod
    def _get_keyframe_position_stride(inference_keyframe_stride: int, range_stride: int) -> int:
        """
        Convert the keyframe stride, expressed as a distance in video frames, into a stride over the
        positions of the requested frames, so that keyframes are never more than
        `inference_keyframe_stride` video frames apart, regardless of the requested range stride.
        """
        return max(1, inference_keyframe_stride // range_stride)

    def _load_frame_range(self, project: Project, video: Video, video_range: VideoRange) -> list[Frame]:
        video_frames: list[Frame] = []

        frame_indexes = list(range(video_range.start_frame, video_range.end_frame + 1, video_range.stride))
        annotated_frames = self._media_service.search_video_frames_by_video_id_and_indexes(
            project=project, video_id=video.id, frame_indexes=frame_indexes
        )
        keyframe_position_stride = self._get_keyframe_position_stride(
            inference_keyframe_stride=self._inference_keyframe_stride, range_stride=video_range.stride
        )
        for idx, frame_index in enumerate(frame_indexes):
            annotated_frame = next((frame for frame in annotated_frames if frame.frame_index == frame_index), None)
            skip = (
                not MediaPredictionService._is_frame_index_to_infer(
                    index=idx, frame_indexes=frame_indexes, inference_keyframe_stride=keyframe_position_stride
                )
                if keyframe_position_stride > 1
                else False
            )
            video_frames.append(Frame(frame_index=frame_index, annotated_frame=annotated_frame, skip=skip))
        return video_frames

    def _get_ome_service(self) -> OmeService:
        if self._ome_service is None:
            raise RuntimeError("OME images cannot be predicted without an OME service")
        return self._ome_service

    def _load_plane_range(self, project: Project, ome_image: OmeImage, plane_range: PlaneRange) -> list[OmePlaneTarget]:
        ome_service = self._get_ome_service()
        info = ome_service.get_info(project_id=project.id, media_id=ome_image.id)
        targets = []
        for t in plane_range.t.indexes:
            for z in plane_range.z.indexes:
                try:
                    annotated_plane = ome_service.get_plane(project=project, ome_image=ome_image, z=z, t=t)
                except OmePlaneOutOfRangeError as error:
                    raise VideoRangeError(str(ome_image.id), str(error)) from error
                targets.append(
                    OmePlaneTarget(
                        ome_image=ome_image,
                        z_index=z,
                        t_index=t,
                        plane_index=info.plane_index(z, t),
                        annotated_plane=annotated_plane,
                    )
                )
        return targets

    def _load_media(self, project: Project, request: MediaListPredictionRequest) -> LoadedMedia:
        single_media: list[Image | VideoFrame | OmePlane] = []
        video_frames: dict[Video, list[Frame]] = {}
        ome_planes: list[OmePlaneTarget] = []

        media_ids: list[UUID] = [media_request.media_id for media_request in request.media]
        media_list = self._media_service.get_media_by_ids(project_id=project.id, media_ids=media_ids)
        media_dict: dict[UUID, Media] = {media.id: media for media in media_list}

        for media_request in request.media:
            media = media_dict.get(media_request.media_id, None)
            if media is None:
                raise ResourceNotFoundError(ResourceType.MEDIA, str(media_request.media_id))
            if media_request.plane_range is not None:
                if not isinstance(media, OmeImage) or media_request.range is not None:
                    raise VideoRangeError(
                        str(media_request.media_id), "Plane range can be specified only for OME images, without range."
                    )
                ome_planes.extend(self._load_plane_range(project, media, media_request.plane_range))
                continue
            if media_request.range is None:
                if media.type == MediaType.VIDEO:
                    raise VideoRangeError(
                        str(media_request.media_id), "Video cannot be used for predictions, please specify frame range."
                    )
                if media.type == MediaType.OME_IMAGE:
                    raise VideoRangeError(
                        str(media_request.media_id),
                        "OME image cannot be used for predictions, please specify plane range.",
                    )
                single_media.append(media)
            else:
                if media.type != MediaType.VIDEO:
                    raise VideoRangeError(str(media_request.media_id), "Frame range can be specified only for videos.")
                video_frames[media] = self._load_frame_range(
                    project=project, video=media, video_range=media_request.range
                )
        return LoadedMedia(single_media=single_media, video_frames=video_frames, ome_planes=ome_planes)

    def _convert_to_inference_input(self, project: Project, loaded_media: LoadedMedia) -> list[BatchInferenceInput]:
        inputs: list[BatchInferenceInput] = []

        # Process single media (images and already-saved video frames)
        for single_media in loaded_media.single_media:
            data = self._media_numpy_loader.load_media_binary(project_id=project.id, media=single_media)
            inputs.append(BatchInferenceInput(media_id=single_media.id, data=data))

        for video in loaded_media.video_frames:
            frames = loaded_media.video_frames[video]
            annotated_frames: list[Frame] = [
                frame for frame in frames if frame.annotated_frame is not None and not frame.skip
            ]
            for frame in annotated_frames:
                binary_data = self._media_numpy_loader.load_media_binary(
                    project_id=project.id,
                    media=frame.annotated_frame,  # pyrefly: ignore[bad-argument-type]
                )
                inputs.append(BatchInferenceInput(media_id=video.id, data=binary_data, frame_index=frame.frame_index))

            not_annotated_frames: list[Frame] = [
                frame for frame in frames if frame.annotated_frame is None and not frame.skip
            ]
            # Batch-extract not-annotated video frames: one video open/close per video
            frame_indexes = [f.frame_index for f in not_annotated_frames]
            extracted = self._media_service.get_frame_binaries(
                project=project, video=video, frame_indexes=frame_indexes
            )
            for frame in not_annotated_frames:
                binary_data = extracted[frame.frame_index]
                inputs.append(BatchInferenceInput(media_id=video.id, data=binary_data, frame_index=frame.frame_index))

        for target in loaded_media.ome_planes:
            if target.annotated_plane is not None:
                plane_data = self._media_numpy_loader.load_media_binary(
                    project_id=project.id, media=target.annotated_plane
                )
            else:
                plane_image = self._get_ome_service().render_training_plane(
                    project_id=project.id, ome_image=target.ome_image, z=target.z_index, t=target.t_index
                )
                plane_data = np.asarray(plane_image)
            inputs.append(
                BatchInferenceInput(media_id=target.ome_image.id, data=plane_data, frame_index=target.plane_index)
            )

        return inputs

    @staticmethod
    def _find_nearest_keyframe_index(frame_index: int, keyframe_indexes: list[int]) -> int:
        """Find the nearest keyframe index for a given frame index using bisect."""
        pos = bisect.bisect_left(keyframe_indexes, frame_index)
        if pos == 0:
            return keyframe_indexes[0]
        if pos == len(keyframe_indexes):
            return keyframe_indexes[-1]
        before = keyframe_indexes[pos - 1]
        after = keyframe_indexes[pos]
        return before if (frame_index - before) <= (after - frame_index) else after

    def _convert_result(
        self, loaded_media: LoadedMedia, inference_result: dict[tuple[UUID, int | None], list[DatasetItemAnnotation]]
    ) -> BatchInferenceResult:
        predictions: list[BatchInferencePrediction] = []
        for single_media in loaded_media.single_media:
            predictions.append(
                BatchInferencePrediction(
                    media=BatchInferenceMedia(id=single_media.id), prediction=inference_result[(single_media.id, None)]
                )
            )
        for video in loaded_media.video_frames:
            frames = loaded_media.video_frames[video]
            # Collect keyframe predictions (frames that were inferred)
            keyframe_predictions: dict[int, list[DatasetItemAnnotation]] = {
                frame.frame_index: inference_result[(video.id, frame.frame_index)] for frame in frames if not frame.skip
            }

            # Sorted keyframe indexes for nearest-keyframe lookup
            keyframe_indexes = sorted(keyframe_predictions.keys())

            for frame in frames:
                if not frame.skip:
                    prediction = keyframe_predictions[frame.frame_index]
                else:
                    nearest = self._find_nearest_keyframe_index(frame.frame_index, keyframe_indexes)
                    prediction = keyframe_predictions[nearest]
                predictions.append(
                    BatchInferencePrediction(
                        media=BatchInferenceMedia(id=video.id, frame_index=frame.frame_index), prediction=prediction
                    )
                )

        for target in loaded_media.ome_planes:
            predictions.append(
                BatchInferencePrediction(
                    media=BatchInferenceMedia(id=target.ome_image.id, frame_index=target.plane_index),
                    prediction=inference_result[(target.ome_image.id, target.plane_index)],
                )
            )

        return BatchInferenceResult(predictions=predictions)

    def predict_media(
        self,
        project: Project,
        request: MediaListPredictionRequest,
        device: DeviceInfo,
    ) -> BatchInferenceResult:
        """
        Perform batch inference for a number of media. Media can be an image, annotated frame or video frame range.
        Method loads media metadata and binaries with extracting frames from video if needed and passes
        binaries to the inference service.

        Args:
            project: Project object containing project information.
            request: Batch inference request object.
            device: DeviceInfo object containing information about device to run inference on.

        Returns:
            BatchInferenceResult object with list of media prediction results.
        """
        logger.debug("Performing batch inference using model {}", request.model_id)

        loaded_media = self._load_media(project=project, request=request)
        logger.debug(
            "Loaded {} media and {} video frames", len(loaded_media.single_media), len(loaded_media.video_frames)
        )

        inputs = self._convert_to_inference_input(project=project, loaded_media=loaded_media)

        labels = self._label_service.list_all(project_id=project.id)

        result = self._inference_server.infer_batch(
            project_id=project.id,
            model_id=request.model_id,
            model_variant_id=request.model_variant_id,
            device=device,
            labels=labels,
            inputs=inputs,
            confidence_threshold=request.confidence_threshold,
        )
        return self._convert_result(loaded_media=loaded_media, inference_result=result)

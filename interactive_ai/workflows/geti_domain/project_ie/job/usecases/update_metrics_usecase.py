# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module is responsible for migrating the documents and binaries to the latest version after they have been imported
"""

import logging

from geti_telemetry_tools import ENABLE_METRICS
from geti_telemetry_tools.metrics import (
    EmptyInstrumentAttributes,
    convert_pixels,
    images_resolution_histogram,
    videos_frames_histogram,
    videos_resolution_histogram,
)
from geti_types import DatasetStorageIdentifier, ProjectIdentifier
from iai_core.entities.image import Image
from iai_core.entities.video import Video
from iai_core.repos import ImageRepo, ProjectRepo, VideoRepo

logger = logging.getLogger(__name__)


class UpdateMetricsUseCase:
    """
    This class is responsible for updating the metrics after a project has been imported
    """

    @staticmethod
    def update_metrics(project_identifier: ProjectIdentifier) -> None:
        """
        Updates the image and video metrics after a project has been imported

        :param project_identifier: ProjectIdentifier of the project to upgrade
        """
        if not ENABLE_METRICS:
            return

        project_repo = ProjectRepo()
        project = project_repo.get_by_id(id_=project_identifier.project_id)
        for dataset_storage_id in project.dataset_storage_ids:
            dataset_storage_identifier = DatasetStorageIdentifier(
                workspace_id=project_identifier.workspace_id,
                project_id=project_identifier.project_id,
                dataset_storage_id=dataset_storage_id,
            )
            image_repo = ImageRepo(dataset_storage_identifier=dataset_storage_identifier)
            for image in image_repo.get_all():
                UpdateMetricsUseCase._update_image_metrics(image=image)
            video_repo = VideoRepo(dataset_storage_identifier=dataset_storage_identifier)
            for video in video_repo.get_all():
                UpdateMetricsUseCase._update_video_metrics(video=video)

    @staticmethod
    def _update_image_metrics(image: Image) -> None:
        """
        Update metrics relative to images:
          - resolution histogram

        :param image: Uploaded image
        """
        # Compute the size of the image in the unit required by the instrument
        image_resolution = convert_pixels(
            num_pixels=(image.width * image.height),
            unit=images_resolution_histogram.unit,  # type: ignore
        )
        # Record data point
        images_resolution_histogram.record(image_resolution, EmptyInstrumentAttributes().to_dict())

    @staticmethod
    def _update_video_metrics(video: Video) -> None:
        """
        Update metrics relative to videos:
          - resolution histogram
          - frames histogram

        :param video: Uploaded video
        """
        # Compute the size of the video in the unit required by the instrument
        video_resolution = convert_pixels(
            num_pixels=(video.width * video.height),
            unit=videos_resolution_histogram.unit,  # type: ignore
        )
        # Record data point
        videos_resolution_histogram.record(video_resolution, EmptyInstrumentAttributes().to_dict())
        videos_frames_histogram.record(video.total_frames, EmptyInstrumentAttributes().to_dict())

# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import shutil
from pathlib import Path
from typing import BinaryIO
from uuid import UUID, uuid4

import numpy as np
from loguru import logger
from PIL import Image
from sqlalchemy.orm import Session

from app.db.schema import MediaDB, OmeImageDB
from app.models import MediaType, Project
from app.models.media import OmeFormat, OmeImage, OmePlane
from app.models.ome import ChannelDisplaySetting, ChannelMapping, OmeChannelView, OmeImageInfo
from app.repositories import MediaRepository, OmeImageRepository
from app.utils.images import convert_to_jpeg_compatible, crop_to_thumbnail

from .base import BaseSessionManagedService, ResourceNotFoundError, ResourceType
from .media_service import DEFAULT_THUMBNAIL_SIZE, InvalidImageError, MediaService
from .ome.channel_mapping import compute_training_channel_mapping
from .ome.reader import InvalidOmeImageError, MediaStorage, OmeReader, OmeTiffReader
from .ome.rendering import compose_rgb, default_display_settings, settings_hash, validate_display_settings

OME_RENDER_CACHE_DIR = "ome_cache"
PLANE_IMAGE_FORMAT = "png"


class OmePlaneOutOfRangeError(ValueError):
    """Raised when a (z, t) plane or pyramid level does not exist in an OME image."""


class OmeService(BaseSessionManagedService):
    """Ingest, inspect, render and annotate OME images, whose (Z, T) planes are lazily created leaf media."""

    def __init__(
        self,
        data_dir: Path,
        media_service: MediaService,
        reader: OmeReader | None = None,
        db_session: Session | None = None,
    ) -> None:
        super().__init__(db_session)
        self.projects_dir = data_dir / "projects"
        self._media_service = media_service
        self._reader: OmeReader = reader if reader is not None else OmeTiffReader()

    def _dataset_dir(self, project_id: UUID) -> Path:
        return self.projects_dir / f"{project_id}/dataset"

    def _storage(self, project_id: UUID, media: OmeImage | MediaDB) -> MediaStorage:
        return MediaStorage(root=self._media_service.get_media_binary_path(project_id=project_id, media=media))

    @staticmethod
    def render_cache_dir(dataset_dir: Path, media_id: UUID | str) -> Path:
        """Directory holding the cached renders of an OME image."""
        return dataset_dir / OME_RENDER_CACHE_DIR / str(media_id)

    def create_ome_image(self, project_id: UUID, name: str, ome_format: OmeFormat, data: BinaryIO | Path) -> OmeImage:
        """
        Create an OME image media from a stream, or from a file which is moved (not copied) into the dataset.

        Raises:
            InvalidImageError: If the data is not a valid OME image.
        """
        media_id = uuid4()
        dataset_dir = self._dataset_dir(project_id)
        dataset_dir.mkdir(parents=True, exist_ok=True)
        binary_path = dataset_dir / f"{media_id}.{ome_format}"

        source_path: Path | None = None
        if isinstance(data, Path):
            source_path = data
            shutil.move(source_path, binary_path)
        else:
            MediaService._copy_binary(data, binary_path)

        storage = MediaStorage(root=binary_path)
        try:
            parsed = self._reader.parse(storage)
            info = parsed.info
            mid_z, mid_t = info.size_z // 2, info.size_t // 2
            all_channels = list(range(info.size_c))
            lowest_level = max(len(info.pyramid_levels) - 1, 0)
            sample = self._reader.read_plane(storage, z=mid_z, t=mid_t, channels=all_channels, level=lowest_level)
            channel_mapping = compute_training_channel_mapping(
                info, sample_value_range=lambda: (float(np.min(sample)), float(np.max(sample)))
            )
            info = info.model_copy(update={"channel_mapping": channel_mapping})

            display_settings = default_display_settings(info, dict(enumerate(sample)))
            thumbnail = compose_rgb(dict(enumerate(sample)), display_settings)
            self._save_thumbnail(Image.fromarray(thumbnail), dataset_dir / f"{media_id}-thumb.jpg")

            repo = MediaRepository(project_id=str(project_id), db=self.db_session)
            db_media = repo.save(
                MediaDB(
                    id=str(media_id),
                    project_id=str(project_id),
                    type=MediaType.OME_IMAGE,
                    name=name,
                    format=str(ome_format),
                    width=info.size_x,
                    height=info.size_y,
                    frame_count=info.plane_count,
                    size=os.path.getsize(binary_path),
                    source_id=None,
                )
            )
            OmeImageRepository(project_id=str(project_id), db=self.db_session).save_info(
                OmeImageDB(
                    media_id=str(media_id),
                    **info.model_dump(mode="json"),
                    raw_metadata=parsed.raw_metadata,
                    files=[],
                )
            )
        except Exception as error:
            if source_path is not None:
                shutil.move(binary_path, source_path)
            else:
                binary_path.unlink(missing_ok=True)
            (dataset_dir / f"{media_id}-thumb.jpg").unlink(missing_ok=True)
            if isinstance(error, InvalidOmeImageError):
                raise InvalidImageError(str(error)) from error
            raise
        return OmeImage.model_validate(db_media)

    @staticmethod
    def _save_thumbnail(image: Image.Image, path: Path) -> None:
        try:
            thumbnail = crop_to_thumbnail(
                image=image, target_width=DEFAULT_THUMBNAIL_SIZE, target_height=DEFAULT_THUMBNAIL_SIZE
            )
            convert_to_jpeg_compatible(thumbnail).save(path)
        except Exception:
            logger.exception("Failed to generate OME image thumbnail")

    def get_ome_image(self, project_id: UUID, media_id: UUID) -> OmeImage:
        """
        Get an OME image media.

        Raises:
            ResourceNotFoundError: If the media does not exist or is not an OME image.
        """
        db_media = MediaRepository(project_id=str(project_id), db=self.db_session).get_by_id(str(media_id))
        if db_media is None or db_media.type != MediaType.OME_IMAGE:
            raise ResourceNotFoundError(ResourceType.MEDIA, str(media_id), f"OME image with ID {media_id} not found.")
        return OmeImage.model_validate(db_media)

    def get_info(self, project_id: UUID, media_id: UUID) -> OmeImageInfo:
        """
        Get the structure of an OME image.

        Raises:
            ResourceNotFoundError: If the media does not exist or is not an OME image.
        """
        db_info = OmeImageRepository(project_id=str(project_id), db=self.db_session).get_info(str(media_id))
        if db_info is None:
            raise ResourceNotFoundError(ResourceType.MEDIA, str(media_id), f"OME image with ID {media_id} not found.")
        return OmeImageInfo.model_validate(db_info)

    def validate_plane(self, info: OmeImageInfo, z: int, t: int, level: int = 0) -> None:
        """
        Raises:
            OmePlaneOutOfRangeError: If the plane or pyramid level does not exist in the image.
        """
        if not 0 <= z < info.size_z:
            raise OmePlaneOutOfRangeError(f"Z index {z} is out of range, the image has {info.size_z} slice(s).")
        if not 0 <= t < info.size_t:
            raise OmePlaneOutOfRangeError(f"T index {t} is out of range, the image has {info.size_t} time point(s).")
        level_count = max(len(info.pyramid_levels), 1)
        if not 0 <= level < level_count:
            raise OmePlaneOutOfRangeError(f"Level {level} is out of range, the image has {level_count} level(s).")

    def get_channel_view(self, project_id: UUID, media_id: UUID) -> OmeChannelView:
        """Get the display settings of an OME image, or server-computed defaults if the user has not set any."""
        info = self.get_info(project_id=project_id, media_id=media_id)
        db_view = OmeImageRepository(project_id=str(project_id), db=self.db_session).get_channel_view(str(media_id))
        if db_view is not None:
            return OmeChannelView(
                settings=[ChannelDisplaySetting.model_validate(s) for s in db_view.settings], is_default=False
            )
        ome_image = self.get_ome_image(project_id=project_id, media_id=media_id)
        lowest_level = max(len(info.pyramid_levels) - 1, 0)
        sample = self._reader.read_plane(
            self._storage(project_id, ome_image),
            z=info.size_z // 2,
            t=info.size_t // 2,
            channels=list(range(info.size_c)),
            level=lowest_level,
        )
        return OmeChannelView(settings=default_display_settings(info, dict(enumerate(sample))), is_default=True)

    def set_channel_view(
        self, project_id: UUID, media_id: UUID, settings: list[ChannelDisplaySetting]
    ) -> OmeChannelView:
        """
        Store the display settings of an OME image.

        Raises:
            InvalidChannelSettingsError: If the settings are inconsistent with the image.
        """
        info = self.get_info(project_id=project_id, media_id=media_id)
        validate_display_settings(info, settings)
        OmeImageRepository(project_id=str(project_id), db=self.db_session).save_channel_view(
            str(media_id), [setting.model_dump(mode="json") for setting in settings]
        )
        return OmeChannelView(settings=settings, is_default=False)

    def render_plane(self, project_id: UUID, media_id: UUID, z: int, t: int, level: int = 0) -> tuple[Path, str]:
        """
        Render a plane with the current display settings, caching the result on disk.

        Returns:
            The path of the rendered PNG, and the hash of the settings it was rendered with (usable as an ETag).
        """
        info = self.get_info(project_id=project_id, media_id=media_id)
        self.validate_plane(info, z=z, t=t, level=level)
        settings = self.get_channel_view(project_id=project_id, media_id=media_id).settings
        digest = settings_hash(settings)
        cache_dir = self.render_cache_dir(self._dataset_dir(project_id), media_id)
        cache_path = cache_dir / f"r{level}-z{z}-t{t}-{digest}.png"
        if cache_path.exists():
            return cache_path, digest

        ome_image = self.get_ome_image(project_id=project_id, media_id=media_id)
        rgb = self._render(project_id, ome_image, z=z, t=t, level=level, mappings=settings)
        cache_dir.mkdir(parents=True, exist_ok=True)
        # Write to a unique temporary file then rename, so that concurrent renders never expose a partial file
        tmp_path = cache_dir / f"{cache_path.stem}-{uuid4().hex}.tmp.png"
        Image.fromarray(rgb).save(tmp_path)
        os.replace(tmp_path, cache_path)
        return cache_path, digest

    def _render(
        self,
        project_id: UUID,
        ome_image: OmeImage,
        z: int,
        t: int,
        level: int,
        mappings: list[ChannelMapping] | list[ChannelDisplaySetting],
    ) -> np.ndarray:
        enabled = [m for m in mappings if not isinstance(m, ChannelDisplaySetting) or m.enabled]
        channels = sorted({m.channel for m in enabled})
        if not channels:
            info = self.get_info(project_id=project_id, media_id=ome_image.id)
            level_info = info.pyramid_levels[level] if info.pyramid_levels else None
            height = level_info.height if level_info else info.size_y
            width = level_info.width if level_info else info.size_x
            return np.zeros((height, width, 3), dtype=np.uint8)
        data = self._reader.read_plane(self._storage(project_id, ome_image), z=z, t=t, channels=channels, level=level)
        return compose_rgb(dict(zip(channels, data)), enabled)

    def render_training_plane(self, project_id: UUID, ome_image: OmeImage, z: int, t: int) -> Image.Image:
        """Render a full-resolution plane with the fixed training channel mapping."""
        info = self.get_info(project_id=project_id, media_id=ome_image.id)
        self.validate_plane(info, z=z, t=t)
        rgb = self._render(project_id, ome_image, z=z, t=t, level=0, mappings=info.channel_mapping)
        return Image.fromarray(rgb)

    def get_plane(self, project: Project, ome_image: OmeImage, z: int, t: int) -> OmePlane | None:
        """Get the plane media at (z, t) if it has already been created (i.e. annotated)."""
        info = self.get_info(project_id=project.id, media_id=ome_image.id)
        self.validate_plane(info, z=z, t=t)
        repo = MediaRepository(project_id=str(project.id), db=self.db_session)
        db_media = repo.get_child_by_index(parent_id=str(ome_image.id), frame_index=info.plane_index(z, t))
        return OmePlane.model_validate(db_media) if db_media is not None else None

    def create_plane(self, project: Project, ome_image: OmeImage, z: int, t: int) -> OmePlane:
        """
        Materialize the plane at (z, t) as a leaf media: an RGB PNG rendered with the fixed training mapping.

        Like annotated video frames, the plane is then a plain image to dataset revisions, training and inference.
        """
        info = self.get_info(project_id=project.id, media_id=ome_image.id)
        self.validate_plane(info, z=z, t=t)
        image = self.render_training_plane(project_id=project.id, ome_image=ome_image, z=z, t=t)

        media_id = uuid4()
        dataset_dir = self._dataset_dir(project.id)
        plane_path = dataset_dir / f"{media_id}.{PLANE_IMAGE_FORMAT}"
        image.save(plane_path)
        try:
            self._save_thumbnail(image, dataset_dir / f"{media_id}-thumb.jpg")
            repo = MediaRepository(project_id=str(project.id), db=self.db_session)
            db_media = repo.save(
                MediaDB(
                    id=str(media_id),
                    project_id=str(project.id),
                    type=MediaType.OME_PLANE,
                    name=f"{ome_image.name}_z{z}_t{t}",
                    format=PLANE_IMAGE_FORMAT,
                    width=image.width,
                    height=image.height,
                    parent_id=str(ome_image.id),
                    frame_index=info.plane_index(z, t),
                    z_index=z,
                    t_index=t,
                    size=os.path.getsize(plane_path),
                    source_id=None,
                )
            )
        except Exception:
            plane_path.unlink(missing_ok=True)
            (dataset_dir / f"{media_id}-thumb.jpg").unlink(missing_ok=True)
            raise
        return OmePlane.model_validate(db_media)

    def list_annotated_planes(
        self, project: Project, ome_image: OmeImage, offset: int = 0, limit: int = 50
    ) -> list[OmePlane]:
        """List the annotated planes of an OME image, ordered by (t, z)."""
        repo = MediaRepository(project_id=str(project.id), db=self.db_session)
        rows = repo.list_annotated_children(parent_id=str(ome_image.id), offset=offset, limit=limit)
        return [OmePlane.model_validate(db_media) for _, db_media in rows]

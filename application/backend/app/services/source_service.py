# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import time
from uuid import UUID, uuid4

from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.schema import ProjectDB, SourceDB
from app.models import Source, SourceType
from app.models.source import SourceAdapter, SourceConfig, SourceTestResult, VideoFileConfig
from app.repositories import SourceRepository
from app.repositories.base import PrimaryKeyIntegrityError, UniqueConstraintIntegrityError
from app.repositories.pipeline_repo import PipelineRepository

from .base import (
    ResourceInUseError,
    ResourceNotFoundError,
    ResourceType,
    ResourceValidationError,
    ResourceWithIdAlreadyExistsError,
    ResourceWithNameAlreadyExistsError,
)
from .event.event_bus import EventBus, EventType
from .parent_process_guard import parent_process_only
from .source_media_service import SourceMediaService
from .video_stream_service import VideoStreamService


class SourceService:
    def __init__(self, db_session: Session, source_media_service: SourceMediaService | None = None):
        self._db_session = db_session
        self._source_media_service = source_media_service

    @parent_process_only
    def create_source(
        self,
        name: str,
        source_type: SourceType,
        config_data: SourceConfig,
        source_id: UUID | None = None,
    ) -> Source:
        try:
            db_source = SourceRepository(self._db_session).save(
                SourceDB(
                    id=str(source_id) if source_id is not None else None,
                    name=name,
                    source_type=source_type,
                    config_data=config_data.model_dump(mode="json"),
                )
            )
            return SourceAdapter.validate_python(db_source, from_attributes=True)
        except PrimaryKeyIntegrityError:
            raise ResourceWithIdAlreadyExistsError(ResourceType.SOURCE, str(source_id))
        except UniqueConstraintIntegrityError:
            raise ResourceWithNameAlreadyExistsError(ResourceType.SOURCE, name)

    def get_by_id(self, source_id: UUID) -> Source:
        db_source = SourceRepository(self._db_session).get_by_id(str(source_id))
        if not db_source:
            raise ResourceNotFoundError(ResourceType.SOURCE, str(source_id))
        return SourceAdapter.validate_python(db_source, from_attributes=True)

    def list_all(self) -> list[Source]:
        return [
            SourceAdapter.validate_python(db_source, from_attributes=True)
            for db_source in SourceRepository(self._db_session).list_all()
        ]

    @parent_process_only
    def delete_source(self, source: Source) -> None:
        # Check for pipelines using this source before attempting deletion
        pipelines = PipelineRepository(self._db_session).get_by_source_id(str(source.id))
        if pipelines:
            project_details = []
            for p in pipelines:
                project = self._db_session.get(ProjectDB, p.project_id)
                project_name = project.name if project else p.project_id
                state = "running" if p.is_running else "configured"
                project_details.append(f"'{project_name}' ({state})")
            projects_str = ", ".join(project_details)
            msg = (
                f"Source '{source.name}' cannot be deleted because it is used by "
                f"a pipeline in project: {projects_str}. "
                f"Please stop and remove the pipeline configuration in that project first."
            )
            raise ResourceInUseError(ResourceType.SOURCE, str(source.id), msg)
        try:
            deleted = SourceRepository(self._db_session).delete(str(source.id))
            if not deleted:
                raise ResourceNotFoundError(ResourceType.SOURCE, str(source.id))
        except IntegrityError:
            raise ResourceInUseError(ResourceType.SOURCE, str(source.id))

        match source.source_type:
            case SourceType.VIDEO_FILE:
                self._delete_video_best_effort(source.config_data.video_path)
            case _:
                pass

    def get_active_source(self) -> Source | None:
        db_source = SourceRepository(self._db_session).get_active_source()
        return SourceAdapter.validate_python(db_source, from_attributes=True) if db_source else None

    def get_active_source_id(self) -> UUID | None:
        id = SourceRepository(self._db_session).get_active_source_id()
        return UUID(id) if id else None

    def _delete_video_best_effort(self, video_path: str) -> None:
        """Delete an uploaded video file, tolerating any filesystem failure."""
        if self._source_media_service is None:
            return
        try:
            self._source_media_service.delete_video(video_path)
        except OSError as e:
            logger.warning("Failed to delete video file '{}': {}", video_path, e)


class SourceUpdateService(SourceService):
    def __init__(
        self,
        event_bus: EventBus,
        db_session: Session,
        source_media_service: SourceMediaService | None = None,
    ):
        self._event_bus: EventBus = event_bus
        super().__init__(db_session, source_media_service)

    def _validate_candidate(
        self,
        *,
        source_id: UUID,
        name: str,
        source_type: SourceType,
        config_data: SourceConfig,
    ) -> None:
        """Assemble the post-change Source and validate that it is reachable."""
        candidate = SourceAdapter.validate_python(
            {
                "id": source_id,
                "name": name,
                "source_type": source_type,
                "config_data": config_data,
            }
        )
        self.validate_source(candidate)

    @parent_process_only
    def create_source(
        self,
        name: str,
        source_type: SourceType,
        config_data: SourceConfig,
        source_id: UUID | None = None,
    ) -> Source:
        self._validate_candidate(
            source_id=source_id or uuid4(), name=name, source_type=source_type, config_data=config_data
        )
        return super().create_source(name=name, source_type=source_type, config_data=config_data, source_id=source_id)

    @parent_process_only
    def update_source(
        self,
        source: Source,
        new_name: str,
        new_config_data: SourceConfig,
    ) -> Source:
        self._validate_candidate(
            source_id=source.id, name=new_name, source_type=source.source_type, config_data=new_config_data
        )
        try:
            source_repo = SourceRepository(self._db_session)
            db_source = source_repo.update(
                SourceDB(
                    id=str(source.id),
                    name=new_name,
                    config_data=new_config_data.model_dump(mode="json"),
                )
            )
            active_source_id = self.get_active_source_id()
            if active_source_id == UUID(db_source.id):
                self._event_bus.emit_event(EventType.SOURCE_CHANGED)
        except UniqueConstraintIntegrityError:
            raise ResourceWithNameAlreadyExistsError(ResourceType.SOURCE, new_name)

        match source.source_type:
            case SourceType.VIDEO_FILE if isinstance(new_config_data, VideoFileConfig):
                if source.config_data.video_path != new_config_data.video_path:
                    self._delete_video_best_effort(source.config_data.video_path)
            case _:
                pass

        return SourceAdapter.validate_python(db_source, from_attributes=True)

    _TEST_TIMEOUT_MS = 5000

    def _probe_reachability(self, source: Source) -> SourceTestResult:
        """Attempt to open the source and read one frame. Never raises; failures are reported
        via the returned result's `reachable`/`error` fields."""
        try:
            video_stream = VideoStreamService.get_video_stream(input_config=source, timeout=self._TEST_TIMEOUT_MS)
            if video_stream is None:
                return SourceTestResult.failure("Disconnected source")
            start = time.monotonic()
            with video_stream:
                video_stream.get_data()
            elapsed_ms = (time.monotonic() - start) * 1000
            return SourceTestResult.success(latency_ms=round(elapsed_ms, 1))
        except Exception as e:
            return SourceTestResult.failure(str(e))

    def test_source(self, source: Source) -> SourceTestResult:
        """Perform a connectivity check on the source."""
        return self._probe_reachability(source)

    def validate_source(self, source: Source) -> None:
        """Raise ResourceValidationError if the source cannot be opened/reached.

        Reuses the same probe as `test_source`; the resulting error message is expected
        to already be a complete, user-facing sentence (see stream error messages).
        """
        result = self._probe_reachability(source)
        if not result.reachable:
            raise ResourceValidationError(ResourceType.SOURCE, str(source.id), result.error)

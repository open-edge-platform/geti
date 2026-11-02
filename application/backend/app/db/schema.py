# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, BigInteger, Boolean, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .datetime import UTCDateTime


class Base(DeclarativeBase):
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), server_default=func.current_timestamp())


class BaseID(Base):
    __abstract__ = True
    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid4()))


class SourceDB(BaseID):
    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    config_data: Mapped[dict] = mapped_column(JSON, nullable=False)


class ProjectDB(BaseID):
    __tablename__ = "projects"
    __table_args__ = (Index("idx_projects_name", "name"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    exclusive_labels: Mapped[bool] = mapped_column(Boolean, default=False)

    model_revisions = relationship("ModelRevisionDB", back_populates="project")


class PipelineDB(Base):
    __tablename__ = "pipelines"
    __table_args__ = (Index("idx_pipelines_is_running", "is_running"),)

    project_id: Mapped[str] = mapped_column(Text, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    source_id: Mapped[str | None] = mapped_column(Text, ForeignKey("sources.id", ondelete="RESTRICT"))
    sink_id: Mapped[str | None] = mapped_column(Text, ForeignKey("sinks.id", ondelete="RESTRICT"))
    model_revision_id: Mapped[str | None] = mapped_column(Text, ForeignKey("model_revisions.id", ondelete="RESTRICT"))
    model_variant_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("model_variants.id", ondelete="RESTRICT"), nullable=True
    )
    is_running: Mapped[bool] = mapped_column(Boolean, default=False)
    data_collection: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    inference: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    device: Mapped[str] = mapped_column(String(50), nullable=False, default="cpu")

    sink = relationship("SinkDB", uselist=False, lazy="joined")
    source = relationship("SourceDB", uselist=False, lazy="joined")
    model_revision = relationship("ModelRevisionDB", uselist=False, lazy="joined")
    model_variant = relationship("ModelVariantDB", uselist=False, lazy="joined")


class SinkDB(BaseID):
    __tablename__ = "sinks"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    sink_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rate_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    config_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    output_formats: Mapped[list] = mapped_column(JSON, nullable=False, default=list)


class ModelRevisionDB(BaseID):
    __tablename__ = "model_revisions"
    __table_args__ = (
        Index("idx_model_revisions_project_status", "project_id", "training_status"),
        Index("idx_model_revisions_architecture", "project_id", "architecture"),
    )

    project_id: Mapped[str] = mapped_column(Text, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    architecture: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_revision: Mapped[str | None] = mapped_column(Text, ForeignKey("model_revisions.id"), nullable=True)
    training_status: Mapped[str] = mapped_column(String(50), nullable=False)
    training_configuration: Mapped[dict] = mapped_column(JSON, nullable=False)
    training_dataset_id: Mapped[str | None] = mapped_column(Text, ForeignKey("dataset_revisions.id"), nullable=True)
    label_schema_revision: Mapped[dict] = mapped_column(JSON, nullable=False)
    training_started_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    training_finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    training_device: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    files_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    project = relationship("ProjectDB", back_populates="model_revisions")
    variants = relationship("ModelVariantDB", back_populates="model_revision")


class DatasetRevisionDB(BaseID):
    __tablename__ = "dataset_revisions"
    __table_args__ = (Index("idx_dataset_revisions_project", "project_id"),)

    project_id: Mapped[str] = mapped_column(Text, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Dataset view the revision was created from; NULL means the revision covers the entire dataset.
    # Not a foreign key on purpose: if a view is deleted, the reference can't be removed (set to null) otherwise
    # it would appear as if the revision was created from the entire dataset.
    dataset_view_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    files_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    training_count: Mapped[int] = mapped_column(Integer, default=0)
    validation_count: Mapped[int] = mapped_column(Integer, default=0)
    testing_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    size: Mapped[int] = mapped_column(Integer, default=0)


class DatasetItemDB(Base):
    __tablename__ = "dataset_items"
    __table_args__ = (Index("idx_dataset_items_user_reviewed", "project_id", "user_reviewed"),)

    id: Mapped[str] = mapped_column(Text, ForeignKey("media.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    project_id: Mapped[str] = mapped_column(Text, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    annotation_data: Mapped[list | None] = mapped_column(JSON, nullable=True, default=None)
    user_reviewed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    prediction_model_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("model_revisions.id", ondelete="SET NULL"), nullable=True
    )
    subset: Mapped[str | None] = mapped_column(String(20), nullable=False)
    subset_assigned_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)


class DatasetViewDB(BaseID):
    __tablename__ = "dataset_views"
    __table_args__ = (
        Index("idx_dataset_views_project", "project_id"),
        UniqueConstraint("project_id", "name", name="uq_project_dataset_view_name"),
    )

    project_id: Mapped[str] = mapped_column(Text, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class DatasetViewItemDB(Base):
    """
    Associates a dataset view with the media (images/videos) assigned to it.

    References ``media.id`` (rather than ``dataset_items.id``) so that a video can be assigned to a view as soon
    as it is uploaded, even before any of its frames have been annotated (and therefore before a dataset item
    exists for it). Cascading on ``media`` deletion ensures that once a media item is deleted from the project's
    dataset, it is automatically removed from any view it was assigned to.
    """

    __tablename__ = "dataset_view_items"

    dataset_view_id: Mapped[str] = mapped_column(
        Text, ForeignKey("dataset_views.id", ondelete="CASCADE"), primary_key=True
    )
    media_id: Mapped[str] = mapped_column(Text, ForeignKey("media.id", ondelete="CASCADE"), primary_key=True)


class MediaDB(BaseID):
    __tablename__ = "media"
    __table_args__ = (
        Index("idx_media_parent_id", "parent_id"),
        # Constraint name kept from when the column was `video_id`: renaming it on SQLite requires recreating the
        # table, which would cascade-delete dependent rows since migrations run with foreign keys enabled.
        UniqueConstraint("parent_id", "frame_index", name="uq_video_id_frame_index"),
    )

    project_id: Mapped[str] = mapped_column(Text, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str] = mapped_column(String(50), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    frame_count: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    # Parent container media: a video for video frames, an OME image for OME planes.
    parent_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("media.id", ondelete="CASCADE"), nullable=True, default=None
    )
    # Linear index within the parent: video frame number, or (z + t * size_z) for OME planes.
    frame_index: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    # Populated only for OME planes.
    z_index: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    t_index: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    # SQLite INTEGER is always 64-bit, so sizes above 2^31 (BigTIFF) already fit without widening the column.
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    source_id: Mapped[str | None] = mapped_column(Text, ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)


class OmeImageDB(Base):
    """OME-metadata-derived structure of an uploaded OME image, 1:1 with an `ome_image` media row."""

    __tablename__ = "ome_images"

    media_id: Mapped[str] = mapped_column(Text, ForeignKey("media.id", ondelete="CASCADE"), primary_key=True)
    container_format: Mapped[str] = mapped_column(String(20), nullable=False)
    size_x: Mapped[int] = mapped_column(Integer, nullable=False)
    size_y: Mapped[int] = mapped_column(Integer, nullable=False)
    size_z: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    size_c: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    size_t: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Free-form axis string: NGFF declares the axis order per image, so it is not constrained to OME-TIFF orders
    dimension_order: Mapped[str] = mapped_column(String(16), nullable=False)
    pixel_type: Mapped[str] = mapped_column(String(20), nullable=False)
    significant_bits: Mapped[int | None] = mapped_column(Integer, nullable=True)
    series_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_big_tiff: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # [{"index": 0, "name": "DAPI", "color": "#0000ff", "emission_wavelength": 461}, ...]
    channels: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Fixed channel->RGB projection used to materialize training data; computed once at ingest, never mutated
    channel_mapping: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # [{"level": 0, "width": 40000, "height": 30000, "scale": [1, 1]}, ...]; empty if not pyramidal
    pyramid_levels: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Multi-file layouts: entrypoint and constituent files, relative to the media root
    entrypoint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    files: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Verbatim OME-XML / NGFF attributes, to re-parse without touching the binary
    raw_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)


class OmeChannelViewDB(Base):
    """User display settings (channel->RGB mapping and intensity windows) of an OME image in the annotator."""

    __tablename__ = "ome_channel_views"

    media_id: Mapped[str] = mapped_column(Text, ForeignKey("media.id", ondelete="CASCADE"), primary_key=True)
    # [{"channel": 2, "target": "red", "enabled": true, "window_min": 120, "window_max": 4000}, ...]
    settings: Mapped[list] = mapped_column(JSON, nullable=False, default=list)


class LabelDB(BaseID):
    __tablename__ = "labels"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_project_label_name"),
        UniqueConstraint("project_id", "hotkey", name="uq_project_label_hotkey"),
    )

    project_id: Mapped[str] = mapped_column(Text, ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    hotkey: Mapped[str | None] = mapped_column(String(10), nullable=True)


class DatasetItemLabelDB(Base):
    __tablename__ = "dataset_items_labels"

    dataset_item_id: Mapped[str] = mapped_column(
        Text, ForeignKey("dataset_items.id", ondelete="CASCADE"), primary_key=True
    )
    label_id: Mapped[str] = mapped_column(Text, ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True)


class TrainingConfigurationDB(BaseID):
    __tablename__ = "training_configurations"
    __table_args__ = (UniqueConstraint("project_id", "model_architecture_id", name="uq_project_model_config"),)

    # Rows with 'model_architecture = null' store the task-level configuration
    # Rows with 'model_architecture != null' store the algo-level configuration
    # Missing rows imply that the configuration is default, with values derived from the model manifest
    project_id: Mapped[str] = mapped_column(Text, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    model_architecture_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # NULL for general config
    configuration_data: Mapped[dict] = mapped_column(JSON, nullable=False)

    project = relationship("ProjectDB")


class ModelVariantDB(BaseID):
    __tablename__ = "model_variants"
    __table_args__ = (Index("idx_model_variants_model_revision", "model_revision_id"),)

    model_revision_id: Mapped[str] = mapped_column(
        Text, ForeignKey("model_revisions.id", ondelete="CASCADE"), nullable=False
    )
    format: Mapped[str] = mapped_column(String(50), nullable=False)
    precision: Mapped[str] = mapped_column(String(20), nullable=False)
    quantization_info: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)
    files_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    model_revision = relationship("ModelRevisionDB", back_populates="variants")
    evaluations = relationship("EvaluationDB", back_populates="model_variant")


class EvaluationDB(BaseID):
    __tablename__ = "evaluations"

    model_revision_id: Mapped[str] = mapped_column(Text, ForeignKey("model_revisions.id", ondelete="CASCADE"))
    model_variant_id: Mapped[str] = mapped_column(Text, ForeignKey("model_variants.id", ondelete="CASCADE"))
    dataset_revision_id: Mapped[str] = mapped_column(
        Text, ForeignKey("dataset_revisions.id", ondelete="CASCADE"), nullable=False
    )
    subset: Mapped[str] = mapped_column(String(20), nullable=False)

    metric_scores = relationship("MetricScoreDB", back_populates="evaluation")
    model_variant = relationship("ModelVariantDB", back_populates="evaluations")


class MetricScoreDB(BaseID):
    __tablename__ = "metric_scores"

    evaluation_id: Mapped[str] = mapped_column(Text, ForeignKey("evaluations.id", ondelete="CASCADE"))
    metric: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)

    evaluation = relationship("EvaluationDB", back_populates="metric_scores")


class UploadDB(BaseID):
    """Resumable (TUS) upload. The bytes live in '<uploads_dir>/<id>.part'; the client filename is never a path."""

    __tablename__ = "uploads"
    __table_args__ = (
        Index("idx_uploads_state", "state"),
        Index("idx_uploads_expires_at", "expires_at"),
    )

    filename: Mapped[str] = mapped_column(String(255), nullable=False)  # sanitised client-declared name
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # null with Upload-Defer-Length
    offset: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    state: Mapped[str] = mapped_column(String(20), nullable=False)  # pending|in_progress|completed|consumed
    checksum: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)

# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import shutil
from datetime import UTC, datetime

from loguru import logger

from app.core.jobs.models import Job, JobStatus
from app.db.engine import get_db_session
from app.models import TrainingJob, TrainingStatus
from app.services.base import ResourceNotFoundError
from app.services.model_service import ModelService


def finalize_training_job(job: Job) -> None:
    """Reconcile the model status, preserve the training log, and remove the workspace."""
    if not isinstance(job, TrainingJob):
        raise TypeError("finalize_training_job requires a TrainingJob")

    _reconcile_stuck_training_status(job)
    _preserve_training_log(job)
    _remove_workspace(job)


def _preserve_training_log(job: TrainingJob) -> None:
    log_path = job.log_dir / job.log_file
    if job.status == JobStatus.CANCELLED:
        # The trainer deletes a cancelled model; copying the log would recreate its directory.
        logger.info("Training job {} was cancelled, not keeping its log", job.id)
    else:
        try:
            if log_path.exists():
                model_dir = job.data_dir / "projects" / str(job.project_id) / "models" / str(job.params.model_id)
                model_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(log_path, model_dir / "training.log")
            else:
                logger.warning("Log file {} does not exist", log_path)
        except OSError as exc:
            logger.error("Failed to save training log {}: {}", log_path, exc)


def _remove_workspace(job: TrainingJob) -> None:
    workspace_dir = job.data_dir / f"getitune-workspace-{job.params.model_id}"
    try:
        shutil.rmtree(workspace_dir)
        logger.info("Cleaned up getitune workspace directory at {}", workspace_dir)
    except FileNotFoundError:
        pass
    except Exception as cleanup_exc:
        logger.error("Failed to clean up getitune workspace directory at {}: {}", workspace_dir, cleanup_exc)


def _reconcile_stuck_training_status(job: TrainingJob) -> None:
    """Force training_status to FAILED if the trainer process died without updating it."""
    try:
        with get_db_session() as db:
            model_service = ModelService(data_dir=job.data_dir, db_session=db)
            try:
                model = model_service.get_model(project_id=job.project_id, model_id=job.params.model_id)
            except ResourceNotFoundError:
                return  # The revision was never created or was already deleted.

            if model.training_info is not None:
                found_status = model.training_info.status
                if found_status not in (TrainingStatus.SUCCESSFUL, TrainingStatus.FAILED):
                    model_service.update_revision_status(
                        project_id=job.project_id,
                        model_id=job.params.model_id,
                        training_status=TrainingStatus.FAILED,
                        training_finished_at=datetime.now(UTC),
                    )
                    logger.warning(
                        "Model {} was left at {} after job completion; forced to FAILED",
                        job.params.model_id,
                        found_status,
                    )
    except Exception as reconcile_exc:
        logger.error("Failed to verify the training status for model {}: {}", job.params.model_id, reconcile_exc)

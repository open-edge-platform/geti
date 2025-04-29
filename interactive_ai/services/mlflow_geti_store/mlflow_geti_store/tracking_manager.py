# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

# ruff: noqa: ARG002

from __future__ import annotations

import logging as log
from typing import TYPE_CHECKING, Literal

from mlflow.entities import Experiment, ExperimentTag, LifecycleStage, Metric, Param, Run, RunInfo, RunStatus, RunTag
from mlflow.store.entities.paged_list import PagedList
from mlflow.utils.search_utils import SearchUtils

from mlflow_geti_store.s3_object_storage_client import S3ObjectStorageClient
from mlflow_geti_store.tracking_model import (
    MetricsHistoryModel,
    ProgressModel,
    ProjectModel,
    RunDataModel,
    RunInfoModel,
    RunInputsModel,
)
from mlflow_geti_store.utils import ARTIFACT_ROOT_URI_PREFIX, Identifier, TimeStampMapper

if TYPE_CHECKING:
    from mlflow.models import Model as MlflowModel

MlFlowTag = RunTag | ExperimentTag

PROGRESS_KEY = "__progress__"
STAGE_KEY = "__stage__"


class InvalidIdentifierError(Exception):
    def __init__(self, identifier_type: Literal["project", "job"], query_id: str):
        self.identifier_type = identifier_type
        self.query_id = query_id
        super().__init__(identifier_type, query_id)


class NotAllowedCommandError(Exception):
    def __init__(self, command_name: str):
        self.command_name = command_name
        super().__init__(command_name)


class InvalidStateError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class BaseManager:
    """
    :param artifact_uri: String value, "mlflow-artifacts:/"
    """

    def __init__(self, client: S3ObjectStorageClient, identifier: Identifier) -> None:
        self.client = client
        self.identifier = identifier
        self.artifact_root_uri = ARTIFACT_ROOT_URI_PREFIX + str(self.identifier.to_path())


class ExperimentManager(BaseManager):
    def __init__(self, client: S3ObjectStorageClient, identifier: Identifier) -> None:
        super().__init__(client=client, identifier=identifier)

    def get(self, experiment_id: str) -> Experiment:
        """Get MLFlow experiment entity."""
        if experiment_id != self.identifier.project_id:
            raise InvalidIdentifierError(identifier_type="project", query_id=experiment_id)

        return ProjectModel.from_object_storage(client=self.client).to_mlflow()

    def get_all(self) -> list[Experiment]:
        return [self.get(experiment_id=self.identifier.project_id)]


class RunManager(BaseManager):
    def __init__(self, client: S3ObjectStorageClient, identifier: Identifier) -> None:
        super().__init__(client=client, identifier=identifier)

    def get_run_by_id(self, run_id: str) -> Run:
        if run_id != self.identifier.job_id:
            raise InvalidIdentifierError(identifier_type="job", query_id=run_id)

        project_model = ProjectModel.from_object_storage(client=self.client)

        return Run(
            run_info=RunInfoModel.from_object_storage(client=self.client).to_mlflow(project_model=project_model),
            run_data=RunDataModel.from_object_storage(client=self.client).to_mlflow(),
            run_inputs=RunInputsModel.from_object_storage(client=self.client).to_mlflow(),
        )

    def get_runs_by_experiment_ids(self, experiment_ids: list[str]) -> list[Run]:
        msg = "Currently this function only produces one MLFlow Run corresponded to the job_id in its identifier."
        log.warning(msg)
        return [self.get_run_by_id(run_id=self.identifier.job_id)]

    def update_run_info(
        self,
        run_id: str,
        run_status: RunStatus | None,
        end_time: int | None,
        run_name: str | None,
    ) -> RunInfo:
        if run_id != self.identifier.job_id:
            raise InvalidIdentifierError(identifier_type="job", query_id=run_id)

        project_model = ProjectModel.from_object_storage(client=self.client)
        run_model = RunInfoModel.from_object_storage(client=self.client)

        if run_status:
            run_model.status = RunStatus.to_string(run_status)
        if end_time:
            run_model.end_time = TimeStampMapper.backward(end_time)
        if run_name:
            raise NotAllowedCommandError(command_name="update_run_info.run_name")

        run_model.to_object_storage(client=self.client)

        return run_model.to_mlflow(project_model=project_model)

    def create_run(
        self,
        experiment_id: str,
        user_id: str,
        start_time: int,
        tags: list[RunTag],
        run_name: str,
    ) -> Run:
        raise NotAllowedCommandError(command_name="create_run")

    def delete_run(self, run_id: str) -> None:
        raise NotAllowedCommandError(command_name="delete_run")

    def restore_run(self, run_id: str) -> None:
        raise NotAllowedCommandError(command_name="restore_run")

    def get_metric_history(
        self,
        run_id: str,
        metric_key: str,
        limit: int,
        offset: int,
    ) -> PagedList[Metric]:
        if run_id != self.identifier.job_id:
            raise InvalidIdentifierError(identifier_type="job", query_id=run_id)

        model = MetricsHistoryModel.from_object_storage(
            client=self.client, metric_key=metric_key, offset=offset, limit=limit
        )
        token = SearchUtils.create_page_token(offset=offset + len(model.metrics))
        return PagedList(items=model.metrics, token=token)

    def log_batch(
        self,
        run_id: str,
        metrics: list[Metric],
        params: list[Param],
        tags: list[RunTag],
    ) -> None:
        if run_id != self.identifier.job_id:
            raise InvalidIdentifierError(identifier_type="job", query_id=run_id)

        project_model = ProjectModel.from_object_storage(client=self.client)
        run_info_model = RunInfoModel.from_object_storage(client=self.client)
        run_info = run_info_model.to_mlflow(project_model=project_model)

        if run_info.lifecycle_stage != LifecycleStage.ACTIVE:
            raise InvalidStateError(message=f"Run ID={run_id} is not active")

        if metrics:
            MetricsHistoryModel(metrics=metrics).to_object_storage(client=self.client)

        if params:
            msg = "log_batch.params is not supported yet."
            log.warning(msg)

        if tags:
            progress, stage = None, None
            for tag in tags:
                if tag.key == PROGRESS_KEY:
                    progress = float(tag.value)
                elif tag.key == STAGE_KEY:
                    stage = tag.value
                else:
                    msg = f"This tag key is not allowed: {tag.key}."
                    raise ValueError(msg)

            if progress is None or stage is None:
                msg = "progress and stage should not be None."
                raise ValueError(msg)

            ProgressModel(progress=progress, stage=stage).to_object_storage(client=self.client)

    def record_logged_model(self, run_id: str, mlflow_model: MlflowModel) -> None:
        raise NotAllowedCommandError(command_name="record_logged_model")

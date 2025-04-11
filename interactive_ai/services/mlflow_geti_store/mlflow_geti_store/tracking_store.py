# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

# ruff: noqa: ARG002

import logging
from typing import TYPE_CHECKING

from mlflow.entities import (
    DatasetInput,
    Experiment,
    ExperimentTag,
    LifecycleStage,
    Metric,
    Param,
    Run,
    RunInfo,
    RunStatus,
    RunTag,
    ViewType,
    _DatasetSummary,
)
from mlflow.exceptions import BAD_REQUEST, INTERNAL_ERROR, MlflowException
from mlflow.store.entities.paged_list import PagedList
from mlflow.store.tracking.abstract_store import AbstractStore
from mlflow.utils.search_utils import SearchExperimentsUtils, SearchUtils

from mlflow_geti_store.s3_object_storage_client import S3ObjectStorageClientSingleton
from mlflow_geti_store.tracking_manager import ExperimentManager, InvalidIdentifierError, RunManager

if TYPE_CHECKING:
    from mlflow.models import Model

SEARCH_MAX_RESULTS_THRESHOLD = 50000

logger = logging.getLogger(__name__)


class GetiTrackingStore(AbstractStore):
    """Custom mlflow TrackingStore plugin for Geti

    :param store_uri: String value, "geti://{project_id}/{model_storage_id}/{training_operation_id}"
    :param artifact_uri: String value, "mlflow-artifacts:/"
    """

    def __init__(self, store_uri: str | None = None, artifact_uri: str | None = None) -> None:
        self.client = S3ObjectStorageClientSingleton.instance()
        self.identifier = self.client.identifier

        self.experiment_manager = ExperimentManager(client=self.client, identifier=self.identifier)
        self.run_manager = RunManager(client=self.client, identifier=self.identifier)

    def search_experiments(
        self,
        view_type: ViewType = ViewType.ACTIVE_ONLY,
        max_results: int = SEARCH_MAX_RESULTS_THRESHOLD,
        filter_string: str | None = None,
        order_by: list[str] | None = None,
        page_token: bytes | None = None,
    ) -> PagedList:
        if max_results > SEARCH_MAX_RESULTS_THRESHOLD:
            logger.error("Requested max_results=%d exceeds the threshold=%d", max_results, SEARCH_MAX_RESULTS_THRESHOLD)
            raise MlflowException(
                "Invalid value for request parameter max_results. It must be at "
                f"most {SEARCH_MAX_RESULTS_THRESHOLD}, but got value {max_results}",
                error_code=BAD_REQUEST,
            )

        if view_type != ViewType.ACTIVE_ONLY:
            logger.error("Requested view_type=%s is not allowed", view_type)
            raise MlflowException("Only ViewType.ACTIVE_ONLY is allowed", error_code=BAD_REQUEST)

        experiments = self.experiment_manager.get_all()
        filtered = SearchExperimentsUtils.filter(experiments, filter_string)
        sorted_experiments = SearchExperimentsUtils.sort(
            filtered, order_by or ["creation_time DESC", "experiment_id ASC"]
        )
        experiments, next_page_token = SearchUtils.paginate(sorted_experiments, page_token, max_results)
        return PagedList(experiments, next_page_token)

    def get_experiment(self, experiment_id: str) -> Experiment:
        try:
            return self.experiment_manager.get(experiment_id=experiment_id)
        except InvalidIdentifierError as e:
            message = f"{e.identifier_type} id ({e.query_id}) is invalid."
            logger.exception(message)
            raise MlflowException(message=message, error_code=BAD_REQUEST)
        except Exception:
            logger.exception("Failed to get experiment with id=%s", experiment_id)
            raise MlflowException(message="internal error", error_code=INTERNAL_ERROR)

    def create_experiment(self, name: str, artifact_location: str, tags: list[ExperimentTag]) -> str:
        raise MlflowException("Creating experiment by MLFlow API is not allowed.", error_code=BAD_REQUEST)

    def get_experiment_by_name(self, experiment_name: str) -> Experiment:
        raise MlflowException("Cannot get experiment by name. Please use get by ID.", error_code=BAD_REQUEST)

    def delete_experiment(self, experiment_id: str) -> None:
        raise MlflowException("Deleting experiment by MLFlow API is not allowed.", error_code=BAD_REQUEST)

    def restore_experiment(self, experiment_id: str) -> None:
        raise MlflowException("Restoring experiment by MLFlow API is not allowed.", error_code=BAD_REQUEST)

    def rename_experiment(self, experiment_id: str, new_name: str) -> None:
        raise MlflowException("Renaming experiment by MLFlow API is not allowed.", error_code=BAD_REQUEST)

    def set_experiment_tag(self, experiment_id: str, tag: ExperimentTag) -> None:
        raise MlflowException("Set experiment tag by MLFlow API is not allowed.", error_code=BAD_REQUEST)

    def get_run(self, run_id: str) -> Run:
        try:
            return self.run_manager.get_run_by_id(run_id=run_id)
        except InvalidIdentifierError as e:
            message = f"{e.identifier_type} id ({e.query_id}) is invalid."
            logger.exception(message)
            raise MlflowException(message=message, error_code=BAD_REQUEST)
        except Exception:
            logger.exception("Failed to get run with id=%s", run_id)
            raise MlflowException(message="internal error", error_code=INTERNAL_ERROR)

    def update_run_info(
        self,
        run_id: str,
        run_status: RunStatus | None,
        end_time: int | None,
        run_name: str | None,
    ) -> RunInfo:
        return self.run_manager.update_run_info(
            run_id=run_id,
            run_status=run_status,
            end_time=end_time,
            run_name=run_name,
        )

    def create_run(
        self,
        experiment_id: str,
        user_id: str,
        start_time: int,
        tags: list[RunTag],
        run_name: str,
    ) -> Run:
        raise MlflowException("Create run by MLFlow API is not allowed.", error_code=BAD_REQUEST)

    def delete_run(self, run_id: str) -> None:
        raise MlflowException("Delete run by MLFlow API is not allowed.", error_code=BAD_REQUEST)

    def restore_run(self, run_id: str) -> None:
        raise MlflowException("Restore run by MLFlow API is not allowed.", error_code=BAD_REQUEST)

    def get_metric_history(
        self,
        run_id: str,
        metric_key: str,
        max_results: int | None = None,
        page_token: str | None = None,
    ) -> PagedList[Metric]:
        limit = max_results if max_results is not None else 0
        offset = SearchUtils.parse_start_offset_from_page_token(page_token)

        return self.run_manager.get_metric_history(
            run_id=run_id,
            metric_key=metric_key,
            limit=limit,
            offset=offset,
        )

    def _search_runs(
        self,
        experiment_ids: list[str],
        filter_string: str,
        run_view_type: ViewType,
        max_results: int = SEARCH_MAX_RESULTS_THRESHOLD,
        order_by: list[str] | None = None,
        page_token: str | None = None,
    ) -> tuple[list[Run], str]:
        if max_results > SEARCH_MAX_RESULTS_THRESHOLD:
            raise MlflowException(
                "Invalid value for request parameter max_results. It must be at "
                f"most {SEARCH_MAX_RESULTS_THRESHOLD}, but got value {max_results}",
            )

        runs = [
            run
            for run in self.run_manager.get_runs_by_experiment_ids(experiment_ids=experiment_ids)
            if LifecycleStage.matches_view_type(view_type=run_view_type, lifecycle_stage=run.info.lifecycle_stage)
        ]

        filtered = SearchUtils.filter(runs, filter_string)
        sorted_runs = SearchUtils.sort(filtered, order_by)
        runs, next_page_token = SearchUtils.paginate(sorted_runs, page_token, max_results)
        return runs, next_page_token

    def log_batch(
        self,
        run_id: str,
        metrics: list[Metric],
        params: list[Param],
        tags: list[RunTag],
    ) -> None:
        self.run_manager.log_batch(run_id=run_id, metrics=metrics, params=params, tags=tags)

    def record_logged_model(self, run_id: str, mlflow_model: "Model") -> None:
        raise MlflowException("Recording logged model is not allowed")

    def log_inputs(self, run_id: str, datasets: list[DatasetInput] | None = None) -> None:
        raise MlflowException("Logging inputs is not allowed")

    def _search_datasets(self, experiment_ids: list[str]) -> list[_DatasetSummary]:
        runs, _ = self._search_runs(experiment_ids=experiment_ids, filter_string="", run_view_type=ViewType.ALL)

        summaries = []
        for run in runs:
            for dataset_input in run.inputs.dataset_inputs:
                summaries.append(
                    _DatasetSummary(
                        experiment_id=run.info.experiment_id,
                        name=dataset_input.dataset.name,
                        digest=dataset_input.dataset.digest,
                        context=dataset_input.dataset.source,
                    )
                )

        return summaries

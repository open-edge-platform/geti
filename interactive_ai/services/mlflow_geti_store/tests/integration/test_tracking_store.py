# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
import requests
from mlflow.entities import Metric, RunStatus, ViewType
from mlflow.exceptions import MlflowException
from mlflow_geti_store.tracking_store import GetiTrackingStore


class TestTrackingStore:
    @pytest.fixture()
    def fxt_tracking_store(self) -> GetiTrackingStore:
        store_uri = "geti://"
        artifact_uri = "mlflow-artifacts:/"

        return GetiTrackingStore(store_uri=store_uri, artifact_uri=artifact_uri)

    def test_search_experiments(self, fxt_tracking_store: GetiTrackingStore, fxt_project_id):
        results = fxt_tracking_store.search_experiments()

        assert len(results) == 1
        assert results[0].experiment_id == fxt_project_id

    def test_get_experiment(self, fxt_tracking_store: GetiTrackingStore, fxt_project_id):
        exp = fxt_tracking_store.get_experiment(experiment_id=fxt_project_id)

        assert exp.experiment_id == fxt_project_id

        with pytest.raises(MlflowException):
            fxt_tracking_store.get_experiment(experiment_id="wrong_id")

    def test_get_run(self, fxt_tracking_store: GetiTrackingStore, fxt_job_id):
        run = fxt_tracking_store.get_run(run_id=fxt_job_id)

        assert run.info.run_id == fxt_job_id
        assert set(run.data.metrics.keys()) == {"car", "cat", "dog"}
        assert len(run.inputs.dataset_inputs) == 10

        for inp in run.inputs.dataset_inputs:
            assert inp.dataset.source_type == "http"
            response = requests.get(url=inp.dataset.source)
            assert response.content == b"data"

    def test_update_run_info(self, fxt_tracking_store: GetiTrackingStore, fxt_job_id):
        updated = fxt_tracking_store.update_run_info(
            run_id=fxt_job_id,
            run_status=RunStatus.FINISHED,  # type: ignore
            end_time=1000,
            run_name=None,
        )

        assert updated.status == "FINISHED"
        assert updated.end_time == 1000

        retrieved = fxt_tracking_store.get_run(run_id=fxt_job_id)
        assert retrieved.info.status == "FINISHED"
        assert retrieved.info.end_time == 1000

    def test_get_metric_history(self, fxt_tracking_store: GetiTrackingStore, fxt_job_id):
        keys = ["lr", "loss"]

        max_step = 10
        metrics = [Metric(key=key, value=step, timestamp=step, step=step) for step in range(max_step) for key in keys]
        for metric in metrics:
            fxt_tracking_store.log_metric(run_id=fxt_job_id, metric=metric)

        for key in keys:
            retrieved = sorted(
                fxt_tracking_store.get_metric_history(
                    run_id=fxt_job_id,
                    metric_key=key,
                    max_results=None,
                    page_token=None,
                ),
                key=lambda metric: metric.step,
            )

            assert retrieved == [metric for metric in metrics if metric.key == key]

    def test_search_runs(
        self,
        fxt_tracking_store: GetiTrackingStore,
        fxt_project_id,
        fxt_job_id,
    ):
        runs = fxt_tracking_store.search_runs(
            experiment_ids=[fxt_project_id],
            filter_string="",
            run_view_type=ViewType.ALL,
        )
        assert len(runs) == 1
        assert runs[0].info.run_id == fxt_job_id

    def test_log_batch(self, fxt_tracking_store: GetiTrackingStore, fxt_job_id):
        keys = ["loss", "lr"]

        max_step = 10
        metrics = [Metric(key=key, value=step, timestamp=step, step=step) for step in range(max_step) for key in keys]

        fxt_tracking_store.log_batch(run_id=fxt_job_id, metrics=metrics, params=[], tags=[])

        updated = fxt_tracking_store.get_run(run_id=fxt_job_id)

        assert set(updated.data.metrics.keys()) == {"car", "cat", "dog", "loss", "lr"}

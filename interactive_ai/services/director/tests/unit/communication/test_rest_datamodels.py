# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest
from testfixtures import compare

from communication.views.job_rest_views import JobRestViews
from communication.views.model_test_result_rest_views import ModelTestResultRestViews
from communication.views.performance_rest_views import PerformanceRESTViews

from geti_types import ID
from iai_core.entities.dataset_storage import NullDatasetStorage
from iai_core.repos import DatasetStorageRepo, ModelRepo


class TestRestDataModels:
    def test_job_ids_to_rest(
        self,
        fxt_ote_id,
    ) -> None:
        rest_view = JobRestViews.job_id_to_rest(job_id=fxt_ote_id(0))

        expected_rest_view = {"job_id": str(fxt_ote_id(0))}
        assert rest_view == expected_rest_view

    @pytest.mark.parametrize(
        "lazyfxt_performance, lazyfxt_performance_rest",
        [
            ("fxt_project_performance", "fxt_project_performance_rest"),
            ("fxt_anomaly_performance", "fxt_anomaly_reduced_performance_rest"),
        ],
        ids=[
            "Performance",
            "Reduced Anomaly localization performance",
        ],
    )
    def test_performance_to_rest(
        self,
        lazyfxt_performance,
        lazyfxt_performance_rest,
        request,
    ):
        # Arrange
        performance = request.getfixturevalue(lazyfxt_performance)
        performance_rest = request.getfixturevalue(lazyfxt_performance_rest)

        # Act
        result = PerformanceRESTViews.performance_to_rest(performance)

        # Assert
        compare(result, performance_rest, ignore_eq=True)

    @pytest.mark.parametrize(
        "model_test_result, model_test_result_rest",
        [
            ("fxt_model_test_result", "fxt_model_test_result_rest"),
            (
                "fxt_model_test_result_deleted_ds",
                "fxt_model_test_result_deleted_ds_rest",
            ),
        ],
    )
    def test_model_test_result_to_rest(
        self,
        request,
        model_test_result,
        model_test_result_rest,
        fxt_model,
        fxt_dataset_storage,
    ) -> None:
        # Arrange
        model_test_result = request.getfixturevalue(model_test_result)
        model_test_result_rest = request.getfixturevalue(model_test_result_rest)
        dummy_datasets_counts = {}
        dataset_storage = (
            NullDatasetStorage() if model_test_result.dataset_storage_ids[0] == ID() else fxt_dataset_storage
        )
        dummy_datasets_counts[dataset_storage.id_] = {
            "n_images": 10,
            "n_frames": 5,
            "n_samples": 15,
        }

        # Act
        with (
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model) as mock_get_model,
            patch.object(DatasetStorageRepo, "get_by_id", return_value=dataset_storage) as mock_get_dataset_storage,
        ):
            result = ModelTestResultRestViews.model_test_result_to_rest(
                model_test_result=model_test_result,
                datasets_counts=dummy_datasets_counts,
            )

        # Assert
        mock_get_model.assert_called_once_with(fxt_model.id_)
        mock_get_dataset_storage.assert_called_once_with(dataset_storage.id_)
        assert "creation_time" in result
        assert "creation_time" in model_test_result_rest
        result.pop("creation_time")
        model_test_result_rest.pop("creation_time")
        result["scores"].sort(key=lambda x: str(x["label_id"]))
        result.pop("scores")
        model_test_result_rest.pop("scores")
        compare(result, model_test_result_rest, ignore_eq=True)

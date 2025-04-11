# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
from unittest.mock import patch

import pytest
from testfixtures import compare

from communication.views.model_test_result_rest_views import ModelTestResultRestViews

from geti_types import ID
from sc_sdk.repos import DatasetStorageRepo, ModelRepo


class TestModelTestResultRESTViews:
    @pytest.mark.parametrize("job_id_available", [False, True])
    def test_model_test_result_to_rest(
        self, job_id_available, fxt_model_test_result, fxt_model_test_result_rest, fxt_dataset_storage, fxt_model
    ) -> None:
        # Arrange
        dataset_info = fxt_model_test_result_rest["datasets_info"][0]
        dummy_dataset_counts = {
            "n_images": dataset_info["n_images"],
            "n_frames": dataset_info["n_frames"],
            "n_samples": dataset_info["n_samples"],
        }
        dummy_datasets_counts = {ID(dataset_info["id"]): dummy_dataset_counts}
        if not job_id_available:
            fxt_model_test_result.job_id = None
            fxt_model_test_result_rest["job_info"]["id"] = None

        # Act
        with (
            patch.object(DatasetStorageRepo, "get_by_id", return_value=fxt_dataset_storage) as mock_get_dataset_storage,
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model) as mock_get_model,
        ):
            result = ModelTestResultRestViews.model_test_result_to_rest(
                model_test_result=fxt_model_test_result, datasets_counts=dummy_datasets_counts
            )

        # Assert
        mock_get_dataset_storage.assert_called_once_with(fxt_model_test_result.dataset_storage_ids[0])
        mock_get_model.assert_called_once_with(fxt_model_test_result.model_id)
        result["scores"].sort(key=lambda x: str(x["label_id"]))
        compare(result, fxt_model_test_result_rest, ignore_eq=True)

    def test_model_test_results_to_rest(
        self,
        fxt_model_test_result,
        fxt_model_test_result_rest,
        fxt_model_test_results_rest,
        fxt_dataset_storage,
        fxt_model,
    ) -> None:
        # Arrange
        model_test_results = [fxt_model_test_result, fxt_model_test_result]
        dataset_info = fxt_model_test_result_rest["datasets_info"][0]
        dummy_dataset_counts = {
            "n_images": dataset_info["n_images"],
            "n_frames": dataset_info["n_frames"],
            "n_samples": dataset_info["n_samples"],
        }
        dummy_datasets_counts_per_model_test = {
            fxt_model_test_result.id_: {ID(dataset_info["id"]): dummy_dataset_counts}
        }

        # Act
        with (
            patch.object(DatasetStorageRepo, "get_by_id", return_value=fxt_dataset_storage),
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model),
        ):
            result = ModelTestResultRestViews.model_test_results_to_rest(
                model_test_results=model_test_results,
                datasets_counts_per_model_test=dummy_datasets_counts_per_model_test,
            )

        # Assert
        for test_result in result["test_results"]:
            test_result["scores"].sort(key=lambda x: str(x["label_id"]))
        compare(result, fxt_model_test_results_rest, ignore_eq=True)

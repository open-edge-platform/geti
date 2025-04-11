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

"""
Converters between objects and their corresponding REST views
"""

import logging
from collections.abc import Sequence
from enum import Enum, auto
from typing import Any

from geti_types import ID
from sc_sdk.entities.dataset_storage import NullDatasetStorage
from sc_sdk.entities.metrics import ScoreMetric
from sc_sdk.entities.model import Model
from sc_sdk.entities.model_test_result import ModelTestResult, TestState

logger = logging.getLogger(__name__)


class MetricRESTEnum(Enum):
    LOCAL = auto()
    GLOBAL = auto()


class ModelTestResultRestViews:
    @staticmethod
    def _datasets_info_to_rest(
        model_test_result: ModelTestResult,
        datasets_counts: dict[ID, dict],
    ) -> list[dict[str, Any]]:
        """
        Get the REST view of list of dataset storages

        :param model_test_result: ModelTestResult object
        :param datasets_counts: Dict mapping dataset storages id with its dataset counts
        :return: List of dataset info rest views
        """
        datasets_rest = []
        dataset_storage = model_test_result.get_dataset_storages()[0]  # todo: review assumption CVS-91240
        ground_truth_dataset_id = model_test_result.ground_truth_dataset_id
        dataset_rest: dict[str, Any] = {
            "id": str(dataset_storage.id_),
            "is_deleted": True,
            "name": "",
            "n_images": 0,
            "n_frames": 0,
            "n_samples": 0,
        }
        if not isinstance(dataset_storage, NullDatasetStorage):
            dataset_per_item_count = datasets_counts.get(dataset_storage.id_, {})
            dataset_rest["is_deleted"] = False
            dataset_rest["name"] = dataset_storage.name
            if ground_truth_dataset_id is not None and dataset_per_item_count:
                dataset_rest.update(
                    {
                        "n_images": dataset_per_item_count["n_images"],
                        "n_frames": dataset_per_item_count["n_frames"],
                        "n_samples": dataset_per_item_count["n_samples"],
                    }
                )
        datasets_rest.append(dataset_rest)
        return datasets_rest

    @staticmethod
    def _model_info_to_rest(model: Model) -> dict[str, Any]:
        """
        Model info to REST view

        :param model: model entity
        :return: model info REST view
        """
        model_storage = model.model_storage
        return {
            "group_id": str(model_storage.id_),
            "id": str(model.id_),
            "template_id": str(model_storage.model_template.model_template_id),
            "task_id": str(model.model_storage.task_node_id),
            "task_type": model_storage.model_template.task_type.name,
            "n_labels": len(model.get_label_schema().get_labels(include_empty=False)),
            "optimization_type": model.optimization_type.name,
            "precision": [precision.name for precision in model.precision],
            "version": model.version,
        }

    @staticmethod
    def _job_info_to_rest(job_id: ID | None, test_state: TestState) -> dict[str, Any]:
        """
        Job info to REST view

        :param job_id: job id
        :param test_state: test state
        :return: job info REST view
        """

        return {
            "id": str(job_id) if job_id else None,
            "status": test_state.name,
        }

    @classmethod
    def scores_to_rest(cls, scores: list[ScoreMetric]) -> list[dict[str, Any]]:
        """
        Scores to REST view

        :param scores: list of scores
        :return: scores REST view
        """
        scores_rest = []
        for score in scores:
            scores_rest.append(cls._score_to_rest(score))
        return scores_rest

    @staticmethod
    def _score_to_rest(score: ScoreMetric) -> dict[str, Any]:
        """
        Score to REST view

        :param score: scores
        :return: score REST view
        """
        return {
            "name": score.name.capitalize(),
            "value": score.value,
            "label_id": str(score.label_id) if score.label_id is not None else None,
        }

    @classmethod
    def model_test_result_to_rest(
        cls,
        model_test_result: ModelTestResult,
        datasets_counts: dict[ID, dict],
    ) -> dict:
        """
        Get the REST view of model test result.

        :param model_test_result: Model test result
        :param datasets_counts: Dictionary containing the dataset items count for each
            dataset storage used in the model test.
        :return: REST view of the model test result
        """
        model_test_result_rest = {
            "id": str(model_test_result.id_),
            "name": model_test_result.name,
            "creation_time": model_test_result.creation_date.isoformat(),
            "model_info": cls._model_info_to_rest(model=model_test_result.get_model()),
            "datasets_info": cls._datasets_info_to_rest(
                model_test_result=model_test_result, datasets_counts=datasets_counts
            ),
            "scores": cls.scores_to_rest(scores=model_test_result.scores),
        }
        # the 'job_id' may be None for imported projects, but the state should be published anyway so that the
        # UI can properly visualize finished tests.
        if model_test_result.job_id is not None or model_test_result.state is TestState.DONE:
            model_test_result_rest["job_info"] = cls._job_info_to_rest(
                model_test_result.job_id, model_test_result.state
            )
        return model_test_result_rest

    @classmethod
    def model_test_results_to_rest(
        cls,
        model_test_results: Sequence[ModelTestResult],
        datasets_counts_per_model_test: dict[ID, dict[ID, dict]],
    ) -> dict[str, Any]:
        """
        Convert model test results to REST view.

        :param model_test_results: List of model test results
        :param datasets_counts_per_model_test: Dictionary containing the dataset
            items count information used in each input model test.
        :return: REST view of the model test results
        """
        return {
            "test_results": [
                cls.model_test_result_to_rest(
                    model_test_result=test_result,
                    datasets_counts=datasets_counts_per_model_test.get(test_result.id_, {}),
                )
                for test_result in model_test_results
            ]
        }

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch

import pytest

from coordination.dataset_manager.dataset_counter_config import (
    AnomalyDatasetCounterConfig,
    ClassificationDatasetCounterConfig,
    DatasetCounterConfig,
    KeypointDetectionCounterConfig,
)
from coordination.dataset_manager.missing_annotations_helper import (
    REQUIRED_ANOMALOUS_IMAGES_FIRST_TRAINING,
    MissingAnnotations,
    MissingAnnotationsHelper,
)
from entities.dataset_item_count import LabelData, NullDatasetItemCount
from storage.repos import DatasetItemCountRepo

from geti_types import ID
from iai_core.repos import ConfigurableParametersRepo, LabelSchemaRepo

WORKSPACE_ID = ID("workspace")


class TestMAHelper:
    @pytest.mark.parametrize(
        "param_fxt_task, param_fxt_config_type, param_fxt_called_method",
        [
            (
                "fxt_anomaly_detection_task",
                AnomalyDatasetCounterConfig,
                "_get_missing_annotations_anomaly_task",
            ),
            (
                "fxt_classification_task",
                ClassificationDatasetCounterConfig,
                "_get_missing_annotations_non_anomaly_task",
            ),
            (
                "fxt_keypoint_task",
                KeypointDetectionCounterConfig,
                "_get_missing_annotations_non_anomaly_task",
            ),
            (
                "fxt_detection_task",
                DatasetCounterConfig,
                "_get_missing_annotations_non_anomaly_task",
            ),
        ],
    )
    def test_get_miss_ann(
        self,
        request,
        fxt_dataset_storage,
        param_fxt_task,
        param_fxt_config_type,
        param_fxt_called_method,
        fxt_configuration,
        fxt_empty_dataset_item_count,
        fxt_missing_annotations,
    ) -> None:
        """
        Checks that the "get_missing_annotations_for_task method calls the correct type of configuration and the
        correct method to determine the missing annotations:
        Anomaly task -> AnomalyDatasetCounterConfig and _get_missing_annotations_anomaly_task method,
        Classification task -> ClassificationDatasetCounterConfig and _get_missing_annotations_non_anomaly_task
        Other -> DatasetCounterConfig and _get_missing_annotations_non_anomaly_task
        """
        task_node = request.getfixturevalue(param_fxt_task)
        with (
            patch.object(
                ConfigurableParametersRepo,
                "get_or_create_component_parameters",
                return_value=fxt_configuration,
            ),
            patch.object(
                DatasetItemCountRepo,
                "get_by_id",
                return_value=fxt_empty_dataset_item_count,
            ) as mock_get_count,
            patch.object(
                MissingAnnotationsHelper,
                param_fxt_called_method,
                return_value=fxt_missing_annotations,
            ) as mock_get_missing_annotations,
        ):
            result = MissingAnnotationsHelper.get_missing_annotations_for_task(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                task_node=task_node,
            )

            assert result == fxt_missing_annotations
            mock_get_count.assert_called_once_with(id_=task_node.id_)
            mock_get_missing_annotations.assert_called_once_with(
                dataset_item_count=fxt_empty_dataset_item_count,
                config=fxt_configuration,
            )

    def test_get_miss_ann_error(
        self,
        request,
        fxt_dataset_storage,
        fxt_configuration,
        fxt_empty_dataset_item_count,
        fxt_missing_annotations,
        fxt_detection_task,
        fxt_detection_label_schema,
    ) -> None:
        """
        Checks that the "get_missing_annotations_for_task method returns missing annotations based on an empty count
        if no DatasetItemCount is present in the repo
        """
        fxt_configuration.label_constraint_first_training = False
        fxt_configuration.required_images_auto_training = 10
        # Disable dynamic required annotations
        fxt_configuration.use_dynamic_required_annotations = False
        with (
            patch.object(
                ConfigurableParametersRepo,
                "get_or_create_component_parameters",
                return_value=fxt_configuration,
            ),
            patch.object(
                LabelSchemaRepo,
                "get_latest_view_by_task",
                return_value=fxt_detection_label_schema,
            ) as mock_get_label_schema,
            patch.object(
                DatasetItemCountRepo,
                "get_by_id",
                return_value=NullDatasetItemCount(),
            ) as mock_get_count,
        ):
            result = MissingAnnotationsHelper.get_missing_annotations_for_task(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                task_node=fxt_detection_task,
            )

            assert result == MissingAnnotations(
                total_missing_annotations_auto_training=10,
                total_missing_annotations_manual_training=3,
                missing_annotations_per_label={},
                task_label_data=[
                    LabelData.from_label(label) for label in fxt_detection_label_schema.get_labels(include_empty=False)
                ],
                n_new_annotations=0,
            )
            mock_get_count.assert_called_once_with(id_=fxt_detection_task.id_)
            mock_get_label_schema.assert_called_once_with(
                task_node_id=fxt_detection_task.id_,
            )

    @pytest.mark.parametrize(
        "label_constraint, first_training",
        [
            (True, True),
            (False, True),
            (False, False),
        ],
        ids=[
            "Training for the first time with label constraint",
            "Training for the first time with no label constraint",
            "Retraining with no label constraint",
        ],
    )
    def test_get_missing_annotations_non_anomaly_task(
        self,
        request,
        fxt_configuration,
        fxt_empty_dataset_item_count,
        fxt_label,
        label_constraint,
        first_training,
    ) -> None:
        """
        Checks that the get_missing_annotations_non_anomaly task gives the correct missing annotation values for
        different configuration values.
        """
        fxt_configuration.label_constraint_first_training = label_constraint
        fxt_configuration.required_images_auto_training = 10
        # Disable dynamic required annotations
        fxt_configuration.use_dynamic_required_annotations = False
        expected_missing_annotations = MissingAnnotations(
            total_missing_annotations_auto_training=10,
            missing_annotations_per_label={fxt_label.id_: 10} if (label_constraint and first_training) else {},
            task_label_data=fxt_empty_dataset_item_count.task_label_data,
            n_new_annotations=0,
            total_missing_annotations_manual_training=3 if first_training else 0,
        )
        if not first_training:
            fxt_empty_dataset_item_count.n_dataset_items = 10

        result = MissingAnnotationsHelper._get_missing_annotations_non_anomaly_task(
            dataset_item_count=fxt_empty_dataset_item_count,
            config=fxt_configuration,
        )

        assert result == expected_missing_annotations

    def test_get_missing_annotations_anomaly_task(
        self,
        request,
        fxt_configuration,
        fxt_empty_anomaly_dataset_item_count,
        fxt_label,
        fxt_anomalous_label,
    ) -> None:
        """
        Checks that the get_missing_annotations_anomaly_task gives the correct missing annotation values for
        different configuration values.
        """
        fxt_configuration.required_images_auto_training = 10
        expected_missing_annotations = MissingAnnotations(
            total_missing_annotations_auto_training=10,
            total_missing_annotations_manual_training=10,
            missing_annotations_per_label={
                fxt_label.id_: 10 - REQUIRED_ANOMALOUS_IMAGES_FIRST_TRAINING,
                fxt_anomalous_label.id_: REQUIRED_ANOMALOUS_IMAGES_FIRST_TRAINING,
            },
            task_label_data=fxt_empty_anomaly_dataset_item_count.task_label_data,
            n_new_annotations=0,
        )

        result = MissingAnnotationsHelper._get_missing_annotations_anomaly_task(
            dataset_item_count=fxt_empty_anomaly_dataset_item_count,
            config=fxt_configuration,
        )

        assert result == expected_missing_annotations

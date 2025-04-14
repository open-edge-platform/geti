# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import call, patch

import numpy as np
import pytest
from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.entities.datasets import Dataset
from sc_sdk.entities.subset import Subset

from jobs_common.utils.subset_management.subset_manager import (
    BATCH_SIZE_THRESHOLD,
    SUBSETS,
    TARGET_LARGE,
    TARGET_MEDIUM,
    TARGET_SMALL,
    SplitTargetSize,
    _AnomalySubsetHelper,
    _SubsetHelper,
)


def do_nothing(*args, **kwargs):
    pass


@pytest.mark.JobsComponent
class TestSubsetHelper:
    def test_split(
        self,
        fxt_task,
        fxt_label,
        fxt_configuration,
        fxt_dataset,
        fxt_dataset_item,
    ) -> None:
        dataset_item = fxt_dataset_item(subset=Subset.UNASSIGNED)
        fxt_dataset.append(dataset_item)

        with (
            patch.object(_SubsetHelper, "compute_target_ratios", return_value=np.array([1, 2, 3])),
            patch.object(_SubsetHelper, "count_item", return_value=None) as mock_count_items,
            patch.object(_SubsetHelper, "reorder_by_priority", return_value=[dataset_item]) as mock_reorder,
            patch.object(_SubsetHelper, "assign_item_to_subset", return_value=None) as mock_assign,
        ):
            subset_helper = _SubsetHelper(
                task_node=fxt_task,
                task_labels=[fxt_label],
                config=fxt_configuration,
            )

            subset_helper.split(dataset_items=fxt_dataset)

            assert subset_helper.number_of_annotations == len(fxt_dataset)
            assert all(subset_helper.target_ratios) == all(np.array([1, 2, 3]))
            mock_count_items.assert_has_calls([call(item=item) for item in fxt_dataset if item.subset in SUBSETS])
            mock_reorder.assert_not_called()
            mock_assign.assert_called_once_with(
                item=dataset_item, target_subsets=(Subset.TRAINING, Subset.VALIDATION, Subset.TESTING)
            )

    def test_split_large_dataset(
        self,
        fxt_task,
        fxt_label,
        fxt_configuration,
        fxt_dataset_item,
        fxt_mongo_id,
    ) -> None:
        dataset_item = fxt_dataset_item(0)
        dataset = Dataset(
            items=[fxt_dataset_item(i) for i in range(1, BATCH_SIZE_THRESHOLD + 2)],
            id=fxt_mongo_id(),
        )

        with (
            patch.object(_SubsetHelper, "compute_target_ratios", return_value=np.array([1, 2, 3])),
            patch.object(_SubsetHelper, "count_item", return_value=None) as mock_count_items,
            patch.object(_SubsetHelper, "reorder_by_priority", return_value=[dataset_item]) as mock_reorder,
            patch.object(_SubsetHelper, "assign_item_to_subset", return_value=None) as mock_assign,
        ):
            subset_helper = _SubsetHelper(
                task_node=fxt_task,
                task_labels=[fxt_label],
                config=fxt_configuration,
            )

            subset_helper.split(dataset_items=dataset)

            assert subset_helper.number_of_annotations == len(dataset)
            assert np.array_equal(subset_helper.target_ratios, np.array([1, 2, 3]))
            mock_count_items.assert_has_calls([call(item=item) for item in dataset if item.subset in SUBSETS])
            mock_reorder.assert_called_once_with(training_dataset_items=list(dataset))
            mock_assign.assert_has_calls([call(item=item) for item in dataset if item.subset in SUBSETS])

    def test_update_deficiencies(self, fxt_task, fxt_label, fxt_configuration) -> None:
        with (
            patch.object(_SubsetHelper, "__init__", new=do_nothing),
            patch.object(_SubsetHelper, "compute_actual_ratios", return_value=np.zeros(1)) as mock_compute_ratios,
            patch.object(_SubsetHelper, "compute_deficiencies", return_value=None) as mock_compute_deficiencies,
        ):
            subset_helper = _SubsetHelper(
                task_node=fxt_task,
                task_labels=[fxt_label],
                config=fxt_configuration,
            )

            subset_helper.update_deficiencies(subset_label_counter=np.zeros(2))

            mock_compute_ratios.assert_called_once()
            mock_compute_deficiencies.assert_called_once()

    @pytest.mark.parametrize(
        "param_fxt_subset_counter, param_fxt_ratios",
        [
            (np.array([[10, 10], [10, 10]]), np.array([[0.5, 0.5], [0.5, 0.5]])),
            (np.array([[1, 1], [9, 9]]), np.array([[0.1, 0.1], [0.9, 0.9]])),
        ],
    )
    def test_compute_actual_ratios(
        self,
        fxt_task,
        fxt_label,
        param_fxt_subset_counter,
        param_fxt_ratios,
        fxt_configuration,
    ):
        with patch.object(_SubsetHelper, "__init__", new=do_nothing):
            subset_helper = _SubsetHelper(
                task_node=fxt_task,
                task_labels=[fxt_label],
                config=fxt_configuration,
            )

            result = subset_helper.compute_actual_ratios(subset_counter=param_fxt_subset_counter)

            assert np.array_equal(result, param_fxt_ratios)

    @pytest.mark.parametrize(
        "param_fxt_actual_ratios, param_fxt_deficiencies",
        [
            (np.array([[1, 0, 0], [0, 1, 0]]), np.array([[0, 1, 1], [1, 0, 1]])),
            (
                np.array([[0.25, 0.25, 0.5], [0.5, 0.25, 0.25]]),
                np.array([[0.5, 0, 0], [0, 0, 0]]),
            ),
        ],
    )
    def test_compute_deficiencies(
        self,
        fxt_task,
        fxt_label,
        fxt_configuration,
        param_fxt_actual_ratios,
        param_fxt_deficiencies,
    ) -> None:
        with patch.object(_SubsetHelper, "__init__", new=do_nothing):
            subset_helper = _SubsetHelper(
                task_node=fxt_task,
                task_labels=[fxt_label],
                config=fxt_configuration,
            )
            subset_helper.target_ratios = np.array([0.5, 0.25, 0.25])

            result = subset_helper.compute_deficiencies(actual_ratios=param_fxt_actual_ratios)

            assert np.array_equal(result, param_fxt_deficiencies)

    def test_get_item_labels_global(
        self,
        fxt_classification_task,
        fxt_label,
        fxt_configuration,
        fxt_dataset_item,
    ) -> None:
        dataset_item = fxt_dataset_item()

        with patch.object(_SubsetHelper, "__init__", new=do_nothing):
            subset_helper = _SubsetHelper(
                task_node=fxt_classification_task,
                task_labels=[fxt_label],
                config=fxt_configuration,
            )
            subset_helper.task = fxt_classification_task

            result = subset_helper.get_item_label_ids(item=dataset_item, labels_to_get=[fxt_label])

            assert result == dataset_item.get_roi_label_ids([fxt_label.id_])

    def test_get_item_labels_local(
        self,
        fxt_detection_task,
        fxt_label,
        fxt_configuration,
        fxt_dataset_item,
    ) -> None:
        dataset_item = fxt_dataset_item()
        with patch.object(_SubsetHelper, "__init__", new=do_nothing):
            subset_helper = _SubsetHelper(
                task_node=fxt_detection_task,
                task_labels=[fxt_label],
                config=fxt_configuration,
            )
            subset_helper.task = fxt_detection_task

            result = subset_helper.get_item_label_ids(item=dataset_item, labels_to_get=[fxt_label])

            assert result == {fxt_label.id_}

    def test_assign_item_to_subset_empty_subset(self, fxt_task, fxt_label, fxt_configuration, fxt_dataset_item) -> None:
        dataset_item = fxt_dataset_item()
        with (
            patch.object(_SubsetHelper, "__init__", new=do_nothing),
            patch.object(_SubsetHelper, "count_item", return_value=None) as mock_count_item,
        ):
            subset_helper = _SubsetHelper(
                task_node=fxt_task,
                task_labels=[fxt_label],
                config=fxt_configuration,
            )
            subset_helper.task = fxt_task
            subset_helper.subset_counter = np.array([0, 1, 1])
            subset_helper.latest_task_label_ids = [fxt_label.id_]

            subset_helper.assign_item_to_subset(item=dataset_item)

            mock_count_item.assert_called_once_with(item=dataset_item, item_label_ids={fxt_label.id_})
            assert dataset_item.subset == Subset.TRAINING

    def test_assign_item_to_subset_no_empty_subset(
        self, fxt_task, fxt_label, fxt_configuration, fxt_dataset_item
    ) -> None:
        dataset_item = fxt_dataset_item()
        with (
            patch.object(_SubsetHelper, "__init__", new=do_nothing),
            patch.object(
                _SubsetHelper, "compute_potential_deficiency", return_value=[1, 0, 0]
            ) as mock_compute_deficiency,
            patch.object(_SubsetHelper, "count_item", return_value=None) as mock_count_item,
        ):
            subset_helper = _SubsetHelper(
                task_node=fxt_task,
                task_labels=[fxt_label],
                config=fxt_configuration,
            )
            subset_helper.task = fxt_task
            subset_helper.subset_counter = np.array([10, 1, 10])
            subset_helper.latest_task_labels = [fxt_label]
            subset_helper.latest_task_label_ids = [fxt_label.id_]

            subset_helper.assign_item_to_subset(item=dataset_item)

            mock_compute_deficiency.assert_has_calls(
                [call(label_ids={fxt_label.id_}, subset=subset) for subset in SUBSETS]
            )
            mock_count_item.assert_called_once_with(item=dataset_item, item_label_ids={fxt_label.id_})
            assert dataset_item.subset == Subset.VALIDATION

    def test_count_item(
        self,
        fxt_detection_task,
        fxt_label,
        fxt_configuration,
        fxt_dataset_item,
    ) -> None:
        dataset_item = fxt_dataset_item()
        dataset_item.subset = Subset.TRAINING
        with (
            patch.object(_SubsetHelper, "__init__", new=do_nothing),
            patch.object(_SubsetHelper, "update_deficiencies", return_value=None),
        ):
            subset_helper = _SubsetHelper(
                task_node=fxt_detection_task,
                task_labels=[fxt_label],
                config=fxt_configuration,
            )
            subset_helper.task = fxt_detection_task
            subset_helper.subset_label_counter = np.array([[0, 0, 0]])
            subset_helper.labels_to_index = {fxt_label.id_: 0}
            subset_helper.subset_counter = np.array([0, 0, 0])

            subset_helper.count_item(item=dataset_item, item_label_ids={fxt_label.id_})

            assert np.array_equal(subset_helper.subset_counter, np.array([1, 0, 0]))
            assert np.array_equal(subset_helper.subset_label_counter, np.array([[1, 0, 0]]))

    def test_compute_potential_deficiency(self, fxt_detection_task, fxt_label, fxt_configuration) -> None:
        with (
            patch.object(_SubsetHelper, "__init__", new=do_nothing),
            patch.object(
                _SubsetHelper,
                "compute_actual_ratios",
                return_value=np.array([0.8, 0.1, 0.1]),
            ) as mock_compute_ratios,
            patch.object(
                _SubsetHelper, "compute_deficiencies", return_value=np.array([1, 0, 0])
            ) as mock_compute_deficiencies,
        ):
            subset_helper = _SubsetHelper(
                task_node=fxt_detection_task,
                task_labels=[fxt_label],
                config=fxt_configuration,
            )
            subset_helper.subset_label_counter = np.array([[7, 1, 1]])
            subset_helper.labels_to_index = {fxt_label.id_: 0}

            result = subset_helper.compute_potential_deficiency(label_ids=[fxt_label.id_], subset=Subset.TRAINING)

            mock_compute_ratios.assert_called_once()
            mock_compute_deficiencies.assert_called_once()
            assert result == 1

    @pytest.mark.parametrize(
        "param_fxt_auto_subset_fractions, param_fxt_n_annotations, param_fxt_expected_ratios",
        [
            (True, SplitTargetSize.SMALL - 1, TARGET_SMALL),
            (True, SplitTargetSize.MEDIUM - 1, TARGET_MEDIUM),
            (True, SplitTargetSize.MEDIUM + 1, TARGET_LARGE),
            (False, None, np.array([1, 0, 0])),
        ],
    )
    def test_compute_target_ratios(
        self,
        fxt_detection_task,
        fxt_label,
        fxt_configuration,
        param_fxt_n_annotations,
        param_fxt_auto_subset_fractions,
        param_fxt_expected_ratios,
    ) -> None:
        """
        Checks that the compute_target_ratios method peroperly computes target ratios based on the size of the dataset
        and the "auto_subset_fractions parameters.
        """
        with patch.object(_SubsetHelper, "__init__", new=do_nothing):
            subset_helper = _SubsetHelper(
                task_node=fxt_detection_task,
                task_labels=[fxt_label],
                config=fxt_configuration,
            )
            fxt_configuration.auto_subset_fractions = param_fxt_auto_subset_fractions
            fxt_configuration.subset_parameters = ConfigurableParameters(header="subset_parameters")
            fxt_configuration.subset_parameters.train_proportion = 1
            fxt_configuration.subset_parameters.validation_proportion = 0
            fxt_configuration.subset_parameters.test_proportion = 0
            subset_helper.config = fxt_configuration
            subset_helper.number_of_annotations = param_fxt_n_annotations

            result = subset_helper.compute_target_ratios()

            assert np.array_equal(result, param_fxt_expected_ratios[:, np.newaxis])

    def test_reorder_by_priority(self, fxt_task, fxt_label, fxt_configuration, fxt_dataset_item) -> None:
        dataset_item_1 = fxt_dataset_item(0)
        dataset_item_2 = fxt_dataset_item(1)
        dataset_items = [dataset_item_1, dataset_item_2]
        with (
            patch.object(_SubsetHelper, "__init__", new=do_nothing),
            patch.object(_SubsetHelper, "group_by_labels", return_value=[[1, 1]]) as mock_group_by_labels,
            patch.object(
                _SubsetHelper, "compute_batch_priority", return_value=np.array([0, 1])
            ) as mock_compute_batch_prio,
            patch("numpy.random.shuffle", new=do_nothing),
        ):
            subset_helper = _SubsetHelper(
                task_node=fxt_task,
                task_labels=[fxt_label],
                config=fxt_configuration,
            )
            subset_helper.task = fxt_task
            subset_helper.subset_counter = np.array([0, 1, 1])
            subset_helper.latest_task_labels = [fxt_label]

            result = subset_helper.reorder_by_priority(training_dataset_items=dataset_items)

            assert result == [dataset_item_2, dataset_item_1]
            mock_group_by_labels.assert_called_once_with(training_dataset_items=dataset_items)
            mock_compute_batch_prio.assert_called_once_with(group_indices=[[1, 1]], n_items=2)

    def test_group_by_labels(
        self,
        fxt_detection_task,
        fxt_label,
        fxt_label_2,
        fxt_configuration,
        fxt_dataset_item,
    ) -> None:
        dataset_item_1 = fxt_dataset_item(0)
        dataset_item_2 = fxt_dataset_item(1)
        dataset_items = [dataset_item_1, dataset_item_2]
        with (
            patch.object(_SubsetHelper, "__init__", new=do_nothing),
            patch.object(
                _SubsetHelper, "get_item_label_ids", return_value={fxt_label.id_, fxt_label_2.id_}
            ) as mock_get_item_labels,
        ):
            subset_helper = _SubsetHelper(
                task_node=fxt_detection_task,
                task_labels=[fxt_label, fxt_label_2],
                config=fxt_configuration,
            )
            subset_helper.labels_to_index = {fxt_label.id_: 0, fxt_label_2.id_: 1}
            subset_helper.latest_task_labels = [fxt_label, fxt_label_2]

            result = subset_helper.group_by_labels(training_dataset_items=dataset_items)

            mock_get_item_labels.assert_has_calls(
                [call(item=item, labels_to_get=subset_helper.latest_task_labels) for item in dataset_items]
            )
            assert result == [[0, 1], [0, 1]]

    @pytest.mark.parametrize(
        "param_fxt_group_indices, param_fxt_expected_prio",
        [
            ([[0, 1], [0, 1]], [1, 1]),
            ([[0], [0]], [2, 0]),
            ([[0, 1], [0]], [1.5, 0.5]),
        ],
    )
    def test_compute_batch_priority(self, param_fxt_group_indices, param_fxt_expected_prio) -> None:
        result = _SubsetHelper.compute_batch_priority(group_indices=param_fxt_group_indices, n_items=2)

        assert np.array_equal(result, np.array(param_fxt_expected_prio))


@pytest.mark.JobsComponent
class TestAnomalySubsetHelper:
    def test_assign_item_to_subset_empty_subset(
        self,
        fxt_anomaly_detection_task,
        fxt_label,
        fxt_configuration,
        fxt_anomalous_label,
        fxt_dataset_item,
    ) -> None:
        """
        Checks that the 'assign_item_to_subset' method properly assigns anomalous items to the first empty subset,
        which is the training subset.
        """
        dataset_item = fxt_dataset_item()
        with (
            patch.object(_AnomalySubsetHelper, "__init__", new=do_nothing),
            patch.object(_AnomalySubsetHelper, "count_item", return_value=None) as mock_count_item,
        ):
            subset_helper = _AnomalySubsetHelper(
                task_node=fxt_anomaly_detection_task,
                task_labels=[fxt_label, fxt_anomalous_label],
                config=fxt_configuration,
            )
            subset_helper.task = fxt_anomaly_detection_task
            subset_helper.subset_label_counter = np.array([[0, 0, 0], [0, 0, 0]])
            subset_helper.latest_task_labels = [fxt_label, fxt_anomalous_label]
            subset_helper.latest_task_label_map = {label.id_: label for label in subset_helper.latest_task_labels}
            subset_helper.latest_task_label_ids = [fxt_label.id_, fxt_anomalous_label.id_]
            subset_helper.labels_to_index = {
                fxt_label.id_: 0,
                fxt_anomalous_label.id_: 1,
            }

            subset_helper.assign_item_to_subset(item=dataset_item)

            mock_count_item.assert_called_once_with(item=dataset_item, item_label_ids={fxt_label.id_})
            assert dataset_item.subset == Subset.TRAINING

    def test_assign_item_to_subset_empty_subset_anomaly_label(
        self,
        fxt_anomaly_detection_task,
        fxt_label,
        fxt_configuration,
        fxt_anomalous_label,
        fxt_dataset_item_anomalous,
    ) -> None:
        """
        Checks that the 'assign_item_to_subset' method properly assigns anomalous items to the first empty
        non-training subset, which is the validation subset.
        """
        dataset_item = fxt_dataset_item_anomalous()
        with (
            patch.object(_AnomalySubsetHelper, "__init__", new=do_nothing),
            patch.object(_AnomalySubsetHelper, "count_item", return_value=None) as mock_count_item,
        ):
            subset_helper = _AnomalySubsetHelper(
                task_node=fxt_anomaly_detection_task,
                task_labels=[fxt_label, fxt_anomalous_label],
                config=fxt_configuration,
            )
            subset_helper.task = fxt_anomaly_detection_task
            subset_helper.subset_label_counter = np.array([[0, 0, 0], [0, 0, 0]])
            subset_helper.latest_task_labels = [fxt_label, fxt_anomalous_label]
            subset_helper.latest_task_label_map = {label.id_: label for label in subset_helper.latest_task_labels}
            subset_helper.latest_task_label_ids = [fxt_label.id_, fxt_anomalous_label.id_]
            subset_helper.labels_to_index = {
                fxt_label.id_: 0,
                fxt_anomalous_label.id_: 1,
            }

            subset_helper.assign_item_to_subset(item=dataset_item)

            mock_count_item.assert_called_once_with(item=dataset_item, item_label_ids={fxt_anomalous_label.id_})
            assert dataset_item.subset == Subset.VALIDATION

    def test_assign_item_to_subset_no_empty_subset(
        self,
        fxt_task,
        fxt_label,
        fxt_anomalous_label,
        fxt_configuration,
        fxt_dataset_item,
    ) -> None:
        """
        Checks that the 'assign_item_to_subset' method properly assigns anomalous items to the subset with the highest
        deficiency, if there is no empty subset.
        """
        dataset_item = fxt_dataset_item()
        with (
            patch.object(_SubsetHelper, "__init__", new=do_nothing),
            patch.object(
                _AnomalySubsetHelper,
                "compute_potential_deficiency",
                return_value=[1, 0, 0],
            ) as mock_compute_deficiency,
            patch.object(_AnomalySubsetHelper, "count_item", return_value=None) as mock_count_item,
        ):
            subset_helper = _AnomalySubsetHelper(
                task_node=fxt_task,
                task_labels=[fxt_label, fxt_anomalous_label],
                config=fxt_configuration,
            )
            subset_helper.task = fxt_task
            subset_helper.subset_label_counter = np.array([[10, 2, 10], [10, 2, 10]])
            subset_helper.latest_task_labels = [fxt_label, fxt_anomalous_label]
            subset_helper.latest_task_label_map = {label.id_: label for label in subset_helper.latest_task_labels}
            subset_helper.latest_task_label_ids = [fxt_label.id_, fxt_anomalous_label.id_]
            subset_helper.labels_to_index = {
                fxt_label.id_: 0,
                fxt_anomalous_label.id_: 1,
            }

            subset_helper.assign_item_to_subset(item=dataset_item)

            mock_compute_deficiency.assert_has_calls(
                [call(label_ids={fxt_label.id_}, subset=subset) for subset in SUBSETS]
            )
            mock_count_item.assert_called_once_with(item=dataset_item, item_label_ids={fxt_label.id_})
            assert dataset_item.subset == Subset.VALIDATION

    def test_compute_target_ratios(self, fxt_detection_task, fxt_label, fxt_configuration) -> None:
        with patch.object(_AnomalySubsetHelper, "__init__", new=do_nothing):
            subset_helper = _AnomalySubsetHelper(
                task_node=fxt_detection_task,
                task_labels=[fxt_label],
                config=fxt_configuration,
            )
            fxt_configuration.subset_parameters = ConfigurableParameters(header="subset_parameters")
            fxt_configuration.subset_parameters.train_proportion = 0.8
            fxt_configuration.subset_parameters.validation_proportion = 0.1
            fxt_configuration.subset_parameters.test_proportion = 0.1
            fxt_configuration.auto_subset_fractions = False
            subset_helper.config = fxt_configuration

            result = subset_helper._compute_target_ratios()

            expected_result = np.array([[0.8, 0], [0.1, 0.5], [0.1, 0.5]])
            assert np.array_equal(result, expected_result)

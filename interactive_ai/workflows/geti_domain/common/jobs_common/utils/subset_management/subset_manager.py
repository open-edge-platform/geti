# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the subset splitting logic."""

import abc
import itertools
import logging
import math
import random
from collections.abc import Iterable, Iterator, Sequence

import numpy as np
from geti_telemetry_tools import unified_tracing
from geti_types import CTX_SESSION_VAR, ID, ProjectIdentifier
from iai_core_py.configuration.elements.component_parameters import ComponentParameters, ComponentType
from iai_core_py.entities.dataset_item import DatasetItem
from iai_core_py.entities.label import Label
from iai_core_py.entities.subset import Subset
from iai_core_py.entities.task_node import TaskNode
from iai_core_py.repos import ConfigurableParametersRepo
from iai_core_py.utils.dataset_helper import DatasetHelper
from iai_core_py.utils.type_helpers import SequenceOrSet

from .subset_manager_config import SubsetManagerConfig

logger = logging.getLogger(__name__)

# Training / validation / testing
TARGET_SMALL = np.array([0.33, 0.33, 0.33])
TARGET_MEDIUM = np.array([0.5, 0.25, 0.25])
TARGET_LARGE = np.array([0.8, 0.1, 0.1])
# Batch size criteria
BATCH_SIZE_THRESHOLD = 25
SUBSETS = (Subset.TRAINING, Subset.VALIDATION, Subset.TESTING)
SUBSET_TO_INDEX = {subset: index for index, subset in enumerate(SUBSETS)}


class SplitTargetSize:
    """
    Class to provide criteria for the dataset size.

    If config.auto_subset_fractions == True, this class is used to automatically compute
    the dataset size on the basis of the size of the split target items set.
    This is done to determine the target_ratios.
    """

    SMALL = 10
    MEDIUM = 40


class _SubsetHelper:
    """
    Helper that splits the dataset into subsets for a specific task.

    It takes into consideration the labels of dataset items when assigning subset.
    It supports single subset split and batch subset split. The batch subset split
    rearranges the order of items in the training dataset based on their scores,
    which are computed as normalized sum of all labels per image. For the rest,
    the logic is the same as for single subset split. We keep track of the subset
    ratios of each label using self.ratios. We use ratios and the targets to compute
    the deficiency of each subset for each label. Deficiency refers to the relative
    distance between the actual ratio and the target. Deficiency is 0 when the ratio
    is the same as the target and it is negative when the ratio is higher than
    the target (there is a surplus). Using deficiency as relative distance from the
    target allows us to sum the deficiencies for all subsets and labels to get a
    single score of how far the subset division is from the target. A dataset item
    can contain multiple labels but can only be assigned to a single subset.
    In order to decide which subset to assign to a dataset item, we simulate assigning
    the dataset item to each of the subsets and find the subset assignment that gets
    us closest to our target (the one with a total deficiency or score closest to 0).
    """

    def __init__(
        self,
        task_node: TaskNode,
        task_labels: list[Label],
        config: ComponentParameters[SubsetManagerConfig],
    ) -> None:
        self.task = task_node
        self.latest_task_labels = task_labels
        self.latest_task_label_ids = [label.id_ for label in task_labels]
        self.latest_task_label_map = {label.id_: label for label in task_labels}
        self.config = config

        self.subset_counter = np.zeros(len(SUBSETS))
        self.subset_label_counter = np.zeros((len(SUBSETS), len(self.latest_task_labels)))
        self.labels_to_index = {label.id_: index for index, label in enumerate(self.latest_task_labels)}
        self.ratios = np.zeros((len(SUBSETS), len(self.latest_task_labels)))
        self.deficiencies = np.ones((len(SUBSETS), len(self.latest_task_labels)))
        self.number_of_annotations = 0
        self.target_ratios = self.compute_target_ratios()

    def split(
        self,
        dataset_items: Iterable[DatasetItem],
        subsets_to_reset: tuple[Subset, ...] | None = None,
    ) -> None:
        """
        Splits a dataset into subsets
        """
        self.number_of_annotations = 0
        new_training_items = []

        if subsets_to_reset:
            # Remove any items assigned to the subsets that need to be reset
            dataset_items = self.reset_subsets_and_shuffle_items(
                dataset_items=dataset_items, eligible_subsets=subsets_to_reset, shuffle_items=True
            )

        for item in dataset_items:
            self.number_of_annotations += 1
            if item.subset in SUBSETS:
                # If the item already has been assigned a subset, count that subset
                self.count_item(item=item)
            else:
                new_training_items.append(item)

        self.target_ratios = self.compute_target_ratios()

        if len(new_training_items) >= BATCH_SIZE_THRESHOLD:
            new_training_items = self.reorder_by_priority(training_dataset_items=new_training_items)
        for item in new_training_items:
            self.assign_item_to_subset(item=item, target_subsets=subsets_to_reset if subsets_to_reset else SUBSETS)

    @staticmethod
    def reset_subsets_and_shuffle_items(
        dataset_items: Iterable[DatasetItem],
        eligible_subsets: tuple[Subset, ...],
        shuffle_items: bool = True,
    ) -> Iterable[DatasetItem]:
        """
        Reset the subset of the items and assigns them the Subset UNASSIGNED.

        :param dataset_items: Dataset items for which subset has to be removed
        :param eligible_subsets: A list of Type Subset. Items assigned to only these subsets will be unassigned
        :param shuffle_items: If set to True, the order of the dataset items will be shuffled before returning
        :return: Iterable Dataset items with their subsets reset to UNASSIGNED
        """

        # Convert dataset_items to a list to ensure consistent logging and avoid iterator exhaustion
        items = list(dataset_items)

        # Reset subset values for eligible items
        for item in items:
            if item.subset in eligible_subsets:
                item.subset = Subset.UNASSIGNED

        if shuffle_items:
            random.shuffle(items)

        return iter(items)

    def update_deficiencies(self, subset_label_counter: np.ndarray) -> None:
        """
        Update the deficiencies.

        First updates the ratios based on the subset_counter, then updates the
        deficiencies based on the ratios
        """
        self.ratios = self.compute_actual_ratios(subset_counter=subset_label_counter)
        self.deficiencies = self.compute_deficiencies(actual_ratios=self.ratios)

    @staticmethod
    def compute_actual_ratios(subset_counter: np.ndarray) -> np.ndarray:
        """
        Compute the actual subset ratios on a per-label basis.

        :param subset_counter: numpy array representing the occurrence
            of label per subset (dim: 3 x n_labels).
        :return: numpy array with ratios per label per subset (dim: 3 x n_labels).
            E.g: ratios[0][cat_label_id] contains:
            # of items with label cat in train subset / # total of items with label cat
        """
        total_per_label = subset_counter.sum(axis=0)
        ratios = subset_counter / total_per_label[np.newaxis]
        ratios[:, total_per_label <= 0] = 0
        return ratios

    def compute_deficiencies(self, actual_ratios: np.ndarray) -> np.ndarray:
        """
        Compute the deficiencies based on the subset ratios and the target ratios.

        :param actual_ratios:  numpy array representing the ratios for which
            to get the deficiency (dim: 3 x n_labels).
        :return:  numpy array representing the deficiency per label per subset
            (dim: 3 x n_labels).
            E.g: deficiencies[0][cat_label_id] contains:
            relative dist between the cat-label ratio in train subset and the target one
        """
        targets = self.target_ratios
        return np.where(
            targets <= 0,
            0,
            np.where(actual_ratios <= targets, (targets - actual_ratios) / targets, 0),
        )

    def get_item_label_ids(self, item: DatasetItem, labels_to_get: Sequence[Label]) -> set[ID]:
        """
        Return label ids relevant to the task and roi for the passed item.
        If the task is global, then the label ids are found in the roi.

        If task is local, then we traverse the shapes within the roi and collect the
        label ids for the current task.

        :param item: dataset item
        :param labels_to_get: List of labels to search for
        :return: list of relevant labels within the item's roi
        """
        label_ids_to_get = {label.id_ for label in labels_to_get}
        if self.task.task_properties.is_global:
            return item.get_roi_label_ids(label_ids_to_get)

        label_ids = set(
            itertools.chain.from_iterable(
                annotation.get_label_ids(include_empty=True) for annotation in item.get_annotations()
            )
        )
        label_ids &= label_ids_to_get
        return label_ids

    def assign_item_to_subset(self, item: DatasetItem, target_subsets: tuple[Subset, ...] = SUBSETS) -> None:
        """
        Assign an item to the best subset in two ways:
        - if a subset still does not have any items, we assign that subset to
          the dataset item
        - otherwise we decide by simulating putting the item in each subset and
          checking which assignment produces the best score (the closest to zero,
          meaning the least deficiency/surplus)

        :param item: dataset_item that needs its subset assigned
        :param target_subsets: List of subsets to regard when assigning the item to a subset. By default, all subsets
            are considered.
        """
        if target_subsets == SUBSETS:
            occurrence_counter = self.subset_counter
        else:
            # create a copy of the subset counter but remove the indices of the subsets that are not to be regarded
            occurrence_counter = np.zeros(len(target_subsets))
            for subset in SUBSETS:
                if subset in target_subsets:
                    occurrence_counter[target_subsets.index(subset)] = self.subset_counter[SUBSET_TO_INDEX[subset]]

        item_label_ids = DatasetHelper.get_dataset_item_label_ids(
            item=item,
            task_label_ids=self.latest_task_label_ids,
            is_task_global=self.task.task_properties.is_global,
            include_empty=True,
        )
        empty_subsets = [subset for subset, occurrences in zip(target_subsets, occurrence_counter) if occurrences == 0]
        if len(empty_subsets) > 0:
            item.subset = empty_subsets[0]
        else:
            # Simulate what deficiencies would look like if we added the current item to each subset
            scores = np.asarray(
                [
                    self.compute_potential_deficiency(label_ids=item_label_ids, subset=subset)
                    for subset in target_subsets
                ]
            )
            # The best score is the closest to 0 (no deficiency or surplus)
            item.subset = target_subsets[int(scores.argmin())]
        self.count_item(item=item, item_label_ids=item_label_ids)

    def count_item(self, item: DatasetItem, item_label_ids: SequenceOrSet[ID] | None = None) -> None:
        """
        After an item has its subset set, we update the state of the subset manager
        to reflect this addition.

        :param item: The item whose subset is set
        :param item_label_ids: the item's label ids. They could be retrieved from the item,
            but that's an expensive operation, so we pass them if they have
            previously been retrieved.
        """
        if item_label_ids is None and self.latest_task_label_ids is None:
            raise ValueError("Either 'item_label_ids' or 'latest_task_label_ids' must be non-null.")

        if item_label_ids is None:
            item_label_ids = DatasetHelper.get_dataset_item_label_ids(
                item=item,
                task_label_ids=self.latest_task_label_ids,
                is_task_global=self.task.task_properties.is_global,
                include_empty=True,
            )
        # Update the subset_counter and the deficiencies
        for label_id in item_label_ids:
            self.subset_label_counter[SUBSET_TO_INDEX[item.subset], self.labels_to_index[label_id]] += 1
        self.subset_counter[SUBSET_TO_INDEX[item.subset]] += 1
        self.update_deficiencies(self.subset_label_counter)

    def compute_potential_deficiency(self, label_ids: SequenceOrSet[ID], subset: Subset) -> float:
        """
        Compute potential deficiency by simulating like adding the item with given
        labels to the subset, gets ratios and deficiency that result from setting the
        item to that subset. Computes total deficiency and returns it.

        :param label_ids: the item's labels
        :param subset: the potential subset
        :return: the score, aka total deficiency
        """
        subset_label_counter = self.subset_label_counter.copy()
        for label_id in label_ids:
            subset_label_counter[SUBSET_TO_INDEX[subset]][self.labels_to_index[label_id]] += 1

        ratios = self.compute_actual_ratios(subset_counter=subset_label_counter)
        deficiencies = self.compute_deficiencies(actual_ratios=ratios)
        score = np.sum(deficiencies)
        return float(score)

    def compute_target_ratios(self) -> np.ndarray:
        """
        Return the target ratio we want to achieve based on the number of
        annotations so far.

        :return: Dictionary where: ratios[subset] = ratio for subset
        """
        if self.config.auto_subset_fractions:
            # Determine fractions automatically
            if self.number_of_annotations < SplitTargetSize.SMALL:
                ratios = TARGET_SMALL
            elif self.number_of_annotations < SplitTargetSize.MEDIUM:
                ratios = TARGET_MEDIUM
            else:
                ratios = TARGET_LARGE
        else:
            # In case manual definition is required, use values from the configuration
            ratios = np.array(
                [
                    self.config.subset_parameters.train_proportion,
                    self.config.subset_parameters.validation_proportion,
                    self.config.subset_parameters.test_proportion,
                ]
            )
            if not math.isclose(a=np.sum(ratios), b=1.0, rel_tol=1e-6):
                # if the ratios don't add up to one, we can rescale them to 1.
                if math.isclose(a=np.sum(ratios), b=0.0, abs_tol=1e-6):
                    logger.warning(
                        "The sum of the current train-valid-test ratios is 0: overriding them to equal proportions."
                    )
                    ratios = np.array([1 / 3, 1 / 3, 1 / 3])
                ratios /= np.sum(ratios)
                logger.warning(
                    "The train-valid-split ratios %s do not add up to 1.0: rescaling them accordingly",
                    str(ratios),
                )
        return ratios[:, np.newaxis]

    def reorder_by_priority(self, training_dataset_items: list[DatasetItem]) -> list[DatasetItem]:
        """
        Reorder the priority of the dataset items so that the largest annotations or
        sparse labels can be assigned first by inferring the statistics of
        the entire dataset.

        :param training_dataset_items: a list of training dataset items
        :return: a list of training dataset items reordered for batch mode split
        """
        np.random.shuffle(training_dataset_items)  # type: ignore
        groups_by_labels = self.group_by_labels(training_dataset_items=training_dataset_items)
        dataset_priorities = self.compute_batch_priority(
            group_indices=groups_by_labels, n_items=len(training_dataset_items)
        )
        return [training_dataset_items[i] for i in np.argsort(dataset_priorities)[::-1]]

    def group_by_labels(
        self,
        training_dataset_items: list[DatasetItem],
    ) -> list[list[int]]:
        """
        Group the dataset items by combination labels. This is usually returned as a
        list by creating groups for each label. If there are items for each label, it
        will be grouped by itself.

        :param training_dataset_items: a list of training dataset items
        :return: A list of grouped results by labels, indices of grouped items.
            E.g: group_by_label[0] contains: list of item indices label 0
        """
        group_by_label: list[list[int]] = [[] for _ in self.latest_task_labels]
        for item_idx, item in enumerate(training_dataset_items):
            item_label_ids = self.get_item_label_ids(item=item, labels_to_get=self.latest_task_labels)
            for label_id in item_label_ids:
                group_by_label[self.labels_to_index[label_id]].append(item_idx)
        return [v for v in group_by_label if v]

    @staticmethod
    def compute_batch_priority(group_indices: list[list[int]], n_items: int) -> np.ndarray:
        """
        Compute priority of dataset items based on score, which is calculated as
        normalized sum of all labels per image.

        :param group_indices: a group list of list(image indices)
        :param n_items: length of training dataset
        :return: a list of priority per items
            E.g: batch_priority[item_index] contains:
            item(index: item_index, int)'s priority score
        """
        # If an image has many labels, it it high priority
        # In addition, fewer labels in the entire dataset have high priorities
        dataset_priorities = np.zeros(n_items)
        for indices in group_indices:
            items, counts = np.unique(indices, return_counts=True)
            dataset_priorities[items] += counts.astype(np.float_) / len(indices)
        return dataset_priorities


class _AnomalySubsetHelper(_SubsetHelper):
    """
    Helper to split the dataset into subsets for an anomaly classification task.
    """

    def assign_item_to_subset(
        self,
        item: DatasetItem,
        target_subsets: tuple[Subset, ...] = SUBSETS,
    ) -> None:
        """
        Assign an item to the best subset in two ways:
        - if a subset still does not have any items, we assign that subset
          to the dataset item
        - otherwise we decide by simulating putting the item in each subset
          and checking which assignment produces the best score (the closest to zero,
          meaning the least deficiency/surplus)

        :param item: dataset_item that needs its subset assigned
        :param target_subsets: This parameter is unused for anomaly tasks. All subsets are considered.
        """
        if target_subsets != SUBSETS:
            logger.warning("The 'target_subsets' parameter is not used for anomaly tasks. All subsets are considered.")
        item_label_ids = DatasetHelper.get_dataset_item_label_ids(
            item=item,
            task_label_ids=self.latest_task_label_ids,
            is_task_global=self.task.task_properties.is_global,
            include_empty=True,
        )

        # Set subsets for normal and anomalous classes.
        # Anomalous class is not included in the training set.
        if any(self.latest_task_label_map[label_id].is_anomalous for label_id in item_label_ids):
            subsets = [Subset.VALIDATION, Subset.TESTING]
        else:
            subsets = [Subset.TRAINING, Subset.VALIDATION, Subset.TESTING]

        # Find which subset does not have items yet.
        subset_occurences = self.subset_label_counter[:, self.labels_to_index[next(iter(item_label_ids))]]
        empty_subsets = [
            subset for subset, occurence in zip(SUBSETS, subset_occurences) if occurence == 0 and subset in subsets
        ]

        if len(empty_subsets) > 0:
            item.subset = empty_subsets[0]
        else:
            # Simulate what deficiencies would look like if we added
            # the current item to each subset
            scores = np.asarray(
                [self.compute_potential_deficiency(label_ids=item_label_ids, subset=subset) for subset in subsets]
            )
            # The best score is the closest to 0 (no deficiency or surplus)
            item.subset = subsets[int(scores.argmin())]
        self.count_item(item=item, item_label_ids=item_label_ids)

    def _compute_target_ratios(self) -> np.ndarray:
        """
        Computes target ratios for anomaly classification. First, the normal target ratios are computed by calling
        the parent class. Then, target ratios are added specifically for anomaly labels, because these cannot be
        assigned to the training set.

        :return: 3x2 numpy array consisting of subset ratios for normal and anomalous labels
        """
        normal_ratios = super().compute_target_ratios()

        val_proportion = self.config.subset_parameters.validation_proportion / (
            self.config.subset_parameters.test_proportion + self.config.subset_parameters.validation_proportion
        )
        test_proportion = 1 - val_proportion
        anomaly_ratios = [[0], [val_proportion], [test_proportion]]

        return np.append(normal_ratios, anomaly_ratios, axis=1)


class ITaskSubsetManager(metaclass=abc.ABCMeta):
    """
    SubsetManager interface.

    It defines functions used by any SubsetManager implementation.
    """

    @staticmethod
    @abc.abstractmethod
    def split(
        dataset_items: Iterator[DatasetItem], task_node: TaskNode, subsets_to_reset: tuple[Subset, ...] | None = None
    ) -> None:
        """
        Split the training dataset to subsets such as train, val and test.

        It keeps the subset status of the items from the subset cache if applicable,
        otherwise it splits to subsets based on deficiencies.

        :param dataset_items: Dataset items to split
        :param task_node: TaskNode for which to split the dataset
        :param subsets_to_reset: Tuple of subsets to reset. The dataset items assigned to these subsets will be
            unassigned before getting split into subsets. If None, no subsets will be reset.
        """


class TaskSubsetManager(ITaskSubsetManager):
    """
    SubsetManager implementation.
    """

    @staticmethod
    @unified_tracing
    def split(
        dataset_items: Iterator[DatasetItem],
        task_node: TaskNode,
        subsets_to_reset: tuple[Subset, ...] | None = None,
    ) -> None:
        """
        Split the dataset into training, validation and testing subsets.

        :param dataset_items: Dataset items to split
        :param task_node: TaskNode for which to split the dataset
        :param subsets_to_reset: Tuple of subsets to reset. The dataset items assigned to these subsets will be
            unassigned before getting split into subsets. If None, no subsets will be reset.
        """
        workspace_id = CTX_SESSION_VAR.get().workspace_id
        project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=task_node.project_id)
        task_labels = DatasetHelper.get_latest_labels_for_task(
            project_identifier=project_identifier,
            task_node_id=task_node.id_,
            include_empty=True,
        )
        config_param_repo = ConfigurableParametersRepo(project_identifier)
        config = config_param_repo.get_or_create_component_parameters(
            data_instance_of=SubsetManagerConfig,
            component=ComponentType.SUBSET_MANAGER,
            task_id=task_node.id_,
        )
        subset_helper_type = _AnomalySubsetHelper if task_node.task_properties.is_anomaly else _SubsetHelper
        subset_helper = subset_helper_type(
            task_node=task_node,
            task_labels=task_labels,
            config=config,
        )

        # Determine subsets for resetting based on task type and configuration
        if not task_node.task_properties.is_anomaly and config.train_validation_remixing:
            # if train_validation_remixing is enabled, we need to reset the training and validation subsets
            # if subsets_to_reset is not empty, then we take a union of the subsets to reset
            subsets_to_reset = tuple(set(subsets_to_reset or []) | {Subset.TRAINING, Subset.VALIDATION})

        logger.info(f"Splitting dataset for task {task_node.id_} into subsets. Subsets to reset: {subsets_to_reset}")

        subset_helper.split(
            dataset_items=dataset_items,
            subsets_to_reset=subsets_to_reset,
        )

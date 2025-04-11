# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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
import copy
import random
from unittest.mock import patch

import numpy as np
import pytest
from geti_types import DatasetStorageIdentifier, ImageIdentifier
from sc_sdk.configuration.elements.component_parameters import ComponentParameters, ComponentType
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.dataset_entities import TaskDataset
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.datasets import Dataset
from sc_sdk.entities.image import Image
from sc_sdk.entities.label import Label
from sc_sdk.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from sc_sdk.entities.project import Project
from sc_sdk.entities.scored_label import ScoredLabel
from sc_sdk.entities.shapes import Rectangle
from sc_sdk.entities.subset import Subset
from sc_sdk.entities.task_node import TaskNode
from sc_sdk.repos import (
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    ConfigurableParametersRepo,
    DatasetRepo,
    ImageRepo,
    LabelSchemaRepo,
)
from sc_sdk.repos.dataset_entity_repo import PipelineDatasetRepo
from sc_sdk.utils.dataset_helper import DatasetHelper
from sc_sdk.utils.project_factory import ProjectFactory
from testfixtures import compare

from jobs_common.utils.dataset_helpers import DatasetHelpers
from jobs_common.utils.subset_management.subset_manager import (
    SUBSET_TO_INDEX,
    SUBSETS,
    TaskSubsetManager,
    _SubsetHelper,
)
from jobs_common.utils.subset_management.subset_manager_config import SubsetManagerConfig
from tests.test_helpers import generate_random_annotated_project, register_model_template


@pytest.mark.JobsComponent
class TestSubsetManager:
    @staticmethod
    def create_annotation(project: Project, project_labels: list[Label], labels: list[str]) -> Annotation:
        x1, y1 = random.uniform(0, 0.5), random.uniform(0, 0.5)
        if project.tasks[-1].task_properties.is_global:
            shape = Rectangle.generate_full_box()
        else:
            shape = Rectangle(x1=x1, y1=y1, x2=x1 + 0.3, y2=y1 + 0.3)
        generated_labels: list[ScoredLabel] = []
        task_label = {label.name: label for label in project_labels}
        for label in labels:
            generated_labels.append(
                ScoredLabel(label_id=task_label[label].id_, is_empty=task_label[label].is_empty, probability=1.0)
            )
        generated_annotation = Annotation(shape=shape, labels=generated_labels)
        return generated_annotation

    def create_dataset(self, project: Project, image_config: dict[str, list]) -> Dataset:
        items: list[DatasetItem] = []
        dataset_storage = project.get_training_dataset_storage()
        project_labels = LabelSchemaRepo(project.identifier).get_latest().get_labels(include_empty=False)
        for image_name, labels in image_config.items():
            # create images
            image = Image(
                name=f"{image_name}",
                uploader_id="",
                id=ImageRepo.generate_id(),
                width=100,
                height=100,
                size=100,
                preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
            )
            ImageRepo(dataset_storage.identifier).save(image)
            image_identifier = ImageIdentifier(image_id=image.id_)
            annotation = self.create_annotation(project=project, project_labels=project_labels, labels=labels)
            test_annotation = AnnotationScene(
                kind=AnnotationSceneKind.ANNOTATION,
                media_identifier=image_identifier,
                media_height=image.height,
                media_width=image.width,
                id_=AnnotationSceneRepo.generate_id(),
                annotations=[annotation],
            )
            test_dataset_item = DatasetItem(
                id_=DatasetRepo.generate_id(), media=image, annotation_scene=test_annotation
            )
            items.append(test_dataset_item)
        return Dataset(items=items, id=DatasetRepo.generate_id())

    @staticmethod
    def get_split_test_dataset_configuration(test_type: str = "single"):
        labels: list[dict] = [
            {"name": "apple", "color": "#61ff00ff"},
            {"name": "banana", "color": "#ecff00ff"},
            {"name": "orange", "color": "#ffa900ff"},
            {"name": "grape", "color": "#ba00ffff"},
            {"name": "melon", "color": "#00ff19ff"},
            {"name": "cherry", "color": "#ff0000ff"},
        ]
        data_config: dict[str, list[str]]
        if test_type == "single":
            data_config = {
                "image0": ["apple", "banana"],
                "image1": ["apple", "orange"],
                "image2": ["apple", "grape", "orange", "banana"],
                "image3": ["orange", "melon"],
                "image4": ["apple"],
                "image5": ["banana", "grape", "apple"],
                "image6": ["apple", "cherry", "melon", "grape"],
                "image7": ["banana", "orange"],
                "image8": ["melon"],
                "image9": ["apple", "banana", "orange"],
                "image10": ["apple", "cherry"],
                "image11": ["banana", "cherry"],
            }
            expected_subset_counter = np.array(
                [
                    [4.0, 3.0, 3.0, 0.0, 1.0, 1.0, 0.0],
                    [2.0, 2.0, 1.0, 1.0, 1.0, 1.0, 0.0],
                    [2.0, 1.0, 1.0, 2.0, 1.0, 1.0, 0.0],
                ]
            )
        elif test_type == "batch":
            data_config = {
                "image0": ["apple"],
                "image1": ["banana"],
                "image2": ["orange"],
                "image3": ["grape", "cherry"],
                "image4": ["apple", "melon"],
                "image5": ["banana", "apple"],
                "image6": ["apple", "orange"],
                "image7": ["apple", "grape"],
                "image8": ["banana", "orange", "cherry"],
                "image9": ["grape", "banana"],
                "image10": ["apple", "banana", "orange"],
                "image11": ["apple", "banana", "grape"],
                "image12": ["apple", "banana", "melon"],
                "image13": ["apple", "melon", "orange"],
                "image14": ["apple", "banana", "grape", "orange"],
                "image15": ["apple", "orange", "melon", "cherry"],
                "image16": ["apple", "orange", "grape"],
                "image17": ["apple", "grape", "melon"],
                "image18": ["banana", "orange", "melon"],
                "image19": ["banana", "orange", "grape"],
                "image20": ["banana", "grape", "melon"],
                "image21": ["grape", "melon"],
                "image22": ["banana", "orange", "grape", "melon"],
                "image23": ["apple", "banana", "orange", "grape", "melon"],
                "image24": ["cherry", "orange"],
                "image25": ["cherry", "apple"],
                "image26": ["banana", "apple", "cherry"],
            }
            expected_subset_counter = np.array(
                [
                    [8.0, 7.0, 6.0, 6.0, 5.0, 2.0, 0.0],
                    [4.0, 3.0, 3.0, 3.0, 2.0, 2.0, 0.0],
                    [4.0, 4.0, 4.0, 3.0, 3.0, 2.0, 0.0],
                ]
            )
        return labels, data_config, expected_subset_counter

    @staticmethod
    def assert_equal_label_distribution(
        dataset: Dataset,
        labels_for_task: list[Label],
        expected_subset_counter: np.ndarray,
    ):
        """
        Asserts that the label distribution over the various subsets in the subset
        manager is equal to the expected distribution provided in `expected_subset_counter`
        """
        actual_subset_counter = np.zeros(expected_subset_counter.shape)
        labels_to_index = {label.id_: index for index, label in enumerate(labels_for_task)}
        for item in dataset:
            for label_id in DatasetHelper.get_dataset_item_label_ids(item):
                label_index = labels_to_index[label_id]
                subset_index = SUBSET_TO_INDEX[item.subset]
                actual_subset_counter[subset_index, label_index] += 1

        assert np.array_equal(actual_subset_counter, expected_subset_counter), (
            "The distribution of labels is different from expectations"
        )

    @staticmethod
    def set_config(
        project: Project,
        task_node: TaskNode,
        auto_subset_fractions: bool | None = True,
        train_proportion: float | None = 0.5,
        validation_proportion: float | None = 0.2,
        test_proportion: float | None = 0.3,
    ):
        new_config = SubsetManagerConfig()

        new_config.auto_subset_fractions = auto_subset_fractions
        new_config.subset_parameters.train_proportion = train_proportion
        new_config.subset_parameters.test_proportion = validation_proportion
        new_config.subset_parameters.validation_proportion = test_proportion
        new_conf_params = ComponentParameters(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            component=ComponentType.SUBSET_MANAGER,
            id_=ConfigurableParametersRepo.generate_id(),
            task_id=task_node.id_,
            data=new_config,
        )
        ConfigurableParametersRepo(project.identifier).save(new_conf_params)

    @staticmethod
    def assert_equal_ratios(dataset: Dataset, expected_subsets: np.ndarray):
        actual_ratios = np.zeros(len(SUBSETS))
        for item in dataset:
            actual_ratios[SUBSET_TO_INDEX[item.subset]] += 1
        assert np.array_equal(actual_ratios, expected_subsets), (
            "Subset distribution is not equal to the expected distribution"
        )

    def test_subset_manager_detection_task_split(self, request):
        """
        <b>Description:</b>
        Tests detection task subset split with 12 images

        <b>Input data:</b>
        A custom detection project

        <b>Steps:</b>
        1. Create Project and Dataset (12 items/Subset.NONE)
        2. Check number of datasetitem
        3. Split dataset & Check Subset.NONE not in subset of dataset
        4. Compare the subsets in the dataset with Expected Result
        """
        (
            labels,
            image_config,
            expected_subset_counter,
        ) = self.get_split_test_dataset_configuration(test_type="single")
        number_of_items = 12
        project = ProjectFactory.create_project_single_task(
            name="test_subset_manager_detection_task_split",
            description="",
            creator_id="",
            labels=labels,
            model_template_id="detection",
        )
        task_node = project.get_trainable_task_nodes()[-1]
        labels_for_task = (
            LabelSchemaRepo(project.identifier)
            .get_latest_view_by_task(task_node_id=task_node.id_)
            .get_labels(include_empty=True)
        )

        # Dataset Configuration and Generation
        dataset = self.create_dataset(project=project, image_config=image_config)
        assert len(dataset) == number_of_items, f"Expected all {number_of_items} items"

        # Subset Split
        self.set_config(project=project, task_node=task_node, auto_subset_fractions=True)
        TaskSubsetManager.split(dataset_items=dataset, task_node=task_node)

        # Check the result
        assert [item for item in dataset if item.subset not in SUBSETS] == [], "Some of the items were not split"
        self.assert_equal_label_distribution(
            expected_subset_counter=expected_subset_counter,
            labels_for_task=labels_for_task,
            dataset=dataset,
        )

    def test_subset_manager_detection_task_split_with_batch(self, request):
        """
        <b>Description:</b>
        Tests detection task subset split with 27 images,
        which meet the batch mode enabling condition (# of images >= 25)

        <b>Input data:</b>
        A custom detection project

        <b>Steps:</b>
        1. Create Project and Dataset (27 items/Subset.NONE)
        2. Check number of datasetitem
        3. Split dataset
        4. Compare the subsets in the dataset with Expected Result
        """
        (
            labels,
            image_config,
            expected_subset_counter,
        ) = self.get_split_test_dataset_configuration(test_type="batch")
        number_of_items = 27
        project = ProjectFactory.create_project_single_task(
            name="test_subset_manager_detection_task_split_with_batch",
            description="",
            creator_id="",
            labels=labels,
            model_template_id="detection",
        )
        task_node = project.tasks[-1]
        labels_for_task = (
            LabelSchemaRepo(project.identifier)
            .get_latest_view_by_task(task_node_id=task_node.id_)
            .get_labels(include_empty=True)
        )

        # Dataset Configuration and Generation
        dataset = self.create_dataset(project=project, image_config=image_config)
        # subset_manager._number_of_annotations = len(dataset)
        assert len(dataset) == number_of_items, f"Expected all {number_of_items} items"

        # Subset Split
        self.set_config(project=project, task_node=task_node, auto_subset_fractions=True)
        TaskSubsetManager.split(dataset_items=dataset, task_node=task_node)

        # Check the result
        assert [item for item in dataset if item.subset not in SUBSETS] == [], "Some of the items were not split"
        self.assert_equal_label_distribution(
            expected_subset_counter=expected_subset_counter,
            labels_for_task=labels_for_task,
            dataset=dataset,
        )

    def test_subset_manager_classification_task_split(self, request):
        """
        <b>Description:</b>
        Tests classification task subset split with 12 images

        <b>Input data:</b>
        A custom classification project

        <b>Steps:</b>
        1. Create Project and Dataset (12 items/Subset.NONE)
        2. Check number of datasetitem
        3. Split dataset
        4. Compare the subsets in the dataset with Expected Result
        """
        (
            labels,
            image_config,
            expected_subset_counter,
        ) = self.get_split_test_dataset_configuration(test_type="single")
        number_of_items = 12
        register_model_template(request, type(None), "Classification", "CLASSIFICATION", trainable=True)
        project = ProjectFactory.create_project_single_task(
            name="test_subset_manager_classification_task_split",
            description="",
            creator_id="",
            labels=labels,
            model_template_id="Classification",
        )
        task_node = project.tasks[-1]
        labels_for_task = (
            LabelSchemaRepo(project.identifier)
            .get_latest_view_by_task(task_node_id=task_node.id_)
            .get_labels(include_empty=True)
        )

        # Dataset Configuration and Generation
        dataset = self.create_dataset(project=project, image_config=image_config)
        assert len(dataset) == number_of_items, f"Expected all {number_of_items} items"

        # Subset Split
        TaskSubsetManager.split(dataset_items=dataset, task_node=task_node)

        # Check the result
        assert [item for item in dataset if item.subset not in SUBSETS] == [], "Some of the items were not split"
        self.assert_equal_label_distribution(
            expected_subset_counter=expected_subset_counter,
            labels_for_task=labels_for_task,
            dataset=dataset,
        )

    def test_subset_manager_classification_task_with_batch(self, request):
        """
        <b>Description:</b>
        Tests batch subset split in classification task with 27 images,
        which meet the batch mode enabling condition (# of images >= 25)

        <b>Input data:</b>
        A custom classification project

        <b>Steps:</b>
        1. Create Project and Dataset (27 items/Subset.NONE)
        2. Check number of datasetitem
        3. Split dataset
        4. Compare the subsets in the dataset with Expected Result
        """
        (
            labels,
            image_config,
            expected_subset_counter,
        ) = self.get_split_test_dataset_configuration(test_type="batch")
        number_of_items = 27
        register_model_template(request, type(None), "classification", "CLASSIFICATION", trainable=True)
        project = ProjectFactory.create_project_single_task(
            name="test_subset_manager_classification_task_with_batch",
            description="",
            creator_id="",
            labels=labels,
            model_template_id="classification",
        )
        task_node = project.tasks[-1]
        labels_for_task = (
            LabelSchemaRepo(project.identifier)
            .get_latest_view_by_task(task_node_id=task_node.id_)
            .get_labels(include_empty=True)
        )

        # Dataset Configuration and Generation
        dataset = self.create_dataset(project=project, image_config=image_config)
        assert len(dataset) == number_of_items, f"Expected all {number_of_items} items"

        # Split into subsets
        TaskSubsetManager.split(dataset_items=dataset, task_node=task_node)

        # Check the result
        assert [item for item in dataset if item.subset not in SUBSETS] == [], "Some of the items were not split"
        self.assert_equal_label_distribution(
            expected_subset_counter=expected_subset_counter,
            labels_for_task=labels_for_task,
            dataset=dataset,
        )

    def test_subset_manager_segmentation_task_split(self, request):
        """
        <b>Description:</b>
        Tests segmentation task subset split with 12 images

        <b>Input data:</b>
        A custom segmentation project

        <b>Steps:</b>
        1. Create Project and Dataset (12 items/Subset.NONE)
        2. Check number of datasetitem
        3. Split dataset
        4. Compare the subsets in the dataset with Expected Result
        """
        (
            labels,
            image_config,
            expected_subset_counter,
        ) = self.get_split_test_dataset_configuration(test_type="single")
        number_of_items = 12
        register_model_template(request, type(None), "segmentation", "SEGMENTATION", trainable=True)
        project = ProjectFactory.create_project_single_task(
            name="test_normal_segmentation_single_subset_split",
            description="",
            creator_id="",
            labels=labels,
            model_template_id="segmentation",
        )
        task_node = project.tasks[-1]
        labels_for_task = (
            LabelSchemaRepo(project.identifier)
            .get_latest_view_by_task(task_node_id=task_node.id_)
            .get_labels(include_empty=True)
        )

        # Dataset Configuration and Generation
        dataset = self.create_dataset(project=project, image_config=image_config)
        assert len(dataset) == number_of_items, f"Expected all {number_of_items} items"

        # Subset Split
        TaskSubsetManager.split(dataset_items=dataset, task_node=task_node)

        # Check the result
        assert [item for item in dataset if item.subset not in SUBSETS] == [], "Some of the items were not split"
        self.assert_equal_label_distribution(
            expected_subset_counter=expected_subset_counter,
            labels_for_task=labels_for_task,
            dataset=dataset,
        )

    def test_subset_manager_segmentation_task_split_with_batch(self, request):
        """
        <b>Description:</b>
        Tests batch subset split in segmentation task with 27 images,
        which meet the batch mode enabling condition (# of images >= 25)

        <b>Input data:</b>
        A custom Segmentation project

        <b>Steps:</b>
        1. Create Project and Dataset (27 items/Subset.NONE)
        2. Check number of datasetitem
        3. Split dataset
        4. Compare the subsets in the dataset with Expected Result
        """
        (
            labels,
            image_config,
            expected_subset_counter,
        ) = self.get_split_test_dataset_configuration(test_type="batch")
        number_of_items = 27
        register_model_template(request, type(None), "segmentation", "SEGMENTATION", trainable=True)
        project = ProjectFactory.create_project_single_task(
            name="test_subset_manager_segmentation_task_split_with_batch",
            description="",
            creator_id="",
            labels=labels,
            model_template_id="segmentation",
        )
        task_node = project.tasks[-1]
        labels_for_task = (
            LabelSchemaRepo(project.identifier)
            .get_latest_view_by_task(task_node_id=task_node.id_)
            .get_labels(include_empty=True)
        )

        # Dataset Configuration and Generation
        dataset = self.create_dataset(project=project, image_config=image_config)
        assert len(dataset) == number_of_items, f"Expected all {number_of_items} items in the training dataset"

        # Subset Split
        TaskSubsetManager.split(dataset_items=dataset, task_node=task_node)

        # Check the result
        assert [item for item in dataset if item.subset not in SUBSETS] == [], "Some of the items were not split"
        self.assert_equal_label_distribution(
            expected_subset_counter=expected_subset_counter,
            labels_for_task=labels_for_task,
            dataset=dataset,
        )

    def test_subset_manager_with_cache(self, request):
        """
        <b>Description:</b>
        Tests whether the cached data maintains the original split status
        when there is a cache of a subset of the previous dataset

        <b>Input data:</b>
        A custom Detection project

        <b>Steps:</b>
        1. Create Project and Dataset (12 items/Subset.NONE)
        2. Check number of datasetitem
        3. Split dataset
        4. Compare the subsets in the dataset with Expected Result
        6. Create New Dataset (12 items/Subset.NONE) and add it
        7. Check number of datasetitem
        8. Split dataset
        9. Compare the subsets in the dataset with Expected Result
        """
        labels, image_config, _ = self.get_split_test_dataset_configuration(test_type="single")
        number_of_items = 12
        project = ProjectFactory.create_project_single_task(
            name="test_subset_manager_with_cache",
            description="",
            creator_id="",
            labels=labels,
            model_template_id="detection",
        )
        task_node = project.tasks[-1]

        # Dataset Configuration and Generation
        dataset = self.create_dataset(project=project, image_config=image_config)
        assert len(dataset) == number_of_items, f"Expected all {number_of_items} items"

        # Split into subsets
        TaskSubsetManager.split(dataset_items=dataset, task_node=task_node)

        # Check the result
        assert [item for item in dataset if item.subset not in SUBSETS] == [], "Some of the items were not split"

        # Add new items
        second_dataset = self.create_dataset(project=project, image_config=image_config)
        assert len(second_dataset) == number_of_items, f"Expected all {number_of_items} items"

        new_dataset = dataset + second_dataset
        assert len(new_dataset) == 2 * number_of_items, f"Expected all {number_of_items} items"

        # Split into subsets
        TaskSubsetManager.split(dataset_items=new_dataset, task_node=task_node)

        # Check the result
        expected = np.array([12.0, 7.0, 5.0])
        self.assert_equal_ratios(dataset=new_dataset, expected_subsets=expected)
        assert [item for item in dataset if item.subset not in SUBSETS] == [], "Some of the items were not split"

    def test_subset_manager_manual_target_ratios(self, request):
        """
        <b>Description:</b>
        Tests whether subset split is performed correctly with target split ratio, which is inputted by user

        <b>Input data:</b>
        A custom detection project

        <b>Steps:</b>
        1. Create Project and Dataset (27 items/Subset.NONE)
        2. Check number of datasetitem
        3. Config manual target ratio
        3. Split dataset
        4. Compare Output with expected result
        """
        labels, data_config, _ = self.get_split_test_dataset_configuration(test_type="batch")
        number_of_items = 27
        project = ProjectFactory.create_project_single_task(
            name="test_subset_manager_manual_target_ratios",
            description="",
            creator_id="",
            labels=labels,
            model_template_id="detection",
        )
        task_node = project.tasks[-1]

        dataset = self.create_dataset(project=project, image_config=data_config)
        assert len(dataset) == number_of_items, f"Expected all {number_of_items} items"

        # Update configuration
        self.set_config(
            project=project,
            task_node=task_node,
            auto_subset_fractions=False,
            train_proportion=0.7,
            validation_proportion=0.2,
            test_proportion=0.1,
        )

        # Split into subsets
        TaskSubsetManager.split(dataset_items=dataset, task_node=task_node)

        # Check the result
        expected_subsets = np.array([17, 5, 5])
        self.assert_equal_ratios(dataset=dataset, expected_subsets=expected_subsets)
        assert [item for item in dataset if item.subset not in SUBSETS] == [], "Some of the items were not split"

    def test_subset_manager_manual_target_ratios_out_of_range(self, request):
        """
        <b>Description:</b>
        Tests whether ratios with out of range handled
        when the sum of the target split ratio for subsets exceeds or is less than 1
        if proportion < 0.0 or > 1.0, ValueError
        when the sum of the target split ratio is out of range, then Rescale to sum 1

        <b>Input data:</b>
        Out of range ratio Examples

        <b>Steps:</b>
        1. Create Project and Dataset (27 items/Subset.NONE)
        2. Check number of datasetitem
        3. Config manual target ratio (ratios sum != 1)
        3. Split dataset
        4. Compare Output with expected result
        """
        labels, data_config, _ = self.get_split_test_dataset_configuration(test_type="batch")
        number_of_items = 27
        project = ProjectFactory.create_project_single_task(
            name="test_subset_manager_manual_target_ratios_out_of_range",
            description="",
            creator_id="",
            labels=labels,
            model_template_id="detection",
        )
        task_node = project.tasks[-1]

        dataset = self.create_dataset(project=project, image_config=data_config)
        assert len(dataset) == number_of_items, f"Expected all {number_of_items} items"

        # Update the configuration to set manual ratios
        self.set_config(
            project=project,
            task_node=task_node,
            auto_subset_fractions=False,
            train_proportion=0.1,
            validation_proportion=0.1,
            test_proportion=0.1,
        )

        # Split into subsets
        TaskSubsetManager.split(dataset_items=dataset, task_node=task_node)

        # Check the result
        assert [item for item in dataset if item.subset not in SUBSETS] == [], "Some of the items were not split"
        expected_subsets = np.array([9, 8, 10])
        self.assert_equal_ratios(dataset=dataset, expected_subsets=expected_subsets)

    def test_subset_manager_edge_split_3_images(self, request):
        """
        <b>Description:</b>
        Tests whether data is assigned one for each subset regardless of subset split
        ratio when there are 3 input images

        <b>Input data:</b>
        A custom detection project

        <b>Steps:</b>
        1. Create Project and Dataset(3 items/Subset.NONE)
        2. Check number of datasetitem, count subsets
        3. Split dataset & Check Subset.NONE not in subset of dataset
        4. Check if each subset has one item
        """
        labels = [
            {"name": "rectangle", "color": "#00ff00ff"},
            {"name": "ellipse", "color": "#0000ffff"},
            {"name": "triangle", "color": "#ff0000ff"},
        ]
        number_of_items = 3
        project = ProjectFactory.create_project_single_task(
            name="test_subset_manager_edge_split_3_images",
            description="",
            creator_id="",
            labels=labels,
            model_template_id="detection",
        )
        task_node = project.tasks[-1]

        # Dataset Configuration and Generation
        data_config = {
            "image0": ["rectangle", "ellipse"],
            "image1": ["rectangle", "triangle"],
            "image2": ["rectangle", "ellipse", "triangle"],
        }

        dataset = self.create_dataset(project=project, image_config=data_config)
        assert len(dataset) == number_of_items, f"Expected all {number_of_items} items in the training dataset"

        # Set manual ratios in the configuration
        self.set_config(
            project=project,
            task_node=task_node,
            auto_subset_fractions=False,
            train_proportion=0.8,
            test_proportion=0.1,
            validation_proportion=0.1,
        )

        # Split into subsets
        TaskSubsetManager.split(dataset_items=dataset, task_node=task_node)

        # Check the result
        expected_subsets = np.array([1.0, 1.0, 1.0])
        self.assert_equal_ratios(dataset=dataset, expected_subsets=expected_subsets)

    def test_subset_manager_remix_train_validation_subsets(self, request):
        """
        <b>Description:</b>
        Tests whether the subset manager can remix the train and validation subsets while keeping the test subset
        the same.

        <b>Input data:</b>
        A custom classification project with 12 images

        <b>Steps:</b>
        1. Set configurable parameters and initialize subset helper
        2. Use split twice to check if the train and validation subsets are different after the second split
        3. Check that the test subset is the same after the second split
        """

        np.random.seed(98)
        request.addfinalizer(lambda: np.random.seed(None))

        # Initiate Classification Project and TaskSubsetManager
        labels, data_config, _ = self.get_split_test_dataset_configuration(test_type="single")
        register_model_template(request, type(None), "classification", "CLASSIFICATION", trainable=True)
        project = ProjectFactory.create_project_single_task(
            name="test_subset_manager_remixing_train_validation_subsets",
            description="",
            creator_id="",
            labels=labels,
            model_template_id="classification",
        )
        task_node = project.tasks[-1]

        # Dataset Configuration and Generation
        dataset = self.create_dataset(project=project, image_config=data_config)
        items = list(dataset)

        task_labels = (
            LabelSchemaRepo(project.identifier)
            .get_latest_view_by_task(task_node_id=task_node.id_)
            .get_labels(include_empty=True)
        )
        config = ConfigurableParametersRepo(project.identifier).get_or_create_component_parameters(
            data_instance_of=SubsetManagerConfig,
            component=ComponentType.SUBSET_MANAGER,
            task_id=task_node.id_,
        )
        config.train_validation_remixing = True
        subset_helper = _SubsetHelper(
            task_node=task_node,
            config=config,
            task_labels=task_labels,
        )

        subset_helper.split(items, subsets_to_reset=(Subset.TRAINING, Subset.VALIDATION))
        items_after_split = copy.deepcopy(items)
        subset_helper.split(items, subsets_to_reset=(Subset.TRAINING, Subset.VALIDATION))

        train_split = [item.media.name for item in items if item.subset == Subset.TRAINING]
        validation_split = [item.media.name for item in items if item.subset == Subset.VALIDATION]
        test_split = [item.media.name for item in items if item.subset == Subset.TESTING]
        train_split_after = [item.media.name for item in items_after_split if item.subset == Subset.TRAINING]
        validation_split_after = [item.media.name for item in items_after_split if item.subset == Subset.VALIDATION]
        test_split_after = [item.media.name for item in items_after_split if item.subset == Subset.TESTING]

        # Confirm that the train and validation splits are different after the second split
        assert set(train_split) != set(train_split_after), "The train split is the same after the second split"
        assert set(validation_split) != set(validation_split_after), (
            "The validation split is the same after the second split"
        )
        assert set(test_split) == set(test_split_after), "The test split is different after the second split"

    def test_subset_manager_reorder_by_priority(self, request):
        """
        <b>Description:</b>
        Tests whether _reorder_by_priority function works as designed

        <b>Input data:</b>
        A custom detection project with 12 images

        <b>Steps:</b>
        1. Set configurable parameters and initialize subset helper
        2. Use _reorder_by_priority to check same length consistency of dataitem list (In & Out length check)
        """
        # Initiate Detection Project and TaskSubsetManager
        labels, data_config, _ = self.get_split_test_dataset_configuration(test_type="single")
        project = ProjectFactory.create_project_single_task(
            name="test_subset_manager_reorder_by_priority",
            description="",
            creator_id="",
            labels=labels,
            model_template_id="detection",
        )
        task_node = project.tasks[-1]

        # Dataset Configuration and Generation
        dataset = self.create_dataset(project=project, image_config=data_config)
        items = list(dataset)

        # Check that the method _reorder_by_priority works as expected
        task_labels = (
            LabelSchemaRepo(project.identifier)
            .get_latest_view_by_task(task_node_id=task_node.id_)
            .get_labels(include_empty=True)
        )
        config = ConfigurableParametersRepo(project.identifier).get_or_create_component_parameters(
            data_instance_of=SubsetManagerConfig,
            component=ComponentType.SUBSET_MANAGER,
            task_id=task_node.id_,
        )
        subset_helper = _SubsetHelper(
            task_node=task_node,
            config=config,
            task_labels=task_labels,
        )
        reordered_items = subset_helper.reorder_by_priority(
            items,
        )
        assert len(items) == len(reordered_items)

        result = [reordered_item.media.name for reordered_item in reordered_items]
        expected = [
            "image6",
            "image2",
            "image5",
            "image3",
            "image11",
            "image9",
            "image10",
            "image7",
            "image8",
            "image1",
            "image0",
            "image4",
        ]
        compare(result, expected)

    def test_subset_manager_group_by_labels(self, request):
        """
        <b>Description:</b>
        Tests whether _group_by_labels function works as designed

        <b>Input data:</b>
        A custom detection project

        <b>Steps:</b>
        1. Set configurable parameters and initialize subset helper
        2. Use _group_by_labels to check grouping well
        """
        labels = [
            {"name": "rectangle", "color": "#00ff00ff"},
            {"name": "ellipse", "color": "#0000ffff"},
            {"name": "triangle", "color": "#ff0000ff"},
        ]
        project = ProjectFactory.create_project_single_task(
            name="test_subset_manager_group_by_labels",
            description="",
            creator_id="",
            labels=labels,
            model_template_id="detection",
        )
        task_node = project.tasks[-1]

        # Case1: Normal Case
        image_config = {
            "image0": ["rectangle"],
            "image1": ["ellipse"],
            "image2": ["rectangle", "ellipse"],
            "image3": ["rectangle", "ellipse", "triangle"],
            "image4": ["rectangle"],
            "image5": ["ellipse", "rectangle"],
            "image6": ["triangle"],
        }
        dataset = self.create_dataset(project=project, image_config=image_config)
        # Check that the method _reorder_by_priority works as expected
        task_labels = (
            LabelSchemaRepo(project.identifier)
            .get_latest_view_by_task(task_node_id=task_node.id_)
            .get_labels(include_empty=True)
        )
        config = ConfigurableParametersRepo(project.identifier).get_or_create_component_parameters(
            data_instance_of=SubsetManagerConfig,
            component=ComponentType.SUBSET_MANAGER,
            task_id=task_node.id_,
        )
        subset_helper = _SubsetHelper(
            task_node=task_node,
            config=config,
            task_labels=task_labels,
        )
        items = list(dataset)
        groups = subset_helper.group_by_labels(
            items,
        )
        expected = [[0, 2, 3, 4, 5], [1, 2, 3, 5], [3, 6]]
        compare(groups, expected)

        # Case2: 1 item Case
        image_config = {
            "image0": ["rectangle"],
        }
        dataset = self.create_dataset(project=project, image_config=image_config)
        items = list(dataset)
        groups = subset_helper.group_by_labels(items)
        expected = [[0]]
        compare(groups, expected)

    def test_subset_manager_compute_batch_priority(self, request, fxt_empty_dataset):
        """
        <b>Description:</b>
        Tests whether _compute_batch_priority function works as designed

        <b>Input data:</b>
        custom group_indices(List[List[int]])

        <b>Steps:</b>
        1. Set configurable parameters and initialize subset helper
        2. Use _compute_batch_priority to check computing priority and check the result
        """
        labels = [
            {"name": "rectangle", "color": "#00ff00ff"},
            {"name": "ellipse", "color": "#0000ffff"},
            {"name": "triangle", "color": "#ff0000ff"},
        ]
        project = ProjectFactory.create_project_single_task(
            name="test_subset_manager_compute_batch_priority",
            description="",
            creator_id="",
            labels=labels,
            model_template_id="detection",
        )
        task_node = project.tasks[-1]
        task_labels = (
            LabelSchemaRepo(project.identifier)
            .get_latest_view_by_task(task_node_id=task_node.id_)
            .get_labels(include_empty=True)
        )
        config = ConfigurableParametersRepo(project.identifier).get_or_create_component_parameters(
            data_instance_of=SubsetManagerConfig,
            component=ComponentType.SUBSET_MANAGER,
            task_id=task_node.id_,
        )
        subset_helper = _SubsetHelper(
            task_node=task_node,
            config=config,
            task_labels=task_labels,
        )
        # Case 1 : empty group_indices
        test_group = []
        priority = subset_helper.compute_batch_priority(test_group, 3)
        expected = np.array([0.0, 0.0, 0.0])
        assert np.array_equal(priority, expected)

        # Case 2 : 1 by 1 case
        test_group = [[0], [1], [2]]
        priority = subset_helper.compute_batch_priority(test_group, 3)
        expected = np.array([1.0, 1.0, 1.0])
        assert np.array_equal(priority, expected)

        # Case 3 : non-1 index case
        test_group = [[0], [2]]
        priority = subset_helper.compute_batch_priority(test_group, 3)
        expected = np.array([1.0, 0.0, 1.0])
        assert np.array_equal(priority, expected)

        # Case 4 : normal indices group case
        test_group = [[2, 1, 2, 0, 3, 1, 4, 5, 7, 9], [1, 2, 3, 8], [0, 6]]
        priority = subset_helper.compute_batch_priority(test_group, 10)
        expected = np.array([0.6, 0.45, 0.45, 0.35, 0.1, 0.1, 0.5, 0.1, 0.25, 0.1])
        assert np.array_equal(priority, expected)

    def test_subset_manager_compute_actual_ratios(self, request, fxt_empty_dataset):
        """
        <b>Description:</b>
        Tests whether _compute_actual_ratios function works as designed

        <b>Input data:</b>
        custom subset_counter (np.array)

        <b>Steps:</b>
        1. Set configurable parameters and initialize subset helper
        2. Use _compute_actual_ratios to check computing well
        """
        labels = [
            {"name": "apple", "color": "#61ff00ff"},
            {"name": "banana", "color": "#ecff00ff"},
            {"name": "orange", "color": "#ffa900ff"},
            {"name": "grape", "color": "#ba00ffff"},
            {"name": "melon", "color": "#00ff19ff"},
            {"name": "cherry", "color": "#ff0000ff"},
        ]
        project = ProjectFactory.create_project_single_task(
            name="test_subset_manager_compute_actual_ratios",
            description="",
            creator_id="",
            labels=labels,
            model_template_id="detection",
        )
        task_node = project.tasks[-1]
        task_labels = (
            LabelSchemaRepo(project.identifier)
            .get_latest_view_by_task(task_node_id=task_node.id_)
            .get_labels(include_empty=True)
        )
        config = ConfigurableParametersRepo(project.identifier).get_or_create_component_parameters(
            data_instance_of=SubsetManagerConfig,
            component=ComponentType.SUBSET_MANAGER,
            task_id=task_node.id_,
        )
        subset_helper = _SubsetHelper(
            task_node=task_node,
            config=config,
            task_labels=task_labels,
        )

        # Case 1: normal 3x3 case
        subset_counter = np.array([[0.0, 1.0, 1.0], [1.0, 2.0, 1.0], [3.0, 1.0, 2.0]])
        actual_ratios = subset_helper.compute_actual_ratios(subset_counter=subset_counter)
        expected = np.array([[0.0, 0.25, 0.25], [0.25, 0.5, 0.25], [0.75, 0.25, 0.5]])
        assert np.array_equal(actual_ratios, expected), "actual_ratios is different from expectations"

        # Case 2: 0 3x3 case
        subset_counter = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
        actual_ratios = subset_helper.compute_actual_ratios(subset_counter=subset_counter)
        expected = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
        assert np.array_equal(actual_ratios, expected), "actual_ratios is different from expectations"

    def test_subset_manager_compute_deficiencies(self, request, fxt_empty_dataset):
        """
        <b>Description:</b>
        Tests whether _compute_deficiencies function works as designed

        <b>Input data:</b>
        custom subset_counter or actual_ratios(np.array)

        <b>Steps:</b>
        1. Set configurable parameters and initialize subset helper
        2. Use _compute_deficiencies to check computing well
        """
        labels: list[dict] = [
            {"name": "apple", "color": "#61ff00ff"},
            {"name": "banana", "color": "#ecff00ff"},
            {"name": "orange", "color": "#ffa900ff"},
            {"name": "grape", "color": "#ba00ffff"},
            {"name": "melon", "color": "#00ff19ff"},
            {"name": "cherry", "color": "#ff0000ff"},
        ]
        project = ProjectFactory.create_project_single_task(
            name="test_subset_manager_compute_deficiencies",
            description="",
            creator_id="",
            labels=labels,
            model_template_id="detection",
        )
        task_node = project.tasks[-1]

        self.set_config(
            project=project,
            task_node=task_node,
            auto_subset_fractions=False,
            train_proportion=0.5,
            validation_proportion=0.25,
            test_proportion=0.25,
        )
        task_labels = (
            LabelSchemaRepo(project.identifier)
            .get_latest_view_by_task(task_node_id=task_node.id_)
            .get_labels(include_empty=True)
        )
        config = ConfigurableParametersRepo(project.identifier).get_or_create_component_parameters(
            data_instance_of=SubsetManagerConfig,
            component=ComponentType.SUBSET_MANAGER,
            task_id=task_node.id_,
        )
        subset_helper = _SubsetHelper(
            task_node=task_node,
            config=config,
            task_labels=task_labels,
        )

        # Case 1: Normal Case
        subset_counter = np.array([[0.0, 1.0, 1.0], [1.0, 2.0, 1.0], [3.0, 1.0, 2.0]])
        actual_ratios = subset_helper.compute_actual_ratios(subset_counter=subset_counter)
        subset_helper.target_ratios = subset_helper.compute_target_ratios()
        deficiencies = subset_helper.compute_deficiencies(actual_ratios=actual_ratios)
        expected = np.array([[1.0, 0.5, 0.5], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
        assert np.array_equal(deficiencies, expected), "actual_ratios is different from expectations"

        # Case 2: 0 3x3 case
        actual_ratios = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
        deficiencies = subset_helper.compute_deficiencies(actual_ratios=actual_ratios)
        expected = np.array([[1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0]])
        assert np.array_equal(deficiencies, expected), "actual_ratios is different from expectations"

    def test_reshuffling_subsets(self, request):
        """
        <b>Description:</b>
        Test if the subsets' items are reshuffled when the reshuffle_subsets param is set to true
        for construct_and_save_train_dataset_for_task()

        <b>Input data:</b>
        A classification project.

        <b>Expected results:</b>
        When reshuffle_subsets is True, the dataset subsets must NOT be the same before and after calling the
        construct_and_save_train_dataset_for_task() method and vice versa

        <b>Steps</b>
        1. Create a dataset with 100 items and assign each item to TRAIN, VAL OR TEST Subset.
        2. Save the dataset
        3. Call construct_and_save_train_dataset_for_task() with reshuffle_subsets FALSE
        4. Check if the subsets with TRAIN/VAL/TEST have not changed
        6. Call construct_and_save_train_dataset_for_task() with reshuffle_subsets TRUE
        7. Check if the subsets have changed.
        """
        num_dataset_items = 100
        register_model_template(request, type(None), "classification", "CLASSIFICATION", trainable=True)
        project = generate_random_annotated_project(
            test_case=request,
            name="test_reshuffle_subsets",
            description="",
            model_template_id="classification",
            number_of_images=num_dataset_items,
            number_of_videos=0,
            image_width=224,
            image_height=224,
        )[0]

        task_node = project.get_trainable_task_nodes()[0]
        dataset_storage = project.get_training_dataset_storage()

        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
        )
        pipeline_dataset_entity = PipelineDatasetRepo.get_or_create(dataset_storage_identifier)

        annotation_scenes = list(
            AnnotationSceneRepo(dataset_storage_identifier).get_all_by_kind(
                kind=AnnotationSceneKind.ANNOTATION,
            )
        )

        # Initially, the dataset items are assigned to the subsets in a round-robin fashion
        # with these subsets
        subset_assignment_possibilities = [
            Subset.TRAINING,
            Subset.VALIDATION,
            Subset.TESTING,
            Subset.UNASSIGNED,
        ]

        dataset_items = []
        for idx, ann_scene in enumerate(annotation_scenes):
            subset_to_assign = subset_assignment_possibilities[idx % len(subset_assignment_possibilities)]

            ann_scene_state = AnnotationSceneStateRepo(dataset_storage_identifier).get_latest_for_annotation_scenes(
                annotation_scene_ids=[ann_scene.id_]
            )

            dataset_items.append(
                DatasetHelper.annotation_scene_to_dataset_item(
                    annotation_scene=ann_scene,
                    dataset_storage=dataset_storage,
                    subset=subset_to_assign,
                    annotation_scene_state=ann_scene_state.get(ann_scene.id_),
                )
            )
        request.addfinalizer(
            lambda: PipelineDatasetRepo(dataset_storage_identifier).delete_by_id(pipeline_dataset_entity.id_)
        )

        initial_dataset = Dataset(items=dataset_items, id=DatasetRepo.generate_id())

        with patch.object(TaskDataset, "get_dataset", return_value=initial_dataset):
            un_shuffled_dataset = DatasetHelpers.construct_and_save_train_dataset_for_task(
                task_dataset_entity=pipeline_dataset_entity.task_datasets[task_node.id_],
                project_id=project.id_,
                task_node=task_node,
                dataset_storage=dataset_storage,
                reshuffle_subsets=False,
            )

        initial_dataset_subsets = {
            "train": [item.media.name for item in initial_dataset if item.subset == Subset.TRAINING],
            "val": [item.media.name for item in initial_dataset if item.subset == Subset.VALIDATION],
            "test": [item.media.name for item in initial_dataset if item.subset == Subset.TESTING],
        }

        unshuffled_subset_items = {
            "train": [item.media.name for item in un_shuffled_dataset if item.subset == Subset.TRAINING],
            "val": [item.media.name for item in un_shuffled_dataset if item.subset == Subset.VALIDATION],
            "test": [item.media.name for item in un_shuffled_dataset if item.subset == Subset.TESTING],
        }

        # After constructing dataset without reshuffling, the subsets should be exactly the same
        assert initial_dataset_subsets == unshuffled_subset_items

        with patch.object(TaskDataset, "get_dataset", return_value=initial_dataset):
            shuffled_dataset = DatasetHelpers.construct_and_save_train_dataset_for_task(
                task_dataset_entity=pipeline_dataset_entity.task_datasets[task_node.id_],
                project_id=project.id_,
                task_node=task_node,
                dataset_storage=dataset_storage,
                reshuffle_subsets=True,
            )

        shuffled_dataset_subsets = {
            "train": [item.media.name for item in shuffled_dataset if item.subset == Subset.TRAINING],
            "val": [item.media.name for item in shuffled_dataset if item.subset == Subset.VALIDATION],
            "test": [item.media.name for item in shuffled_dataset if item.subset == Subset.TESTING],
        }

        # At the dataset level, all images should be there. None should be lost
        all_items_in_initial_dataset = {item.media.name for item in initial_dataset}
        all_items_in_shuffled_dataset = {item.media.name for item in shuffled_dataset}
        assert all_items_in_initial_dataset == all_items_in_shuffled_dataset

        # After constructing dataset with reshuffling, the subsets should be different
        assert initial_dataset_subsets["train"] != shuffled_dataset_subsets["train"]
        assert initial_dataset_subsets["val"] != shuffled_dataset_subsets["val"]
        assert initial_dataset_subsets["test"] != shuffled_dataset_subsets["test"]

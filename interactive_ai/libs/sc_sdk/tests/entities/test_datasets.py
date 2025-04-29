# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import copy
import os
from datetime import datetime
from pathlib import Path
from typing import cast

import cv2
import numpy as np
import pytest
from _pytest.fixtures import FixtureRequest
from testfixtures import compare

from sc_sdk.adapters.binary_interpreters import NumpyBinaryInterpreter
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.datasets import Dataset, DatasetPurpose
from sc_sdk.entities.image import Image
from sc_sdk.entities.label import Label, NullLabel
from sc_sdk.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from sc_sdk.entities.project import Project
from sc_sdk.entities.scored_label import ScoredLabel
from sc_sdk.entities.shapes import Point, Polygon, Rectangle
from sc_sdk.entities.subset import Subset
from sc_sdk.repos import AnnotationSceneRepo, DatasetRepo, ImageRepo, LabelSchemaRepo
from sc_sdk.repos.mappers.mongodb_mappers.dataset_mapper import AnnotationSceneCache
from sc_sdk.repos.storage.binary_repos import ImageBinaryRepo
from tests.entities.test_dataset_item import DatasetItemParameters
from tests.test_helpers import (
    generate_inference_dataset_of_all_media_in_project,
    generate_random_annotated_project,
    generate_training_dataset_of_all_annotated_media_in_project,
    register_model_template,
)

from geti_types import ID, ImageIdentifier


@pytest.mark.ScSdkComponent
class TestDataset:
    @staticmethod
    def __assert_equality(dataset: Dataset):
        for i, dataset_item in enumerate(dataset):
            assert id(dataset_item) == id(dataset[i]), "Expected the same object for fetching and iterating"

    @staticmethod
    def __create_project_two_images(request: FixtureRequest) -> Project:
        project = generate_random_annotated_project(
            request,
            name="__Test with altering annotations",
            description="TestDataset()",
            model_template_id="segmentation",
            number_of_images=2,
            number_of_videos=0,
        )[0]
        return project

    @staticmethod
    def generate_random_image():
        return DatasetItemParameters.generate_random_image()

    @staticmethod
    def labels() -> list[Label]:
        return DatasetItemParameters.labels()

    @staticmethod
    def annotations_entity() -> AnnotationScene:
        return DatasetItemParameters().annotations_entity()

    @staticmethod
    def metadata():
        return DatasetItemParameters.metadata()

    @staticmethod
    def default_values_dataset_item() -> DatasetItem:
        return DatasetItemParameters().default_values_dataset_item()

    @staticmethod
    def dataset_item() -> DatasetItem:
        return DatasetItemParameters().dataset_item()

    def dataset(self) -> Dataset:
        other_dataset_item = DatasetItem(
            id_=ID("other_dataset_item"),
            media=self.generate_random_image(),
            annotation_scene=self.annotations_entity(),
            metadata=self.metadata(),
            subset=Subset.VALIDATION,
        )
        items = [
            self.default_values_dataset_item(),
            self.dataset_item(),
            other_dataset_item,
        ]
        return Dataset(id=ID("dataset"), items=items, purpose=DatasetPurpose.TEMPORARY_DATASET)

    def test_dataset_entity_fetch(self):
        """
        <b>Description:</b>
        Check Dataset class "_fetch" method

        <b>Input data:</b>
        Dataset class object with specified "items" and "purpose" parameters

        <b>Expected results:</b>
        Test passes if value returned by "_fetch" method is equal to expected

        <b>Steps</b>
        1. Check value returned by "_fetch" method when list of DatasetItems indexes is specified as "key" parameter
        2. Check value returned by "_fetch" method when slice of DatasetItems indexes is specified as "key" parameter
        3. Check value returned by "_fetch" method when DatasetItem index is specified as "key" parameter
        4. Check TypeError exception is raised when unexpected type object is specified as "key" parameter
        """
        dataset = self.dataset()
        dataset_items = dataset._items
        # Checking  "_fetch" method when list of DatasetItems indexes is specified as "key" parameter
        assert dataset._fetch([0, 2]) == [dataset_items[0], dataset_items[2]]
        # Checking  "_fetch" method when slice of DatasetItems indexes is specified as "key" parameter
        assert dataset._fetch(slice(0, 3, 2)) == [dataset_items[0], dataset_items[2]]
        assert dataset._fetch(slice(-1, -4, -1)) == [
            dataset_items[2],
            dataset_items[1],
            dataset_items[0],
        ]
        # Checking  "_fetch" method when DatasetItem index is specified as "key" parameter
        assert dataset._fetch(1) == dataset_items[1]
        # Checking that TypeError exception is raised when unexpected type object is specified as "key" parameter
        with pytest.raises(TypeError):
            dataset._fetch(str)

    def test_dataset_entity_len(self):
        """
        <b>Description:</b>
        Check Dataset class "__len__" method

        <b>Input data:</b>
        Dataset class objects with specified "items" and "purpose" parameters

        <b>Expected results:</b>
        Test passes if value returned by "__len__" method is equal to expected

        <b>Steps</b>
        1. Check value returned by "__len__" method for Dataset with default optional parameters
        2. Check value returned by "__len__" method for Dataset with specified optional parameters
        """
        # Checking value returned by "__str__" method for Dataset with default optional parameters
        default_parameters_dataset = Dataset(id=ID())
        assert len(default_parameters_dataset) == 0
        # Checking value returned by "__str__" method for Dataset with specified optional parameters
        optional_parameters_dataset = self.dataset()
        assert len(optional_parameters_dataset) == 3

    def test_dataset_entity_add(self):
        """
        <b>Description:</b>
        Check Dataset class "__add__" method

        <b>Input data:</b>
        Dataset class object with specified "items" and "purpose" parameters

        <b>Expected results:</b>
        Test passes if Dataset object returned by "__add__"" method is equal to expected

        <b>Steps</b>
        1. Check Dataset object returned by "__add__"" method with Dataset specified as "other" parameter
        2. Check Dataset object returned by "__add__"" method with list of DatasetItem objects specified
        as "other" parameter
        3. Check ValueError exception is raised when unexpected type object is specified in "other" parameter of
        "__add__" method
        """
        dataset = self.dataset()
        dataset._label_schema_id = ID("label_schema_id")
        dataset_items = list(dataset._items)
        # Checking Dataset object returned by "__add__"" method with Dataset specified as "other" parameter
        other_dataset_items = [self.dataset_item(), self.dataset_item()]
        other_dataset = Dataset(
            id=ID("training_datasest"),
            items=other_dataset_items,
            label_schema_id=ID("label_schema_id"),
            purpose=DatasetPurpose.TRAINING,
        )
        new_dataset = dataset.__add__(other_dataset)
        assert new_dataset._items == dataset_items + other_dataset_items
        assert new_dataset.purpose == DatasetPurpose.TEMPORARY_DATASET
        # Checking Dataset object returned by "__add__"" method with list of DatasetItem objects specified
        # as "other" parameter
        items_to_add = [
            self.dataset_item(),
            self.dataset_item(),
            "unexpected type object",
        ]
        new_dataset = dataset.__add__(items_to_add)
        # Expected that str object will not be added to new_dataset._items
        assert new_dataset._items == dataset_items + items_to_add[0:2]
        assert new_dataset.purpose == DatasetPurpose.TEMPORARY_DATASET
        # Checking ValueError exception is raised when unexpected type object is specified in "other" parameter of
        # "__add__" method
        with pytest.raises(ValueError):
            dataset.__add__(str)

    def test_dataset_entity_getitem(self):
        """
        <b>Description:</b>
        Check Dataset class "__getitem__" method

        <b>Input data:</b>
        Dataset class object with specified "items" and "purpose" parameters

        <b>Expected results:</b>
        Test passes if value returned by "__getitem__" method is equal to expected

        <b>Steps</b>
        1. Check value returned by "__getitem__" method when index is specified as "key" parameter
        2. Check value returned by "__getitem__" method when slice is specified as "key" parameter
        """
        dataset = self.dataset()
        dataset_items = dataset._items
        # Checking value returned by "__getitem__" method when index is specified as "key" parameter
        assert dataset[1] == dataset_items[1]
        # Checking value returned by "__getitem__" method when slice is specified as "key" parameter
        assert dataset[slice(0, 3, 2)] == [dataset_items[0], dataset_items[2]]
        assert dataset[slice(-1, -4, -1)] == [
            dataset_items[2],
            dataset_items[1],
            dataset_items[0],
        ]

    def test_dataset_entity_iter(self):
        """
        <b>Description:</b>
        Check Dataset class "__iter__" method

        <b>Input data:</b>
        Dataset class object with specified "items" and "purpose" parameters

        <b>Expected results:</b>
        Test passes if DatasetItem returned by "__iter__" method is equal to expected
        """
        dataset = self.dataset()
        dataset_items = list(dataset._items)
        dataset_iterator = dataset.__iter__()
        expected_index = 0
        for expected_dataset_item in dataset_items:
            assert dataset_iterator.index == expected_index
            assert next(dataset_iterator) == expected_dataset_item
            expected_index += 1
        with pytest.raises(StopIteration):
            next(dataset_iterator)

    def test_dataset_entity_get_subset(self):
        """
        <b>Description:</b>
        Check Dataset class "get_subset" method

        <b>Input data:</b>
        Dataset class object with specified "items" and "purpose" parameters

        <b>Expected results:</b>
        Test passes if Dataset returned by "get_subset" method is equal to expected

        <b>Steps</b>
        1. Check Dataset object returned by "get_subset" method with "subset" parameter that in items of base
        dataset
        2. Check Dataset object returned by "get_subset" method with "subset" parameter that not in items of base
        dataset
        """
        validation_item = self.dataset_item()
        validation_item.subset = Subset.VALIDATION
        dataset = self.dataset()
        dataset._items.append(validation_item)
        # Checking Dataset object returned by "get_subset" method with "subset" parameter that in items of base
        # dataset
        validation_dataset = dataset.get_subset(Subset.VALIDATION)
        assert validation_dataset.purpose is dataset.purpose
        assert len(validation_dataset) == 2
        assert validation_dataset[0].subset == dataset[2].subset
        assert validation_dataset[0].media == dataset[2].media
        assert validation_dataset[0].annotation_scene == dataset[2].annotation_scene
        assert validation_dataset[1].subset == validation_item.subset
        assert validation_dataset[1].media == validation_item.media
        assert validation_dataset[1].annotation_scene == validation_item.annotation_scene
        # Checking Dataset object returned by "get_subset" method with "subset" parameter that not in items of
        # base dataset
        empty_items_dataset = dataset.get_subset(Subset.UNLABELED)
        assert empty_items_dataset.purpose is dataset.purpose
        assert empty_items_dataset._items == []

    def test_dataset_entity_remove(self):
        """
        <b>Description:</b>
        Check Dataset class "remove" method

        <b>Input data:</b>
        Dataset class object with specified "items" and "purpose" parameters

        <b>Expected results:</b>
        Test passes if "items" attribute of Dataset object is equal to expected after using "remove" method
        """
        dataset = self.dataset()
        dataset_items = list(dataset._items)
        # Removing DatasetItem included in Dataset
        dataset.remove(dataset_items[1])
        dataset_items.pop(1)
        assert dataset._items == dataset_items
        non_included_dataset_item = self.dataset_item()
        # Check that ValueError exception is raised when removing non-included DatasetItem
        with pytest.raises(ValueError):
            dataset.remove(non_included_dataset_item)

    def test_dataset_entity_append(self):
        """
        <b>Description:</b>
        Check Dataset class "append" method

        <b>Input data:</b>
        Dataset class object with specified "items" and "purpose" parameters

        <b>Expected results:</b>
        Test passes if "items" attribute of Dataset object is equal to expected after using "append" method

        <b>Steps</b>
        1. Check "items" attribute of Dataset object after adding new Dataset object
        2. Check "items" attribute of Dataset object after adding existing Dataset object
        3. Check that ValueError exception is raised when appending Dataset with "media" attribute is equal to
        "None"
        """
        dataset = self.dataset()
        expected_items = list(dataset._items)
        # Checking "items" attribute of Dataset object after adding new Dataset object
        item_to_add = self.dataset_item()
        dataset.append(item_to_add)
        expected_items.append(item_to_add)
        assert dataset._items == expected_items
        # Checking "items" attribute of Dataset object after adding existing Dataset object
        dataset.append(item_to_add)
        expected_items.append(item_to_add)
        assert dataset._items == expected_items
        # Checking that ValueError exception is raised when appending Dataset with "media" is "None" attribute
        with pytest.raises(ValueError):
            DatasetItem(ID(), None, self.annotations_entity())

    def test_dataset_entity_remove_at_indices(self):
        """
        <b>Description:</b>
        Check Dataset class "remove_at_indices" method

        <b>Input data:</b>
        Dataset class object with specified "items" and "purpose" parameters

        <b>Expected results:</b>
        Test passes if "items" attribute of Dataset object is equal to expected after using "remove_at_indices"
        method
        """
        dataset = self.dataset()
        expected_items = list(dataset._items)
        # Removing DatasetItem included in Dataset
        dataset.remove_at_indices([0, 2])
        expected_items.pop(2)
        expected_items.pop(0)
        assert dataset._items == expected_items
        # Check that IndexError exception is raised when removing DatasetItem with non-included index
        with pytest.raises(IndexError):
            dataset.remove_at_indices([20])

    def test_dataset_entity_get_label_ids(self):
        """
        <b>Description:</b>
        Check Dataset class "get_label_ids" method

        <b>Input data:</b>
        Dataset class object with specified "items" and "purpose" parameters

        <b>Expected results:</b>
        Test passes if list returned by "get_label_ids" method is equal to expected

         <b>Steps</b>
        1. Check list returned by "get_label_ids" method with "include_empty" parameter is "False"
        2. Check list returned by "get_label_ids" method with "include_empty" parameter is "True"
        """
        labels = self.labels()
        detection_label = labels[0]
        segmentation_empty_label = labels[1]
        dataset = self.dataset()
        # Checking list returned by "get_labels" method with "include_empty" parameter is "False"
        assert dataset.get_label_ids() == {detection_label.id_}
        # Checking list returned by "get_labels" method with "include_empty" parameter is "True"
        actual_empty_labels = dataset.get_label_ids(include_empty=True)
        assert len(actual_empty_labels) == 2
        assert isinstance(actual_empty_labels, set)
        assert segmentation_empty_label.id_ in actual_empty_labels
        assert detection_label.id_ in actual_empty_labels

    def test_image_dataset(self, request) -> None:
        """
        <b>Description:</b>
        Check that image datasets can be created, saved and iterated over correctly

        <b>Input data:</b>
        A random annotated project

        <b>Expected results:</b>
        Test passes if image can be retrieved from the dataset and the dataset can be saved
        without changes to the dataset.

        <b>Steps</b>
        1. Create Project and two datasets
        2. Create combined dataset and check that iteration works correctly
        3. Save and re-fetch dataset
        4. Check that iteration still works correctly
        5. Read image from dataset
        """
        project = generate_random_annotated_project(
            request,
            name="__Test dataset entities (1)",
            description="TestDataset()",
            model_template_id="classification",
            number_of_images=12,
            number_of_videos=0,
        )[0]
        dataset_storage = project.get_training_dataset_storage()
        items_1 = list(generate_training_dataset_of_all_annotated_media_in_project(project)[1][:6])
        items_2 = list(generate_training_dataset_of_all_annotated_media_in_project(project)[1][7:])

        combined_dataset = Dataset(items=items_1 + items_2, id=DatasetRepo.generate_id())
        self.__assert_equality(combined_dataset)

        assert (len(items_1) + len(items_2)) == len(combined_dataset)

        # Save, and re-fetch. Now the dataset items use an adapter
        dataset_repo = DatasetRepo(dataset_storage.identifier)
        dataset_repo.save_deep(combined_dataset)
        request.addfinalizer(lambda: dataset_repo.delete_by_id(combined_dataset.id_))

        combined_dataset = dataset_repo.get_by_id(combined_dataset.id_)
        self.__assert_equality(combined_dataset)

        dataset_items_fetched = []
        for i, dataset_item in enumerate(combined_dataset):
            dataset_items_fetched.append(dataset_item)
            if i >= 1:
                break
        dataset_items_sliced = combined_dataset[:2]
        for item_fetched, item_sliced in zip(dataset_items_fetched, dataset_items_sliced):
            assert id(item_fetched) == id(item_sliced)

        # Try to read an image from the dataset
        image = cast(Image, combined_dataset[0].media)
        image_binary_repo = ImageBinaryRepo(dataset_storage.identifier)
        data = cast(
            np.ndarray,
            image_binary_repo.get_by_filename(
                filename=image.data_binary_filename, binary_interpreter=NumpyBinaryInterpreter()
            ),
        )
        data_roi = Rectangle(
            2 / data.shape[1],
            3 / data.shape[0],
            10 / data.shape[1],
            15 / data.shape[0],
        ).crop_numpy_array(data)
        np.testing.assert_equal(data[3:15, 2:10], data_roi)

    def test_altering_dataset(self, request) -> None:
        """
        <b>Description:</b>
        Test that annotations in a dataset can be changed

        <b>Input data:</b>
        Empty Dataset

        <b>Expected results:</b>
        Test passes if Annotations in a dataset can be altered

        <b>Steps</b>
        1. Create dataset
        2. Add polygon to dataset
        3. Check that the Polygon is saved to the dataset
        """
        project = generate_random_annotated_project(
            request,
            name="__Test with altering annotations",
            description="TestDataset()",
            model_template_id="segmentation",
            number_of_images=2,
            number_of_videos=0,
        )[0]
        last_task = project.tasks[-1]
        dataset_storage = project.get_training_dataset_storage()
        # Make an inference dataset (empty annotations)
        dataset = generate_inference_dataset_of_all_media_in_project(project=project)

        # Save and re-fetch (to be sure there is a dataset adapter)
        dataset_repo = DatasetRepo(dataset_storage.identifier)
        dataset_repo.save_deep(dataset)
        request.addfinalizer(lambda: dataset_repo.delete_by_id(dataset.id_))
        dataset = dataset_repo.get_by_id(dataset.id_)  # Reload
        label_schema_repo = LabelSchemaRepo(project.identifier)
        last_task_schema = label_schema_repo.get_latest_view_by_task(task_node_id=last_task.id_)
        label = last_task_schema.get_labels(include_empty=False)[0]

        # Add polygon to an annotation
        points = [Point(0.5, 0.5), Point(0.1, 0.5), Point(0.5, 0.1)]
        polygon = Polygon(points=points)
        row_0 = dataset[0]
        num_shapes = len(dataset[0].get_annotations())
        row_0.annotation_scene.append_annotation(
            Annotation(shape=polygon, labels=[ScoredLabel(label_id=label.id_, is_empty=label.is_empty)])
        )
        assert len(row_0.get_annotations()) == num_shapes + 1, "There should be 1 polygon in the given row"

        # Re-fetch item from adapter
        row_0_again = dataset[0]
        assert len(row_0_again.get_annotations()) == num_shapes + 1, (
            "There should be 1 polygon in the row after re-fetching"
        )

        for row in dataset:
            assert len(row.get_annotations()) == 1, "There should be 1 polygon in the row after re-fetching"
            break

    def test_converting_to_list(self, request) -> None:
        """
        <b>Description:</b>
        Test that a Dataset can be converted to a list

        <b>Input data:</b>
        Dataset with two images

        <b>Expected results:</b>
        Test passes if content of dataset is the same once it is converted to a list

        <b>Steps</b>
        1. Create dataset
        2. Convert dataset to list
        """
        project = self.__create_project_two_images(request)

        # Make an inference dataset (empty annotations)
        dataset = generate_inference_dataset_of_all_media_in_project(project=project)
        items = dataset[::]
        items2 = list(dataset)
        assert items == items2
        assert len(items) == len(dataset), "Expected the list of DatasetItems to be as long as the Dataset entity"

    def test_add_operator(self, request) -> None:
        """
        <b>Description:</b>
        Test that two datasets can be combined using the "+" operator

        <b>Input data:</b>
        Two datasets with two images

        <b>Expected results:</b>
        Test passes if the datasets can be combined

        <b>Steps</b>
        1. Create datasets
        2. Combine datasets
        """
        project_a = self.__create_project_two_images(request)
        project_b = self.__create_project_two_images(request)

        # Make an inference dataset (empty annotations)
        dataset_a = generate_inference_dataset_of_all_media_in_project(project=project_a)
        dataset_b = generate_inference_dataset_of_all_media_in_project(project=project_b)

        a_plus_b = dataset_a + dataset_b  # Valid
        a_plus_b_items = dataset_a + list(dataset_b)  # Also valid
        a_plus_b.id_ = ID()
        a_plus_b_items.id_ = ID()
        assert a_plus_b == a_plus_b_items, (
            "Expected the datasets of dataset_a + dataset_b to be equal to dataset_a plus the items of dataset_b"
        )

    def test_append(self, fxt_dataset, fxt_dataset_item) -> None:
        initial_length = len(fxt_dataset)
        new_item = fxt_dataset_item(index=101)

        fxt_dataset.append(new_item)

        assert len(fxt_dataset) == initial_length + 1
        assert fxt_dataset[-1] == new_item

    def test_append_many(self, fxt_dataset, fxt_dataset_item) -> None:
        initial_length = len(fxt_dataset)
        new_items = [fxt_dataset_item(index=101), fxt_dataset_item(index=102)]

        fxt_dataset.append_many(new_items)

        assert len(fxt_dataset) == initial_length + 2
        assert fxt_dataset[-2:] == new_items

    def test_remove_operator(self, request) -> None:
        """
        <b>Description:</b>
        Test that items can be removed from the dataset

        <b>Input data:</b>
        Dataset with two images

        <b>Expected results:</b>
        Test passes if item is removed from the dataset

        <b>Steps</b>
        1. Create dataset
        2. Remove item from dataset by instance
        3. Remove item from dataset by indices
        """
        project = self.__create_project_two_images(request)
        # Make an inference dataset (empty annotations)
        dataset_a = generate_inference_dataset_of_all_media_in_project(project=project)
        len_a_before = len(dataset_a)
        dataset_a.remove(dataset_a[0])
        assert len_a_before - 1 == len(dataset_a), (
            "Expected the datasets of dataset_a to have 1 less DatasetItem after remove"
        )
        dataset_a.remove_at_indices([0])
        assert len_a_before - 2 == len(dataset_a), (
            "Expected the datasets of dataset_a to have 2 less DatasetItem after remove"
        )

    def test_dataset_item_deletion(self, request) -> None:
        """
        <b>Description:</b>
        This test verifies whether the dataset item deletion works either using dataset adapter or not.
        The verification checks after dataset[0] is deleted, the old dataset[1] should be equal to new dataset[0].

        <b>Input data:</b>
        Dataset with two images

        <b>Expected results:</b>
        Test passes if items can be deleted using either the dataset adapter or not

        <b>Steps</b>
        1. Create dataset
        2. Get dataset with adapter
        3. Delete items from dataset
        4. Re-fetch dataset
        5. Delete items from dataset
        """
        project = self.__create_project_two_images(request)
        dataset_storage = project.get_training_dataset_storage()
        # Make an inference dataset (empty annotations)
        dataset = generate_inference_dataset_of_all_media_in_project(project=project)

        # Save and re-fetch (to be sure there is a dataset adapter)
        dataset_repo = DatasetRepo(dataset_storage.identifier)
        dataset_repo.save_deep(dataset)
        request.addfinalizer(lambda: dataset_repo.delete_by_id(dataset.id_))

        dataset = dataset_repo.get_by_id(dataset.id_)

        ori_dataset_item_1 = dataset[1]
        ori_dataset_item_0 = dataset[0]
        assert ori_dataset_item_0 != ori_dataset_item_1, "Dataset items have to be different"

        # delete item 0
        dataset.remove_at_indices([0])

        # make sure the new item 0 is now the same as original item 1
        new_dataset_item_0 = dataset[0]
        assert new_dataset_item_0 == ori_dataset_item_1, "Dataset items have to be equal"

        # re-fetch
        dataset = dataset_repo.get_by_id(dataset.id_)

        ori_dataset_item_1 = dataset[1]
        ori_dataset_item_0 = dataset[0]
        assert ori_dataset_item_0 != ori_dataset_item_1, "Dataset items have to be different"

        # delete item 0
        dataset.remove_at_indices([0])

        # make sure the new item 0 is now the same as original item 1
        new_dataset_item_0 = dataset[0]
        assert new_dataset_item_0 == ori_dataset_item_1, "Dataset items have to be equal"

    def test_image_consistency(self, request, fxt_single_crate_image_dataset_for_project) -> None:
        """
        <b>Description:</b>
        Test that images are not changed when read and fetched.

        <b>Input data:</b>
        PNG image: "sc_sdk/tests/crate.png"

        <b>Expected results:</b>
        Test passes if the image from the dataset is the same as the original image

        <b>Steps</b>
        1. Create dataset and get image
        2. Read original image using OpenCV
        3. Compare both images
        """
        project = generate_random_annotated_project(
            request,
            name="__Test image consistency",
            description="TestDataset()",
            model_template_id="segmentation",
            number_of_images=0,
            number_of_videos=0,
        )[0]

        dataset_storage_identifier, dataset = fxt_single_crate_image_dataset_for_project(project)

        image = cast(Image, dataset[0].media)
        image_binary_repo = ImageBinaryRepo(dataset_storage_identifier)
        image_sc = image_binary_repo.get_by_filename(
            filename=image.data_binary_filename, binary_interpreter=NumpyBinaryInterpreter()
        )
        image_cv = cv2.imread(os.path.join(Path(__file__).parents[1], "crate.png"))

        comparison = image_sc == image_cv
        assert isinstance(comparison, np.ndarray)
        assert comparison.all()

    def test_shared_dataset(self, request) -> None:
        """
        <b>Description:</b>
        This test verifies that shared datasets are managed correctly.

        <b>Input data:</b>
        Dataset with two images

        <b>Expected results:</b>
        The test passes if after dataset[0] is deleted, the old dataset[1] is be equal to new dataset[0].

        <b>Steps</b>
        1. Create and save dataset
        2. Add shape to the first dataset item
        3. Delete dataset
        """
        project = self.__create_project_two_images(request)
        dataset_storage = project.get_training_dataset_storage()
        images = list(ImageRepo(dataset_storage.identifier).get_all())

        dataset_items = []

        # Create a first dataset item
        annotation = AnnotationScene(
            AnnotationSceneKind.ANNOTATION,
            images[0].media_identifier,
            media_height=images[0].height,
            media_width=images[0].width,
            id_=AnnotationSceneRepo.generate_id(),
        )
        roi = Annotation(Rectangle(0, 0, 0.9, 0.9), labels=[])
        dataset_items.append(
            DatasetItem(
                media=images[0],
                annotation_scene=annotation,
                roi=roi,
                id_=DatasetRepo.generate_id(),
            )
        )

        # Create a second dataset item with a different ROI on the same image (and same annotation).
        roi = Annotation(Rectangle(0.1, 0.1, 1, 1), labels=[])
        dataset_items.append(
            DatasetItem(
                media=images[0],
                annotation_scene=annotation,
                roi=roi,
                id_=DatasetRepo.generate_id(),
            )
        )

        # Create a third dataset item with a different image.
        annotation = AnnotationScene(
            AnnotationSceneKind.ANNOTATION,
            images[1].media_identifier,
            media_height=images[1].height,
            media_width=images[1].width,
            id_=AnnotationSceneRepo.generate_id(),
        )
        roi = Annotation(Rectangle(0.5, 0.5, 1, 1), labels=[])
        dataset_items.append(
            DatasetItem(
                media=images[1],
                annotation_scene=annotation,
                roi=roi,
                id_=DatasetRepo.generate_id(),
            )
        )

        # Save the dataset to Mongo
        dataset = Dataset(items=dataset_items, id=DatasetRepo.generate_id())
        dataset_repo = DatasetRepo(dataset_storage.identifier)
        dataset_repo.save_deep(dataset)

        # Reload the dataset to Mongo to ensure that the object references
        # are properly managed by Mongo in the remaining tests in this test case.
        dataset = dataset_repo.get_by_id(dataset.id_)

        # Add a shape to the first dataset item.
        # Since the first and second item share the same image, the shape should be visible in the second item too.
        box = Annotation(Rectangle(0.1, 0.2, 0.8, 0.9), labels=[ScoredLabel(NullLabel().id_, is_empty=False)])
        dataset[0].append_annotations([box])

        assert len(dataset[0].get_annotations()) == 1
        assert len(dataset[1].get_annotations()) == 1

        # However, the shape should not be visible in the third item because they are for different images.
        assert len(dataset[2].get_annotations()) == 0

        assert len(AnnotationSceneCache()._shared_annotations) == 2
        del dataset
        assert len(AnnotationSceneCache()._shared_annotations) == 0

    def test_dataset_item_get_shapes(self, request) -> None:
        """
        <b>Description:</b>
        This test checks that shapes can be retrieved correctly from each item

        <b>Input data:</b>
        Dataset with two images

        <b>Expected results:</b>
        The test passes if after dataset[0] is deleted, the old dataset[1] is be equal to new dataset[0].

        <b>Steps</b>
        1. Create and save dataset
        2. Add annotation to an image
        3. Retrieve Annotation shapes for that image
        4. Check that both shapes are equal
        5. Check subregion with only 2 shapes
        6. Check that filtering shapes by label works correctly
        7. Check t hat retrieving shapes in a ROI works correctly
        """
        project = self.__create_project_two_images(request)
        image_repo = ImageRepo(project.get_training_dataset_storage().identifier)
        label_schema_repo = LabelSchemaRepo(project.identifier)
        project_label_schema = label_schema_repo.get_latest()

        images = list(image_repo.get_all())

        label1, label2, label3 = project_label_schema.get_labels(include_empty=False)
        annotations = [
            Annotation(
                Rectangle(0.2, 0.5, 0.3, 0.6),
                [ScoredLabel(label_id=label1.id_, is_empty=label1.is_empty, probability=1.0)],
            ),
            Annotation(
                Rectangle(0.8, 0.5, 0.9, 0.6),
                [ScoredLabel(label_id=label2.id_, is_empty=label2.is_empty, probability=1.0)],
            ),
            Annotation(
                Rectangle(0.8, 0.8, 0.9, 0.9),
                [
                    ScoredLabel(label_id=label3.id_, is_empty=label3.is_empty, probability=1.0),
                    ScoredLabel(label_id=label2.id_, is_empty=label2.is_empty, probability=1.0),
                ],
            ),
        ]

        # Create a first dataset item
        annotation_scene = AnnotationScene(
            AnnotationSceneKind.ANNOTATION,
            images[0].media_identifier,
            media_height=images[0].height,
            media_width=images[0].width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=annotations,
        )
        dataset_item = DatasetItem(
            media=images[0],
            annotation_scene=annotation_scene,
            id_=DatasetRepo.generate_id(),
        )

        # Get all the shapes and compare them with the original shapes
        shapes = [annotation.shape for annotation in dataset_item.annotation_scene.annotations]
        assert shapes == annotation_scene.shapes

        # Get a subregion with only 2 shapes
        dataset_item.roi = Annotation(Rectangle(0.4, 0, 1.0, 1.0), labels=[])
        shapes = [annotation.shape for annotation in dataset_item.get_annotations()]
        compare(
            shapes,
            [
                annotation_scene.annotations[1].shape.denormalize_wrt_roi_shape(Rectangle(0.4, 0, 1.0, 1.0)),
                annotation_scene.annotations[2].shape.denormalize_wrt_roi_shape(Rectangle(0.4, 0, 1.0, 1.0)),
            ],
            ignore_eq=True,
        )

        # Try to filter by label
        # The second returned shape should be the third shape of the annotation_scene. This shape has two labels,
        # but we are selecting only one label; therefore, the returned shape should only have one label
        annotation2 = copy.deepcopy(annotation_scene.annotations[2])
        annotation2.set_labels([annotation2.get_labels()[0]])
        dataset_item.roi = Annotation(Rectangle.generate_full_box(), labels=[])
        shapes = [annotation.shape for annotation in dataset_item.get_annotations(label_ids=[label1.id_, label3.id_])]
        compare(
            shapes,
            [annotation_scene.annotations[0].shape, annotation2.shape],
            ignore_eq=True,
        )

        # Similar to the previous test, but with a ROI
        dataset_item.roi = Annotation(Rectangle(0.4, 0, 1.0, 1.0), labels=[])
        shape2 = annotation2.shape.denormalize_wrt_roi_shape(Rectangle(0.4, 0, 1.0, 1.0))
        shapes = [annotation.shape for annotation in dataset_item.get_annotations(label_ids=[label1.id_, label3.id_])]
        compare(shapes, [shape2], ignore_eq=True)

    def test_datasetitem_in_taskchain(self, request) -> None:
        """
        <b>Description:</b>
        This test will check if the get_labels and get_annotations function of the DatasetItem
        work correctly in a chain-like situation

        <b>Input data:</b>
        Randomly annotated project

        <b>Expected results:</b>
        The test passes if images can be retrieved according to the defined task chain.

        <b>Steps</b>
        1. Create project and add annotations to a DatasetItem
        2. Set the ROI of that dataset item to either a full box, the right half of the image or the left half of the
        image, and check that get_annotations() properly returns the annotations whose center falls in that half.
        3. Check that get_annotations properly rescales the annotations to the ROI.
        4. Check that the method get_roi_label_ids returns the correct labels, the labels of the annotations that fall
        into the ROI.
        """
        # Step 1
        register_model_template(request, type(None), "classification", "CLASSIFICATION", trainable=True)
        project = generate_random_annotated_project(
            request,
            name="__Test training dataset on taskchain",
            description="TestTaskChain()",
            model_template_id="classification",
        )[0]
        label_schema_repo = LabelSchemaRepo(project.identifier)
        project_label_schema = label_schema_repo.get_latest()
        project_labels = project_label_schema.get_labels(include_empty=False)
        last_task = project.tasks[-1]
        task_label_schema = label_schema_repo.get_latest_view_by_task(task_node_id=last_task.id_)
        last_task_labels = task_label_schema.get_labels(include_empty=False)
        project.get_training_dataset_storage()
        test_image = Image(
            name="Test image",
            uploader_id="",
            id=ImageRepo.generate_id(),
            width=1000,
            height=1000,
            size=100,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        annotation_in_left_half = Annotation(
            Rectangle(x1=0.0, y1=0.0, x2=0.1, y2=0.1),
            labels=[ScoredLabel(label_id=project_labels[0].id_, is_empty=project_labels[0].is_empty)],
        )
        annotation_in_right_half = Annotation(
            Rectangle(x1=0.9, y1=0.9, x2=1.0, y2=1.0),
            labels=[ScoredLabel(label_id=project_labels[1].id_, is_empty=project_labels[1].is_empty)],
        )
        annotation_slightly_left_of_middle = Annotation(
            Rectangle(x1=0.4, y1=0.4, x2=0.55, y2=0.6),
            labels=[ScoredLabel(label_id=project_labels[2].id_, is_empty=project_labels[2].is_empty)],
        )
        annotations = [
            annotation_in_left_half,
            annotation_in_right_half,
            annotation_slightly_left_of_middle,
        ]

        # Step 2
        left_half_roi = Annotation(Rectangle(x1=0.0, y1=0.0, x2=0.5, y2=1.0), labels=[])
        right_half_roi = Annotation(Rectangle(x1=0.5, y1=0.0, x2=1, y2=1), labels=[])
        test_annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=ImageIdentifier(test_image.id_),
            media_height=test_image.height,
            media_width=test_image.width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=annotations,
        )
        test_dataset_item_full = DatasetItem(
            id_=DatasetRepo.generate_id(), media=test_image, annotation_scene=test_annotation_scene
        )
        test_dataset_item_left_half = DatasetItem(
            id_=DatasetRepo.generate_id(), media=test_image, annotation_scene=test_annotation_scene, roi=left_half_roi
        )
        test_dataset_item_right_half = DatasetItem(
            id_=DatasetRepo.generate_id(), media=test_image, annotation_scene=test_annotation_scene, roi=right_half_roi
        )

        assert len(test_dataset_item_full.get_annotations()) == 3
        assert len(test_dataset_item_left_half.get_annotations()) == 2
        assert len(test_dataset_item_right_half.get_annotations()) == 1

        # Step 3
        out_of_bounds_shape = test_dataset_item_left_half.get_annotations()[1].shape
        assert isinstance(out_of_bounds_shape, Rectangle)
        assert out_of_bounds_shape.x2 == 1.1

        # Step 4
        label = project_labels[0]
        test_dataset_item_left_half.append_labels(
            [ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=0.5)]
        )
        test_label_id = list(
            test_dataset_item_left_half.get_roi_label_ids(label_ids=[label.id_ for label in last_task_labels])
        )[0]
        assert test_label_id == label.id_

    def test_dataset_item_validate_crops(self, request, freezer, fxt_dataset_item_no_annotations) -> None:
        """
        <b>Description:</b>
        Checks whether boxes that are too small will be added as empty boxes
        We now allow dimensionless shapes, see CVS-155635 and CVS-161730

        <b>Input data:</b>
        Dataset with empty annotations

        <b>Expected results:</b>
        The test passes if both annotations are added to the dataset item

        <b>Steps</b>
        1. Create normal rectangle and very small rectangle
        2. Add boxes to dataset item
        """
        freezer.move_to(datetime(year=1970, month=1, day=1))
        annotation1 = Annotation(
            Polygon([Point(0.0, 0.0), Point(0.0, 0.5), Point(0.0, 0.75), Point(0.5, 0.5)]),
            labels=[ScoredLabel(NullLabel().id_, is_empty=False)],
        )
        annotation2 = Annotation(
            Polygon(
                [
                    Point(0.0, 0.0),
                    Point(0.0, 0.000001),
                    Point(0.000001, 0.0),
                    Point(0.000001, 0.000001),
                ]
            ),
            labels=[ScoredLabel(NullLabel().id_, is_empty=False)],
        )
        # Shape 2 will produce an empty cropped rectangle, as the points are really close together
        fxt_dataset_item_no_annotations.append_annotations([annotation1, annotation2])

        annotations = fxt_dataset_item_no_annotations.get_annotations()
        assert len(annotations) == 2
        assert annotations[0].id_ != annotation1.id_
        compare(annotations[0].shape, annotation1.shape)
        compare(annotations[0].get_labels(), annotation1.get_labels())

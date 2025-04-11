# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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
import os

import cv2
import pytest
from _pytest.fixtures import FixtureRequest

from sc_sdk.adapters.binary_interpreters import NumpyBinaryInterpreter
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.datasets import Dataset, DatasetIdentifier
from sc_sdk.entities.image import Image
from sc_sdk.entities.label import Label
from sc_sdk.entities.media import ImageExtensions, MediaPreprocessing, MediaPreprocessingStatus
from sc_sdk.entities.project import Project
from sc_sdk.entities.subset import Subset
from sc_sdk.repos import AnnotationSceneRepo, DatasetRepo, ImageRepo
from sc_sdk.repos.storage.binary_repos import ImageBinaryRepo
from tests import test_helpers

from .values import DummyValues
from geti_types import DatasetStorageIdentifier, ImageIdentifier


@pytest.fixture
def fxt_dataset_item_no_annotations(fxt_image_entity, fxt_annotation_scene_empty):
    yield DatasetItem(
        media=fxt_image_entity,
        annotation_scene=fxt_annotation_scene_empty,
        id_=DatasetRepo.generate_id(),
    )


@pytest.fixture
def fxt_dataset_item_no_annotations_2(fxt_video_frame, fxt_annotation_scene_empty):
    yield DatasetItem(
        media=fxt_video_frame,
        annotation_scene=fxt_annotation_scene_empty,
        id_=DatasetRepo.generate_id(),
    )


@pytest.fixture
def fxt_dataset_single_item(fxt_dataset_storage, fxt_dataset_item_no_annotations):
    yield Dataset(items=[fxt_dataset_item_no_annotations], id=DatasetRepo.generate_id())


@pytest.fixture
def fxt_single_crate_image_dataset_for_project(request):
    def _create_dataset(
        project: Project, annotations: list[Annotation] | None = None
    ) -> tuple[DatasetStorageIdentifier, Dataset]:
        dataset_storage = project.get_training_dataset_storage()
        image_repo = ImageRepo(dataset_storage.identifier)
        image_binary_repo = ImageBinaryRepo(dataset_storage.identifier)
        ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
        image = cv2.imread(os.path.join(os.path.dirname(test_helpers.__file__), "crate.png"))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        image_id = ImageRepo.generate_id()
        extension = ImageExtensions.PNG
        filename = f"{str(image_id)}{extension.value}"
        binary_filename = image_binary_repo.save(
            dst_file_name=filename,
            data_source=NumpyBinaryInterpreter.get_bytes_from_numpy(image_numpy=image, extension=extension.value),
        )
        size = image_binary_repo.get_object_size(binary_filename)
        test_image = Image(
            name="random_image",
            uploader_id="",
            creation_date=DummyValues.CREATION_DATE,
            id=image_id,
            width=image.shape[1],
            height=image.shape[0],
            size=size,
            extension=extension,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        image_repo.save(test_image)
        request.addfinalizer(lambda: image_repo.delete_by_id(test_image.id_))
        request.addfinalizer(lambda: image_binary_repo.delete_by_filename(binary_filename))
        image_identifier = ImageIdentifier(image_id=test_image.id_)

        test_annotation = AnnotationScene(
            kind=AnnotationSceneKind.PREDICTION,
            media_identifier=image_identifier,
            media_height=test_image.height,
            media_width=test_image.width,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=annotations,
        )
        ann_scene_repo.save(test_annotation)
        request.addfinalizer(lambda: ann_scene_repo.delete_by_id(test_annotation.id_))

        test_dataset_item = DatasetItem(
            media=test_image,
            annotation_scene=test_annotation,
            id_=DatasetRepo.generate_id(),
        )
        return dataset_storage.identifier, Dataset(items=[test_dataset_item], id=DatasetRepo.generate_id())

    yield _create_dataset


@pytest.fixture
def fxt_single_random_classification_row(
    request: FixtureRequest,
    fxt_classification_labels_persisted,
    fxt_random_annotated_image_factory,
):
    def _dataset_item_factory(
        project: Project,
        labels: list[Label] | None = None,
        subset: Subset = Subset.UNLABELED,
    ) -> DatasetItem:
        """
        Generates a random image for classification. The class is based on the type of
        shapes (rectangle, circle, triangle) in the image.

        :param project: Project in which to generate the dataset item
        :param labels: Classification labels to add to the image. If left unspecified,
            the default classification labels ['rectangle', 'circle', 'triangle']
            will be used.
        :param subset: subset to which the image should go
        :return: DatasetItem with associated Image, AnnotationScene and shapes
        """
        dataset_storage = project.get_training_dataset_storage()
        image_repo = ImageRepo(dataset_storage.identifier)
        image_binary_repo = ImageBinaryRepo(dataset_storage.identifier)
        ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)

        if labels is None:
            labels = fxt_classification_labels_persisted(project.identifier)
        image_array, annotations = fxt_random_annotated_image_factory(
            image_width=512,
            image_height=384,
            labels=labels,
        )
        image_id = ImageRepo.generate_id()
        extension = ImageExtensions.PNG
        filename = f"{str(image_id)}{extension.value}"
        binary_filename = image_binary_repo.save(
            dst_file_name=filename,
            data_source=NumpyBinaryInterpreter.get_bytes_from_numpy(image_numpy=image_array, extension=extension.value),
        )
        size = image_binary_repo.get_object_size(binary_filename)
        test_image = Image(
            name="random_image",
            uploader_id="",
            creation_date=DummyValues.CREATION_DATE,
            id=image_id,
            width=image_array.shape[1],
            height=image_array.shape[0],
            size=size,
            extension=extension,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        image_repo.save(test_image)
        request.addfinalizer(lambda: image_repo.delete_by_id(test_image.id_))
        request.addfinalizer(lambda: image_binary_repo.delete_by_filename(binary_filename))

        image_identifier = ImageIdentifier(test_image.id_)
        test_annotation = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=image_identifier,
            media_height=test_image.height,
            media_width=test_image.width,
            id_=AnnotationSceneRepo.generate_id(),
            last_annotator_id=DummyValues.CREATOR_NAME,
            creation_date=DummyValues.CREATION_DATE,
            annotations=annotations,
        )
        ann_scene_repo.save(test_annotation)
        request.addfinalizer(lambda: ann_scene_repo.delete_by_id(test_annotation.id_))

        row = DatasetItem(
            media=test_image,
            annotation_scene=test_annotation,
            subset=subset,
            id_=DatasetRepo.generate_id(),
        )
        return row

    yield _dataset_item_factory


@pytest.fixture
def fxt_dataset_item(fxt_image_entity_factory, fxt_annotation_scene):
    """
    DatasetItem with a media and annotation
    The subset can be specified by parameter.
    """

    def _build_item(index: int = 1, subset: Subset = Subset.NONE, cropped: bool = False):
        roi = fxt_annotation_scene.annotations[0] if cropped else None
        return DatasetItem(
            media=fxt_image_entity_factory(index=index),
            annotation_scene=fxt_annotation_scene,
            roi=roi,
            subset=subset,
            id_=DatasetRepo.generate_id(),
        )

    yield _build_item


@pytest.fixture
def fxt_dataset(fxt_dataset_item, fxt_dataset_storage, fxt_mongo_id):
    """Dataset with 3 items, belonging to train, valid and test subsets, respectively"""

    items = [
        fxt_dataset_item(index=1, subset=Subset.TRAINING),
        fxt_dataset_item(index=2, subset=Subset.VALIDATION),
        fxt_dataset_item(index=3, subset=Subset.TESTING),
    ]
    dataset = Dataset(items=items, id=fxt_mongo_id(1))
    yield dataset


@pytest.fixture
def fxt_dataset_identifier(fxt_dataset_storage, fxt_dataset):
    yield DatasetIdentifier.from_ds_identifier(
        dataset_storage_identifier=fxt_dataset_storage.identifier,
        dataset_id=fxt_dataset.id_,
    )

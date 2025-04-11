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
import pytest
from _pytest.fixtures import FixtureRequest
from geti_types import CTX_SESSION_VAR, DatasetStorageIdentifier, ImageIdentifier, ProjectIdentifier
from sc_sdk.entities.annotation import AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.annotation_scene_state import AnnotationSceneState, AnnotationState
from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.image import Image
from sc_sdk.repos import AnnotationSceneRepo, AnnotationSceneStateRepo, DatasetStorageRepo, ImageRepo
from sc_sdk.utils.deletion_helpers import DeletionHelpers

from tests.fixtures.values import DummyValues, IDOffsets


@pytest.fixture
def fxt_dataset_storage_identifier(fxt_ote_id):
    yield DatasetStorageIdentifier(
        workspace_id=fxt_ote_id(1),
        project_id=fxt_ote_id(2),
        dataset_storage_id=fxt_ote_id(3),
    )


@pytest.fixture
def fxt_dataset_storage(fxt_ote_id):
    dataset_storage = DatasetStorage(
        name="dummy_dataset_storage",
        project_id=fxt_ote_id(IDOffsets.SINGLE_TASK_PROJECT),
        _id=fxt_ote_id(IDOffsets.DATASET_STORAGE),
        creation_date=DummyValues.CREATION_DATE,
        creator_name=DummyValues.CREATOR_NAME,
        use_for_training=True,
    )
    yield dataset_storage


@pytest.fixture
def fxt_testing_dataset_storage(fxt_ote_id):
    yield DatasetStorage(
        name="dummy_testing_dataset_storage",
        project_id=fxt_ote_id(IDOffsets.SINGLE_TASK_PROJECT),
        use_for_training=False,
        _id=fxt_ote_id(IDOffsets.DATASET_STORAGE),
        creation_date=DummyValues.CREATION_DATE,
        creator_name=DummyValues.CREATOR_NAME,
    )


@pytest.fixture
def fxt_dataset_storage_persisted(
    request: FixtureRequest,
    fxt_dataset_storage,
):
    dataset_storage: DatasetStorage = fxt_dataset_storage
    dataset_storage.workspace_id = CTX_SESSION_VAR.get().workspace_id
    project_identifier = ProjectIdentifier(
        workspace_id=dataset_storage.workspace_id,
        project_id=dataset_storage.project_id,
    )
    dataset_storage_repo = DatasetStorageRepo(project_identifier)
    dataset_storage_repo.save(dataset_storage)
    request.addfinalizer(lambda: DeletionHelpers.delete_dataset_storage_by_id(dataset_storage.identifier))
    yield dataset_storage


@pytest.fixture
def fxt_filled_dataset_storage(request, fxt_mongo_id):
    """
    Creates a dataset storage with images and annotations with increasing widths
    and heights. Also creates annotation scene states with an equal distribution for
    each AnnotationState enum type.
    """
    project_identifier = ProjectIdentifier(workspace_id=fxt_mongo_id(0), project_id=fxt_mongo_id(1))
    test_dataset_storage = DatasetStorage(
        name="testing_storage",
        project_id=project_identifier.project_id,
        _id=DatasetStorageRepo.generate_id(),
        use_for_training=True,
    )
    ds_repo = DatasetStorageRepo(project_identifier)
    ds_repo.save(test_dataset_storage)
    image_repo = ImageRepo(test_dataset_storage.identifier)
    ann_scene_repo = AnnotationSceneRepo(test_dataset_storage.identifier)
    ann_scene_state_repo = AnnotationSceneStateRepo(test_dataset_storage.identifier)
    annotation_state_list = list(AnnotationState)
    for i in range(1, request.param + 1):
        image = Image(
            name=f"image {i}",
            uploader_id="",
            id=ImageRepo.generate_id(),
            width=i,
            height=i,
            size=100,
        )
        image_repo.save(image)
        image_identifier = ImageIdentifier(image_id=image.id_)
        if i % 2 == 0:
            annotation_scene = AnnotationScene(
                kind=AnnotationSceneKind.ANNOTATION,
                media_identifier=image_identifier,
                media_height=i,
                media_width=i,
                id_=AnnotationSceneRepo.generate_id(),
            )
        else:
            annotation_scene = AnnotationScene(
                kind=AnnotationSceneKind.PREDICTION,
                media_identifier=image_identifier,
                media_height=i,
                media_width=i,
                id_=AnnotationSceneRepo.generate_id(),
            )
        ann_scene_repo.save(annotation_scene)
        annotation_state_per_task = {fxt_mongo_id(): annotation_state_list[i % len(annotation_state_list)]}
        annotation_scene_state = AnnotationSceneState(
            media_identifier=image_identifier,
            annotation_scene_id=annotation_scene.id_,
            annotation_state_per_task=annotation_state_per_task,
            unannotated_rois={},
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        ann_scene_state_repo.save(annotation_scene_state)
    yield test_dataset_storage

    ds_repo.delete_by_id(test_dataset_storage.id_)

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from sc_sdk.entities.suspended_scenes import (
    NullSuspendedAnnotationScenesDescriptor,
    SuspendedAnnotationScenesDescriptor,
)
from sc_sdk.repos import SuspendedAnnotationScenesRepo

from geti_types import CTX_SESSION_VAR, DatasetStorageIdentifier


@pytest.fixture
def fxt_suspended_annotation_scenes_descriptor_1(fxt_mongo_id):
    yield SuspendedAnnotationScenesDescriptor(
        id_=fxt_mongo_id(101),
        project_id=fxt_mongo_id(1),
        dataset_storage_id=fxt_mongo_id(2),
        scenes_ids=(fxt_mongo_id(3), fxt_mongo_id(4)),
    )


@pytest.fixture
def fxt_suspended_annotation_scenes_descriptor_2(fxt_mongo_id):
    yield SuspendedAnnotationScenesDescriptor(
        id_=fxt_mongo_id(102),
        project_id=fxt_mongo_id(1),
        dataset_storage_id=fxt_mongo_id(2),
        scenes_ids=(fxt_mongo_id(5), fxt_mongo_id(6)),
    )


class TestSuspendedAnnotationScenesRepo:
    def test_suspended_annotation_scenes_repo(
        self,
        request,
        fxt_ote_id,
        fxt_suspended_annotation_scenes_descriptor_1,
        fxt_suspended_annotation_scenes_descriptor_2,
    ) -> None:
        """
        <b>Description:</b>
        Check that the SuspendedAnnotationScenesRepo works as expected

        <b>Input data:</b>
        Two SuspendedAnnotationScenesDescriptor

        <b>Expected results:</b>
        The test succeeds if SuspendedAnnotationScenesRepo methods returns the
        correct objects.

        <b>Steps</b>
        1. Save a couple of test descriptors to SuspendedAnnotationScenesRepo
        2. Check that get_by_id returns the correct descriptor, if present
        3. Check that get_by_id returns a null descriptor if the id is unknown
        """
        desc_1 = fxt_suspended_annotation_scenes_descriptor_1
        desc_2 = fxt_suspended_annotation_scenes_descriptor_2
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=CTX_SESSION_VAR.get().workspace_id,
            project_id=desc_1.project_id,
            dataset_storage_id=desc_1.dataset_storage_id,
        )
        repo = SuspendedAnnotationScenesRepo(dataset_storage_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        repo.save(fxt_suspended_annotation_scenes_descriptor_1)
        repo.save(fxt_suspended_annotation_scenes_descriptor_2)

        desc_1_reloaded = repo.get_by_id(desc_1.id_)
        desc_2_reloaded = repo.get_by_id(desc_2.id_)
        assert desc_1_reloaded == desc_1
        assert desc_2_reloaded == desc_2

        desc_nonexisting = repo.get_by_id(fxt_ote_id(345))
        assert isinstance(desc_nonexisting, NullSuspendedAnnotationScenesDescriptor)

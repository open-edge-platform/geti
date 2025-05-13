# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from operator import itemgetter

import pytest
from freezegun import freeze_time

from repos.vps_dataset_filter_repo import VPSDatasetFilterRepo

from geti_types import ID, DatasetStorageIdentifier, ImageIdentifier, MediaIdentifierEntity
from iai_core.entities.annotation_scene_state import AnnotationState
from iai_core.entities.dataset_storage_filter_data import (
    AnnotationSceneFilterData,
    DatasetStorageFilterData,
    MediaFilterData,
)
from iai_core.entities.media import ImageExtensions, MediaPreprocessingStatus, VideoExtensions
from iai_core.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo
from iai_core.utils.time_utils import now


@pytest.fixture
def fxt_dataset_storage_identifier(fxt_project_identifier, fxt_ote_id):
    yield DatasetStorageIdentifier(
        workspace_id=fxt_project_identifier.workspace_id,
        project_id=fxt_project_identifier.project_id,
        dataset_storage_id=fxt_ote_id(123456),
    )


@freeze_time("2024-01-01 00:00:01")
@pytest.fixture
def fxt_dataset_filter_data_factory():
    def factory(media_identifier: MediaIdentifierEntity, annotation_scene_id, label_ids):
        return DatasetStorageFilterData(
            media_identifier=media_identifier,
            media_filter_data=MediaFilterData(
                media_name=f"media_name_{media_identifier.media_id}",
                media_extension=ImageExtensions.JPG
                if isinstance(media_identifier, ImageIdentifier)
                else VideoExtensions.MP4,
                media_width=100,
                media_height=100,
                upload_date=now(),
                size=16,
                uploader_id="user_id",
            ),
            annotation_scene_filter_data=AnnotationSceneFilterData(
                annotation_scene_id=annotation_scene_id,
                user_name="user_name",
                shapes=[],
                label_ids=label_ids,
                creation_date=now(),
            ),
            media_annotation_state=AnnotationState.ANNOTATED,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )

    yield factory


@pytest.fixture
def fxt_construct_filter_data(fxt_dataset_filter_data_factory, fxt_project_identifier):
    def construct(dataset_filter_data_dicts):
        for data in dataset_filter_data_dicts:
            filter_data = fxt_dataset_filter_data_factory(
                media_identifier=ImageIdentifier(image_id=ID(data["media_identifier"])),
                annotation_scene_id=data["annotation_scene_id"],
                label_ids=[ID(lab) for lab in data["label_ids"]],
            )
            ds_identifier = DatasetStorageIdentifier(
                workspace_id=fxt_project_identifier.workspace_id,
                project_id=fxt_project_identifier.project_id,
                dataset_storage_id=data["dataset_storage_id"],
            )
            yield ds_identifier, filter_data

    yield construct


class TestVPSDatesetFilterRepo:
    def test_get_by_id(
        self,
        request,
        fxt_session_ctx,
        fxt_ote_id,
        fxt_dataset_storage_identifier,
        fxt_project_identifier,
        fxt_dataset_filter_data_factory,
    ) -> None:
        # Arrange
        dummy_media_identifier = ImageIdentifier(image_id=fxt_ote_id(123))
        dummy_annotation_id = fxt_ote_id(345)
        label_ids = [fxt_ote_id(456), fxt_ote_id(567)]
        dataset_filter_data = fxt_dataset_filter_data_factory(dummy_media_identifier, dummy_annotation_id, label_ids)
        dataset_filter_data_repo = DatasetStorageFilterRepo(fxt_dataset_storage_identifier)
        dataset_filter_data_repo.save(dataset_filter_data)
        request.addfinalizer(lambda: dataset_filter_data_repo.delete_by_id(dataset_filter_data.id_))

        # Act
        fetched_filter_data = VPSDatasetFilterRepo(fxt_project_identifier).get_by_id(dataset_filter_data.id_)

        # Assert
        assert fetched_filter_data == dataset_filter_data
        assert fetched_filter_data.media_filter_data == dataset_filter_data.media_filter_data
        assert fetched_filter_data.annotation_scene_filter_data == dataset_filter_data.annotation_scene_filter_data

    @pytest.mark.parametrize(
        "dataset_filter_data",
        [
            (
                {
                    "media_identifier": "1",
                    "dataset_storage_id": "ds_1",
                    "annotation_scene_id": "a1",
                    "label_ids": ["a", "b"],
                },
                {
                    "media_identifier": "2",
                    "dataset_storage_id": "ds_2",
                    "annotation_scene_id": "a2",
                    "label_ids": ["b", "c"],
                },
            ),
        ],
    )
    def test_get_all(
        self,
        dataset_filter_data,
        request,
        fxt_project_identifier,
        fxt_construct_filter_data,
    ) -> None:
        # Arrange
        for ds_identifier, filter_data in fxt_construct_filter_data(dataset_filter_data):
            dsf_repo = DatasetStorageFilterRepo(ds_identifier)
            dsf_repo.save(filter_data)
            request.addfinalizer(lambda _dsf_repo=dsf_repo: _dsf_repo.delete_all())

        # Act
        filter_data = list(VPSDatasetFilterRepo(fxt_project_identifier).get_all())

        # Assert
        assert len(filter_data) == 2
        assert filter_data[0].annotation_scene_filter_data.label_ids == [
            ID("b"),
            ID("c"),
        ]
        assert filter_data[1].annotation_scene_filter_data.label_ids == [
            ID("a"),
            ID("b"),
        ]

    @pytest.mark.parametrize(
        "dataset_filter_data, expected_samples, target_dataset_storage",
        [
            [
                (),  # dataset filter data docs
                [],  # expected samples
                None,  # target dataset storage
            ],
            [
                (  # dataset filter data docs
                    {
                        "media_identifier": "1",
                        "dataset_storage_id": "ds_1",
                        "annotation_scene_id": "a1",
                        "label_ids": ["a", "b"],
                    },
                    {
                        "media_identifier": "2",
                        "dataset_storage_id": "ds_1",
                        "annotation_scene_id": "a2",
                        "label_ids": ["b", "c"],
                    },
                    {
                        "media_identifier": "3",
                        "dataset_storage_id": "ds_1",
                        "annotation_scene_id": "a3",
                        "label_ids": ["a", "c"],
                    },
                ),
                [  # expected samples (same number of labels -> select by higher ann id)
                    {
                        "dataset_storage_id": "ds_1",
                        "annotation_scene_id": "a2",
                        "label_ids": ["b", "c"],
                    },
                    {
                        "dataset_storage_id": "ds_1",
                        "annotation_scene_id": "a3",
                        "label_ids": ["a", "c"],
                    },
                ],
                None,  # target dataset storage
            ],
            [
                (  # dataset filter data docs
                    {
                        "media_identifier": "1",
                        "dataset_storage_id": "ds_1",
                        "annotation_scene_id": "a1",
                        "label_ids": ["a", "b", "c"],
                    },
                    {
                        "media_identifier": "2",
                        "dataset_storage_id": "ds_1",
                        "annotation_scene_id": "a2",
                        "label_ids": ["a", "c"],
                    },
                    {
                        "media_identifier": "3",
                        "dataset_storage_id": "ds_2",
                        "annotation_scene_id": "a3",
                        "label_ids": ["a"],
                    },
                    {
                        "media_identifier": "4",
                        "dataset_storage_id": "ds_2",
                        "annotation_scene_id": "a2",
                        "label_ids": ["b"],
                    },
                ),
                [  # expected samples (select by higher number of labels)
                    {
                        "dataset_storage_id": "ds_1",
                        "annotation_scene_id": "a1",
                        "label_ids": ["a", "b", "c"],
                    },
                ],
                None,  # target dataset storage
            ],
            [
                (  # dataset filter data docs
                    {
                        "media_identifier": "1",
                        "dataset_storage_id": "ds_1",
                        "annotation_scene_id": "a1",
                        "label_ids": ["a", "b"],
                    },
                    {
                        "media_identifier": "2",
                        "dataset_storage_id": "ds_2",
                        "annotation_scene_id": "a2",
                        "label_ids": ["a", "b", "c"],
                    },
                ),
                [  # expected samples (only sample from target dataset ds_1)
                    {
                        "dataset_storage_id": "ds_1",
                        "annotation_scene_id": "a1",
                        "label_ids": ["a", "b"],
                    },
                ],
                "ds_1",  # target dataset storage
            ],
        ],
        ids=[
            "no annotations",
            "all media have the same number of labels",
            "media have different number of labels",
            "only select media from specific dataset storage",
        ],
    )
    def test_sample_annotations_by_label_ids(
        self,
        dataset_filter_data,
        expected_samples,
        target_dataset_storage,
        request,
        fxt_project_identifier,
        fxt_construct_filter_data,
    ) -> None:
        # Arrange
        target_label_ids = [ID("a"), ID("b"), ID("c")]
        for ds_identifier, filter_data in fxt_construct_filter_data(dataset_filter_data):
            dsf_repo = DatasetStorageFilterRepo(ds_identifier)
            dsf_repo.save(filter_data)
            request.addfinalizer(lambda _dsf_repo=dsf_repo: _dsf_repo.delete_all())

        # Act
        repo = VPSDatasetFilterRepo(fxt_project_identifier)
        sampling_results = list(
            repo.sample_annotations_by_label_ids(label_ids=target_label_ids, dataset_storage_id=target_dataset_storage)
        )

        # Assert
        assert len(sampling_results) == len(expected_samples)
        sampling_results.sort(key=lambda x: x.annotation_scene_id)
        expected_samples.sort(key=itemgetter("annotation_scene_id"))
        for sample, expected_sample in zip(sampling_results, expected_samples):
            assert sample.dataset_storage_identifier.dataset_storage_id == ID(expected_sample["dataset_storage_id"])
            assert sample.annotation_scene_id == ID(expected_sample["annotation_scene_id"])
            assert set(sample.label_ids) == {ID(lab) for lab in expected_sample["label_ids"]}

    def test_write_operation_error(
        self,
        fxt_session_ctx,
        fxt_project_identifier,
        fxt_dataset_filter_data_factory,
        fxt_ote_id,
    ) -> None:
        # Arrange
        repo = VPSDatasetFilterRepo(fxt_project_identifier)
        filter_data = fxt_dataset_filter_data_factory(
            media_identifier=ImageIdentifier(image_id=fxt_ote_id(11)),
            annotation_scene_id=fxt_ote_id(22),
            label_ids=[fxt_ote_id(33)],
        )

        # Act & Assert
        with pytest.raises(NotImplementedError):
            repo.save(filter_data)

        with pytest.raises(NotImplementedError):
            repo.save_many([filter_data])

        with pytest.raises(NotImplementedError):
            repo.delete_by_id(filter_data.id_)

        with pytest.raises(NotImplementedError):
            repo.delete_all()

        with pytest.raises(NotImplementedError):
            repo.delete_all_by_media_id(filter_data.media_identifier.media_id)

        with pytest.raises(NotImplementedError):
            repo.update_annotation_scenes_to_revisit([fxt_ote_id(22)])

        with pytest.raises(NotImplementedError):
            repo.upsert_dataset_storage_filter_data(filter_data)

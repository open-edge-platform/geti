# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import TYPE_CHECKING

import pytest

from geti_types import ImageIdentifier, MediaType, ProjectIdentifier, VideoFrameIdentifier
from iai_core.entities.annotation import AnnotationScene, AnnotationSceneKind
from iai_core.entities.annotation_scene_state import AnnotationSceneState, AnnotationState
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.datasets import Dataset, DatasetPurpose
from iai_core.entities.image import Image
from iai_core.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from iai_core.entities.subset import Subset
from iai_core.entities.video import VideoFrame
from iai_core.repos import (
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    DatasetRepo,
    DatasetStorageRepo,
    ImageRepo,
    VideoRepo,
)
from iai_core.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo
from iai_core.services.dataset_storage_filter_service import DatasetStorageFilterService
from iai_core.utils.time_utils import now

if TYPE_CHECKING:
    from geti_types import ID
    from iai_core.entities.dataset_storage import DatasetStorage


@pytest.fixture
def fxt_filled_image_dataset_storage(request, fxt_workspace_id, fxt_dataset_storage, fxt_mongo_id):
    """
    Creates a dataset storage with images and annotations with increasing widths
    and heights. Also creates annotation scene states with an equal distribution for
    each AnnotationState enum type.
    """
    dataset_storage: DatasetStorage = fxt_dataset_storage
    workspace_id: ID = dataset_storage.workspace_id
    project_id: ID = dataset_storage.project_id
    project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=project_id)
    ds_repo = DatasetStorageRepo(project_identifier)
    image_repo = ImageRepo(dataset_storage.identifier)
    ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
    ann_scene_state_repo = AnnotationSceneStateRepo(dataset_storage.identifier)
    dataset_repo = DatasetRepo(dataset_storage.identifier)
    dataset_storage_filter_repo = DatasetStorageFilterRepo(dataset_storage.identifier)
    upload_time = now()

    dataset_storage_filter_repo.delete_all()
    image_repo.delete_all()
    request.addfinalizer(lambda: image_repo.delete_all())
    request.addfinalizer(lambda: ann_scene_repo.delete_all())
    request.addfinalizer(lambda: ann_scene_state_repo.delete_all())
    request.addfinalizer(lambda: dataset_repo.delete_all())
    request.addfinalizer(lambda: dataset_storage_filter_repo.delete_all())

    ds_repo.save(dataset_storage)
    request.addfinalizer(lambda: ds_repo.delete_by_id(dataset_storage.id_))

    dataset = Dataset(
        id=DatasetRepo.generate_id(),
        purpose=DatasetPurpose.TRAINING,
        label_schema_id=fxt_mongo_id(1),
    )
    annotation_state_list = list(AnnotationState)
    annotation_kinds = [AnnotationSceneKind.ANNOTATION, AnnotationSceneKind.PREDICTION]
    for i in range(1, request.param + 1):
        image = Image(
            name=f"image {i}",
            uploader_id="",
            id=ImageRepo.generate_id(),
            creation_date=upload_time,
            width=i,
            height=i,
            size=100,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
        image_repo.save(image)
        DatasetStorageFilterService.on_new_media_upload(
            workspace_id=dataset_storage.workspace_id,
            dataset_storage_id=dataset_storage.id_,
            project_id=dataset_storage.project_id,
            media_id=image.id_,
            media_type=MediaType.IMAGE,
        )

        image_identifier = ImageIdentifier(image_id=image.id_)
        annotation_scene = AnnotationScene(
            kind=annotation_kinds[i % 2],
            media_identifier=image_identifier,
            media_height=i,
            media_width=i,
            id_=AnnotationSceneRepo.generate_id(),
        )
        ann_scene_repo.save(annotation_scene)
        DatasetStorageFilterService.on_new_annotation_scene(
            project_id=dataset_storage.project_id,
            dataset_storage_id=dataset_storage.id_,
            annotation_scene_id=annotation_scene.id_,
        )

        annotation_state_per_task = {fxt_mongo_id(): annotation_state_list[i % len(annotation_state_list)]}
        annotation_scene_state = AnnotationSceneState(
            media_identifier=image_identifier,
            annotation_scene_id=annotation_scene.id_,
            annotation_state_per_task=annotation_state_per_task,
            unannotated_rois={},
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        ann_scene_state_repo.save(annotation_scene_state)

        dataset.append(
            DatasetItem(
                id_=DatasetRepo.generate_id(),
                media=image,
                annotation_scene=annotation_scene,
                subset=Subset.TRAINING,
            )
        )
    dataset_repo.save_shallow(dataset)

    yield dataset_storage


@pytest.fixture
def fxt_filled_video_dataset_storage(
    request,
    fxt_project,
    fxt_mongo_id,
    fxt_unannotated_video_factory,
):
    """
    Creates a dataset storage with videos which each have 4 frames, 2 of which have a
    prediction and the other 2 have an annotation. Also creates annotation scene states
    with an equal distribution for each AnnotationState enum type.
    """
    dataset_storage = fxt_project.get_training_dataset_storage()
    workspace_id: ID = dataset_storage.workspace_id
    project_id: ID = dataset_storage.project_id
    project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=project_id)
    ds_repo = DatasetStorageRepo(project_identifier)
    video_repo = VideoRepo(dataset_storage.identifier)
    ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
    ann_scene_state_repo = AnnotationSceneStateRepo(dataset_storage.identifier)
    dataset_repo = DatasetRepo(dataset_storage.identifier)
    dataset_storage_filter_repo = DatasetStorageFilterRepo(dataset_storage.identifier)

    dataset_storage_filter_repo.delete_all()
    request.addfinalizer(lambda: video_repo.delete_all())
    request.addfinalizer(lambda: ann_scene_repo.delete_all())
    request.addfinalizer(lambda: ann_scene_state_repo.delete_all())
    request.addfinalizer(lambda: dataset_repo.delete_all())
    request.addfinalizer(lambda: dataset_storage_filter_repo.delete_all())

    ds_repo.save(dataset_storage)
    request.addfinalizer(lambda: ds_repo.delete_by_id(dataset_storage.id_))

    dataset = Dataset(
        id=DatasetRepo.generate_id(),
        purpose=DatasetPurpose.TRAINING,
        label_schema_id=fxt_mongo_id(1),
    )

    annotation_state_list = list(AnnotationState)
    annotation_kinds = [AnnotationSceneKind.ANNOTATION, AnnotationSceneKind.PREDICTION]
    subsets = [Subset.TRAINING, Subset.TESTING, Subset.VALIDATION]

    for i in range(1, request.param + 1):
        video = fxt_unannotated_video_factory(project=fxt_project, width=50, height=50, number_of_frames=4)
        DatasetStorageFilterService.on_new_media_upload(
            workspace_id=dataset_storage.workspace_id,
            dataset_storage_id=dataset_storage.id_,
            project_id=dataset_storage.project_id,
            media_id=video.id_,
            media_type=MediaType.VIDEO,
        )

        for j in range(4):
            video_frame_identifier = VideoFrameIdentifier(video_id=video.id_, frame_index=j + 1)
            annotation_scene = AnnotationScene(
                kind=annotation_kinds[j % 2],
                media_identifier=video_frame_identifier,
                media_height=video.height,
                media_width=video.width,
                id_=AnnotationSceneRepo.generate_id(),
            )
            ann_scene_repo.save(annotation_scene)
            if annotation_scene.kind == AnnotationSceneKind.ANNOTATION:
                DatasetStorageFilterService.on_new_annotation_scene(
                    project_id=dataset_storage.project_id,
                    dataset_storage_id=dataset_storage.id_,
                    annotation_scene_id=annotation_scene.id_,
                )

            annotation_state_per_task = {fxt_mongo_id(): annotation_state_list[j % len(annotation_state_list)]}
            annotation_scene_state = AnnotationSceneState(
                media_identifier=video_frame_identifier,
                annotation_scene_id=annotation_scene.id_,
                annotation_state_per_task=annotation_state_per_task,
                unannotated_rois={},
                id_=AnnotationSceneStateRepo.generate_id(),
            )
            ann_scene_state_repo.save(annotation_scene_state)

            dataset.append(
                DatasetItem(
                    id_=DatasetRepo.generate_id(),
                    media=VideoFrame(video=video, frame_index=j + 1),
                    annotation_scene=annotation_scene,
                    subset=subsets[i % 3],
                )
            )
    dataset_repo.save_shallow(dataset)

    yield dataset_storage

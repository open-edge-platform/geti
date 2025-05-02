# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from copy import deepcopy
from random import random

import pytest

from geti_types import ID, DatasetStorageIdentifier, ImageIdentifier, MediaType, VideoFrameIdentifier
from iai_core_py.entities.media_score import MediaScore
from iai_core_py.entities.metrics import ScoreMetric
from iai_core_py.repos import ImageRepo, MediaScoreRepo, ProjectRepo, VideoRepo


@pytest.fixture
def fxt_label_ids(fxt_ote_id):
    return [fxt_ote_id(i) for i in range(15, 20)]


@pytest.fixture
def fxt_model_test_result_ids(fxt_ote_id):
    return [fxt_ote_id(i) for i in range(10, 12)]


@pytest.fixture
def fxt_media_identifiers(fxt_ote_id):
    """
    Create
      - 20 image identifiers
    and
      - 16 video frame identifiers, 4 videos with 4 frames each
    """
    media_identifiers = []
    for i in range(20, 40):
        media_identifiers.append(ImageIdentifier(image_id=fxt_ote_id(i)))
    for i in range(40, 44):
        for j in range(44, 48):
            media_identifiers.append(VideoFrameIdentifier(video_id=fxt_ote_id(i), frame_index=j))
    return media_identifiers


@pytest.fixture
def fxt_project_with_media_scores(
    fxt_ote_id,
    fxt_project,
    fxt_media_identifiers,
    fxt_model_test_result_ids,
    fxt_label_ids,
    fxt_image_entity,
    fxt_video_entity,
):
    """
    Project with various media scores
    """
    dataset_storage_identifier = DatasetStorageIdentifier(
        workspace_id=fxt_project.workspace_id,
        project_id=fxt_project.id_,
        dataset_storage_id=fxt_project.training_dataset_storage_id,
    )
    MediaScoreRepo(dataset_storage_identifier).delete_all()
    image_repo = ImageRepo(dataset_storage_identifier)
    video_repo = VideoRepo(dataset_storage_identifier)
    for i, model_test_result_id in enumerate(fxt_model_test_result_ids):
        for j, media_identifier in enumerate(fxt_media_identifiers):
            scores = {
                ScoreMetric(
                    name="F-Measure",
                    value=(j + 1) / len(fxt_media_identifiers),
                    label_id=None,
                )
            }
            for label_id in fxt_label_ids:
                scores.add(ScoreMetric(name="F-Measure", value=random(), label_id=label_id))
            media_score = MediaScore(
                id_=fxt_ote_id((50 + j) * (i + 1)),
                model_test_result_id=model_test_result_id,
                media_identifier=media_identifier,
                scores=scores,
                annotated_label_ids=set(fxt_label_ids),
            )
            MediaScoreRepo(dataset_storage_identifier).save(media_score)
            if media_identifier.media_type is MediaType.IMAGE:
                image_entity = deepcopy(fxt_image_entity)
                image_entity.id_ = media_identifier.media_id
                image_repo.save(image_entity)
            else:
                video_entity = deepcopy(fxt_video_entity)
                video_entity.id_ = media_identifier.media_id
                video_repo.save(video_entity)

    yield fxt_project
    ProjectRepo().delete_by_id(fxt_project.id_)
    MediaScoreRepo(dataset_storage_identifier).delete_all()
    image_repo.delete_all()
    video_repo.delete_all()


@pytest.fixture
def fxt_media_score_filter_factory():
    def _media_score_filter_factory(label_id: ID | None, score_threshold: float, score_operator: str):
        return {
            "condition": "and",
            "rules": [
                {
                    "field": "label_id",
                    "operator": "equal",
                    "value": label_id,
                },
                {
                    "field": "score",
                    "operator": score_operator,
                    "value": score_threshold,
                },
            ],
        }

    return _media_score_filter_factory

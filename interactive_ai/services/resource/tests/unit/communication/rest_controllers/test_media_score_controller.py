# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest

from communication.rest_controllers import MediaScoreRESTController
from managers.project_manager import ProjectManager
from tests.unit.mocked_method_helpers import mock_get_image_by_id, mock_get_video_by_id
from usecases.dataset_filter import DatasetFilterSortDirection, MediaScoreFilterField

from geti_types import ID, DatasetStorageIdentifier, ImageIdentifier, ProjectIdentifier, VideoFrameIdentifier
from iai_core_py.entities.video import Video
from iai_core_py.repos import (
    AnnotationSceneRepo,
    DatasetRepo,
    ImageRepo,
    MediaScoreRepo,
    ModelTestResultRepo,
    ProjectRepo,
    VideoRepo,
)
from iai_core_py.repos.base.session_repo import QueryAccessMode
from iai_core_py.repos.mappers import IDToMongo, MediaIdentifierToMongo

LABEL_IDS = [
    ID("5f7b1b3b7f7e4b0001f3b3b1"),
    ID("5f7b1b3b7f7e4b0001f3b3b2"),
    ID("5f7b1b3b7f7e4b0001f3b3b3"),
]


@pytest.fixture
def fxt_media_identifiers(fxt_mongo_id):
    # 10 images + 10 video frames (single video)
    images = [ImageIdentifier(fxt_mongo_id(i)) for i in range(10)]
    video_id = fxt_mongo_id(11)
    video_frames = [VideoFrameIdentifier(video_id=video_id, frame_index=i) for i in range(12, 22)]
    yield images + video_frames


@pytest.fixture
def fxt_label_ids_per_media_identifier(fxt_media_identifiers):
    a, b, c = LABEL_IDS
    label_ids = [
        [a],
        [a],
        [a],
        [b, c],
        [a],
        [b],
        [a, c],
        [a, b],
        [b],
        [b],
        [b],
        [c],
        [c],
        [c],
        [a],
        [b],
        [c],
        [a, b],
        [a, b, c],
        [a, b, c],
    ]
    yield dict(zip(fxt_media_identifiers, label_ids))


@pytest.fixture
def fxt_dataset_identifier(fxt_mongo_id, fxt_empty_project_persisted):
    yield DatasetStorageIdentifier(
        workspace_id=fxt_empty_project_persisted.workspace_id,
        project_id=fxt_empty_project_persisted.id_,
        dataset_storage_id=ID(fxt_mongo_id(3)),
    )


@pytest.fixture
def fxt_dataset_id(fxt_mongo_id):
    yield fxt_mongo_id(2000)


@pytest.fixture
def fxt_populate_annotation_scenes(fxt_mongo_id, fxt_dataset_identifier, fxt_label_ids_per_media_identifier):
    repo = AnnotationSceneRepo(fxt_dataset_identifier)
    offset = 1000
    annotation_ids = []
    for i, (media_identifier, label_ids) in enumerate(fxt_label_ids_per_media_identifier.items()):
        annotation_id = fxt_mongo_id(offset + i)
        doc = repo.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        doc.update(
            {
                "media_identifier": MediaIdentifierToMongo.forward(media_identifier),
                "label_ids": [IDToMongo.forward(_id) for _id in label_ids],
            }
        )
        repo._collection.update_one(
            {"_id": IDToMongo.forward(annotation_id)},
            {"$set": doc},
            upsert=True,
        )
        annotation_ids.append(annotation_id)
    yield annotation_ids


@pytest.fixture
def fxt_populate_images(fxt_media_identifiers, fxt_dataset_identifier, fxt_image_entity):
    image_repo = ImageRepo(fxt_dataset_identifier)
    ids = []
    for i in range(10):
        fxt_image_entity.id_ = fxt_media_identifiers[i].media_id
        image_repo.save(fxt_image_entity)
        ids.append(fxt_image_entity.id_)
    yield ids


@pytest.fixture
def fxt_populate_video(fxt_media_identifiers, fxt_dataset_identifier, fxt_video_entity):
    video_repo = VideoRepo(fxt_dataset_identifier)
    fxt_video_entity.id_ = fxt_media_identifiers[-1].media_id
    video_repo.save(fxt_video_entity)
    yield fxt_video_entity.id_


@pytest.fixture
def fxt_populate_dataset_items(fxt_dataset_id, fxt_mongo_id, fxt_dataset_identifier, fxt_populate_annotation_scenes):
    repo = DatasetRepo(fxt_dataset_identifier).get_dataset_item_repo(fxt_dataset_id)
    dataset_item_ids = []
    offset = 3000
    for i, annotation_scene_id in enumerate(fxt_populate_annotation_scenes):
        doc = repo.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        doc.update({"annotation_scene_id": IDToMongo.forward(annotation_scene_id)})
        _id = IDToMongo.forward(fxt_mongo_id(offset + i))
        repo._collection.update_one(
            {"_id": _id},
            {"$set": doc},
            upsert=True,
        )
        dataset_item_ids.append(_id)


@pytest.fixture
def fxt_populate_model_test_result(fxt_dataset_identifier, fxt_dataset_id, fxt_model_test_result):
    project_identifier = ProjectIdentifier(
        workspace_id=fxt_dataset_identifier.workspace_id,
        project_id=fxt_dataset_identifier.project_id,
    )
    repo = ModelTestResultRepo(project_identifier)
    fxt_model_test_result.ground_truth_dataset_id = fxt_dataset_id
    repo.save(fxt_model_test_result)
    yield fxt_model_test_result.id_


@pytest.fixture
def fxt_populate_media_scores(
    fxt_mongo_id,
    fxt_dataset_identifier,
    fxt_populate_model_test_result,
    fxt_media_identifiers,
):
    repo = MediaScoreRepo(fxt_dataset_identifier)
    a, b, c = LABEL_IDS

    def _create_score(score_per_label, overall_score):
        _scores = []
        for label, score in score_per_label.items():
            _scores.append(
                {
                    "name": "ACCURACY",
                    "label_id": IDToMongo.forward(label),
                    "value": score,
                    "type": "score",
                }
            )
        for label in LABEL_IDS:
            if label not in score_per_label:
                _scores.append(
                    {
                        "name": "ACCURACY",
                        "label_id": IDToMongo.forward(label),
                        "value": 0.0,
                        "type": "score",
                    }
                )
        _scores.append(
            {
                "name": "ACCURACY",
                "label_id": None,
                "value": overall_score,
                "type": "score",
            }
        )
        return _scores

    media_score_ids = []
    offset = 5000
    for i, media_identifier in enumerate(fxt_media_identifiers):
        scores = _create_score({a: 0.6}, overall_score=0.6)
        doc = repo.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        doc.update(
            {
                "model_test_result_id": IDToMongo.forward(fxt_populate_model_test_result),
                "media_identifier": MediaIdentifierToMongo.forward(media_identifier),
                "scores": scores,
            }
        )
        media_score_id = fxt_mongo_id(offset + i)
        media_score_ids.append(media_score_id)
        repo._collection.update_one(
            {"_id": IDToMongo.forward(media_score_id)},
            {"$set": doc},
            upsert=True,
        )
    yield media_score_ids


class TestMediaScoreRESTController:
    def test_get_filtered_media_scores(
        self,
        fxt_media_score_filter_factory,
        fxt_project_with_media_scores,
        fxt_model_test_result,
        fxt_media_score,
        fxt_model_test_result_ids,
    ):
        """
        Test media score controller by using it to fetch a
        """
        controller = MediaScoreRESTController()
        project_id = fxt_project_with_media_scores.id_
        model_test_result_id = fxt_model_test_result_ids[0]
        sort_by = MediaScoreFilterField.SCORE
        sort_direction = DatasetFilterSortDirection.ASC
        skip = 0
        limit = 100
        query = fxt_media_score_filter_factory(label_id=None, score_operator="greater", score_threshold=0.5)

        with (
            patch.object(
                ProjectManager,
                "get_project_by_id",
                return_value=fxt_project_with_media_scores,
            ),
            patch.object(
                ModelTestResultRepo,
                "get_by_id",
                return_value=fxt_model_test_result,
            ),
            patch.object(
                MediaScoreRepo,
                "get_by_test_and_media_identifier",
                return_value=fxt_media_score,
            ),
            patch.object(ImageRepo, "get_by_id", side_effect=mock_get_image_by_id),
            patch.object(VideoRepo, "get_by_id", side_effect=mock_get_video_by_id),
            patch.object(Video, "stride", create=True, return_value=1),
        ):
            result = controller.get_filtered_items(
                project_id=project_id,
                model_test_result_id=model_test_result_id,
                sort_by=sort_by,
                sort_direction=sort_direction,
                limit=limit,
                skip=skip,
                query=query,
            )

        assert "media" in result
        n_images = 0
        for media in result["media"]:
            if media["type"] == "image":
                n_images += 1
        assert n_images == result["total_matched_images"]

    @pytest.mark.parametrize(
        "label_id, score_operator, score_threshold, expected_count",
        [
            (None, "greater_or_equal", 0.5, 20),
            (None, "less", 0.5, 0),
            (str(LABEL_IDS[0]), "greater_or_equal", 0.5, 10),
            (str(LABEL_IDS[0]), "less", 0.5, 0),
            (str(LABEL_IDS[1]), "greater_or_equal", 0.5, 0),
            (str(LABEL_IDS[1]), "less", 0.5, 10),
            (str(LABEL_IDS[2]), "greater_or_equal", 0.5, 0),
            (str(LABEL_IDS[2]), "less", 0.5, 8),
        ],
        ids=[
            "Overall media scores >= 0.5",
            "Overall media scores < 0.5",
            "Label[0] media scores >= 0.5",
            "Label[0] media scores < 0.5",
            "Label[1] media scores >= 0.5",
            "Label[1] media scores < 0.5",
            "Label[2] media scores >= 0.5",
            "Label[2] media scores < 0.5",
        ],
    )
    def test_media_scores_filtering(
        self,
        request,
        label_id,
        score_operator,
        score_threshold,
        expected_count,
        fxt_dataset_id,
        fxt_empty_project_persisted,
        fxt_dataset_identifier,
        fxt_populate_annotation_scenes,
        fxt_populate_dataset_items,
        fxt_populate_model_test_result,
        fxt_populate_media_scores,
        fxt_populate_images,
        fxt_populate_video,
    ) -> None:
        def clean_up():
            # annotations
            repo = AnnotationSceneRepo(fxt_dataset_identifier)
            for ann_scene_id in fxt_populate_annotation_scenes:
                repo.delete_by_id(ann_scene_id)

            # dataset items
            repo = DatasetRepo(fxt_dataset_identifier).get_dataset_item_repo(fxt_dataset_id)
            repo.delete_all()

            # model test result
            ModelTestResultRepo(fxt_empty_project_persisted.identifier).delete_by_id(fxt_populate_model_test_result)

            # media scores
            MediaScoreRepo(fxt_dataset_identifier).delete_all_by_model_test_result_id(fxt_populate_model_test_result)

            # images and videos
            image_repo = ImageRepo(fxt_dataset_identifier)
            for image_id in fxt_populate_images:
                image_repo.delete_by_id(image_id)

            video_repo = VideoRepo(fxt_dataset_identifier)
            video_repo.delete_by_id(fxt_populate_video)

            # project
            ProjectRepo().delete_by_id(fxt_empty_project_persisted.id_)

        request.addfinalizer(lambda: clean_up())

        query = {
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
            "condition": "and",
        }

        rest = MediaScoreRESTController.get_filtered_items(
            project_id=fxt_empty_project_persisted.id_,
            model_test_result_id=fxt_populate_model_test_result,
            sort_by=MediaScoreFilterField.SCORE,
            sort_direction=DatasetFilterSortDirection.ASC,
            limit=50,
            skip=0,
            query=query,
        )

        assert len(rest["media"]) == expected_count

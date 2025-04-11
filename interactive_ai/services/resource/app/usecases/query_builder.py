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
import logging
import math
from dataclasses import dataclass
from typing import Any

from pymongo.collation import Collation

from usecases.dataset_filter import DatasetFilter

from geti_types import (
    ID,
    DatasetStorageIdentifier,
    MediaIdentifierEntity,
    MediaType,
    ProjectIdentifier,
    VideoFrameIdentifier,
    VideoIdentifier,
)
from sc_sdk.entities.datasets import DatasetIdentifier
from sc_sdk.entities.image import Image
from sc_sdk.entities.media import ImageExtensions, MediaPreprocessing, MediaPreprocessingStatus, VideoExtensions
from sc_sdk.entities.video import Video
from sc_sdk.entities.video_annotation_statistics import VideoAnnotationStatistics
from sc_sdk.repos import AnnotationSceneRepo, DatasetRepo, ImageRepo, MediaScoreRepo, ModelTestResultRepo, VideoRepo
from sc_sdk.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo
from sc_sdk.repos.mappers import DatetimeToMongo
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from sc_sdk.repos.mappers.mongodb_mappers.media_mapper import MediaIdentifierToMongo
from sc_sdk.repos.training_revision_filter_repo import _TrainingRevisionFilterRepo

logger = logging.getLogger(__name__)


class MatchedFramesVideoIdentifier(VideoIdentifier):
    """
    Video identifier that can store the amount of frames in a video matching a dataset filter.
    """

    def __init__(self, video_id: ID, matched_frames: int) -> None:
        self.matched_frames = matched_frames
        super().__init__(video_id=video_id)


@dataclass
class AnnotationSceneDetails:
    annotation_scene_id: ID | None = None
    roi_id: ID | None = None
    last_annotator_id: ID | None = None


@dataclass
class MediaQueryResult:
    """
    Container to store media identifier, media and optionally an annotation scene id
    and roi id.
    """

    media_identifier: MediaIdentifierEntity
    media: Image | Video
    annotation_scene_id: ID | None = None
    roi_id: ID | None = None
    last_annotator_id: str | None = None
    video_annotation_statistics: VideoAnnotationStatistics | None = None


@dataclass(frozen=True)
class QueryResults:
    """
    This class can be used to store resulting media identifiers from a query and the
    counts of each matched media type. Also contains the skip integer for the next page.
    """

    media_query_results: list[MediaQueryResult]
    skip: int
    matching_images_count: int
    matching_videos_count: int
    matching_video_frames_count: int
    total_images_count: int
    total_videos_count: int

    @property
    def media_identifiers(self) -> list[MediaIdentifierEntity]:
        return [media_query.media_identifier for media_query in self.media_query_results]

    def __eq__(self, other: object):
        if isinstance(other, QueryResults):
            return (
                self.media_query_results == other.media_query_results
                and self.skip == other.skip
                and self.matching_images_count == other.matching_images_count
                and self.matching_videos_count == other.matching_videos_count
                and self.matching_video_frames_count == other.matching_video_frames_count
                and self.total_images_count == other.total_images_count
                and self.total_videos_count == other.total_videos_count
            )
        return False


@dataclass
class VideoFrameQueryResult:
    video_frame_indices: list[int]
    query_results: QueryResults


class QueryBuilder:
    @staticmethod
    def get_results_for_media_scores_dataset_filter(
        dataset_filter: DatasetFilter,
        dataset_storage_identifier: DatasetStorageIdentifier,
        model_test_result_id: ID,
    ) -> QueryResults:
        """
        Gets all the media identifiers for items that match the query in the DatasetFilter from a specific
        DatasetStorage and counts the amount of images, videos and video frames in the
        results.

        :param dataset_filter: filter to select media identifiers
        :param dataset_storage_identifier: dataset storage identifier for model test
        :param model_test_result_id: id of the model test result
        :return: a QueryResults object with the media identifiers and counts per matched
        media category.
        """
        QueryBuilder._cache_media_scores_annotated_label_ids(
            dataset_storage_identifier=dataset_storage_identifier,
            model_test_result_id=model_test_result_id,
        )
        repo = MediaScoreRepo(dataset_storage_identifier)
        query: list[dict] = [
            {"$match": {"model_test_result_id": IDToMongo.forward(model_test_result_id)}},
            {"$unwind": "$scores"},
            {
                "$project": {
                    "annotated_label_ids": 1,
                    "label_id": "$scores.label_id",
                    "score": "$scores.value",
                    "media_identifier": 1,
                }
            },
            {
                "$match": {
                    "$or": [
                        {"label_id": None},  # needed for "all labels" selection
                        {"$expr": {"$in": ["$label_id", "$annotated_label_ids"]}},
                    ],
                },
            },
            dataset_filter.generate_match_query(),
            dataset_filter.generate_pagination_query(),
        ]

        doc = repo.aggregate_read(query, collation=Collation(locale="en_US")).next()

        media_docs = list(doc["paginated_results"])

        image_by_id, video_by_id = QueryBuilder._get_additional_media(media_docs, dataset_storage_identifier)

        media_query_results: list[MediaQueryResult] = []
        for media_doc in media_docs:
            media_identifier = MediaIdentifierToMongo.backward(media_doc["media_identifier"])  # type: ignore
            media: Image | Video
            if media_identifier.media_type in [MediaType.VIDEO_FRAME, MediaType.VIDEO]:
                media = video_by_id[media_identifier.media_id]
            else:
                media = image_by_id[media_identifier.media_id]
            media_query_results.append(
                MediaQueryResult(
                    media_identifier=media_identifier,
                    media=media,
                )
            )

        matching_images_count = doc["image_count"][0]["count"] if doc["image_count"] else 0
        matching_videos_count = doc["video_count"][0]["count"] if doc["video_count"] else 0
        matching_video_frames_count = doc["video_frame_count"][0]["count"] if doc["video_frame_count"] else 0

        total_images = ImageRepo(dataset_storage_identifier).count()
        total_videos = VideoRepo(dataset_storage_identifier).count()

        return QueryResults(
            media_query_results=media_query_results,
            skip=dataset_filter.limit + dataset_filter.skip,
            matching_images_count=matching_images_count,
            matching_videos_count=matching_videos_count,
            matching_video_frames_count=matching_video_frames_count,
            total_images_count=total_images,
            total_videos_count=total_videos,
        )

    @staticmethod
    def get_video_frame_results_for_dataset_storage_filter(
        dataset_filter: DatasetFilter,
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
        fps: int,
        include_frame_details: bool,
    ) -> VideoFrameQueryResult:
        """
        Get all video frame items that match the query in the DatasetFilter from a specific
        DatasetStorage

        :param dataset_filter: Filter to select find media items
        :param dataset_storage_identifier: DatasetStorageIdentifier to initialize repo which items need
        to be found in
        :param video_id: ID of a video to find frames for
        :param fps: number of frames per second to return, if 0, return all frames
        :param include_frame_details: bool indicating whether to include frame details
        :return: a list of video frame indexes that match the filter
        """
        query = [dataset_filter.generate_match_query()]
        query.insert(
            0,
            {"$match": {"media_identifier.media_id": IDToMongo.forward(video_id)}},
        )

        repo = DatasetStorageFilterRepo(dataset_storage_identifier=dataset_storage_identifier)
        docs = repo.aggregate_read(query, collation=Collation(locale="en_US"))

        video: Video = VideoRepo(dataset_storage_identifier=dataset_storage_identifier).get_by_id(video_id)
        frame_skip = math.ceil(video.fps / fps) if fps else 1

        dict_of_frames: dict[int, dict] = {}
        for doc in docs:
            if doc["media_identifier"]["type"] == "video":
                annotated_video_frame_indices = repo.get_video_frame_indices(video_id=video_id)
                for frame_index in range(0, video.total_frames, frame_skip):
                    if frame_index not in annotated_video_frame_indices:
                        dict_of_frames[frame_index] = doc
            elif doc["media_identifier"]["type"] == "video_frame":
                frame_index = doc["media_identifier"]["frame_index"]
                if frame_index % frame_skip == 0:
                    dict_of_frames[frame_index] = doc
            else:
                raise ValueError(f"Unexpected media identifier type, expected 'video' or 'video_frame': {doc}")

        video_frame_indices = sorted(dict_of_frames.keys())[
            dataset_filter.skip : dataset_filter.skip + dataset_filter.limit
        ]

        total_images = repo.count(extra_filter={"media_identifier.type": "image"})
        total_videos = repo.count(extra_filter={"media_identifier.type": "video"})

        media_query_results: list[MediaQueryResult] = []
        if include_frame_details:
            for frame_index in video_frame_indices:
                doc = dict_of_frames[frame_index]
                annotation_scene_details = QueryBuilder._get_annotation_scene_details(media_doc=doc)
                media_identifier = VideoFrameIdentifier(video_id=video_id, frame_index=frame_index)
                media_query_results.append(
                    MediaQueryResult(
                        media_identifier=media_identifier,
                        media=video,
                        annotation_scene_id=annotation_scene_details.annotation_scene_id,
                        last_annotator_id=annotation_scene_details.last_annotator_id,
                    )
                )

        return VideoFrameQueryResult(
            video_frame_indices=video_frame_indices,
            query_results=QueryResults(
                media_query_results=media_query_results,
                skip=dataset_filter.limit + dataset_filter.skip,
                matching_images_count=0,
                matching_videos_count=1,
                matching_video_frames_count=len(dict_of_frames),
                total_images_count=total_images,
                total_videos_count=total_videos,
            ),
        )

    @staticmethod
    def get_media_results_for_dataset_storage_filter(
        dataset_filter: DatasetFilter,
        dataset_storage_identifier: DatasetStorageIdentifier,
    ) -> QueryResults:
        """
        Gets all the media items that match the query in the DatasetFilter from a specific
        DatasetStorage and counts the amount of images, videos and video frames in the
        results.

        :param dataset_filter: Filter to select find media items
        :param dataset_storage_identifier: DatasetStorageIdentifier to initialize repo which items need
        to be found in
        :param video_id: ID of a video to find frames for
        :return: a QueryResults object with the media identifiers and counts per matched
        media category.
        """
        repo = DatasetStorageFilterRepo(dataset_storage_identifier=dataset_storage_identifier)

        query = [dataset_filter.generate_match_query()]
        group_stage = {
            "$group": {
                "_id": "$media_identifier.media_id",
                "media_identifier": {"$first": "$media_identifier"},
                "media_name": {"$first": "$media_name"},
                "media_extension": {"$first": "$media_extension"},
                "upload_date": {"$first": "$upload_date"},
                "uploader_id": {"$first": "$uploader_id"},
                "media_height": {"$first": "$media_height"},
                "media_width": {"$first": "$media_width"},
                "annotation_scene_id": {"$first": "$annotation_scene_id"},
                "user_name": {"$first": "$user_name"},
                "media_annotation_state": {"$first": "$media_annotation_state"},
                "matched_frames": {
                    "$sum": {
                        "$ifNull": ["$unannotated_frames", 1],
                    },
                },
                "size": {"$first": "$size"},
                "frame_rate": {"$first": "$frame_rate"},
                "frame_stride": {"$first": "$frame_stride"},
                "frame_count": {"$first": "$frame_count"},
                "preprocessing": {"$first": "$preprocessing"},
            },
        }
        query.append(dataset_filter.generate_pagination_query(group_stage=group_stage))

        doc = repo.aggregate_read(query, collation=Collation(locale="en_US")).next()
        total_images = repo.count(extra_filter={"media_identifier.type": "image"})
        total_videos = repo.count(extra_filter={"media_identifier.type": "video"})

        return QueryBuilder.create_query_results(
            doc=doc,
            dataset_filter=dataset_filter,
            ds_identifier=dataset_storage_identifier,
            total_images=total_images,
            total_videos=total_videos,
            should_group_video_frames=True,
        )

    @staticmethod
    def get_results_for_training_revision_filter(
        dataset_filter: DatasetFilter,
        dataset_identifier: DatasetIdentifier,
        video_id: ID | None = None,
    ) -> QueryResults:
        """
        Gets all the media items that match the query in the DatasetFilter from a specific
        DatasetStorage and counts the amount of images, videos and video frames in the
        results.

        :param dataset_filter: Filter to select find media items
        :param dataset_identifier: DatasetIdentifier to initialize repo which items need
        to be found in
        :param video_id: ID of a video to find frames for
        :return: a QueryResults object with the media identifiers and counts per matched
        media category.
        """
        repo = _TrainingRevisionFilterRepo(dataset_identifier)

        query = [dataset_filter.generate_match_query()]
        group_stage = None
        if video_id is not None:
            # Only filter video frames within the video with video_id as id.
            query.insert(
                0,
                {"$match": {"media_identifier.media_id": {"$eq": IDToMongo.forward(video_id)}}},  # type: ignore
            )
            # All media in a training revision are ANNOTATED and its preprocessing is therefore FINISHED,
            # but we need to add this info to the docs to ensure annotation_scene_id, roi_id, last_annotator_id and
            # preprocessing are handled.
            query.append({"$addFields": {"media_annotation_state": "ANNOTATED", "preprocessing": "FINISHED"}})
        else:
            # Results of all media are filtered, but video frames are grouped by video_id.
            # For media related fields, all video frames have the same info, except media_identifier.frame_index,
            # but this is ignored, so we can take the first match.
            # For videos, count the number of matched frames as "matched_frames" (for images this field is irrelevant)
            # For videos the annotation_scene_id and roi are irrelevant, thus we can take the first match.
            group_stage = {
                "$group": {
                    "_id": "$media_identifier.media_id",
                    "media_identifier": {"$first": "$media_identifier"},
                    "media_name": {"$first": "$media_name"},
                    "media_extension": {"$first": "$media_extension"},
                    "upload_date": {"$first": "$upload_date"},
                    "uploader_id": {"$first": "$uploader_id"},
                    "media_height": {"$first": "$media_height"},
                    "media_width": {"$first": "$media_width"},
                    "annotation_scene_id": {"$first": "$annotation_scene_id"},
                    "roi": {"$first": "$roi"},
                    "user_name": {"$first": "$user_name"},
                    "matched_frames": {"$count": {}},
                    "media_annotation_state": {"$first": "ANNOTATED"},
                    "size": {"$first": "$size"},
                    "frame_rate": {"$first": "$frame_rate"},
                    "frame_stride": {"$first": "$frame_stride"},
                    "frame_count": {"$first": "$frame_count"},
                    "preprocessing": {"$first": "FINISHED"},
                },
            }
        query.append(dataset_filter.generate_pagination_query(group_stage=group_stage))

        doc = repo.aggregate_read(query, collation=Collation(locale="en_US")).next()
        total_images = repo.count(extra_filter={"media_identifier.type": "image"})

        # Video entities are never in the training revision filter repo, so we filter on video frames and group them.
        pipeline: list[dict[str, Any]] = [
            {"$match": {"media_identifier.type": "video_frame"}},
            {
                "$group": {
                    "_id": "$media_identifier.media_id",
                }
            },
            {"$count": "total_videos"},
        ]
        try:
            total_videos_doc = repo.aggregate_read(pipeline=pipeline).next()
            total_videos = total_videos_doc["total_videos"]
        except StopIteration:
            total_videos = 0

        return QueryBuilder.create_query_results(
            doc=doc,
            dataset_filter=dataset_filter,
            ds_identifier=dataset_identifier.ds_identifier,
            total_images=total_images,
            total_videos=total_videos,
            should_group_video_frames=video_id is None,
        )

    @staticmethod
    def __image_from_media_doc(media_doc: dict) -> Image:
        media_extension = media_doc.get("media_extension")
        extension = ImageExtensions[media_extension] if media_extension is not None else ImageExtensions.PNG

        return Image(
            name=media_doc["media_name"],
            id=IDToMongo.backward(media_doc["media_identifier"]["media_id"]),
            uploader_id=media_doc["uploader_id"],
            width=media_doc["media_width"],
            height=media_doc["media_height"],
            size=media_doc["size"],
            creation_date=DatetimeToMongo.backward(media_doc["upload_date"]),
            extension=extension,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus[media_doc["preprocessing"]])
            # TODO: remove in scope of CVS-163688
            if "preprocessing" in media_doc and media_doc["preprocessing"] is not None
            else MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )

    @staticmethod
    def __video_from_media_doc(media_doc: dict) -> Video:
        media_extension = media_doc.get("media_extension")
        extension = VideoExtensions[media_extension] if media_extension is not None else VideoExtensions.MP4

        return Video(
            name=media_doc["media_name"],
            id=IDToMongo.backward(media_doc["media_identifier"]["media_id"]),
            uploader_id=media_doc["uploader_id"],
            fps=media_doc["frame_rate"] if media_doc["frame_rate"] else 0,
            width=media_doc["media_width"],
            height=media_doc["media_height"],
            total_frames=media_doc["frame_count"] if media_doc["frame_count"] else 0,
            size=media_doc["size"],
            stride=media_doc["frame_stride"] if media_doc["frame_stride"] else 0,
            creation_date=DatetimeToMongo.backward(media_doc["upload_date"]),
            extension=extension,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus[media_doc["preprocessing"]])
            # TODO: remove in scope of CVS-163688
            if "preprocessing" in media_doc and media_doc["preprocessing"] is not None
            else MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )

    @staticmethod
    def create_query_results(
        doc: dict,
        dataset_filter: DatasetFilter,
        ds_identifier: DatasetStorageIdentifier,
        total_images: int,
        total_videos: int,
        should_group_video_frames: bool,
    ) -> QueryResults:
        """
        Create a QueryResults object from a database result object and dataset filter.

        :param doc: the result object from database
        :param dataset_filter: the dataset filter object
        :param ds_identifier: DatasetIdentifier to initialize repo which items need
        to be found in
        :param total_images: total number of images in the dataset that is filtered
        :param total_videos: total number of videos in the dataset that is filtered
        :param should_group_video_frames: Boolean indicating whether to video frames have been grouped
        :return: QueryResults object
        """
        docs = list(doc["paginated_results"])

        video_annotation_statistics_by_id: dict[ID, VideoAnnotationStatistics] = {}
        if should_group_video_frames:
            # video annotation statistics are independent of the filter and have to be retrieved separately
            ds_filter_repo = DatasetStorageFilterRepo(ds_identifier)
            video_annotation_statistics_by_id = ds_filter_repo.get_video_annotation_statistics_by_ids(
                video_ids={
                    IDToMongo.backward(doc["media_identifier"]["media_id"])
                    for doc in docs
                    if doc["media_identifier"]["type"] in [MediaType.VIDEO.value, MediaType.VIDEO_FRAME.value]
                }
            )

        media_query_results: list[MediaQueryResult] = []
        for media_doc in docs:
            matched_frames = media_doc.get("matched_frames", 1)
            if matched_frames == 0:
                # Video docs with 0 matched frames should be ignored
                continue

            annotation_scene_details = QueryBuilder._get_annotation_scene_details(media_doc)
            media_identifier = MediaIdentifierToMongo.backward(media_doc["media_identifier"])  # type: ignore
            video_annotation_statistics = None

            media: Image | Video
            if media_identifier.media_type in [MediaType.VIDEO_FRAME, MediaType.VIDEO]:
                if should_group_video_frames:
                    # this is the case for media filtering
                    media_identifier = MatchedFramesVideoIdentifier(
                        video_id=media_identifier.media_id,
                        matched_frames=matched_frames,
                    )
                    video_annotation_statistics = video_annotation_statistics_by_id[media_identifier.media_id]

                media = QueryBuilder.__video_from_media_doc(media_doc)
            else:
                media = QueryBuilder.__image_from_media_doc(media_doc)

            media_query_results.append(
                MediaQueryResult(
                    media_identifier=media_identifier,
                    media=media,
                    annotation_scene_id=annotation_scene_details.annotation_scene_id,
                    roi_id=annotation_scene_details.roi_id,
                    last_annotator_id=annotation_scene_details.last_annotator_id,
                    video_annotation_statistics=video_annotation_statistics,
                )
            )

        matching_images_count = doc["image_count"][0]["count"] if doc["image_count"] else 0
        matching_videos_count = doc["video_count"][0]["count"] if doc["video_count"] else 0
        matching_video_frames_count = doc["video_frame_count"][0]["count"] if doc["video_frame_count"] else 0

        return QueryResults(
            media_query_results=media_query_results,
            skip=dataset_filter.limit + dataset_filter.skip,
            matching_images_count=matching_images_count,
            matching_videos_count=matching_videos_count,
            matching_video_frames_count=matching_video_frames_count,
            total_images_count=total_images,
            total_videos_count=total_videos,
        )

    @staticmethod
    def _get_annotation_scene_details(
        media_doc: dict[str, Any],
    ) -> AnnotationSceneDetails:
        """
        Get annotation scene id, roi id and last annotator id if non-empty annotation scene for media exist

        :param media_doc: dict containing DB content of media
        :return AnnotationSceneDetails containing annotation scene id, roi id and last annotator id
        """
        annotation_scene_details = AnnotationSceneDetails()

        media_annotation_state = media_doc.get("media_annotation_state")
        if media_annotation_state not in [None, "NONE"]:
            ann_scene_id = media_doc.get("annotation_scene_id")
            annotation_scene_details.annotation_scene_id = ID(ann_scene_id) if ann_scene_id is not None else None
            roi = media_doc.get("roi")
            roi_id = None
            if roi is not None:
                roi_id = roi.get("_id", None)
            annotation_scene_details.roi_id = ID(roi_id) if roi_id is not None else None
            last_annotator_id = media_doc.get("user_name")
            annotation_scene_details.last_annotator_id = (
                ID(last_annotator_id) if last_annotator_id is not None else None
            )

        return annotation_scene_details

    @staticmethod
    def _get_additional_media(
        docs: list[dict],
        ds_identifier: DatasetStorageIdentifier,
    ) -> tuple[dict[ID, Image], dict[ID, Video]]:
        """
        Get additional media for filtered media

        Media can only be retrieved from the image/video repo

        :param docs: List of the MongoDB documents from the dataset storage filter repo
                     of the filtered images and videos
        :param ds_identifier: DatasetStorageIdentifier that the images and videos belong to
        """
        image_repo = ImageRepo(ds_identifier)
        image_ids = {
            IDToMongo.backward(doc["media_identifier"]["media_id"])
            for doc in docs
            if doc["media_identifier"]["type"] == MediaType.IMAGE.value
        }
        image_by_id = image_repo.get_image_by_ids(image_ids)
        video_repo = VideoRepo(ds_identifier)
        video_ids = {
            IDToMongo.backward(doc["media_identifier"]["media_id"])
            for doc in docs
            if doc["media_identifier"]["type"] in [MediaType.VIDEO.value, MediaType.VIDEO_FRAME.value]
        }
        video_by_id = video_repo.get_video_by_ids(video_ids)

        return image_by_id, video_by_id

    @staticmethod
    def _cache_media_scores_annotated_label_ids(
        dataset_storage_identifier: DatasetStorageIdentifier, model_test_result_id: ID
    ) -> None:
        """
        Cache the user-annotated label IDs for a media item in the media_scores MongoDB document if they are
        not already available.

        :param dataset_storage_identifier: Identifier of the dataset_storage for the media scores
        :param model_test_result_id: ID of the model test result containing the media scores
        """
        project_identifier = ProjectIdentifier(
            workspace_id=dataset_storage_identifier.workspace_id,
            project_id=dataset_storage_identifier.project_id,
        )
        media_score_repo = MediaScoreRepo(dataset_storage_identifier)

        # Find any media score that don't have "annotated_label_ids"
        query_annotated_labels_not_cached = {
            "model_test_result_id": IDToMongo.forward(model_test_result_id),
            "annotated_label_ids": {"$exists": False},
        }
        missing_annotated_labels = media_score_repo.count(extra_filter=query_annotated_labels_not_cached)
        # early termination, all media scores have "annotated_label_ids"
        if missing_annotated_labels == 0:
            return

        # Populate "annotated_label_ids" field
        dataset_repo = DatasetRepo(dataset_storage_identifier)
        model_test_result_repo = ModelTestResultRepo(project_identifier)
        annotation_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)
        model_test_result = model_test_result_repo.get_by_id(model_test_result_id)

        dataset_item_repo = dataset_repo.get_dataset_item_repo(dataset_id=model_test_result.ground_truth_dataset_id)
        annotation_scene_ids = dataset_item_repo.distinct("annotation_scene_id")
        annotated_labels_query: list[dict] = [
            {"$match": {"_id": {"$in": list(annotation_scene_ids)}}},
            {
                "$project": {
                    "label_ids": "$label_ids",
                    "media_identifier": "$media_identifier",
                }
            },
        ]
        annotated_labels_info = annotation_scene_repo.aggregate_read(
            annotated_labels_query, collation=Collation(locale="en_US")
        )
        updated_media_scores = 0
        for label_info in annotated_labels_info:
            label_ids = [IDToMongo.backward(_id) for _id in label_info["label_ids"]]
            media_identifier = MediaIdentifierToMongo.backward(label_info["media_identifier"])
            media_score_repo.set_annotated_label_ids_by_test_and_media_identifier(
                annotated_label_ids=label_ids,
                model_test_result_id=model_test_result_id,
                media_identifier=media_identifier,
            )
            updated_media_scores += 1
        logger.debug(f"Updated {updated_media_scores} media scores with annotated label ids")

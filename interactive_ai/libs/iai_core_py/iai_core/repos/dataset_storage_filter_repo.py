# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the repos for dataset storage filtering"""

from collections.abc import Callable, Iterable, Sequence
from random import shuffle
from typing import Any

from pymongo import DESCENDING, IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core.entities.annotation_scene_state import AnnotationState
from iai_core.entities.dataset_storage_filter_data import DatasetStorageFilterData, NullDatasetStorageFilterData
from iai_core.entities.media import MediaPreprocessingStatus
from iai_core.entities.video_annotation_statistics import VideoAnnotationStatistics
from iai_core.repos.base.dataset_storage_based_repo import DatasetStorageBasedSessionRepo
from iai_core.repos.base.session_repo import QueryAccessMode
from iai_core.repos.mappers import CursorIterator, IDToMongo, MediaIdentifierToMongo
from iai_core.repos.mappers.mongodb_mappers.dataset_storage_filter_mapper import DatasetStorageFilterDataToMongo

from geti_types import (
    ID,
    DatasetStorageIdentifier,
    MediaIdentifierEntity,
    MediaType,
    Session,
    VideoFrameIdentifier,
    VideoIdentifier,
)


class DatasetStorageFilterRepo(DatasetStorageBasedSessionRepo[DatasetStorageFilterData]):
    """
    Repository to store dataset storage filtering data
    """

    collection_name = "dataset_storage_filter_data"

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name=self.collection_name,
            session=session,
            dataset_storage_identifier=dataset_storage_identifier,
        )

    @property
    def forward_map(self) -> Callable[[DatasetStorageFilterData], dict]:
        return DatasetStorageFilterDataToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], DatasetStorageFilterData]:
        return DatasetStorageFilterDataToMongo.backward

    @property
    def null_object(self) -> DatasetStorageFilterData:
        return NullDatasetStorageFilterData()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=DatasetStorageFilterDataToMongo,
            parameter=None,
        )

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel([("media_identifier.media_id", DESCENDING)]),  # Indexed to quickly filter in a video
            IndexModel(
                [("media_identifier.type", DESCENDING)]
            ),  # Indexed to quickly exclude results of not relevant types
            IndexModel(
                [("media_identifier.frame_index", DESCENDING)]
            ),  # Indexed to quickly fetch annotated frame indices
            IndexModel(
                [("annotation_scene_id", DESCENDING)]
            ),  # Indexed to quickly update media_annotation_state to revisit
            IndexModel([("media_name", DESCENDING)]),  # Indexed because results can be filtered by name
            IndexModel([("label_ids", DESCENDING)]),  # Frequently filtered by
            IndexModel([("upload_date", DESCENDING)]),  # Indexed because results can be sorted by upload_date
            IndexModel([("media_annotation_state", DESCENDING)]),  # Indexed to count annotated video frames
        ]
        return super_indexes + new_indexes

    def upsert_dataset_storage_filter_data(
        self,
        dataset_storage_filter_data: DatasetStorageFilterData,
    ) -> None:
        """
        Updates a DatasetStorageFilterData entity to the database.

        - If a document with this id does not already exist, a new document is created.
        - If for a new document, media_annotation_state is not specified, it is set to None.
        - If filter data for a video is upserted, a field "unannotated_frames" is added with the total frames
        - If a new doc for a VideoFrameIdentifier gets created, the unannotated_frames of the corresponding
          video is decreased by 1

        :param dataset_storage_filter_data: Object to save
        """
        data_filter = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        data_filter["_id"] = IDToMongo.forward(dataset_storage_filter_data.id_)

        dataset_storage_filter_data_dict = DatasetStorageFilterDataToMongo.forward(dataset_storage_filter_data)
        if dataset_storage_filter_data.media_identifier.media_type is MediaType.VIDEO:
            video_id = dataset_storage_filter_data.media_identifier.media_id
            media_filter_data = dataset_storage_filter_data.media_filter_data
            if (
                media_filter_data is None
                or media_filter_data.video_filter_data is None
                or media_filter_data.video_filter_data.unannotated_frames is None
            ):
                raise ValueError(
                    f"A DatasetStorageFilterData for a VideoIdentifier should always "
                    f"contain a media_filter_data with unannotated_frames specified: "
                    f"{dataset_storage_filter_data}."
                )
            # For a new video upload, the MediaFilterData.unannotated_frames is set to the total_frames of the video
            # entity. However, for rare cases, like dataset imports, it could be that some annotation scenes for video
            # frames have been processed before the video entity itself, therefore we have to subtract any video frame
            # already in the collection. Annotation scenes for video frames processed after the video entity, will
            # cause the "unannotated_frames" field of the video entity to be decreased by 1 (see the code a few lines
            # below in this method).
            dataset_storage_filter_data_dict["unannotated_frames"] = (
                media_filter_data.video_filter_data.unannotated_frames
                - len(self.get_video_frame_indices(video_id=video_id))
            )

        update: dict = {"$set": dataset_storage_filter_data_dict}
        if "media_annotation_state" not in dataset_storage_filter_data_dict:
            update["$setOnInsert"] = {"media_annotation_state": "NONE"}

        update_result = self._collection.update_one(
            filter=data_filter,
            update=update,
            upsert=True,
        )
        dataset_storage_filter_data.mark_as_persisted()

        media_identifier = dataset_storage_filter_data.media_identifier
        if update_result.upserted_id is not None and media_identifier.media_type is MediaType.VIDEO_FRAME:
            # If a new video frame is inserted into the DB, decrease the
            # unannotated_frames of the corresponding video by 1
            video_identifier = VideoIdentifier(video_id=media_identifier.media_id)
            video_id = video_identifier.as_id()
            video_data_filter = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
            video_data_filter["_id"] = IDToMongo.forward(video_id)
            self._collection.update_one(
                filter=video_data_filter,
                update={
                    "$inc": {"unannotated_frames": -1},
                    "$setOnInsert": {"media_identifier": MediaIdentifierToMongo.forward(video_identifier)},
                },
                upsert=True,
            )

    def update_preprocessing_status(
        self, media_identifier: MediaIdentifierEntity, status: MediaPreprocessingStatus
    ) -> None:
        """
        Updates a DatasetStorageFilterData entity in the database with new media preprocessing status.
        :param media_identifier: media identifier
        :param status: media preprocessing status
        """
        data_filter = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        data_filter["_id"] = IDToMongo.forward(media_identifier.as_id())

        self._collection.update_one(filter=data_filter, update={"$set": {"preprocessing": status.value}}, upsert=False)

    def delete_all_by_media_id(self, media_id: ID) -> None:
        """
        Delete all DatasetStorageFilterData associated with a media from the database.

        Videos can have multiple entries, one for each video frame. Both video and its
        video frames will be deleted. For images, only one entry should exist.

        :param media_id: ID of the media to delete entities for
        """
        query = {"media_identifier.media_id": IDToMongo.forward(media_id)}
        self.delete_all(extra_filter=query)

    def update_annotation_scenes_to_revisit(self, annotation_scene_ids: Sequence[ID]) -> None:
        """
        Update entries annotation state to TO_REVISIT based on annotation_scene_id

        :param annotation_scene_ids: ID of annotation scenes that have been suspended
            due to a change in the label schema
        """
        set_to_revisit = {"$set": {"media_annotation_state": "TO_REVISIT"}}

        # Update in chunks of 100 to avoid performance bottlenecks
        for i in range(0, len(annotation_scene_ids), 100):
            annotation_scene_ids_chunk = annotation_scene_ids[i : i + 100]
            data_filter: dict[str, Any] = self.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
            data_filter["annotation_scene_id"] = {"$in": [IDToMongo.forward(id_) for id_ in annotation_scene_ids_chunk]}
            self._collection.update_many(filter=data_filter, update=set_to_revisit, upsert=False)

    def get_video_frame_indices(self, video_id: ID) -> set[int]:
        """
        Get the video frame indices of a video that have a doc in the filter repo

        :param video_id: ID of the video
        :returns set of video frame indices
        """
        data_filter = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        data_filter["media_identifier.media_id"] = IDToMongo.forward(video_id)
        data_filter["media_identifier.type"] = MediaType.VIDEO_FRAME.value
        docs = self._collection.find(filter=data_filter, projection=["media_identifier.frame_index"])
        return {doc["media_identifier"]["frame_index"] for doc in docs}

    def get_media_identifiers_by_annotation_state(
        self, annotation_state: AnnotationState, sample_size: int = 10000
    ) -> list[MediaIdentifierEntity]:
        """
        Get a list of randomized media identifiers that have a specific annotation state.

        :param annotation_state: AnnotationState to filter the media identifiers
        :param sample_size: int maximum number of returned media identifiers
        """
        if sample_size <= 0:
            raise ValueError(f"sample_size should be a positive integer, but {sample_size} was given.")

        image_data_filter: dict[str, Any] = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        image_data_filter["media_annotation_state"] = annotation_state.name
        image_data_filter["media_identifier.type"] = {"$ne": "video"}
        image_and_frame_docs = self._collection.find(
            filter=image_data_filter, limit=sample_size, projection=["media_identifier"]
        )
        media_identifiers = [MediaIdentifierToMongo.backward(doc["media_identifier"]) for doc in image_and_frame_docs]

        if annotation_state is AnnotationState.NONE:
            # for performance, reduce video sample size. Assume each video has at least 20 relevant frames
            video_sample_size = int(sample_size / 20) + 1

            pipeline: list[dict[str, Any]] = [
                {
                    "$match": {
                        "media_identifier.type": "video",
                        "unannotated_frames": {"$ne": 0},
                    },
                },
                {
                    "$sample": {
                        "size": video_sample_size,
                    }
                },
                {
                    "$project": {
                        "media_identifier": "$media_identifier",
                    }
                },
                {
                    "$lookup": {
                        "from": "video",
                        "as": "video_info",
                        "let": {"media_id": "$media_identifier.media_id"},
                        "pipeline": [
                            self.preliminary_aggregation_match_stage(QueryAccessMode.READ),
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": [
                                            "$$media_id",
                                            "$_id",
                                        ]
                                    },
                                }
                            },
                            {
                                "$project": {
                                    "stride": "$stride",
                                    "total_frames": "$total_frames",
                                }
                            },
                        ],
                    }
                },
                {
                    "$unwind": "$video_info",
                },
                {
                    "$addFields": {
                        "stride": "$video_info.stride",
                        "total_frames": "$video_info.total_frames",
                    },
                },
                {
                    "$unset": "video_info",
                },
                {
                    "$lookup": {
                        "from": "dataset_storage_filter_data",
                        "as": "frames_info",
                        "let": {"media_id": "$media_identifier.media_id"},
                        "pipeline": [
                            self.preliminary_aggregation_match_stage(QueryAccessMode.READ),
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": [
                                            "$$media_id",
                                            "$media_identifier.media_id",
                                        ]
                                    },
                                }
                            },
                            {"$project": {"media_identifier": "$media_identifier"}},
                        ],
                    }
                },
                {
                    "$addFields": {
                        "annotated_frame_indices": "$frames_info.media_identifier.frame_index",
                    },
                },
                {
                    "$unset": "frames_info",
                },
            ]
            video_docs = self.aggregate_read(pipeline=pipeline)
            media_identifiers.extend(
                VideoFrameIdentifier(
                    video_id=IDToMongo.backward(video_doc["media_identifier"]["media_id"]),
                    frame_index=frame_index,
                )
                for video_doc in video_docs
                for frame_index in range(0, video_doc["total_frames"], video_doc["stride"])
                if frame_index not in video_doc["annotated_frame_indices"]
            )

        shuffle(media_identifiers)
        return media_identifiers[:sample_size]

    def get_video_annotation_statistics_by_ids(self, video_ids: Iterable[ID]) -> dict[ID, VideoAnnotationStatistics]:
        """
        Get the video annotation statistics (number of annotated, unannotated and partially annotated frames)
        for all given video IDs.

        The video annotation statistics are independent of the filter and should always describe all frames,
        therefore we have to obtain these statistics separately from the filter query.

        :param video_ids: IDs of the videos for which to get the annotation statistics.
        :return: Dictionary containing per-video annotation statistics {video_id: video_annotation_statistics}
        """
        if not video_ids:
            return {}

        mongo_video_ids = [IDToMongo.forward(video_id) for video_id in video_ids]

        pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "media_identifier.media_id": {"$in": mongo_video_ids},
                },
            },
            {
                "$group": {
                    "_id": "$media_identifier.media_id",
                    "annotated": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$media_annotation_state", "ANNOTATED"]},
                                1,
                                0,
                            ]
                        }
                    },
                    "partially_annotated": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$media_annotation_state",
                                        "PARTIALLY_ANNOTATED",
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "unannotated": {"$sum": {"$ifNull": ["$unannotated_frames", 0]}},
                }
            },
        ]

        video_docs = self.aggregate_read(pipeline=pipeline)

        return {
            IDToMongo.backward(video_doc["_id"]): VideoAnnotationStatistics(
                annotated=video_doc["annotated"],
                partially_annotated=video_doc["partially_annotated"],
                unannotated=video_doc["unannotated"],
            )
            for video_doc in video_docs
        }

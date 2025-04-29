# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the repository for annotation entities"""

from collections.abc import Callable, Sequence
from functools import partial
from typing import Any, cast

from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.client_session import ClientSession
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from sc_sdk.entities.annotation import AnnotationScene, AnnotationSceneKind, NullAnnotationScene
from sc_sdk.repos.base.dataset_storage_based_repo import DatasetStorageBasedSessionRepo
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator
from sc_sdk.repos.mappers.mongodb_mappers.annotation_mapper import AnnotationSceneToMongo
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from sc_sdk.repos.mappers.mongodb_mappers.media_mapper import MediaIdentifierToMongo

from geti_types import (
    ID,
    DatasetStorageIdentifier,
    MediaIdentifierEntity,
    NullMediaIdentifier,
    ProjectIdentifier,
    Session,
    VideoFrameIdentifier,
)


class AnnotationSceneRepo(DatasetStorageBasedSessionRepo[AnnotationScene]):
    """
    Repository to persist AnnotationScene entities in the database.

    :param dataset_storage_identifier: Identifier of the dataset_storage
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    collection_name = "annotation_scene"

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name=AnnotationSceneRepo.collection_name,
            session=session,
            dataset_storage_identifier=dataset_storage_identifier,
        )
        self.project_identifier = ProjectIdentifier(
            workspace_id=dataset_storage_identifier.workspace_id,
            project_id=dataset_storage_identifier.project_id,
        )

    @property
    def forward_map(self) -> Callable[[AnnotationScene], dict]:
        return AnnotationSceneToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], AnnotationScene]:
        return partial(AnnotationSceneToMongo.backward, project_identifier=self.project_identifier)

    @property
    def null_object(self) -> NullAnnotationScene:
        return NullAnnotationScene()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=AnnotationSceneToMongo,
            parameter=self.project_identifier,
        )

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel(
                [
                    ("dataset_storage_id", DESCENDING),
                    ("media_identifier.media_id", DESCENDING),
                    ("kind", DESCENDING),
                    ("media_identifier.frame_index", ASCENDING),
                ]
            ),
            IndexModel(
                [
                    ("dataset_storage_id", DESCENDING),
                    ("kind", DESCENDING),
                    ("media_identifier", DESCENDING),
                    ("creation_date", ASCENDING),
                ]
            ),
        ]
        return super_indexes + new_indexes

    def save(
        self,
        instance: AnnotationScene,
        mongodb_session: ClientSession | None = None,  # noqa: ARG002
    ) -> None:
        """
        Save an AnnotationScene to the database.

        If the annotation does not exist in the database (i.e. `annotation.id_ == ID()`),
        the annotation will be created and `annotation.id_` will be automatically
        updated in-place with the new ID.
        If a document with the same id already exists, it is overwritten.
        Otherwise, a new document is created.

        Steps:
          1) serialize the entity
          2) inject context
          3) insert to DB
          4) mark the object as persisted

        :param instance: AnnotationScene to save
        :param mongodb_session: Optional, ClientSession for MongoDB transactions
        """
        if isinstance(instance.media_identifier, NullMediaIdentifier):
            raise ValueError("Cannot save annotation that does not belong to a Media.")
        if instance.id_ == ID():
            instance.id_ = self.generate_id()
        super().save(instance)

    def delete_all_by_media_id(self, media_id: ID) -> None:
        """
        Delete all annotation entities associated with a media from the database.

        :param media_id: ID of the media to delete entities for
        """
        query = {"media_identifier.media_id": IDToMongo.forward(media_id)}
        self.delete_all(extra_filter=query)

    def count_all_by_identifier_and_annotation_kind(
        self,
        media_identifier: MediaIdentifierEntity,
        annotation_kind: AnnotationSceneKind | list[AnnotationSceneKind],
    ) -> int:
        """
        Count all annotation scenes associated with a media with a specified kind from the database.

        :param media_identifier: Identifier of the media to count entities for
        :param annotation_kind: Type(s) of annotations to consider (e.g. user annotation vs prediction).
        :return: count of all annotation entities associated with the media
        """
        if not isinstance(annotation_kind, list):
            annotation_kind = [annotation_kind]
        query = {
            "kind": {"$in": [str(annotation_kind) for annotation_kind in annotation_kind]},
            "media_identifier": MediaIdentifierToMongo.forward(media_identifier),
        }
        return self.count(extra_filter=query)

    def delete_n_earliest_annotations_by_identifier_and_annotation_kind(
        self,
        media_identifier: MediaIdentifierEntity,
        annotation_kind: AnnotationSceneKind | list[AnnotationSceneKind],
        n: int = 1,
    ) -> bool:
        """
        Deletes n number of annotation scenes, sorted by ID from oldest to newest, associated with a media and with a
        specified annotation kind.

        :param media_identifier: Identifier of the media to delete entities for
        :param annotation_kind: Type(s) of annotations to consider (e.g. user annotation vs prediction).
        :param n: Amount of annotations to delete
        :return: True if documents were deleted, False otherwise
        """
        if not isinstance(annotation_kind, list):
            annotation_kind = [annotation_kind]
        query_match = {
            "kind": {"$in": [str(annotation_kind) for annotation_kind in annotation_kind]},
            "media_identifier": MediaIdentifierToMongo.forward(media_identifier),
        }
        pipeline: list[dict] = [
            {"$match": query_match},
            {"$sort": {"creation_date": 1}},
            {"$limit": n},
        ]
        aggregation_results = self.aggregate_read(pipeline)
        _ids = [r["_id"] for r in aggregation_results]
        return self.delete_all({"_id": {"$in": _ids}})

    def get_latest_annotation_by_kind_and_identifier(
        self,
        media_identifier: MediaIdentifierEntity,
        annotation_kind: AnnotationSceneKind | list[AnnotationSceneKind],
        task_id: ID | None = None,
        model_ids: set[ID] | None = None,
    ) -> AnnotationScene:
        """
        Get the latest AnnotationScene of the given type for a specific media identifier.

        :param media_identifier: Identifier of the media relative to the annotation
        :param annotation_kind: Type(s) of annotations to consider (e.g. user annotation
            vs prediction).
        :param task_id: ID of the task (only if kind is TASK_PREDICTION).
        :param model_ids: ID of the models to be used for filtering (only for kind
            PREDICTION or TASK_PREDICTION)
        :return: AnnotationScene entity, or NullAnnotationScene if not found
        """
        return self.get_latest_annotations_by_kind_and_identifiers(
            media_identifiers=[media_identifier],
            annotation_kind=annotation_kind,
            task_id=task_id,
            model_ids=model_ids,
        )[0]

    def get_latest_annotations_by_kind_and_identifiers(
        self,
        media_identifiers: Sequence[MediaIdentifierEntity],
        annotation_kind: AnnotationSceneKind | list[AnnotationSceneKind],
        task_id: ID | None = None,
        model_ids: set[ID] | None = None,
    ) -> tuple[AnnotationScene, ...]:
        """
        Get the latest AnnotationScene with a given type for all the specified media.

        If no annotation is found for a media identifier, then a NullAnnotationScene is
        used as placeholder in the output list at the position relative to that media.

        :param media_identifiers: Identifiers of the media relative to the annotations
        :param annotation_kind: Type(s) of annotations to consider (e.g. user annotation
            vs prediction).
        :param task_id: ID of the task (only if kind is TASK_PREDICTION).
        :param model_ids: ID of the models to be used for filtering (only for kind
            PREDICTION or TASK_PREDICTION)
        :return: Tuple of AnnotationScene entities, where each item is the latest
            annotation for the media at the same position in the input sequence.
            NullAnnotationScene is used for media whose annotation cannot be found.
        """
        if not isinstance(annotation_kind, list):
            annotation_kind = [annotation_kind]

        match_dict: dict = {
            "kind": {"$in": [str(annotation_kind) for annotation_kind in annotation_kind]},
            "media_identifier": {
                "$in": [MediaIdentifierToMongo.forward(media_identifier) for media_identifier in media_identifiers]
            },
        }
        # Match on task_id can be skipped if model_ids is available
        if task_id is not None and model_ids is None:
            match_dict["task_id"] = IDToMongo.forward(task_id)
        if model_ids is not None:
            match_dict["model_ids"] = {"$all": [IDToMongo.forward(model_id) for model_id in model_ids]}

        pipeline: list[dict] = [
            {"$match": match_dict},
            {"$sort": {"creation_date": 1}},
            {"$group": {"_id": "$media_identifier", "annotation": {"$last": "$$ROOT"}}},
        ]

        annotation_docs = self.aggregate_read(pipeline)
        annotation_map = {
            MediaIdentifierToMongo.backward(doc["_id"]): self.backward_map(doc["annotation"]) for doc in annotation_docs
        }

        return tuple(
            (annotation_map[identifier] if identifier in annotation_map else NullAnnotationScene())
            for identifier in media_identifiers
        )

    def get_latest_annotations_by_kind_and_media_id(
        self,
        media_id: ID,
        annotation_kind: AnnotationSceneKind | list[AnnotationSceneKind],
        task_id: ID | None = None,
        model_ids: set[ID] | None = None,
    ) -> tuple[AnnotationScene, ...]:
        """
        Get the latest AnnotationScene of the given type relative to a specific media id.

        Note that the same media id may correspond to multiple media identifiers
        (in case of videos), so the method returns a list of annotations (one per frame).

        :param media_id: ID of the media (image or video)
        :param annotation_kind: Type(s) of annotations to consider (e.g. user annotation
            vs prediction).
        :param task_id: ID of the task (only if kind is TASK_PREDICTION).
        :param model_ids: ID of the models to be used for filtering (only for kind
            PREDICTION or TASK_PREDICTION)
        :return: tuple of AnnotationScene entities
        """
        if not isinstance(annotation_kind, list):
            annotation_kind = [annotation_kind]
        pipeline = self._build_query_for_latest_annotations_by_media_id(
            media_id=media_id,
            kind=annotation_kind,
            task_id=task_id,
            model_ids=model_ids,
        )
        aggregation_results = self.aggregate_read(pipeline)
        return tuple(self.backward_map(result["annotation"]) for result in aggregation_results)

    @staticmethod
    def _build_query_for_latest_annotations_by_media_id(
        media_id: ID,
        kind: list[AnnotationSceneKind] | None = None,
        task_id: ID | None = None,
        model_ids: set[ID] | None = None,
        frame_index_query: dict[str, Any] | None = None,
    ) -> list:
        if kind is None:
            kind = [AnnotationSceneKind.ANNOTATION]
        query_match = {
            "media_identifier.media_id": IDToMongo.forward(media_id),
            "kind": {"$in": [str(annotation_kind) for annotation_kind in kind]},
        }
        if frame_index_query is not None:
            query_match["media_identifier.frame_index"] = frame_index_query
        # Match on task_id can be skipped if model_ids is available
        if task_id is not None and model_ids is None:
            query_match["task_id"] = IDToMongo.forward(task_id)
        if model_ids is not None:
            query_match["model_ids"] = {"$all": [IDToMongo.forward(model_id) for model_id in model_ids]}  # type: ignore
        return [
            {"$match": query_match},
            {"$sort": {"creation_date": 1}},
            {
                "$group": {
                    "_id": "$media_identifier",
                    "annotation": {"$last": "$$ROOT"},
                    "media_identifier": {"$last": "$media_identifier"},
                }
            },
        ]

    def get_video_frame_annotations_by_video_id(  # noqa: PLR0913
        self,
        video_id: ID,
        annotation_kind: AnnotationSceneKind = AnnotationSceneKind.ANNOTATION,
        start_frame: int | None = None,
        end_frame: int | None = None,
        frame_skip: int | None = None,
        limit: int | None = None,
        task_id: ID | None = None,
        model_ids: set[ID] | None = None,
    ) -> tuple[list[AnnotationScene], int]:
        """
        Get the latest annotation scene for video frames that have annotations of the given type.

        :param video_id: ID of the video to add the annotation to
        :param annotation_kind: Type of annotations to consider (user annotation vs prediction).
        :param start_frame: return annotation scenes for frame indices greater than or equal to start frame,
        :param end_frame: return annotation scenes for frame indices smaller than or equal end frame,
        :param frame_skip: return annotation scenes for frame indices that are a multiple of frame_skip,
        :param limit: sets a maximum number of annotation scenes to return,
        :param task_id: ID of the task (only if kind is TASK_PREDICTION).
        :param model_ids: ID of the models to be used for filtering (only for kind
            PREDICTION or TASK_PREDICTION)
        :return A tuple with a list of annotation scenes and the total matching annotation scenes (without applying a
            limit)
        """
        frame_index_query: dict[str, Any] = {}
        if start_frame is not None:
            frame_index_query["$gte"] = start_frame
        if end_frame is not None:
            frame_index_query["$lte"] = end_frame
        if frame_skip is not None and frame_skip > 1:
            frame_index_query["$mod"] = [frame_skip, 0]
        pipeline: list[dict] = self._build_query_for_latest_annotations_by_media_id(
            media_id=video_id,
            kind=[annotation_kind],
            task_id=task_id,
            model_ids=model_ids,
            frame_index_query=frame_index_query if frame_index_query else None,
        )
        # Filter out empty annotations which were created when the video was uploaded
        pipeline.append({"$match": {"annotation.label_ids": {"$not": {"$size": 0}}}})
        sort_and_limit_pipeline: list[dict[str, Any]] = [{"$sort": {"_id.frame_index": 1}}]
        if limit is not None:
            sort_and_limit_pipeline.append({"$limit": limit})
        pipeline.append(
            {
                "$facet": {
                    "annotation_scenes": sort_and_limit_pipeline,
                    "count": [{"$count": "count"}],
                }
            }
        )
        aggregation_results = self.aggregate_read(pipeline).next()

        annotation_scenes = [
            self.backward_map(annotation_scene_doc["annotation"])
            for annotation_scene_doc in aggregation_results["annotation_scenes"]
        ]
        count = aggregation_results["count"][0]["count"] if aggregation_results["count"] else 0

        return annotation_scenes, count

    def get_annotated_video_frame_identifiers_by_video_id(
        self,
        video_id: ID,
        annotation_kind: AnnotationSceneKind = AnnotationSceneKind.ANNOTATION,
        task_id: ID | None = None,
        model_ids: set[ID] | None = None,
    ) -> list[VideoFrameIdentifier]:
        """
        Get all the video frame identifiers of frames that have annotations of the given type.

        :param video_id: ID of the video to add the annotation to
        :param annotation_kind: Type of annotations to consider (user annotation vs prediction).
        :param task_id: ID of the task (only if kind is TASK_PREDICTION).
        :param model_ids: ID of the models to be used for filtering (only for kind
            PREDICTION or TASK_PREDICTION)
        :return List of VideoFrameIdentifiers
        """
        video_frame_annotations, _ = self.get_video_frame_annotations_by_video_id(
            video_id=video_id,
            annotation_kind=annotation_kind,
            task_id=task_id,
            model_ids=model_ids,
        )

        return [
            cast("VideoFrameIdentifier", annotation_scene.media_identifier)
            for annotation_scene in video_frame_annotations
        ]

    @staticmethod
    def _get_query_latest(
        annotation_kind: AnnotationSceneKind | None = None,
    ) -> list[Any]:
        """
        Returns a query aggregate to only retrieve the latest annotations

        :param annotation_kind: Optional argument used to filter by annotation kind
        :return: Aggregate query with to get the latest annotations
        """
        query: list = [] if annotation_kind is None else [{"$match": {"kind": annotation_kind.name}}]
        query.extend(
            [
                {"$sort": {"media_identifier": -1, "creation_date": 1}},
                {
                    "$group": {
                        "_id": "$media_identifier",
                        "annotation": {"$last": "$$ROOT"},
                    }
                },
                {"$replaceRoot": {"newRoot": "$annotation"}},
            ]
        )
        return query

    def get_all_by_kind(
        self,
        *,
        kind: AnnotationSceneKind,
    ) -> CursorIterator[AnnotationScene]:
        """
        Get all the latest annotations of the given type.

        :param kind: Type of annotations to consider (user annotation vs prediction)
        :param newer_than_id: Only return entities that are newer than given ID.
        :return: CursorIterator with annotations
        """
        pipeline = self._get_query_latest(annotation_kind=kind)
        cursor = self.aggregate_read(pipeline)
        return self.cursor_wrapper(cursor)

    def get_all_by_kind_and_labels(
        self, kind: AnnotationSceneKind, label_ids: list[ID], only_latest: bool = True
    ) -> CursorIterator[AnnotationScene]:
        """
        Get all the annotation scenes inside the dataset storage for a specific kind and
        with specific labels.

        :param kind: Type of annotations to consider (user annotation vs prediction)
        :param label_ids: List of label ids which need to be in the annotation scene.
        :param only_latest: Only consider the latest available of each annotation kind
        for each media entity.
        """
        pipeline = [
            {
                "$match": {
                    "kind": str(kind),
                    "label_ids": {"$in": [IDToMongo.forward(label_id) for label_id in label_ids]},
                }
            }
        ]
        if only_latest:
            pipeline.extend(self._get_query_latest())
        cursor = self.aggregate_read(pipeline)
        return self.cursor_wrapper(cursor)

    def count_label_occurrence(
        self,
        label_ids: Sequence[ID],
    ) -> tuple[dict, dict]:
        """
        Counts the number of occurrences for each label_id, at annotation and shape level.
        Only considers the latest user annotations, i.e. of kind `ANNOTATION`.
        Returns two dictionaries:
            1. per annotation: a dict with label id -> set(annotation_ids)
            2. per shape: a dict with label id -> int of occurrence.

        :param label_ids: sequence of label IDs for filtering annotations
        :return: Two dictionaries with per-label_id counts
        """
        query = self._get_query_latest(annotation_kind=AnnotationSceneKind.ANNOTATION)
        query.extend(
            [
                {"$unwind": "$annotations"},
                {"$unwind": "$annotations.labels"},
                {
                    "$match": {
                        "annotations.labels.label_id": {"$in": [IDToMongo.forward(label_id) for label_id in label_ids]},
                        "$or": [
                            {"annotations.shape.is_visible": {"$exists": False}},
                            {"annotations.shape.is_visible": True},
                        ],
                    }
                },
                {
                    "$group": {
                        "_id": "$annotations.labels.label_id",
                        "shape_count": {"$sum": 1},
                        "unique_annotation_scenes": {"$addToSet": "._id"},
                    }
                },
                {
                    "$project": {
                        "shape_count": "$shape_count",
                        "annotation_scenes_count": {"$size": "$unique_annotation_scenes"},
                    }
                },
            ]
        )
        docs = self.aggregate_read(query)
        count_shape_level = {}
        count_annotation_scene_level = {}
        for doc in docs:
            label_id = ID(doc["_id"])
            count_shape_level[label_id] = doc["shape_count"]
            count_annotation_scene_level[label_id] = doc["annotation_scenes_count"]
        return count_annotation_scene_level, count_shape_level

    def get_annotation_count_and_object_sizes(
        self, label_ids: Sequence[ID], max_object_sizes_per_label: int
    ) -> tuple[dict[ID, tuple[tuple[int, int], ...]], dict, dict]:
        """
        This functions creates an aggregate which splits into two stages.

        1. Returns and computes the latest annotations objects sizes with the specified label_id.
        Object sizes is computed as follows:
            - for shape if type "RECTANGLE" and "ELLIPSE":
                (shape.x2 - shape.x1, shape.y2 - shape.y2)
            - for "KEYPOINT":
                (1, 1)
            - for other types of shapes (i.e. POLYGON):
                (max(shape.points.x) - min(shape.points.x), max(shape.points.y) - min(shape.points.y)

        2. Counts the number of occurrences for each label_id, at annotation and shape level.
        Only considers the latest user annotations, i.e. of kind `ANNOTATION`.
        Returns two dictionaries:
            2.1. per annotation: a dict with label id -> set(annotation_ids)
            2.2. per shape: a dict with label id -> int of occurrence.

        :param label_ids: sequence of label IDs for filtering annotations
        :return:
        :param label_ids: list of label IDs that the annotations must match
        :param max_object_sizes_per_label: limit the object sizes returned per label
        :return: Returns a tuple containing 3 dictionaries.
            1. dictionary with label ID as key and annotation object sizes, with format (width, height), as value
            2. dictionary with annotation scene count per label id
            3. dictionary with shape count per label id
        """
        query = self._get_query_latest(annotation_kind=AnnotationSceneKind.ANNOTATION)
        query.extend(
            [
                {"$unwind": "$annotations"},
                {"$unwind": "$annotations.labels"},
                {
                    "$match": {
                        "annotations.labels.label_id": {"$in": [IDToMongo.forward(label_id) for label_id in label_ids]},
                        "$or": [
                            {"annotations.shape.is_visible": {"$exists": False}},
                            {"annotations.shape.is_visible": True},
                        ],
                    }
                },
                {
                    "$project": {
                        "annotations": 1,
                        "media_width": 1,
                        "media_height": 1,
                    },
                },
                {
                    "$addFields": {
                        "annotations.media_height": "$media_height",
                        "annotations.media_width": "$media_width",
                    },
                },
                {
                    "$group": {
                        "_id": "$annotations.labels.label_id",
                        "shape_count": {"$sum": 1},
                        "unique_annotation_scenes": {"$addToSet": "._id"},
                        "annotations": {
                            "$firstN": {
                                "input": "$annotations",
                                "n": max_object_sizes_per_label,
                            }
                        },
                    }
                },
                {
                    "$project": {
                        "shape_count": "$shape_count",
                        "annotation_scenes_count": {"$size": "$unique_annotation_scenes"},
                        "label_id": "$_id",
                        "width_sizes": {
                            "$map": {
                                "input": "$annotations",
                                "in": {
                                    "$toInt": {
                                        "$cond": [
                                            {
                                                "$or": [
                                                    {
                                                        "$eq": [
                                                            "$$this.shape.type",
                                                            "RECTANGLE",
                                                        ],
                                                    },
                                                    {
                                                        "$eq": [
                                                            "$$this.shape.type",
                                                            "ELLIPSE",
                                                        ],
                                                    },
                                                ],
                                            },
                                            {
                                                "$multiply": [
                                                    {
                                                        "$subtract": [
                                                            "$$this.shape.x2",
                                                            "$$this.shape.x1",
                                                        ],
                                                    },
                                                    "$$this.media_width",
                                                ],
                                            },
                                            {
                                                "$cond": [
                                                    {
                                                        "$eq": [
                                                            "$$this.shape.type",
                                                            "KEYPOINT",
                                                        ],
                                                    },
                                                    1,
                                                    {
                                                        "$multiply": [
                                                            {
                                                                "$subtract": [
                                                                    {
                                                                        "$max": "$$this.shape.points.x",
                                                                    },
                                                                    {
                                                                        "$min": "$$this.shape.points.x",
                                                                    },
                                                                ],
                                                            },
                                                            "$$this.media_width",
                                                        ],
                                                    },
                                                ],
                                            },
                                        ],
                                    },
                                },
                            },
                        },
                        "height_sizes": {
                            "$map": {
                                "input": "$annotations",
                                "in": {
                                    "$toInt": {
                                        "$cond": [
                                            {
                                                "$or": [
                                                    {
                                                        "$eq": [
                                                            "$$this.shape.type",
                                                            "RECTANGLE",
                                                        ],
                                                    },
                                                    {
                                                        "$eq": [
                                                            "$$this.shape.type",
                                                            "ELLIPSE",
                                                        ],
                                                    },
                                                ],
                                            },
                                            {
                                                "$multiply": [
                                                    {
                                                        "$subtract": [
                                                            "$$this.shape.y2",
                                                            "$$this.shape.y1",
                                                        ],
                                                    },
                                                    "$$this.media_height",
                                                ],
                                            },
                                            {
                                                "$cond": [
                                                    {
                                                        "$eq": [
                                                            "$$this.shape.type",
                                                            "KEYPOINT",
                                                        ],
                                                    },
                                                    1,
                                                    {
                                                        "$multiply": [
                                                            {
                                                                "$subtract": [
                                                                    {
                                                                        "$max": "$$this.shape.points.y",
                                                                    },
                                                                    {
                                                                        "$min": "$$this.shape.points.y",
                                                                    },
                                                                ],
                                                            },
                                                            "$$this.media_height",
                                                        ],
                                                    },
                                                ],
                                            },
                                        ],
                                    },
                                },
                            }
                        },
                    }
                },
            ]
        )
        docs = self.aggregate_read(query)

        annotation_object_sizes = {}
        count_shape_level = {}
        count_annotation_scene_level = {}
        for doc in docs:
            label_id = ID(doc["_id"])
            count_shape_level[label_id] = doc["shape_count"]
            count_annotation_scene_level[label_id] = doc["annotation_scenes_count"]
            annotation_object_sizes[label_id] = tuple(zip(doc["width_sizes"], doc["height_sizes"]))
        return annotation_object_sizes, count_annotation_scene_level, count_shape_level

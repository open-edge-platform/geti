# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements convert utilities
"""

import logging
import os.path as osp
import random
from collections import defaultdict
from collections.abc import Callable, Sequence
from typing import Any, NamedTuple, cast

import datumaro as dm
import numpy as np
from datumaro.components.annotation import NO_GROUP
from datumaro.components.transformer import ItemTransform
from datumaro.util import take_by
from geti_types import ID, MediaIdentifierEntity
from iai_core.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core.entities.label import Domain, Label, NullLabel
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.media import ImageExtensions, MediaPreprocessing, MediaPreprocessingStatus, VideoExtensions
from iai_core.entities.scored_label import LabelSource, ScoredLabel
from iai_core.entities.shapes import Ellipse, Keypoint, Point, Polygon, Rectangle
from iai_core.entities.video import Video
from iai_core.repos import AnnotationSceneRepo, BinaryRepo, VideoRepo
from media_utils import VideoDecoder

from jobs_common_extras.datumaro_conversion.definitions import SUPPORTED_DOMAIN_TO_ANNOTATION_TYPES, GetiProjectType
from jobs_common_extras.datumaro_conversion.import_utils import ImportUtils

logger = logging.getLogger(__name__)


class MediaInfo(NamedTuple):
    identifier: MediaIdentifierEntity
    height: int
    width: int


class ConvertUtils:
    class ShapeMapper:
        """
        Convert Datumaro shape annotations to SC annotation.
        dm.Label will not be covered in this class and it should be handled separately.

        :param media_w: width of the media
        :param media_h: height of the media
        :param label_source: label source
        :param get_sc_label: method to get sc label from datumaro label
        """

        def __init__(
            self,
            media_w: int,
            media_h: int,
            label_source: LabelSource,
            get_sc_label: Callable[[int | str], Label],
        ):
            if media_w <= 0 or media_h <= 0:
                raise ValueError("media_w and media_h should be positive")

            self._w = media_w
            self._h = media_h
            self._label_source = label_source
            self._get_sc_label = get_sc_label

        def convert(self, dm_ann: dm.Annotation) -> list[Annotation]:
            if isinstance(dm_ann, dm.Bbox):
                return self._convert_bbox(dm_ann)
            if isinstance(dm_ann, dm.Polygon):
                return self._convert_polygon(dm_ann)
            if isinstance(dm_ann, dm.Ellipse):
                return self._convert_ellipse(dm_ann)
            if isinstance(dm_ann, dm.Points):
                return self._convert_points(dm_ann)
            if not isinstance(dm_ann, dm.Label):
                logger.warning("Unsupported annotation type: %s", dm_ann.type.name)
            return []

        def _get_scored_label(self, dm_label: int | str) -> ScoredLabel | None:
            sc_label: Label = self._get_sc_label(dm_label)
            if isinstance(sc_label, NullLabel):
                return None
            return ScoredLabel(
                label_id=sc_label.id_,
                is_empty=sc_label.is_empty,
                probability=1,
                label_source=self._label_source,
            )

        def _convert_bbox(self, dm_ann: dm.Bbox) -> list[Annotation]:
            scored_label = self._get_scored_label(dm_ann.label)
            if scored_label is None:
                return []
            sc_labels = [scored_label]

            # For chained_tasks such as Detection > Classification, Detection > Segmentation,
            # sc_label of each item had been exported like
            # dm.Bbox{
            #   label=0,
            #   attributes={"apple": True},
            # }
            # where dm.Bbox.label is dm_label_id of Detection, and attributes indicate classification label
            # We should re-construct secondary labels
            for attr_key, attr_value in dm_ann.attributes.items():
                if not isinstance(attr_value, bool) or not attr_value:
                    continue
                scored_label = self._get_scored_label(attr_key)
                if scored_label:
                    sc_labels.append(scored_label)

            return [
                Annotation(
                    Rectangle(
                        dm_ann.points[0] / self._w,
                        dm_ann.points[1] / self._h,
                        dm_ann.points[2] / self._w,
                        dm_ann.points[3] / self._h,
                    ),
                    labels=sc_labels,
                )
            ]

        def _convert_polygon(self, dm_ann: dm.Polygon) -> list[Annotation]:
            scored_label = self._get_scored_label(dm_ann.label)
            if scored_label is None:
                return []

            return [
                Annotation(
                    Polygon([Point(x / self._w, y / self._h) for x, y in take_by(dm_ann.points, 2)]),
                    labels=[scored_label],
                )
            ]

        def _convert_ellipse(self, dm_ann: dm.Ellipse) -> list[Annotation]:
            scored_label = self._get_scored_label(dm_ann.label)
            if scored_label is None:
                return []

            return [
                Annotation(
                    Ellipse(
                        dm_ann.x1 / self._w,
                        dm_ann.y1 / self._h,
                        dm_ann.x2 / self._w,
                        dm_ann.y2 / self._h,
                    ),
                    labels=[scored_label],
                )
            ]

        def _convert_points(self, dm_ann: dm.Points) -> list[Annotation]:
            sc_anns = []
            points = dm_ann.get_points()
            for idx in range(len(points)):
                scored_label = self._get_scored_label(idx)
                if scored_label is None:
                    continue
                try:
                    visibility = dm_ann.visibility[idx]
                except (TypeError, IndexError):
                    visibility = dm.Points.Visibility.absent
                if visibility == dm.Points.Visibility.absent:
                    continue  # we'll not generate a AnnotationScene when the visibility is absent
                sc_anns.append(
                    Annotation(
                        Keypoint(
                            x=points[idx][0] / self._w,
                            y=points[idx][1] / self._h,
                            is_visible=visibility == dm.Points.Visibility.visible,
                        ),
                        labels=[scored_label],
                    )
                )
            return sc_anns

    class FilterEmptyLabels(ItemTransform):
        def __init__(self, extractor: dm.IDataset, empty_labels: list[int]):
            super().__init__(extractor)
            self._empty_labels = empty_labels

        def transform_item(self, item: dm.DatasetItem) -> dm.DatasetItem | None:
            # we don't need to consider chained project
            # because import to existing chained project isn't supported.
            # So, single-task is assumed.
            anns_with_valid_labels = [ann for ann in item.annotations if ann.label not in self._empty_labels]
            if len(anns_with_valid_labels) < len(item.annotations):
                item.attributes["has_empty_label"] = len(anns_with_valid_labels) == 0
                return self.wrap_item(item, annotations=anns_with_valid_labels, attributes=item.attributes)
            return item

    @staticmethod
    def filter_dataset(dm_dataset: dm.Dataset, domain: Domain | None, labels: list[str] | None) -> None:
        """
        Filter out unused labels from dataset and keep only annotations with type compatible
        with chosen domain

        :param dm_dataset: datumaro dataset to filter
        :param domain: SC domain
        :param labels: list of label names of the labels to keep
        """
        if labels:
            dm_dataset.transform("project_labels", dst_labels=labels)

        if domain is None:
            return

        filter_str = " or ".join(f"type='{ann_type.name}'" for ann_type in SUPPORTED_DOMAIN_TO_ANNOTATION_TYPES[domain])

        dm_dataset.filter(
            f"/item/annotation[{filter_str}]",
            filter_annotations=True,
            remove_empty=False,
        )

    @staticmethod
    def filter_empty_label(dm_dataset: dm.Dataset, labels_map: dict[str, Label]) -> None:
        """
        Filter out annotations if there's a mapping to the empty label.

        :param dm_dataset: datumaro dataset to filter
        :param labels_map: mapping from dm label names to sc label
        :return: None
        """
        label_cat: dm.LabelCategories = dm_dataset.categories()[dm.AnnotationType.label]
        empty_labels = []
        for label_name, sc_label in labels_map.items():
            if sc_label.is_empty:
                label, _ = label_cat.find(label_name)
                if label is not None:
                    empty_labels.append(label)
        if empty_labels:
            dm_dataset.transform(ConvertUtils.FilterEmptyLabels, empty_labels=empty_labels)

    @staticmethod
    def check_all_label_names_in_dataset(dm_categories: dm.CategoriesInfo, dm_label_names: list[str]) -> bool:
        """
        Check if dm_label_names contains valid label_name for dm_dataset

        :param dm_categories: categories of datumaro dataset to filter
        :param dm_label_names: list of label names to be checked
        :return: True if all label_names are valid
        """
        label_cat: dm.LabelCategories = dm_categories[dm.AnnotationType.label]
        label_names_in_dm_dataset = {dm_label_item.name for dm_label_item in label_cat.items}

        return not any(label_name not in label_names_in_dm_dataset for label_name in dm_label_names)

    @classmethod
    def get_image_from_dm_item(cls, dm_item: dm.DatasetItem) -> tuple[np.ndarray, ImageExtensions]:
        """
        Convert Datumaro item to SC image.

        :param dm_item: Datumaro item to convert.
        :param get_image_name: Method mapping image name in Datumaro to image name in SC.
        :param uploader_id: ID of the user who uploaded.
        :return: The SC Image instance.
        """
        numpy = dm_item.media.data.astype(np.uint8)
        # Determine the image's file extension. This is required to ensure that the image
        # is imported in its original format to avoid any conversions, and hence preserving
        # the quality. If no extension is provided, or not part of ImageExtensions, we
        # set the default to ".jpg".
        try:
            file_extension = dm_item.media.ext
            image_extension = ImageExtensions[file_extension[1:].upper()]
        except KeyError:
            image_extension = ImageExtensions.JPG
        return numpy, image_extension

    @classmethod
    def get_video_from_dm_item(
        cls,
        dm_item: dm.DatasetItem,
        get_video_name: Callable,
        uploader_id: str,
        video_binary_repo: BinaryRepo,
    ) -> Video:
        """
        Convert Datumaro item to SC video.

        :param dm_item: Datumaro item to convert. Assume it's media type is Video or VideoFrame
        :param get_video_name: Method for mapping video name in Datumaro to video name in SC.
        :param uploader_id: ID of the user who uploaded.
        :param video_binary_repo: BinaryRepo to save video data.
        :return: The SC Video instance.
        """
        video_name = get_video_name(dm_item)
        base_name, extension = osp.splitext(video_name)
        try:
            video_extension = VideoExtensions[extension[1:].upper()]
        except KeyError:
            video_extension = VideoExtensions.MP4

        video_id = VideoRepo.generate_id()
        video_path = dm_item.media.path  # data source

        # save video to binary repo.
        binary_filename = video_binary_repo.save(
            dst_file_name=f"{str(video_id)}{video_extension.value}",
            data_source=video_path,
        )

        logger.info(
            "Saved bytes of video `%s` (file ID `%s`) in dataset storage `%s`",
            video_path,
            video_id,
            video_binary_repo.identifier.dataset_storage_id,  # type: ignore
        )
        try:
            logger.debug(f"Getting video information for video with ID {video_id} with name {binary_filename}.")
            info = VideoDecoder.get_video_information(str(video_path))
            logger.debug(f"Successfully fetched video information for video with ID {video_id}.")
        except RuntimeError:
            video_binary_repo.delete_by_filename(filename=binary_filename)
            raise

        return Video(
            name=base_name,
            id=video_id,
            uploader_id=uploader_id,
            fps=info.fps,
            width=info.width,
            height=info.height,
            total_frames=info.total_frames,
            size=video_binary_repo.get_object_size(binary_filename),
            extension=video_extension,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.SCHEDULED),
        )

    @classmethod
    def get_annotation_scene_from_dm_item(
        cls,
        dm_item: dm.DatasetItem,
        media_info: MediaInfo,
        get_sc_label: Callable[[int | str], Label],
        uploader_id: str,
        empty_labels: Sequence[Label] | None = None,
        sc_label_to_all_parents: dict[Label, list[Label]] | None = None,
        sc_label_to_group_id: dict[Label, ID] | None = None,
    ) -> AnnotationScene:
        """
        Convert annotations in Datumaro item to SC annotation scene.

        :param dm_item: Datumaro item to convert.
        :param media_info: Media information of SC image or video.
        :param get_sc_label: Method to get sc label from dm label.
        :param uploader_id: ID of the user who uploaded.
        :param empty_labels: A list of empty labels of the project.
        :param sc_label_to_all_parents: Optional. Dictionary of mapping sc_label to all ancestor labels.
        :param sc_label_to_group_id: Optional. Dictionary of mapping sc_label to group id.
        :return: The annotation scene generated from Datumaro item, if compatible
              annotations are present, otherwise null annotation scene
        """
        annotations = cls.convert_dm_anns(
            dm_item=dm_item,
            get_sc_label=get_sc_label,
            empty_labels=empty_labels,
            uploader_id=uploader_id,
            sc_label_to_all_parents=sc_label_to_all_parents,
            sc_label_to_group_id=sc_label_to_group_id,
        )
        return AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=media_info.identifier,
            media_height=media_info.height,
            media_width=media_info.width,
            id_=AnnotationSceneRepo.generate_id(),
            last_annotator_id=uploader_id,
            annotations=annotations,
        )

    @staticmethod
    def get_label_annotation(  # noqa: C901
        dm_anns: list[dm.Annotation],
        get_sc_label: Callable[[int | str], Label],
        uploader_id: str,
        sc_label_to_all_parents: dict[Label, list[Label]] | None = None,
        sc_label_to_group_id: dict[Label, ID] | None = None,
    ) -> Annotation | None:
        """
        Create sc Annotation of an item from dm.Label only.
        When an item has multi-label annotations, we change to single-label annotation if allow_multi_label is False

        :param dm_anns: List of datumaro annotations
        :param get_sc_label: method to get sc label from datumaro label
        :param uploader_id: ID of the user who uploaded
        :param sc_label_to_all_parents: Optional. dictionary of mapping sc_label to all ancestor labels
        :param sc_label_to_group_id: Optional. dictionary of mapping sc_label to group id
        :return: generated Annotation
        """
        # We interest in dm.Label annotation only
        dm_labels = []
        for dm_ann in dm_anns:
            if isinstance(dm_ann, dm.Label) and not isinstance(get_sc_label(dm_ann.label), NullLabel):
                dm_labels.append(dm_ann.label)

        if len(dm_labels) == 0:
            return None

        if sc_label_to_group_id is None:
            sc_label_to_group_id = {}

        sc_labels = set()
        sc_group_ids = set()
        # iterate through the dm_labels then
        # 1) includes all ancestor of sc_label
        # 2) check if following multi-label rule
        for dm_label in dm_labels:
            sc_label_for_dm_label = get_sc_label(dm_label)

            sc_labels_for_dm_label = [sc_label_for_dm_label]
            # for hierarchical structure, parents of label are auto-selected
            if sc_label_to_all_parents is not None:
                sc_labels_for_dm_label += sc_label_to_all_parents.get(sc_label_for_dm_label, [])

            # check multi-label error.
            # In the following example,
            # 1) '1 <- a' denotes 1 is parent of 'a'.
            # 2) '[1, 2]' denotes label '1' and '2' are grouped together.
            # e.g.) 1 <- a0, 1 <- a1, 2 <- b0, 2 <- b1, [1, 2], [a0, a1], [b0, b1]
            # if an item is annotated to 'a0' and 'b0',
            # it disobeys the multi-label rule after including ancestors of 'a0' and 'b0'
            # because '1' and '2' are grouped together.
            # In this case, we remove 'b0' and all ancestors of 'b0'
            multi_label_error = False
            for sc_label in sc_labels_for_dm_label:
                if sc_label not in sc_label_to_group_id:
                    continue
                # e.g.) 1 <- 10, 1 <- a1, 1 <- b0, 1 <- b1, [1, 2], [a0, a1], [b0, b1]
                # if an item is annotated to 'a0' and 'b0'
                # sc_labels should be ['1', 'a0', 'b0'] since it doesn't disobey the multi-label rule
                if sc_label in sc_labels:
                    continue
                group_id = sc_label_to_group_id[sc_label]
                if group_id in sc_group_ids:
                    multi_label_error = True
                    break
                sc_group_ids.add(group_id)

            if not multi_label_error:
                sc_labels.update(sc_labels_for_dm_label)

        label_source = LabelSource(user_id=uploader_id)
        return Annotation(
            Rectangle.generate_full_box(),
            labels=[
                ScoredLabel(
                    label_id=sc_label.id_,
                    is_empty=sc_label.is_empty,
                    probability=1,
                    label_source=label_source,
                )
                for sc_label in sc_labels
            ],
        )

    @staticmethod
    def convert_dm_anns(  # noqa: C901, PLR0912
        dm_item: dm.DatasetItem,
        get_sc_label: Callable[[int | str], Label],
        uploader_id: str,
        empty_labels: Sequence[Label] | None = None,
        sc_label_to_all_parents: dict[Label, list[Label]] | None = None,
        sc_label_to_group_id: dict[Label, ID] | None = None,
    ) -> list[Annotation]:
        """
        Convert dm annotations in datumaro item to sc annotations

        :param dm_item: datumaro item
        :param get_sc_label: method to get sc label from datumaro label
        :param uploader_id: ID of the user who uploaded
        :param empty_labels: a list of empty labels of the project
        :param sc_label_to_all_parents: Optional. dictionary of mapping sc_label to all ancestor labels
        :param sc_label_to_group_id: Optional. dictionary of mapping sc_label to group id
        :return: list of sc annotations
        """

        sc_anns = []
        empty_annotation: Annotation | None
        label_source = LabelSource(user_id=uploader_id)
        if empty_labels is not None and len(empty_labels) > 0:
            empty_annotation = Annotation(
                Rectangle.generate_full_box(),
                labels=[
                    ScoredLabel(
                        label_id=empty_labels[0].id_,
                        is_empty=True,
                        probability=1,
                        label_source=label_source,
                    )
                ],
            )
        else:
            empty_annotation = None

        # 'group' of Datumaro annotations
        # some data-format, e.g. COCO, allows multiple annotation formats for an annotation.
        # e.g.) an annotation for an item may have both bbox and polygon formats labeling the same target.
        # In this case, Datumaro groups them by the 'group' attribute.
        # This means that len(dm_anns_group_by) is equal to # of annotation for dm_item
        dm_anns_group_by = defaultdict(list)
        for dm_ann in dm_item.annotations:
            dm_anns_group_by[dm_ann.group].append(dm_ann)

        dm_anns = []
        for group, dm_annotations in dm_anns_group_by.items():
            # all annotations with 'group == NO_GROUP' annotates the independent labeling object.
            if group == NO_GROUP:
                dm_anns += dm_annotations
                continue
            # Since Geti doesn't have 'group' like concept,
            # we filter-out bbox annotation
            # if both bbox and polygon annotation types grouped together.
            bbox_anns = []
            has_polygon = False
            for dm_ann in dm_annotations:
                if isinstance(dm_ann, dm.Polygon):
                    has_polygon = True
                elif isinstance(dm_ann, dm.Bbox):
                    bbox_anns.append(dm_ann)
            if has_polygon and len(bbox_anns) > 0:
                for bbox_ann in bbox_anns:
                    dm_annotations.remove(bbox_ann)
            dm_anns += dm_annotations

        # Multi-label is only allowed in classification task now,
        # thus, we change multi-label item to single-label by selecting lowest label
        sc_label_ann = ConvertUtils.get_label_annotation(
            dm_anns=dm_anns,
            get_sc_label=get_sc_label,
            uploader_id=uploader_id,
            sc_label_to_all_parents=sc_label_to_all_parents,
            sc_label_to_group_id=sc_label_to_group_id,
        )
        if sc_label_ann is not None:
            sc_anns.append(sc_label_ann)

        try:
            h, w = dm_item.media.size
            converter = ConvertUtils.ShapeMapper(
                media_w=w,
                media_h=h,
                label_source=label_source,
                get_sc_label=get_sc_label,
            )
            for dm_ann in dm_anns:
                sc_anns.extend(converter.convert(dm_ann))
        except TypeError:
            logger.warning(
                f"Invalid media for a dm_item(id='{dm_item.id}', subset='{dm_item.subset}')"
                " in the dataset. Skipping the item."
            )
        except ValueError:
            logger.warning(
                f"Invalid media size: {dm_item.media.size} for a dm_item(id='{dm_item.id}', subset='{dm_item.subset}')"
                " in the dataset. Skipping the item."
            )

        empty_attr_key = "has_empty_label"
        if empty_annotation is not None and dm_item.attributes.get(empty_attr_key, False):
            sc_anns.append(empty_annotation)

        return sc_anns

    @staticmethod
    def map_image_names(has_single_subset: bool) -> Callable:
        """
        Return a method getting sc image name from datumaro item in dataset.

        :param has_single_subset: Whether the dataset has a single subset or not.
        :return: Method returning sc image name for datumaro item in given dataset.
        """
        ids = set()

        def _get_image_name(item: dm.DatasetItem):
            return f"{item.id}"

        def _get_image_name_with_subset(item: dm.DatasetItem):
            if item.id in ids:
                return f"{item.id}_{item.subset}"
            ids.add(item.id)
            return f"{item.id}"

        return _get_image_name if has_single_subset else _get_image_name_with_subset

    @staticmethod
    def map_video_names(has_single_subset: bool) -> Callable:
        """
        Return a method getting sc video name from datumaro item in dataset.

        The name of a Video is determined by its path, not by the (id, subset).
        This is because while the (id, subset) differentiates VideoFrames,
        a Video can be shared across multiple VideoFrames.

        :param has_single_subset: Whether the dataset has a single subset or not.
        :return: method returning sc video name for datumaro item in given dataset.
        """

        def _get_video_name(item: dm.DatasetItem):
            return osp.basename(item.media.path)

        def _get_video_name_with_subset(item: dm.DatasetItem):
            basename = osp.basename(item.media.path)
            return osp.join(item.subset, basename) if item.subset else basename

        return _get_video_name if has_single_subset else _get_video_name_with_subset

    @staticmethod
    def get_dm_label_mapper(
        dm_categories: dm.Categories,
        domain: Domain,
    ) -> dict[int, str]:
        dm_label_mapper: dict[int, str] = {}
        if domain == Domain.KEYPOINT_DETECTION:
            # create point_labels.
            try:
                # We assume that the point category should exist for the keypoint detection domain and
                # it has a corresponding label category with label=0.
                point_cat: dm.PointsCategories = dm_categories[dm.AnnotationType.points]
                for idx, label in enumerate(point_cat.items[0].labels):
                    dm_label_mapper[idx] = label
            except KeyError:
                logger.error("Point category is not found in the dataset.")
        else:
            try:
                label_cat: dm.LabelCategories = dm_categories[dm.AnnotationType.label]
                for idx, cat in enumerate(label_cat):
                    dm_label_mapper[idx] = cat.name
            except KeyError:
                logger.error("Label category is not found in the dataset.")

        return dm_label_mapper

    @staticmethod
    def get_labels_mapper_from_dataset(
        dm_categories: dm.CategoriesInfo,
        dm_infos: dict[str, Any],
        sc_labels: list[Label],
        domain: Domain,
    ) -> Callable[[int | str], Label]:
        """
        Map datumaro label ids to sc labels and return method getting sc label for
        datumaro label id.

        :param dm_categories: Categories of datumaro dataset to map.
        :param dm_infos: Infos of datumaro dataset to map.
        :param sc_labels: SC labels.
        :param domain: Label domain. We should provide special mapping for anomaly labels.
        :return: Method that return sc label corresponding to datumaro label id.
        """
        dm_label_mapper = ConvertUtils.get_dm_label_mapper(dm_categories, domain)
        sc_label_mapper: dict[str, Label] = {}
        if domain in [
            Domain.ANOMALY_CLASSIFICATION,
            Domain.ANOMALY_DETECTION,
            Domain.ANOMALY_SEGMENTATION,
        ]:
            # create sc_label_map by label attribute, is_anomalous
            sc_anomaly_label: Label = NullLabel()
            sc_normal_label: Label = NullLabel()

            # For anomaly task, sc_labels should have one anomaly and one normal label
            for sc_label in sc_labels:
                if sc_label.is_anomalous:
                    sc_anomaly_label = sc_label
                else:
                    sc_normal_label = sc_label

            anomaly_label_names = dm_infos.get("GetiAnomalyLabels", [])
            try:
                label_cat: dm.LabelCategories = dm_categories[dm.AnnotationType.label]
                for cat in label_cat:
                    sc_label_mapper[cat.name] = sc_anomaly_label if cat.name in anomaly_label_names else sc_normal_label
            except KeyError:
                logger.error("Label category is not found in the dataset.")
        else:
            # create sc_label_map by label_name
            for label in sc_labels:
                sc_label_mapper[label.name] = label

        def _get_sc_label(dm_label_id: int | str) -> Label:
            try:
                dm_label_name = dm_label_mapper[dm_label_id] if isinstance(dm_label_id, int) else dm_label_id
                return sc_label_mapper[dm_label_name]
            except KeyError:
                return NullLabel()

        return _get_sc_label

    @staticmethod
    def get_labels_mapper_from_labels_map(dm_categories: dm.CategoriesInfo, labels_map: dict[str, Label]) -> Callable:
        """
        :param dm_categories: categories of datumaro dataset to map
        :param labels_map: map of datumaro label names to sc labels
        :return: method mapping dm label id to sc label
        """
        dm_labels: dm.LabelCategories = dm_categories[dm.AnnotationType.label]
        dm_points: dm.PointsCategories | None = dm_categories.get(dm.AnnotationType.points, None)

        def _get_sc_label(dm_label_id: int | str) -> Label | None:
            try:
                if dm_points:
                    dm_label_name = dm_points.items[0].labels[dm_label_id]
                else:
                    dm_label_name = dm_labels[dm_label_id].name if isinstance(dm_label_id, int) else dm_label_id
                return labels_map[dm_label_name]
            except KeyError:
                return NullLabel()

        return _get_sc_label

    @staticmethod
    def get_sc_label_to_group_id(label_schema: LabelSchema) -> dict[Label, ID]:
        """
        Mapping of sc_label to group id

        :param label_schema: label_schema of target sc project
        :return: mapping of sc_label to all ancestor labels
        """
        sc_label_to_group_id = {}
        for label_group in label_schema.get_groups(include_empty=False):
            for sc_label in label_group.labels:
                sc_label_to_group_id[cast("Label", sc_label)] = label_group.id_
        return sc_label_to_group_id

    @staticmethod
    def get_sc_label_to_all_parents(sc_labels: list[Label], label_schema: LabelSchema) -> dict[Label, list[Label]]:
        """
        Mapping of sc_label to all ancestor labels

        :param sc_labels: list of sc_label
        :param label_schema: label_schema of target sc project
        :return: mapping of sc_label to all ancestor labels
        """
        sc_label_to_all_parents = defaultdict(list)
        for sc_label in sc_labels:
            sc_parent = sc_label
            while True:
                sc_parent = cast("Label", label_schema.label_tree.get_parent(sc_parent))
                if sc_parent is None:
                    break
                sc_label_to_all_parents[sc_label].append(sc_parent)
        return sc_label_to_all_parents

    @staticmethod
    def build_labels_data(label_names: list[str], anomaly_label_names: list[str] | None = None) -> list[dict[str, Any]]:
        """
        Generate meta-data (color, is_anomalous) for Labels.

        :param label_names: List of label names
        :param anomaly_label_names: List of label names that are anomalous
        :return: List of dictional that contains label meta-data
        """
        if anomaly_label_names is None:
            anomaly_label_names = []

        label_datas = []
        for label_name in label_names:
            label_data: dict[str, Any] = {
                "name": label_name,
                "color": "#00" + "".join([random.choice("0123456789ABCDEF") for j in range(6)]),  # noqa: S311
            }
            label_datas.append(label_data)

        if anomaly_label_names:
            for label_data in label_datas:
                label_data["is_anomalous"] = bool(label_data["name"] in anomaly_label_names)

        return label_datas

    @staticmethod
    def get_label_metadata(  # noqa: C901, PLR0912
        dm_categories: dm.CategoriesInfo,
        dm_infos: dict[str, Any],
        selected_labels: Sequence[str],
        project_type: GetiProjectType,
        include_all_labels: bool = False,
    ) -> tuple[list[dict[str, Any]] | None, dict[str, str] | None, list[dict[str, Any]]]:
        """
        :param dm_categories: categories of datumaro dataset
        :param dm_infos: infos of datumaro dataset
        :param selected_labels: labels selected by a user for being imported
        :param project_type: Geti project type
        :param include_all_labels: if True, ignore selected_labels then include all possible labels for each task_type
        :return: label_groups metadata, hierarchical labeling tree, list of label names
        """
        # Collect the label names from the categories()
        # that are utilized to construct a hierarchical labeling structure or LabelGroup
        label_groups: list[dict[str, Any]] = []
        labelname_to_parent: dict[str, str] = {}

        label_cat: dm.LabelCategories = dm_categories[dm.AnnotationType.label]
        label_mask: dm.MaskCategories = dm_categories.get(dm.AnnotationType.mask, {})

        # colormap from dm_dataset
        dm_label_id_to_name: dict[int, str] = {
            label_id: cate_item.name for label_id, cate_item in enumerate(label_cat.items)
        }
        dm_label_name_to_color: dict[str, str] = {}
        if hasattr(label_mask, "colormap"):
            for label_id, dm_colormap in label_mask.colormap.items():
                if label_id not in dm_label_id_to_name:
                    continue
                label_name = dm_label_id_to_name[label_id]

                colormap = "#"
                for color_int in dm_colormap:
                    colormap += f"{color_int:02x}"

                dm_label_name_to_color[label_name] = colormap

        exported_project_type = ImportUtils.get_exported_project_type(dm_infos)
        logger.warning(f"{exported_project_type}, {project_type}")
        if project_type != exported_project_type:
            labels = [{"name": label_name} for label_name in selected_labels]
            for label_meta in labels:
                label_name = label_meta["name"]
                if label_name in dm_label_name_to_color:
                    label_meta["color"] = dm_label_name_to_color[label_name]
            return None, None, labels

        # trace label_names needed to be included into the target project
        label_names_to_include: set[str] = set(selected_labels)

        # find the hierarchical structure
        for cat_item in label_cat.items:
            if len(cat_item.parent) == 0:
                continue
            if cat_item.name != cat_item.parent:
                labelname_to_parent[cat_item.name] = cat_item.parent

        # all ancestor labels have to alive if any child is alive
        label_names_for_hierarchical_structure: set[str] = set()
        for label_name in labelname_to_parent:
            if not include_all_labels and label_name not in label_names_to_include:
                continue

            parent_name = label_name
            while len(parent_name) > 0:
                label_names_for_hierarchical_structure.add(parent_name)
                parent_name = labelname_to_parent.get(parent_name, "")
        label_names_to_include.update(label_names_for_hierarchical_structure)

        # extract a label group meta-data
        dm_label_groups: list[dm.LabelCategories.LabelGroup] = label_cat.label_groups

        for dm_label_group in dm_label_groups:
            group_labels = [
                label_name
                for label_name in dm_label_group.labels
                if (include_all_labels or label_name in label_names_to_include)
            ]

            if len(group_labels) == 0:
                continue

            label_groups.append(
                {
                    "name": dm_label_group.name,
                    "labels": group_labels,
                    "group_type": dm_label_group.group_type,
                }
            )

        anomaly_label_names = dm_infos.get("GetiAnomalyLabels", [])
        labels = ConvertUtils.build_labels_data(
            label_names=list(label_names_to_include),
            anomaly_label_names=anomaly_label_names,
        )
        # preserve the previous color
        for label in labels:
            if label["name"] in dm_label_name_to_color:
                label["color"] = dm_label_name_to_color[label["name"]]

        return label_groups, labelname_to_parent, labels

    @staticmethod
    def get_keypoint_structure(
        dm_categories: dm.CategoriesInfo,
        selected_labels: Sequence[str],
        include_all_labels: bool = False,
    ) -> dict[str, list]:
        """
        Get the keypoint structure(a.k.a. skeleton or keypoint graph, and positions) from datumaro dataset.

        :param dm_categories: categories of datumaro dataset
        :param selected_labels: labels selected by a user for being imported
        :param include_all_labels: if True, ignore selected_labels then include all possible labels for each task_type
        :return: the keypoint structure
        """
        structure: dict[str, list] = {
            "edges": [],
            "positions": [],
        }
        point_cat: dm.PointsCategories = dm_categories.get(dm.AnnotationType.points, None)
        logger.warning(f"{point_cat}")
        if point_cat:
            for cat in point_cat.items.values():
                logger.warning(f"{cat}")
                idx_to_label_name = {idx + 1: label for idx, label in enumerate(cat.labels)}
                logger.warning(f"{idx_to_label_name}")
                for joint in cat.joints:
                    logger.warning(f"{joint}")
                    if len(joint) != 2:
                        logger.warning(f"Skip invalid joint: {joint}")
                        continue
                    joint_names = tuple(idx_to_label_name[idx] for idx in joint)
                    logger.warning(f"{joint_names}")
                    if not include_all_labels and not any(label in selected_labels for label in joint_names):
                        continue
                    structure["edges"].append({"nodes": list(joint_names)})
                for i in range(0, len(cat.positions), 2):
                    logger.warning(f"{cat.positions[i]}, {cat.positions[i + 1]}")
                    structure["positions"].append(
                        {"label": cat.labels[i // 2], "x": cat.positions[i], "y": cat.positions[i + 1]}
                    )

        return structure

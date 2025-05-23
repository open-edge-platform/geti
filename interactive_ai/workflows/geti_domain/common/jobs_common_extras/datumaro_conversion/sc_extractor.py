# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module implements conversion from Geti Dataset to Datumaro dataset."""

import logging
import os
import shutil
from collections import defaultdict
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from itertools import chain
from multiprocessing.pool import AsyncResult, ThreadPool
from typing import TYPE_CHECKING, Any, NamedTuple, cast

import cv2
from datumaro import Annotation as dm_Annotation
from datumaro import AnnotationType as dm_AnnotationType
from datumaro import Bbox as dm_Bbox
from datumaro import CategoriesInfo as dm_CategoriesInfo
from datumaro import DatasetBase as dm_DatasetBase
from datumaro import DatasetItem as dm_DatasetItem
from datumaro import Ellipse as dm_Ellipse
from datumaro import Image as dm_Image
from datumaro import Label as dm_Label
from datumaro import LabelCategories as dm_LabelCategories
from datumaro import MaskCategories as dm_MaskCategories
from datumaro import Points as dm_Points
from datumaro import PointsCategories as dm_PointCategories
from datumaro import Polygon as dm_Polygon
from datumaro import Video as dm_Video
from datumaro import VideoFrame as dm_VideoFrame
from datumaro.components.annotation import GroupType as DmGroupType
from datumaro.components.dataset_base import DEFAULT_SUBSET_NAME
from geti_types import (
    ID,
    DatasetStorageIdentifier,
    ImageIdentifier,
    ProjectIdentifier,
    VideoFrameIdentifier,
    VideoIdentifier,
)
from iai_core.entities.annotation import Annotation, AnnotationSceneKind
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.datasets import Dataset, NullDataset
from iai_core.entities.image import Image
from iai_core.entities.keypoint_structure import KeypointStructure
from iai_core.entities.label import Domain
from iai_core.entities.label_schema import LabelGroupType, LabelSchema
from iai_core.entities.shapes import Ellipse, Keypoint, Polygon, Rectangle
from iai_core.entities.subset import Subset
from iai_core.entities.video import Video, VideoFrame
from iai_core.repos import (
    AnnotationSceneRepo,
    DatasetRepo,
    ImageRepo,
    LabelRepo,
    ProjectRepo,
    VideoAnnotationRangeRepo,
    VideoRepo,
)

from jobs_common_extras.datumaro_conversion.mappers.annotation_scene_mapper import AnnotationSceneMapper, LabelMap
from jobs_common_extras.datumaro_conversion.mappers.dataset_item_mapper import DatasetItemMapper
from jobs_common_extras.datumaro_conversion.mappers.id_mapper import IDMapper, MediaNameIDMapper, VideoNameIDMapper
from jobs_common_extras.datumaro_conversion.mappers.label_mapper import LabelSchemaMapper

__all__ = ["ScExtractor", "ScExtractorForFlyteJob", "ScExtractorFromDatasetStorage"]

from geti_types import CTX_SESSION_VAR, Session, session_context
from iai_core.repos.storage.binary_repos import VideoBinaryRepo
from media_utils import get_image_bytes, get_media_numpy, get_video_bytes

if TYPE_CHECKING:
    from iai_core.entities.video_annotation_range import RangeLabels, VideoAnnotationRange

logger = logging.getLogger(__name__)


class ScExtractor(dm_DatasetBase):
    """
    Represents the Geti dataset as a lazy dataset for Datumaro.
    """

    VERSION = "1.0"

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        sc_dataset_or_list_of_sc_items: Dataset | list[DatasetItem],
        label_schema: LabelSchema,
        use_subset: bool = False,
    ) -> None:
        if isinstance(sc_dataset_or_list_of_sc_items, Dataset):
            self._dataset = sc_dataset_or_list_of_sc_items
        elif isinstance(sc_dataset_or_list_of_sc_items, list):
            self._dataset = Dataset(id=ID(), items=sc_dataset_or_list_of_sc_items)
        else:
            raise TypeError("Input type should be Dataset or Sequence[DatasetItem]")

        self._dataset_storage_identifier = dataset_storage_identifier
        self._video_binary_repo = VideoBinaryRepo(dataset_storage_identifier)

        # We need all labels to be mapped
        project_identifier = ProjectIdentifier(
            workspace_id=dataset_storage_identifier.workspace_id,
            project_id=dataset_storage_identifier.project_id,
        )
        project = ProjectRepo().get_by_id(dataset_storage_identifier.project_id)
        label_repo = LabelRepo(project_identifier=project_identifier)
        self._label_id_to_label = {label.id_: label for label in label_repo.get_all()}

        sc_labels = label_schema.get_labels(include_empty=True)
        sc_non_empty_labels = label_schema.get_labels(include_empty=False)
        self._label_id_to_idx = {label.id_: i for i, label in enumerate(sc_non_empty_labels)}
        self._label_name_to_label = {label.name: label for label in sc_labels}
        super().__init__()

        self._infos: dict[str, Any] = {}
        self._init_infos()

        self._categories: dm_CategoriesInfo = {}
        self._init_categories(
            sc_dataset=self._dataset, label_schema=label_schema, keypoint_structure=project.keypoint_structure
        )
        self._use_subset = use_subset
        self._set_name_mapper()

    def _set_name_mapper(self):
        self._name_mapper = MediaNameIDMapper()
        self._video_mapper = VideoNameIDMapper()

    def _init_infos(self) -> None:
        """
        Initialize infos field of dm_dataset.

        We mark ScExtractor version into infos() field to support backward compatibility in the future
        """
        self._infos = {"ScExtractorVersion": ScExtractor.VERSION}

    def _init_categories(
        self,
        sc_dataset: Dataset,  # noqa: ARG002
        label_schema: LabelSchema,
        keypoint_structure: KeypointStructure | None,
    ) -> None:
        label_cat = dm_LabelCategories()
        mask_cat = dm_MaskCategories()
        point_cat = dm_PointCategories()
        geti_labels = label_schema.get_labels(include_empty=False)

        # Collect label names that are necessary to be exported
        valid_labelnames: set[str] = set()
        valid_labelnames.update([sc_label.name for sc_label in geti_labels])

        for i, sc_label in enumerate(geti_labels):
            if label_schema is not None:
                sc_parent = label_schema.label_tree.get_parent(sc_label)
                if sc_parent is not None:
                    # A parent is also necessary when child is necessary
                    valid_labelnames.add(sc_parent.name)
                    label_cat.add(sc_label.name, parent=sc_parent.name)
                else:
                    label_cat.add(sc_label.name)
            else:
                label_cat.add(sc_label.name)
            mask_cat.colormap[i] = sc_label.color.rgb_tuple

        if keypoint_structure:
            joints = []
            for edge in keypoint_structure._edges:
                node_1 = self._label_id_to_idx[edge.node_1] + 1
                node_2 = self._label_id_to_idx[edge.node_2] + 1
                joints.append([node_1, node_2])  # Joints start at 1 index
            positions = []
            for position in keypoint_structure._positions:
                positions.extend([position.x, position.y])
            point_cat.add(label_id=0, labels=[label.name for label in geti_labels], joints=joints, positions=positions)

        # Old version of datumaro doesn't have 'add_label_group' function
        # We thus check the existence of function before the function call
        if label_schema is not None:
            label_groups = label_schema.get_groups()
            for label_group in label_groups:
                dm_group_name = label_group.name
                dm_group_type = (
                    DmGroupType.EXCLUSIVE
                    if label_group.group_type == LabelGroupType.EXCLUSIVE
                    else DmGroupType.RESTRICTED
                )
                dm_child_names = [sc_label.name for sc_label in label_group.labels]

                # When a group contains at least one valid label,
                # the group is necessary to be exported
                label_cat.add_label_group(
                    name=dm_group_name,
                    labels=dm_child_names,
                    group_type=dm_group_type,
                )

        self._categories = {
            dm_AnnotationType.label: label_cat,
            dm_AnnotationType.mask: mask_cat,
            dm_AnnotationType.points: point_cat,
        }

        self._label_name_to_all_parent = self.get_label_to_all_parents()

    def __iter__(self) -> Iterator[dm_DatasetItem]:
        for item in self._dataset:
            yield self._convert_item(item)

    def infos(self) -> dict[str, Any]:
        return self._infos

    def categories(self) -> dm_CategoriesInfo:
        return self._categories

    def get_label_to_all_parents(self) -> dict[str, list[str]]:
        label_name_to_parent = {}
        label_names = []

        for label_info in self._categories[dm_AnnotationType.label]:
            label_name = label_info.name
            parent_name = label_info.parent

            label_names.append(label_name)
            label_name_to_parent[label_name] = parent_name

        label_name_to_all_parents = defaultdict(list)
        for label_name in label_names:
            label_parent = label_name
            while True:
                label_parent = label_name_to_parent[label_parent]
                if len(label_parent) == 0:
                    break
                label_name_to_all_parents[label_name].append(label_parent)

        return label_name_to_all_parents

    def _convert_annotations(self, annotations: list[Annotation], width: int, height: int) -> list[dm_Annotation]:  # noqa: PLR0912, C901
        dm_anns: list[dm_Annotation] = []
        keypoints = []
        visibilities = []
        keypoint_labels: dict[str, list] = {"keypoint_label_ids": []}
        for sc_ann in annotations:
            non_empty_scored_labels = sc_ann.get_labels(include_empty=False)

            primary_label_id = None
            secondary_labels = {}
            if len(non_empty_scored_labels) > 1:
                # In case of task chaining we can have multiple labels.
                # All supported output formats (VOC, YOLO, COCO) support
                # only 1 label per annotation. Other labels can be represented
                # as attributes.
                # in detection > classification scenario,
                # we only have 1 detection and some
                # classification labels. In multi-label classification
                # scenario, we have only classification labels
                for scored_label in non_empty_scored_labels:
                    if primary_label_id is None and self._label_id_to_label[scored_label.label_id].domain in [
                        Domain.DETECTION,
                        Domain.ANOMALY_DETECTION,
                    ]:
                        primary_label_id = self._label_id_to_idx[scored_label.id_]
                    else:
                        secondary_labels[self._label_id_to_label[scored_label.id_].name] = True
                if primary_label_id is not None:
                    for label_name in secondary_labels:
                        self._categories[dm_AnnotationType.label][primary_label_id].attributes.add(label_name)

            elif len(non_empty_scored_labels) == 1:
                primary_label_id = self._label_id_to_idx[non_empty_scored_labels[0].id_]

            shape = sc_ann.shape
            if isinstance(shape, Polygon):
                dm_anns.append(
                    dm_Polygon(
                        points=list(chain.from_iterable((p.x * width, p.y * height) for p in shape.points)),
                        label=primary_label_id,
                        attributes=secondary_labels,
                    )
                )
            elif isinstance(shape, Rectangle):
                # Classification is represented as full boxes in Geti
                if Rectangle.is_full_box(shape):
                    # hierarchical classification task may store multiple-labels
                    # e.g.) in "rectangle" -> "square" structure,
                    #       if we annotate "square", an item will have both "rectangle" and "square"
                    # Datumaro only keep user annotated label, "square"
                    parent_label_names = set()
                    for non_empty_label in non_empty_scored_labels:
                        parent_label_names.update(self._label_name_to_all_parent[non_empty_label.id_])
                    non_empty_scored_labels = [
                        non_empty_label
                        for non_empty_label in non_empty_scored_labels
                        if non_empty_label.id_ not in parent_label_names
                    ]

                    for scored_label in non_empty_scored_labels:
                        dm_anns.append(dm_Label(self._label_id_to_idx[scored_label.id_]))

                else:
                    dm_anns.append(
                        dm_Bbox(
                            x=shape.x1 * width,
                            y=shape.y1 * height,
                            w=shape.width * width,
                            h=shape.height * height,
                            label=primary_label_id,
                            attributes=secondary_labels,
                        )
                    )
            elif isinstance(shape, Ellipse):
                dm_anns.append(
                    dm_Ellipse(
                        x1=shape.x1 * width,
                        y1=shape.y1 * height,
                        x2=(shape.x1 + shape.width) * width,
                        y2=(shape.y1 + shape.height) * height,
                        label=primary_label_id,
                        attributes=secondary_labels,
                    )
                )
            elif isinstance(shape, Keypoint):
                keypoints.extend([shape.x * width, shape.y * height])
                keypoint_labels["keypoint_label_ids"].append(
                    self._label_id_to_label[non_empty_scored_labels[0].id_].name
                )
                visibilities.append(dm_Points.Visibility.visible if shape.is_visible else dm_Points.Visibility.hidden)
            else:
                raise NotImplementedError(f"Unsupported conversion to DM of {sc_ann.__class__.__name__} items")

        if keypoints and visibilities:
            dm_anns.append(
                dm_Points(
                    points=keypoints,
                    visibility=visibilities,
                    label=0,
                    attributes=keypoint_labels,
                )
            )

        return dm_anns

    def _convert_item(
        self,
        sc_item: DatasetItem,
        video_root: str | None = None,
    ) -> dm_DatasetItem:
        """
        Convert Geti dataset item to DM dataset item.

        :param sc_item: Geti dataset item
        :param video_root: If this value is None, save the video as individual frame images.
                           Otherwise, save the video in its original format.
        :return: Datumaro dataset item
        """
        height = sc_item.height
        width = sc_item.width
        sc_annotations = sc_item.get_annotations(include_empty=True)

        # check if sc_item has empty label
        has_empty_label = False
        for sc_ann in sc_annotations:
            empty_labels = [label for label in sc_ann.get_labels(include_empty=True) if label.is_empty]
            if len(empty_labels) > 0:
                has_empty_label = True
                break

        dm_anns = self._convert_annotations(annotations=sc_annotations, width=width, height=height)

        if video_root is None or not isinstance(sc_item.media, VideoFrame):
            numpy_data = get_media_numpy(
                dataset_storage_identifier=self._dataset_storage_identifier,
                media=sc_item.media,
            )
            dm_media = dm_Image.from_numpy(
                lambda: cv2.cvtColor(numpy_data, cv2.COLOR_RGB2BGR),
                ext=cast("Image", sc_item.media).extension.value if isinstance(sc_item.media, Image) else ".jpg",
                size=(height, width),
            )
        else:
            video_frame = cast("VideoFrame", sc_item.media)
            video_path = self._save_video(video=video_frame.video, video_root=video_root)
            dm_media = dm_VideoFrame(video=dm_Video(path=video_path), index=video_frame.frame_index)

        return dm_DatasetItem(
            id=self._name_mapper.forward(sc_item),
            subset=sc_item.subset.name if self._use_subset else DEFAULT_SUBSET_NAME,
            media=dm_media,
            annotations=dm_anns,
            attributes={"has_empty_label": has_empty_label},
        )

    def _save_video(self, video: Video, video_root: str) -> str:
        video_name = self._video_mapper.forward(video)
        extension = os.path.splitext(video.data_binary_filename)[1]
        video_path = os.path.join(video_root, f"{video_name}{extension}")
        video_dir = os.path.dirname(video_path)
        if not os.path.exists(video_dir):
            os.makedirs(video_dir, exist_ok=True)
        if not os.path.exists(video_path):
            file_location = self._video_binary_repo.get_path_or_presigned_url(video.data_binary_filename)
            if os.path.exists(file_location):  # local path
                shutil.copyfile(file_location, video_path)
            else:  # url
                with open(video_path, "wb") as file:
                    video_data = get_video_bytes(
                        dataset_storage_identifier=self._dataset_storage_identifier,
                        video=video,
                    )
                    file.write(video_data)
        return video_path

    @property
    def is_stream(self) -> bool:
        return True


@dataclass(frozen=True)
class DatasetItemWithFuture:
    item: DatasetItem
    img_bytes_future: AsyncResult[bytes] | None = None
    img_extension: str | None = None


class ScExtractorForFlyteJob(ScExtractor):
    """
    Represents the Geti dataset as a lazy dataset for Datumaro.
    It is used for Flyte job.
    """

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        sc_dataset_or_list_of_sc_items: list[DatasetItem],
        label_schema: LabelSchema,
        num_thread_pools: int = 10,
    ) -> None:
        super().__init__(
            dataset_storage_identifier,
            sc_dataset_or_list_of_sc_items,
            label_schema,
            use_subset=True,
        )
        self._thread_pool = ThreadPool(processes=num_thread_pools)

    def _set_name_mapper(self):
        self._name_mapper = IDMapper

    def _init_categories(
        self, sc_dataset: Dataset, label_schema: LabelSchema | None, keypoint_structure: KeypointStructure | None = None
    ) -> None:
        if label_schema is None:
            raise RuntimeError("label_schema=None is not allowed.")

        dm_label_schema_info = LabelSchemaMapper.forward(
            label_schema=label_schema, include_empty=True, keypoint_structure=keypoint_structure
        )

        self._categories = {
            dm_AnnotationType.label: dm_label_schema_info.label_cat,  # label names: name, parent, attributes
            dm_AnnotationType.mask: dm_label_schema_info.mask_cat,  # label colour: rgb
            dm_AnnotationType.points: dm_label_schema_info.point_cat,  # keypoint label: position, visibility
        }

        self.dataset_item_mapper = DatasetItemMapper(
            uploader_id=sc_dataset.id_,
            annotation_scene_mapper=AnnotationSceneMapper(
                label_map=LabelMap(
                    label_schema=label_schema,
                    label_categories=self.categories().get(dm_AnnotationType.label),
                    point_categories=self.categories().get(dm_AnnotationType.points),
                ),
            ),
            label_id_to_label=self._label_id_to_label,
        )

    @staticmethod
    def _get_image_bytes(
        session: Session,
        dataset_storage_identifier: DatasetStorageIdentifier,
        image: Image,
    ) -> bytes:
        with session_context(session=session):
            return get_image_bytes(dataset_storage_identifier=dataset_storage_identifier, image=image)

    def __iter__(self) -> Iterator[dm_DatasetItem]:
        items: list[DatasetItemWithFuture] = []

        for sc_item in self._dataset:
            if isinstance(sc_item.media, Image):
                future = self._thread_pool.apply_async(
                    self._get_image_bytes,
                    args=(
                        CTX_SESSION_VAR.get(),
                        self._dataset_storage_identifier,
                        sc_item.media,
                    ),
                )
                items.append(
                    DatasetItemWithFuture(
                        item=sc_item,
                        img_bytes_future=future,
                        img_extension=cast("Image", sc_item.media).extension.value,
                    )
                )
            elif isinstance(sc_item.media, VideoFrame):
                items.append(DatasetItemWithFuture(item=sc_item))
            else:
                raise TypeError(type(sc_item.media))

        for item in items:
            yield self.dataset_item_mapper.forward(
                dataset_storage_identifier=self._dataset_storage_identifier,
                instance=item.item,
                image_bytes_future=item.img_bytes_future,
                extension=item.img_extension,
            )


@dataclass
class RangeIdentifier:
    range_id: ID
    range_idx: int


class VideoExportConfig(NamedTuple):
    """
    Configuration class for exporting videos as their original format.
    Attributes:
        video_root(str): Root path of a video when saved as its original format.
        save_video_annotation_range(bool): Whether to save video annotations range or not.
    """

    video_root: str
    save_video_annotation_range: bool


class ProgressConfig(NamedTuple):
    """
    Configuration class for reporting progress of export job.
    Attributes:
        progress_callback (Callable[[int, int], None]): An optional callback function
            that takes two integers (current progress, total) and returns None.
            It is called to update the progress of the iteration.
        total_iter_count (int): Total count of iterations (epochs).
            The number of iterations (epochs) over dataset within the export function
            of Datumaro varies for each dataset format.
    """

    progress_callback: Callable[[int, int], None]
    total_iter_count: int


class ScExtractorFromDatasetStorage(ScExtractor):
    """
    Represents the Geti dataset storage as a lazy dataset for Datumaro.
    """

    def __init__(
        self,
        dataset_storage: DatasetStorage,
        label_schema: LabelSchema,
        use_subset: bool = False,
        include_unannotated: bool = True,
        video_export_config: VideoExportConfig | None = None,
        progress_config: ProgressConfig | None = None,
    ) -> None:
        """
        Represents the Geti dataset storage as a lazy dataset for Datumaro.

        :param dataset_storage: Geti dataset storage
        :param label_schema: Geti label schema
        :param use_subset: Whether to set subset name from sc item or not
        :param include_unannotated: Whether to include unannotated media or not
        :param video_export_config: If this is given, save video as its original format.
        :param progress_config: If this is given, iteration progress will be reported.
        """
        super().__init__(
            dataset_storage_identifier=dataset_storage.identifier,
            sc_dataset_or_list_of_sc_items=NullDataset(),
            label_schema=label_schema,
            use_subset=use_subset,
        )

        self._dataset_storage = dataset_storage
        self._include_unannotated = include_unannotated
        self._video_root = video_export_config.video_root if video_export_config else None
        self._sc_id_to_label = {label.id_: label for label in label_schema.get_labels(include_empty=True)}

        self._annotation_scene_repo = AnnotationSceneRepo(self._dataset_storage.identifier)

        image_repo = ImageRepo(self._dataset_storage.identifier)
        video_repo = VideoRepo(self._dataset_storage.identifier)
        range_repo = VideoAnnotationRangeRepo(self._dataset_storage.identifier)

        self._images_dict = {image.id_: image for image in image_repo.get_all()}
        self._videos_dict = {video.id_: video for video in video_repo.get_all()}

        self._identifiers: list[ImageIdentifier | VideoIdentifier | VideoFrameIdentifier | RangeIdentifier] = []
        self._identifiers.extend(image_repo.get_all_identifiers())
        for video_id in self._videos_dict:
            annotated_frame_identifiers = self._annotation_scene_repo.get_annotated_video_frame_identifiers_by_video_id(
                video_id=video_id, annotation_kind=AnnotationSceneKind.ANNOTATION
            )
            if annotated_frame_identifiers:
                self._identifiers.extend(annotated_frame_identifiers)
            elif self._video_root:
                self._identifiers.append(VideoIdentifier(video_id))

        self._ranges_dict = {}
        self._sc_id_to_name = {}
        if video_export_config and video_export_config.save_video_annotation_range:
            range_identifiers: list[RangeIdentifier] = []
            for video_id in self._videos_dict:
                ann_range = range_repo.get_latest_by_video_id(video_id=video_id)
                if ann_range.range_labels:
                    self._ranges_dict[ann_range.id_] = ann_range
                    identifiers = [RangeIdentifier(ann_range.id_, i) for i in range(len(ann_range.range_labels))]
                    range_identifiers.extend(identifiers)
            self._identifiers.extend(range_identifiers)
            sc_labels = label_schema.get_labels(include_empty=False)
            self._sc_id_to_name = {sc_label.id_: sc_label.name for sc_label in sc_labels}

        self._progress_config = progress_config
        self._iter_count = -1
        self._total = len(self._identifiers)

    def __iter__(self) -> Iterator[dm_DatasetItem]:
        # It is required to init name mapper for multiple iterators within dm.StreamDataset
        self._set_name_mapper()
        for i, identifier in enumerate(self._identifiers):
            if self._progress_config:
                # Datumaro's export iterates the dataset several times while exporting.
                # This is tricky, but we need to consider the implementation detail of datumaro here.
                if i == 0:
                    self._iter_count += 1
                    logger.info(
                        "new iteration started: iter_count = "
                        f"{self._iter_count + 1} / {self._progress_config.total_iter_count}"
                    )
                if 0 <= self._iter_count < self._progress_config.total_iter_count:
                    self._progress_config.progress_callback(
                        self._iter_count * self._total + i,
                        self._total * self._progress_config.total_iter_count,
                    )
            if isinstance(identifier, RangeIdentifier):
                yield self._convert_video_annotation_range(identifier)
            elif isinstance(identifier, VideoIdentifier):
                yield self._convert_video_without_annotations(identifier)
            else:
                scene = self._annotation_scene_repo.get_latest_annotations_by_kind_and_identifiers(
                    media_identifiers=[identifier],
                    annotation_kind=AnnotationSceneKind.ANNOTATION,
                )[0]
                if not self._include_unannotated and not scene.annotations:
                    continue
                if isinstance(identifier, ImageIdentifier):
                    media = self._images_dict[identifier.media_id]
                elif isinstance(identifier, VideoFrameIdentifier):
                    video = self._videos_dict[identifier.media_id]
                    media = VideoFrame(video=video, frame_index=identifier.frame_index)
                else:
                    raise ValueError(f"Unexpected media '{identifier}' to export.")
                dataset_item = DatasetItem(media=media, annotation_scene=scene, id_=DatasetRepo.generate_id())
                yield self._convert_item(sc_item=dataset_item, video_root=self._video_root)

    def _convert_video_without_annotations(self, identifier: VideoIdentifier) -> dm_DatasetItem:
        """
        Convert Video to DM Video item without annotations.
        Note that Geti assumes that dm.Video is for VideoAnnotationRange or Video without annotations,
        not for AnnotationScene.

        :param identifier: Identifier to indicate a Video item
        :return: Datumaro dataset item
        """
        video = self._videos_dict[identifier.media_id]
        video_path = self._save_video(video=video, video_root=self._video_root)  # type: ignore
        dm_video = dm_Video(path=video_path)

        return dm_DatasetItem(
            id=f"{self._video_mapper.forward(video)}",
            subset=Subset.NONE.name if self._use_subset else DEFAULT_SUBSET_NAME,
            media=dm_video,
            annotations=[],
            attributes={
                "has_empty_label": False,
            },
        )

    def _convert_video_annotation_range(self, identifier: RangeIdentifier) -> dm_DatasetItem:
        """
        Convert VideoAnnotationRange's range_labels item to DM Video item.
        Note that Geti assumes that dm.Video is for VideoAnnotationRange or Video without annotations,
        not for AnnotationScene.

        :param identifier: Identifier to indicate a RangeLabels item
        :return: Datumaro dataset item
        """
        ann_range: VideoAnnotationRange = self._ranges_dict[identifier.range_id]
        range_labels: RangeLabels = ann_range.range_labels[identifier.range_idx]

        video = self._videos_dict[ann_range.video_id]
        video_path = self._save_video(video=video, video_root=self._video_root)  # type: ignore
        dm_video = dm_Video(
            path=video_path,
            start_frame=range_labels.start_frame,
            end_frame=range_labels.end_frame,
        )

        dm_anns = []
        has_empty_label = False
        for label_id in range_labels.label_ids:
            try:
                dm_anns.append(dm_Label(self._label_id_to_idx[label_id]))
            except KeyError:  # empty label
                has_empty_label = True

        return dm_DatasetItem(
            id=f"{self._video_mapper.forward(video)}_range_{identifier.range_idx}",
            subset=Subset.NONE.name if self._use_subset else DEFAULT_SUBSET_NAME,
            media=dm_video,
            annotations=dm_anns,
            attributes={
                "has_empty_label": has_empty_label,
            },
        )

    def _init_cache(self):
        # This is to avoid iteration when creating StreamDataset(...)
        if self._length is None:
            self._length = self._total
        if self._subsets is None:
            self._subsets = {Subset.NONE.name if self._use_subset else DEFAULT_SUBSET_NAME}

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements import utilities
"""

import logging
import os.path as osp
from collections.abc import Callable

from bson import ObjectId
from datumaro import Dataset as dm_Dataset
from datumaro import DatasetItem as dm_DatasetItem
from datumaro import Image as dm_Image
from datumaro import Video as dm_Video
from datumaro import VideoFrame as dm_VideoFrame
from datumaro.components.errors import (
    DatasetImportError,
    MultipleFormatsMatchError,
    NoMatchingFormatsError,
    UnknownFormatError,
)
from geti_kafka_tools import publish_event
from geti_types import CTX_SESSION_VAR, ID, DatasetStorageIdentifier, ProjectIdentifier, VideoFrameIdentifier
from iai_core.adapters.adapter import ReferenceAdapter
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.label import Label, NullLabel
from iai_core.entities.label_schema import LabelGroup, LabelSchema
from iai_core.entities.project import NullProject, Project
from iai_core.entities.video import NullVideo
from iai_core.entities.video_annotation_range import RangeLabels, VideoAnnotationRange
from iai_core.repos import (
    DatasetStorageRepo,
    ImageRepo,
    LabelRepo,
    LabelSchemaRepo,
    ProjectRepo,
    VideoAnnotationRangeRepo,
    VideoRepo,
)
from jobs_common_extras.datumaro_conversion.convert_utils import ConvertUtils, MediaInfo
from jobs_common_extras.datumaro_conversion.definitions import GetiProjectType
from jobs_common_extras.datumaro_conversion.import_utils import ImportUtils as BaseImportUtils
from jobs_common_extras.datumaro_conversion.import_utils import ScImportErrorPolicy

from job.utils.constants import MAX_NUMBER_OF_DATASET_STORAGES, MAX_NUMBER_OF_MEDIA_PER_PROJECT
from job.utils.exceptions import (
    DatasetFormatException,
    DatasetLoadingException,
    DatasetStorageAlreadyExistsException,
    FileNotFoundException,
    InvalidIDException,
    InvalidLabelException,
    InvalidMediaException,
    MaxDatasetStorageReachedException,
    MaxMediaReachedException,
    ProjectNotFoundException,
)
from job.utils.upload_utils import AnnotationUploadManager, ImageUploadManager, VideoUploadManager

logger = logging.getLogger(__name__)


class ImportUtils(BaseImportUtils):
    @staticmethod
    def detect_format(path: str) -> str:
        try:
            return BaseImportUtils.detect_format(path=path)
        except MultipleFormatsMatchError as e:
            raise DatasetFormatException(
                "Failed to detect dataset format automatically: "
                f"data matches more than one format: {','.join(e.formats)}"
            )
        except NoMatchingFormatsError:
            raise DatasetFormatException("Failed to detect dataset format automatically: no matching formats found")
        except KeyError as e:
            raise DatasetFormatException(f"Detected dataset format ({str(e)}) is not supported")

    @staticmethod
    def parse_dataset(path: str, fmt: str) -> tuple[dm_Dataset, ScImportErrorPolicy]:
        try:
            return BaseImportUtils.parse_dataset(path, fmt)
        except UnknownFormatError:
            raise DatasetLoadingException(f"Failed to load the dataset due to the unknown format({fmt})")
        except DatasetImportError as e:
            message = f"Failed to load the dataset with given format({fmt})"
            cause = str(getattr(e, "__cause__", ""))
            if fmt == "yolo" and cause == "Failed to parse names file path from config":
                message += " due to missing 'names' field in 'obj.data'"
            elif cause:
                message += f": {cause}"

            raise DatasetLoadingException(message)

    @staticmethod
    def is_video_unannotated(dm_item: dm_DatasetItem) -> bool:
        """
        Check if the video has no annotations.

        We use the dm_Video media type for two purposes:
        to represent unannotated videos or video annotation ranges.
        In the case of an Unannotated Video, it should return True,
        and for representing a VideoAnnotationRange, it should return False.
        """
        has_empty_label = dm_item.attributes.get("has_empty_label", False)
        return not (has_empty_label or dm_item.annotations)

    @staticmethod
    def _count_media_in_dm_dataset(dm_dataset: dm_Dataset) -> int:
        dm_images: int = 0
        dm_videos: set[str] = set()

        for dm_item in dm_dataset:
            if isinstance(dm_item.media, dm_VideoFrame) or (
                isinstance(dm_item.media, dm_Video) and ImportUtils.is_video_unannotated(dm_item)
            ):
                dm_videos.add(getattr(dm_item.media, "path", ""))
            elif isinstance(dm_item.media, dm_Image):
                dm_images += 1

        return dm_images + len(dm_videos)

    @staticmethod
    def check_max_number_of_media(dm_dataset: dm_Dataset, project: Project = NullProject()) -> None:
        existing_media_files = 0
        if not isinstance(project, NullProject):
            for dataset_storage in project.get_dataset_storages():
                n_all_images = ImageRepo(dataset_storage.identifier).count()
                n_all_videos = VideoRepo(dataset_storage.identifier).count()
                existing_media_files += n_all_images + n_all_videos

        if (
            MAX_NUMBER_OF_MEDIA_PER_PROJECT
            and ImportUtils._count_media_in_dm_dataset(dm_dataset) + existing_media_files
            >= MAX_NUMBER_OF_MEDIA_PER_PROJECT
        ):
            message = (
                f"Importing this dataset will exceed the maximum number of media allowed per project "
                f"({MAX_NUMBER_OF_MEDIA_PER_PROJECT}). Please "
            )
            if existing_media_files > 0:
                message += "delete any existing media or "
            message += "reduce the size of the dataset and try again."
            raise MaxMediaReachedException(message)

    @staticmethod
    def publish_project_created_message(project: Project) -> None:
        """
        Publishes kafka message for newly created project

        :param project: Newly created project
        """
        publish_event(
            topic="project_creations",
            body={
                "workspace_id": str(project.workspace_id),
                "project_id": str(project.id_),
            },
            key=str(project.id_).encode(),
            headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
        )

    @staticmethod
    def get_validated_labels_map(labels_map: dict, project_identifier: ProjectIdentifier) -> dict[str, Label]:
        """
        Validate that the label map is either empty, or each key has a valid ID as value

        :param labels_map: The label data that needs to be validated
        :param project_identifier: Identifier of the project containing the labels
        :return: The validated labels map which maps the datumaro label name to the project's label
        """

        valid_labels_map = {}
        label_repo = LabelRepo(project_identifier)
        for dm_name, sc_label_id in labels_map.items():
            label = label_repo.get_by_id(ID(sc_label_id))
            if isinstance(label, NullLabel):
                raise InvalidLabelException(f"The provided label ID({sc_label_id}) does not belong to any label.")
            valid_labels_map[dm_name] = label

        return valid_labels_map

    @staticmethod
    def get_validated_mongo_id(id: str, id_name: str) -> ID:
        """Validate and returns ID"""
        if not ObjectId.is_valid(id):
            raise InvalidIDException(f"Invalid {id_name}. The provided string is not a valid ID: '{id}'.")
        return ID(id)

    @staticmethod
    def get_validated_project(project_id: str) -> Project:
        """Validate and returns project from project_id"""
        project = ProjectRepo().get_by_id(ImportUtils.get_validated_mongo_id(id=project_id, id_name="Project ID"))
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(
                f"No project with given project ID({project_id}) is found. Please verify provided IDs."
            )
        return project

    @staticmethod
    def is_task_hierarhical_or_multi_labels(
        project_identifier: ProjectIdentifier,
    ) -> tuple[bool, bool]:
        """
        Check if the given classification task is hierarchical or multi-labels.

        :param project_identifier: Identifier of the project.
        :return is_task_hierarchical: Whether if the project is hierarchical classification or not.
        :return is_task_multi_labels: Whether if the project is multi-labels classification or not.
        """
        is_task_hierarchical = False
        is_task_multi_labels = False
        label_schema = LabelSchemaRepo(project_identifier).get_latest()
        if label_schema.label_tree.num_labels > 0:
            is_task_hierarchical = True
        else:
            label_groups: list[LabelGroup] = label_schema.get_groups(include_empty=True)
            if len(label_groups) > 1:
                is_task_multi_labels = True
                for group in label_groups:
                    if not group.is_single_label():
                        is_task_hierarchical = True
                        break

        return is_task_hierarchical, is_task_multi_labels

    @staticmethod
    def create_dataset_storage(project: Project, dataset_name: str = "") -> DatasetStorage:
        """
        Create a new dataset storage and return its ID.

        :param project: The project where the dataset storage will be created.
        :param dataset_name: Optional. The name of the dataset storage.
        :return: The ID of the created dataset storage.
        """
        if MAX_NUMBER_OF_DATASET_STORAGES and project.dataset_storage_count >= MAX_NUMBER_OF_DATASET_STORAGES:
            raise MaxDatasetStorageReachedException(
                f"Cannot create another dataset. The maximum of {MAX_NUMBER_OF_DATASET_STORAGES} has been reached."
            )
        if not dataset_name:
            dataset_name = ImportUtils.get_new_dataset_name(
                project=project,
            )
        else:
            dataset_storages = project.get_dataset_storages()
            names = {dataset_storage.name for dataset_storage in dataset_storages}
            if dataset_name in names:
                raise DatasetStorageAlreadyExistsException(
                    f"Cannot create another dataset. Dataset with name '{dataset_name}' already exists."
                )
        dataset_storage = DatasetStorage(
            name=dataset_name,
            project_id=project.id_,
            _id=DatasetStorageRepo.generate_id(),
            use_for_training=False,
        )
        dataset_storage_repo = DatasetStorageRepo(project_identifier=project.identifier)
        dataset_storage_repo.save(dataset_storage)
        project.dataset_storage_adapters.append(ReferenceAdapter(dataset_storage))
        ProjectRepo().save(project)

        return dataset_storage

    @staticmethod
    def populate_project_from_datumaro_dataset(  # noqa: PLR0913
        project: Project,
        dataset_storage_identifier: DatasetStorageIdentifier,
        dm_dataset: dm_Dataset,
        label_schema: LabelSchema,
        get_sc_label: Callable,
        user_id: str,
        sc_label_to_all_parents: dict[Label, list[Label]] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> None:
        """
        Convert datumaro dataset items to SC images and annotation scenes
        and add these to project with given id

        :param project: project to populate with images and annotation scenes
        :param dataset_storage_identifier: The identifier of the target dataset storage
        :param dm_dataset: datumaro dataset
        :param label_schema: label_schema of the project
        :param get_sc_label: method used to get SC label from datumaro label name
        :param user_id: id the user who uploaded
        :param sc_label_to_all_parents: Optional. dictionary of mapping sc_label to all ancestor labels
        :param progress_callback: An optional callback function that takes two integers
                                  (current progress, total) and returns None. It is called
                                  to update the progress of the operation.
        """
        population_manager = PopulationManager(
            project=project,
            dataset_storage_identifier=dataset_storage_identifier,
            dm_dataset=dm_dataset,
            label_schema=label_schema,
            get_sc_label=get_sc_label,
            user_id=user_id,
            sc_label_to_all_parents=sc_label_to_all_parents,
        )
        population_manager.populate(progress_callback=progress_callback)


class PopulationManager:
    def __init__(
        self,
        project: Project,
        dataset_storage_identifier: DatasetStorageIdentifier,
        dm_dataset: dm_Dataset,
        label_schema: LabelSchema,
        get_sc_label: Callable,
        user_id: str,
        sc_label_to_all_parents: dict[Label, list[Label]] | None = None,
    ):
        """
        Convert datumaro dataset items to SC images and annotation scenes
        and add these to project with given id

        :param project: project to populate with images and annotation scenes
        :param dataset_storage_identifier: The identifier of the target dataset storage
        :param dm_dataset: datumaro dataset
        :param label_schema: label_schema of the project
        :param get_sc_label: method used to get SC label from datumaro label name
        :param user_id: id the user who uploaded
        :param sc_label_to_all_parents: Optional. dictionary of mapping sc_label to all ancestor labels
        """
        has_single_subset = len(dm_dataset.subsets()) <= 1
        get_image_name = ConvertUtils.map_image_names(has_single_subset)
        get_video_name = ConvertUtils.map_video_names(has_single_subset)

        image_uploader = ImageUploadManager(
            dataset_storage_identifier=dataset_storage_identifier,
            uploader_id=user_id,
            get_image_name=get_image_name,
        )
        video_uploader = VideoUploadManager(
            dataset_storage_identifier=dataset_storage_identifier,
            uploader_id=user_id,
            get_video_name=get_video_name,
        )
        annotations_uploader = AnnotationUploadManager(
            dataset_storage_identifier=dataset_storage_identifier,
            uploader_id=user_id,
            project=project,
            label_schema=label_schema,
            get_sc_label=get_sc_label,
            sc_label_to_all_parents=sc_label_to_all_parents,
        )

        self._dataset_storage_identifier = dataset_storage_identifier
        self._dm_dataset = dm_dataset
        self._image_uploader = image_uploader
        self._video_uploader = video_uploader
        self._annotations_uploader = annotations_uploader
        self._ranges_per_video: dict[str, list[dm_DatasetItem]] = {}

        # Check if we need to create VideoAnnotationRange from VideoFrame annotations
        if ImportUtils.get_exported_project_type(self._dm_dataset.infos()) == GetiProjectType.UNKNOWN:
            tasks = project.get_trainable_task_nodes()
            self._create_video_annotation_range = len(tasks) == 1 and tasks[0].task_properties.is_global
            # Anomaly tasks should have a valid GetiProjectType. So we don't need to check 'is_anomaly' here.
        else:
            self._create_video_annotation_range = False

    def _add_range_labels(self, video_path: str | None, range_labels: RangeLabels | None):
        if not video_path or not range_labels:
            logger.warning("video path or range_labels item is None.")
            return

        if video_path not in self._ranges_per_video:
            self._ranges_per_video[video_path] = [range_labels]
        else:
            self._ranges_per_video[video_path].append(range_labels)

    def _populate_image(self, dm_item: dm_DatasetItem) -> None:
        media_info = self._image_uploader.upload(dm_item=dm_item)
        if media_info:
            self._annotations_uploader.upload(dm_item=dm_item, media_info=media_info)

    def _populate_video_frame(self, dm_item: dm_DatasetItem) -> None:
        # Handle Media
        video = self._video_uploader.upload(dm_item=dm_item)
        if isinstance(video, NullVideo):
            raise FileNotFoundException(
                "The requested video could not be found in this dataset. "
                f"Dataset Storage ID: `{self._dataset_storage_identifier.dataset_storage_id}`, "
                f"video_path: {osp.basename(getattr(dm_item.media, 'path', ''))}."
            )
        frame_index = dm_item.media.index
        if not 0 <= frame_index < video.total_frames:
            raise InvalidMediaException(
                f"The frame index {frame_index} could not be found in the video with ID `{video.id_}`. "
            )
        media_info = MediaInfo(
            identifier=VideoFrameIdentifier(video.id_, frame_index),
            height=video.height,
            width=video.width,
        )

        # Handle Annotations
        annotation_scene = self._annotations_uploader.upload(dm_item=dm_item, media_info=media_info)
        if annotation_scene.annotations and self._create_video_annotation_range:
            video_path = getattr(dm_item.media, "path", None)
            label_ids = list(annotation_scene.annotations[0].get_label_ids(include_empty=True))
            range_labels = RangeLabels(start_frame=frame_index, end_frame=frame_index, label_ids=label_ids)
            self._add_range_labels(video_path=video_path, range_labels=range_labels)

    def _handle_video(self, dm_item: dm_DatasetItem) -> None:
        video_path = getattr(dm_item.media, "path", None)
        if ImportUtils.is_video_unannotated(dm_item):
            video = self._video_uploader.upload(dm_item=dm_item)
            if isinstance(video, NullVideo):
                raise FileNotFoundException(
                    "The requested video could not be found in this dataset. "
                    f"Dataset Storage ID: `{self._dataset_storage_identifier.dataset_storage_id}`, "
                    f"video_path: {osp.basename(getattr(dm_item.media, 'path', ''))}."
                )
        else:
            range_labels = self._annotations_uploader.get_range_labels(dm_item=dm_item)
            self._add_range_labels(video_path=video_path, range_labels=range_labels)

    def _populate_video_annotation_range(self) -> None:
        video_ann_range_repo = VideoAnnotationRangeRepo(self._dataset_storage_identifier)
        count = 0
        for video_path, range_labels in self._ranges_per_video.items():
            video_id = self._video_uploader.get_video_id(video_path)
            if not video_id:
                logger.warning(f"Skip video annotation ranges for video path '{video_path}'")
                continue
            # TODO: Need to check if the actual annotations match the video annotation range.
            video_annotation_range = VideoAnnotationRange(
                video_id=video_id,
                range_labels=range_labels,
                id_=VideoAnnotationRangeRepo.generate_id(),
            )
            video_ann_range_repo.save(video_annotation_range)
            count += 1

        logger.info(f"Created {count} video annotation range items")

    def populate(self, progress_callback: Callable[[int, int], None] | None = None) -> None:
        """
        Polulate media items and annotations.

        :param progress_callback: An optional callback function that takes two integers
                                  (current progress, total) and returns None. It is called
                                  to update the progress of the operation.
        """
        total = len(self._dm_dataset)
        for i, dm_item in enumerate(self._dm_dataset):
            if progress_callback:
                progress_callback(i, total)
            try:
                media = dm_item.media
                if isinstance(media, dm_VideoFrame):  # VideoFrame should come before Image
                    self._populate_video_frame(dm_item=dm_item)
                elif isinstance(media, dm_Image):
                    self._populate_image(dm_item=dm_item)
                elif isinstance(media, dm_Video):
                    self._handle_video(dm_item=dm_item)
                else:
                    logger.warning(f"Skip dm item with unsupported media type '{media.type.value}'.")
            except InvalidMediaException as e:
                logger.warning(f"Skip dm item due to following error: {str(e)}")
            except AttributeError as e:
                logger.exception(f"Failed to convert dm item to SC with following error: {str(e)}")
        if self._ranges_per_video:
            self._populate_video_annotation_range()

        logger.info(
            "Saved %d images, %d videos, and %d annotation scenes to dataset with id %s",
            len(self._image_uploader),
            len(self._video_uploader),
            len(self._annotations_uploader),
            str(self._dataset_storage_identifier.dataset_storage_id),
        )

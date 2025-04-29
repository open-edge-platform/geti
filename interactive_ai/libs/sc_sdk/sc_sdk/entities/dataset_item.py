# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the DatasetItem entity"""

import copy
import itertools
import logging
from collections.abc import Sequence

from sc_sdk.adapters.adapter import ReferenceAdapter
from sc_sdk.entities.annotation import Annotation, AnnotationScene, NullAnnotationScene
from sc_sdk.entities.image import NullImage
from sc_sdk.entities.label import Label
from sc_sdk.entities.media_2d import Media2D
from sc_sdk.entities.metadata import IMetadata, MetadataItem
from sc_sdk.entities.model import Model
from sc_sdk.entities.persistent_entity import PersistentEntity
from sc_sdk.entities.scored_label import ScoredLabel
from sc_sdk.entities.shapes import Rectangle
from sc_sdk.entities.subset import Subset
from sc_sdk.utils.shape_factory import ShapeFactory
from sc_sdk.utils.type_helpers import SequenceOrSet
from sc_sdk.utils.uid_generator import generate_uid

from geti_types import ID, MediaIdentifierEntity

logger = logging.getLogger(__name__)


class DatasetItem(PersistentEntity):
    """
    DatasetItem represents an item in the Dataset.

    It holds a media item, annotation and an ROI. The ROI determines the region of interest for the dataset item, and
    is described by a shape entity.

    The fundamental properties of a dataset item are:

    - A 2d media entity (e.g. Image)
    - A 2d annotation entity for the full resolution media entity
    - An ROI, describing the region of interest.
    - The subset it belongs to
    - Metadata for the media entity (e.g. saliency map or active score)
    - A list of labels to ignore

    .. rubric:: Getting data from dataset item

    >>> dataset_item = DatasetItem()

    Get the subset of labels for the item ROI:

    >>> labels = dataset_item.get_roi_label_ids(label_ids=)

    Get the annotations __visible__ in the ROI:

    >>> dataset_item.get_annotations()

    .. rubric:: Adding output data to dataset item

    It is possible to add shapes or just labels for the ROI.

    Add shapes to dataset item:

    >>> box = Rectangle(x1=0.2, y1=0.3, x2=0.6, y2=0.5)
    >>> dataset_item.append_annotations(annotations=[Annotation(box,labels=[...])])

    Add labels to ROI:

    >>> dataset_item.append_labels(labels=[...])

    :param media: Media associated with this dataset item
    :param annotation_scene: Annotation scene associated with this dataset item
    :param roi: Region Of Interest, it defines the scope (in spatial terms) of this item within the media.
        If None, the ROI is implicitly the full image.
    :param metadata: Accessory metadata items associated with this dataset item
    :param subset: Dataset subset this item is assigned to
    :param ignored_label_ids: Collection of label ID's that should be ignored in this dataset item.
        For instance, in a training scenario, this parameter is used to ignore certain labels within the
        existing annotations because their status becomes uncertain following a label schema change.
    :param id_: ID of the dataset item
    """

    def __init__(  # noqa: PLR0913
        self,
        id_: ID,
        media: Media2D,
        annotation_scene: AnnotationScene,
        roi: Annotation | None = None,
        metadata: list[MetadataItem] | None = None,
        subset: Subset = Subset.NONE,
        ignored_label_ids: SequenceOrSet[ID] | None = None,
        ephemeral: bool = True,
    ) -> None:
        if not isinstance(media, Media2D):  # type: ignore[arg-type, misc]
            raise ValueError("Dataset item can only contain 2D media.")

        PersistentEntity.__init__(self, id_=id_, ephemeral=ephemeral)

        self.__media: Media2D = media
        self.annotation_scene: AnnotationScene = annotation_scene
        self.subset: Subset = subset
        self._ignored_label_ids: set[ID] = set() if ignored_label_ids is None else set(ignored_label_ids)

        # set ROI
        if roi is None:
            for annotation in annotation_scene.annotations:
                # if there is a full box in annotation.shapes, set it as ROI
                if Rectangle.is_full_box(annotation.shape):
                    roi = annotation
                    break
            else:
                roi = Annotation(Rectangle.generate_full_box(), labels=[])
        self.roi = roi

        self.metadata_adapters: list[ReferenceAdapter] = (
            [ReferenceAdapter(metadata_item) for metadata_item in metadata] if metadata is not None else []
        )

    @classmethod
    def with_adapters(
        cls,
        id_: ID,
        metadata_adapters: list[ReferenceAdapter[MetadataItem]],
        media: Media2D,
        annotation_scene: AnnotationScene,
        roi: Annotation | None = None,
        subset: Subset = Subset.NONE,
        ignored_label_ids: SequenceOrSet[ID] | None = None,
    ):
        """
        Instantiate the Dataset with adapters
        """
        inst = cls(
            media=media,
            annotation_scene=annotation_scene,
            roi=roi,
            subset=subset,
            ignored_label_ids=ignored_label_ids,
            id_=id_,
        )
        inst.metadata_adapters = metadata_adapters
        return inst

    def set_metadata(self, metadata: Sequence[MetadataItem]) -> None:
        """
        Sets the metadata adapters
        """
        self.metadata_adapters = [ReferenceAdapter(metadata_item) for metadata_item in metadata]

    def get_metadata(self) -> list[MetadataItem]:
        """
        Returns the metadata adapters
        """
        return [metadata.get() for metadata in self.metadata_adapters]

    @property
    def metadata_ids(self) -> Sequence[ID]:
        """
        Returns the ID of the metadatas, taken from the adapters
        """
        return [adapter.id_ for adapter in self.metadata_adapters]

    @property
    def ignored_label_ids(self) -> set[ID]:
        """Return ignored_label_ids"""
        return self._ignored_label_ids

    @ignored_label_ids.setter
    def ignored_label_ids(self, value: SequenceOrSet[ID]) -> None:
        self._ignored_label_ids = set(value)

    @property
    def media(self) -> Media2D:
        return self.__media

    def append_metadata_item(self, data: IMetadata, model: Model | None = None) -> None:
        """Appends an IMetadata attribute to the DatasetItem."""

        self.metadata_adapters.append(
            ReferenceAdapter(
                MetadataItem(
                    data=data,
                    dataset_item_id=self.id_,
                    media_identifier=self.media.media_identifier,
                    model=model,
                    id=generate_uid(),
                )
            )
        )

    def get_metadata_by_name_and_model(self, name: str, model: Model | None) -> list[MetadataItem]:
        """
        Returns a metadata item with `name` and generated by `model`.

        :param name: the name of the metadata
        :param model: the model which was used to generate the metadata.
        :return:
        """

        if model is None:
            return [meta for meta in self.get_metadata() if meta.data.name == name and meta.model is None]

        return [
            meta
            for meta in self.get_metadata()
            if meta.data.name == name and meta.model is not None and meta.model.id_ == model.id_
        ]

    @property
    def media_identifier(self) -> MediaIdentifierEntity:
        """
        The media identifier of the media stored in this item
        """
        return self.media.media_identifier

    @property
    def roi_id(self) -> ID:
        """
        Return ROI id if an ROI is specified, otherwise return an empty ID
        """
        return self.roi.id_ if self.roi is not None else ID()

    def get_rois_containing_labels(
        self,
        labels: list[Label],
    ) -> list[Annotation]:
        """
        Returns a list of rois that exist in the dataset item (wrt. ROI).

        ROIs inside the dataset item are annotations from the annotation scene that have
        their center inside the ROI of the dataset item and at least one relevant label:
        non empty, and not an ignored label. Note that the
        annotation is taken from the original annotation scene as is with all labels and
        not denormalized or otherwise adjusted.

        :param labels: List of relevant labels to filter on
        :return: List of annotations whose shape center is within the dataset item ROI and
            contain at least one of the relevant labels
        """
        result = []
        relevant_label_ids = {label.id_ for label in labels if label.id_ not in self.ignored_label_ids}
        for annotation in self.annotation_scene.annotations:
            if self.roi.shape.contains_center(annotation.shape) and relevant_label_ids.intersection(
                annotation.get_label_ids(include_empty=False)
            ):
                result.append(annotation)

        return result

    @property
    def width(self) -> int:
        """The width of the dataset item, taking into account the ROI."""
        roi_shape_as_box = ShapeFactory.shape_as_rectangle(self.roi.shape)
        roi_shape_as_box = roi_shape_as_box.clip_to_visible_region()
        width = self.media.width

        # Note that we cannot directly use roi_shape_as_box.width due to the rounding
        # because round(x2 - x1) is not always equal to round(x2) - round(x1)
        x1 = int(round(roi_shape_as_box.x1 * width))
        x2 = int(round(roi_shape_as_box.x2 * width))
        return x2 - x1

    @property
    def height(self) -> int:
        """The height of the dataset item, taking into account the ROI."""
        roi_shape_as_box = ShapeFactory.shape_as_rectangle(self.roi.shape)
        roi_shape_as_box = roi_shape_as_box.clip_to_visible_region()
        height = self.media.height

        # Note that we cannot directly use roi_shape_as_box.height due to the rounding
        # because round(y2 - y1) is not always equal to round(y2) - round(y1)
        y1 = int(round(roi_shape_as_box.y1 * height))
        y2 = int(round(roi_shape_as_box.y2 * height))
        return y2 - y1

    def get_annotations(
        self,
        label_ids: SequenceOrSet[ID] | None = None,
        include_empty: bool = False,
        include_ignored: bool = False,
        preserve_id: bool = False,
    ) -> list[Annotation]:
        """
        Returns a list of annotations that exist in the dataset item (wrt. ROI).

        This is done by checking that the center of the annotation is located in the ROI.

        :param label_ids: Subset of input labels to filter with; if ``None``, all the shapes within
                the ROI are returned.
        :param include_empty: if True, returns both empty and non-empty labels
        :param include_ignored: if True, includes the labels in ignored_label_ids
        :param preserve_id: if True, preserve the annotation id when copying
        :returns List[Annotation]: The intersection of the input label set and those present within the ROI
        """
        is_full_box = Rectangle.is_full_box(self.roi.shape)
        annotations = []
        if is_full_box and label_ids is None and include_empty and include_ignored:
            # Fast path for the case where we do not need to change the shapes
            annotations = self.annotation_scene.annotations
        else:
            # Todo: improve speed. This is O(n) for n shapes. CVS-156947
            roi_as_box = ShapeFactory.shape_as_rectangle(self.roi.shape)

            label_ids_set = set(label_ids) if label_ids is not None else set()

            for annotation in self.annotation_scene.annotations:
                if not is_full_box and not self.roi.shape.contains_center(annotation.shape):
                    continue

                shape_labels = annotation.get_labels(include_empty)

                check_labels = False
                if not include_ignored:
                    shape_labels = [label for label in shape_labels if label.id_ not in self.ignored_label_ids]
                    check_labels = True

                if label_ids is not None:
                    shape_labels = [label for label in shape_labels if label.id_ in label_ids_set]
                    check_labels = True

                if check_labels and len(shape_labels) == 0:
                    continue

                if not is_full_box:
                    # Create a denormalized copy of the shape.
                    shape = annotation.shape.denormalize_wrt_roi_shape(roi_as_box)
                else:
                    # Also create a copy of the shape, so that we can safely modify the labels
                    # without tampering with the original shape.
                    shape = copy.deepcopy(annotation.shape)

                annotations.append(
                    Annotation(
                        shape=shape,
                        labels=shape_labels,
                        id_=annotation.id_ if preserve_id else None,
                    )
                )
        return annotations

    def append_annotations(self, annotations: Sequence[Annotation]) -> None:
        """Adds a list of shapes to the annotation."""
        roi_as_box = ShapeFactory.shape_as_rectangle(self.roi.shape)

        validated_annotations = [
            Annotation(
                shape=annotation.shape.normalize_wrt_roi_shape(roi_as_box),
                labels=annotation.get_labels(),
            )
            for annotation in annotations
            if ShapeFactory.shape_produces_valid_crop(shape=annotation.shape)
        ]

        n_invalid_shapes = len(annotations) - len(validated_annotations)
        if n_invalid_shapes > 0:
            logger.info(
                "%d shapes will not be added to the dataset item as they "
                "would produce invalid crops (this is expected for some tasks, "
                "such as segmentation).",
                n_invalid_shapes,
            )

        self.annotation_scene.append_annotations(validated_annotations)

    def get_roi_label_ids(
        self, label_ids: list[ID] | set[ID] | None = None, include_empty: bool = False, include_ignored: bool = False
    ) -> set[ID]:
        """
        Return the subset of the input label ids that exist in the dataset item (wrt. ROI).

        :param label_ids: Subset of input labels to filter with; if ``None``, all the labels
                within the ROI are returned.
        :param include_empty: if True, returns both empty and non-empty labels
        :param include_ignored: if True, includes the labels in ignored_label_ids
        :returns: The intersection of the input label ids set and those present within the ROI.
        """
        filtered_label_ids = {
            scored_label_id
            for scored_label_id in self.roi.get_label_ids(include_empty)
            if label_ids is None or scored_label_id in label_ids
        }
        if not include_ignored:
            filtered_label_ids -= self.ignored_label_ids
        return filtered_label_ids

    def get_shapes_label_ids(
        self, label_ids: SequenceOrSet[ID] | None = None, include_empty: bool = False, include_ignored: bool = False
    ) -> set[ID]:
        """
        Get the label ids of the shapes present in this dataset item.

        if a label ids list is supplied, only label ids present within that list are returned. if include_empty is True,
        present ids of empty labels are returned as well.

        :param label_ids: if supplied only labels present in this list are returned.
                Defaults to None.
        :param include_empty: if True, returns ids of both empty and non-empty labels. Defaults to False.
        :param include_ignored: if True, includes the label ids in ignored_label_ids. Defaults to False.
        :returns: a set of label ID's from the shapes within the roi of this dataset item
        """
        annotations = self.get_annotations(
            label_ids=label_ids, include_empty=include_empty, include_ignored=include_ignored
        )
        label_ids_set = set(
            itertools.chain.from_iterable(annotation.get_label_ids(include_empty) for annotation in annotations)
        )
        if not include_ignored:
            label_ids_set -= self.ignored_label_ids
        if label_ids is not None:
            label_ids_set &= set(label_ids)
        return label_ids_set

    def append_labels(self, labels: list[ScoredLabel]) -> None:
        """
        Appends labels to the DatasetItem and adds it to the annotation label as well if it's not yet there.

        :param labels (List[ScoredLabel]): list of labels to be appended.
        """
        if len(labels) == 0:
            return

        roi_annotation = None
        for annotation in self.annotation_scene.annotations:
            if annotation.shape == self.roi.shape:
                roi_annotation = annotation
                break

        if roi_annotation is None:  # no annotation found with shape
            roi_annotation = self.roi
            self.annotation_scene.append_annotation(roi_annotation)

        for label in labels:
            if label not in self.roi.get_labels(include_empty=True):
                self.roi.append_label(label)
            if label not in roi_annotation.get_labels(include_empty=True):
                roi_annotation.append_label(label)

    def __deepcopy__(self, memo):  # noqa: ANN001
        """Avoid unintentional ID sharing among AnnotationScene instances.

        We prevent deepcopy of AnnotationScene member variable to avoid unintentional ID sharing among instances.
        Same instance reference is copied to the output instead.
        """
        # Call ROI getter to ensure original object has an ROI.
        _ = self.roi

        clone = copy.copy(self)

        for name, value in vars(self).items():
            if "__annotation_scene" in name:
                pass  # Keep the same instance
            else:
                setattr(clone, name, copy.deepcopy(value, memo))
        return clone

    def __repr__(self):
        """String representation of the dataset item."""
        return (
            f"{self.__class__.__name__}("
            f"id_={self.id_}, "
            f"media={self.media.media_identifier}, "
            f"annotation_scene={self.annotation_scene.id_}, "
            f"roi={self.roi.id_}, "
            f"subset={self.subset})"
        )

    def __eq__(self, other: object):
        if not isinstance(other, DatasetItem):
            return False
        return (
            self.id_ == other.id_
            and self.media.media_identifier == other.media.media_identifier
            and self.annotation_scene.id_ == other.annotation_scene.id_
            and self.roi.id_ == other.roi.id_
            and self.subset == other.subset
            and self.ignored_label_ids == other.ignored_label_ids
        )


class NullDatasetItem(DatasetItem):
    """Representation of a null (not found) DatasetItem"""

    def __init__(self) -> None:
        super().__init__(id_=ID(), media=NullImage(), annotation_scene=NullAnnotationScene(), ephemeral=False)

    def __repr__(self) -> str:
        return "NullDatasetItem()"

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the Annotation entity"""

import datetime
import itertools
from enum import Enum

from bson import ObjectId

from iai_core.entities.label import Label
from iai_core.entities.scored_label import ScoredLabel
from iai_core.entities.shapes import Rectangle, Shape
from iai_core.utils.constants import DEFAULT_USER_NAME
from iai_core.utils.time_utils import now

from geti_types import ID, MediaIdentifierEntity, NullMediaIdentifier, PersistentEntity


class Annotation:
    """Base class for annotation objects.

    :param shape: the shape of the annotation
    :param labels: the labels of the annotation
    :param id_: the id of the annotation
    """

    def __init__(self, shape: Shape, labels: list[ScoredLabel], id_: ID | None = None):
        self.id_ = ID(ObjectId()) if id_ is None else id_
        self.shape = shape
        self._labels = labels

    def __repr__(self):
        """String representation of the annotation."""
        return (
            f"{self.__class__.__name__}("
            f"shape={self.shape}, "
            f"labels={self.get_labels(include_empty=True)}, "
            f"id_={self.id_})"
        )

    def get_labels(self, include_empty: bool = False) -> list[ScoredLabel]:
        """Get scored labels that are assigned to this annotation.

        :param include_empty: set to True to include empty label (if exists) in the output. Defaults to False.

        :return: List of labels in annotation
        """
        return [label for label in self._labels if include_empty or (not label.is_empty)]

    def get_label_ids(self, include_empty: bool = False) -> set[ID]:
        """Get a set of ID's of labels that are assigned to this annotation.

        :param include_empty: set to True to include id of empty label (if exists) in the output. Defaults to False.

        :return: Set of label id's in annotation
        """
        return {label.id_ for label in self._labels if include_empty or (not label.is_empty)}

    def append_label(self, label: ScoredLabel) -> None:
        """Appends the scored label to the annotation.

        :param label: the scored label to be appended to the annotation
        """
        self._labels.append(label)

    def set_labels(self, labels: list[ScoredLabel]) -> None:
        """Sets the labels of the annotation to be the input of the function.

        :param labels: the scored labels to be set as annotation labels
        """
        self._labels = labels

    def __eq__(self, other: object) -> bool:
        """Checks if the two annotations are equal.

        :param other: Annotation to compare with.

        :return: True if the two annotations are equal, False otherwise.
        """
        if isinstance(other, Annotation):
            return (
                self.id_ == other.id_ and self.get_labels(True) == other.get_labels(True) and self.shape == other.shape
            )
        return False


class AnnotationSceneKind(Enum):
    """AnnotationSceneKinds for an Annotation object."""

    #:  NONE represents NULLAnnotationScene's (See :class:`NullAnnotationScene`)
    NONE = 0
    #:  ANNOTATION represents user annotation
    ANNOTATION = 1
    #:  PREDICTION represents analysis result, which will be shown to the user
    PREDICTION = 2
    #:  EVALUATION represents analysis result for evaluation purposes, which will NOT be shown to the user
    EVALUATION = 3
    #:  INTERMEDIATE represents intermediary state.
    #:  This is used when the analysis is being transferred from one task to another.
    #:  This will not be shown to the user.
    #:  This state will be changed to either PREDICTION or EVALUATION at the end of analysis process.
    INTERMEDIATE = 4
    #:  TASK_PREDICTION represents analysis results for a single task
    TASK_PREDICTION = 5

    def __str__(self):
        """String representation of the AnnotationSceneKind."""
        return str(self.name)


class AnnotationScene(PersistentEntity):
    """
    This class represents a user annotation or a result (prediction).
    It serves as a collection of shapes, with a relation to the media entity.

    Annotations are only updated by tasks, when SC requests to do so.
    If the user changes an annotation from the UI, a new entity is made while keeping the original version.
    This makes sure the full annotation history is saved within SC.

    :example: Creating an annotation:

    >>> from iai_core.entities.scored_label import ScoredLabel
    >>> from geti_types import ImageIdentifier
    >>> from iai_core.entities.label import NullLabel
    >>> from iai_core.entities.shapes import Rectangle
    >>> media_identifier = ImageIdentifier(image_id=ID("Test image"))
    >>> rectangle = Rectangle(x1=0.0, y1=0.0, x2=0.5, y2=0.5) # Box covering top-left quart of image
    >>> annotation_scene = AnnotationScene(
    >>>    kind=AnnotationSceneKind.ANNOTATION,
    >>>    media_identifier=media_identifier,
    >>>    annotations=[Annotation(shape=rectangle,labels=[ScoredLabel(label_id=ID(), is_empty=True])]
    >>>)

    :param id_: ID of AnnotationScene
    :param kind: Kind of annotation scene `AnnotationSceneKind`. E.g. `AnnotationSceneKind.ANNOTATION`
    :param media_identifier: The `media_identifier` of the media entity the annotation scene is made for
    :param media_height: height of the media in pixels
    :param media_width: width in pixels of the media
    :param last_annotator_id: The editor that made this annotation scene object
    :param creation_date: Creation date of annotation scene entity.
    :param annotations: List of Annotations.
    :param invalid_task_ids: A list of task ids where the annotation has been invalidated for
    :param task_id: if the annotation pertains to a specific task, the task_id refers to the task in question
    """

    def __init__(  # noqa: PLR0913
        self,
        kind: AnnotationSceneKind,
        media_identifier: MediaIdentifierEntity | None = None,
        media_height: int = 0,
        media_width: int = 0,
        id_: ID | None = None,
        last_annotator_id: str = DEFAULT_USER_NAME,
        creation_date: datetime.datetime | None = None,
        annotations: list[Annotation] | None = None,
        invalid_task_ids: list[ID] | None = None,
        task_id: ID = ID(),
        ephemeral: bool = True,
    ) -> None:
        creation_date = now() if creation_date is None else creation_date
        annotations = [] if annotations is None else annotations
        media_identifier = NullMediaIdentifier() if media_identifier is None else media_identifier
        id_ = ID() if id_ is None else id_

        PersistentEntity.__init__(self, id_=id_, ephemeral=ephemeral)
        self.kind = kind
        self.media_identifier = media_identifier
        self.media_height = media_height
        self.media_width = media_width
        self.task_id = task_id
        self.last_annotator_id = last_annotator_id
        self.creation_date = creation_date
        self.annotations = annotations
        if invalid_task_ids is None:
            invalid_task_ids = []
        self.invalid_for_task_ids: list[ID] = invalid_task_ids

    @property
    def shapes(self) -> list[Shape]:
        """Returns all shapes that are inside the annotations of the AnnotationScene."""
        return [annotation.shape for annotation in self.annotations]

    def contains_any(self, labels: list[Label]) -> bool:
        """Checks whether the annotation contains any labels in the input parameter.

        :param labels: List of labels to compare to.

        :return: True if there is any intersection between self.get_labels(include_empty=True) with labels.
        """
        label_ids = {label.id_ for label in labels}
        return len(self.get_label_ids(include_empty=True).intersection(label_ids)) != 0

    def append_annotation(self, annotation: Annotation) -> None:
        """Appends the passed annotation to the list of annotations present in the AnnotationScene object.

        :param annotation: the annotation to be appended
        """
        self.annotations.append(annotation)

    def append_annotations(self, annotations: list[Annotation]) -> None:
        """Adds a list of annotations to the annotation scene.

        :param annotations: the list of annotations to be added
        """
        self.annotations.extend(annotations)

    def get_label_ids(self, include_empty: bool = False) -> set[ID]:
        """Returns a set of the ID's of unique labels which appear in this annotation scene.

        :param include_empty: Set to True to include id of the empty label (if exists) in the output. Defaults to False.

        :return: a set of the ID's of labels which appear in this annotation.
        """
        return set(
            itertools.chain.from_iterable(
                annotation.get_label_ids(include_empty=include_empty) for annotation in self.annotations
            )
        )

    def is_valid_for_task_id(self, task_id: ID) -> bool:
        """
        Returns whether the annotation is valid for the task with `task_id`.
        The annotations are made invalid for a task when the user updates the labels inside the task
        (i.e., add a new label or remove a label).

        :param task_id: task ID
        """
        return task_id not in self.invalid_for_task_ids

    def invalidate_for_task(self, task_id: ID) -> None:
        """
        Invalidates the annotation for the task with `task_id`

        Invalidated means that the annotation will not be used to create datasets for the task. The invalidation
        is typically solved by the user revisiting the image.

        :param task_id: task ID
        """
        if self.is_valid_for_task_id(task_id):
            self.invalid_for_task_ids.append(task_id)

    def get_annotation_with_annotation_id(self, annotation_id: ID) -> Annotation | None:
        """
        Returns the annotation with specific annotation id. Returns None if no annotation matches the provided ID

        :param annotation_id: annotation id for annotation to retrieve from AnnotationScene

        :return: Either None, or an Annotation object
        """
        for annotation in self.annotations:
            if annotation_id == annotation.id_:
                return annotation
        return None

    def get_annotations_with_label_ids(
        self,
        label_ids: list[ID] | set[ID],
        ignore_full_box: bool = False,
    ) -> list[Annotation]:
        """
        Returns a list of annotations which contain any of the label id defined in label_ids.

        :param label_ids: set or list of label ids to cross reference from the AnnotationScene
        :param ignore_full_box: ignore the annotation if it is a full box (covers the whole image)

        :return: Either empty list, or a list of Annotation objects
        """
        output = []
        for annotation in self.annotations:
            if ignore_full_box and Rectangle.is_full_box(annotation.shape):
                continue
            if not set(label_ids).isdisjoint(set(annotation.get_label_ids(include_empty=True))):
                output.append(annotation)
        return output

    def get_model_ids(self, include_user_annotations: bool) -> set[ID]:
        """
        Returns a set of the ID's of unique models which appear in this annotation scene.

        :param include_user_annotations: whether to include annotations submitted
            by the user, that were previously generate by a model.

        :return: a set of model IDs which appear in this annotation scene.
        """
        model_ids = set()
        for annotation in self.annotations:
            annotation_model_ids = {
                label.label_source.model_id
                for label in annotation.get_labels()
                if (
                    label.label_source.model_id != ID() and (include_user_annotations or not label.label_source.user_id)
                )
            }
            model_ids.update(annotation_model_ids)
        return model_ids

    def __repr__(self) -> str:
        n_annotations = str(len(self.annotations))
        return (
            f"AnnotationScene(id_={self.id_}, media_identifier={self.media_identifier}, "
            f"labels={self.get_label_ids(include_empty=True)}, "
            f"{n_annotations} annotations)"
        )

    def __eq__(self, other: object):
        if not isinstance(other, AnnotationScene):
            return False
        return (
            self.id_ == other.id_
            and self.kind == other.kind
            and self.media_identifier == other.media_identifier
            and self.last_annotator_id == other.last_annotator_id
            and self.annotations == other.annotations
            and self.media_height == other.media_height
            and self.media_width == other.media_width
        )

    def __hash__(self):
        return hash(str(self))


class NullAnnotationScene(AnnotationScene):
    """Represents 'AnnotationScene not found'"""

    def __init__(self) -> None:
        super().__init__(
            kind=AnnotationSceneKind.NONE,
            media_identifier=NullMediaIdentifier(),
            media_height=0,
            media_width=0,
            id_=ID(),
            last_annotator_id="",
            creation_date=datetime.datetime.min,
            ephemeral=False,
        )

    def __repr__(self) -> str:
        return "NullAnnotationScene()"

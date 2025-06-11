# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the AnnotationRestValidator class"""

import math
import os

import jsonschema

from communication.constants import MINIMUM_PIXELS_FOR_ANNOTATION
from communication.exceptions import (
    ConflictingExclusiveLabelsException,
    DuplicatedAnnotationIDException,
    LabelNotFoundException,
)
from communication.rest_views.annotation_rest_views import AnnotationRESTViews, RestShapeType
from service.label_schema_service import LabelSchemaService

from geti_fastapi_tools.exceptions import BadRequestException
from geti_fastapi_tools.validation import RestApiValidator
from geti_telemetry_tools import unified_tracing
from geti_types import ID, ImageIdentifier, MediaIdentifierEntity, VideoFrameIdentifier
from iai_core.entities.label import Label
from iai_core.entities.label_schema import LabelGroupType, LabelSchema, LabelSchemaView
from iai_core.entities.model_template import TaskType
from iai_core.entities.project import Project
from iai_core.entities.shapes import Ellipse, Point, Polygon, Rectangle
from iai_core.entities.task_node import TaskNode
from iai_core.utils.constants import MAX_POLYGON_POINTS
from iai_core.utils.type_helpers import SequenceOrSet

ANNOTATIONS = "annotations"
ID_ = "id"
LABELS = "labels"
LABEL_IDS = "label_ids"
SHAPE = "shape"
TYPE = "type"
WIDTH = "width"
HEIGHT = "height"
ANGLE = "angle"
X = "x"
Y = "y"
POINTS = "points"
RANGE_LABELS = "range_labels"
START_FRAME = "start_frame"
END_FRAME = "end_frame"


class AnnotationRestValidator(RestApiValidator):
    def __init__(self) -> None:
        base_dir = os.path.dirname(__file__) + "/../../../../api/schemas/"
        self.image_annotation_schema = self.load_schema_file_as_dict(
            base_dir + "annotations/requests/annotation_scene_image.yaml"
        )
        self.video_frame_annotation_schema = self.load_schema_file_as_dict(
            base_dir + "annotations/requests/annotation_scene_video_frame.yaml"
        )
        self.shapes_schemas = {
            shape: self.load_schema_file_as_dict(base_dir + os.path.join("annotations", shape.lower() + ".yaml"))
            for shape in (shape_type.name for shape_type in RestShapeType)
        }
        self.video_range_schema = self.load_schema_file_as_dict(
            base_dir + "annotations/requests/video_annotation_range.yaml"
        )

    @unified_tracing
    def validate_annotation_scene(
        self,
        annotation_scene_rest: dict,
        project: Project,
        media_identifier: MediaIdentifierEntity,
        media_height: int,
        media_width: int,
        label_schema: LabelSchema | None = None,
        label_schema_by_task: dict[ID, LabelSchemaView] | None = None,
    ) -> None:
        """
        Validate annotation json data with sanity checks. Steps:
        1. Schema validation
        2. Labels validation
        3. Annotations validation

        One of the label_schema or label_schema_by_task must be provided.

        :param annotation_scene_rest: annotation json data
        :param project: project for which to validate the annotation scene
        :param media_identifier: MediaIdentifierEntity used to identify the media the annotation is posted to
        :param media_height: height of the media
        :param media_width: width of the media
        :param label_schema: Optional label schema for the project to which the annotation belongs
        :param label_schema_by_task: Optional, dictionary with the label schema for each task node. If not provided,
            the label schema per task will be fetched from the database.
        """
        if label_schema is None and label_schema_by_task is None:
            raise BadRequestException("Label schema is required to validate annotation scene.")
        if label_schema_by_task is None:
            label_schema_by_task = {
                task_node.id_: LabelSchemaService.get_latest_label_schema_for_task(
                    project_identifier=project.identifier,
                    task_node_id=task_node.id_,
                )
                for task_node in project.get_trainable_task_nodes()
            }
        self.__validate_scene_against_schema(
            annotation_scene_rest=annotation_scene_rest,
            media_identifier=media_identifier,
        )
        self.__validate_all_labels_exist(
            labels_to_check=self.__get_label_ids_from_annotation_scene(annotation_scene_rest=annotation_scene_rest),
            existing_labels=[
                label.id_ for schema in label_schema_by_task.values() for label in schema.get_labels(True)
            ],
        )
        self.__validate_all_individual_annotations(
            annotation_scene_rest=annotation_scene_rest,
            project=project,
            label_schema_by_task=label_schema_by_task,
            media_height=media_height,
            media_width=media_width,
        )

    def validate_video_annotation_range(
        self,
        video_annotation_range_rest: dict,
        label_schema: LabelSchema,
        video_total_frames: int,
    ) -> None:
        """
        Validation video annotation range JSON data. Steps:
        1. Schema validation
        2. Range validation
        3. Label validation

        :param video_annotation_range_rest: Video annotation range REST representation
        :param label_schema: Label schema for the project to which the annotation belongs
        :param video_total_frames: Number of frames of the video
        """
        # Schema validation
        self.__validate_video_annotation_range_against_schema(video_annotation_range_rest=video_annotation_range_rest)

        # Range validation
        self.__validate_ranges_boundaries(
            video_annotation_range_rest=video_annotation_range_rest,
            video_total_frames=video_total_frames,
        )

        # Label validation
        self.__validate_all_labels_exist(
            labels_to_check=self.__get_label_ids_from_video_annotation_range(
                video_annotation_range_rest=video_annotation_range_rest
            ),
            existing_labels=[label.id_ for label in label_schema.get_labels(True)],
        )

    def __validate_scene_against_schema(
        self,
        annotation_scene_rest: dict,
        media_identifier: MediaIdentifierEntity,
    ):
        """
        Validate the given annotation scene against the appropriate schema,
        determined by its relative media type.

        Note: the presence of 'oneOf' in the shape schema produces
        misleading error messages when the shape type is valid but some properties
        are missing or invalid; if so, we validate again, now against the
        shape-specific schema, in order to polish the exception message.

        :param annotation_scene_rest: annotation json data
        :param media_identifier: MediaIdentifierEntity used to identify the media the annotation is posted to
        :raises jsonschema.exceptions.ValidationError when data doesn't match the yaml schema
        :raises BadRequestException when annotation_scene_rest is empty or when media is not an image or video
        """
        if not annotation_scene_rest:
            raise BadRequestException("Server received empty annotation data. It cannot be empty.")
        try:
            if isinstance(media_identifier, VideoFrameIdentifier):
                jsonschema.validate(annotation_scene_rest, self.video_frame_annotation_schema)
            elif isinstance(media_identifier, ImageIdentifier):
                jsonschema.validate(annotation_scene_rest, self.image_annotation_schema)
            else:
                raise BadRequestException("Only images or video frames can be annotated.")
        except jsonschema.exceptions.ValidationError:
            # If the validation failed because there was something wrong with the "annotations" list, we raise the
            # original exception because the jsonschema error message is sufficiently informative.
            if ANNOTATIONS not in annotation_scene_rest or not isinstance(annotation_scene_rest[ANNOTATIONS], list):
                raise
            for ann in annotation_scene_rest[ANNOTATIONS]:
                # If the validation failed because of something wrong in the shape, we validate for that specific shape.
                self.__validate_shape_against_schema(shape=ann[SHAPE])
            # If the shapes were not the problem, raise the original exception
            raise

    def __validate_shape_against_schema(self, shape: dict):
        """
        Validates that a shape dictionary conforms to the schema for that shape. This method is used when the
        full annotation schema validation found something wrong: we add shape-specific checks to improve the error
        message. In the case that too many points are provided or a shape is out of bounds, we add custom error
        messages. In all other cases, the original exception is sufficient and we raise back to that exception level.

        :param shape: Shape dictionary as provided by the user
        :raises: BadRequestException for specific error cases
        :raises: jsonschema.exceptions.ValidationError for general error cases found by jsonschema
        """
        shape_type = shape[TYPE]
        self.__validate_shape_type(shape_type=shape_type)

        try:
            jsonschema.validate(shape, self.shapes_schemas[shape_type])
        except jsonschema.exceptions.ValidationError as e:
            if e.validator in ["minimum"]:
                raise BadRequestException(f"One or more {shape_type} shapes have invalid {e.path[0]}: {e.message}.")
            if e.validator == "maxItems":
                raise BadRequestException(
                    f"Too many points in annotation - requested annotation had {str(len(e.instance))} points but the "
                    f"maximum is {str(MAX_POLYGON_POINTS)}."
                )
            raise

    def __validate_shape_type(self, shape_type: str):
        """
        Checks if the shape type is valid

        :param shape_type: str
        :raises BadRequestException when shape type is not valid
        """
        if shape_type not in self.shapes_schemas:
            raise BadRequestException(
                f"Shape type {shape_type} is not valid. Valid shape types are:"
                f" {str([sh_type.name for sh_type in RestShapeType])}"
            )

    def __validate_shape_bounds(self, shape: dict, media_height: int, media_width: int):
        """
        Validates that the annotation shape is not out of bounds.
        - For a rectangle, x+width and y+height cannot exceed 1.
        - For an ellipse, it's validated that the ellipse does not intersect the outside bounds of the image.
        - For a polygon, all out-of-bounds possibilities are already caught by the schema validation.

        :param shape: REST view of the Shape to validate
        :raises BadRequestException for REST views of shapes that are out of bounds
        """
        shape_type = shape[TYPE]

        if shape_type == RestShapeType.RECTANGLE.name:
            self.__validate_rectangle_shape_bounds(shape=shape, media_width=media_width, media_height=media_height)

        if shape_type == RestShapeType.ELLIPSE.name:
            self.__validate_ellipse_shape_bounds(shape=shape, media_width=media_width, media_height=media_height)

        if shape_type == RestShapeType.ROTATED_RECTANGLE.name:
            self.__validate_rotated_rectangle_shape_bounds(
                shape=shape, media_width=media_width, media_height=media_height
            )

        if shape_type == RestShapeType.POLYGON.name:
            self.__validate_polygon_shape_bounds(shape=shape, media_width=media_width, media_height=media_height)

    def __validate_rectangle_shape_bounds(self, shape: dict, media_width: int, media_height: int):
        """
        Checks if the shape type rectangle is out of bounds

         :param shape: REST view of the Shape to validate
         :param media_height: height of the media
        :param media_width: width of the media
         :raises BadRequestException when rectangle is out of bounds
        """
        if shape[X] + shape[WIDTH] > media_width or shape[Y] + shape[HEIGHT] > media_height:
            raise BadRequestException(
                f"Shape out of bounds for annotation with type {shape[TYPE]} and dimensions "
                f"x={shape[X]}, y={shape[Y]}, width={shape[WIDTH]}, height={shape[HEIGHT]}"
            )

    def __validate_ellipse_shape_bounds(self, shape: dict, media_width: int, media_height: int) -> None:
        """
        Checks if the shape type ellipse is out of bounds. An ellipse is out of bounds if it does not have enough
        pixels that fall within the image.

        :param shape: REST view of the Shape to validate
        :param media_height: height of the media
        :param media_width: width of the media
        :raises BadRequestException when ellipse is out of bounds
        """
        x1 = float(shape[X]) / media_width
        y1 = float(shape[Y]) / media_height
        width = float(shape[WIDTH]) / media_width
        height = float(shape[HEIGHT]) / media_height
        ellipse_shape = Ellipse(x1=x1, y1=y1, x2=x1 + width, y2=y1 + height)
        full_rectangle = Rectangle.generate_full_box()
        intersection_area = full_rectangle._as_shapely_polygon().intersection(ellipse_shape._as_shapely_polygon()).area
        if intersection_area * (media_width * media_height) < MINIMUM_PIXELS_FOR_ANNOTATION:
            raise BadRequestException(
                f"Shape out of bounds for annotation with type {shape[TYPE]} and dimensions "
                f"x={shape[X]}, y={shape[Y]}, width={shape[WIDTH]}, height={shape[HEIGHT]}: "
                f"this shape needs to have at least {MINIMUM_PIXELS_FOR_ANNOTATION} pixels within the image."
            )

    def __validate_rotated_rectangle_shape_bounds(self, shape: dict, media_width: int, media_height: int) -> None:
        """
        Checks if the shape type rotated rectangle is out of bounds. A rotated rectangle is out of bounds if it does
        not have enough pixels that fall within the image.

        :param shape: REST view of the Shape to validate
        :param media_height: height of the media
        :param media_width: width of the media
        :raises BadRequestException when the rotated rectangle is out of bounds
        """
        rotated_rectangle_shape = self.__create_rotated_rectangle_polygon(
            rotated_rectangle_data=shape,
            media_width=media_width,
            media_height=media_height,
        )
        full_rectangle = Rectangle.generate_full_box()
        intersection_area = (
            full_rectangle._as_shapely_polygon().intersection(rotated_rectangle_shape._as_shapely_polygon()).area
        )
        if intersection_area * (media_width * media_height) < MINIMUM_PIXELS_FOR_ANNOTATION:
            raise BadRequestException(
                f"Shape out of bounds for annotation with type {shape[TYPE]} and dimensions "
                f"x={shape[X]}, y={shape[Y]}, width={shape[WIDTH]}, height={shape[HEIGHT]}, angle={shape[ANGLE]}: "
                f"this shape needs to have at least {MINIMUM_PIXELS_FOR_ANNOTATION} pixels within the image."
            )

    @staticmethod
    def __create_rotated_rectangle_polygon(
        rotated_rectangle_data: dict,
        media_height: int,
        media_width: int,
    ) -> Polygon:
        """
        Creates a rotated rectangle shape from a REST representation. For justification of the method, see
        AnnotationRESTViews.rotated_rectangle_shape_from_rest.

        :param rotated_rectangle_data: the REST representation of a rotated rectangle
        :param media_height: The height in pixels of the media
        :param media_width: The width in pixels of the media
        :return: Polygon representation of the Rotated Rectangle object
        """
        x_center = float(rotated_rectangle_data[X])
        y_center = float(rotated_rectangle_data[Y])
        width = float(rotated_rectangle_data[WIDTH])
        height = float(rotated_rectangle_data[HEIGHT])
        angle = math.radians(rotated_rectangle_data[ANGLE])

        points = [
            Point(
                x_center + (width / 2 * math.cos(angle)) - (height / 2 * math.sin(angle)),
                y_center + (width / 2 * math.sin(angle)) + (height / 2 * math.cos(angle)),
            ),
            Point(
                x_center - (width / 2 * math.cos(angle)) - (height / 2 * math.sin(angle)),
                y_center - (width / 2 * math.sin(angle)) + (height / 2 * math.cos(angle)),
            ),
            Point(
                x_center - (width / 2 * math.cos(angle)) + (height / 2 * math.sin(angle)),
                y_center - (width / 2 * math.sin(angle)) - (height / 2 * math.cos(angle)),
            ),
            Point(
                x_center + (width / 2 * math.cos(angle)) + (height / 2 * math.sin(angle)),
                y_center + (width / 2 * math.sin(angle)) - (height / 2 * math.cos(angle)),
            ),
        ]
        points = [Point(p.x / media_width, p.y / media_height) for p in points]
        return Polygon(
            points=points,
        )

    def __validate_polygon_shape_bounds(self, shape: dict, media_width: int, media_height: int):
        """
        Checks if the shape type ellipse is out of bounds

        :param shape: REST view of the Shape to validate
        :param media_height: height of the media
        :param media_width: width of the media
        :raises BadRequestException when ellipse is out of bunds
        """
        for point in shape[POINTS]:
            if point[X] > media_width or point[Y] > media_height:
                raise BadRequestException(f"Polygon point out of bounds with coordinates x={point[X]}, y={point[Y]}")

    @staticmethod
    def __validate_all_labels_exist(labels_to_check: SequenceOrSet[ID], existing_labels: SequenceOrSet[ID]) -> None:
        """
        Check that all the given labels actually exist in the label schema

        :param labels_to_check: IDs of the labels to check
        :param existing_labels: IDs of the labels in the project
        :raises LabelNotFoundException when labels are not found
        """
        not_found_labels = {label_id for label_id in labels_to_check if label_id not in existing_labels}
        if not_found_labels:
            raise LabelNotFoundException(label_id=next(iter(not_found_labels)))

    def __get_label_ids_from_annotation_scene(self, annotation_scene_rest: dict) -> set[ID]:
        """
        Gets label ids from given annotation scene

        :param annotation_scene_rest: annotation json data
        :return type: Set[ID]
        """
        return {
            ID(label_rest[ID_])
            for annotation_rest in annotation_scene_rest[ANNOTATIONS]
            for label_rest in annotation_rest[LABELS]
        }

    def __validate_all_individual_annotations(
        self,
        annotation_scene_rest: dict,
        project: Project,
        label_schema_by_task: dict[ID, LabelSchemaView],
        media_width: int,
        media_height: int,
    ):
        """
        Validate all the annotations in the scene, one by one.

        Steps:
          1. Validate the shape (e.g. not out of bounds)
          2. Validate labels exclusivity
          3. Validate that the annotation is suitable for the task
          4. Validate that the annotations are unique (ID)

        :param annotation_scene_rest: annotation json data
        :param project: project for which to validate the annotation scene
        :param label_schema_by_task: Dictionary mapping each trainable task node ID to its label schema
        :param media_height: height of the media
        :param media_width: width of the media
        """
        labels_by_task = {
            task_node_id: label_schema.get_labels(include_empty=True)
            for task_node_id, label_schema in label_schema_by_task.items()
        }
        for annotation_rest in annotation_scene_rest[ANNOTATIONS]:
            self.__validate_shape_bounds(
                shape=annotation_rest[SHAPE],
                media_height=media_height,
                media_width=media_width,
            )

            self.__validate_labels_exclusivity(
                annotation_rest=annotation_rest,
                label_schema_by_task=label_schema_by_task,
            )

            self.__validate_annotation_compatibility_with_tasks(
                annotation_scene_rest=annotation_scene_rest,
                annotation_rest=annotation_rest,
                project=project,
                media_width=media_width,
                media_height=media_height,
                labels_by_task=labels_by_task,  # type: ignore
            )
            self.__validate_annotations_uniqueness(annotation_scene_rest=annotation_scene_rest)

    def __validate_labels_exclusivity(
        self, annotation_rest: dict, label_schema_by_task: dict[ID, LabelSchemaView]
    ) -> None:
        """
        Validates that the annotation does not contain mutually exclusive labels.

        :param annotation_rest: annotation json data
        :param label_schema_by_task: Dictionary mapping each trainable task node ID to its label schema
        :raises ConflictingExclusiveLabelsException when groups with conflict are present
        """
        project_groups = []
        label_map: dict[ID, Label] = {}
        label_schema_map: dict[ID, LabelSchemaView] = {}
        for label_schema in label_schema_by_task.values():
            for label in label_schema.get_all_labels():
                label_map[label.id_] = label
                label_schema_map[label.id_] = label_schema
            project_groups += label_schema.get_groups(include_empty=True)

        labels_ids_in_annotation: set[ID] = set()
        for label_rest in annotation_rest[LABELS]:
            label_id = ID(label_rest[ID_])
            label = label_map[label_id]
            label_schema = label_schema_map[label_id]
            # Add the label ids including their ancestors
            family_labels = label_schema.label_tree.get_ancestors(label)
            labels_ids_in_annotation.update([label.id_ for label in family_labels])

        found_labels_by_excl_group: dict[str, set[str]] = {
            group.name: {
                group_label.name for group_label in group.labels if group_label.id_ in labels_ids_in_annotation
            }
            for group in project_groups
            if group.group_type == LabelGroupType.EXCLUSIVE
        }
        excl_groups_with_multiple_labels = dict(
            filter(lambda item: len(item[1]) > 1, found_labels_by_excl_group.items())
        )
        if excl_groups_with_multiple_labels:
            raise ConflictingExclusiveLabelsException(groups_with_conflicts=excl_groups_with_multiple_labels)

    def __validate_annotation_compatibility_with_tasks(
        self,
        annotation_scene_rest: dict,
        annotation_rest: dict,
        project: Project,
        media_height: int,
        media_width: int,
        labels_by_task: dict[ID, list[Label]],
    ):
        """
        Validate that the annotation is compatible with the task nodes.

        :param annotation_scene_rest: annotation json data
        :param annotation_rest: given annotation that needs to be validated
        :param project: project for which to validate the annotation scene
        :param media_height: height of the media
        :param media_width: width of the media
        :param labels_by_task: Dictionary mapping each trainable task node ID to its labels
        :raises NotImplementedError when a task is present that can't be annotated
        """
        previous_task: TaskNode | None = None
        previous_task_labels: list[Label] = []
        for task in project.get_trainable_task_nodes():
            task_labels = labels_by_task[task.id_]
            if task.task_properties.is_global:
                self.__validate_global_annotation(
                    annotation_rest=annotation_rest,
                    task=task,
                    previous_task=previous_task,
                    task_labels=task_labels,
                    previous_task_labels=previous_task_labels,
                    media_height=media_height,
                    media_width=media_width,
                )
            elif task.task_properties.task_type.is_local:
                self.__validate_local_annotation(
                    annotation_rest=annotation_rest,
                    task=task,
                    previous_task=previous_task,
                    annotation_scene_rest=annotation_scene_rest,
                    task_labels=task_labels,
                    previous_task_labels=previous_task_labels,
                    media_width=media_width,
                    media_height=media_height,
                )
            else:
                raise NotImplementedError(
                    f"Cannot create annotation for task {task.title} with task type "
                    f"{task.task_properties.task_type}: annotating is only "
                    f"possible for the following tasks: "
                    f"{[task.name for task in TaskType if task.is_trainable]}. "
                    f" Task Node ID: `{task.id_}`."
                )
            previous_task = task
            previous_task_labels = task_labels

    def __validate_annotations_uniqueness(self, annotation_scene_rest: dict):
        """
        Checks if duplicate annotation ids are present

        :param annotation_scene_rest: annotation json data
         :raises DuplicatedAnnotationIDException when a duplicate annotation ids are present
        """
        annotation_ids = [
            annotation_rest[ID_] for annotation_rest in annotation_scene_rest[ANNOTATIONS] if ID_ in annotation_rest
        ]
        annotation_ids_set = set(annotation_ids)
        if not len(annotation_ids) == len(annotation_ids_set):
            raise DuplicatedAnnotationIDException(
                f"Using duplicate annotation IDs is not allowed - the following IDs were used "
                f"multiple times: {[id_ for id_ in annotation_ids_set if annotation_ids.count(id_) > 1]}"
            )

    @staticmethod
    def __validate_global_annotation(
        annotation_rest: dict,
        task: TaskNode,
        previous_task: TaskNode | None,
        task_labels: list[Label],
        media_height: int,
        media_width: int,
        previous_task_labels: list[Label] | None = None,
    ) -> None:
        """
        Validates that an annotation for a global task is valid. Checks the following rules:
        - No annotation is allowed to have both empty and non-empty annotations for the same task
        - If the task is the first task, global annotations must be a full box.
        - If the task is not the first task, the annotation must also contain labels for the previous task.

        :param annotation_rest: REST view of the annotation
        :param task: TaskNode for which the annotation is checked to be valid
        :param previous_task: TaskNode that precedes the task that is being checked
        :param task_labels: Labels of the task node
        :param media_height: height of the media
        :param media_width: width of the media
        :param previous_task_labels: labels of the previous task node

        :return: Skip making checks and return if there are no annotations in the REST view for the task
        :raises BadRequestException: if the annotation is not valid
        """
        annotation_label_ids = {ID(label_rest[ID_]) for label_rest in annotation_rest[LABELS]}
        annotation_labels_current_task = [label for label in task_labels if label.id_ in annotation_label_ids]
        if len(annotation_labels_current_task) == 0:
            # If the annotation contains no labels for this task, return without doing validation for this task
            return

        # Validate that annotations don't have both empty and non-empty labels for the same task
        empty_labels_in_annotation = {label for label in annotation_labels_current_task if label.is_empty}
        non_empty_labels_in_annotation = {label for label in annotation_labels_current_task if not label.is_empty}
        if bool(empty_labels_in_annotation) and bool(non_empty_labels_in_annotation):
            raise BadRequestException(
                f"Cannot create annotation that has both empty label with ID "
                f"{next(iter(empty_labels_in_annotation)).id_} and non-empty label with ID "
                f"{next(iter(non_empty_labels_in_annotation)).id_} for task {task.id_}"
            )

        # Validate that global annotations for the first task use a full box shape
        if previous_task is None and annotation_rest[SHAPE] != AnnotationRESTViews.generate_full_box_rest(
            media_height=media_height, media_width=media_width
        ):
            raise BadRequestException(
                "Only full box rectangle annotations are allowed for a classification label on a full image."
            )

        # Validate that global annotations for a cropped task contain a label for the previous task
        if (
            previous_task is not None
            and previous_task_labels is not None
            and not any(label.id_ in annotation_label_ids for label in previous_task_labels)
        ):
            raise BadRequestException("Annotation for a global task is missing a label for the preceding task.")

    @staticmethod
    def __validate_local_annotation(  # noqa: C901, PLR0913
        annotation_rest: dict,
        task: TaskNode,
        previous_task: TaskNode | None,
        annotation_scene_rest: dict,
        task_labels: list[Label],
        media_width: int,
        media_height: int,
        previous_task_labels: list[Label] | None = None,
    ) -> None:
        """
        Validates that an annotation for a local task is valid. Checks the following rules:
        - If the annotation contains an empty label, and it's the first task, the annotation must be a full box
        - If the annotation contains an empty label, and it is not the first task, a label from the previous task should
          be present
        - If the annotation contains an empty label, no other annotation for this task may intersect with the empty
          label.
        - If the task is (rotated) detection, shape must be (rotated) rectangle

        :param annotation_rest: REST view of the annotation
        :param task: TaskNode for which the annotation is checked to be valid
        :param previous_task: TaskNode that precedes the task that is being checked
        :param annotation_scene_rest: REST view of the entire annotation scene
        :param task_labels: Labels of the task node
        :param previous_task_labels: labels of the previous task node
        :raises BadRequestException: if the annotation is not valid
        """
        annotation_label_ids = {ID(label_rest[ID_]) for label_rest in annotation_rest[LABELS]}
        annotation_labels_current_task = [label for label in task_labels if label.id_ in annotation_label_ids]
        if len(annotation_labels_current_task) == 0:
            # If the annotation contains no labels for this task, return without doing validation for this task
            return

        # Validate that if the task is a local anomaly task, it contains only one of the labels (it's not allowed to
        # have both the normal and the anomalous label).
        if task.task_properties.is_anomaly and not task.task_properties.is_global:
            annotation_scene_label_ids: set[ID] = set()
            for annotation_rest in annotation_scene_rest[ANNOTATIONS]:  # noqa: PLR1704
                for label_rest in annotation_rest[LABELS]:
                    annotation_scene_label_ids.add(ID(label_rest[ID_]))
            task_label_ids = {label.id_ for label in task_labels}
            if len(annotation_scene_label_ids.intersection(task_label_ids)) > 1:
                raise BadRequestException(
                    "It is not allowed to have both the normal and the anomalous label in an annotation scene for "
                    "local anomaly tasks."
                )

        is_empty_annotation = any(label.is_empty for label in annotation_labels_current_task)
        if is_empty_annotation:
            # Validate that the empty label for the first task is a full box
            if previous_task is None and annotation_rest[SHAPE] != AnnotationRESTViews.generate_full_box_rest(
                media_height=media_height, media_width=media_width
            ):
                raise BadRequestException("Empty label for the first task must be a full box rectangle.")

            # Validate that the empty label for a cropped task contains a label of the previous task
            if (
                previous_task is not None
                and previous_task_labels is not None
                and not any(label.id_ in annotation_label_ids for label in previous_task_labels)
            ):
                raise BadRequestException("Empty annotation for a task is missing a label for the preceding task.")

            # Validate that no non-empty annotations coincide with the empty box
            empty_shape = AnnotationRESTViews.shape_from_rest(
                annotation_rest[SHAPE],
                media_height=media_height,
                media_width=media_width,
            )
            non_empty_label_ids = {label.id_ for label in task_labels if not label.is_empty}
            for annotation in annotation_scene_rest[ANNOTATIONS]:
                if any(label_rest[ID_] in non_empty_label_ids for label_rest in annotation[LABELS]):
                    shape = AnnotationRESTViews.shape_from_rest(
                        annotation[SHAPE],
                        media_height=media_height,
                        media_width=media_width,
                    )
                    if shape.intersects(empty_shape):
                        raise BadRequestException(
                            "Not allowed to create annotation that overlaps with an empty box annotation."
                        )

        AnnotationRestValidator._validate_shape_type(annotation_rest=annotation_rest, task=task)

    @staticmethod
    def _validate_shape_type(annotation_rest: dict, task: TaskNode) -> None:
        """
        Validate that the shape is a rectangle in the case of a detection task
        Validate that the shape is either a rectangle or a rotated rectangle in the case of a rotated detection task
        - if the shape is a rectangle, then convert it to a rotated rectangle with an angle of 0

        :param task: TaskNode for which the annotation is created
        :param annotation_rest: REST dict of the annotation
        :raises BadRequestException: if the shape is not valid
        """
        task_type = task.task_properties.task_type
        annotation_type = annotation_rest[SHAPE][TYPE]
        if task_type == TaskType.DETECTION and annotation_type != RestShapeType.RECTANGLE.name:
            raise BadRequestException("Only rectangle annotations are allowed for a detection task.")
        if task_type == TaskType.ROTATED_DETECTION:
            if annotation_type == RestShapeType.RECTANGLE.name:
                annotation_rest[SHAPE] = AnnotationRESTViews.rest_rectangle_to_rest_rotated_rectangle(
                    annotation_rest[SHAPE]
                )
                return
            if annotation_type != RestShapeType.ROTATED_RECTANGLE.name:
                raise BadRequestException(
                    "Only rectangle and rotated rectangle annotations are allowed for a rotated detection task."
                )

    def __validate_video_annotation_range_against_schema(self, video_annotation_range_rest: dict) -> None:
        try:
            jsonschema.validate(video_annotation_range_rest, self.video_range_schema)
        except jsonschema.exceptions.ValidationError as e:
            if e.validator in ["minimum"]:
                raise BadRequestException("Frame indices cannot be negative.")
            raise

    @staticmethod
    def __validate_ranges_boundaries(video_annotation_range_rest: dict, video_total_frames: int) -> None:
        """
        Validate the boundaries of all ranges with respect to the video length.

        :param video_annotation_range_rest: video annotation range REST data
        :param video_total_frames: number of frames of the video
        :raises BadRequestException: if any of the ranges is invalid
        """
        for range_labels_rest in video_annotation_range_rest[RANGE_LABELS]:
            start_frame = range_labels_rest[START_FRAME]
            end_frame = range_labels_rest[END_FRAME]
            if start_frame < 0:
                raise BadRequestException(f"'start_frame' ({start_frame}) cannot be negative")
            if end_frame < start_frame:
                raise BadRequestException(
                    f"'end_frame' ({end_frame}) cannot be smaller than 'start_frame' ({start_frame})"
                )
            if end_frame >= video_total_frames:
                raise BadRequestException(
                    f"The 'end_frame' ({end_frame}) exceeds the video length ({video_total_frames} frames)"
                )

    @staticmethod
    def __get_label_ids_from_video_annotation_range(
        video_annotation_range_rest: dict,
    ) -> set[ID]:
        """
        Get the set of label IDs contained in a video annotation range.

        :param video_annotation_range_rest: video annotation range REST data
        :return type: Set of label ids
        """
        return {
            ID(label_id_str)
            for range_labels_rest in video_annotation_range_rest[RANGE_LABELS]
            for label_id_str in range_labels_rest[LABEL_IDS]
        }

# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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
import random
from collections import Counter
from dataclasses import dataclass
from uuid import uuid4

from behave import then, when
from behave.runner import Context
from geti_client import (
    AnnotationsApi,
    CreateImageAnnotationRequest,
    CreateImageAnnotationRequestAnnotationsInner,
    CreateImageAnnotationRequestAnnotationsInnerLabelsInner,
    CreateImageAnnotationRequestAnnotationsInnerShape,
    CreateImageAnnotationRequestMediaIdentifier,
    CreateVideoFrameAnnotationRequest,
    CreateVideoFrameAnnotationRequestAnnotationsInner,
    CreateVideoFrameAnnotationRequestAnnotationsInnerLabelsInner,
    CreateVideoFrameAnnotationRequestMediaIdentifier,
    Ellipse,
    Keypoint,
    Point,
    Polygon,
    Rectangle,
    RotatedRectangle,
)
from static_definitions import PROJECT_TYPE_TO_EMPTY_LABEL_NAME_MAPPING, ProjectType


@dataclass
class Annotation:
    """Simplified representation of an annotation (shape and labels)"""

    shape: Rectangle | Polygon | Ellipse | RotatedRectangle | Keypoint
    label_ids: list[str]


def _generate_random_bbox_coords(media_width: int, media_height: int, empty_label: bool) -> tuple[int, int, int, int]:
    if empty_label:
        return 0, 0, media_width, media_height

    x = random.randint(0, media_width - 1)
    y = random.randint(0, media_height - 1)
    w = random.randint(1, media_width - x)
    h = random.randint(1, media_height - y)

    return x, y, w, h


def _generate_random_rotated_bbox_coords(media_width: int, media_height: int) -> tuple[int, int, int, int, float]:
    x, y, w, h = _generate_random_bbox_coords(media_width=media_width, media_height=media_height, empty_label=False)
    angle = random.uniform(-180.0, 180.0)

    return x, y, w, h, angle


def _generate_random_polygon_coords(media_width: int, media_height: int) -> list[tuple[int, int]]:
    num_points = random.randint(3, 10)
    return [(random.randint(0, media_width - 1), random.randint(0, media_height - 1)) for _ in range(num_points)]


def _generate_random_keypoint_coords(media_width: int, media_height: int) -> tuple[int, int]:
    return random.randint(0, media_width - 1), random.randint(0, media_height - 1)


def _annotate_image_or_frame(  # noqa: C901, PLR0912, PLR0915
    context: Context,
    media_type: str,
    media_name: str,
    labels: list[str],
    frame_index: int | None = None,
) -> None:
    annotations_api: AnnotationsApi = context.annotations_api

    media_details = context._media_info_by_name[media_name]
    media_width = media_details.media_information.width
    media_height = media_details.media_information.height
    match media_type:
        case "image":
            media_identifier = CreateImageAnnotationRequestMediaIdentifier(
                image_id=media_details.id,
                type="image",
            )
            create_annotations_inner = CreateImageAnnotationRequestAnnotationsInner
            create_annotation_labels_inner = CreateImageAnnotationRequestAnnotationsInnerLabelsInner
        case "video":
            media_identifier = CreateVideoFrameAnnotationRequestMediaIdentifier(
                video_id=media_details.id,
                type="video_frame",
                frame_index=frame_index,
            )
            create_annotations_inner = CreateVideoFrameAnnotationRequestAnnotationsInner
            create_annotation_labels_inner = CreateVideoFrameAnnotationRequestAnnotationsInnerLabelsInner
        case _:
            raise ValueError(f"Unsupported media type: {media_type}")

    annotations: list[
        CreateImageAnnotationRequestAnnotationsInner | CreateVideoFrameAnnotationRequestAnnotationsInner
    ] = []
    label_req_obj_by_name = {
        label_name: create_annotation_labels_inner(id=context.label_info_by_name[label_name].id)
        for label_name in labels
    }
    match context.project_type:
        case (
            ProjectType.MULTICLASS_CLASSIFICATION
            | ProjectType.MULTILABEL_CLASSIFICATION
            | ProjectType.HIERARCHICAL_CLASSIFICATION
            | ProjectType.ANOMALY_DETECTION
        ):
            if context.project_type in [
                ProjectType.MULTICLASS_CLASSIFICATION,
                ProjectType.ANOMALY_DETECTION,
            ]:
                assert len(labels) == 1, f"{context.project_type} projects support only one label"
            if context.project_type == ProjectType.ANOMALY_DETECTION:
                assert labels[0] in ("Normal", "Anomalous"), f"Invalid label {labels[0]} for anomaly detection project"
            annotations = [
                create_annotations_inner(
                    id=str(uuid4()),
                    shape=CreateImageAnnotationRequestAnnotationsInnerShape(
                        Rectangle(
                            type="RECTANGLE",
                            x=0,
                            y=0,
                            width=media_width,
                            height=media_height,
                        )
                    ),
                    labels=[label_req_obj_by_name[label_name] for label_name in labels],  # all labels to the same bbox
                )
            ]
        case ProjectType.DETECTION:
            for label_name in labels:  # create a bbox for each label
                x, y, w, h = _generate_random_bbox_coords(
                    media_width=media_width,
                    media_height=media_height,
                    empty_label=context.label_info_by_name[label_name].is_empty,
                )
                annotations.append(
                    create_annotations_inner(
                        id=str(uuid4()),
                        shape=CreateImageAnnotationRequestAnnotationsInnerShape(
                            Rectangle(type="RECTANGLE", x=x, y=y, width=w, height=h)
                        ),
                        labels=[label_req_obj_by_name[label_name]],
                    )
                )
        case ProjectType.ORIENTED_DETECTION:  # create a rotated bbox for each label (or full-image box for empty label)
            for label_name in labels:
                if context.label_info_by_name[label_name].is_empty:
                    x, y, w, h = 0, 0, media_width, media_height
                    shape = CreateImageAnnotationRequestAnnotationsInnerShape(
                        Rectangle(type="RECTANGLE", x=x, y=y, width=w, height=h)
                    )
                else:
                    x, y, w, h, angle = _generate_random_rotated_bbox_coords(
                        media_width=media_width, media_height=media_height
                    )
                    shape = CreateImageAnnotationRequestAnnotationsInnerShape(
                        RotatedRectangle(
                            type="ROTATED_RECTANGLE",
                            x=x,
                            y=y,
                            width=w,
                            height=h,
                            angle=angle,
                        )
                    )
                annotations.append(
                    create_annotations_inner(
                        id=str(uuid4()),
                        shape=shape,
                        labels=[label_req_obj_by_name[label_name]],
                    )
                )
        case ProjectType.SEMANTIC_SEGMENTATION | ProjectType.INSTANCE_SEGMENTATION:
            for label_name in labels:  # create a polygon for each label (or a full-image rectangle for empty label)
                if context.label_info_by_name[label_name].is_empty:
                    shape = CreateImageAnnotationRequestAnnotationsInnerShape(
                        Rectangle(
                            type="RECTANGLE",
                            x=0,
                            y=0,
                            width=media_width,
                            height=media_height,
                        )
                    )
                else:
                    points = [
                        Point(x=x, y=y)
                        for x, y in _generate_random_polygon_coords(media_width=media_width, media_height=media_height)
                    ]
                    shape = CreateImageAnnotationRequestAnnotationsInnerShape(Polygon(type="POLYGON", points=points))
                annotations.append(
                    create_annotations_inner(
                        id=str(uuid4()),
                        shape=shape,
                        labels=[label_req_obj_by_name[label_name]],
                    )
                )
        case ProjectType.KEYPOINT_DETECTION:
            raise NotImplementedError("Keypoint annotations are not yet supported")
            # for label_name in labels:
            #     x, y = _generate_random_keypoint_coords(media_width=media_width, media_height=media_height)
            #     annotations.append(
            #         create_annotations_inner(
            #             id=str(uuid4()),
            #             shape=CreateImageAnnotationRequestAnnotationsInnerShape(
            #                 Keypoint(type="KEYPOINT", x=x, y=y, is_visible=random.choice([True, False]))
            #             ),
            #             labels=[label_req_obj_by_name[label_name]],
            #         )
            #     )
        case ProjectType.TASK_CHAIN_DETECTION_CLASSIFICATION:
            x, y, w, h = _generate_random_bbox_coords(
                media_width=media_width,
                media_height=media_height,
                empty_label=context.label_info_by_name[labels[0]].is_empty,
            )
            annotations.append(
                create_annotations_inner(
                    id=str(uuid4()),
                    shape=CreateImageAnnotationRequestAnnotationsInnerShape(
                        Rectangle(type="RECTANGLE", x=x, y=y, width=w, height=h)
                    ),
                    labels=[label_req_obj_by_name[label_name] for label_name in labels],
                )
            )
        case ProjectType.TASK_CHAIN_DETECTION_SEGMENTATION:
            x, y, w, h = _generate_random_bbox_coords(
                media_width=media_width,
                media_height=media_height,
                empty_label=context.label_info_by_name[labels[0]].is_empty,
            )
            annotations.append(
                create_annotations_inner(
                    id=str(uuid4()),
                    shape=CreateImageAnnotationRequestAnnotationsInnerShape(
                        Rectangle(type="RECTANGLE", x=x, y=y, width=w, height=h)
                    ),
                    labels=[label_req_obj_by_name[labels[0]]],
                )
            )
            if len(labels) > 1:
                for label_name in labels[1:]:
                    points = [
                        Point(x=x + sx, y=y + sy)
                        for sx, sy in _generate_random_polygon_coords(media_width=w, media_height=h)
                    ]
                    shape = CreateImageAnnotationRequestAnnotationsInnerShape(Polygon(type="POLYGON", points=points))
                    annotations.append(
                        create_annotations_inner(
                            id=str(uuid4()),
                            shape=shape,
                            labels=[label_req_obj_by_name[label_name]],
                        )
                    )
        case _:
            raise NotImplementedError(f"Implementation not yet available for project type {context.project_type}")

    match media_type:
        case "image":
            annotations_api.create_image_annotation(
                organization_id=context.organization_id,
                workspace_id=context.workspace_id,
                project_id=context.project_id,
                dataset_id=context.dataset_id,
                image_id=media_details.id,
                create_image_annotation_request=CreateImageAnnotationRequest(
                    media_identifier=media_identifier,
                    annotations=annotations,
                ),
            )
        case "video":
            annotations_api.create_video_frame_annotation(
                organization_id=context.organization_id,
                workspace_id=context.workspace_id,
                project_id=context.project_id,
                dataset_id=context.dataset_id,
                video_id=media_details.id,
                frame_index=frame_index,
                create_video_frame_annotation_request=CreateVideoFrameAnnotationRequest(
                    media_identifier=media_identifier,
                    annotations=annotations,
                ),
            )
        case _:
            raise ValueError(f"Unsupported media type: {media_type}")


def _get_image_or_frame_annotations(
    context: Context, media_type: str, media_name: str, frame_index: int | None = None
) -> list[Annotation]:
    annotations_api: AnnotationsApi = context.annotations_api
    annotations: list[Annotation] = []

    if media_type == "image":
        ann_response = annotations_api.get_image_annotation(
            organization_id=context.organization_id,
            workspace_id=context.workspace_id,
            project_id=context.project_id,
            dataset_id=context.dataset_id,
            image_id=context._media_info_by_name[media_name].id,
            annotation_id="latest",
        )
    elif media_type == "video":
        ann_response = annotations_api.get_video_frame_annotation(
            organization_id=context.organization_id,
            workspace_id=context.workspace_id,
            project_id=context.project_id,
            dataset_id=context.dataset_id,
            video_id=context._media_info_by_name[media_name].id,
            frame_index=frame_index,
            annotation_id="latest",
        )
    else:
        raise ValueError(f"Unsupported media type: {media_type}")
    for ann in ann_response.annotations:
        shape = ann.shape.actual_instance
        label_ids = [label.id for label in ann.labels]
        annotations.append(Annotation(shape=shape, label_ids=label_ids))
    return annotations


@when("the user annotates the image '{image_name}' with label '{label_name}'")
def step_when_user_annotates_image_with_custom_label(context: Context, image_name: str, label_name: str) -> None:
    _annotate_image_or_frame(context=context, media_type="image", media_name=image_name, labels=[label_name])


@when("the user annotates the image '{image_name}' with labels '{label_names}'")
def step_when_user_annotates_image_with_custom_labels(context: Context, image_name: str, label_names: str) -> None:
    _annotate_image_or_frame(
        context=context,
        media_type="image",
        media_name=image_name,
        labels=label_names.split(", "),
    )


@when("the user annotates the image '{image_name}' with the empty label")
def step_when_user_annotates_image_with_empty_label(context: Context, image_name: str) -> None:
    empty_label_name = PROJECT_TYPE_TO_EMPTY_LABEL_NAME_MAPPING.get(context.project_type)
    labels = [empty_label_name] if empty_label_name else []
    _annotate_image_or_frame(context=context, media_type="image", media_name=image_name, labels=labels)


@when("the user tries to annotate the image '{image_name}' with labels '{label_names}'")
def step_when_user_tries_annotating_image_with_custom_labels(
    context: Context, image_name: str, label_names: str
) -> None:
    try:
        _annotate_image_or_frame(
            context=context,
            media_type="image",
            media_name=image_name,
            labels=label_names.split(", "),
        )
    except Exception as e:
        context.exception = e


@then("the image '{image_name}' has labels '{raw_expected_label_names}'")
def step_then_image_has_expected_labels(context: Context, image_name: str, raw_expected_label_names: str) -> None:
    annotations = _get_image_or_frame_annotations(context=context, media_type="image", media_name=image_name)

    expected_label_names = raw_expected_label_names.split(", ")

    label_info_by_id = {label.id: label for label in context.label_info_by_name.values()}
    found_label_names = [
        label_info_by_id[label_id].name for annotation in annotations for label_id in annotation.label_ids
    ]
    expected_label_names_freq = Counter(expected_label_names)
    found_label_names_freq = Counter(found_label_names)
    assert expected_label_names_freq == found_label_names_freq, (
        f"Expected to find labels with the respective frequency: {expected_label_names_freq}, "
        f"found instead: {found_label_names_freq}"
    )


@then("the image '{image_name}' has label '{expected_label_name}'")
def step_then_image_has_expected_label(context: Context, image_name: str, expected_label_name: str) -> None:
    step_then_image_has_expected_labels(
        context=context,
        image_name=image_name,
        raw_expected_label_names=expected_label_name,
    )


@then("the image '{image_name}' has the empty label")
def step_then_image_has_empty_label(context: Context, image_name: str) -> None:
    empty_label_name = PROJECT_TYPE_TO_EMPTY_LABEL_NAME_MAPPING.get(context.project_type)
    step_then_image_has_expected_label(context=context, image_name=image_name, expected_label_name=empty_label_name)


@when("the user annotates frame {frame_index:d} of the video '{video_name}' with label '{label_name}'")
def step_when_user_annotates_video_frame_with_custom_label(
    context: Context, frame_index: int, video_name: str, label_name: str
) -> None:
    _annotate_image_or_frame(
        context=context,
        media_type="video",
        media_name=video_name,
        frame_index=frame_index,
        labels=[label_name],
    )


@when("the user annotates frame {frame_index:d} of the video '{video_name}' with labels '{label_names}'")
def step_when_user_annotates_video_frame_with_custom_labels(
    context: Context, frame_index: int, video_name: str, label_names: str
) -> None:
    _annotate_image_or_frame(
        context=context,
        media_type="video",
        media_name=video_name,
        frame_index=frame_index,
        labels=label_names.split(", "),
    )


@when("the user annotates frame {frame_index:d} of the video '{video_name}' with the empty label")
def step_when_user_annotates_video_frame_with_empty_label(context: Context, frame_index: int, video_name: str) -> None:
    empty_label_name = PROJECT_TYPE_TO_EMPTY_LABEL_NAME_MAPPING.get(context.project_type)
    labels = [empty_label_name] if empty_label_name else []
    _annotate_image_or_frame(
        context=context,
        media_type="video",
        media_name=video_name,
        frame_index=frame_index,
        labels=labels,
    )


@when("the user tries to annotate frame {frame_index:d} of the video '{video_name}' with labels '{label_names}'")
def step_when_user_tries_annotating_video_frame_with_custom_labels(
    context: Context, frame_index: int, video_name: str, label_names: str
) -> None:
    try:
        _annotate_image_or_frame(
            context=context,
            media_type="video",
            media_name=video_name,
            frame_index=frame_index,
            labels=label_names.split(", "),
        )
    except Exception as e:
        context.exception = e


@then("frame {frame_index:d} of the video '{video_name}' has labels '{raw_expected_label_names}'")
def step_then_video_frame_has_expected_labels(
    context: Context,
    frame_index: int,
    video_name: str,
    raw_expected_label_names: str,
) -> None:
    annotations = _get_image_or_frame_annotations(
        context=context,
        media_type="video",
        media_name=video_name,
        frame_index=frame_index,
    )

    expected_label_names = raw_expected_label_names.split(", ")

    label_info_by_id = {label.id: label for label in context.label_info_by_name.values()}
    found_label_names = [
        label_info_by_id[label_id].name for annotation in annotations for label_id in annotation.label_ids
    ]
    expected_label_names_freq = Counter(expected_label_names)
    found_label_names_freq = Counter(found_label_names)
    assert expected_label_names_freq == found_label_names_freq, (
        f"Expected to find labels with the respective frequency: {expected_label_names_freq}, "
        f"found instead: {found_label_names_freq}"
    )


@then("frame {frame_index:d} of the video '{video_name}' has label '{expected_label_name}'")
def step_then_video_frame_has_expected_label(
    context: Context, frame_index: int, video_name: str, expected_label_name: str
) -> None:
    step_then_video_frame_has_expected_labels(
        context=context,
        video_name=video_name,
        frame_index=frame_index,
        raw_expected_label_names=expected_label_name,
    )


@then("frame {frame_index:d} of the video '{video_name}' has the empty label")
def step_then_video_frame_has_empty_label(context: Context, frame_index: int, video_name: str) -> None:
    empty_label_name = PROJECT_TYPE_TO_EMPTY_LABEL_NAME_MAPPING.get(context.project_type)
    step_then_video_frame_has_expected_label(
        context=context,
        video_name=video_name,
        frame_index=frame_index,
        expected_label_name=empty_label_name,
    )

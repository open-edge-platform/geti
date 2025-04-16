# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import random
from collections.abc import Sequence

import numpy as np
import pytest

from tests.fixtures.values import DefaultImageValues

from sc_sdk.entities.annotation import Annotation
from sc_sdk.entities.label import Domain, Label, NullLabel
from sc_sdk.entities.scored_label import ScoredLabel
from sc_sdk.entities.shapes import Ellipse, Point, Polygon, Rectangle

logger = logging.getLogger(__name__)


@pytest.fixture
def fxt_random_annotated_image_factory():  # noqa: C901
    """
    Factory fixture that generates random images with annotations.

    Takes the following required parameter:
        -   labels: List of Labels to associate with the image. If label names match
                the drawn shapes, the factory will assign the correct label to the
                shapes as annotation. Available shapes are {"rectangle", "triangle",
                "ellipse"}. If the label names do not match, a label will be assigned
                randomly for each shape (for local labels) or each image
                (for global labels)

    Takes the following optional parameters:
        -   image_width: Width of the image to generate
        -   image_height: Height of the image to generate
        -   min_size: minimum dimension for a shape to be drawn in the image
        -   max_size: maximum dimension for a shape to be drawn in the image
        -   max_shapes: maximum number of shapes to draw
        -   intensity_range: range of values to sample pixel values from for the drawn
                shapes
        -   shape: name of the shape to draw. If not specified, shape is chosen
                randomly from {"rectangle", "triangle" , "ellipse"}

    Returns a Tuple containing:
        - image : uint8 array
            An image with the fitted shapes.
        - annotations : list
            A list of annotations, depending on label domain this can contain either:
            - A single annotation covering the whole image (for global domains)
            - Multiple annotations, one for each shape in the image
    """

    def _annotated_image_factory(
        labels: Sequence[Label],
        image_width: int | None = None,
        image_height: int | None = None,
        min_size: int | None = None,
        max_size: int | None = None,
        max_shapes: int | None = None,
    ):
        image_width = image_width if image_width is not None else DefaultImageValues.IMAGE_WIDTH
        image_height = image_height if image_height is not None else DefaultImageValues.IMAGE_HEIGHT
        min_size = min_size if min_size is not None else DefaultImageValues.MIN_SHAPE_SIZE
        max_size = max_size if max_size is not None else DefaultImageValues.MAX_SHAPE_SIZE
        max_shapes = max_shapes if max_shapes is not None else DefaultImageValues.MAX_NUMBER_OF_SHAPES

        assert min_size <= image_width <= max_size
        assert min_size <= image_height <= max_size

        if len(labels) == 0:
            labels = [NullLabel()]

        domains = [label.domain for label in labels]
        is_single_domain = len(set(domains)) == 1
        domain = domains[0]
        if not is_single_domain:
            logger.warning(
                "Fixture `fxt_random_annotated_image_factory` received labels from "
                "multiple domains: %s. Please validate label input. "
                "Using domain %s",
                set(domains),
                domain,
            )

        needs_local_labels = domain not in [
            Domain.CLASSIFICATION,
            Domain.ANOMALY_CLASSIFICATION,
        ]

        img = (np.random.standard_normal([image_height, image_width, 3]) * 255).astype(np.uint8)
        label_map = {label.name: label for label in labels}
        rng = np.random.default_rng()
        num_shapes = rng.integers(low=1, high=max_shapes + 1)
        img_labels = rng.choice(list(label_map), num_shapes)

        annotations: list[Annotation] = []
        shape_counts = {"ellipse": 0, "triangle": 0, "rectangle": 0}
        for label_name in img_labels:
            rx, ry = rng.integers(low=[1, 1], high=[image_width - min_size, image_height - min_size])
            rw, rh = rng.integers(
                low=[min_size, min_size], high=[min(max_size, image_width - rx), min(max_size, image_height - ry)]
            )
            y_min, y_max = float(ry / image_height), float((ry + rh) / image_height)
            x_min, x_max = float(rx / image_width), float((rx + rw) / image_width)

            if label_name in shape_counts:
                shape_counts[label_name] += 1

            if needs_local_labels:
                # Generate annotation shape for local labels
                label = label_map[label_name]
                box_shape = Rectangle(x1=x_min, y1=y_min, x2=x_max, y2=y_max)
                scored_labels = [ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=1.0)]
                annotation = Annotation(box_shape, labels=scored_labels)

                if label_name == "ellipse":
                    annotation = Annotation(
                        Ellipse(
                            x1=box_shape.x1,
                            y1=box_shape.y1,
                            x2=box_shape.x2,
                            y2=box_shape.y2,
                        ),
                        labels=scored_labels,
                    )
                elif label_name == "triangle":
                    points = [
                        Point(
                            x=(box_shape.x1 + box_shape.x2) / 2,
                            y=box_shape.y1,
                        ),
                        Point(x=box_shape.x1, y=box_shape.y2),
                        Point(x=box_shape.x2, y=box_shape.y2),
                    ]
                    annotation = Annotation(
                        Polygon(points=points),
                        labels=scored_labels,
                    )

                annotations.append(annotation)

        if not needs_local_labels:
            # For classification domains, determine dominant shape and assign
            # global label
            dominant_shape_name = max(shape_counts, key=lambda key: shape_counts.get(key, 0))
            label = next(
                (label for label in labels if label.name == dominant_shape_name),
                NullLabel(),
            )
            if label == NullLabel():
                # No matching label found, assign label randomly
                logger.warning(
                    "Generated a random image, but available label names do not match "
                    "shapes in the image. Assigning a label randomly."
                )
                label = random.choice(labels)
            full_box_annotation = Annotation(
                shape=Rectangle.generate_full_box(),
                labels=[ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=1.0)],
            )
            annotations.append(full_box_annotation)

        return img, annotations

    return _annotated_image_factory

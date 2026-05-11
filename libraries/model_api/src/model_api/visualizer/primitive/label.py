"""Label primitive."""

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from io import BytesIO
from typing import Union

from PIL import Image

from model_api.visualizer.defaults import DEFAULT_FONT_SIZE
from model_api.visualizer.utils import default_font, make_label_image, truetype_font

from .primitive import Primitive


class Label(Primitive):
    """Label primitive.

    Labels require a different processing than other primitives as the class also handles the instance when the layout
    requests all the labels to be drawn on a single image.

    Args:
        label (str): Text of the label.
        score (float | None): Score of the label. This is optional.
        fg_color (str | tuple[int, int, int]): Foreground color of the label.
        bg_color (str | tuple[int, int, int]): Background color of the label.
        font_path (str | None | BytesIO): Path to the font file.
        size (int): Size of the font.

    Examples:
        >>> label = Label(label="Label 1")
        >>> label.compute(image).save("label.jpg")

        >>> label = Label(text="Label 1", fg_color="red", bg_color="blue", font_path="arial.ttf", size=20)
        >>> label.compute(image).save("label.jpg")

        or multiple labels on a single image:
        >>> label1 = Label(text="Label 1")
        >>> label2 = Label(text="Label 2")
        >>> label3 = Label(text="Label 3")
        >>> Label.overlay_labels(image, [label1, label2, label3]).save("labels.jpg")
    """

    def __init__(
        self,
        label: str,
        score: Union[float, None] = None,
        fg_color: Union[str, tuple[int, int, int]] = "black",
        bg_color: Union[str, tuple[int, int, int]] = "yellow",
        font_path: Union[str, BytesIO, None] = None,
        size: int = DEFAULT_FONT_SIZE,
    ) -> None:
        self.label = f"{label} ({score:.2f})" if score is not None else label
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.font = default_font(size=size) if font_path is None else truetype_font(font_path, size)

    def compute(self, image: Image) -> Image:
        """Generate label on top of the image.

        Args:
            image (PIL.Image): Image to paste the label on.
        """
        label_image = make_label_image(self.label, self.font, fg_color=self.fg_color, bg_color=self.bg_color)
        image.paste(label_image, (0, 0))
        return image

    @classmethod
    def overlay_labels(cls, image: Image, labels: list["Label"], buffer_x: int = 5, buffer_y: int = 5) -> Image:
        """Overlay multiple label images on top of the image.
        Paste the labels in a row but wrap the labels if they exceed the image width.

        Args:
            image (PIL.Image): Image to paste the labels on.
            labels (list[Label]): Labels to be pasted on the image.
            buffer_x (int): Horizontal space between the labels.
            buffer_y (int): Vertical space between rows of labels.

        Returns:
            PIL.Image: Image with the labels pasted on it.
        """
        offset_x = 0
        offset_y = 0
        row_height = 0
        for label in labels:
            label_image = make_label_image(label.label, label.font, fg_color=label.fg_color, bg_color=label.bg_color)
            if offset_x > 0 and offset_x + label_image.width > image.width:
                offset_x = 0
                offset_y += row_height + buffer_y
                row_height = 0
            image.paste(label_image, (offset_x, offset_y))
            row_height = max(row_height, label_image.height)
            offset_x += label_image.width + buffer_x
        return image

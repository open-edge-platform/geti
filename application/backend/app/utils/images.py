# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

_HIGH_BIT_DEPTH_MODES = ("I;16", "I;16B", "I;16L", "I;16S", "I;16BS", "I", "F")
# 8-bit modes that PNG can store and browsers can display
_PNG_DISPLAY_MODES = ("1", "L", "LA", "P", "RGB", "RGBA")


def crop_to_thumbnail(image: Image.Image, target_height: int, target_width: int) -> Image.Image:
    """
    Crop an image to a thumbnail using maximal visible area preservation.

    The image is first scaled according to the side with the least amount of
    rescaling, and then the other side is cropped. This approach ensures that
    a maximal portion of the original image is visible in the final thumbnail.

    Args:
        image: PIL Image object to generate thumbnail for.
        target_height: Target height in pixels to crop the thumbnail to.
        target_width: Target width in pixels to crop the thumbnail to.

    Returns:
        Image.Image: Cropped and resized thumbnail image.

    Note:
        Uses center cropping after scaling to maintain the most important
        visual content from the original image.
    """
    scale_width = target_width / image.width
    scale_height = target_height / image.height
    scaling_factor = max(scale_width, scale_height)
    resized_image = image.resize((int(image.width * scaling_factor), int(image.height * scaling_factor)))
    # cropping
    x1 = (resized_image.width - target_width) / 2
    x2 = x1 + target_width
    y1 = (resized_image.height - target_height) / 2
    y2 = y1 + target_height
    x1 = round(max(x1, 0))
    x2 = round(min(x2, resized_image.width))
    y1 = round(max(y1, 0))
    y2 = round(min(y2, resized_image.height))
    return resized_image.crop((x1, y1, x2, y2))


def is_high_bit_depth_image(image: Image.Image) -> bool:
    """Check if a PIL image is in a high bit depth mode (16-bit, 32-bit int, or float)."""
    return image.mode in _HIGH_BIT_DEPTH_MODES


def normalize_high_bit_depth_image(image: Image.Image) -> Image.Image:
    """Normalize a high bit depth image to 8-bit RGB using min-max scaling.

    This maps the actual pixel value range to [0, 255], making narrow-range
    images (e.g. 16-bit values in [500-1000]) visible instead of appearing black.

    Args:
        image: A PIL Image in a high bit depth mode (16-bit, 32-bit int, or float).

    Returns:
        An 8-bit RGB PIL Image with normalized pixel values.
    """
    arr = np.array(image, dtype=np.float64)
    lo, hi = arr.min(), arr.max()
    if hi > lo:
        arr = (arr - lo) / (hi - lo) * 255.0
    else:
        arr = np.zeros_like(arr)
    return Image.fromarray(arr.astype(np.uint8), mode="L").convert("RGB")


def normalize_high_bit_depth_array(array: np.ndarray) -> np.ndarray:
    """Min-max scale a high bit depth array to 8-bit values in [0, 255].

    Mirrors :func:`normalize_high_bit_depth_image` but operates on a raw numpy
    array so it can be applied to decoded media (e.g. an OpenCV ``IMREAD_UNCHANGED``
    result) without a PIL round-trip. Scaling is computed over the whole array so
    that multi-channel images keep their relative channel intensities.

    Args:
        array: Numeric array of any shape and dtype.

    Returns:
        An array of the same shape with dtype ``uint8``.
    """
    if array.size == 0:
        return array.astype(np.uint8)
    arr = array.astype(np.float64)
    lo, hi = float(arr.min()), float(arr.max())
    if hi > lo:
        arr = (arr - lo) / (hi - lo) * 255.0
    else:
        arr = np.zeros_like(arr)
    return arr.astype(np.uint8)


def to_uint8_rgb(array: np.ndarray) -> np.ndarray:
    """Convert a decoded image array to a 3-channel 8-bit RGB array.

    Models such as the SAM image encoder accept only ``(H, W, 3)`` ``uint8`` inputs,
    whereas media is decoded with the original bit depth and channel count preserved
    (e.g. 16-bit grayscale TIFF/PNG images decode to ``(H, W, 1)`` ``uint16``).
    This normalizes any decoded array to what those models expect:

    * high bit depth (non-``uint8``) data is min-max scaled to ``[0, 255]``, which
      matches the normalization applied when displaying such images in the UI, so
      the model sees the same pixels as the user;
    * single-channel data is replicated across three channels;
    * a fourth (alpha) channel is dropped, leaving the existing channel order intact.

    Channel order is never changed: colour input must already be in RGB(A) order.
    OpenCV decodes BGR(A), so callers reading with ``cv2.imread`` have to convert first
    (:meth:`app.services.media_numpy_loader.MediaNumpyLoader.load_media_binary` does this
    for both 3- and 4-channel images).

    Args:
        array: Decoded image array of shape ``(H, W)``, ``(H, W, 1)``, ``(H, W, 3)``
            or ``(H, W, 4)``, in RGB(A) order for colour input.

    Returns:
        A ``(H, W, 3)`` ``uint8`` array.

    Raises:
        ValueError: If the array does not have a supported shape or channel count.
    """
    if array.ndim == 2:
        array = array[..., np.newaxis]
    if array.ndim != 3:
        raise ValueError(f"Expected a 2D or 3D image array, got shape {array.shape}")

    channels = array.shape[-1]
    if channels == 4:
        # Drop the alpha channel; the remaining channels keep their original order.
        array = array[..., :3]
        channels = 3
    if channels not in (1, 3):
        raise ValueError(f"Unsupported number of image channels: {channels}")

    if array.dtype != np.uint8:
        array = normalize_high_bit_depth_array(array)

    if channels == 1:
        array = np.repeat(array, 3, axis=-1)

    return np.ascontiguousarray(array)


def convert_to_jpeg_compatible(image: Image.Image) -> Image.Image:
    """Convert an image to a JPEG-compatible mode (RGB, L, or CMYK).

    High bit depth modes (I;16, I, F) require explicit normalization: PIL's built-in
    RGB conversion only preserves the most-significant byte, clipping the
    lower half of the dynamic range and producing washed-out thumbnails.
    We normalize the full value range to [0, 255] before converting to L.
    """
    if image.mode in ("RGB", "L", "CMYK"):
        return image
    if is_high_bit_depth_image(image):
        return normalize_high_bit_depth_image(image)
    # All other non-JPEG-compatible modes (RGBA, P, …)
    return image.convert("RGB")


def needs_display_conversion(image_path: Path) -> bool:
    """Return True if browsers cannot display the image at the given path as-is.

    Browsers cannot decode TIFF, and high bit depth images must be normalized to 8-bit.
    Opens the image with deferred decoding (no pixel data read), so this is cheap
    enough to call on every request.

    Args:
        image_path: Path to the image file on disk.

    Returns:
        True if the image is a TIFF or high bit depth and should be converted before display.
    """
    with Image.open(image_path) as img:
        return img.format == "TIFF" or is_high_bit_depth_image(img)


def convert_image_to_display_png_bytes(image_path: Path) -> bytes:
    """Convert an image to 8-bit PNG bytes that any browser can display.

    High bit depth images are min-max normalized to [0, 255]; modes that PNG cannot
    store (e.g. CMYK) are converted to RGB; all other images keep their pixels as-is.

    Call :func:`needs_display_conversion` first to avoid re-encoding images that
    browsers can already display.

    Args:
        image_path: Path to the image file on disk.

    Returns:
        PNG-encoded bytes of the 8-bit image.
    """
    with Image.open(image_path) as img:
        if is_high_bit_depth_image(img):
            display_img = normalize_high_bit_depth_image(img)
        elif img.mode in _PNG_DISPLAY_MODES:
            display_img = img
        else:
            display_img = img.convert("RGB")
        buffer = BytesIO()
        display_img.save(buffer, format="PNG")
        return buffer.getvalue()

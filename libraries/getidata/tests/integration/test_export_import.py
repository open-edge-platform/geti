"""
Tests for export and import functionality.

This test suite covers:
- Exporting datasets with various field types (ImageCallableField, ImagePathField, InstanceMaskCallableField)
- Importing datasets from directories and ZIP files
- Image export in different formats (PNG, JPEG preservation)
- Metadata serialization and deserialization
- Schema and categories preservation
- Object column handling
"""

import json
import zipfile
from pathlib import Path
from typing import Callable

import numpy as np
import polars as pl
import pytest
from PIL import Image as PILImage

from getidata.categories import LabelCategories, MaskCategories
from getidata.dataset import Dataset, Sample
from getidata.export_import import (
    DATAFRAME_FILE,
    IMAGES_DIR,
    METADATA_FILE,
    VERSION,
    VIDEOS_DIR,
    ExportMode,
    _build_index_based_lookup,
    _export_images_from_dataset,
    _get_registered_samples,
    _get_video_fields,
    _match_dtype_from_schema,
    _patch_annotation_files,
    _reconstruct_video_fields,
    _sample_registry,
    _sanitize_extracted_files,
    export_dataset,
    import_dataset,
    register_sample,
    sanitize_filename,
)
from getidata.fields import (
    ImageInfo,
    Subset,
    TileInfo,
    bbox_field,
    image_callable_field,
    image_info_field,
    image_path_field,
    instance_mask_callable_field,
    keypoints_field,
    label_field,
    mask_callable_field,
    numeric_field,
    rotated_bbox_field,
    subset_field,
    tensor_field,
    tile_field,
)
from getidata.fields.videos import media_path_field, video_frame_path_field
from getidata.media import LazyImage, LazyVideoFrame

LABEL_CATEGORIES = LabelCategories(labels=("apple", "orange", "pear", "mango", "coconut"))
MASK_CATEGORIES = MaskCategories.generate(size=256)


def test_export_no_image_fields(tmp_path):
    """Test that datasets without image fields return empty dict."""

    class SimpleSample(Sample):
        label: int = label_field()

    dataset = Dataset(
        dtype_or_schema=SimpleSample,
        categories={"label": LABEL_CATEGORIES},
    )
    dataset.append(SimpleSample(label=1))

    output_dir = tmp_path / "output"
    result = _export_images_from_dataset(dataset, output_dir)

    assert result == {}


def test_export_image_callable_field(tmp_path):
    """Test exporting datasets with ImageCallableField."""

    class CallableSample(Sample):
        image: Callable[[], np.ndarray] = image_callable_field(format="RGB")

    # Create sample images as callables
    def make_image_callable(idx):
        def load_image():
            # Create a simple test image
            img = np.zeros((50, 60, 3), dtype=np.uint8)
            img[:, :, 0] = idx * 50  # Varying red channel
            return img

        return load_image

    dataset = Dataset(CallableSample)
    dataset.append(CallableSample(image=make_image_callable(0)))
    dataset.append(CallableSample(image=make_image_callable(1)))
    dataset.append(CallableSample(image=make_image_callable(2)))

    output_dir = tmp_path / "output"
    result = _export_images_from_dataset(dataset, output_dir)

    # Check that images were saved
    assert "image" in result
    assert len(result["image"]) == 3
    for idx in range(3):
        assert idx in result["image"]
        rel_path = result["image"][idx]
        assert rel_path == f"image_{idx:06d}.png"

        # Verify file exists and is valid
        img_file = output_dir / rel_path
        assert img_file.exists()

        # Load and verify image content
        loaded_img = np.array(PILImage.open(img_file))
        assert loaded_img.shape == (50, 60, 3)
        assert loaded_img[0, 0, 0] == idx * 50  # Check red channel


def test_export_image_path_field(tmp_path):
    """Test exporting datasets with ImagePathField (copies files directly)."""

    class PathSample(Sample):
        image_path: str = image_path_field()

    # Create source images
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    image_paths = []
    for idx in range(3):
        # Create images with different formats
        ext = [".png", ".jpg", ".jpeg"][idx % 3]
        img_path = source_dir / f"image_{idx}{ext}"

        img = np.random.randint(0, 255, (40, 50, 3), dtype=np.uint8)
        pil_img = PILImage.fromarray(img)
        if ext == ".jpg" or ext == ".jpeg":
            pil_img.save(img_path, "JPEG")
        else:
            pil_img.save(img_path)

        image_paths.append(str(img_path))

    dataset = Dataset(PathSample)
    for path in image_paths:
        dataset.append(PathSample(image_path=path))

    output_dir = tmp_path / "output"
    result = _export_images_from_dataset(dataset, output_dir)

    # Check that images were copied
    assert "image_path" in result
    assert len(result["image_path"]) == 3

    for idx in range(3):
        assert idx in result["image_path"]
        rel_path = result["image_path"][idx]

        # Verify the file exists and format is preserved
        img_file = output_dir / rel_path
        assert img_file.exists()

        # Check that the file extension is preserved
        expected_ext = [".png", ".jpg", ".jpeg"][idx % 3]
        assert img_file.suffix == expected_ext


def test_export_instance_mask_callable_field(tmp_path):
    """Test exporting datasets with InstanceMaskCallableField."""

    class MaskSample(Sample):
        mask: Callable[[], np.ndarray] = instance_mask_callable_field()

    def make_mask_callable(idx):
        def load_mask():
            # Create a simple mask
            mask = np.zeros((30, 40), dtype=np.uint8)
            mask[5:25, 5:35] = idx + 1  # Different values per mask
            return mask

        return load_mask

    dataset = Dataset(dtype_or_schema=MaskSample, categories={"mask": MASK_CATEGORIES})
    for idx in range(3):
        dataset.append(MaskSample(mask=make_mask_callable(idx)))

    output_dir = tmp_path / "output"
    result = _export_images_from_dataset(dataset, output_dir)

    # Check that masks were saved
    assert "mask" in result
    assert len(result["mask"]) == 3

    for idx in range(3):
        assert idx in result["mask"]
        rel_path = result["mask"][idx]
        assert rel_path == f"mask_{idx:06d}.png"

        # Verify file exists
        mask_file = output_dir / rel_path
        assert mask_file.exists()

        # Load and verify mask content
        loaded_mask = np.array(PILImage.open(mask_file))
        assert loaded_mask.shape == (30, 40)
        # Check that the mask has the expected value in center region
        assert loaded_mask[10, 10] == idx + 1


def test_export_mixed_fields(tmp_path):
    """Test exporting datasets with multiple image field types."""

    class MixedSample(Sample):
        image: Callable[[], np.ndarray] = image_callable_field()
        image_path: str = image_path_field()
        mask: Callable[[], np.ndarray] = instance_mask_callable_field()

    # Create source image
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    img_path = source_dir / "source.png"
    PILImage.fromarray(np.zeros((10, 10, 3), dtype=np.uint8)).save(img_path)

    def make_image():
        return np.ones((20, 20, 3), dtype=np.uint8) * 100

    def make_mask():
        return np.ones((15, 15), dtype=np.uint8) * 255

    dataset = Dataset(dtype_or_schema=MixedSample, categories={"mask": MASK_CATEGORIES})
    dataset.append(
        MixedSample(
            image=make_image,
            image_path=str(img_path),
            mask=make_mask,
        )
    )

    output_dir = tmp_path / "output"
    result = _export_images_from_dataset(dataset, output_dir)

    # Check all three fields were exported
    assert "image" in result
    assert "image_path" in result
    assert "mask" in result
    assert len(result["image"]) == 1
    assert len(result["image_path"]) == 1
    assert len(result["mask"]) == 1


def test_export_with_none_values(tmp_path):
    """Test exporting datasets with None values in image fields."""

    class OptionalImageSample(Sample):
        image: Callable[[], np.ndarray] | None = image_callable_field()

    def make_image():
        return np.zeros((10, 10, 3), dtype=np.uint8)

    dataset = Dataset(OptionalImageSample)
    dataset.append(OptionalImageSample(image=make_image))
    dataset.append(OptionalImageSample(image=None))
    dataset.append(OptionalImageSample(image=make_image))

    output_dir = tmp_path / "output"
    result = _export_images_from_dataset(dataset, output_dir)

    # Only indices 0 and 2 should be in result
    assert "image" in result
    assert len(result["image"]) == 2
    assert 0 in result["image"]
    assert 1 not in result["image"]
    assert 2 in result["image"]


def test_export_images_error_missing_image_path_file(tmp_path):
    """Error when an ImagePathField points to a non-existent file and ignore_missing_media=False."""

    class PathImageSample(Sample):
        image_path: str = image_path_field()

    dataset = Dataset(PathImageSample)
    missing_path = tmp_path / "does_not_exist.png"
    dataset.append(PathImageSample(image_path=str(missing_path)))

    output_dir = tmp_path / "output_missing_path"
    with pytest.raises(ValueError, match="image"):
        _export_images_from_dataset(dataset, output_dir)


def test_export_images_error_failing_image_callable(tmp_path):
    """Error when an ImageCallableField cannot generate an image and ignore_missing_media=False."""

    class CallableImageSample(Sample):
        image: Callable[[], np.ndarray] = image_callable_field()

    def bad_image():
        raise RuntimeError("failed to generate image")

    dataset = Dataset(CallableImageSample)
    dataset.append(CallableImageSample(image=bad_image))

    output_dir = tmp_path / "output_bad_callable"
    with pytest.raises(ValueError, match="image"):
        _export_images_from_dataset(dataset, output_dir)


def test_export_images_ignore_missing_media_skips_missing_image_path(tmp_path):
    """Missing ImagePathField file is skipped when ignore_missing_media=True."""

    class PathImageSample(Sample):
        image_path: str = image_path_field()

    # Create one valid image and one missing
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    valid_path = source_dir / "valid.png"
    PILImage.fromarray(np.zeros((10, 10, 3), dtype=np.uint8)).save(valid_path)
    missing_path = tmp_path / "does_not_exist.png"

    dataset = Dataset(PathImageSample)
    dataset.append(PathImageSample(image_path=str(valid_path)))
    dataset.append(PathImageSample(image_path=str(missing_path)))

    output_dir = tmp_path / "output"
    result = _export_images_from_dataset(dataset, output_dir, ignore_missing_media=True)

    # Only the valid image should be exported
    assert "image_path" in result
    assert len(result["image_path"]) == 1
    assert 0 in result["image_path"]
    assert 1 not in result["image_path"]


def test_export_images_ignore_missing_media_skips_failing_callable(tmp_path):
    """Failing ImageCallableField is skipped when ignore_missing_media=True."""

    class CallableImageSample(Sample):
        image: Callable[[], np.ndarray] = image_callable_field()

    def good_image():
        return np.zeros((10, 10, 3), dtype=np.uint8)

    def bad_image():
        raise RuntimeError("failed to generate image")

    dataset = Dataset(CallableImageSample)
    dataset.append(CallableImageSample(image=good_image))
    dataset.append(CallableImageSample(image=bad_image))
    dataset.append(CallableImageSample(image=good_image))

    output_dir = tmp_path / "output"
    result = _export_images_from_dataset(dataset, output_dir, ignore_missing_media=True)

    # Only the good images should be exported
    assert "image" in result
    assert len(result["image"]) == 2
    assert 0 in result["image"]
    assert 1 not in result["image"]
    assert 2 in result["image"]


def test_export_dataset_ignore_missing_media_roundtrip(tmp_path):
    """Test that export_dataset with ignore_missing_media=True works end-to-end."""

    class OptionalImageSample(Sample):
        image: Callable[[], np.ndarray] | None = image_callable_field()
        label: int = label_field()

    def make_image():
        return np.zeros((10, 10, 3), dtype=np.uint8)

    # Export dataset with mixed None values
    original_dataset = Dataset(OptionalImageSample, categories={"label": LABEL_CATEGORIES})
    original_dataset.append(OptionalImageSample(image=make_image, label=1))
    original_dataset.append(OptionalImageSample(image=None, label=2))
    original_dataset.append(OptionalImageSample(image=make_image, label=3))

    export_dir = tmp_path / "export"
    export_dataset(original_dataset, export_dir, export_media=ExportMode.COPY, as_zip=False, ignore_missing_media=True)

    imported_dataset = import_dataset(export_dir, dtype=OptionalImageSample)

    assert len(imported_dataset) == 3
    assert callable(imported_dataset[0].image)
    assert imported_dataset[1].image is None
    assert callable(imported_dataset[2].image)


def test_export_basic_dataset_to_directory(tmp_path):
    """Test basic export to directory."""

    class SimpleSample(Sample):
        label: int = label_field()
        score: float = numeric_field(dtype=pl.Float32(), semantic="score")

    dataset = Dataset(SimpleSample, categories={"label": LABEL_CATEGORIES})
    dataset.append(SimpleSample(label=1, score=0.9))
    dataset.append(SimpleSample(label=2, score=0.8))

    output_dir = tmp_path / "export"
    export_dataset(dataset, output_dir, export_media=ExportMode.SKIP, as_zip=False)

    # Check directory structure
    assert output_dir.exists()
    assert (output_dir / METADATA_FILE).exists()
    assert (output_dir / DATAFRAME_FILE).exists()

    # Check metadata content
    with open(output_dir / METADATA_FILE) as f:
        metadata = json.load(f)
    assert metadata["version"] == VERSION
    assert "schema" in metadata

    # Check dataframe can be loaded
    df = pl.read_parquet(output_dir / DATAFRAME_FILE)
    assert len(df) == 2
    assert "label" in df.columns
    assert "score" in df.columns


def test_export_dataset_with_images_to_directory(tmp_path):
    """Test export with images to directory."""

    class ImageSample(Sample):
        image: Callable[[], np.ndarray] = image_callable_field()
        label: int = label_field()

    def make_image(idx):
        def load_image():
            img = np.zeros((30, 40, 3), dtype=np.uint8)
            img[:, :, 0] = idx * 50
            return img

        return load_image

    dataset = Dataset(ImageSample, categories={"label": LABEL_CATEGORIES})
    dataset.append(ImageSample(image=make_image(0), label=1))
    dataset.append(ImageSample(image=make_image(1), label=2))

    output_dir = tmp_path / "export"
    export_dataset(dataset, output_dir, export_media=ExportMode.COPY, as_zip=False)

    # Check directory structure
    assert output_dir.exists()
    assert (output_dir / METADATA_FILE).exists()
    assert (output_dir / DATAFRAME_FILE).exists()
    assert (output_dir / IMAGES_DIR).exists()

    # Check images were exported
    images_dir = output_dir / IMAGES_DIR
    assert len(list(images_dir.glob("image_*.png"))) == 2


def test_export_dataset_as_zip(tmp_path):
    """Test export as ZIP file."""

    class SimpleSample(Sample):
        label: int = label_field()

    dataset = Dataset(SimpleSample, categories={"label": LABEL_CATEGORIES})
    dataset.append(SimpleSample(label=1))

    output_zip = tmp_path / "export.zip"
    export_dataset(dataset, output_zip, export_media=ExportMode.SKIP, as_zip=True)

    # Check ZIP file was created
    assert output_zip.exists()
    assert output_zip.suffix == ".zip"

    # Extract and verify contents

    with zipfile.ZipFile(output_zip) as zf:
        namelist = zf.namelist()
        assert METADATA_FILE in namelist
        assert DATAFRAME_FILE in namelist


def test_export_with_object_columns(tmp_path):
    """Test that object columns are tracked in metadata."""

    class CallableSample(Sample):
        image: Callable[[], np.ndarray] = image_callable_field()
        label: int = label_field()

    def make_image():
        return np.zeros((10, 10, 3), dtype=np.uint8)

    dataset = Dataset(CallableSample, categories={"label": LABEL_CATEGORIES})
    dataset.append(CallableSample(image=make_image, label=1))

    output_dir = tmp_path / "export"
    export_dataset(dataset, output_dir, export_media=ExportMode.SKIP, as_zip=False)

    # Check metadata tracks object columns
    with open(output_dir / METADATA_FILE) as f:
        metadata = json.load(f)
    assert "object_columns" in metadata
    assert "image" in metadata["object_columns"]


def test_export_dataset_with_categories(tmp_path):
    """Test export preserves category information."""

    class LabeledSample(Sample):
        label: int = label_field()

    # Create dataset with categories
    categories = LabelCategories(labels=("cat", "dog"))

    dataset = Dataset(LabeledSample, categories={"label": categories})
    dataset.append(LabeledSample(label=0))
    dataset.append(LabeledSample(label=1))

    output_dir = tmp_path / "export"
    export_dataset(dataset, output_dir, export_media=ExportMode.SKIP, as_zip=False)

    # Check schema is preserved
    with open(output_dir / METADATA_FILE) as f:
        metadata = json.load(f)
    assert "schema" in metadata
    schema_dict = metadata["schema"]
    assert "label" in schema_dict["categories"]


def test_export_media_skip_skips_image_export(tmp_path):
    """Test that export_media=ExportMode.SKIP skips image export."""

    class ImageSample(Sample):
        image: Callable[[], np.ndarray] = image_callable_field()

    def make_image():
        return np.zeros((10, 10, 3), dtype=np.uint8)

    dataset = Dataset(ImageSample)
    dataset.append(ImageSample(image=make_image))

    output_dir = tmp_path / "export"
    export_dataset(dataset, output_dir, export_media=ExportMode.SKIP, as_zip=False)

    # Images directory should not exist
    assert not (output_dir / IMAGES_DIR).exists()


def test_import_basic_dataset_from_directory(tmp_path):
    """Test importing a basic dataset from directory."""

    class SimpleSample(Sample):
        label: int = label_field()
        score: float = numeric_field(dtype=pl.Float32(), semantic="score")

    # Export first
    original_dataset = Dataset(SimpleSample, categories={"label": LABEL_CATEGORIES})
    original_dataset.append(SimpleSample(label=1, score=0.9))
    original_dataset.append(SimpleSample(label=2, score=0.8))

    export_dir = tmp_path / "export"
    export_dataset(original_dataset, export_dir, export_media=ExportMode.SKIP, as_zip=False)

    # Import back
    imported_dataset = import_dataset(export_dir, dtype=SimpleSample)

    # Verify dataset
    assert len(imported_dataset) == 2
    assert imported_dataset[0].label == 1
    assert imported_dataset[0].score == pytest.approx(0.9)
    assert imported_dataset[1].label == 2
    assert imported_dataset[1].score == pytest.approx(0.8)


def test_import_dataset_from_zip(tmp_path):
    """Test importing dataset from ZIP file."""

    class SimpleSample(Sample):
        label: int = label_field()

    # Export as ZIP
    original_dataset = Dataset(SimpleSample, categories={"label": LABEL_CATEGORIES})
    original_dataset.append(SimpleSample(label=1))
    original_dataset.append(SimpleSample(label=2))

    export_zip = tmp_path / "export.zip"
    export_dataset(original_dataset, export_zip, export_media=ExportMode.SKIP, as_zip=True)

    # Import from ZIP
    imported_dataset = import_dataset(export_zip, dtype=SimpleSample)

    # Verify dataset
    assert len(imported_dataset) == 2
    assert imported_dataset[0].label == 1
    assert imported_dataset[1].label == 2


def test_import_dataset_with_image_callables(tmp_path):
    """Test importing dataset with ImageCallableField reconstructs callables."""

    class ImageSample(Sample):
        image: Callable[[], np.ndarray] = image_callable_field()
        label: int = label_field()

    def make_image(idx):
        def load_image():
            img = np.zeros((30, 40, 3), dtype=np.uint8)
            img[:, :, 0] = idx * 50
            return img

        return load_image

    # Export dataset
    original_dataset = Dataset(ImageSample, categories={"label": LABEL_CATEGORIES})
    original_dataset.append(ImageSample(image=make_image(0), label=1))
    original_dataset.append(ImageSample(image=make_image(1), label=2))

    export_dir = tmp_path / "export"
    export_dataset(original_dataset, export_dir, export_media=ExportMode.COPY, as_zip=False)

    # Import back
    imported_dataset = import_dataset(export_dir, dtype=ImageSample)

    # Verify dataset
    assert len(imported_dataset) == 2

    # Check that images are callables and work correctly
    sample0 = imported_dataset[0]
    assert callable(sample0.image)
    img0 = sample0.image()
    assert isinstance(img0, np.ndarray)
    assert img0.shape == (30, 40, 3)
    assert img0[0, 0, 0] == 0  # First image has red=0

    sample1 = imported_dataset[1]
    assert callable(sample1.image)
    img1 = sample1.image()
    assert img1.shape == (30, 40, 3)
    assert img1[0, 0, 0] == 50  # Second image has red=50


def test_import_dataset_with_image_paths(tmp_path):
    """Test importing dataset with ImagePathField updates paths."""

    class PathSample(Sample):
        image_path: str = image_path_field()
        label: int = label_field()

    # Create source image
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    img_path = source_dir / "test.png"
    PILImage.fromarray(np.zeros((10, 10, 3), dtype=np.uint8)).save(img_path)

    # Export dataset
    original_dataset = Dataset(PathSample, categories={"label": LABEL_CATEGORIES})
    original_dataset.append(PathSample(image_path=str(img_path), label=1))

    export_dir = tmp_path / "export"
    export_dataset(original_dataset, export_dir, export_media=ExportMode.COPY, as_zip=False)

    # Import back
    imported_dataset = import_dataset(export_dir, dtype=PathSample)

    # Verify dataset
    assert len(imported_dataset) == 1
    sample = imported_dataset[0]

    # Check that path points to exported image location
    assert sample.image_path is not None
    path = Path(sample.image_path)
    assert path.exists()
    assert IMAGES_DIR in path.parts


def test_import_dataset_with_instance_masks(tmp_path):
    """Test importing dataset with InstanceMaskCallableField."""

    class MaskSample(Sample):
        mask: Callable[[], np.ndarray] = instance_mask_callable_field()
        label: int = label_field()

    def make_mask(idx):
        def load_mask():
            mask = np.zeros((20, 30), dtype=np.uint8)
            mask[5:15, 5:25] = (idx + 1) * 100
            return mask

        return load_mask

    # Export dataset
    original_dataset = Dataset(MaskSample, categories={"label": LABEL_CATEGORIES, "mask": MASK_CATEGORIES})
    original_dataset.append(MaskSample(mask=make_mask(0), label=1))
    original_dataset.append(MaskSample(mask=make_mask(1), label=2))

    export_dir = tmp_path / "export"
    export_dataset(original_dataset, export_dir, export_media=ExportMode.COPY, as_zip=False)

    # Import back
    imported_dataset = import_dataset(export_dir, dtype=MaskSample)

    # Verify dataset
    assert len(imported_dataset) == 2

    # Check masks are callables and work correctly
    sample0 = imported_dataset[0]
    assert callable(sample0.mask)
    mask0 = sample0.mask()
    assert isinstance(mask0, np.ndarray)
    assert mask0.shape == (20, 30)
    assert mask0[10, 10] == 100  # First mask

    sample1 = imported_dataset[1]
    mask1 = sample1.mask()
    assert mask1[10, 10] == 200  # Second mask


def _count_path_glob_calls(monkeypatch) -> dict[str, int]:
    """Patch ``Path.glob`` to count invocations for the duration of a test.

    Returns a mutable dict with a ``"count"`` key that callers can reset
    between measurements (e.g. before each ``import_dataset`` call).
    """
    counters = {"count": 0}
    original_glob = Path.glob

    def counting_glob(self, *args, **kwargs):
        counters["count"] += 1
        return original_glob(self, *args, **kwargs)

    monkeypatch.setattr(Path, "glob", counting_glob)
    return counters


def test_import_image_path_field_does_not_rescan_directory_per_row(tmp_path, monkeypatch):
    """Regression test for a perf bug where resolving ``ImagePathField``
    values called ``Path.glob()`` once per row, rescanning the entire images
    directory on every call. On a ~100k-image real-world dataset this made
    loading take roughly two hours instead of seconds (O(rows * files)
    instead of O(files)). ``Path.glob()`` call count must not scale with the
    number of rows.
    """

    class PathSample(Sample):
        image_path: str = image_path_field()
        label: int = label_field()

    counters = _count_path_glob_calls(monkeypatch)

    def build_and_import(num_samples: int) -> int:
        source_dir = tmp_path / f"source_{num_samples}"
        source_dir.mkdir()
        dataset = Dataset(PathSample, categories={"label": LABEL_CATEGORIES})
        for i in range(num_samples):
            img_path = source_dir / f"img_{i}.png"
            PILImage.fromarray(np.zeros((4, 4, 3), dtype=np.uint8)).save(img_path)
            dataset.append(PathSample(image_path=str(img_path), label=1))

        export_dir = tmp_path / f"export_{num_samples}"
        export_dataset(dataset, export_dir, export_media=ExportMode.COPY, as_zip=False)

        counters["count"] = 0
        import_dataset(export_dir, dtype=PathSample)
        return counters["count"]

    small_calls = build_and_import(5)
    large_calls = build_and_import(50)

    assert large_calls == small_calls, (
        f"Path.glob() call count scaled with the number of rows ({small_calls} -> {large_calls} "
        "for 5 -> 50 rows); expected a constant, row-count-independent number of calls. This "
        "indicates the O(rows * files) per-row directory rescan regression has returned."
    )


def test_import_instance_mask_field_does_not_rescan_directory_per_row(tmp_path, monkeypatch):
    """Regression test for the callable-field branch of the same perf bug:
    resolving ``{field}_{idx:06d}.*`` mask files must build a single index of
    the images directory rather than calling ``Path.glob()`` once per row.
    """

    class MaskSample(Sample):
        mask: Callable[[], np.ndarray] = instance_mask_callable_field()
        label: int = label_field()

    def make_mask(idx):
        def load_mask():
            m = np.zeros((6, 6), dtype=np.uint8)
            m[:, :] = (idx % 250) + 1
            return m

        return load_mask

    counters = _count_path_glob_calls(monkeypatch)

    def build_and_import(num_samples: int) -> int:
        dataset = Dataset(MaskSample, categories={"label": LABEL_CATEGORIES, "mask": MASK_CATEGORIES})
        for i in range(num_samples):
            dataset.append(MaskSample(mask=make_mask(i), label=1))

        export_dir = tmp_path / f"mask_export_{num_samples}"
        export_dataset(dataset, export_dir, export_media=ExportMode.COPY, as_zip=False)

        counters["count"] = 0
        import_dataset(export_dir, dtype=MaskSample)
        return counters["count"]

    small_calls = build_and_import(5)
    large_calls = build_and_import(50)

    assert large_calls == small_calls, (
        f"Path.glob() call count scaled with the number of rows ({small_calls} -> {large_calls} "
        "for 5 -> 50 rows) when resolving callable-field mask files."
    )


def test_build_index_based_lookup_matches_simple_filename(tmp_path):
    """Baseline case: `{field}_{idx:06d}.<ext>` resolves to that file."""
    (tmp_path / "mask_000001.png").touch()

    lookup = _build_index_based_lookup("mask", tmp_path)

    assert lookup == {1: tmp_path / "mask_000001.png"}


def test_build_index_based_lookup_matches_filename_with_extra_dots(tmp_path):
    """Regression test: the original per-row glob pattern was
    `{field}_{idx:06d}.*`, where `.*` matches anything after the first dot -
    including filenames with additional embedded dots, e.g. a versioned
    extension like "mask_000001.v1.png". `Path.stem` only strips the last
    suffix, so naively parsing `candidate.stem` (stem == "mask_000001.v1")
    would wrongly reject this file. It must still be matched.
    """
    (tmp_path / "mask_000001.v1.png").touch()

    lookup = _build_index_based_lookup("mask", tmp_path)

    assert lookup == {1: tmp_path / "mask_000001.v1.png"}


def test_build_index_based_lookup_ignores_extensionless_filename(tmp_path):
    """Regression test: the original glob pattern `{field}_{idx:06d}.*`
    requires a literal "." after the zero-padded index - it would never
    match an extension-less file like "mask_000001". The lookup must not
    match it either (naively checking `stem[len(prefix):].isdigit()` would
    incorrectly accept it, since an extension-less file's stem equals its
    full name).
    """
    (tmp_path / "mask_000001").touch()

    lookup = _build_index_based_lookup("mask", tmp_path)

    assert lookup == {}


def test_build_index_based_lookup_ignores_non_canonical_padding(tmp_path):
    """A file whose numeric suffix isn't the canonical zero-padded (min
    width 6) form (e.g. "mask_42.png" instead of "mask_000042.png") would
    never have matched the per-row query `{field}_{42:06d}.*` == "mask_000042.*",
    so it must not be matched by the lookup either.
    """
    (tmp_path / "mask_42.png").touch()

    lookup = _build_index_based_lookup("mask", tmp_path)

    assert lookup == {}


def test_import_missing_metadata_raises_error(tmp_path):
    """Test that an empty directory raises ValueError when format cannot be detected."""

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(ValueError, match="Could not detect dataset format"):
        import_dataset(empty_dir)


def test_import_missing_dataframe_raises_error(tmp_path):
    """Test that missing dataframe file raises appropriate error.

    With automatic format detection, a directory with only metadata.json
    but no data.parquet will not be detected as getidata format, so it
    will raise a format detection error.
    """

    export_dir = tmp_path / "export"
    export_dir.mkdir()

    # Create metadata but no dataframe - this won't be detected as getidata format
    metadata = {"version": VERSION, "schema": {}}
    with open(export_dir / METADATA_FILE, "w") as f:
        json.dump(metadata, f)

    with pytest.raises(ValueError, match="Could not detect dataset format"):
        import_dataset(export_dir)


def test_import_preserves_categories(tmp_path):
    """Test that import preserves category information."""

    class LabeledSample(Sample):
        label: int = label_field()

    # Create Dataset with categories
    categories = LabelCategories(labels=("cat", "dog"))
    original_dataset = Dataset(LabeledSample, categories={"label": categories})
    original_dataset.append(LabeledSample(label=0))

    export_dir = tmp_path / "export"
    export_dataset(original_dataset, export_dir, export_media=ExportMode.SKIP, as_zip=False)

    # Import back
    imported_dataset = import_dataset(export_dir, dtype=LabeledSample)

    # Verify categories are preserved
    assert imported_dataset.schema.attributes["label"] is not None
    assert len(imported_dataset.schema.attributes["label"].categories.labels) == 2


def test_import_with_none_image_values(tmp_path):
    """Test importing dataset with None values in image fields."""

    class OptionalImageSample(Sample):
        image: Callable[[], np.ndarray] | None = image_callable_field()
        label: int = label_field()

    def make_image():
        return np.zeros((10, 10, 3), dtype=np.uint8)

    # Export dataset with mixed None values
    original_dataset = Dataset(OptionalImageSample, categories={"label": LABEL_CATEGORIES})
    original_dataset.append(OptionalImageSample(image=make_image, label=1))
    original_dataset.append(OptionalImageSample(image=None, label=2))
    original_dataset.append(OptionalImageSample(image=make_image, label=3))

    export_dir = tmp_path / "export"
    export_dataset(original_dataset, export_dir, export_media=ExportMode.COPY, as_zip=False)

    # Import back
    imported_dataset = import_dataset(export_dir, dtype=OptionalImageSample)

    # Verify dataset
    assert len(imported_dataset) == 3
    assert callable(imported_dataset[0].image)
    assert imported_dataset[1].image is None
    assert callable(imported_dataset[2].image)


def test_roundtrip_preserves_data_integrity(tmp_path):
    """Test that export-import roundtrip preserves data integrity."""

    class ComplexSample(Sample):
        label: int = label_field()
        score: float = numeric_field(dtype=pl.Float32(), semantic="score")
        image: Callable[[], np.ndarray] = image_callable_field()

    def make_image(value):
        def load_image():
            return np.full((20, 20, 3), value, dtype=np.uint8)

        return load_image

    # Create dataset
    original_dataset = Dataset(ComplexSample, categories={"label": LABEL_CATEGORIES})
    for i in range(5):
        original_dataset.append(ComplexSample(label=i, score=i * 0.2, image=make_image(i * 50)))

    # Export and import
    export_dir = tmp_path / "export"
    export_dataset(original_dataset, export_dir, export_media=ExportMode.COPY, as_zip=False)
    imported_dataset = import_dataset(export_dir, dtype=ComplexSample)

    # Verify complete data integrity
    assert len(imported_dataset) == len(original_dataset)
    for i in range(5):
        orig_sample = original_dataset[i]
        imported_sample = imported_dataset[i]

        assert orig_sample.label == imported_sample.label
        assert orig_sample.score == pytest.approx(imported_sample.score)

        # Check images produce the same values
        orig_img = orig_sample.image()
        imported_img = imported_sample.image()
        np.testing.assert_array_equal(orig_img, imported_img)


def test_export_empty_dataset(tmp_path):
    """Test exporting empty dataset."""

    class SimpleSample(Sample):
        label: int = label_field()

    dataset = Dataset(SimpleSample)

    output_dir = tmp_path / "export"
    export_dataset(dataset, output_dir, export_media=ExportMode.SKIP, as_zip=False)

    # Should succeed and create valid structure
    assert (output_dir / METADATA_FILE).exists()
    assert (output_dir / DATAFRAME_FILE).exists()

    # Import should work
    imported = import_dataset(output_dir, dtype=SimpleSample)
    assert len(imported) == 0


def test_export_large_dataset(tmp_path):
    """Test exporting larger dataset (performance check)."""

    class SimpleSample(Sample):
        value: int = numeric_field(dtype=pl.UInt16(), semantic="value")

    dataset = Dataset(SimpleSample)
    for i in range(1000):
        dataset.append(SimpleSample(value=i))

    output_dir = tmp_path / "export"
    export_dataset(dataset, output_dir, export_media=ExportMode.SKIP, as_zip=False)

    # Import and verify
    imported = import_dataset(output_dir, dtype=SimpleSample)
    assert len(imported) == 1000
    assert imported[0].value == 0
    assert imported[999].value == 999


def test_export_with_special_characters_in_paths(tmp_path):
    """Test handling of special characters in file paths."""

    class PathSample(Sample):
        image_path: str = image_path_field()

    # Create image with special characters in name
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    img_path = source_dir / "image with spaces & special.png"
    PILImage.fromarray(np.zeros((10, 10, 3), dtype=np.uint8)).save(img_path)

    dataset = Dataset(PathSample)
    dataset.append(PathSample(image_path=str(img_path)))

    output_dir = tmp_path / "export"
    export_dataset(dataset, output_dir, export_media=ExportMode.COPY, as_zip=False)

    # Should handle gracefully
    imported = import_dataset(output_dir, dtype=PathSample)
    assert len(imported) == 1


def test_zip_path_without_zip_extension(tmp_path):
    """Test that as_zip=True adds .zip extension if missing."""

    class SimpleSample(Sample):
        label: int = label_field()

    dataset = Dataset(SimpleSample, categories={"label": LABEL_CATEGORIES})
    dataset.append(SimpleSample(label=1))

    output_path = tmp_path / "export_no_ext"
    export_dataset(dataset, output_path, export_media=ExportMode.SKIP, as_zip=True)

    # Should create .zip file
    expected_zip = tmp_path / "export_no_ext/dataset.zip"
    assert expected_zip.exists()
    assert expected_zip.suffix == ".zip"


def test_export_import_different_field_types(tmp_path):
    """Test export/import with a sample containing one of every field type."""

    # Create source image for image_path field
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source_img_path = source_dir / "source_image.png"
    PILImage.fromarray(np.ones((20, 30, 3), dtype=np.uint8) * 100).save(source_img_path)

    class ComprehensiveSample(Sample):
        label: int = label_field()
        score: float = numeric_field(semantic="score")
        subset: Subset = subset_field()

        tensor: np.ndarray = tensor_field(dtype=pl.Float32())
        bbox: np.ndarray = bbox_field(dtype=pl.Float32(), normalize=False)
        rotated_bbox: np.ndarray = rotated_bbox_field(dtype=pl.Float32())
        keypoints: np.ndarray = keypoints_field(dtype=pl.Float32())

        image_callable: Callable[[], np.ndarray] = image_callable_field()
        image_path: str = image_path_field()
        image_info: ImageInfo = image_info_field()

        mask_callable: Callable[[], np.ndarray] = mask_callable_field()
        instance_mask_callable: np.ndarray | Callable[[], np.ndarray] = instance_mask_callable_field()

        tile: TileInfo = tile_field()

    # Create helper functions for callables
    def make_image():
        return np.full((20, 30, 3), 150, dtype=np.uint8)

    def make_mask():
        return np.ones((20, 30), dtype=np.uint8) * 255

    def make_instance_mask():
        return np.ones((20, 30), dtype=np.uint8) * 128

    # Create dataset with sample containing all field types
    dataset = Dataset(
        ComprehensiveSample,
        categories={
            "label": LABEL_CATEGORIES,
            "mask_callable": MASK_CATEGORIES,
            "instance_mask_callable": MASK_CATEGORIES,
        },
    )
    sample = ComprehensiveSample(
        label=1,
        score=0.95,
        subset=Subset.TRAINING,
        tensor=np.array([1.0, 2.0, 3.0], dtype=np.float32),
        bbox=np.array([[10.0, 20.0, 50.0, 60.0]], dtype=np.float32),
        rotated_bbox=np.array([[25.0, 35.0, 40.0, 50.0, 0.5]], dtype=np.float32),
        keypoints=np.array([[15.0, 25.0, 1.0], [35.0, 45.0, 1.0]], dtype=np.float32),
        image_callable=make_image,
        image_path=str(source_img_path),
        image_info=ImageInfo(width=30, height=20),
        mask_callable=make_mask,
        instance_mask_callable=make_instance_mask,
        tile=TileInfo(source_sample_idx=0, x=10, y=20, width=30, height=40),
    )
    dataset.append(sample)

    # Export dataset
    export_dir = tmp_path / "export"
    export_dataset(dataset, export_dir, export_media=ExportMode.COPY, as_zip=False)

    # Verify export structure
    assert (export_dir / METADATA_FILE).exists()
    assert (export_dir / DATAFRAME_FILE).exists()
    assert (export_dir / IMAGES_DIR).exists()

    # Verify images were exported
    images_dir = export_dir / IMAGES_DIR
    assert (images_dir / "image_callable_000000.png").exists()
    assert (images_dir / "source_image.png").exists()  # ImagePathField preserves original filename
    assert (images_dir / "mask_callable_000000.png").exists()
    assert (images_dir / "instance_mask_callable_000000.png").exists()

    # Import dataset
    imported_dataset = import_dataset(export_dir, dtype=ComprehensiveSample)

    # Verify dataset length
    assert len(imported_dataset) == 1

    # Get the imported sample
    imported_sample = imported_dataset[0]

    # Verify basic fields
    assert imported_sample.label == sample.label
    assert imported_sample.score == pytest.approx(sample.score)
    assert imported_sample.subset == sample.subset

    # Verify tensor
    np.testing.assert_array_equal(sample.tensor, imported_sample.tensor)

    # Verify bounding boxes
    np.testing.assert_array_equal(sample.bbox, imported_sample.bbox)
    np.testing.assert_array_equal(sample.rotated_bbox, imported_sample.rotated_bbox)

    # Verify keypoints
    np.testing.assert_array_equal(sample.keypoints, imported_sample.keypoints)

    # Verify image callable
    assert callable(imported_sample.image_callable)
    img = imported_sample.image_callable()
    expected_img = sample.image_callable()
    np.testing.assert_array_equal(expected_img, img)

    # Verify image path was updated (content matches original source image)
    assert imported_sample.image_path is not None
    assert Path(imported_sample.image_path).exists()
    loaded_img = np.array(PILImage.open(imported_sample.image_path))
    original_loaded_img = np.array(PILImage.open(sample.image_path))
    np.testing.assert_array_equal(original_loaded_img, loaded_img)

    # Verify image info
    assert imported_sample.image_info.width == sample.image_info.width
    assert imported_sample.image_info.height == sample.image_info.height

    # Verify mask callable
    assert callable(imported_sample.mask_callable)
    mask = imported_sample.mask_callable()
    expected_mask = sample.mask_callable()
    np.testing.assert_array_equal(expected_mask, mask)

    # Verify instance mask callable
    assert callable(imported_sample.instance_mask_callable)
    inst_mask = imported_sample.instance_mask_callable()
    expected_inst_mask = sample.instance_mask_callable()
    np.testing.assert_array_equal(expected_inst_mask, inst_mask)

    # Verify tile info
    assert imported_sample.tile.source_sample_idx == sample.tile.source_sample_idx
    assert imported_sample.tile.x == sample.tile.x
    assert imported_sample.tile.y == sample.tile.y
    assert imported_sample.tile.width == sample.tile.width
    assert imported_sample.tile.height == sample.tile.height


def test_export_dataset_export_media_copy_and_skip(tmp_path):
    """
    Test that export_dataset stores relative paths in Parquet when export_media=ExportMode.COPY
    and original absolute paths when export_media=ExportMode.SKIP.
    """
    # 1. Setup: Create a temporary source image
    source_dir = tmp_path / "source_media"
    source_dir.mkdir()
    source_img_path = source_dir / "cat1.jpg"
    PILImage.fromarray(np.zeros((10, 10, 3), dtype=np.uint8)).save(source_img_path)

    class SampleWithPath(Sample):
        img: str = image_path_field()

    dataset = Dataset(SampleWithPath)
    dataset.append(SampleWithPath(img=str(source_img_path)))

    # 2. Case: export_media=ExportMode.COPY
    # The path in Parquet should be relative to the export directory
    export_dir_true = tmp_path / "exported_with_images"
    export_dataset(
        dataset=dataset,
        output_path=export_dir_true,
        as_zip=False,
        export_media=ExportMode.COPY,
    )

    df_true = pl.read_parquet(export_dir_true / DATAFRAME_FILE)
    exported_path = df_true["img"][0]

    assert exported_path is not None
    assert exported_path != str(source_img_path)
    # ImagePathField preserves the original filename
    assert exported_path == "cat1.jpg"

    # Check if the file exists on disk
    exported_file_on_disk = export_dir_true / IMAGES_DIR / exported_path
    assert exported_file_on_disk.exists()

    # 3. Case: export_media=ExportMode.SKIP
    # The path in Parquet should remain the original absolute path
    export_dir_false = tmp_path / "exported_without_images"
    export_dataset(
        dataset=dataset,
        output_path=export_dir_false,
        as_zip=False,
        export_media=ExportMode.SKIP,
    )

    df_false = pl.read_parquet(export_dir_false / DATAFRAME_FILE)
    assert df_false["img"][0] == str(source_img_path)
    assert not (export_dir_false / IMAGES_DIR).exists()


# ---------------------------------------------------------------------------
# Tests for automatic dtype detection (_get_registered_samples,
# _match_dtype_from_schema, register_sample)
# ---------------------------------------------------------------------------


def test_get_registered_samples_returns_empty_without_registration():
    """_get_registered_samples should return empty list when no classes are registered."""
    # Clear any existing registrations for this test
    original_registry = _sample_registry.copy()
    _sample_registry.clear()
    try:
        result = _get_registered_samples()
        assert result == []
    finally:
        _sample_registry.update(original_registry)


def test_get_registered_samples_returns_registered_classes():
    """_get_registered_samples should return classes that were explicitly registered."""

    class RegisteredChild(Sample):
        label: int = label_field()

    _sample_registry.discard(RegisteredChild)
    try:
        # Before registration, should not be in results
        assert RegisteredChild not in _get_registered_samples()

        # After registration, should be in results
        register_sample(RegisteredChild)
        assert RegisteredChild in _get_registered_samples()
    finally:
        _sample_registry.discard(RegisteredChild)


def test_get_registered_samples_does_not_include_base_sample():
    """The base Sample class itself should not appear in the result."""
    result = _get_registered_samples()
    assert Sample not in result


def test_match_dtype_from_schema_returns_matching_subclass():
    """_match_dtype_from_schema should return the subclass whose schema matches."""

    @register_sample
    class MatchMe(Sample):
        label: int = label_field()
        score: float = numeric_field(dtype=pl.Float32(), semantic="score")
        subset: Subset = subset_field()

    try:
        schema = MatchMe.infer_schema()
        result = _match_dtype_from_schema(schema)
        assert result is MatchMe
    finally:
        _sample_registry.discard(MatchMe)


def test_match_dtype_from_schema_falls_back_to_sample():
    """When no subclass matches, _match_dtype_from_schema should return Sample."""
    from getidata.fields.types import NumericField
    from getidata.schema import AttributeInfo, Schema

    # Build a schema that no existing subclass will match
    schema = Schema(
        attributes={
            "unique_xyz_field": AttributeInfo(
                type=int,
                field=NumericField(dtype=pl.Int64(), semantic="unique_xyz"),
            ),
            "another_unique_abc": AttributeInfo(
                type=float,
                field=NumericField(dtype=pl.Float64(), semantic="unique_abc"),
            ),
        }
    )
    result = _match_dtype_from_schema(schema)
    assert result is Sample


def test_register_sample_makes_class_discoverable():
    """register_sample should add a class to the registry so it is discoverable."""

    class ExternalSample(Sample):
        label: int = label_field()
        score: float = numeric_field(dtype=pl.Float32(), semantic="score")

    # Remove from registry in case a previous test registered it
    _sample_registry.discard(ExternalSample)

    register_sample(ExternalSample)
    try:
        assert ExternalSample in _sample_registry
        assert ExternalSample in _get_registered_samples()
    finally:
        _sample_registry.discard(ExternalSample)


def test_register_sample_works_as_decorator():
    """register_sample should work as a class decorator and return the class."""

    @register_sample
    class DecoratedSample(Sample):
        label: int = label_field()

    try:
        assert DecoratedSample in _sample_registry
        # The decorator should return the class unchanged
        assert issubclass(DecoratedSample, Sample)
    finally:
        _sample_registry.discard(DecoratedSample)


def test_import_without_dtype_falls_back_to_sample_for_unknown_schema(tmp_path):
    """When the exported schema doesn't match any subclass, dtype should fall back to Sample."""
    from getidata.fields.types import NumericField
    from getidata.schema import AttributeInfo, Schema

    # Create a dataset with a unique schema that won't match any subclass
    unique_schema = Schema(
        attributes={
            "weird_field_xyz": AttributeInfo(
                type=int,
                field=NumericField(dtype=pl.Int64(), semantic="weird_xyz"),
            ),
        }
    )
    dataset = Dataset(unique_schema)
    dataset.append(Sample(weird_field_xyz=42))

    export_dir = tmp_path / "export"
    export_dataset(dataset, export_dir, export_media=ExportMode.SKIP, as_zip=False)

    imported_dataset = import_dataset(export_dir, dtype=None)
    assert len(imported_dataset) == 1
    assert imported_dataset.dtype == Sample


def test_import_auto_detects_dtype_roundtrip(tmp_path):
    """Full roundtrip: export with a known Sample subclass, import without dtype, verify auto-detection."""

    @register_sample
    class AutoDetectSample(Sample):
        label: int = label_field()
        score: float = numeric_field(dtype=pl.Float32(), semantic="score")
        subset: Subset = subset_field()

    try:
        original_dataset = Dataset(AutoDetectSample, categories={"label": LABEL_CATEGORIES})
        original_dataset.append(AutoDetectSample(label=2, score=0.75, subset=Subset.TRAINING))

        export_dir = tmp_path / "export"
        export_dataset(original_dataset, export_dir, export_media=ExportMode.SKIP, as_zip=False)

        imported_dataset = import_dataset(export_dir)  # no dtype
        # Should auto-detect a matching subclass (not fall back to base Sample)
        assert imported_dataset.dtype is not Sample
        assert issubclass(imported_dataset.dtype, Sample)
        assert len(imported_dataset) == 1
    finally:
        _sample_registry.discard(AutoDetectSample)


def test_match_dtype_distinguishes_similar_samples_with_different_field_configs():
    """
    _match_dtype_from_schema should correctly distinguish between Sample subclasses
    that have the same field names but different field configurations.
    """

    @register_sample
    class ClassificationSample(Sample):
        label: int | None = label_field(dtype=pl.UInt8(), is_list=False)
        confidence: float | None = numeric_field(dtype=pl.Float32(), semantic="confidence")

    @register_sample
    class MultilabelClassificationSample(Sample):
        label: list[int] = label_field(dtype=pl.UInt8(), multi_label=True)
        confidence: list[float] | None = numeric_field(dtype=pl.Float32(), is_list=True, semantic="confidence")

    try:
        classification_schema = ClassificationSample.infer_schema()
        result = _match_dtype_from_schema(classification_schema)
        assert result is ClassificationSample

        multilabel_schema = MultilabelClassificationSample.infer_schema()
        result = _match_dtype_from_schema(multilabel_schema)
        assert result is MultilabelClassificationSample

    finally:
        _sample_registry.discard(ClassificationSample)
        _sample_registry.discard(MultilabelClassificationSample)


def test_import_zip_extracts_to_directory_next_to_zip_by_default(tmp_path):
    """Test that importing a zip file extracts to a directory next to the zip with the same name."""

    class ImageSample(Sample):
        image: Callable[[], np.ndarray] = image_callable_field()
        label: int = label_field()

    def make_image():
        return np.zeros((20, 30, 3), dtype=np.uint8)

    # Create and export dataset as zip
    original_dataset = Dataset(ImageSample, categories={"label": LABEL_CATEGORIES})
    original_dataset.append(ImageSample(image=make_image, label=1))
    original_dataset.append(ImageSample(image=make_image, label=2))

    export_zip = tmp_path / "my_dataset.zip"
    export_dataset(original_dataset, export_zip, export_media=ExportMode.COPY, as_zip=True)

    # Import from zip (no extract_dir provided)
    imported_dataset = import_dataset(export_zip, dtype=ImageSample)

    # Verify the dataset was extracted to a directory next to the zip
    expected_extract_dir = tmp_path / "my_dataset"
    assert expected_extract_dir.exists()
    assert expected_extract_dir.is_dir()
    assert (expected_extract_dir / METADATA_FILE).exists()
    assert (expected_extract_dir / DATAFRAME_FILE).exists()
    assert (expected_extract_dir / IMAGES_DIR).exists()

    # Verify the dataset works correctly
    assert len(imported_dataset) == 2
    sample0 = imported_dataset[0]
    assert sample0.label == 1
    assert callable(sample0.image)
    img0 = sample0.image()
    assert img0.shape == (20, 30, 3)

    sample1 = imported_dataset[1]
    assert sample1.label == 2
    assert callable(sample1.image)
    img1 = sample1.image()
    assert img1.shape == (20, 30, 3)


def test_import_zip_extracts_to_custom_directory_when_extract_dir_provided(tmp_path):
    """Test that importing a zip file extracts to a custom directory when extract_dir is provided."""

    class ImageSample(Sample):
        image: Callable[[], np.ndarray] = image_callable_field()
        label: int = label_field()

    def make_image():
        return np.zeros((25, 35, 3), dtype=np.uint8)

    # Create and export dataset as zip
    original_dataset = Dataset(ImageSample, categories={"label": LABEL_CATEGORIES})
    original_dataset.append(ImageSample(image=make_image, label=2))

    export_zip = tmp_path / "dataset.zip"
    export_dataset(original_dataset, export_zip, export_media=ExportMode.COPY, as_zip=True)

    # Import with custom extract_dir
    custom_extract_dir = tmp_path / "custom" / "location"
    imported_dataset = import_dataset(export_zip, dtype=ImageSample, extract_dir=custom_extract_dir)

    # Verify the dataset was extracted to the custom directory
    assert custom_extract_dir.exists()
    assert custom_extract_dir.is_dir()
    assert (custom_extract_dir / METADATA_FILE).exists()
    assert (custom_extract_dir / DATAFRAME_FILE).exists()
    assert (custom_extract_dir / IMAGES_DIR).exists()

    # Verify the default location was NOT created
    default_extract_dir = tmp_path / "dataset"
    assert not default_extract_dir.exists()

    # Verify the dataset works correctly
    assert len(imported_dataset) == 1
    sample = imported_dataset[0]
    assert sample.label == 2
    assert callable(sample.image)
    img = sample.image()
    assert img.shape == (25, 35, 3)


def test_import_zip_images_accessible_after_import(tmp_path):
    """Test that images from a zip import are accessible after import."""

    class ImageSample(Sample):
        image: Callable[[], np.ndarray] = image_callable_field()
        label: int = label_field()

    def make_image(value):
        def load():
            img = np.zeros((10, 10, 3), dtype=np.uint8)
            img[:, :, 0] = value
            return img

        return load

    # Create and export dataset as zip
    original_dataset = Dataset(ImageSample, categories={"label": LABEL_CATEGORIES})
    original_dataset.append(ImageSample(image=make_image(100), label=1))
    original_dataset.append(ImageSample(image=make_image(200), label=2))

    export_zip = tmp_path / "test_dataset.zip"
    export_dataset(original_dataset, export_zip, export_media=ExportMode.COPY, as_zip=True)

    # Import from zip
    imported_dataset = import_dataset(export_zip, dtype=ImageSample)

    # Access images multiple times to verify they persist
    for _ in range(2):
        img0 = imported_dataset[0].image()
        img1 = imported_dataset[1].image()
        assert img0[0, 0, 0] == 100
        assert img1[0, 0, 0] == 200


def test_import_zip_extract_dir_is_ignored_for_directory_input(tmp_path):
    """Test that extract_dir parameter is ignored when input is a directory (not a zip)."""

    class SimpleSample(Sample):
        label: int = label_field()

    # Export to directory (not zip)
    original_dataset = Dataset(SimpleSample, categories={"label": LABEL_CATEGORIES})
    original_dataset.append(SimpleSample(label=3))

    export_dir = tmp_path / "exported"
    export_dataset(original_dataset, export_dir, export_media=ExportMode.SKIP, as_zip=False)

    # Import from directory with extract_dir (should be ignored)
    custom_dir = tmp_path / "should_not_be_created"
    imported_dataset = import_dataset(export_dir, dtype=SimpleSample, extract_dir=custom_dir)

    # Verify the custom directory was NOT created (since input was a directory, not zip)
    assert not custom_dir.exists()

    # Verify the dataset works correctly
    assert len(imported_dataset) == 1
    assert imported_dataset[0].label == 3


# ============================================================================
# Video Export/Import Tests
# ============================================================================

# Path to test video in assets
TEST_VIDEO_PATH = Path(__file__).parent.parent / "assets" / "cvat_dataset" / "test.mp4"


def test_export_video_frame_path_field_reference_mode(tmp_path):
    """Test exporting VideoFramePathField in reference mode (keeps original paths)."""

    class VideoSample(Sample):
        frame: LazyVideoFrame = video_frame_path_field()
        label: int = label_field()

    dataset = Dataset(VideoSample, categories={"label": LABEL_CATEGORIES})
    for i in range(3):
        dataset.append(
            VideoSample(
                frame=LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=i),
                label=i,
            )
        )

    output_dir = tmp_path / "export"
    export_dataset(dataset, output_dir, export_media=ExportMode.REFERENCE, as_zip=False)

    # Check metadata
    with open(output_dir / METADATA_FILE) as f:
        metadata = json.load(f)

    assert "videos" in metadata
    assert metadata["videos"]["export_mode"] == "reference"
    assert "frame" in metadata["videos"]["fields"]

    # Video directory should not exist in reference mode
    assert not (output_dir / VIDEOS_DIR).exists()


def test_export_video_frame_path_field_copy_mode(tmp_path):
    """Test exporting VideoFramePathField in copy mode (copies video files)."""

    class VideoSample(Sample):
        frame: LazyVideoFrame = video_frame_path_field()
        label: int = label_field()

    dataset = Dataset(VideoSample, categories={"label": LABEL_CATEGORIES})
    for i in range(3):
        dataset.append(
            VideoSample(
                frame=LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=i),
                label=i,
            )
        )

    output_dir = tmp_path / "export"
    export_dataset(dataset, output_dir, export_media=ExportMode.COPY, as_zip=False)

    # Check that video was copied
    videos_dir = output_dir / VIDEOS_DIR
    assert videos_dir.exists()
    video_files = list(videos_dir.glob("*.mp4"))
    assert len(video_files) == 1


def test_export_import_video_frames_roundtrip(tmp_path):
    """Test complete export/import roundtrip for video frames."""

    class VideoSample(Sample):
        frame: LazyVideoFrame = video_frame_path_field()
        label: int = label_field()

    original_dataset = Dataset(VideoSample, categories={"label": LABEL_CATEGORIES})
    for i in range(5):
        original_dataset.append(
            VideoSample(
                frame=LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=i * 2),
                label=i,
            )
        )

    # Export
    output_dir = tmp_path / "export"
    export_dataset(original_dataset, output_dir, export_media=ExportMode.REFERENCE, as_zip=False)

    # Import
    imported_dataset = import_dataset(output_dir, dtype=VideoSample)

    # Verify
    assert len(imported_dataset) == 5
    for i in range(5):
        sample = imported_dataset[i]
        assert sample.label == i
        assert isinstance(sample.frame, LazyVideoFrame)
        assert sample.frame.frame_index == i * 2


def test_export_import_video_to_zip(tmp_path):
    """Test exporting and importing video dataset as ZIP."""

    class VideoSample(Sample):
        frame: LazyVideoFrame = video_frame_path_field()
        label: int = label_field()

    dataset = Dataset(VideoSample, categories={"label": LABEL_CATEGORIES})
    for i in range(3):
        dataset.append(
            VideoSample(
                frame=LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=i),
                label=i,
            )
        )

    # Export as ZIP with copy mode
    zip_path = tmp_path / "dataset.zip"
    export_dataset(dataset, zip_path, export_media=ExportMode.COPY, as_zip=True)

    assert zip_path.exists()

    # Verify ZIP contents
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        assert METADATA_FILE in names
        assert DATAFRAME_FILE in names
        # Check video file was included
        video_files = [n for n in names if n.startswith(VIDEOS_DIR)]
        assert len(video_files) >= 1

    # Import from ZIP
    imported = import_dataset(zip_path, dtype=VideoSample)

    assert len(imported) == 3


def test_export_empty_video_fields(tmp_path):
    """Test exporting dataset with video fields but no video samples."""

    class VideoSample(Sample):
        frame: LazyVideoFrame = video_frame_path_field()
        label: int = label_field()

    dataset = Dataset(VideoSample, categories={"label": LABEL_CATEGORIES})
    # Add sample with None frame
    dataset.df = pl.DataFrame(
        {
            "frame": [None],
            "frame_frame_index": [None],
            "label": [0],
        }
    )

    output_dir = tmp_path / "export"
    export_dataset(dataset, output_dir, export_media=ExportMode.COPY, as_zip=False)

    # Should succeed without creating videos directory
    assert (output_dir / METADATA_FILE).exists()
    assert (output_dir / DATAFRAME_FILE).exists()


def test_get_video_fields_identifies_video_fields(tmp_path):
    """Test that _get_video_fields correctly identifies video-related fields."""

    class MixedSample(Sample):
        frame: LazyVideoFrame = video_frame_path_field()
        image: str = image_path_field()
        label: int = label_field()

    dataset = Dataset(MixedSample)

    video_fields = _get_video_fields(dataset)
    field_names = [name for name, _ in video_fields]

    assert "frame" in field_names
    assert "image" not in field_names
    assert "label" not in field_names


def test_export_import_media_path_field_with_videos(tmp_path):
    """Test export/import of MediaPathField with video frames."""

    class MediaSample(Sample):
        media: LazyVideoFrame | LazyImage = media_path_field()
        label: int = label_field()

    dataset = Dataset(MediaSample, categories={"label": LABEL_CATEGORIES})

    # Add video frame
    dataset.append(
        MediaSample(
            media=LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=5),
            label=0,
        )
    )

    # Export
    output_dir = tmp_path / "export"
    export_dataset(dataset, output_dir, export_media=ExportMode.COPY, as_zip=False)

    # Import
    imported = import_dataset(output_dir, dtype=MediaSample)

    assert len(imported) == 1
    sample = imported[0]
    assert isinstance(sample.media, LazyVideoFrame)
    assert sample.media.frame_index == 5


def test_export_import_media_path_field_mixed_content(tmp_path):
    """Test export/import of MediaPathField with both images and video frames."""

    class MediaSample(Sample):
        media: LazyVideoFrame | LazyImage = media_path_field()
        label: int = label_field()

    # Create a test image
    test_image_path = tmp_path / "test_image.png"
    img = np.zeros((50, 50, 3), dtype=np.uint8)
    img[:, :, 0] = 128  # Red channel
    PILImage.fromarray(img).save(test_image_path)

    dataset = Dataset(MediaSample, categories={"label": LABEL_CATEGORIES})

    # Add image sample
    dataset.append(
        MediaSample(
            media=LazyImage(path=str(test_image_path)),
            label=0,
        )
    )

    # Add video frame sample
    dataset.append(
        MediaSample(
            media=LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=10),
            label=1,
        )
    )

    # Export
    output_dir = tmp_path / "export"
    export_dataset(dataset, output_dir, export_media=ExportMode.COPY, as_zip=False)

    # Import
    imported = import_dataset(output_dir, dtype=MediaSample)

    assert len(imported) == 2

    # First sample should be image
    sample0 = imported[0]
    assert sample0.label == 0
    # After import, image paths become strings pointing to exported images

    # Second sample should be video frame
    sample1 = imported[1]
    assert sample1.label == 1
    assert isinstance(sample1.media, LazyVideoFrame)
    assert sample1.media.frame_index == 10


def test_export_videos_copy_mode_creates_correct_paths(tmp_path):
    """Test that copy mode creates correct relative paths in the DataFrame."""

    class VideoSample(Sample):
        frame: LazyVideoFrame = video_frame_path_field()

    dataset = Dataset(VideoSample)
    dataset.append(VideoSample(frame=LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0)))

    output_dir = tmp_path / "export"
    export_dataset(dataset, output_dir, export_media=ExportMode.COPY, as_zip=False)

    # Load the parquet and check the path is relative
    df = pl.read_parquet(output_dir / DATAFRAME_FILE)
    frame_path = df["frame"][0]

    # Path should be relative to export dir and start with videos/
    assert frame_path.startswith(VIDEOS_DIR + "/")


def test_reconstruct_video_fields_uses_sanitized_fallback_path(tmp_path):
    """Video path reconstruction should fall back to sanitized extracted names."""
    exported_rel_path = f"{VIDEOS_DIR}/clip\x01name.mp4"
    sanitized_rel_path = f"{VIDEOS_DIR}/clip_name.mp4"
    sanitized_abs_path = tmp_path / sanitized_rel_path
    sanitized_abs_path.parent.mkdir(parents=True, exist_ok=True)
    sanitized_abs_path.touch()

    df = pl.DataFrame({"frame": [exported_rel_path], "frame_frame_index": [0]})
    metadata = {"videos": {"fields": ["frame"], "export_mode": "copy"}}

    updated_df = _reconstruct_video_fields(df, metadata, tmp_path)

    assert updated_df["frame"][0] == str(sanitized_abs_path)


def test_export_video_error_missing_video_file(tmp_path):
    """Error when a video file does not exist and ignore_missing_media=False."""

    class VideoSample(Sample):
        frame: LazyVideoFrame = video_frame_path_field()
        label: int = label_field()

    dataset = Dataset(VideoSample, categories={"label": LABEL_CATEGORIES})
    missing_video_path = tmp_path / "does_not_exist.mp4"
    dataset.append(
        VideoSample(
            frame=LazyVideoFrame(video_path=str(missing_video_path), frame_index=0),
            label=0,
        )
    )

    output_dir = tmp_path / "export"
    with pytest.raises(ValueError, match="Video file not found"):
        export_dataset(dataset, output_dir, export_media=ExportMode.COPY, as_zip=False)


def test_export_video_ignore_missing_media_skips_missing_video(tmp_path):
    """Missing video file is skipped when ignore_missing_media=True."""

    class VideoSample(Sample):
        frame: LazyVideoFrame = video_frame_path_field()
        label: int = label_field()

    dataset = Dataset(VideoSample, categories={"label": LABEL_CATEGORIES})

    # Add one valid video frame and one missing
    missing_video_path = tmp_path / "does_not_exist.mp4"
    dataset.append(
        VideoSample(
            frame=LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0),
            label=0,
        )
    )
    dataset.append(
        VideoSample(
            frame=LazyVideoFrame(video_path=str(missing_video_path), frame_index=0),
            label=1,
        )
    )

    output_dir = tmp_path / "export"
    # Should not raise when ignore_missing_media=True
    export_dataset(
        dataset,
        output_dir,
        export_media=ExportMode.COPY,
        as_zip=False,
        ignore_missing_media=True,
    )

    # Check that the valid video was copied
    videos_dir = output_dir / VIDEOS_DIR
    assert videos_dir.exists()
    video_files = list(videos_dir.glob("*.mp4"))
    assert len(video_files) == 1


def test_export_mixed_media_ignore_missing_media(tmp_path):
    """Test ignore_missing_media works for both images and videos together."""

    class MixedMediaSample(Sample):
        image: Callable[[], np.ndarray] = image_callable_field()
        frame: LazyVideoFrame = video_frame_path_field()
        label: int = label_field()

    def good_image():
        return np.zeros((10, 10, 3), dtype=np.uint8)

    def bad_image():
        raise RuntimeError("failed to generate image")

    missing_video_path = tmp_path / "does_not_exist.mp4"

    dataset = Dataset(MixedMediaSample, categories={"label": LABEL_CATEGORIES})

    # Valid image, valid video
    dataset.append(
        MixedMediaSample(
            image=good_image,
            frame=LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=0),
            label=0,
        )
    )

    # Bad image, valid video
    dataset.append(
        MixedMediaSample(
            image=bad_image,
            frame=LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=1),
            label=1,
        )
    )

    # Valid image, missing video
    dataset.append(
        MixedMediaSample(
            image=good_image,
            frame=LazyVideoFrame(video_path=str(missing_video_path), frame_index=0),
            label=2,
        )
    )

    output_dir = tmp_path / "export"
    # Should not raise when ignore_missing_media=True
    export_dataset(
        dataset,
        output_dir,
        export_media=ExportMode.COPY,
        as_zip=False,
        ignore_missing_media=True,
    )

    # Check that valid video was copied
    videos_dir = output_dir / VIDEOS_DIR
    assert videos_dir.exists()
    video_files = list(videos_dir.glob("*.mp4"))
    assert len(video_files) == 1

    # Check that valid images were exported
    images_dir = output_dir / IMAGES_DIR
    assert images_dir.exists()
    image_files = list(images_dir.glob("image_*.png"))
    assert len(image_files) == 2  # Indices 0 and 2


def test_video_to_images_end_to_end_workflow(tmp_path):
    """End-to-end workflow: video frames → convert to images → export → import → ZIP."""
    from getidata.fields import image_field

    # Step 1: Define sample classes
    class VideoFrameSample(Sample):
        frame: LazyVideoFrame = video_frame_path_field()
        label: int = label_field()

    class ImageTensorSample(Sample):
        image: np.ndarray | None = image_field(dtype=pl.UInt8(), format="RGB")
        label: int = label_field()

    # Step 2: Create dataset from video frames
    source_dataset = Dataset(VideoFrameSample, categories={"label": LABEL_CATEGORIES})
    for i in range(3):
        source_dataset.append(
            VideoFrameSample(
                frame=LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=i),
                label=i % 3,
            )
        )

    assert len(source_dataset) == 3

    # Step 3: Convert to image tensor format
    converted_dataset = source_dataset.convert_to_schema(ImageTensorSample)

    # Verify conversion works (accessing samples loads image data)
    for i in range(3):
        sample = converted_dataset[i]
        assert sample.image is not None
        assert len(sample.image.shape) == 3  # H, W, C
        assert sample.label == i % 3

    # Step 4: Export to directory
    export_path = tmp_path / "exported"
    export_dataset(
        source_dataset,  # Export original video frame dataset
        export_path,
        export_media=ExportMode.COPY,
    )

    # Verify videos were copied
    videos_dir = export_path / VIDEOS_DIR
    assert videos_dir.exists()
    video_files = list(videos_dir.glob("*.mp4"))
    assert len(video_files) == 1

    # Step 5: Import from directory
    imported_dataset = import_dataset(export_path, dtype=VideoFrameSample)
    assert len(imported_dataset) == 3

    # Verify data integrity
    for i in range(3):
        orig = source_dataset[i]
        imp = imported_dataset[i]
        assert orig.label == imp.label

    # Step 6: Export as ZIP
    zip_path = tmp_path / "dataset.zip"
    export_dataset(
        imported_dataset,
        zip_path,
        export_media=ExportMode.REFERENCE,
        as_zip=True,
    )

    assert zip_path.exists()

    # Step 7: Import from ZIP
    extract_dir = tmp_path / "extracted"
    from_zip = import_dataset(zip_path, dtype=VideoFrameSample, extract_dir=extract_dir)
    assert len(from_zip) == 3


def test_multiple_videos_export_import_workflow(tmp_path):
    """Test export/import with frames from multiple videos."""

    class VideoSample(Sample):
        frame: LazyVideoFrame = video_frame_path_field()
        label: int = label_field()

    # Create dataset with frames from same video (simulating multiple videos)
    dataset = Dataset(VideoSample, categories={"label": LABEL_CATEGORIES})

    # Add multiple frames from the test video
    for frame_idx in range(5):
        dataset.append(
            VideoSample(
                frame=LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=frame_idx),
                label=frame_idx % 3,
            )
        )

    assert len(dataset) == 5

    # Export with video copy
    export_path = tmp_path / "multi_video_export"
    export_dataset(
        dataset,
        export_path,
        export_media=ExportMode.COPY,
    )

    # Verify video was copied
    videos_dir = export_path / VIDEOS_DIR
    assert videos_dir.exists()
    video_files = list(videos_dir.glob("*.mp4"))
    assert len(video_files) == 1

    # Import and verify
    imported = import_dataset(export_path, dtype=VideoSample)
    assert len(imported) == 5

    # Verify all samples accessible
    for i, sample in enumerate(imported):
        assert sample.label == i % 3
        assert isinstance(sample.frame, LazyVideoFrame)


def test_mixed_media_dataset_export_import(tmp_path):
    """Test export/import with mixed images and video frames."""

    class MixedSample(Sample):
        media: LazyImage | LazyVideoFrame = media_path_field()
        label: int = label_field()

    # Create test image
    test_image_path = tmp_path / "test_image.jpg"
    test_img = PILImage.new("RGB", (100, 100), color="red")
    test_img.save(test_image_path)

    dataset = Dataset(MixedSample, categories={"label": LABEL_CATEGORIES})

    # Add image sample
    dataset.append(
        MixedSample(
            media=LazyImage(str(test_image_path)),
            label=0,
        )
    )

    # Add video frame samples
    for i in range(2):
        dataset.append(
            MixedSample(
                media=LazyVideoFrame(video_path=str(TEST_VIDEO_PATH), frame_index=i),
                label=i + 1,
            )
        )

    assert len(dataset) == 3

    # Export with both image and video copy
    export_path = tmp_path / "mixed_export"
    export_dataset(
        dataset,
        export_path,
        export_media=ExportMode.COPY,
    )

    # Verify both images and videos directories exist
    assert (export_path / IMAGES_DIR).exists()
    assert (export_path / VIDEOS_DIR).exists()

    # Verify image was copied
    image_files = list((export_path / IMAGES_DIR).glob("*"))
    assert len(image_files) == 1

    # Verify video was copied
    video_files = list((export_path / VIDEOS_DIR).glob("*.mp4"))
    assert len(video_files) == 1

    # Import and verify
    imported = import_dataset(export_path, dtype=MixedSample)
    assert len(imported) == 3

    # Verify sample types
    assert imported[0].label == 0  # Image sample
    assert imported[1].label == 1  # Video frame
    assert imported[2].label == 2  # Video frame


# ============================================================================
# Automatic Format Detection Tests
# ============================================================================


def test_import_dataset_auto_detects_coco_format(tmp_path):
    """Test that import_dataset automatically detects and loads COCO format datasets."""
    # Create a minimal COCO dataset structure
    annotations_dir = tmp_path / "annotations"
    annotations_dir.mkdir()
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    # Create a test image
    img = PILImage.new("RGB", (100, 100), color="red")
    img.save(images_dir / "test.jpg")

    # Create COCO annotation file
    coco_annotations = {
        "images": [{"id": 1, "file_name": "test.jpg", "width": 100, "height": 100}],
        "annotations": [
            {"id": 1, "image_id": 1, "category_id": 1, "bbox": [10, 20, 30, 40], "area": 1200, "iscrowd": 0}
        ],
        "categories": [{"id": 1, "name": "cat", "supercategory": "animal"}],
    }

    with open(annotations_dir / "instances.json", "w") as f:
        json.dump(coco_annotations, f)

    # Import using auto-detection
    dataset = import_dataset(tmp_path)

    # Verify the dataset was loaded correctly
    assert len(dataset) == 1


def test_import_and_export_coco_with_subset_image_dirs(tmp_path):
    """Test import and export of COCO datasets where images are in subset subdirectories."""
    annotations_dir = tmp_path / "coco" / "annotations"
    annotations_dir.mkdir(parents=True)
    images_dir = tmp_path / "coco" / "images" / "default"
    images_dir.mkdir(parents=True)

    # Create test images
    for i in range(3):
        img = PILImage.new("RGB", (100, 80), color="red")
        img.save(images_dir / f"image_{i:06d}.jpg")

    # Create COCO annotation file named instances_default.json
    coco_annotations = {
        "images": [{"id": idx, "file_name": f"image_{idx:06d}.jpg", "width": 100, "height": 80} for idx in range(3)],
        "annotations": [
            {
                "id": idx,
                "image_id": idx,
                "category_id": 1,
                "bbox": [10, 20, 30, 40],
                "area": 1200,
                "iscrowd": 0,
            }
            for idx in range(3)
        ],
        "categories": [{"id": 1, "name": "cat", "supercategory": "animal"}],
    }

    with open(annotations_dir / "instances_default.json", "w") as f:
        json.dump(coco_annotations, f)

    # Import using auto-detection — this should find images under images/default/
    dataset = import_dataset(tmp_path / "coco")
    assert len(dataset) == 3

    # Verify image data is accessible
    image_data = dataset[0].image.data
    assert image_data is not None
    assert image_data.shape == (80, 100, 3)

    # Export to a new directory — this should succeed (previously raised ValueError
    # because the resolved image path was missing the subset subdirectory)
    export_dir = tmp_path / "exported"
    export_dataset(dataset, output_path=export_dir, as_zip=False)

    # Verify the exported dataset has the expected structure
    assert (export_dir / METADATA_FILE).exists()
    assert (export_dir / DATAFRAME_FILE).exists()
    assert (export_dir / IMAGES_DIR).is_dir()

    # Verify exported images exist
    exported_images = list((export_dir / IMAGES_DIR).glob("*.jpg"))
    assert len(exported_images) == 3

    # Verify the exported dataset can be re-imported
    reimported = import_dataset(export_dir)
    assert len(reimported) == 3


def test_import_coco_with_multiple_subset_image_dirs(tmp_path):
    """Test import of COCO datasets with multiple subset subdirectories under images/.

    For example:
        annotations/instances_train.json
        annotations/instances_val.json
        images/train/img1.jpg
        images/val/img2.jpg
    """
    annotations_dir = tmp_path / "annotations"
    annotations_dir.mkdir()
    train_images_dir = tmp_path / "images" / "train"
    train_images_dir.mkdir(parents=True)
    val_images_dir = tmp_path / "images" / "val"
    val_images_dir.mkdir(parents=True)

    # Create images in each subset directory
    img = PILImage.new("RGB", (50, 50), color="blue")
    img.save(train_images_dir / "train_img.jpg")
    img.save(val_images_dir / "val_img.jpg")

    # Create annotation files for each subset
    train_annotations = {
        "images": [{"id": 1, "file_name": "train_img.jpg", "width": 50, "height": 50}],
        "annotations": [{"id": 1, "image_id": 1, "category_id": 1, "bbox": [5, 5, 10, 10], "area": 100, "iscrowd": 0}],
        "categories": [{"id": 1, "name": "dog"}],
    }
    val_annotations = {
        "images": [{"id": 1, "file_name": "val_img.jpg", "width": 50, "height": 50}],
        "annotations": [{"id": 1, "image_id": 1, "category_id": 1, "bbox": [5, 5, 10, 10], "area": 100, "iscrowd": 0}],
        "categories": [{"id": 1, "name": "dog"}],
    }

    with open(annotations_dir / "instances_train.json", "w") as f:
        json.dump(train_annotations, f)
    with open(annotations_dir / "instances_val.json", "w") as f:
        json.dump(val_annotations, f)

    # Import using auto-detection — should detect subset-based layout
    dataset = import_dataset(tmp_path)
    assert len(dataset) == 2

    # Verify image data is accessible for both samples
    for i in range(len(dataset)):
        image_data = dataset[i].image.data
        assert image_data is not None
        assert image_data.shape == (50, 50, 3)


def test_import_dataset_auto_detects_yolo_ultralytics_format(tmp_path):
    """Test that import_dataset automatically detects and loads YOLO Ultralytics format datasets."""
    # Create Ultralytics YOLO structure
    images_dir = tmp_path / "images" / "train"
    images_dir.mkdir(parents=True)
    labels_dir = tmp_path / "labels" / "train"
    labels_dir.mkdir(parents=True)

    # Create a test image
    img = PILImage.new("RGB", (100, 100), color="blue")
    img.save(images_dir / "test.jpg")

    # Create label file (YOLO format: class x_center y_center width height)
    with open(labels_dir / "test.txt", "w") as f:
        f.write("0 0.5 0.5 0.3 0.4\n")

    # Create data.yaml
    import yaml

    data_yaml = {"names": ["cat", "dog"], "nc": 2, "train": "images/train", "val": "images/train"}
    with open(tmp_path / "data.yaml", "w") as f:
        yaml.dump(data_yaml, f)

    # Import using auto-detection
    dataset = import_dataset(tmp_path)

    # Verify the dataset was loaded correctly
    assert len(dataset) == 1


def test_import_dataset_auto_detects_yolo_traditional_format(tmp_path):
    """Test that import_dataset automatically detects and loads traditional YOLO format datasets."""
    # Create traditional YOLO structure
    train_dir = tmp_path / "obj_train_data"
    train_dir.mkdir()

    # Create a test image
    img = PILImage.new("RGB", (100, 100), color="green")
    img.save(train_dir / "test.jpg")

    # Create label file
    with open(train_dir / "test.txt", "w") as f:
        f.write("0 0.5 0.5 0.3 0.4\n")

    # Create obj.names
    with open(tmp_path / "obj.names", "w") as f:
        f.write("cat\ndog\n")

    # Import using auto-detection
    dataset = import_dataset(tmp_path)

    # Verify the dataset was loaded correctly
    assert len(dataset) == 1


def test_import_dataset_auto_detects_getidata_format(tmp_path):
    """Test that import_dataset correctly detects native getidata format."""

    class SimpleSample(Sample):
        label: int = label_field()

    # Create and export a getidata dataset
    original_dataset = Dataset(SimpleSample, categories={"label": LABEL_CATEGORIES})
    original_dataset.append(SimpleSample(label=1))
    original_dataset.append(SimpleSample(label=2))

    export_dir = tmp_path / "getidata_export"
    export_dataset(original_dataset, export_dir, export_media=ExportMode.SKIP)

    # Import using auto-detection
    imported_dataset = import_dataset(export_dir)

    # Verify the dataset was loaded correctly
    assert len(imported_dataset) == 2


def test_import_zip_with_nested_coco_structure(tmp_path):
    """Test that import_dataset handles zips with a single top-level folder.

    Many third-party dataset zips contain a single folder at the root level
    (e.g., dataset.zip -> dataset/annotations/...). The import should descend
    into such directories to find the actual dataset.
    """
    # Create a nested COCO structure: nested_folder/annotations/instances.json
    nested_folder = tmp_path / "coco_dataset"
    annotations_dir = nested_folder / "annotations"
    annotations_dir.mkdir(parents=True)
    images_dir = nested_folder / "images"
    images_dir.mkdir(parents=True)

    # Create a test image
    img = PILImage.new("RGB", (100, 100), color="red")
    img.save(images_dir / "test.jpg")

    # Create COCO annotation file
    coco_annotations = {
        "images": [{"id": 1, "file_name": "test.jpg", "width": 100, "height": 100}],
        "annotations": [
            {"id": 1, "image_id": 1, "category_id": 1, "bbox": [10, 20, 30, 40], "area": 1200, "iscrowd": 0}
        ],
        "categories": [{"id": 1, "name": "cat", "supercategory": "animal"}],
    }
    with open(annotations_dir / "instances.json", "w") as f:
        json.dump(coco_annotations, f)

    # Create a zip file with the nested structure
    zip_path = tmp_path / "nested_coco.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file_path in nested_folder.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(tmp_path)
                zipf.write(file_path, arcname)

    # Import using auto-detection - should descend into coco_dataset/
    extract_dir = tmp_path / "extracted"
    dataset = import_dataset(zip_path, extract_dir=extract_dir)

    # Verify the dataset was loaded correctly
    assert len(dataset) == 1


def test_export_dataset_raises_error_if_output_already_exists(tmp_path):
    """Test that export_dataset raises FileExistsError when the output already exists."""
    import shutil

    class SimpleSample(Sample):
        label: int = label_field()

    dataset = Dataset(SimpleSample, categories={"label": LABEL_CATEGORIES})
    dataset.append(SimpleSample(label=1))

    # Directory export: second call should fail
    output_dir = tmp_path / "export_dir"
    export_dataset(dataset, output_dir, export_media=ExportMode.SKIP, as_zip=False)
    with pytest.raises(FileExistsError, match="Output directory already exists"):
        export_dataset(dataset, output_dir, export_media=ExportMode.SKIP, as_zip=False)

    # After removing the directory, export should succeed again
    shutil.rmtree(output_dir)
    export_dataset(dataset, output_dir, export_media=ExportMode.SKIP, as_zip=False)
    assert (output_dir / METADATA_FILE).exists()

    # Zip export with .zip suffix: second call should fail
    output_zip = tmp_path / "export.zip"
    export_dataset(dataset, output_zip, export_media=ExportMode.SKIP, as_zip=True)
    with pytest.raises(FileExistsError, match="Output file already exists"):
        export_dataset(dataset, output_zip, export_media=ExportMode.SKIP, as_zip=True)

    # Zip export without .zip suffix (creates dataset.zip inside dir): second call should fail
    output_dir_zip = tmp_path / "export_zip_dir"
    export_dataset(dataset, output_dir_zip, export_media=ExportMode.SKIP, as_zip=True)
    assert (output_dir_zip / "dataset.zip").exists()
    with pytest.raises(FileExistsError, match="Output file already exists"):
        export_dataset(dataset, output_dir_zip, export_media=ExportMode.SKIP, as_zip=True)

    # Zip export without .zip suffix where output_path is an existing file (not a directory)
    file_path = tmp_path / "existing_file"
    file_path.touch()
    with pytest.raises(FileExistsError, match="Output path already exists as a file"):
        export_dataset(dataset, file_path, export_media=ExportMode.SKIP, as_zip=True)


def test_export_import_preserves_original_filenames(tmp_path):
    """Test that original filenames are preserved through export/import roundtrip.

    When exporting an ImagePathField, the original filename should be kept
    (not replaced with an index-based name). On import, the path should
    resolve to the exported file with the original name.
    """

    class PathSample(Sample):
        image_path: str = image_path_field()
        label: int = label_field()

    # Create source images with distinct, meaningful filenames
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    filenames = ["cat_photo.jpg", "dog_running.png", "bird in flight.jpeg"]
    source_paths = []
    for fname in filenames:
        img_path = source_dir / fname
        img = np.random.randint(0, 255, (20, 30, 3), dtype=np.uint8)
        pil_img = PILImage.fromarray(img)
        fmt = "JPEG" if fname.endswith((".jpg", ".jpeg")) else "PNG"
        pil_img.save(img_path, fmt)
        source_paths.append(str(img_path))

    dataset = Dataset(PathSample, categories={"label": LABEL_CATEGORIES})
    for idx, path in enumerate(source_paths):
        dataset.append(PathSample(image_path=path, label=idx))

    # ---- Export ----
    export_dir = tmp_path / "export"
    export_dataset(dataset, export_dir, export_media=ExportMode.COPY, as_zip=False)

    # Verify that the images directory contains files with the original names
    images_dir = export_dir / IMAGES_DIR
    for fname in filenames:
        assert (images_dir / fname).exists(), f"Expected {fname} in images directory"

    # Verify the parquet stores the original filenames (not index-based names)
    df_exported = pl.read_parquet(export_dir / DATAFRAME_FILE)
    for idx, fname in enumerate(filenames):
        assert df_exported["image_path"][idx] == fname

    # ---- Import ----
    imported_dataset = import_dataset(export_dir, dtype=PathSample)

    assert len(imported_dataset) == len(filenames)
    for idx, fname in enumerate(filenames):
        sample = imported_dataset[idx]
        path = Path(sample.image_path)

        # The path should exist and point to the original-named file
        assert path.exists(), f"Imported path {path} does not exist"
        assert path.name == fname, f"Expected filename {fname}, got {path.name}"

        # The image content should be loadable
        loaded_img = np.array(PILImage.open(path))
        assert loaded_img.shape[0] == 20
        assert loaded_img.shape[1] == 30


def test_export_import_preserves_filenames_with_collisions(tmp_path):
    """Test that filename collisions are handled when multiple source files share the same name."""

    class PathSample(Sample):
        image_path: str = image_path_field()

    # Create two images with the same filename but in different directories
    dir_a = tmp_path / "source_a"
    dir_b = tmp_path / "source_b"
    dir_a.mkdir()
    dir_b.mkdir()

    img_a = np.full((10, 10, 3), 100, dtype=np.uint8)
    img_b = np.full((10, 10, 3), 200, dtype=np.uint8)
    PILImage.fromarray(img_a).save(dir_a / "photo.png")
    PILImage.fromarray(img_b).save(dir_b / "photo.png")

    dataset = Dataset(PathSample)
    dataset.append(PathSample(image_path=str(dir_a / "photo.png")))
    dataset.append(PathSample(image_path=str(dir_b / "photo.png")))

    # ---- Export ----
    export_dir = tmp_path / "export"
    export_dataset(dataset, export_dir, export_media=ExportMode.COPY, as_zip=False)

    images_dir = export_dir / IMAGES_DIR
    # One file keeps the original name, the other gets a numeric suffix
    assert (images_dir / "photo.png").exists()
    assert (images_dir / "photo_1.png").exists()

    # ---- Import ----
    imported_dataset = import_dataset(export_dir, dtype=PathSample)
    assert len(imported_dataset) == 2

    # Both paths should exist and be distinct
    path_0 = Path(imported_dataset[0].image_path)
    path_1 = Path(imported_dataset[1].image_path)
    assert path_0.exists()
    assert path_1.exists()
    assert path_0 != path_1

    # Verify image content is preserved (pixel values distinguish the two)
    loaded_0 = np.array(PILImage.open(path_0))
    loaded_1 = np.array(PILImage.open(path_1))
    assert loaded_0[0, 0, 0] == 100
    assert loaded_1[0, 0, 0] == 200


def test_export_import_preserves_filenames_via_zip(tmp_path):
    """Test that original filenames survive a ZIP export/import roundtrip."""

    class PathSample(Sample):
        image_path: str = image_path_field()
        label: int = label_field()

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    img_path = source_dir / "my_image.png"
    PILImage.fromarray(np.zeros((15, 20, 3), dtype=np.uint8)).save(img_path)

    dataset = Dataset(PathSample, categories={"label": LABEL_CATEGORIES})
    dataset.append(PathSample(image_path=str(img_path), label=0))

    # ---- Export as ZIP ----
    export_zip = tmp_path / "export.zip"
    export_dataset(dataset, export_zip, export_media=ExportMode.COPY, as_zip=True)

    # Verify the ZIP contains the original filename
    with zipfile.ZipFile(export_zip) as zf:
        image_entries = [n for n in zf.namelist() if n.startswith(IMAGES_DIR + "/")]
        assert any("my_image.png" in entry for entry in image_entries)

    # ---- Import from ZIP ----
    imported_dataset = import_dataset(export_zip, dtype=PathSample)
    assert len(imported_dataset) == 1

    sample = imported_dataset[0]
    path = Path(sample.image_path)
    assert path.exists()
    assert path.name == "my_image.png"


# ============================================================
# sanitize_filename unit tests
# ============================================================


class SanitizeFilenameTest:
    """Unit tests for the sanitize_filename function."""

    def test_empty_string(self):
        assert sanitize_filename("") == ""

    def test_normal_filename_unchanged(self):
        assert sanitize_filename("image_001.png") == "image_001.png"

    def test_replaces_colons_cross_platform(self):
        assert sanitize_filename("2024:01:15_photo.jpg") == "2024_01_15_photo.jpg"

    def test_replaces_angle_brackets(self):
        assert sanitize_filename("file<1>.txt") == "file_1_.txt"

    def test_replaces_question_mark(self):
        assert sanitize_filename("what?.png") == "what_.png"

    def test_replaces_asterisk(self):
        assert sanitize_filename("star*.png") == "star_.png"

    def test_replaces_pipe(self):
        assert sanitize_filename("a|b.png") == "a_b.png"

    def test_replaces_double_quote(self):
        assert sanitize_filename('say"hello".png') == "say_hello_.png"

    def test_replaces_backslash(self):
        assert sanitize_filename("path\\file.png") == "path_file.png"

    def test_strips_trailing_dots(self):
        assert sanitize_filename("file...") == "file"

    def test_strips_trailing_spaces(self):
        assert sanitize_filename("file   ") == "file"

    def test_strips_trailing_dots_and_spaces(self):
        assert sanitize_filename("file. . .") == "file"

    def test_reserved_name_con(self):
        assert sanitize_filename("CON") == "_CON"

    def test_reserved_name_con_with_extension(self):
        assert sanitize_filename("CON.txt") == "_CON.txt"

    def test_reserved_name_nul(self):
        assert sanitize_filename("NUL") == "_NUL"

    def test_reserved_name_com1(self):
        assert sanitize_filename("COM1") == "_COM1"

    def test_reserved_name_lpt3(self):
        assert sanitize_filename("LPT3.log") == "_LPT3.log"

    def test_reserved_name_case_insensitive(self):
        assert sanitize_filename("con") == "_con"
        assert sanitize_filename("Aux.txt") == "_Aux.txt"

    def test_not_reserved_name(self):
        # "CONSOLE" is not a reserved name
        assert sanitize_filename("CONSOLE") == "CONSOLE"

    def test_control_characters_replaced(self):
        assert sanitize_filename("file\x01name\x1f.png") == "file_name_.png"

    def test_null_byte_replaced(self):
        assert sanitize_filename("file\x00name.png") == "file_name.png"

    def test_result_not_empty_after_sanitization(self):
        # All characters are replaced but result is not empty
        assert sanitize_filename(":::") == "___"
        # Trailing dots/spaces stripped to empty → falls back to "_"
        assert sanitize_filename("...") == "_"

    def test_cross_platform_false_on_current_os(self):
        """cross_platform=False should at least handle control chars."""
        result = sanitize_filename("file\x00\x01.png", cross_platform=False)
        assert "\x00" not in result
        assert "\x01" not in result

    def test_multiple_illegal_chars(self):
        assert sanitize_filename('a<b>c:d"e|f?g*.png') == "a_b_c_d_e_f_g_.png"

    def test_preserves_unicode(self):
        assert sanitize_filename("日本語ファイル.png") == "日本語ファイル.png"

    def test_preserves_dashes_and_underscores(self):
        assert sanitize_filename("my-file_name.png") == "my-file_name.png"

    def test_preserves_dots_in_middle(self):
        assert sanitize_filename("file.v2.0.png") == "file.v2.0.png"


# ============================================================
# _sanitize_extracted_files tests
# ============================================================


class SanitizeExtractedFilesTest:
    """Tests for _sanitize_extracted_files which renames files after zip extraction."""

    def test_renames_file_with_colon(self, tmp_path):
        """Files with colons should be renamed (important for macOS/Windows)."""
        import platform

        # On macOS/Windows we can't even create files with colons, so skip
        if platform.system() != "Linux":
            pytest.skip("Can only create files with colons on Linux")

        bad_file = tmp_path / "image:01.png"
        bad_file.touch()
        _sanitize_extracted_files(tmp_path)
        assert not bad_file.exists()
        sanitized = tmp_path / "image_01.png"
        assert sanitized.exists()

    def test_no_rename_needed(self, tmp_path):
        """Normal files should not be renamed."""
        good_file = tmp_path / "normal_image.png"
        good_file.touch()
        _sanitize_extracted_files(tmp_path)
        assert good_file.exists()

    def test_handles_collision(self, tmp_path):
        """When sanitized name already exists, a numeric suffix is added."""
        import platform

        if platform.system() != "Linux":
            pytest.skip("Can only create files with colons on Linux")

        # Create the target name first
        (tmp_path / "image_01.png").touch()
        # Create the file that needs sanitizing
        (tmp_path / "image:01.png").touch()

        _sanitize_extracted_files(tmp_path)

        assert (tmp_path / "image_01.png").exists()  # original untouched
        assert (tmp_path / "image_01_1.png").exists()  # collision resolved

    def test_subdirectories_handled(self, tmp_path):
        """Files in subdirectories are also sanitized."""
        import platform

        if platform.system() != "Linux":
            pytest.skip("Can only create files with colons on Linux")

        sub = tmp_path / "images"
        sub.mkdir()
        bad_file = sub / "img:1.png"
        bad_file.touch()

        _sanitize_extracted_files(tmp_path)

        assert not bad_file.exists()
        assert (sub / "img_1.png").exists()

    def test_control_chars_renamed(self, tmp_path):
        """Files with control characters should be renamed."""
        import platform

        # Control characters cannot be created in filenames on Windows
        if platform.system() == "Windows":
            pytest.skip("Cannot create files with control characters on Windows")

        bad_file = tmp_path / "file\x01name.txt"
        bad_file.touch()
        _sanitize_extracted_files(tmp_path)
        assert not bad_file.exists()
        assert (tmp_path / "file_name.txt").exists()

    def test_patches_annotation_files_after_rename(self, tmp_path):
        """Annotation files (JSON, YAML, XML, TXT) should be updated to reference renamed files."""
        import platform

        if platform.system() != "Linux":
            pytest.skip("Can only create files with colons on Linux")

        # Create an image with a colon
        (tmp_path / "photo:1.jpg").touch()

        # Create annotation files referencing the old name
        ann_json = tmp_path / "annotations.json"
        ann_json.write_text('{"images": [{"file_name": "photo:1.jpg"}]}')

        ann_xml = tmp_path / "annotation.xml"
        ann_xml.write_text("<annotation><filename>photo:1.jpg</filename></annotation>")

        ann_yaml = tmp_path / "data.yaml"
        ann_yaml.write_text("train: photo:1.jpg\n")

        ann_txt = tmp_path / "train.txt"
        ann_txt.write_text("photo:1.jpg\n")

        _sanitize_extracted_files(tmp_path)

        # Image should be renamed
        assert not (tmp_path / "photo:1.jpg").exists()
        assert (tmp_path / "photo_1.jpg").exists()

        # All annotation files should reference the new name
        assert "photo_1.jpg" in ann_json.read_text()
        assert "photo:1.jpg" not in ann_json.read_text()

        assert "photo_1.jpg" in ann_xml.read_text()
        assert "photo:1.jpg" not in ann_xml.read_text()

        assert "photo_1.jpg" in ann_yaml.read_text()
        assert "photo:1.jpg" not in ann_yaml.read_text()

        assert "photo_1.jpg" in ann_txt.read_text()
        assert "photo:1.jpg" not in ann_txt.read_text()

    def test_patch_does_not_modify_unrelated_files(self, tmp_path):
        """Annotation files without renamed references should not be modified."""
        ann = tmp_path / "clean.json"
        ann.write_text('{"images": [{"file_name": "normal.jpg"}]}')
        (tmp_path / "normal.jpg").touch()

        _sanitize_extracted_files(tmp_path)

        assert ann.read_text() == '{"images": [{"file_name": "normal.jpg"}]}'

    def test_patches_relative_paths_without_basename_collisions(self, tmp_path):
        """Relative-path references should be patched correctly when basenames collide."""
        import platform

        if platform.system() != "Linux":
            pytest.skip("Can only create files with colons on Linux")

        sub1 = tmp_path / "sub1"
        sub2 = tmp_path / "sub2"
        sub1.mkdir()
        sub2.mkdir()

        (sub1 / "img_1.jpg").touch()
        (sub1 / "img:1.jpg").touch()
        (sub2 / "img:1.jpg").touch()

        ann = tmp_path / "annotations.json"
        ann.write_text('["sub1/img:1.jpg", "sub2/img:1.jpg"]')

        _sanitize_extracted_files(tmp_path)

        text = ann.read_text()
        # sub1/img:1.jpg collides with an existing sub1/img_1.jpg, so a numeric
        # suffix is added during sanitization.
        assert "sub1/img_1_1.jpg" in text
        assert "sub2/img_1.jpg" in text
        assert "sub1/img:1.jpg" not in text
        assert "sub2/img:1.jpg" not in text


# ============================================================
# _patch_annotation_files unit tests
# ============================================================


class PatchAnnotationFilesTest:
    """Tests for _patch_annotation_files in isolation."""

    def test_replaces_in_json(self, tmp_path):
        ann = tmp_path / "ann.json"
        ann.write_text('{"file_name": "old:name.jpg"}')
        _patch_annotation_files(tmp_path, {"old:name.jpg": "old_name.jpg"})
        assert ann.read_text() == '{"file_name": "old_name.jpg"}'

    def test_replaces_in_xml(self, tmp_path):
        ann = tmp_path / "ann.xml"
        ann.write_text("<filename>old:name.jpg</filename>")
        _patch_annotation_files(tmp_path, {"old:name.jpg": "old_name.jpg"})
        assert ann.read_text() == "<filename>old_name.jpg</filename>"

    def test_replaces_in_yaml(self, tmp_path):
        ann = tmp_path / "data.yaml"
        ann.write_text("path: old:name.jpg\n")
        _patch_annotation_files(tmp_path, {"old:name.jpg": "old_name.jpg"})
        assert ann.read_text() == "path: old_name.jpg\n"

    def test_replaces_in_txt(self, tmp_path):
        ann = tmp_path / "train.txt"
        ann.write_text("old:name\n")
        _patch_annotation_files(tmp_path, {"old:name": "old_name"})
        assert ann.read_text() == "old_name\n"

    def test_multiple_replacements(self, tmp_path):
        ann = tmp_path / "ann.json"
        ann.write_text('["a:1.jpg", "b:2.jpg"]')
        _patch_annotation_files(tmp_path, {"a:1.jpg": "a_1.jpg", "b:2.jpg": "b_2.jpg"})
        assert ann.read_text() == '["a_1.jpg", "b_2.jpg"]'

    def test_skips_non_annotation_extensions(self, tmp_path):
        f = tmp_path / "data.parquet"
        f.write_text("old:name.jpg")
        _patch_annotation_files(tmp_path, {"old:name.jpg": "old_name.jpg"})
        assert f.read_text() == "old:name.jpg"

    def test_skips_binary_files(self, tmp_path):
        f = tmp_path / "binary.json"
        f.write_bytes(b"\x80\x81\x82\x83")
        # Should not raise
        _patch_annotation_files(tmp_path, {"old": "new"})

    def test_patches_in_subdirectories(self, tmp_path):
        sub = tmp_path / "annotations"
        sub.mkdir()
        ann = sub / "instances.json"
        ann.write_text('{"file_name": "img:1.jpg"}')
        _patch_annotation_files(tmp_path, {"img:1.jpg": "img_1.jpg"})
        assert ann.read_text() == '{"file_name": "img_1.jpg"}'


def test_export_sanitizes_filenames_cross_platform(tmp_path):
    """Export with COPY mode should sanitize filenames for cross-platform safety."""
    import platform

    if platform.system() != "Linux":
        pytest.skip("Can only create source files with colons on Linux")

    class PathSample(Sample):
        image_path: str = image_path_field()
        label: int = label_field()

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    # Create an image with a colon in the name (valid on Linux, invalid on Windows/macOS)
    img_path = source_dir / "photo:2024:01.png"
    PILImage.fromarray(np.zeros((10, 10, 3), dtype=np.uint8)).save(img_path)

    dataset = Dataset(PathSample, categories={"label": LABEL_CATEGORIES})
    dataset.append(PathSample(image_path=str(img_path), label=0))

    output_dir = tmp_path / "export"
    export_dataset(dataset, output_dir, export_media=ExportMode.COPY)

    # The exported image should have colons replaced
    images_dir = output_dir / IMAGES_DIR
    exported_files = list(images_dir.iterdir())
    assert len(exported_files) == 1
    assert ":" not in exported_files[0].name
    assert exported_files[0].name == "photo_2024_01.png"


def test_export_import_roundtrip_sanitized_filename(tmp_path):
    """Full roundtrip: export a dataset with problematic filename, import it back."""
    import platform

    if platform.system() != "Linux":
        pytest.skip("Can only create source files with colons on Linux")

    class PathSample(Sample):
        image_path: str = image_path_field()
        label: int = label_field()

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    img_path = source_dir / "test:image.png"
    img_array = np.random.randint(0, 255, (10, 15, 3), dtype=np.uint8)
    PILImage.fromarray(img_array).save(img_path)

    dataset = Dataset(PathSample, categories={"label": LABEL_CATEGORIES})
    dataset.append(PathSample(image_path=str(img_path), label=2))

    output_dir = tmp_path / "export"
    export_dataset(dataset, output_dir, export_media=ExportMode.COPY)

    imported = import_dataset(output_dir, dtype=PathSample)
    assert len(imported) == 1
    sample = imported[0]
    assert Path(sample.image_path).exists()
    assert sample.label == 2

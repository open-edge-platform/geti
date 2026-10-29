import os
import tempfile
import zipfile
from enum import Enum

import pytest

from getidata.data_formats.base import DataFormat
from getidata.data_formats.coco.sample import CocoSample
from getidata.export_import import export_dataset, import_dataset


class FakeFormat(Enum):
    OTHER = "OTHER"


class DummyDataset:
    def __init__(self):
        self.converted_schema = None

    def convert_to_schema(self, schema, **kwargs):
        self.converted_schema = schema
        return self


def test_import_dataset_delegates_to_coco(monkeypatch):
    captured = {}

    def fake_loader(images_dir_path, annotations_path):
        captured["images_dir_path"] = images_dir_path
        captured["annotations_path"] = annotations_path
        return "dataset"

    monkeypatch.setattr("getidata.data_formats.coco.io.load_coco_dataset", fake_loader)

    result = import_dataset(
        "",
        data_format=DataFormat.COCO,
        images_dir_path="/tmp/images",
        annotations_path="/tmp/annotations.json",
    )

    assert result == "dataset"
    assert captured["images_dir_path"] == "/tmp/images"
    assert captured["annotations_path"] == "/tmp/annotations.json"


def test_import_dataset_requires_paths_for_coco():
    with pytest.raises(ValueError, match="images_dir_path and annotations_path are required"):
        import_dataset("", data_format=DataFormat.COCO)


def test_import_dataset_unsupported_format_raises():
    with pytest.raises(ValueError, match="Unsupported data format"):
        import_dataset(
            "",
            data_format=FakeFormat.OTHER,
            images_dir_path="/tmp/images",
            annotations_path="/tmp/annotations.json",
        )


def test_export_dataset_delegates_to_coco_with_converted_schema(monkeypatch):
    dummy_dataset = DummyDataset()
    captured = {}

    def fake_saver(dataset, images_dir_path, annotations_path):
        captured["dataset"] = dataset
        captured["images_dir_path"] = images_dir_path
        captured["annotations_path"] = annotations_path

    monkeypatch.setattr("getidata.data_formats.coco.io.save_coco_dataset", fake_saver)

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = os.path.join(tmp_dir, "output")
        export_dataset(
            dummy_dataset,
            output_dir,
            data_format=DataFormat.COCO,
        )

        assert captured["dataset"] is dummy_dataset
        assert captured["images_dir_path"] == os.path.join(output_dir, "images")
        assert captured["annotations_path"] == os.path.join(output_dir, "annotations.json")
        assert dummy_dataset.converted_schema == CocoSample.infer_schema()


def test_export_dataset_unsupported_format_raises():
    with pytest.raises(ValueError, match="Unsupported data format"):
        export_dataset(
            DummyDataset(),
            "/tmp/output",
            data_format=FakeFormat.OTHER,
        )


# Tests for the as_zip functionality in export_dataset


def test_export_as_zip_creates_archive_with_correct_files(monkeypatch):
    """Test that as_zip=True creates a zip archive containing the expected files."""
    dummy_dataset = DummyDataset()

    def fake_saver(dataset, images_dir_path, annotations_path):
        os.makedirs(images_dir_path, exist_ok=True)
        with open(os.path.join(images_dir_path, "test_image.jpg"), "w") as f:
            f.write("fake image data")
        with open(annotations_path, "w") as f:
            f.write('{"images": [], "annotations": []}')

    monkeypatch.setattr("getidata.data_formats.coco.io.save_coco_dataset", fake_saver)

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, "my_dataset.zip")

        export_dataset(
            dummy_dataset,
            zip_path,
            data_format=DataFormat.COCO,
            as_zip=True,
        )

        assert os.path.exists(zip_path)
        assert zipfile.is_zipfile(zip_path)

        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            assert "annotations.json" in names
            assert "images/test_image.jpg" in names


def test_export_as_zip_adds_extension_if_missing(monkeypatch):
    """Test that .zip extension is added if not present in output_path."""
    dummy_dataset = DummyDataset()

    def fake_saver(dataset, images_dir_path, annotations_path):
        os.makedirs(images_dir_path, exist_ok=True)
        with open(annotations_path, "w") as f:
            f.write("{}")

    monkeypatch.setattr("getidata.data_formats.coco.io.save_coco_dataset", fake_saver)

    with tempfile.TemporaryDirectory() as tmp_dir:
        # No .zip extension
        output_path = os.path.join(tmp_dir, "my_dataset")

        export_dataset(
            dummy_dataset,
            output_path,
            data_format=DataFormat.COCO,
            as_zip=True,
        )

        # Should have added .zip
        zip_path = os.path.join(tmp_dir, "my_dataset.zip")
        assert os.path.exists(zip_path)


def test_export_as_zip_unsupported_format_raises():
    """Test that unsupported format raises ValueError when as_zip=True."""
    with pytest.raises(ValueError, match="Unsupported data format"):
        export_dataset(
            DummyDataset(),
            "/tmp/test.zip",
            data_format=FakeFormat.OTHER,
            as_zip=True,
        )


def test_export_as_zip_cleans_up_on_error(monkeypatch):
    """Test that temp directory is cleaned up even if an error occurs."""
    dummy_dataset = DummyDataset()
    created_temp_dirs: list[str] = []

    original_td = tempfile.TemporaryDirectory

    class TrackingTempDir(original_td):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            created_temp_dirs.append(self.name)

    import getidata.export_import as ei_module

    monkeypatch.setattr(ei_module.tempfile, "TemporaryDirectory", TrackingTempDir)

    def failing_saver(dataset, images_dir_path, annotations_path):
        raise RuntimeError("Simulated save failure")

    monkeypatch.setattr("getidata.data_formats.coco.io.save_coco_dataset", failing_saver)

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, "test.zip")

        with pytest.raises(RuntimeError, match="Simulated save failure"):
            export_dataset(
                dummy_dataset,
                zip_path,
                data_format=DataFormat.COCO,
                as_zip=True,
            )

        # Verify temp directory was still cleaned up
        assert len(created_temp_dirs) > 0
        assert not os.path.exists(created_temp_dirs[-1])


# Tests for FileExistsError protection


def test_export_to_existing_directory_raises(monkeypatch):
    """Test that exporting to an existing directory raises FileExistsError."""
    dummy_dataset = DummyDataset()

    def fake_saver(dataset, images_dir_path, annotations_path):
        pass  # Should never be called

    monkeypatch.setattr("getidata.data_formats.coco.io.save_coco_dataset", fake_saver)

    # tmp_dir already exists, so export should fail
    with tempfile.TemporaryDirectory() as tmp_dir, pytest.raises(FileExistsError, match="already exists"):
        export_dataset(
            dummy_dataset,
            tmp_dir,
            data_format=DataFormat.COCO,
        )


def test_export_as_zip_to_existing_archive_raises(monkeypatch):
    """Test that exporting to an existing ZIP archive raises FileExistsError."""
    dummy_dataset = DummyDataset()

    def fake_saver(dataset, images_dir_path, annotations_path):
        pass

    monkeypatch.setattr("getidata.data_formats.coco.io.save_coco_dataset", fake_saver)

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, "existing.zip")
        # Create an existing zip file
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("dummy.txt", "existing data")

        with pytest.raises(FileExistsError, match="already exists"):
            export_dataset(
                dummy_dataset,
                zip_path,
                data_format=DataFormat.COCO,
                as_zip=True,
            )


# Tests for input_path as default root_dir


def test_import_dataset_uses_input_path_as_default_root_dir(monkeypatch):
    """Test that input_path is used as default root_dir when data_format is set."""
    captured = {}

    def fake_loader(root_dir, format):
        captured["root_dir"] = root_dir
        return "dataset"

    monkeypatch.setattr("getidata.data_formats.yolo.io.load_yolo_dataset", fake_loader)

    input_path = os.path.join("/some", "yolo", "path")
    result = import_dataset(
        input_path,
        data_format=DataFormat.YOLO,
    )

    assert result == "dataset"
    assert os.path.normpath(captured["root_dir"]) == os.path.normpath(input_path)


def test_import_dataset_explicit_root_dir_overrides_input_path(monkeypatch):
    """Test that explicit root_dir overrides input_path."""
    captured = {}

    def fake_loader(root_dir, format):
        captured["root_dir"] = root_dir
        return "dataset"

    monkeypatch.setattr("getidata.data_formats.yolo.io.load_yolo_dataset", fake_loader)

    result = import_dataset(
        "/some/input/path",
        data_format=DataFormat.YOLO,
        root_dir="/explicit/root",
    )

    assert result == "dataset"
    assert captured["root_dir"] == "/explicit/root"

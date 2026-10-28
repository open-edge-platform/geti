"""Unit tests for pickle serialization of Dataset, Transform and mask loader classes."""

import pickle
from typing import Annotated, Callable

import numpy as np
import polars as pl

from getidata.dataset import Dataset, Sample
from getidata.fields.images import image_callable_field


# Module-level sample class for pickle tests (local classes can't be pickled)
class PicklableSample(Sample):
    """Sample class defined at module level for pickle testing."""

    image: Annotated[Callable, image_callable_field()]


# Module-level callable for pickle tests (local functions can't be pickled by default pickle)
def module_level_image_loader():
    """A module-level callable that can be pickled."""
    return np.zeros((10, 10, 3), dtype=np.uint8)


class DatasetPickleSerializationTest:
    """Tests for Dataset pickle serialization with Object columns."""

    def test_dataset_with_object_columns_is_picklable(self):
        """Test that a Dataset with Object columns can be pickled and unpickled."""
        # Use module-level sample class (local classes can't be pickled)
        ds = Dataset(PicklableSample)

        # Add a sample with a module-level callable (local functions can't be pickled)
        sample = PicklableSample(image=module_level_image_loader)
        ds.append(sample)

        # Verify the dataset has Object columns
        assert pl.Object in ds.df.schema.values()

        # Pickle and unpickle
        pickled = pickle.dumps(ds)
        restored_ds = pickle.loads(pickled)

        # Verify the restored dataset works
        assert len(restored_ds) == 1
        # Verify the callable was restored and works
        restored_sample = restored_ds[0]
        result = restored_sample.image()
        assert result.shape == (10, 10, 3)

    def test_empty_dataset_with_object_schema_is_picklable(self):
        """Test that an empty Dataset with Object column schema can be pickled."""
        # Use module-level sample class
        ds = Dataset(PicklableSample)

        # Pickle and unpickle empty dataset
        pickled = pickle.dumps(ds)
        restored_ds = pickle.loads(pickled)

        assert len(restored_ds) == 0


class TransformPickleSerializationTest:
    """Tests for Transform pickle serialization with Object columns."""

    def test_identity_transform_with_object_columns_is_picklable(self):
        """Test that IdentityTransform with Object columns can be pickled."""
        from getidata.fields.images import ImageCallableField
        from getidata.schema import AttributeInfo, Schema
        from getidata.transform import IdentityTransform

        # Create a DataFrame with Object column using module-level callable
        df = pl.DataFrame({"data": pl.Series([module_level_image_loader], dtype=pl.Object())})

        # Create schema
        schema = Schema(attributes={"data": AttributeInfo(type=callable, field=ImageCallableField())})

        transform = IdentityTransform(df, schema)

        # Pickle and unpickle
        pickled = pickle.dumps(transform)
        restored_transform = pickle.loads(pickled)

        # Verify the restored transform works
        assert len(restored_transform) == 1
        result_df = restored_transform.apply(["data"])
        assert "data" in result_df.columns


class LazyLoaderPicklabilityRegressionTest:
    """Regression tests for the picklable dataclass loaders introduced to make
    lazy media/mask loaders survive ``torch.utils.data.DataLoader`` ``spawn``
    pickling.

    These guard against two regressions:
    - reverting to non-picklable closures (only module-level callables survive
      ``spawn`` pickling), and
    - the ``InvalidOperation: nested objects are not allowed`` Polars error that
      occurs when such loaders (which expose named attributes) are stored in a
      callable column without an explicit ``pl.Object()`` dtype.
    """

    def test_image_file_loader_is_picklable(self, tmp_path):
        """``_ImageFileLoader`` used during export/import must round-trip."""
        from PIL import Image

        from getidata.export_import import _ImageFileLoader

        img_path = tmp_path / "img.png"
        Image.fromarray(np.zeros((4, 4, 3), dtype=np.uint8)).save(img_path)

        loader = _ImageFileLoader(img_path)
        assert loader().shape == (4, 4, 3)

        restored = pickle.loads(pickle.dumps(loader))
        assert restored().shape == (4, 4, 3)

    def test_image_path_loader_is_picklable(self, tmp_path):
        """``_ImagePathLoader`` used by ImagePathToImageCallableConverter must round-trip."""
        from PIL import Image

        from getidata.converters.image_converters import _ImagePathLoader

        img_path = tmp_path / "img.png"
        Image.fromarray(np.zeros((4, 4, 3), dtype=np.uint8)).save(img_path)

        loader = _ImagePathLoader(str(img_path), "RGB")
        assert loader().shape == (4, 4, 3)

        restored = pickle.loads(pickle.dumps(loader))
        assert restored().shape == (4, 4, 3)

    def test_voc_mask_loader_is_picklable(self, tmp_path):
        """``_VocMaskLoader`` used for VOC segmentation masks must round-trip."""
        from PIL import Image

        from getidata.data_formats.voc.helpers import _VocMaskLoader

        mask_path = tmp_path / "mask.png"
        Image.fromarray(np.zeros((4, 4), dtype=np.uint8), mode="L").save(mask_path)

        loader = _VocMaskLoader(mask_path, None)
        assert loader().shape == (4, 4)

        restored = pickle.loads(pickle.dumps(loader))
        assert restored().shape == (4, 4)

    def test_dataset_with_loader_callable_column_is_picklable(self, tmp_path):
        """A Dataset storing dataclass loaders in a callable column must pickle."""
        from PIL import Image

        from getidata.converters.image_converters import _ImagePathLoader

        ds = Dataset(PicklableSample)

        img_path = tmp_path / "img.png"
        Image.fromarray(np.zeros((4, 4, 3), dtype=np.uint8)).save(img_path)
        loader = _ImagePathLoader(str(img_path), "RGB")

        ds.append(PicklableSample(image=loader))
        assert pl.Object in ds.df.schema.values()

        restored = pickle.loads(pickle.dumps(ds))
        assert len(restored) == 1
        assert restored[0].image().shape == (4, 4, 3)

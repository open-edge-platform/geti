import numpy as np

from getidata.data_formats.coco.sample import CocoCategories, CocoSample
from getidata.fields import ImageInfo, Subset


def make_sample(polygons=None):
    return CocoSample(
        image="",
        image_info=ImageInfo(height=0, width=0),
        polygons=polygons,
        subset=Subset.TRAINING,
        image_id=1,
    )


def _poly(points):
    return np.array(points, dtype=np.float32)


def test_coco_categories_lists_super_categories():
    cats = CocoCategories()
    assert len(cats) == 80
    assert cats.label_to_super["person"] == "person"
    assert "cat" in cats.get_labels_by_super_category("animal")

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import copy

import pytest
from geti_types import ID
from iai_core_py.entities.annotation import Annotation
from iai_core_py.entities.dataset_item import DatasetItem
from iai_core_py.entities.shapes import Rectangle

from jobs_common.utils.annotation_filter import AnnotationFilter


@pytest.mark.JobsComponent
class TestMapItemsToShardsCommand:
    def test_filter_annotation_size(self, fxt_dataset_with_images) -> None:
        """Verifies that a too small annotation is filtered out of the dataset item"""

        new_dataset = AnnotationFilter.apply_annotation_filters(
            dataset=fxt_dataset_with_images, min_annotation_size=1000000
        )
        assert len(new_dataset) == 0

    def test_filter_max_annotations(self, fxt_dataset_with_images, fxt_image):
        """Tests that the max annotation filter functions correctly"""

        # Add one annotation that doesn't match the filter
        additional_annotation = Annotation(shape=Rectangle.generate_full_box(), labels=[])
        annotation_scene = copy.deepcopy(fxt_dataset_with_images[0].annotation_scene)
        annotation_scene.append_annotation(additional_annotation)
        dataset_item = DatasetItem(id_=ID(), media=fxt_image, annotation_scene=annotation_scene)
        fxt_dataset_with_images.append(dataset_item)
        copy_of_fxt_dataset = copy.deepcopy(fxt_dataset_with_images)
        new_dataset = AnnotationFilter.apply_annotation_filters(
            dataset=copy_of_fxt_dataset, max_number_of_annotations=1
        )

        assert len(new_dataset) == (len(fxt_dataset_with_images) - 1)

# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is
# governed by the express license under which they were provided to you ("License"). Unless the
# License provides otherwise, you may not use, modify, copy, publish, distribute, disclose or transmit
# this software or the related documents without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.
import copy

import pytest
from geti_types import ID
from sc_sdk.entities.annotation import Annotation
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.shapes import Rectangle

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

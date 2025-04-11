# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.


import datumaro as dm
import pytest
from geti_types import DatasetStorageIdentifier
from sc_sdk.entities.datasets import Dataset
from sc_sdk.entities.label_schema import LabelSchema

from jobs_common_extras.datumaro_conversion.sc_extractor import ScExtractor


@pytest.mark.CommonComponent
class TestScExtractor:
    def test_sc_extractor(self, fxt_dataset_and_label_schema: tuple[DatasetStorageIdentifier, Dataset, LabelSchema]):
        dataset_storage_identifier, sc_dataset, label_schema = fxt_dataset_and_label_schema
        dm_dataset = ScExtractor(dataset_storage_identifier, sc_dataset, label_schema)

        assert len(dm_dataset) == len(sc_dataset)

        len_dm_anns = sum(len(item.annotations) for item in dm_dataset)
        len_sc_anns = sum(len(item.get_annotations(include_empty=True)) for item in sc_dataset)
        assert len_dm_anns == len_sc_anns

        dm_label_names = {label_category.name for label_category in dm_dataset.categories()[dm.AnnotationType.label]}
        sc_label_names = {label_entity.name for label_entity in label_schema.get_labels(False)}
        assert dm_label_names == sc_label_names

# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

import pytest

from jobs_common.k8s_helpers.k8s_resources_calculation import EphemeralStorageResources


@pytest.mark.JobsComponent
class TestEphemeralStorageResources:
    def test_create_from_compiled_dataset_shards(self, fxt_compiled_dataset_shards):
        if not fxt_compiled_dataset_shards.is_null():
            ephemeral_storage_resources = EphemeralStorageResources.create_from_compiled_dataset_shards(
                fxt_compiled_dataset_shards
            )
            assert isinstance(ephemeral_storage_resources, EphemeralStorageResources)
        else:
            with pytest.raises(ValueError) as ctx:
                ephemeral_storage_resources = EphemeralStorageResources.create_from_compiled_dataset_shards(
                    fxt_compiled_dataset_shards
                )
                ctx.match("Cannot create from NullCompiledDatasetShards.")

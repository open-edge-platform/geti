# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

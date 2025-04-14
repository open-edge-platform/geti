#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for CompiledDatasetShards entities"""

from sc_sdk.entities.compiled_dataset_shards import CompiledDatasetShard, CompiledDatasetShards
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo


class CompiledDatasetShardToMongo(
    IMapperSimple[CompiledDatasetShard, dict],
):
    """MongoDB mapper for `CompiledDatasetShard` entities"""

    @staticmethod
    def forward(instance: CompiledDatasetShard) -> dict:
        return {
            "filename": instance.filename,
            "binary_filename": instance.binary_filename,
            "size": instance.size,
            "checksum": instance.checksum,
        }

    @staticmethod
    def backward(instance: dict) -> CompiledDatasetShard:
        return CompiledDatasetShard(
            filename=instance["filename"],
            binary_filename=instance["binary_filename"],
            size=instance["size"],
            checksum=instance["checksum"],
        )


class CompiledDatasetShardsToMongo(
    IMapperSimple[CompiledDatasetShards, dict],
):
    """MongoDB mapper for `CompiledDatasetShards` entities"""

    @staticmethod
    def forward(instance: CompiledDatasetShards) -> dict:
        return {
            "_id": IDToMongo.forward(instance.id_),
            "label_schema_id": IDToMongo.forward(instance.label_schema_id),
            "compiled_shard_files": [
                CompiledDatasetShardToMongo.forward(compiled_shard_file)
                for compiled_shard_file in instance.compiled_shard_files
            ],
            "creator_name": instance.creator_name,
        }

    @staticmethod
    def backward(instance: dict) -> CompiledDatasetShards:
        return CompiledDatasetShards(
            dataset_id=IDToMongo.backward(instance["_id"]),
            label_schema_id=IDToMongo.backward(instance["label_schema_id"]),
            compiled_shard_files=[
                CompiledDatasetShardToMongo.backward(item) for item in instance["compiled_shard_files"]
            ],
            creator_name=instance["creator_name"],
            ephemeral=False,
        )

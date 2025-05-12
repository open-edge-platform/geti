#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for MetadataItem entities"""

from enum import Enum
from typing import TYPE_CHECKING, cast

from iai_core.adapters.adapter import ProxyAdapter
from iai_core.entities.metadata import FloatMetadata, FloatType, IMetadata, MetadataItem
from iai_core.entities.model import NullModel
from iai_core.entities.model_storage import ModelStorageIdentifier
from iai_core.entities.tensor import Tensor
from iai_core.repos.mappers.mongodb_mapper_interface import IMapperForward, IMapperParametricBackward, IMapperSimple

from .id_mapper import IDToMongo
from .media_mapper import MediaIdentifierToMongo
from geti_types import DatasetStorageIdentifier

if TYPE_CHECKING:
    from iai_core.repos.storage.binary_repos import TensorBinaryRepo


class MetadataDocSchema(Enum):
    """Metadata schemas supported by the metadata repo"""

    FLOAT = "float"
    TENSOR = "tensor"


class FloatMetadataToMongo(IMapperSimple[FloatMetadata, dict]):
    """MongoDB mapper for `FloatMetadata` entities"""

    @staticmethod
    def forward(instance: FloatMetadata) -> dict:
        return {
            "type": str(instance.float_type),
            "name": instance.name,
            "value": float(instance.value),
        }

    @staticmethod
    def backward(instance: dict) -> FloatMetadata:
        float_type_str = instance.get("type")
        float_type = FloatType[float_type_str]  # type: ignore
        return FloatMetadata(name=instance["name"], value=float(instance["value"]), float_type=float_type)


class TensorMapperBackwardParameters:
    """Parameters for the TensorToMongo backward mapper"""

    def __init__(self, tensor_binary_repo: "TensorBinaryRepo") -> None:
        self.tensor_binary_repo = tensor_binary_repo


class TensorToMongo(
    IMapperForward[Tensor, dict],
    IMapperParametricBackward[Tensor, dict, TensorMapperBackwardParameters],
):
    """MongoDB mapper for `Tensor` entities"""

    @staticmethod
    def forward(instance: Tensor) -> dict:
        if instance.data_binary_filename == "":
            raise ValueError("Cannot map Tensor before its binary data is saved")
        return {
            "name": instance.name,
            "binary_filename": instance.data_binary_filename,
            "shape": instance.shape,
        }

    @staticmethod
    def backward(instance: dict, parameters: TensorMapperBackwardParameters) -> Tensor:
        from iai_core.adapters.tensor_adapter import TensorAdapter

        tensor_adapter = TensorAdapter(
            data_source=parameters.tensor_binary_repo,
            binary_filename=instance["binary_filename"],
            shape=tuple(instance["shape"]),
        )

        return Tensor(
            name=instance["name"],
            tensor_adapter=tensor_adapter,
        )


class MetadataItemMapperBackwardParameters:
    """Parameters for the MetadataItemToMongo backward mapper"""

    def __init__(
        self,
        tensor_binary_repo: "TensorBinaryRepo",
        dataset_storage_identifier: DatasetStorageIdentifier,
    ) -> None:
        self.tensor_binary_repo = tensor_binary_repo
        self.dataset_storage_identifier = dataset_storage_identifier


class MetadataItemToMongo(
    IMapperForward[MetadataItem, dict],
    IMapperParametricBackward[MetadataItem, dict, MetadataItemMapperBackwardParameters],
):
    @staticmethod
    def forward(instance: MetadataItem) -> dict:
        content: dict
        content_schema: str
        match instance.data:
            case FloatMetadata():
                content_schema = MetadataDocSchema.FLOAT.name
                content = FloatMetadataToMongo.forward(cast("FloatMetadata", instance.data))
            case Tensor():
                content_schema = MetadataDocSchema.TENSOR.name
                content = TensorToMongo.forward(cast("Tensor", instance.data))
            case _:
                raise TypeError(f"Unknown instance type `{type(instance)}`")

        doc = {
            "_id": IDToMongo.forward(instance.id_),
            "dataset_item_id": IDToMongo.forward(instance.dataset_item_id),
            "media_identifier": MediaIdentifierToMongo.forward(instance.media_identifier),
            "content": {
                "schema": content_schema.lower(),
                **content,
            },
        }

        if instance.model is not None and not isinstance(instance.model, NullModel):
            doc["model_storage_id"] = IDToMongo.forward(instance.model.model_storage.id_)
            doc["model_id"] = IDToMongo.forward(instance.model.id_)
        return doc

    @staticmethod
    def backward(instance: dict, parameters: MetadataItemMapperBackwardParameters) -> MetadataItem:
        from iai_core.repos import ModelRepo

        content: IMetadata
        content_dict = instance["content"]
        content_schema = content_dict["schema"]
        match content_schema.lower():
            case MetadataDocSchema.FLOAT.value:
                content = FloatMetadataToMongo.backward(content_dict)
            case MetadataDocSchema.TENSOR.value:
                content = TensorToMongo.backward(
                    content_dict,
                    parameters=TensorMapperBackwardParameters(tensor_binary_repo=parameters.tensor_binary_repo),
                )
            case _:
                raise ValueError(f"Cannot decode metadata of type `{content_schema}`")

        model_storage_id = instance.get("model_storage_id")
        if model_storage_id is None:
            return MetadataItem(
                id=IDToMongo.backward(instance["_id"]),
                data=content,
                dataset_item_id=IDToMongo.backward(instance["dataset_item_id"]),
                media_identifier=MediaIdentifierToMongo.backward(instance["media_identifier"]),
                ephemeral=False,
            )

        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=parameters.dataset_storage_identifier.workspace_id,
            project_id=parameters.dataset_storage_identifier.project_id,
            model_storage_id=model_storage_id,
        )
        model_id = IDToMongo.backward(instance["model_id"])
        model_adapter = ProxyAdapter(
            id=model_id,
            proxy=lambda: ModelRepo(model_storage_identifier).get_by_id(model_id),
        )

        return MetadataItem.with_adapters(
            id=IDToMongo.backward(instance["_id"]),
            data=content,
            dataset_item_id=IDToMongo.backward(instance["dataset_item_id"]),
            media_identifier=MediaIdentifierToMongo.backward(instance["media_identifier"]),
            model_adapter=model_adapter,
            ephemeral=False,
        )

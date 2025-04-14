# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import numpy as np
import pytest

from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.metadata import FloatMetadata, IMetadata, MetadataItem
from sc_sdk.entities.model import NullModel
from sc_sdk.entities.tensor import Tensor
from sc_sdk.repos import MetadataRepo

from geti_types import ID, MediaIdentifierEntity


@pytest.fixture
def fxt_metadata_item_factory(request, fxt_annotation_scene):
    def _factory(
        dataset_storage: DatasetStorage,
        media_identifier: MediaIdentifierEntity,
        metadata_type: str = "float_metadata",
        dataset_item_id: ID = MetadataRepo.generate_id(),
        name: str | None = None,
        save: bool = True,
    ):
        metadata: IMetadata
        if metadata_type == "float_metadata":
            metadata = FloatMetadata(name="aaa", value=3.0)
        elif metadata_type == "tensor":
            metadata = Tensor(name=name if name else "test tensor", numpy=np.ones((2, 2)))
        else:
            raise ValueError(f"Metadata type {metadata_type} unknown.")
        metadata_item = MetadataItem(
            data=metadata,
            dataset_item_id=dataset_item_id,
            media_identifier=media_identifier,
            model=NullModel(),
            id=MetadataRepo.generate_id(),
        )
        if save:
            metadata_repo = MetadataRepo(dataset_storage.identifier)
            metadata_repo.save(metadata_item)
            request.addfinalizer(lambda: metadata_repo.delete_by_id(metadata_item.id_))
        return metadata_item

    yield _factory

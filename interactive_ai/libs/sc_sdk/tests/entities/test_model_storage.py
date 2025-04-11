"""This module tests the ModelStorage class"""

# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

import pytest

from sc_sdk.entities.model_storage import ModelStorage, NullModelStorage
from sc_sdk.entities.model_template import NullModelTemplate
from sc_sdk.repos import ModelStorageRepo

from geti_types import ID


@pytest.mark.ScSdkComponent
class TestModelStorage:
    def test_model_storage_equality(self, fxt_mongo_id) -> None:
        """
        <b>Description:</b>
        Check that ModelStorage equality works correctly

        <b>Input data:</b>
        ModelStorage instances

        <b>Expected results:</b>
        == and != operations work correctly for various inputs

        <b>Steps</b>
        1. Test ModelStorage equality
        2. Test NullModelStorage equality
        """
        fxt_mongo_id(0)
        project_id = fxt_mongo_id(1)
        model_template = NullModelTemplate()
        task_node_id = ID()

        model_storage = ModelStorage(
            id_=ModelStorageRepo.generate_id(),
            project_id=project_id,
            task_node_id=task_node_id,
            model_template=model_template,
        )

        new_model_storage = ModelStorage(
            id_=ID("new"), project_id=project_id, task_node_id=task_node_id, model_template=model_template
        )
        assert model_storage != new_model_storage

        identical_model_storage = ModelStorage(
            id_=ID("new"),
            project_id=project_id,
            task_node_id=task_node_id,
            model_template=model_template,
            creation_date=new_model_storage.creation_date,
        )
        assert new_model_storage == identical_model_storage

        assert NullModelStorage() == NullModelStorage()
        assert model_storage != NullModelStorage()
        assert NullModelStorage() != model_storage

# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

from entities.deployment import ModelIdentifier
from repos.model_identifier_mapper import ModelIdentifierToMongo


class TestModelIdentifierMapper:
    def test_code_deployment_model_identifier_mapper(self, fxt_mongo_id, fxt_model) -> None:
        """
        Tests the forward and backward mongo mapper in the model identifier mapper
        """
        model_identifier = ModelIdentifier(model_storage_id=fxt_model.model_storage.id_, model_id=fxt_model.id_)

        model_identifier_forward_dict = ModelIdentifierToMongo().forward(instance=model_identifier)

        model_identifier_backward = ModelIdentifierToMongo().backward(instance=model_identifier_forward_dict)

        assert model_identifier.model_id == model_identifier_backward.model_id
        assert model_identifier.model_storage_id == model_identifier_backward.model_storage_id

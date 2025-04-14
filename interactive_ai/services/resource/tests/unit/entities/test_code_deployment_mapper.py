# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from entities.deployment import CodeDeployment, ModelIdentifier
from repos.code_deployment_mapper import CodeDeploymentToMongo
from tests.utils.test_helpers import verify_mongo_mapper


class TestCodeDeploymentMapper:
    def test_code_deployment_mongo_mapper(self, fxt_mongo_id, fxt_model) -> None:
        """
        Tests forward and backward functions in the code deployment mongo mapper
        """
        model_identifier = ModelIdentifier(model_storage_id=fxt_model.model_storage.id_, model_id=fxt_model.id_)
        code_deployment = CodeDeployment(
            id_=fxt_mongo_id(5),
            creator_id=fxt_mongo_id(6),
            model_identifiers=[model_identifier],
            message="test message",
        )

        verify_mongo_mapper(entity_to_map=code_deployment, mapper_class=CodeDeploymentToMongo)

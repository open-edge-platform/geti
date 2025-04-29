# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from entities.deployment import CodeDeployment, DeploymentState, ModelIdentifier, NullCodeDeployment
from repos.code_deployment_repo import CodeDeploymentRepo

from geti_types import ProjectIdentifier


class TestCodeDeploymentRepo:
    def test_code_deployment_repo_save_get_by_id_and_delete_by_id(
        self, fxt_project, fxt_mongo_id, fxt_model, fxt_dataset_storage
    ) -> None:
        """
        Tests saving, get_by_id and delete_by_id functions in the code deployment repo.
        """
        code_deployment_repo = CodeDeploymentRepo(
            project_identifier=ProjectIdentifier(
                workspace_id=fxt_project.workspace_id,
                project_id=fxt_project.id_,
            ),
        )
        model_identifier = ModelIdentifier(model_storage_id=fxt_model.model_storage.id_, model_id=fxt_model.id_)

        code_deployment = CodeDeployment(
            id_=fxt_mongo_id(5),
            creator_id=fxt_mongo_id(6),
            model_identifiers=[model_identifier],
        )

        code_deployment.state = DeploymentState.DONE

        # Save code deployment
        code_deployment_repo.save(code_deployment)

        # Get code deployment from repo
        retrieved_code_deployment_entity = code_deployment_repo.get_by_id(code_deployment.id_)

        # Check if the entity retrieved is equal to the initial code deployment entity
        assert code_deployment == retrieved_code_deployment_entity

        # Delete retrieved entity by id
        code_deployment_repo.delete_by_id(retrieved_code_deployment_entity.id_)

        null_code_deployment = code_deployment_repo.get_by_id(code_deployment.id_)

        # Check if the entity is deleted
        assert isinstance(null_code_deployment, NullCodeDeployment)

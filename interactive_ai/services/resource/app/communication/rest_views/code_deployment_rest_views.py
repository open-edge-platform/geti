# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from entities.deployment import CodeDeployment


class CodeDeploymentRestViews:
    @staticmethod
    def to_rest(code_deployment: CodeDeployment) -> dict:
        return {
            "id": str(code_deployment.id_),
            "models": [
                {
                    "model_id": model_identifier.model_id,
                    "model_group_id": model_identifier.model_storage_id,
                }
                for model_identifier in code_deployment.model_identifiers
            ],
            "progress": code_deployment.progress,
            "state": code_deployment.state.name,
            "message": code_deployment.message,
            "creator_id": code_deployment.creator_id,
            "creation_time": code_deployment.creation_time.isoformat(),
        }

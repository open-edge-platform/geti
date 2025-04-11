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

# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.


from service.custom_resource import CustomResource


class InferenceService(CustomResource):
    """Helm chart repository resource class."""

    api_group_name = "serving.kserve.io"
    crd_plural_name = "inferenceservices"
    crd_version = "v1beta1"

    def __init__(
        self,
        name: str,
        namespace: str,
        body: dict | None = None,
        *,
        storage_name: str | None = None,
        path: str | None = None,
    ) -> None:
        if not body:
            body = {
                "metadata": {
                    "name": name,
                    "namespace": namespace,
                    "annotations": {
                        "serving.kserve.io/deploymentMode": "ModelMesh",
                    },
                },
                "apiVersion": f"{self.__class__.api_group_name}/{self.__class__.crd_version}",
                "kind": self.__class__.__name__,
                "spec": {
                    "predictor": {
                        "model": {
                            "modelFormat": {
                                "name": "mediapipe_graph",
                                "version": "1",
                            },
                            "storage": {
                                "key": storage_name,
                                "path": path,
                            },
                        },
                    },
                },
            }
        super().__init__(name=name, namespace=namespace, body=body)

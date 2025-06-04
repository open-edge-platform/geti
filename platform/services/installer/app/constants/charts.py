# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.
"""
Module with definition of all charts used to deploy Geti
"""

from dataclasses import dataclass

from platform_configuration.features import FeatureFlag, is_feature_flag_enabled

ambient_mesh: bool = is_feature_flag_enabled(FeatureFlag.AMBIENT_MESH)


@dataclass
class ChartDefinition:
    name: str
    directory: str
    namespace: str
    values_file: str = ""
    values_template_file: str = ""


# TODO remove unnecessary charts (probably all except for GetiController)

GETI_CONTROLLER_CHART = ChartDefinition(
    name="geti-controller",
    directory="geti_controller_chart",
    namespace="default",
)

PV_CHART = ChartDefinition(name="pv", directory="pv-creation", namespace="impt")
KUBELET_CSR_APPROVER_CHART = ChartDefinition(
    name="kubelet-csr-approver", directory="kubelet-csr-approver", namespace="kube-system"
)
CERT_MANAGER_CHART = ChartDefinition(
    name="cert-manager",
    directory="impt/charts/cert-manager",
    namespace="cert-manager",
    values_file="cert-manager-values.yaml",
    values_template_file="cert-manager-values.yaml.j2",
)
CERT_MANAGER_ISTIO_CSR_CHART = ChartDefinition(
    name="cert-manager-istio-csr" if not ambient_mesh else "ambient-istio-cert-manager-istio-csr",
    directory="impt/charts/cert-manager-istio-csr" if not ambient_mesh else "ambient-istio/cert-manager-istio-csr",
    namespace="cert-manager",
    values_file="cert-manager-istio-csr-values.yaml",
    values_template_file="cert-manager-istio-csr-values.yaml.j2",
)
ISTIO_BASE_CHART = ChartDefinition(
    name="istio-base" if not ambient_mesh else "ambient-istio-base",
    directory="istio/istio-base" if not ambient_mesh else "ambient-istio/base",
    namespace="istio-system",
)
ISTIO_CNI_CHART = ChartDefinition(
    name="ambient-istio-cni",
    directory="ambient-istio/cni",
    namespace="istio-system",
    values_file="istio-cni-values.yaml",
    values_template_file="istio-cni-values.yaml.j2",
)
ISTIO_GATEWAY_CHART = ChartDefinition(
    name="istio-gateway" if not ambient_mesh else "ambient-istio-gateway",
    directory="istio/istio-gateway" if not ambient_mesh else "ambient-istio/gateway",
    namespace="istio-system" if not ambient_mesh else "istio-ingress",
    values_file="istio-gateway-values.yaml",
    values_template_file="istio-gateway-values.yaml.j2",
)
ISTIO_ISTIOD_CHART = ChartDefinition(
    name="istio-istiod" if not ambient_mesh else "ambient-istio-istiod",
    directory="istio/istio-istiod" if not ambient_mesh else "ambient-istio/istiod",
    namespace="istio-system",
    values_file="istio-istiod-values.yaml",
    values_template_file="istio-istiod-values.yaml.j2",
)
ISTIO_ZTUNNEL_CHART = ChartDefinition(
    name="ambient-istio-ztunnel",
    directory="ambient-istio/ztunnel",
    namespace="istio-system",
    values_file="istio-ztunnel-values.yaml",
    values_template_file="istio-ztunnel-values.yaml.j2",
)
OPA_CHART = ChartDefinition(
    name="opa",
    directory="impt/charts/opa",
    namespace="opa-istio",
    values_file="opa-values.yaml",
    values_template_file="opa-values.yaml.j2",
)
INTERNAL_REGISTRY_CHART = ChartDefinition(
    name="internal-registry",
    directory="internal-registry",
    namespace="impt",
    values_file="internal-registry-values.yaml",
    values_template_file="internal-registry-values.yaml.j2",
)
SEAWEED_FS_CHART = ChartDefinition(
    name="seaweed-fs",
    directory="impt/charts/seaweed-fs",
    namespace="impt",
    values_file="seaweed-fs-values.yaml",
    values_template_file="seaweed-values.yaml.j2",
)
CONTROL_PLANE_CHART = ChartDefinition(
    name="control-plane",
    directory="control-plane",
    namespace="impt",
    values_file="control-plane-values.yaml",
    values_template_file="control-plane-values.yaml.j2",
)
PLATFORM_CHART = ChartDefinition(
    name="impt",
    directory="impt",
    namespace="impt",
    values_file="impt-values.yaml",
    values_template_file="impt-values.yaml.j2",
)
WEIGHT_UPLOADER = ChartDefinition(
    name="weight-uploader",
    directory="",
    namespace="impt",
    values_file="weight-uploader-job.yaml",
    values_template_file="weight-uploader-job.yaml.j2",
)
CRDS = ChartDefinition(name="crds", directory="crds", namespace="impt")
MIGRATION_JOB = ChartDefinition(
    name="migration-job",
    directory="migration-job",
    namespace="impt",
    values_file="migration-job-values.yaml",
    values_template_file="migration-job-values.yaml.j2",
)

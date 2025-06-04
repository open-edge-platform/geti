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
A module containing exceptions raised by checks functions.
"""

import subprocess


class StepsError(subprocess.SubprocessError):
    """
    Error raised by steps function.
    """


class LoadImagesError(StepsError):
    """
    Error raised by function used to load images.
    """


class ChartInstallationError(StepsError):
    """
    Error raised by function used to install/upgrade charts.
    """


class GetiControllerInstallationError(ChartInstallationError):
    """
    Error raised by function used to deploy Geti Controller chart.
    """


class GetiControllerUninstallationError(ChartInstallationError):
    """
    Error raised by function used to remove Geti Controller chart.
    """


class ChartPullError(StepsError):
    """
    Error raised by function used to pull charts.
    """


class ExtractRegistryDataError(StepsError):
    """
    Error raised by function used to extract registry data.
    """


class CreatePlatformDirectoryError(StepsError):
    """
    Error raised by function used to create platform directory.
    """


class CopyPlatformChartsError(StepsError):
    """
    Error raised by function used to copy platform charts.
    """


class InstallSystemPackagesError(StepsError):
    """
    Error raised by function used to install system packages.
    """


class DownloadSystemPackagesError(StepsError):
    """
    Exception raised when an error occurs while downloading system packages.
    """


class LabelError(StepsError):
    """
    Error raised by function used to relabeling kubernetes secrets
    """


class RemovePreviousK8SObjectsError(StepsError):
    """
    Error raised by function used to remove previous k8s objects
    """


class ConfigureGpuError(StepsError):
    """
    Error raised by function used to configure gpu.
    """


class NamespaceCreationError(StepsError):
    """
    Error raised by function used to create ns.
    """


class PatchServiceAccountError(StepsError):
    """
    Error raised by function used to patch sa.
    """


class KubeletCSRApproverInstallationError(ChartInstallationError):
    """
    Error raised by function used to deploy kubelet csr approver chart.
    """


class SeaweedFSInstallationError(ChartInstallationError):
    """
    Error raised by function used to deploy seaweedfs chart.
    """


class SeaweedFSBucketTTLError(ChartInstallationError):
    """
    Error raised by function setting ttl for seaweed buckets
    """


class IstioBaseInstallationError(ChartInstallationError):
    """
    Error raised by function used to deploy base chart.
    """


class OPAInstallationError(ChartInstallationError):
    """
    Error raised by function used to deploy OPA chart
    """


class CRDsInstallationError(ChartInstallationError):
    """
    Error raised by function used to deploy crds chart.
    """


class GenerateTemplateError(StepsError):
    """
    Error raised by function used to render template.
    """


class PVInstallationError(ChartInstallationError):
    """
    Error raised by function used to deploy PV chart
    """


class AllocatableResourcesError(StepsError):
    """
    Error raised by function used to get master node resources.
    """


class GenerateChartsResourcesError(StepsError):
    """
    Error raised by function used to generate charts resources.
    """


class CertManagerInstallationError(ChartInstallationError):
    """
    Error raised by function used to deploy Cert Manager chart.
    """


class GetSecretError(StepsError):
    """
    Error raised by function used to get secret.
    """


class CertManagerIstioCSRInstallationError(ChartInstallationError):
    """
    Error raised by function used to deploy Cert Manager Istio CSR chart.
    """


class IstioIstiodInstallationError(ChartInstallationError):
    """
    Error raised by function used to deploy IstioD chart.
    """


class IstioGatewayInstallationError(ChartInstallationError):
    """
    Error raised by function used to deploy Istio Gateway chart.
    """


class RestartDeploymentError(StepsError):
    """
    Error raised by function used to restart deployment
    """


class ContainerdConfigurationError(StepsError):
    """
    Error raised by function used to configure containerd.
    """


class ContainerdCertificateCreationError(StepsError):
    """
    Error raised by function used to create containerd certificates.
    """


class InternalRegistryInstallationError(ChartInstallationError):
    """
    Error raised by function used to deploy Internal Registry chart.
    """


class PlatformInstallationError(ChartInstallationError):
    """
    Error raised by function used to deploy Platform chart.
    """


class ControlPlaneInstallationError(ChartInstallationError):
    """
    Error raised by function used to deploy control plane
    """


class WeightUploaderInstallationError(ChartInstallationError):
    """
    Error raised by function used to deploy weight uploader job.
    """


class FailedJobError(StepsError):
    """
    Error raised by function waiting for job completion, caused by failed job
    """


class MigrationInstallationError(ChartInstallationError):
    """
    Error raised by function used to deploy migration job
    """


class CRDPatchingError(StepsError):
    """
    Exception raised when an error occurs while patching Kubernetes Custom Resource Definitions (CRDs).
    """


class PinImageVersionError(StepsError):
    """
    Exception raised when an error occurs while pinning registry image version
    """

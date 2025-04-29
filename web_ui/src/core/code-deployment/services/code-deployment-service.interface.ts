// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ProjectIdentifier } from '../../projects/core.interface';

interface DeploymentModelDTO {
    model_group_id: string;
    model_id: string;
}

interface DeploymentModel {
    modelGroupId: string;
    modelId: string;
}

export interface DownloadDeploymentPackageBodyDTO {
    package_type: 'ovms' | 'geti_sdk';
    models: DeploymentModelDTO[];
}

export interface DownloadDeploymentPackageBody {
    packageType: 'ovms' | 'geti_sdk';
    models: DeploymentModel[];
}

export interface CodeDeploymentService {
    downloadDeploymentPackage: (
        projectIdentifier: ProjectIdentifier,
        body: DownloadDeploymentPackageBody
    ) => Promise<void>;
}

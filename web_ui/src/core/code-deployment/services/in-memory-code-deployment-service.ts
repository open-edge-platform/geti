// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CodeDeploymentService } from './code-deployment-service.interface';

export const createInMemoryCodeDeploymentService = (): CodeDeploymentService => {
    const downloadDeploymentPackage: CodeDeploymentService['downloadDeploymentPackage'] = async (
        _projectIdentifier,
        _body
    ) => {
        return Promise.resolve();
    };
    return { downloadDeploymentPackage };
};

// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from '@geti/core';

import { CreateApiService } from '../../../../packages/core/src/services/create-api-service.interface';
import { API_URLS } from '../../../../packages/core/src/services/urls';
import { downloadFile } from '../../../shared/utils';
import { CodeDeploymentService, DownloadDeploymentPackageBodyDTO } from './code-deployment-service.interface';

export const createApiCodeDeploymentService: CreateApiService<CodeDeploymentService> = (
    { instance, router } = { instance: apiClient, router: API_URLS }
) => {
    const downloadDeploymentPackage: CodeDeploymentService['downloadDeploymentPackage'] = async (
        projectIdentifier,
        { packageType, models }
    ) => {
        const bodyDTO: DownloadDeploymentPackageBodyDTO = {
            package_type: packageType,
            models: models.map((model) => ({
                model_group_id: model.modelGroupId,
                model_id: model.modelId,
            })),
        };

        const { data } = await instance.post(router.DEPLOYMENT_PACKAGE_DOWNLOAD(projectIdentifier), bodyDTO, {
            responseType: 'blob',
        });

        const blob = new Blob([data], { type: 'application/zip' });
        const downloadURL = URL.createObjectURL(blob);
        const fileName = `${packageType.toLocaleLowerCase()}-deployment.zip`;

        downloadFile(downloadURL, fileName);

        URL.revokeObjectURL(downloadURL);
    };

    return {
        downloadDeploymentPackage,
    };
};

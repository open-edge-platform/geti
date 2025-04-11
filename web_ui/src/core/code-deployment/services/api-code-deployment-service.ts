// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { downloadFile } from '../../../shared/utils';
import { instance as defaultAxiosInstance } from '../../services/axios-instance';
import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { CodeDeploymentService, DownloadDeploymentPackageBodyDTO } from './code-deployment-service.interface';

export const createApiCodeDeploymentService: CreateApiService<CodeDeploymentService> = (
    { instance, router } = { instance: defaultAxiosInstance, router: API_URLS }
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

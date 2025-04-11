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

import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { ProjectIdentifier } from '../../projects/core.interface';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { getErrorMessage } from '../../services/utils';
import { DownloadDeploymentPackageBody } from '../services/code-deployment-service.interface';

interface UseDownloadDeploymentPackageMutation {
    projectIdentifier: ProjectIdentifier;
    body: DownloadDeploymentPackageBody;
}

interface UseCodeDeployment {
    useDownloadDeploymentPackageMutation: () => UseMutationResult<
        void,
        AxiosError,
        UseDownloadDeploymentPackageMutation
    >;
}

export const useCodeDeployment = (): UseCodeDeployment => {
    const { codeDeploymentService } = useApplicationServices();
    const { addNotification } = useNotification();

    const onError = (error: AxiosError) => {
        addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
    };

    const useDownloadDeploymentPackageMutation = (): UseMutationResult<
        void,
        AxiosError,
        UseDownloadDeploymentPackageMutation
    > => {
        return useMutation({
            mutationFn: ({ projectIdentifier, body }) =>
                codeDeploymentService.downloadDeploymentPackage(projectIdentifier, body),
            onError,
        });
    };

    return {
        useDownloadDeploymentPackageMutation,
    };
};

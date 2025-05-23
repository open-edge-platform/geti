// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { getErrorMessage } from '@geti/core/src/services/utils';
import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { ProjectIdentifier } from '../../projects/core.interface';
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

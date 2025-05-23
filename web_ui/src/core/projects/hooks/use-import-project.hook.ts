// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { getErrorMessage } from '../../services/utils';
import { ProjectImport, ProjectImportIdentifier } from '../project.interface';
import { ImportOptions } from '../services/project-service.interface';

interface UseImportProject {
    useImportProjectMutation: () => UseMutationResult<
        ProjectImport,
        AxiosError,
        {
            identifier: ProjectImportIdentifier;
            options: ImportOptions;
        }
    >;
}

export const IMPORT_STATUS_ERROR = 'Project is not uploaded due to an error.';

export const useImportProject = (): UseImportProject => {
    const { addNotification } = useNotification();
    const { projectService } = useApplicationServices();

    const useImportProjectMutation = () =>
        useMutation<
            ProjectImport,
            AxiosError,
            {
                identifier: ProjectImportIdentifier;
                options: ImportOptions;
            }
        >({
            mutationFn: ({ identifier, options }) => projectService.importProject(identifier, options),

            onError: (error: AxiosError) => {
                addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
            },
        });

    return {
        useImportProjectMutation,
    };
};

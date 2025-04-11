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
import { useApplicationServices } from '../../services/application-services-provider.component';
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

// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import {
    useMutation,
    UseMutationResult,
    useQueryClient,
    useSuspenseQuery,
    UseSuspenseQueryResult,
} from '@tanstack/react-query';
import { AxiosError } from 'axios';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import QUERY_KEYS from '../../requests/query-keys';
import { useApplicationServices } from '../../services/application-services-provider.component';
import { getErrorMessage } from '../../services/utils';
import { WorkspaceEntity } from '../services/workspaces.interface';

interface UseWorkspacesApi {
    useWorkspacesQuery: () => UseSuspenseQueryResult<WorkspaceEntity[], AxiosError>;
    useCreateWorkspaceMutation: () => UseMutationResult<WorkspaceEntity, AxiosError, Pick<WorkspaceEntity, 'name'>>;
    useEditWorkspaceMutation: () => UseMutationResult<WorkspaceEntity, AxiosError, WorkspaceEntity>;
    useDeleteWorkspaceMutation: () => UseMutationResult<void, AxiosError, Pick<WorkspaceEntity, 'id'>>;
}

export const useWorkspacesApi = (organizationId: string): UseWorkspacesApi => {
    const { workspacesService } = useApplicationServices();

    const queryClient = useQueryClient();
    const { addNotification } = useNotification();

    const useWorkspacesQuery: UseWorkspacesApi['useWorkspacesQuery'] = () => {
        return useSuspenseQuery<WorkspaceEntity[], AxiosError>({
            queryKey: QUERY_KEYS.WORKSPACES(organizationId),
            queryFn: () => workspacesService.getWorkspaces(organizationId),
            meta: { notifyOnError: true },
            staleTime: 1000 * 60,
        });
    };

    const useCreateWorkspaceMutation: UseWorkspacesApi['useCreateWorkspaceMutation'] = () => {
        return useMutation({
            mutationFn: async ({ name }) => {
                return workspacesService.createWorkspace(organizationId, name);
            },
            onSuccess: async () => {
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.WORKSPACES(organizationId) });
            },
            onError: (error) => {
                addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
            },
        });
    };

    const useEditWorkspaceMutation: UseWorkspacesApi['useEditWorkspaceMutation'] = () => {
        return useMutation({
            mutationFn: async (workspace) => {
                return workspacesService.editWorkspace({ organizationId, workspaceId: workspace.id }, workspace);
            },
            onSuccess: async () => {
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.WORKSPACES(organizationId) });
            },
            onError: (error) => {
                addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
            },
        });
    };

    const useDeleteWorkspaceMutation: UseWorkspacesApi['useDeleteWorkspaceMutation'] = () => {
        return useMutation({
            mutationFn: async ({ id }) => {
                return workspacesService.deleteWorkspace({ organizationId, workspaceId: id });
            },
            onSuccess: async () => {
                await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.WORKSPACES(organizationId) });
            },
            onError: (error) => {
                addNotification({ message: getErrorMessage(error), type: NOTIFICATION_TYPE.ERROR });
            },
        });
    };

    return {
        useWorkspacesQuery,
        useCreateWorkspaceMutation,
        useEditWorkspaceMutation,
        useDeleteWorkspaceMutation,
    };
};

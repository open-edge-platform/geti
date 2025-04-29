// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

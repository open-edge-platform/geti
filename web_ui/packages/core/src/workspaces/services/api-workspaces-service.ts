// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { apiClient } from 'index';

import { CreateApiService } from '../../services/create-api-service.interface';
import { API_URLS } from '../../services/urls';
import { WorkspaceDTO, WorkspacesResponseDTO } from '../dtos/workspace.interface';
import { getWorkspaceEntity, getWorkspaceEntityDTO, getWorkspacesEntity } from './utils';
import { WorkspacesService } from './workspaces-service.interface';
import { WorkspaceEntity, WorkspaceIdentifier } from './workspaces.interface';

export const createApiWorkspacesService: CreateApiService<WorkspacesService> = (
    { instance: platformInstance, router } = { instance: apiClient, router: API_URLS }
) => {
    const getWorkspaces = async (organizationId: string): Promise<WorkspaceEntity[]> => {
        const { data } = await platformInstance.get<WorkspacesResponseDTO>(router.WORKSPACES(organizationId));

        return getWorkspacesEntity(data);
    };

    const createWorkspace = async (organizationId: string, name: string): Promise<WorkspaceEntity> => {
        const { data } = await platformInstance.post<WorkspaceDTO>(router.WORKSPACES(organizationId), {
            name,
        });

        return getWorkspaceEntity(data);
    };

    const editWorkspace = async (
        workspaceIdentifier: WorkspaceIdentifier,
        workspace: WorkspaceEntity
    ): Promise<WorkspaceEntity> => {
        const { organizationId } = workspaceIdentifier;
        const { data } = await platformInstance.put<WorkspaceDTO>(
            router.WORKSPACE({ organizationId, workspaceId: workspace.id }),
            getWorkspaceEntityDTO(workspace)
        );

        return getWorkspaceEntity(data);
    };

    const deleteWorkspace = async (workspaceIdentifier: WorkspaceIdentifier): Promise<void> => {
        await platformInstance.delete(router.WORKSPACE(workspaceIdentifier));
    };

    return { getWorkspaces, createWorkspace, editWorkspace, deleteWorkspace };
};

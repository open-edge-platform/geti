// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedWorkspace } from '../../../test-utils/mocked-items-factory/mocked-workspace';
import { WorkspacesService } from './workspaces-service.interface';
import { WorkspaceEntity, WorkspaceIdentifier } from './workspaces.interface';

export const createInMemoryApiWorkspacesService = (): WorkspacesService => {
    const getWorkspaces = async (): Promise<WorkspaceEntity[]> => {
        return Promise.resolve([
            getMockedWorkspace({ id: 'workspace-id', name: 'Workspace 1' }),
            getMockedWorkspace({ id: 'workspace-id2', name: 'Workspace 2' }),
        ]);
    };

    const createWorkspace = async (_organizationId: string, _workspaceName: string): Promise<WorkspaceEntity> =>
        Promise.resolve(
            getMockedWorkspace({
                id: 'workspace-id',
                name: 'Workspace 1',
            })
        );

    const editWorkspace = async (
        _workspaceIdentifier: WorkspaceIdentifier,
        _workspace: WorkspaceEntity
    ): Promise<WorkspaceEntity> =>
        Promise.resolve(
            getMockedWorkspace({
                id: 'workspace-id',
                name: 'Workspace 1',
            })
        );

    const deleteWorkspace = async (_workspaceIdentifier: WorkspaceIdentifier): Promise<void> => {
        return Promise.resolve();
    };

    return { getWorkspaces, createWorkspace, editWorkspace, deleteWorkspace };
};

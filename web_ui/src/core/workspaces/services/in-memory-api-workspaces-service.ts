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

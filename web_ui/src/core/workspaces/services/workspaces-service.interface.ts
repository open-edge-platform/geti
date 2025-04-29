// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { WorkspaceEntity, WorkspaceIdentifier } from './workspaces.interface';

export interface WorkspacesService {
    getWorkspaces: (organizationId: string) => Promise<WorkspaceEntity[]>;
    createWorkspace: (organizationId: string, workspaceName: string) => Promise<WorkspaceEntity>;
    editWorkspace: (workspaceIdentifier: WorkspaceIdentifier, workspace: WorkspaceEntity) => Promise<WorkspaceEntity>;
    deleteWorkspace: (workspaceIdentifier: WorkspaceIdentifier) => Promise<void>;
}

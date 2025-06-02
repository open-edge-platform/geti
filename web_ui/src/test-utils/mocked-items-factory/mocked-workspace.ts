// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { WorkspaceEntity } from '@geti/core/src/workspaces/services/workspaces.interface';

export const getMockedWorkspace = (workspace: Partial<WorkspaceEntity> = {}): WorkspaceEntity => ({
    id: 'workspace-id',
    name: 'Workspace 1',
    modifiedAt: '',
    modifiedBy: '',
    createdBy: '',
    organizationId: '',
    createdAt: '',
    ...workspace,
});

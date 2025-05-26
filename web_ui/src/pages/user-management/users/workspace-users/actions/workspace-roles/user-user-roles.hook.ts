// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { WorkspaceEntity } from '@geti/core/src/workspaces/services/workspaces.interface';

import { WorkspaceRole } from '../../../../../../core/users/users.interface';

export function useUserRoles(workspaces: WorkspaceEntity[], workspaceRoles: WorkspaceRole[]) {
    //TODO: add check to have at least one admin in the workspace
    const takenWorkspacesIds = workspaceRoles.map(({ workspace }) => workspace.id);
    const availableWorkspaces = workspaces.filter(({ id }) => !takenWorkspacesIds.includes(id));
    const canAddNewRole = !workspaces.every((workspace) => takenWorkspacesIds.includes(workspace.id));

    return { canAddNewRole, availableWorkspaces };
}

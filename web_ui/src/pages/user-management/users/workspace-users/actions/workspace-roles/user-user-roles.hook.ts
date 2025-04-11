// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { WorkspaceRole } from '../../../../../../core/users/users.interface';
import { WorkspaceEntity } from '../../../../../../core/workspaces/services/workspaces.interface';

export function useUserRoles(workspaces: WorkspaceEntity[], workspaceRoles: WorkspaceRole[]) {
    //TODO: add check to have at least one admin in the workspace
    const takenWorkspacesIds = workspaceRoles.map(({ workspace }) => workspace.id);
    const availableWorkspaces = workspaces.filter(({ id }) => !takenWorkspacesIds.includes(id));
    const canAddNewRole = !workspaces.every((workspace) => takenWorkspacesIds.includes(workspace.id));

    return { canAddNewRole, availableWorkspaces };
}

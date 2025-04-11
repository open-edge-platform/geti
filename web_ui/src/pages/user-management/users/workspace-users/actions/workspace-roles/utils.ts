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

import { RESOURCE_TYPE, RoleResource, WorkspaceRole } from '../../../../../../core/users/users.interface';
import { WorkspaceEntity } from '../../../../../../core/workspaces/services/workspaces.interface';
import { hasEqualId } from '../../../../../../shared/utils';

export const getUpdatedWorkspaceRoles = <T>(editedWorkspaceRole: T, index: number, workspaceRoles: T[]): T[] => {
    const prefixPart = index > 0 ? [...workspaceRoles.slice(0, index)] : [];
    const suffixPart = index + 1 < workspaceRoles.length ? [...workspaceRoles.slice(index + 1)] : [];
    return [...prefixPart, editedWorkspaceRole, ...suffixPart];
};

export const mapRolesToWorkspaceRoles = (roles: RoleResource[], workspaces: WorkspaceEntity[]): WorkspaceRole[] =>
    roles
        .filter((role) => role.resourceType === RESOURCE_TYPE.WORKSPACE)
        .map((role) => ({
            role: role.role as WorkspaceRole['role'],
            workspace: workspaces.find(hasEqualId(role.resourceId)) as WorkspaceEntity,
        }));

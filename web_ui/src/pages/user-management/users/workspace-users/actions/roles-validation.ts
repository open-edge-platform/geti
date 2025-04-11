// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { isWorkspaceAdmin, isWorkspaceContributor } from '../../../../../core/users/user-role-utils';
import { User, USER_ROLE, WorkspaceRole } from '../../../../../core/users/users.interface';

export const getAvailableRoles = ({
    activeMember,
    members,
    workspaceId,
    isAccountOwner,
}: {
    activeMember: User;
    members: User[];
    workspaceId: string;
    isAccountOwner: boolean;
}): WorkspaceRole['role'][] => {
    const isActiveUserWorkspaceContributor = isWorkspaceContributor(activeMember, workspaceId);

    if (isActiveUserWorkspaceContributor) {
        return [];
    }

    if (members.length === 1) {
        return [];
    }

    const isActiveUserWorkspaceAdmin = isWorkspaceAdmin(activeMember, workspaceId);
    const atLeastTwoAdminsExist = members.filter((user) => isWorkspaceAdmin(user, workspaceId)).length >= 2;

    if (isActiveUserWorkspaceAdmin && atLeastTwoAdminsExist) {
        return [USER_ROLE.WORKSPACE_ADMIN, USER_ROLE.WORKSPACE_CONTRIBUTOR];
    }

    if (isActiveUserWorkspaceAdmin && !isAccountOwner) {
        return [USER_ROLE.WORKSPACE_ADMIN, USER_ROLE.WORKSPACE_CONTRIBUTOR];
    }

    return [];
};

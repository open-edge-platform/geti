// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isWorkspaceAdmin, isWorkspaceContributor } from '@geti/core/src/users/user-role-utils';
import { User, USER_ROLE, WorkspaceRole } from '@geti/core/src/users/users.interface';

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

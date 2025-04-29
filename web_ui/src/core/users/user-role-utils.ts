// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RESOURCE_TYPE, User, USER_ROLE } from './users.interface';

export const isOrganizationAdmin = (user: User, organizationId: string): boolean => {
    return user.roles.some(
        ({ resourceId, resourceType, role }) =>
            resourceType === RESOURCE_TYPE.ORGANIZATION &&
            resourceId === organizationId &&
            role === USER_ROLE.ORGANIZATION_ADMIN
    );
};

export const isWorkspaceAdmin = (user: User, workspaceId: string): boolean => {
    return user.roles.some(
        ({ resourceId, resourceType, role }) =>
            resourceType === RESOURCE_TYPE.WORKSPACE && resourceId === workspaceId && role === USER_ROLE.WORKSPACE_ADMIN
    );
};

export const isWorkspaceContributor = (member: User, workspaceId: string): boolean => {
    return member.roles.some(
        ({ resourceId, resourceType, role }) =>
            resourceType === RESOURCE_TYPE.WORKSPACE &&
            resourceId === workspaceId &&
            role === USER_ROLE.WORKSPACE_CONTRIBUTOR
    );
};

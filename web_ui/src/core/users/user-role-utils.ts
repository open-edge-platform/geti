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

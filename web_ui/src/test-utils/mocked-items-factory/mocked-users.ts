// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RESOURCE_TYPE, User, USER_ROLE } from '../../../packages/core/src/users/users.interface';
import { AccountStatus } from '../../core/organizations/organizations.interface';

const mockedUser: User = {
    id: 'user-1-id',
    firstName: 'Test',
    lastName: 'User',
    email: 'test@intel.com',
    status: AccountStatus.ACTIVATED,
    externalIdentitySystemId: '',
    organizationStatus: AccountStatus.ACTIVATED,
    modifiedBy: null,
    modifiedAt: null,
    lastSuccessfulLogin: '2023-08-14T11:13:01.679Z',
    createdBy: 'admin@intel.com',
    createdAt: '2023-08-14T11:13:01.679Z',
    organizationId: 'organization-id',
    country: 'US',
    userPhoto: null,
    isAdmin: false,
    roles: [
        {
            role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
            resourceId: '111',
            resourceType: RESOURCE_TYPE.WORKSPACE,
        },
    ],
    currentSuccessfulLogin: null,
};

export const getMockedUser = (customUser: Partial<User> = {}): User => {
    return {
        ...mockedUser,
        ...customUser,
    };
};

export const getMockedOrganizationAdminUser = (
    adminUser: Partial<User> = {},
    workspaceId = 'workspace-id',
    organizationId = 'organization-id'
): User => getMockedAdminUser(adminUser, workspaceId, true, organizationId);

export const getMockedOrganizationContributorUser = (user: Partial<User> = {}): User => {
    return getMockedUser({
        organizationId: 'organization-id',
        roles: [
            {
                resourceId: 'organization-id',
                role: USER_ROLE.ORGANIZATION_CONTRIBUTOR,
                resourceType: RESOURCE_TYPE.ORGANIZATION,
            },
        ],
        ...user,
    });
};

export const getMockedAdminUser = (
    adminUser: Partial<User> = {},
    workspaceId = 'workspace-id',
    isOrganizationAdmin = false,
    organizationId = 'organization-id'
): User => {
    const orgAdminRole = isOrganizationAdmin
        ? [
              {
                  role: USER_ROLE.ORGANIZATION_ADMIN,
                  resourceId: organizationId,
                  resourceType: RESOURCE_TYPE.ORGANIZATION,
              },
          ]
        : [];

    return getMockedUser({
        ...adminUser,
        isAdmin: true,
        roles: [
            {
                role: USER_ROLE.WORKSPACE_ADMIN,
                resourceId: workspaceId,
                resourceType: RESOURCE_TYPE.WORKSPACE,
            },
            ...orgAdminRole,
        ],
    });
};

export const getMockedContributorUser = (customUser: Partial<User> = {}, workspaceId: string = 'workspace-id'): User =>
    getMockedUser({
        ...customUser,
        isAdmin: false,
        roles: [
            {
                role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
                resourceId: workspaceId,
                resourceType: RESOURCE_TYPE.WORKSPACE,
            },
        ],
    });

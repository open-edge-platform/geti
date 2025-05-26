// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';
import { ResourceTypeDTO, UserDTO, UserRoleDTO } from '@geti/core/src/users/users.interface';
import { v4 as uuid } from 'uuid';

import { AccountStatusDTO } from '../../../src/core/organizations/dtos/organizations.interface';

export const ACCOUNT_URL = (organizationId: string, tab: string) => `${paths.account.index({ organizationId })}/${tab}`;

export const organizationId = '5b1f89f3-aba5-4a5f-84ab-de9abb8e0633';

export const workspace = {
    id: '128deb13-11ea-4dea-b050-8f8e308b7d8e',
    name: 'Default workspace',
    organizationId,
    createdAt: '2024-11-25T21:28:27Z',
    createdBy: '',
    modifiedAt: null,
    modifiedBy: '',
};

export const getMockedMember = (member: Partial<UserDTO> = {}): UserDTO => ({
    id: uuid(),
    firstName: 'admin',
    secondName: 'admin',
    email: 'admin@intel.com',
    externalId: 'Cjljbj00MjU4ZDQwNi03MDYzLZTA4MTY5NmYsZGM9ZXhhbXBsZSxkYz1vcmcSDXJlZ3VsYXJfdXNlcnM',
    country: '',
    status: AccountStatusDTO.ACTIVE,
    organizationId,
    organizationStatus: AccountStatusDTO.ACTIVE,
    roles: [
        {
            role: UserRoleDTO.ORGANIZATION_ADMIN,
            resourceType: ResourceTypeDTO.ORGANIZATION,
            resourceId: organizationId,
        },
        {
            role: UserRoleDTO.WORKSPACE_ADMIN,
            resourceType: ResourceTypeDTO.WORKSPACE,
            resourceId: workspace.id,
        },
    ],
    lastSuccessfulLogin: null,
    currentSuccessfulLogin: null,
    createdAt: null,
    createdBy: '',
    modifiedAt: null,
    modifiedBy: '',
    userPhoto: null,
    ...member,
});

export const workspaceAdmin1 = getMockedMember({
    id: '4258d406-7063-4b03-92b2-3b7de081696f',
    firstName: 'admin',
    secondName: 'admin',
    email: 'test@intel.com',
});

export const workspaceAdmin2 = getMockedMember({
    id: 'cd115bf7-507e-434a-bddb-ddc36e2331b9',
    firstName: 'Test',
    secondName: 'User',
    email: 'test2@intel.com',
});

export const workspaceContributor = getMockedMember({
    id: '1eec44a1-5f64-4a93-a67c-3edaf4d27f7d',
    firstName: 'Another',
    secondName: 'Contributor',
    email: 'test3@intel.com',
    externalId: 'Cjljbj0xZWVjNDRhMS01ZjY0LTRRkMjdmN2QsZGM9ZXhhbXBsZSxkYz1vcmcSDXJlZ3VsYXJfdXNlcnM',
    roles: [
        {
            role: UserRoleDTO.ORGANIZATION_CONTRIBUTOR,
            resourceType: ResourceTypeDTO.ORGANIZATION,
            resourceId: organizationId,
        },
        {
            role: UserRoleDTO.WORKSPACE_CONTRIBUTOR,
            resourceType: ResourceTypeDTO.WORKSPACE,
            resourceId: workspace.id,
        },
    ],
});

export const membersPayload = {
    users: [workspaceAdmin1, workspaceAdmin2, workspaceContributor],
    totalCount: 3,
    totalMatchedCount: 3,
    nextPage: {
        skip: 20,
        limit: 0,
    },
};

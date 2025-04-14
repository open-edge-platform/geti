// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AccountStatus } from '../../../core/organizations/organizations.interface';
import { USER_ROLE } from '../../../core/users/users.interface';

export interface Membership {
    id: string;
    organizationId: string;
    organizationName: string;
    status: AccountStatus;
    createdAt: string;
    role: USER_ROLE.ORGANIZATION_CONTRIBUTOR | USER_ROLE.ORGANIZATION_ADMIN;
}

export const MOCKED_MEMBERSHIPS: Membership[] = [
    {
        id: '1',
        organizationId: 'org1',
        organizationName: 'Organization One',
        status: AccountStatus.ACTIVATED,
        createdAt: '2023-01-01T00:00:00Z',
        role: USER_ROLE.ORGANIZATION_ADMIN,
    },
    {
        id: '2',
        organizationId: 'org2',
        organizationName: 'Organization Two',
        status: AccountStatus.INVITED,
        createdAt: '2023-02-01T00:00:00Z',
        role: USER_ROLE.ORGANIZATION_CONTRIBUTOR,
    },
    {
        id: '3',
        organizationId: 'org3',
        organizationName: 'Organization Three',
        status: AccountStatus.SUSPENDED,
        createdAt: '2023-03-01T00:00:00Z',
        role: USER_ROLE.ORGANIZATION_ADMIN,
    },
    {
        id: '4',
        organizationId: 'org4',
        organizationName: 'Organization Four',
        status: AccountStatus.DELETED,
        createdAt: '2023-04-01T00:00:00Z',
        role: USER_ROLE.ORGANIZATION_CONTRIBUTOR,
    },
    {
        id: '5',
        organizationId: 'org5',
        organizationName: 'Organization Five',
        status: AccountStatus.ACTIVATED,
        createdAt: '2023-05-01T00:00:00Z',
        role: USER_ROLE.ORGANIZATION_ADMIN,
    },
];

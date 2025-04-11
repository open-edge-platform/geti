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

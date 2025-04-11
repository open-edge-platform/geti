// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { CreditAccountsResponseDTO } from '../../../src/core/credits/dtos/credits.interface';
import {
    AccountStatusDTO,
    OrganizationDTO,
    OrganizationsResponseDTO,
} from '../../../src/core/organizations/dtos/organizations.interface';
import { getMockedCreditAccountDTO } from '../../../src/test-utils/mocked-items-factory/mocked-credit-accounts';
import { getMockedOrganizationDTO } from '../../../src/test-utils/mocked-items-factory/mocked-organization';

export const mockedOrganizations: OrganizationDTO[] = [
    getMockedOrganizationDTO({
        name: 'Test Org',
        admins: [
            {
                firstName: 'John',
                lastName: 'Doe',
                email: 'test@testorg.com',
            },
        ],
    }),
    getMockedOrganizationDTO({
        name: 'Google',
        admins: [
            {
                firstName: 'Paul',
                lastName: 'Doe',
                email: 'test2@testorg2.com',
            },
        ],
        status: AccountStatusDTO.ACTIVE,
    }),
    getMockedOrganizationDTO({
        name: 'Microsoft',
        admins: [
            {
                firstName: 'Mike',
                lastName: 'Doe',
                email: 'test3@testorg3.com',
            },
        ],
        status: AccountStatusDTO.ACTIVE,
    }),
    getMockedOrganizationDTO({
        name: 'Facebook',
        admins: [
            {
                firstName: 'Chris',
                lastName: 'Doe',
                email: 'test4@testorg4.com',
            },
        ],
        status: AccountStatusDTO.SUSPENDED,
    }),
    getMockedOrganizationDTO({
        name: 'Uber',
        admins: [
            {
                firstName: 'Peter',
                lastName: 'Doe',
                email: 'test5@testorg5.com',
            },
        ],
        status: AccountStatusDTO.SUSPENDED,
    }),
    getMockedOrganizationDTO({
        name: 'Airbnb',
        admins: [
            {
                firstName: 'Oliver',
                lastName: 'Doe',
                email: 'test6@testorg6.com',
            },
        ],
        status: AccountStatusDTO.REGISTERED,
    }),
];

export const mockedOrganizationsResponse: OrganizationsResponseDTO = {
    organizations: mockedOrganizations,
    totalCount: mockedOrganizations.length,
    totalMatchedCount: mockedOrganizations.length,
    nextPage: {
        skip: 1,
        limit: 0,
    },
};

export const mockedCreditAccounts: CreditAccountsResponseDTO = {
    credit_accounts: [
        getMockedCreditAccountDTO({ name: 'Renewable credits' }),
        getMockedCreditAccountDTO({ name: 'Welcoming credits' }),
    ],
    total: 2,
    total_matched: 2,
    next_page: null,
};

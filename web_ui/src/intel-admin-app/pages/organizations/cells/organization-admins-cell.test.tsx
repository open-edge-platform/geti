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

import { screen } from '@testing-library/react';

import { getMockedOrganization } from '../../../../test-utils/mocked-items-factory/mocked-organization';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { checkTooltip } from '../../../../test-utils/utils';
import { OrganizationAdminsCell } from './organization-admins-cell.component';

describe('OrganizationAdminsCell', () => {
    afterAll(() => {
        jest.useRealTimers();
        jest.clearAllTimers();
    });

    it('Check if admins cell is returning proper result - one admin', async () => {
        const mockedOrganizationWithOneAdmin = getMockedOrganization({
            name: 'Organization',
            id: 'organization',
            admins: [
                {
                    firstName: 'Jane',
                    lastName: 'Doe',
                    email: 'jane@doe.com',
                },
            ],
        });

        render(
            <OrganizationAdminsCell
                columnIndex={2}
                dataKey={'role'}
                rowData={mockedOrganizationWithOneAdmin}
                rowIndex={1}
                isScrolling={false}
            />
        );

        expect(screen.getByTestId('organization-Organization-admins-cell-content')).toHaveTextContent('Jane Doe');
    });

    it('Check if admins cell is returning proper result - one admin without full name', async () => {
        const mockedOrganizationOnlyMailAdmin = getMockedOrganization({
            name: 'Organization',
            id: 'organization',
            admins: [
                {
                    firstName: '',
                    lastName: '',
                    email: 'admin@intel.com',
                },
            ],
        });

        render(
            <OrganizationAdminsCell
                columnIndex={2}
                dataKey={'role'}
                rowData={mockedOrganizationOnlyMailAdmin}
                rowIndex={1}
                isScrolling={false}
            />
        );

        expect(screen.getByTestId('organization-Organization-admins-cell-content')).toHaveTextContent(
            'admin@intel.com'
        );
    });

    it('Check if admins cell is returning proper result - two admins', async () => {
        const mockedOrganizationWithTwoAdmins = getMockedOrganization({
            name: 'Organization',
            id: 'organization',
            admins: [
                {
                    firstName: 'Jane',
                    lastName: 'Doe',
                    email: 'jane@doe.com',
                },
                {
                    firstName: 'Frank',
                    lastName: 'Second',
                    email: 'frank@second.com',
                },
            ],
        });

        await render(
            <OrganizationAdminsCell
                columnIndex={2}
                dataKey={'role'}
                rowData={mockedOrganizationWithTwoAdmins}
                rowIndex={1}
                isScrolling={false}
            />
        );

        expect(screen.getByTestId('organization-Organization-admins-cell-content')).toHaveTextContent(
            'Jane Doe,Frank Second'
        );
    });

    it('Check copying of admin email tooltip', async () => {
        jest.useFakeTimers();

        const mockedOrganizationWithTwoAdmins = getMockedOrganization({
            name: 'Organization',
            id: 'organization',
            admins: [
                {
                    firstName: 'Jane',
                    lastName: 'Doe',
                    email: 'jane@doe.com',
                },
                {
                    firstName: 'Frank',
                    lastName: 'Second',
                    email: 'frank@second.com',
                },
            ],
        });

        await render(
            <OrganizationAdminsCell
                columnIndex={2}
                dataKey={'role'}
                rowData={mockedOrganizationWithTwoAdmins}
                rowIndex={1}
                isScrolling={false}
            />
        );

        await checkTooltip(screen.getByText('Jane Doe'), 'jane@doe.com');
    });
});

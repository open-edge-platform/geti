// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

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

import { fireEvent, screen, within } from '@testing-library/react';

import { AccountStatus, Organization } from '../../../core/organizations/organizations.interface';
import { getMockedOrganization } from '../../../test-utils/mocked-items-factory/mocked-organization';
import { getMockedAdminUser } from '../../../test-utils/mocked-items-factory/mocked-users';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { OrganizationsTable } from './organizations-table.component';
import { OrganizationsMenuItems } from './utils';

const activatedOrganization = getMockedOrganization({
    id: 'google-id',
    name: 'Google',
    status: AccountStatus.ACTIVATED,
    admins: [getMockedAdminUser({ email: 'test2@testorg2.com' })],
});
const deletedOrganization = getMockedOrganization({ id: 'fb-id', name: 'Facebook', status: AccountStatus.DELETED });
const suspendedOrganization = getMockedOrganization({ id: 'uber-id', name: 'Uber', status: AccountStatus.SUSPENDED });
const invitedOrganization = getMockedOrganization({ id: 'airbnb-id', name: 'Airbnb', status: AccountStatus.INVITED });
const requestedAccessOrganization = getMockedOrganization({
    id: 'ms-id',
    name: 'Microsoft',
    status: AccountStatus.REQUESTED_ACCESS,
});

const mockedOrganizations = [
    activatedOrganization,
    requestedAccessOrganization,
    deletedOrganization,
    suspendedOrganization,
    invitedOrganization,
];

const getMenu = (organizationName: string) => {
    return screen.queryByRole('button', { name: `${organizationName} menu button` });
};

const openMenu = (organizationName: string) => {
    const menu = getMenu(organizationName);

    menu !== null && fireEvent.click(menu);
};

const getMenuItem = (menuItem: OrganizationsMenuItems) => {
    return screen.queryByRole('menuitem', { name: new RegExp(menuItem, 'i') });
};

const renderOrganizationsTable = (organizations: Organization[]) => {
    return render(
        <OrganizationsTable
            organizations={organizations}
            isLoading={false}
            isFetchingNextPage={false}
            getNextPage={jest.fn()}
            queryOptions={{}}
            setOrganizationsQueryOptions={jest.fn()}
        />
    );
};

describe('OrganizationsTable', () => {
    it('Check if organizations data is visible', () => {
        renderOrganizationsTable(mockedOrganizations);

        expect(screen.getByRole('grid')).toHaveAttribute('aria-rowcount', `${1 + mockedOrganizations.length}`); // Header + all organizations

        const headersElements = screen.getAllByRole('columnheader');
        const expectedHeaders = ['ORGANIZATION', 'ADMINS', 'STATUS', 'MEMBERSHIP SINCE', ''];

        expect(headersElements).toHaveLength(expectedHeaders.length);

        headersElements.map((header, index) => {
            expect(header).toHaveTextContent(expectedHeaders[index]);
        });

        mockedOrganizations.forEach((organization) => {
            const row = screen.getByRole('row', { name: new RegExp(organization.name) });

            expect(within(row).getByText(organization.name)).toBeInTheDocument();
            expect(within(row).getByText(organization.status)).toBeInTheDocument();
        });
    });

    it('should display ACTIVATE and DELETE menu option when status is REQUESTED ACCESS', () => {
        renderOrganizationsTable([requestedAccessOrganization]);

        openMenu(requestedAccessOrganization.name);
        expect(getMenuItem(OrganizationsMenuItems.ACTIVATE)).toBeInTheDocument();
        expect(getMenuItem(OrganizationsMenuItems.DELETE)).toBeInTheDocument();
        expect(getMenuItem(OrganizationsMenuItems.SUSPEND)).not.toBeInTheDocument();
    });

    it('should display SUSPEND and DELETE menu option when status is ACTIVATED', () => {
        renderOrganizationsTable([activatedOrganization]);

        openMenu(activatedOrganization.name);
        expect(getMenuItem(OrganizationsMenuItems.ACTIVATE)).not.toBeInTheDocument();
        expect(getMenuItem(OrganizationsMenuItems.DELETE)).toBeInTheDocument();
        expect(getMenuItem(OrganizationsMenuItems.SUSPEND)).toBeInTheDocument();
    });

    it('should display DELETE menu option when status is INVITED', () => {
        renderOrganizationsTable([invitedOrganization]);

        openMenu(invitedOrganization.name);
        expect(getMenuItem(OrganizationsMenuItems.ACTIVATE)).not.toBeInTheDocument();
        expect(getMenuItem(OrganizationsMenuItems.DELETE)).toBeInTheDocument();
        expect(getMenuItem(OrganizationsMenuItems.SUSPEND)).not.toBeInTheDocument();
    });

    it('should display no menu when status is DELETED', () => {
        renderOrganizationsTable([deletedOrganization]);

        expect(getMenu(deletedOrganization.name)).not.toBeInTheDocument();
    });
});

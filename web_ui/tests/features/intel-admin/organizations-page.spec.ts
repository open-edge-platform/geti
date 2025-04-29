// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    AccountStatusDTO,
    OrganizationsResponseDTO,
} from '../../../src/core/organizations/dtos/organizations.interface';
import { getMockedOrganizationDTO } from '../../../src/test-utils/mocked-items-factory/mocked-organization';
import { test } from '../../fixtures/base-test';
import { registerApiOrganizations } from './api';
import { expectTableContainsUserRow, expectToHaveNRows, expectToHaveTableContent } from './expect';
import { mockedOrganizationsResponse } from './mocks';

test.describe('Organizations list screen', () => {
    test('Filters correctly based on search terms or account status', async ({
        page,
        registerApiResponse,
        intelAdminPage,
    }) => {
        const organizations = registerApiOrganizations({ registerApiResponse });

        await intelAdminPage.goToOrganizationsListPage();

        await expectToHaveTableContent(page, organizations.get());

        await intelAdminPage.filterByNameOrEmail('Google');

        /* Filter by name */
        await expectTableContainsUserRow(page, {
            name: 'Google',
            admin: 'Paul Doe',
            status: 'Activated',
        });

        await intelAdminPage.clearSearchField();

        // After clearing search field we want to return initial organizations
        organizations.reset();

        await expectToHaveTableContent(page, organizations.get());

        /* Filter by email */
        await intelAdminPage.filterByNameOrEmail('test2@testorg2.com');
        await expectTableContainsUserRow(page, {
            name: 'Google',
            admin: 'Paul Doe',
            status: 'Activated',
        });

        await intelAdminPage.clearSearchField();
        organizations.reset();

        await expectToHaveTableContent(page, organizations.get());

        /* Filter by account status */
        await intelAdminPage.filterByOrganizationStatus('Activated');

        // 3 Organizations are activated
        await expectToHaveTableContent(page, organizations.get());
    });

    test('Inviting an organization', async ({ page, intelAdminPage, registerApiResponse }) => {
        const email = 'testemail@intel.com';
        const organizationName = 'Playwright org';
        const adminName = 'Chris Sawyer';

        const organizations = registerApiOrganizations({ registerApiResponse });

        await intelAdminPage.goToOrganizationsListPage();

        await expectToHaveTableContent(page, organizations.get());

        const inviteOrganizationRequestPromise = page.waitForRequest((req) => {
            return req.method() === 'POST' && req.url().includes('organizations/invitations');
        });

        await intelAdminPage.clickSendInvite();
        await intelAdminPage.fillInviteForm(email, organizationName);

        const inviteOrganizationRequest = await inviteOrganizationRequestPromise;
        const inviteOrganizationRequestPayload = inviteOrganizationRequest.postDataJSON();

        await expectTableContainsUserRow(page, {
            name: inviteOrganizationRequestPayload.organizationData.name,
            admin: adminName,
            status: 'Invited',
        });
    });

    test('Suspending/Activating an organization', async ({ page, intelAdminPage, registerApiResponse }) => {
        const organizations = registerApiOrganizations({ registerApiResponse });

        await intelAdminPage.goToOrganizationsListPage();

        await expectToHaveTableContent(page, organizations.get());

        // Select 'Google' org and suspend it
        await intelAdminPage.suspendOrganization('Google');

        await expectTableContainsUserRow(page, {
            name: 'Google',
            admin: 'Paul Doe',
            status: 'Suspended',
        });

        // Activate 'Google' org again
        await intelAdminPage.activateOrganization('Google');

        await expectTableContainsUserRow(page, {
            name: 'Google',
            admin: 'Paul Doe',
            status: 'Activated',
        });
    });

    test('Deleting an organization', async ({ page, intelAdminPage, registerApiResponse }) => {
        const organizations = registerApiOrganizations({ registerApiResponse });

        await intelAdminPage.goToOrganizationsListPage();

        await expectToHaveTableContent(page, organizations.get());

        // Select 'Google' org and delete it
        await intelAdminPage.deleteOrganization('Google');

        await expectTableContainsUserRow(page, {
            name: 'Google',
            admin: 'Paul Doe',
            status: 'Deleted',
        });
    });

    test.describe('FEATURE_FLAG_REQ_ACCESS: true', () => {
        test.use({
            featureFlags: {
                FEATURE_FLAG_REQ_ACCESS: true,
            },
        });

        const requestedAccessOrganization = getMockedOrganizationDTO({
            name: 'Bolt',
            admins: [
                {
                    firstName: 'Scott',
                    lastName: 'Doe',
                    email: 'vp@bolt.com',
                },
            ],
            status: AccountStatusDTO.REQUESTED_ACCESS,
        });

        const mockedOrganization = [requestedAccessOrganization, ...mockedOrganizationsResponse.organizations];

        const organizationsResponse: OrganizationsResponseDTO = {
            organizations: mockedOrganization,
            totalCount: mockedOrganization.length,
            totalMatchedCount: mockedOrganization.length,
            nextPage: {
                skip: 0,
                limit: 10,
            },
        };

        test('Filters based on REQUESTED_ACCESS status', async ({ page, intelAdminPage, registerApiResponse }) => {
            const organizations = registerApiOrganizations({
                registerApiResponse,
                inputOrganizations: organizationsResponse,
            });

            await intelAdminPage.goToOrganizationsListPage();

            await expectToHaveTableContent(page, organizations.get());

            await intelAdminPage.filterByOrganizationStatus('Requested access');

            await expectToHaveNRows(page, 1);

            await expectToHaveTableContent(page, organizations.get());

            await expectTableContainsUserRow(page, {
                name: requestedAccessOrganization.name,
                admin:
                    requestedAccessOrganization.admins[0].firstName +
                    ' ' +
                    requestedAccessOrganization.admins[0].lastName,
                status: requestedAccessOrganization.status,
            });
        });

        test('Activates and deletes organization that has requested access', async ({
            page,
            intelAdminPage,
            registerApiResponse,
        }) => {
            const organizations = registerApiOrganizations({
                registerApiResponse,
                inputOrganizations: organizationsResponse,
            });

            await intelAdminPage.goToOrganizationsListPage();

            await expectToHaveTableContent(page, organizations.get());

            await intelAdminPage.activateOrganization(requestedAccessOrganization.name);

            await expectTableContainsUserRow(page, {
                name: requestedAccessOrganization.name,
                admin:
                    requestedAccessOrganization.admins[0].firstName +
                    ' ' +
                    requestedAccessOrganization.admins[0].lastName,
                status: 'Activated',
            });

            await intelAdminPage.deleteOrganization(requestedAccessOrganization.name);

            await expectTableContainsUserRow(page, {
                name: requestedAccessOrganization.name,
                admin:
                    requestedAccessOrganization.admins[0].firstName +
                    ' ' +
                    requestedAccessOrganization.admins[0].lastName,
                status: 'Deleted',
            });
        });
    });
});

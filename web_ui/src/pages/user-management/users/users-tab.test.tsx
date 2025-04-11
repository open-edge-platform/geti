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

import { createInMemoryPlatformUtilsService } from '../../../core/platform-utils/services/create-in-memory-platform-utils-service';
import { createInMemoryUsersService } from '../../../core/users/services/in-memory-users-service';
import { useIsSaasEnv } from '../../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { applicationRender as render } from '../../../test-utils/application-provider-render';
import { getMockedProductInfo } from '../../../test-utils/mocked-items-factory/mocked-product-info';
import {
    getMockedContributorUser,
    getMockedOrganizationAdminUser,
} from '../../../test-utils/mocked-items-factory/mocked-users';
import { UsersTab } from './users-tab.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace-id',
    }),
}));

jest.mock('../../../hooks/use-is-saas-env/use-is-saas-env.hook', () => ({
    ...jest.requireActual('../../../hooks/use-is-saas-env/use-is-saas-env.hook'),
    useIsSaasEnv: jest.fn(() => false),
}));

describe('UsersTab', () => {
    const adminUser = getMockedOrganizationAdminUser();
    const contributorUser = getMockedContributorUser();

    describe('On-prem', () => {
        describe('Admin user', () => {
            afterEach(() => {
                jest.clearAllMocks();
            });

            const usersService = createInMemoryUsersService();
            usersService.getActiveUser = async () => Promise.resolve(adminUser);

            it('should display "Add user" button when server smtp is not installed', async () => {
                const platformUtilsService = createInMemoryPlatformUtilsService();
                platformUtilsService.getProductInfo = async () =>
                    Promise.resolve(getMockedProductInfo({ isSmtpDefined: false }));

                await render(<UsersTab activeUser={adminUser} />, {
                    services: { platformUtilsService, usersService },
                });

                expect(await screen.findByRole('button', { name: 'Add user' })).toBeInTheDocument();
                expect(screen.queryByRole('button', { name: 'Send invite' })).not.toBeInTheDocument();
            });

            it('should display "Send invite" button when server smtp is installed', async () => {
                const platformUtilsService = createInMemoryPlatformUtilsService();
                platformUtilsService.getProductInfo = async () =>
                    Promise.resolve(getMockedProductInfo({ isSmtpDefined: true }));

                await render(<UsersTab activeUser={adminUser} />, {
                    services: { platformUtilsService, usersService },
                });

                expect(await screen.findByRole('button', { name: 'Send invite' })).toBeInTheDocument();
                expect(screen.queryByRole('button', { name: 'Add user' })).not.toBeInTheDocument();
            });
        });

        describe('Contributor user', () => {
            const usersService = createInMemoryUsersService();
            usersService.getActiveUser = async () => Promise.resolve(contributorUser);

            it('should NOT display "Add user" button when server smtp is not installed', async () => {
                const platformUtilsService = createInMemoryPlatformUtilsService();
                platformUtilsService.getProductInfo = async () =>
                    Promise.resolve(getMockedProductInfo({ isSmtpDefined: false }));

                await render(<UsersTab activeUser={contributorUser} />, {
                    services: { platformUtilsService, usersService },
                });

                expect(screen.queryByRole('button', { name: 'Add user' })).not.toBeInTheDocument();
                expect(screen.queryByRole('button', { name: 'Send invite' })).not.toBeInTheDocument();
            });

            it('should NOT display "Send invite" button when server smtp is installed', async () => {
                const platformUtilsService = createInMemoryPlatformUtilsService();
                platformUtilsService.getProductInfo = async () =>
                    Promise.resolve(getMockedProductInfo({ isSmtpDefined: true }));

                await render(<UsersTab activeUser={contributorUser} />, {
                    services: { platformUtilsService, usersService },
                });

                expect(screen.queryByRole('button', { name: 'Send invite' })).not.toBeInTheDocument();
                expect(screen.queryByRole('button', { name: 'Add user' })).not.toBeInTheDocument();
            });
        });
    });

    describe('Sass', () => {
        beforeAll(() => {
            jest.mocked(useIsSaasEnv).mockImplementation(() => true);
        });

        describe('Admin user', () => {
            const usersService = createInMemoryUsersService();
            usersService.getActiveUser = async () => Promise.resolve(adminUser);

            it('should display "Send invite"', async () => {
                const platformUtilsService = createInMemoryPlatformUtilsService();
                platformUtilsService.getProductInfo = async () =>
                    Promise.resolve(getMockedProductInfo({ isSmtpDefined: false }));

                await render(<UsersTab activeUser={adminUser} />, {
                    services: { platformUtilsService, usersService },
                });

                expect(await screen.findByRole('button', { name: 'Send invite' })).toBeInTheDocument();
                expect(screen.queryByRole('button', { name: 'Add user' })).not.toBeInTheDocument();
            });
        });

        describe('Contributor user', () => {
            const usersService = createInMemoryUsersService();
            usersService.getActiveUser = async () => Promise.resolve(contributorUser);

            it('should NOT display neither "Add user" nor "Send invite" buttons', async () => {
                const platformUtilsService = createInMemoryPlatformUtilsService();
                platformUtilsService.getProductInfo = async () =>
                    Promise.resolve(getMockedProductInfo({ isSmtpDefined: true }));

                await render(<UsersTab activeUser={contributorUser} />, {
                    services: { platformUtilsService, usersService },
                });

                expect(screen.queryByRole('button', { name: 'Add user' })).not.toBeInTheDocument();
                expect(screen.queryByRole('button', { name: 'Send invite' })).not.toBeInTheDocument();
            });
        });
    });
});

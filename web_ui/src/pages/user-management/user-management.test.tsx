// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { createInMemoryPlatformUtilsService } from '../../core/platform-utils/services/create-in-memory-platform-utils-service';
import { createInMemoryUsersService } from '../../core/users/services/in-memory-users-service';
import { RESOURCE_TYPE, USER_ROLE } from '../../core/users/users.interface';
import { useIsSaasEnv } from '../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { MediaUploadProvider } from '../../providers/media-upload-provider/media-upload-provider.component';
import {
    getMockedAdminUser,
    getMockedOrganizationAdminUser,
    getMockedOrganizationContributorUser,
    getMockedUser,
} from '../../test-utils/mocked-items-factory/mocked-users';
import { providersRender as render } from '../../test-utils/required-providers-render';
import { UserManagement, UserManagementTabs } from './user-management.component';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: 'organization-id',
        workspaceId: 'workspace-id',
    }),
}));

jest.mock('../../hooks/use-history-block/use-history-block.hook', () => ({
    useHistoryBlock: () => {
        return [false, jest.fn(), jest.fn()];
    },
}));

jest.mock('../../hooks/use-is-saas-env/use-is-saas-env.hook', () => ({
    ...jest.requireActual('../../hooks/use-is-saas-env/use-is-saas-env.hook'),
    useIsSaasEnv: jest.fn(() => false),
}));

describe('UserManagement', () => {
    const renderPage = async (options?: Parameters<typeof render>[1]) => {
        render(
            <MediaUploadProvider>
                <UserManagement />
            </MediaUploadProvider>,
            options
        );

        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    describe('On-prem', () => {
        beforeAll(() => {
            jest.mocked(useIsSaasEnv).mockReturnValue(false);
        });

        it('user management tabs should be visible', async () => {
            const usersService = createInMemoryUsersService();
            const platformUtilsService = createInMemoryPlatformUtilsService();

            usersService.getActiveUser = async () => Promise.resolve(getMockedOrganizationAdminUser());

            await renderPage({
                services: {
                    usersService,
                    platformUtilsService,
                },
                featureFlags: {
                    FEATURE_FLAG_STORAGE_SIZE_COMPUTATION: true,
                    FEATURE_FLAG_CREDIT_SYSTEM: false,
                },
            });

            expect(
                await screen.findByRole('tab', { name: new RegExp(UserManagementTabs.ANALYTICS, 'i') })
            ).toBeInTheDocument();

            expect(screen.getByRole('tab', { name: new RegExp(UserManagementTabs.USERS, 'i') })).toBeInTheDocument();
            expect(screen.getByRole('tab', { name: new RegExp(UserManagementTabs.PROFILE, 'i') })).toBeInTheDocument();
            expect(screen.queryByRole('tab', { name: /token/i })).toBeInTheDocument();
            expect(screen.getByRole('tab', { name: new RegExp(UserManagementTabs.STORAGE, 'i') })).toBeInTheDocument();
            expect(screen.getByRole('tab', { name: new RegExp(UserManagementTabs.SECURITY, 'i') })).toBeInTheDocument();
            expect(
                screen.queryByRole('tab', { name: new RegExp(UserManagementTabs.USAGE, 'i') })
            ).not.toBeInTheDocument();
        });

        it('Token tab should be shown', async () => {
            await renderPage();

            expect(screen.queryByRole('tab', { name: /token/i })).toBeInTheDocument();
        });

        it(`analytics and usage tabs should be visible for organization admin`, async () => {
            const usersService = createInMemoryUsersService();
            usersService.getActiveUser = async () => Promise.resolve(getMockedOrganizationAdminUser());

            await renderPage({
                services: { usersService },
                featureFlags: {
                    FEATURE_FLAG_CREDIT_SYSTEM: true,
                },
            });

            await screen.findByRole('tab', { name: new RegExp(UserManagementTabs.ANALYTICS, 'i') });
            screen.getByRole('tab', { name: new RegExp(UserManagementTabs.USAGE, 'i') });
        });

        it(`analytics should be visible for workspace admin`, async () => {
            const usersService = createInMemoryUsersService();
            usersService.getActiveUser = async () => Promise.resolve(getMockedAdminUser({}, 'workspace-id'));

            await renderPage({
                services: { usersService },
                featureFlags: {
                    FEATURE_FLAG_CREDIT_SYSTEM: true,
                },
            });

            await screen.findByRole('tab', { name: new RegExp(UserManagementTabs.ANALYTICS, 'i') });
        });

        it(`usage tabs should be visible for workspace admin -> ONLY FOR DEVELOPER PURPOSES, ON ON-PREM FEATURE_FLAG_CREDIT_SYSTEM SHOULD BE ALWAYS DISABLED`, async () => {
            const usersService = createInMemoryUsersService();
            usersService.getActiveUser = async () => Promise.resolve(getMockedAdminUser({}, 'workspace-id'));

            await renderPage({
                services: { usersService },
                featureFlags: {
                    FEATURE_FLAG_CREDIT_SYSTEM: true,
                },
            });

            await screen.findByRole('tab', { name: new RegExp(UserManagementTabs.USAGE, 'i') });
        });

        it('analytics tab should NOT be visible for an organization contributor', async () => {
            const usersService = createInMemoryUsersService();
            usersService.getActiveUser = async () => Promise.resolve(getMockedOrganizationContributorUser());

            await renderPage({
                services: {
                    usersService,
                },
                featureFlags: {
                    FEATURE_FLAG_CREDIT_SYSTEM: true,
                },
            });

            expect(
                screen.queryByRole('tab', { name: new RegExp(UserManagementTabs.ANALYTICS, 'i') })
            ).not.toBeInTheDocument();
        });

        it('analytics tab should NOT be visible for workspace contributor', async () => {
            const usersService = createInMemoryUsersService();
            usersService.getActiveUser = async () =>
                Promise.resolve(
                    getMockedUser({
                        roles: [
                            {
                                role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
                                resourceId: 'workspace_1',
                                resourceType: RESOURCE_TYPE.WORKSPACE,
                            },
                        ],
                    })
                );

            await renderPage({
                services: {
                    usersService,
                },
                featureFlags: {
                    FEATURE_FLAG_CREDIT_SYSTEM: true,
                },
            });

            expect(
                screen.queryByRole('tab', { name: new RegExp(UserManagementTabs.ANALYTICS, 'i') })
            ).not.toBeInTheDocument();
        });

        it('usage tab should NOT be visible for an organization contributor', async () => {
            const usersService = createInMemoryUsersService();
            usersService.getActiveUser = async () => Promise.resolve(getMockedOrganizationContributorUser());

            await renderPage({
                services: {
                    usersService,
                },
                featureFlags: {
                    FEATURE_FLAG_CREDIT_SYSTEM: true,
                },
            });

            expect(
                screen.queryByRole('tab', { name: new RegExp(UserManagementTabs.USAGE, 'i') })
            ).not.toBeInTheDocument();
        });

        it('usage tab should NOT be visible for workspace contributor', async () => {
            const usersService = createInMemoryUsersService();
            usersService.getActiveUser = async () =>
                Promise.resolve(
                    getMockedUser({
                        roles: [
                            {
                                role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
                                resourceId: 'workspace_1',
                                resourceType: RESOURCE_TYPE.WORKSPACE,
                            },
                        ],
                    })
                );

            await renderPage({
                services: {
                    usersService,
                },
                featureFlags: {
                    FEATURE_FLAG_CREDIT_SYSTEM: true,
                },
            });

            expect(
                screen.queryByRole('tab', { name: new RegExp(UserManagementTabs.USAGE, 'i') })
            ).not.toBeInTheDocument();
        });
    });

    describe('Sass', () => {
        beforeAll(() => {
            jest.mocked(useIsSaasEnv).mockReturnValue(true);
        });

        it('user management tabs should be visible', async () => {
            const usersService = createInMemoryUsersService();
            const platformUtilsService = createInMemoryPlatformUtilsService();

            usersService.getActiveUser = async () =>
                Promise.resolve(
                    getMockedUser({
                        organizationId: 'organization-id',
                        roles: [
                            {
                                resourceId: 'organization-id',
                                role: USER_ROLE.ORGANIZATION_ADMIN,
                                resourceType: RESOURCE_TYPE.ORGANIZATION,
                            },
                        ],
                    })
                );

            await renderPage({
                services: {
                    usersService,
                    platformUtilsService,
                },
                featureFlags: {
                    FEATURE_FLAG_WORKSPACE_ACTIONS: true,
                    FEATURE_FLAG_CREDIT_SYSTEM: true,
                },
            });

            expect(screen.queryByRole('tab', { name: new RegExp(UserManagementTabs.USERS, 'i') })).toBeInTheDocument();
            expect(screen.getByRole('tab', { name: new RegExp(UserManagementTabs.PROFILE, 'i') })).toBeInTheDocument();
            expect(
                screen.getByRole('tab', { name: new RegExp(UserManagementTabs.WORKSPACES, 'i') })
            ).toBeInTheDocument();
            expect(
                screen.queryByRole('tab', { name: new RegExp(UserManagementTabs.SECURITY, 'i') })
            ).toBeInTheDocument();

            expect(
                screen.queryByRole('tab', { name: new RegExp(UserManagementTabs.ANALYTICS, 'i') })
            ).not.toBeInTheDocument();
            expect(
                screen.queryByRole('tab', { name: new RegExp(UserManagementTabs.STORAGE, 'i') })
            ).not.toBeInTheDocument();
            expect(
                screen.queryByRole('tab', { name: new RegExp(UserManagementTabs.PERSONAL_ACCESS_TOKEN, 'i') })
            ).toBeNull();
            expect(screen.queryByRole('tab', { name: new RegExp(UserManagementTabs.USAGE, 'i') })).toBeInTheDocument();
        });

        it('analytics tab should not be shown', async () => {
            const usersService = createInMemoryUsersService();

            usersService.getActiveUser = async () => Promise.resolve(getMockedOrganizationAdminUser());

            await renderPage({
                services: {
                    usersService,
                },
            });

            expect(
                screen.queryByRole('tab', { name: new RegExp(UserManagementTabs.ANALYTICS, 'i') })
            ).not.toBeInTheDocument();
        });

        it('usage tab shouldn not be shown if FEATURE_FLAG_CREDIT_SYSTEM is OFF', async () => {
            const usersService = createInMemoryUsersService();

            usersService.getActiveUser = async () => Promise.resolve(getMockedOrganizationAdminUser());

            await renderPage({
                services: {
                    usersService,
                },
                featureFlags: {
                    FEATURE_FLAG_CREDIT_SYSTEM: false,
                },
            });

            expect(
                screen.queryByRole('tab', { name: new RegExp(UserManagementTabs.USAGE, 'i') })
            ).not.toBeInTheDocument();
        });

        it('usage tab should not be shown if user is an organization contributor', async () => {
            const usersService = createInMemoryUsersService();

            usersService.getActiveUser = async () => Promise.resolve(getMockedOrganizationContributorUser());

            await renderPage({
                services: {
                    usersService,
                },
                featureFlags: {
                    FEATURE_FLAG_CREDIT_SYSTEM: true,
                },
            });

            expect(
                screen.queryByRole('tab', { name: new RegExp(UserManagementTabs.USAGE, 'i') })
            ).not.toBeInTheDocument();
        });

        it('usage tab should not be shown if user is a workspace contributor', async () => {
            const usersService = createInMemoryUsersService();

            usersService.getActiveUser = async () =>
                Promise.resolve(
                    getMockedUser({
                        roles: [
                            {
                                role: USER_ROLE.WORKSPACE_CONTRIBUTOR,
                                resourceId: 'workspace_1',
                                resourceType: RESOURCE_TYPE.WORKSPACE,
                            },
                        ],
                    })
                );

            await renderPage({
                services: {
                    usersService,
                },
                featureFlags: {
                    FEATURE_FLAG_CREDIT_SYSTEM: true,
                },
            });

            expect(
                screen.queryByRole('tab', { name: new RegExp(UserManagementTabs.USAGE, 'i') })
            ).not.toBeInTheDocument();
        });

        it('Token tab should be shown', async () => {
            await renderPage();

            expect(screen.getByRole('tab', { name: /token/i })).toBeInTheDocument();
        });

        it('Usage tab should be visible if FEATURE_FLAG_CREDIT_SYSTEM is ON and user is organization admin', async () => {
            const usersService = createInMemoryUsersService();
            usersService.getActiveUser = async () => Promise.resolve(getMockedOrganizationAdminUser());

            await renderPage({
                services: { usersService },
                featureFlags: {
                    FEATURE_FLAG_CREDIT_SYSTEM: true,
                },
            });

            expect(
                await screen.findByRole('tab', { name: new RegExp(UserManagementTabs.USAGE, 'i') })
            ).toBeInTheDocument();
        });

        it('Usage tab should be visible if FEATURE_FLAG_CREDIT_SYSTEM is ON and user is workspace admin', async () => {
            const usersService = createInMemoryUsersService();
            usersService.getActiveUser = async () => Promise.resolve(getMockedAdminUser({}, 'workspace-id'));

            await renderPage({
                services: { usersService },
                featureFlags: {
                    FEATURE_FLAG_CREDIT_SYSTEM: true,
                },
            });

            expect(
                await screen.findByRole('tab', { name: new RegExp(UserManagementTabs.USAGE, 'i') })
            ).toBeInTheDocument();
        });
    });
});

// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ApplicationServicesContextProps } from '@geti/core/src/services/application-services-provider.component';
import { fireEvent, screen, waitFor } from '@testing-library/react';

import { useProducts } from '../../../core/credits/products/hooks/use-products.hook';
import { GLOBAL_MODALS_KEYS } from '../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../core/user-settings/hooks/use-global-settings.hook';
import { createInMemoryUsersService } from '../../../core/users/services/in-memory-users-service';
import { RESOURCE_TYPE, USER_ROLE } from '../../../core/users/users.interface';
import { getMockedPolicy } from '../../../test-utils/mocked-items-factory/mocked-product';
import { getMockedUser } from '../../../test-utils/mocked-items-factory/mocked-users';
import { providersRender as render } from '../../../test-utils/required-providers-render';
import { WelcomeTrialModal } from './welcome-trial-modal.component';

jest.mock('../../../core/credits/products/hooks/use-products.hook', () => ({
    ...jest.requireActual('../../../core/credits/products/hooks/use-products.hook'),
    useProducts: jest.fn(() => ({
        useGetProductQuery: jest.fn(() => ({ data: undefined, isSuccess: true })),
    })),
}));

jest.mock('../../../core/user-settings/hooks/use-global-settings.hook', () => ({
    ...jest.requireActual('../../../core/user-settings/hooks/use-global-settings.hook'),
    useUserGlobalSettings: jest.fn(),
}));

jest.mock('../../../hooks/use-organization-identifier/use-organization-identifier.hook', () => ({
    ...jest.requireActual('../../../hooks/use-organization-identifier/use-organization-identifier.hook'),
    useOrganizationIdentifier: jest.fn(() => ({
        organizationId: 'organization-id',
    })),
}));

describe('WelcomeTrialModal', () => {
    const renderApp = ({
        mockedSaveConfig = jest.fn(),
        isModalEnabled = false,
        isCreditSystemFlagOn = true,
        services,
    }: {
        mockedSaveConfig?: jest.Mock;
        isModalEnabled?: boolean;
        isCreditSystemFlagOn?: boolean;
        services?: Partial<ApplicationServicesContextProps>;
    }) => {
        jest.mocked(useUserGlobalSettings).mockReturnValue({
            saveConfig: mockedSaveConfig,
            isSavingConfig: false,
            config: {
                [GLOBAL_MODALS_KEYS.WELCOME_MODAL]: { isEnabled: isModalEnabled },
                [GLOBAL_MODALS_KEYS.EXHAUSTED_ORGANIZATION_CREDITS_MODAL]: { isEnabled: false },
                [GLOBAL_MODALS_KEYS.LOW_ORGANIZATION_CREDITS_MODAL]: { isEnabled: false },
            },
        });

        render(<WelcomeTrialModal />, { featureFlags: { FEATURE_FLAG_CREDIT_SYSTEM: isCreditSystemFlagOn }, services });
    };

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('closed modal', () => {
        renderApp({ isModalEnabled: false });

        expect(screen.queryByRole('button', { name: /Start exploration now/i })).not.toBeInTheDocument();
    });

    it('open/close modal', async () => {
        const mockedSaveConfig = jest.fn();

        renderApp({ mockedSaveConfig, isModalEnabled: true });

        await waitFor(() => {
            expect(screen.getByRole('button', { name: /Start exploring now/i })).toBeVisible();
        });

        fireEvent.click(screen.getByRole('button', { name: /Start exploring now/i }));

        expect(mockedSaveConfig).toHaveBeenCalledWith({
            [GLOBAL_MODALS_KEYS.WELCOME_MODAL]: { isEnabled: false },
            [GLOBAL_MODALS_KEYS.EXHAUSTED_ORGANIZATION_CREDITS_MODAL]: { isEnabled: false },
            [GLOBAL_MODALS_KEYS.LOW_ORGANIZATION_CREDITS_MODAL]: { isEnabled: false },
        });
    });

    it('should render welcoming credits if the user is the one that created the organization', async () => {
        const initAmount = 5000;
        const renewableAmount = 1000;

        jest.mocked(useProducts).mockReturnValue({
            useGetProductQuery: () => ({
                // @ts-expect-error We only care about 'data' here
                data: {
                    id: 123,
                    name: 'Free Tier STUB',
                    productPolicies: [
                        getMockedPolicy({ accountName: 'welcoming credits', initAmount, renewableAmount: 0 }),
                        getMockedPolicy({ accountName: 'freemium credits', initAmount: 0, renewableAmount }),
                    ],
                },
                isSuccess: true,
            }),
        });

        const mockedUsersService = createInMemoryUsersService();
        mockedUsersService.getUsers = jest.fn(async () =>
            Promise.resolve({
                users: [
                    getMockedUser({
                        roles: [
                            {
                                resourceId: 'organization-id',
                                role: USER_ROLE.ORGANIZATION_ADMIN,
                                resourceType: RESOURCE_TYPE.ORGANIZATION,
                            },
                        ],
                    }),
                ],
                totalCount: 1,
                totalMatchedCount: 1,
                nextPage: {
                    skip: 2,
                    limit: 10,
                },
            })
        );
        renderApp({
            isModalEnabled: true,
            services: { usersService: mockedUsersService },
        });

        await waitFor(() => {
            expect(screen.getByRole('button', { name: /Start exploring now/i })).toBeVisible();
        });

        expect(screen.getByTestId(`init-credits-${initAmount}-id`)).toBeInTheDocument();
        expect(screen.getByTestId(`renewable-credits-${renewableAmount}-id`)).toBeInTheDocument();
    });

    it('should not render welcoming credits if the user is NOT one that created the organization', async () => {
        const initAmount = 5000;
        const renewableAmount = 1000;

        jest.mocked(useProducts).mockReturnValue({
            useGetProductQuery: () => ({
                // @ts-expect-error We only care about 'data' here
                data: {
                    id: 123,
                    name: 'Free Tier STUB',
                    productPolicies: [
                        getMockedPolicy({ accountName: 'welcoming credits', initAmount, renewableAmount: 0 }),
                        getMockedPolicy({ accountName: 'freemium credits', initAmount: 0, renewableAmount }),
                    ],
                },
                isSuccess: true,
            }),
        });

        const mockedUsersService = createInMemoryUsersService();
        mockedUsersService.getUsers = jest.fn(async () =>
            Promise.resolve({
                users: [getMockedUser(), getMockedUser()],
                totalCount: 2,
                totalMatchedCount: 2,
                nextPage: {
                    skip: 2,
                    limit: 10,
                },
            })
        );
        renderApp({
            isModalEnabled: true,
            services: { usersService: mockedUsersService },
        });

        await waitFor(() => {
            expect(screen.getByRole('button', { name: /Start exploring now/i })).toBeVisible();
        });

        expect(screen.queryByTestId(`init-credits-${initAmount}-id`)).not.toBeInTheDocument();
        expect(screen.getByTestId(`renewable-credits-${renewableAmount}-id`)).toBeInTheDocument();
    });
});

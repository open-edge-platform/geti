// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useProfileQuery } from '@geti/core/src/users/hook/use-profile.hook';
import { createInMemoryOnboardingService } from '@geti/core/src/users/services/inmemory-onboarding-service';
import { OrganizationMetadata } from '@geti/core/src/users/services/onboarding-service.interface';
import { act, waitFor } from '@testing-library/react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import * as usehooks from 'usehooks-ts';

import { paths } from '../../../../packages/core/src/services/routes';
import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import { AccountStatus } from '../organizations.interface';
import { useSelectedOrganization } from './use-selected-organization.hook';

jest.mock('usehooks-ts');

const mockedLocation = { state: undefined, key: '', hash: '', search: '', pathname: '' };
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: jest.fn(() => ({})),
    useLocation: jest.fn(() => mockedLocation),
    useNavigate: jest.fn(() => jest.fn()),
}));

jest.mock('@geti/core/src/users/hook/use-profile.hook', () => ({ useProfileQuery: jest.fn() }));

jest.mock('../../user-settings/hooks/use-global-settings.hook', () => ({
    ...jest.requireActual('../../user-settings/hooks/use-global-settings.hook'),
    useUserGlobalSettings: jest.fn(),
}));

const mockedOrganization = {
    id: '111',
    name: 'organization name',
    userStatus: AccountStatus.ACTIVATED,
    status: AccountStatus.ACTIVATED,
    createdAt: '2024-09-11T09:13:57Z',
};

const mockedOrganizationUserInvited = {
    ...mockedOrganization,
    id: '222',
    userStatus: AccountStatus.INVITED,
    status: AccountStatus.INVITED,
};

const mockedSuspendedOrganization = {
    ...mockedOrganization,
    id: '333',
    status: AccountStatus.SUSPENDED,
};

const mockedDeletedOrganization = {
    ...mockedOrganization,
    id: '444',
    status: AccountStatus.DELETED,
};

const mockedRequestedOrganization = {
    ...mockedOrganization,
    id: '555',
    status: AccountStatus.REQUESTED_ACCESS,
};

const updateOrganizationQuery = (organizations: OrganizationMetadata[]) => {
    // @ts-expect-error We only use data
    jest.mocked(useProfileQuery).mockReturnValue({
        data: {
            organizations,
            hasAcceptedUserTermsAndConditions: true,
        },
        refetch: jest.fn(),
    });
};

const renderSelectedOrganizationHook = (onboardingService = createInMemoryOnboardingService()) => {
    return renderHookWithProviders(useSelectedOrganization, {
        providerProps: { onboardingService },
    });
};

describe('useSelectedOrganization', () => {
    const mockedOrganizationTwo = { ...mockedOrganization, id: '222' };

    function mockNavigate(location = { state: undefined, key: '', hash: '', search: '', pathname: '' }) {
        const mockedNavigate = jest.fn();
        jest.mocked(useLocation).mockReturnValue(location);
        jest.mocked(useNavigate).mockReturnValue(mockedNavigate);

        return mockedNavigate;
    }

    beforeEach(() => {
        jest.clearAllMocks();
        jest.mocked(usehooks.useLocalStorage).mockReturnValue([null, jest.fn(), jest.fn()]);
    });

    describe('single organization is selected by default', () => {
        const onboardingService = createInMemoryOnboardingService();
        onboardingService.onboardUser = jest.fn(() => Promise.resolve());

        it('if the organization ID is valid, the selectedOrganization is returned', async () => {
            const mockedNavigate = mockNavigate();
            jest.mocked(useParams).mockReturnValue({ organizationId: mockedOrganization.id });
            updateOrganizationQuery([mockedOrganization]);

            const { result } = renderSelectedOrganizationHook();

            expect(result.current.selectedOrganization).toEqual(mockedOrganization);

            expect(mockedNavigate).not.toHaveBeenCalled();
        });

        it('if the organization ID is invalid, it redirects to a valid organization', async () => {
            const mockedNavigate = mockNavigate();
            jest.mocked(useParams).mockReturnValue({ organizationId: '000' });
            updateOrganizationQuery([mockedOrganization]);

            renderSelectedOrganizationHook(onboardingService);

            await waitFor(() => {
                expect(mockedNavigate).toHaveBeenCalledWith(
                    paths.organization.index({ organizationId: mockedOrganization.id })
                );
            });

            expect(onboardingService.onboardUser).not.toHaveBeenCalled();
        });

        it('append a valid organization ID to the current URL while preserving backwards compatibility', async () => {
            const mockedPathname = '/test';
            const mockedNavigate = mockNavigate({ ...mockedLocation, pathname: mockedPathname });
            jest.mocked(useParams).mockReturnValue({ organizationId: undefined });
            updateOrganizationQuery([mockedOrganization]);

            renderSelectedOrganizationHook(onboardingService);

            await waitFor(() => {
                expect(mockedNavigate).toHaveBeenCalledWith(
                    `${paths.organization.index({ organizationId: mockedOrganization.id })}${mockedPathname}`
                );
            });

            expect(onboardingService.onboardUser).not.toHaveBeenCalled();
        });

        it('onboard users with the status "invited"', async () => {
            const mockedNavigate = mockNavigate();

            updateOrganizationQuery([mockedOrganizationUserInvited]);
            renderSelectedOrganizationHook(onboardingService);

            await waitFor(() => {
                expect(mockedNavigate).toHaveBeenNthCalledWith(
                    1,
                    paths.organization.index({ organizationId: mockedOrganizationUserInvited.id })
                );
            });

            expect(onboardingService.onboardUser).toHaveBeenNthCalledWith(
                1,
                expect.objectContaining({
                    organizationId: mockedOrganizationUserInvited.id,
                    userConsentIsGiven: true,
                })
            );
        });

        it('redirects to stored organization ID from settings', async () => {
            const mockedNavigate = mockNavigate();

            jest.mocked(usehooks.useLocalStorage).mockReturnValue([mockedOrganizationTwo.id, jest.fn(), jest.fn()]);

            updateOrganizationQuery([mockedOrganization, mockedOrganizationTwo]);
            renderSelectedOrganizationHook(onboardingService);

            await waitFor(() => {
                expect(mockedNavigate).toHaveBeenNthCalledWith(
                    1,
                    paths.organization.index({ organizationId: mockedOrganizationTwo.id })
                );
            });
        });

        it.each([
            ['deleted', mockedDeletedOrganization],
            ['invited', mockedOrganizationUserInvited],
            ['suspended', mockedSuspendedOrganization],
            ['requested access', mockedRequestedOrganization],
        ])('avoids redirection when the chosen organization has a status: %s', async (_, organization) => {
            const mockedNavigate = mockNavigate();
            updateOrganizationQuery([mockedOrganization, organization]);
            renderSelectedOrganizationHook(onboardingService);

            await waitFor(() => {
                expect(mockedNavigate).not.toHaveBeenCalled();
            });
        });
    });

    describe('multiple organizations', () => {
        it('if the organization ID is valid, the selectedOrganization is returned', async () => {
            const mockedNavigate = mockNavigate();
            jest.mocked(useParams).mockReturnValue({ organizationId: mockedOrganizationTwo.id });
            updateOrganizationQuery([mockedOrganization, mockedOrganizationTwo]);

            const { result } = renderSelectedOrganizationHook();

            expect(result.current.selectedOrganization).toEqual(mockedOrganizationTwo);
            expect(mockedNavigate).not.toHaveBeenCalled();
        });

        it('if the organization ID is invalid, the selectedOrganization returned null', async () => {
            const mockedNavigate = mockNavigate();
            jest.mocked(useParams).mockReturnValue({ organizationId: '000' });
            updateOrganizationQuery([mockedOrganization, mockedOrganizationTwo]);

            const { result } = renderSelectedOrganizationHook();

            expect(result.current.selectedOrganization).toEqual(null);
            expect(mockedNavigate).not.toHaveBeenCalled();
        });
    });

    describe('select new organization', () => {
        it('valid organization id', async () => {
            const mockedNavigate = mockNavigate();

            const mockedSaveConfig = jest.fn();
            jest.mocked(usehooks.useLocalStorage).mockReturnValue([null, mockedSaveConfig, jest.fn()]);
            jest.mocked(useParams).mockReturnValue({ organizationId: undefined });

            updateOrganizationQuery([mockedOrganization, mockedOrganizationTwo]);
            const { result } = renderSelectedOrganizationHook();
            expect(result.current.selectedOrganization).toEqual(null);

            act(() => {
                result.current.setSelectedOrganization(mockedOrganizationTwo.id);
            });

            expect(mockedNavigate).toHaveBeenCalledWith(
                paths.organization.index({ organizationId: mockedOrganizationTwo.id })
            );
            expect(mockedSaveConfig).toHaveBeenCalledWith(mockedOrganizationTwo.id);
        });

        it('invalid organization id', async () => {
            const mockedNavigate = mockNavigate();
            jest.mocked(useParams).mockReturnValue({ organizationId: undefined });
            updateOrganizationQuery([mockedOrganization, mockedOrganizationTwo]);
            const { result } = renderSelectedOrganizationHook();

            expect(result.current.selectedOrganization).toEqual(null);
            act(() => {
                result.current.setSelectedOrganization('0000');
            });

            expect(mockedNavigate).not.toHaveBeenCalled();
        });
    });
});

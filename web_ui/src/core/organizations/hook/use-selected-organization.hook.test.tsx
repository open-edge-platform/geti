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

import { act, waitFor } from '@testing-library/react';
import { useLocation, useParams } from 'react-router-dom';

import { renderHookWithProviders } from '../../../test-utils/render-hook-with-providers';
import { paths } from '../../services/routes';
import { useProfileQuery } from '../../users/hook/use-profile.hook';
import { createInMemoryOnboardingService } from '../../users/services/inmemory-onboarding-service';
import { OrganizationMetadata } from '../../users/services/onboarding-service.interface';
import { AccountStatus } from '../organizations.interface';
import { useSelectedOrganization } from './use-selected-organization.hook';

const mockedLocation = { state: undefined, key: '', hash: '', search: '', pathname: '' };
const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: jest.fn(() => ({})),
    useLocation: jest.fn(() => mockedLocation),
    useNavigate: jest.fn(() => mockedNavigate),
}));

jest.mock('../../users/hook/use-profile.hook', () => ({ useProfileQuery: jest.fn() }));

const mockedOrganization = {
    id: '111',
    name: 'organization name',
    userStatus: AccountStatus.ACTIVATED,
    status: AccountStatus.ACTIVATED,
    createdAt: '2024-09-11T09:13:57Z',
};

const mockedOrganizationUserInvited = {
    ...mockedOrganization,
    userStatus: AccountStatus.INVITED,
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

    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('single organization is selected by default', () => {
        const onboardingService = createInMemoryOnboardingService();
        onboardingService.onboardUser = jest.fn(() => Promise.resolve());

        it('if the organization ID is valid, the selectedOrganization is returned', async () => {
            jest.mocked(useParams).mockReturnValue({ organizationId: mockedOrganization.id });
            updateOrganizationQuery([mockedOrganization]);

            const { result } = renderSelectedOrganizationHook();

            expect(result.current.selectedOrganization).toEqual(mockedOrganization);

            expect(mockedNavigate).not.toHaveBeenCalled();
        });

        it('if the organization ID is invalid, it redirects to a valid organization', async () => {
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
            jest.mocked(useLocation).mockReturnValueOnce({ ...mockedLocation, pathname: mockedPathname });
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
            updateOrganizationQuery([mockedOrganizationUserInvited]);
            renderSelectedOrganizationHook(onboardingService);

            await waitFor(() => {
                expect(mockedNavigate).toHaveBeenNthCalledWith(
                    1,
                    paths.organization.index({ organizationId: mockedOrganization.id })
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
    });

    describe('multiple organizations', () => {
        it('if the organization ID is valid, the selectedOrganization is returned', async () => {
            jest.mocked(useParams).mockReturnValue({ organizationId: mockedOrganizationTwo.id });
            updateOrganizationQuery([mockedOrganization, mockedOrganizationTwo]);

            const { result } = renderSelectedOrganizationHook();

            expect(result.current.selectedOrganization).toEqual(mockedOrganizationTwo);
            expect(mockedNavigate).not.toHaveBeenCalled();
        });

        it('if the organization ID is invalid, the selectedOrganization returned null', async () => {
            jest.mocked(useParams).mockReturnValue({ organizationId: '000' });
            updateOrganizationQuery([mockedOrganization, mockedOrganizationTwo]);

            const { result } = renderSelectedOrganizationHook();

            expect(result.current.selectedOrganization).toEqual(null);
            expect(mockedNavigate).not.toHaveBeenCalled();
        });
    });

    describe('select new organization', () => {
        it('valid organization id', async () => {
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
        });

        it('invalid organization id', async () => {
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

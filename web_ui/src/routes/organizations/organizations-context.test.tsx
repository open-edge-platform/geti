// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createInMemoryOnboardingService } from '@geti/core/src/users/services/inmemory-onboarding-service';
import {
    OnboardingProfile,
    OnboardingService,
    OrganizationMetadata,
} from '@geti/core/src/users/services/onboarding-service.interface';
import { screen, waitForElementToBeRemoved } from '@testing-library/react';
import { AxiosError, HttpStatusCode } from 'axios';

import { AccountStatus } from '../../core/organizations/organizations.interface';
import { ErrorBoundary } from '../../pages/errors/error-boundary.component';
import { InvalidOrganizationsScreen } from '../../pages/errors/invalid-organization/invalid-organization-screen.component';
import { providersRender as render } from '../../test-utils/required-providers-render';
import { OrganizationsContext } from './organizations-context.component';

const mockedSuspendedOrganizationId = '0000';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
        organizationId: mockedSuspendedOrganizationId,
    }),
}));

const mockedOrganization = {
    id: '1111',
    name: 'active organization-name',
    status: AccountStatus.ACTIVATED,
    userStatus: AccountStatus.ACTIVATED,
    createdAt: '2024-09-11T09:17:42Z',
};

const mockedOrganizationTwo = {
    id: '2222',
    name: 'active organization-name',
    status: AccountStatus.ACTIVATED,
    userStatus: AccountStatus.ACTIVATED,
    createdAt: '2024-09-11T09:17:42Z',
};

const suspendedOrganization = {
    ...mockedOrganization,
    id: mockedSuspendedOrganizationId,
    name: 'suspended organization-name',
    status: AccountStatus.SUSPENDED,
    userStatus: AccountStatus.SUSPENDED,
};

const renderApp = async ({
    profile = null,
    onboardingService,
}: {
    profile?: OnboardingProfile | null;
    isError?: boolean;
    onboardingService?: OnboardingService;
    organizations?: OrganizationMetadata[];
    selectedOrganization?: OrganizationMetadata | null;
}) => {
    render(
        <ErrorBoundary FallbackComponent={() => <InvalidOrganizationsScreen />}>
            <OrganizationsContext>
                <div>App</div>
            </OrganizationsContext>
        </ErrorBoundary>,
        { profile, services: { onboardingService } }
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));
};

describe('Organizations context', () => {
    it('Displays <SuspendedOrganization /> if the organization has been suspended or deleted.', async () => {
        const onboardingService = createInMemoryOnboardingService();
        onboardingService.getActiveUserProfile = jest.fn(() =>
            Promise.resolve({
                organizations: [suspendedOrganization],
                hasAcceptedUserTermsAndConditions: true,
            })
        );

        await renderApp({
            onboardingService,
        });

        expect(screen.getByText(/Your organization's account has been suspended/)).toBeVisible();
    });

    it('Shows <InvalidOrganizationsScreen /> if there was an error loading the profile.', async () => {
        const onboardingService = createInMemoryOnboardingService();
        onboardingService.getActiveUserProfile = jest.fn(() =>
            Promise.reject(
                // @ts-expect-error We mock only necessary things from AxiosError
                new AxiosError(undefined, undefined, undefined, undefined, {
                    status: HttpStatusCode.Unauthorized,
                    request: {
                        responseURL: 'http://localhost:3000/api/v1/user/profile',
                    },
                })
            )
        );

        await renderApp({
            onboardingService,
        });

        expect(screen.getByText(/You do not have access to any Intel Geti organization/)).toBeVisible();
    });

    describe('multiple organizations', () => {
        it('Displays the "OrganizationSelectionModal" when no organization has been selected', async () => {
            const onboardingService = createInMemoryOnboardingService();
            onboardingService.getActiveUserProfile = jest.fn(() =>
                Promise.resolve({
                    organizations: [mockedOrganization, mockedOrganizationTwo],
                    hasAcceptedUserTermsAndConditions: true,
                })
            );
            await renderApp({
                onboardingService,
            });

            expect(screen.getByText(/^You belong to the following organizations./i)).toBeVisible();

            expect(screen.getByRole('button', { name: `select organization ${mockedOrganization.id}` })).toBeVisible();
            expect(
                screen.getByRole('button', { name: `select organization ${mockedOrganizationTwo.id}` })
            ).toBeVisible();
        });

        it('Displays <OrganizationSelectionModal /> if the organization has been suspended.', async () => {
            const onboardingService = createInMemoryOnboardingService();
            onboardingService.getActiveUserProfile = jest.fn(() =>
                Promise.resolve({
                    organizations: [suspendedOrganization, mockedOrganization],
                    hasAcceptedUserTermsAndConditions: true,
                })
            );

            await renderApp({
                onboardingService,
            });

            expect(
                screen.getByText(
                    `You no longer have access to ${suspendedOrganization.name}. Please select the organization you wish to access now.`
                )
            ).toBeVisible();

            expect(
                screen.queryByRole('button', { name: `select organization ${suspendedOrganization.id}` })
            ).not.toBeInTheDocument();

            expect(screen.getByRole('button', { name: `select organization ${mockedOrganization.id}` })).toBeVisible();
        });
    });
});

// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { useSelectedOrganization } from '../../../../core/organizations/hook/use-selected-organization.hook';
import { AccountStatus } from '../../../../core/organizations/organizations.interface';
import { createInMemoryOnboardingService } from '../../../../core/users/services/inmemory-onboarding-service';
import { OrganizationMetadata } from '../../../../core/users/services/onboarding-service.interface';
import { ThemeProvider } from '../../../../providers/theme-provider/theme-provider.component';
import { providersRender } from '../../../../test-utils/required-providers-render';
import { OrganizationsPicker } from './organizations-picker.component';

jest.mock('../../../../core/organizations/hook/use-selected-organization.hook', () => ({
    useSelectedOrganization: jest.fn(),
}));

const mockedOrganization = {
    id: '111',
    name: 'test org name 1',
    userStatus: AccountStatus.ACTIVATED,
    status: AccountStatus.ACTIVATED,
    createdAt: '2024-09-11T09:13:57Z',
};

const mockedInvitedOrganization = {
    ...mockedOrganization,
    id: '333',
    name: 'test invited org',
    status: AccountStatus.ACTIVATED,
    userStatus: AccountStatus.INVITED,
};

const mockedOrganizationTwo = { ...mockedOrganization, id: '222', name: 'test org name 2' };

const renderApp = ({
    isLargeSize = true,
    organizations,
    selectedOrganization = null,
    mockedOnboardUser = jest.fn(() => Promise.resolve()),
    mockedSetSelectedOrganization = jest.fn(),
}: {
    isLargeSize?: boolean;
    organizations: OrganizationMetadata[];
    selectedOrganization?: OrganizationMetadata | null;
    mockedOnboardUser?: jest.Mock;
    mockedSetSelectedOrganization?: () => void;
}) => {
    const onboardingService = createInMemoryOnboardingService();
    onboardingService.onboardUser = mockedOnboardUser;

    // @ts-expect-error We only use data
    jest.mocked(useSelectedOrganization).mockReturnValue({
        organizations,
        selectedOrganization,
        hasMultipleOrganizations: organizations.length > 1,
        setSelectedOrganization: mockedSetSelectedOrganization,
    });

    return providersRender(
        <ThemeProvider>
            <OrganizationsPicker isLargeSize={isLargeSize} />
        </ThemeProvider>,
        { services: { onboardingService } }
    );
};
describe('OrganizationsPicker', () => {
    it('do not render the component if there is only one organization', async () => {
        renderApp({
            isLargeSize: false,
            organizations: [mockedOrganization],
            selectedOrganization: mockedOrganization,
        });

        expect(screen.queryByRole('button', { name: /organizations selection/i })).not.toBeInTheDocument();
    });

    describe('render a popover-listBox for small size', () => {
        it('multiple organizations', async () => {
            const mockedSetSelectedOrganization = jest.fn();
            const organizations = [mockedOrganization, mockedOrganizationTwo];

            renderApp({
                isLargeSize: false,
                organizations,
                selectedOrganization: mockedOrganization,
                mockedSetSelectedOrganization,
            });

            await userEvent.click(screen.getByRole('button', { name: /organizations selection/i }));

            await waitFor(() => {
                expect(screen.getByRole('listbox')).toBeVisible();
            });

            organizations.forEach(({ name }) => {
                expect(screen.getByRole('option', { name })).toBeVisible();
            });

            await userEvent.selectOptions(
                screen.getByRole('listbox'),
                screen.getByRole('option', { name: mockedOrganizationTwo.name })
            );

            await waitFor(() => {
                expect(mockedSetSelectedOrganization).toHaveBeenCalledWith(mockedOrganizationTwo.id);
            });
        });
    });

    describe('large size', () => {
        it('render a picker for multiple active organizations', async () => {
            const mockedSetSelectedOrganization = jest.fn();
            const organizations = [mockedOrganization, mockedOrganizationTwo];
            const mockedOnboardUser = jest.fn(() => Promise.resolve());

            renderApp({
                organizations,
                mockedOnboardUser,
                selectedOrganization: mockedOrganization,
                mockedSetSelectedOrganization,
            });

            fireEvent.click(screen.getByRole('button', { name: `${mockedOrganization.name} organizations selection` }));

            organizations.forEach(({ name }) => {
                expect(screen.getByRole('option', { name })).toBeVisible();
            });

            await userEvent.selectOptions(
                screen.getByRole('listbox'),
                screen.getByRole('option', { name: mockedOrganizationTwo.name })
            );

            expect(mockedSetSelectedOrganization).toHaveBeenCalledWith(mockedOrganizationTwo.id);
            expect(mockedOnboardUser).not.toHaveBeenCalled();
        });

        it('onboard and choose the invited organization', async () => {
            const mockedSetSelectedOrganization = jest.fn();
            const organizations = [mockedOrganization, mockedInvitedOrganization];
            const mockedOnboardUser = jest.fn(() => Promise.resolve());

            renderApp({
                organizations,
                mockedOnboardUser,
                selectedOrganization: mockedOrganization,
                mockedSetSelectedOrganization,
            });

            fireEvent.click(screen.getByRole('button', { name: `${mockedOrganization.name} organizations selection` }));

            await userEvent.selectOptions(
                screen.getByRole('listbox'),
                screen.getByRole('option', { name: mockedInvitedOrganization.name })
            );

            expect(mockedSetSelectedOrganization).toHaveBeenCalledWith(mockedInvitedOrganization.id);
            expect(mockedOnboardUser).toHaveBeenCalledWith(
                expect.objectContaining({
                    organizationId: mockedInvitedOrganization.id,
                    userConsentIsGiven: true,
                })
            );
        });
    });
});

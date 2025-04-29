// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { AccountStatus } from '../../core/organizations/organizations.interface';
import { createInMemoryOnboardingService } from '../../core/users/services/inmemory-onboarding-service';
import { OnboardingService, OrganizationMetadata } from '../../core/users/services/onboarding-service.interface';
import { providersRender as render } from '../../test-utils/required-providers-render';
import { OrganizationSelectionModal } from './organization-selection-modal.component';

const mockedTitle = 'test test';
const mockedOrganizationOne = {
    id: '111',
    name: 'test-name 1',
    createdAt: '2024-09-11T09:13:57Z',
    status: AccountStatus.ACTIVATED,
    userStatus: AccountStatus.ACTIVATED,
};

const mockedOrganizationTwo = {
    ...mockedOrganizationOne,
    id: '222',
    name: 'test-name 2',
};

const mockedInvitedOrganization = {
    ...mockedOrganizationOne,
    id: '333',
    name: 'test-name 2',
    status: AccountStatus.INVITED,
    userStatus: AccountStatus.INVITED,
};

const mockedActiveOrganizationInvitedUser = { ...mockedOrganizationOne, userStatus: AccountStatus.INVITED };

describe('OrganizationSelectionModal', () => {
    const renderApp = ({
        onboardingService = createInMemoryOnboardingService(),
        ...props
    }: {
        title: string;
        organizations: OrganizationMetadata[];
        onSelectedOrganization: (id: string) => void;
        onboardingService?: OnboardingService;
    }) => {
        render(<OrganizationSelectionModal {...props} description={'description test'} />, {
            services: { onboardingService },
        });
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('render title and organizations', async () => {
        const organizations = [mockedOrganizationOne, mockedOrganizationTwo];

        renderApp({
            title: mockedTitle,
            organizations,
            onSelectedOrganization: jest.fn(),
        });

        expect(screen.getByText(mockedTitle)).toBeVisible();

        organizations.forEach(({ id, name }) => {
            expect(screen.getByText(name)).toBeVisible();
            expect(screen.getByRole('button', { name: `select organization ${id}` })).toBeVisible();
        });
    });

    it('organization selection close the modal', async () => {
        const mockedOnSelectedOrganization = jest.fn();
        const onboardingService = createInMemoryOnboardingService();
        onboardingService.onboardUser = jest.fn(() => Promise.resolve());

        renderApp({
            title: mockedTitle,
            onboardingService,
            organizations: [mockedOrganizationOne],
            onSelectedOrganization: mockedOnSelectedOrganization,
        });

        expect(screen.getByText(mockedTitle)).toBeVisible();
        fireEvent.click(screen.getByRole('button', { name: `select organization ${mockedOrganizationOne.id}` }));

        await waitForElementToBeRemoved(() => screen.getByText(mockedTitle));

        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        expect(onboardingService.onboardUser).not.toHaveBeenCalled();
        expect(mockedOnSelectedOrganization).toHaveBeenCalledWith(mockedOrganizationOne.id);
    });

    it('onboard "invited" organization', async () => {
        const onboardingService = createInMemoryOnboardingService();
        onboardingService.onboardUser = jest.fn(() => Promise.resolve());

        const mockedOnSelectedOrganization = jest.fn();
        renderApp({
            title: mockedTitle,
            onboardingService,
            organizations: [mockedInvitedOrganization],
            onSelectedOrganization: mockedOnSelectedOrganization,
        });

        expect(screen.getByText(mockedTitle)).toBeVisible();
        fireEvent.click(screen.getByRole('button', { name: `select organization ${mockedInvitedOrganization.id}` }));

        await waitForElementToBeRemoved(() => screen.getByText(mockedTitle));

        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        expect(onboardingService.onboardUser).toHaveBeenCalled();
        expect(mockedOnSelectedOrganization).toHaveBeenCalledWith(mockedInvitedOrganization.id);
    });

    it('Onboard users with "invited" status in the organization', async () => {
        const onboardingService = createInMemoryOnboardingService();
        onboardingService.onboardUser = jest.fn(() => Promise.resolve());

        const mockedOnSelectedOrganization = jest.fn();
        renderApp({
            title: mockedTitle,
            onboardingService,
            organizations: [mockedActiveOrganizationInvitedUser],
            onSelectedOrganization: mockedOnSelectedOrganization,
        });

        expect(screen.getByText(mockedTitle)).toBeVisible();
        fireEvent.click(
            screen.getByRole('button', { name: `select organization ${mockedActiveOrganizationInvitedUser.id}` })
        );

        await waitForElementToBeRemoved(() => screen.getByText(mockedTitle));

        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        expect(onboardingService.onboardUser).toHaveBeenCalled();
        expect(mockedOnSelectedOrganization).toHaveBeenCalledWith(mockedActiveOrganizationInvitedUser.id);
    });
});

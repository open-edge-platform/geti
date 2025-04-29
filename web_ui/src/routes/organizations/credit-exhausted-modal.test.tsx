// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

import { createInMemoryCreditsService } from '../../core/credits/services/in-memory-credits-service';
import { GLOBAL_MODALS_KEYS, GlobalModalsConfig } from '../../core/user-settings/dtos/user-settings.interface';
import { createInMemoryUserSettingsService } from '../../core/user-settings/services/in-memory-user-settings-service';
import { ProjectProvider } from '../../pages/project-details/providers/project-provider/project-provider.component';
import { openNewTab } from '../../shared/utils';
import { getMockedUserGlobalSettings } from '../../test-utils/mocked-items-factory/mocked-settings';
import { providersRender as render } from '../../test-utils/required-providers-render';
import { CreditExhaustedModal } from './credit-exhausted-modal.component';

jest.mock('../../shared/utils', () => ({
    ...jest.requireActual('../../shared/utils'),
    openNewTab: jest.fn(),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: jest.fn(() => ({ organizationId: 'organizationId' })),
}));

const mockedProjectIdentifier = {
    projectId: 'project-id',
    workspaceId: 'workspace-id',
    organizationId: 'organization-id',
};

describe('CreditExhaustedModal', () => {
    const renderApp = async ({
        settings = {},
        mockedSaveSettings = jest.fn(),
        creditsAvailable = 0,
        creditsIncoming = 10,
    }: {
        mockedSaveSettings?: jest.Mock;
        settings?: Partial<GlobalModalsConfig>;
        creditsAvailable?: number;
        creditsIncoming?: number;
    }) => {
        const userSettingsService = createInMemoryUserSettingsService();
        userSettingsService.getGlobalSettings = async () => getMockedUserGlobalSettings(settings);
        userSettingsService.saveGlobalSettings = mockedSaveSettings;

        const creditsService = createInMemoryCreditsService();
        creditsService.getOrganizationBalance = () =>
            Promise.resolve({ incoming: creditsIncoming, available: creditsAvailable, blocked: 0 });

        render(
            <ProjectProvider projectIdentifier={mockedProjectIdentifier}>
                <CreditExhaustedModal organizationId={mockedProjectIdentifier.projectId} />
            </ProjectProvider>,
            { services: { userSettingsService, creditsService } }
        );

        await waitForElementToBeRemoved(screen.getAllByRole('progressbar'));
    };

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('loading balance', async () => {
        await renderApp({
            settings: { [GLOBAL_MODALS_KEYS.EXHAUSTED_ORGANIZATION_CREDITS_MODAL]: { isEnabled: false } },
        });

        expect(screen.queryByText(/credits have been exhaust/i)).not.toBeInTheDocument();
    });

    it('credits low message', async () => {
        await renderApp({
            creditsAvailable: 10,
            creditsIncoming: 100,
            settings: {
                [GLOBAL_MODALS_KEYS.WELCOME_MODAL]: { isEnabled: false },
                [GLOBAL_MODALS_KEYS.EXHAUSTED_ORGANIZATION_CREDITS_MODAL]: { isEnabled: false },
                [GLOBAL_MODALS_KEYS.LOW_ORGANIZATION_CREDITS_MODAL]: { isEnabled: true },
            },
        });
        expect(await screen.findByText(/credits are low/i)).toBeVisible();
        expect(screen.queryByText(/credits have been exhaust/i)).not.toBeInTheDocument();
    });

    it('credits low message should not be shown with key disabled', async () => {
        const mockedSaveSettings = jest.fn();

        await renderApp({
            creditsAvailable: 10,
            creditsIncoming: 100,
            settings: {
                [GLOBAL_MODALS_KEYS.WELCOME_MODAL]: { isEnabled: false },
                [GLOBAL_MODALS_KEYS.EXHAUSTED_ORGANIZATION_CREDITS_MODAL]: { isEnabled: true },
                [GLOBAL_MODALS_KEYS.LOW_ORGANIZATION_CREDITS_MODAL]: { isEnabled: false },
            },
            mockedSaveSettings,
        });
        expect(screen.queryByText(/credits are low/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/credits have been exhaust/i)).not.toBeInTheDocument();
    });

    it('credits exhausted message should not be shown with key disabled', async () => {
        await renderApp({
            creditsAvailable: 10,
            creditsIncoming: 100,
            settings: {
                [GLOBAL_MODALS_KEYS.WELCOME_MODAL]: { isEnabled: false },
                [GLOBAL_MODALS_KEYS.EXHAUSTED_ORGANIZATION_CREDITS_MODAL]: { isEnabled: false },
                [GLOBAL_MODALS_KEYS.LOW_ORGANIZATION_CREDITS_MODAL]: { isEnabled: false },
            },
        });
        expect(screen.queryByText(/credits are low/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/credits have been exhaust/i)).not.toBeInTheDocument();
    });

    it('open/close modal', async () => {
        const mockedSaveSettings = jest.fn();

        await renderApp({
            creditsAvailable: 0,
            settings: {
                [GLOBAL_MODALS_KEYS.WELCOME_MODAL]: { isEnabled: false },
                [GLOBAL_MODALS_KEYS.EXHAUSTED_ORGANIZATION_CREDITS_MODAL]: { isEnabled: true },
                [GLOBAL_MODALS_KEYS.LOW_ORGANIZATION_CREDITS_MODAL]: { isEnabled: false },
            },
            mockedSaveSettings,
        });

        expect(await screen.findByText(/credits have been exhaust/i)).toBeVisible();

        fireEvent.click(screen.getByRole('button', { name: /close/i }));

        await waitFor(() => {
            expect(mockedSaveSettings).toHaveBeenCalledWith(
                expect.objectContaining({
                    [GLOBAL_MODALS_KEYS.EXHAUSTED_ORGANIZATION_CREDITS_MODAL]: {
                        isEnabled: false,
                    },
                })
            );

            expect(openNewTab).not.toHaveBeenCalled();
        });
    });

    it('close modal and open contact tab', async () => {
        const mockedSaveSettings = jest.fn();

        await renderApp({
            creditsAvailable: 0,
            settings: {
                [GLOBAL_MODALS_KEYS.WELCOME_MODAL]: { isEnabled: false },
                [GLOBAL_MODALS_KEYS.EXHAUSTED_ORGANIZATION_CREDITS_MODAL]: { isEnabled: true },
                [GLOBAL_MODALS_KEYS.LOW_ORGANIZATION_CREDITS_MODAL]: { isEnabled: false },
            },
            mockedSaveSettings,
        });

        expect(await screen.findByText(/credits have been exhaust/i)).toBeVisible();

        fireEvent.click(screen.getByRole('button', { name: /contact support/i }));

        await waitFor(() => {
            expect(openNewTab).toHaveBeenCalled();
            expect(mockedSaveSettings).toHaveBeenCalledWith(
                expect.objectContaining({
                    [GLOBAL_MODALS_KEYS.EXHAUSTED_ORGANIZATION_CREDITS_MODAL]: {
                        isEnabled: false,
                    },
                })
            );
        });
    });
});

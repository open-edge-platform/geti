// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createInMemoryUsersService } from '@geti/core/src/users/services/in-memory-users-service';
import { User } from '@geti/core/src/users/users.interface';
import { fireEvent, screen, waitFor } from '@testing-library/react';
import { useParams } from 'react-router-dom';

import { createInMemoryCreditsService } from '../../../../core/credits/services/in-memory-credits-service';
import {
    FUX_NOTIFICATION_KEYS,
    FuxNotificationsConfig,
    FuxSettingsConfig,
} from '../../../../core/user-settings/dtos/user-settings.interface';
import { createInMemoryUserSettingsService } from '../../../../core/user-settings/services/in-memory-user-settings-service';
import { getMockedUserGlobalSettings } from '../../../../test-utils/mocked-items-factory/mocked-settings';
import { getMockedUser } from '../../../../test-utils/mocked-items-factory/mocked-users';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import { CreditBalanceButton } from './credit-balance-button.component';
import { CREDIT_LOW_LIMIT } from './util';

jest.mock('../../../utils', () => ({
    ...jest.requireActual('../../../utils'),
    openNewTab: jest.fn(),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: jest.fn(),
}));

const renderApp = async ({
    projectId,
    settings = {},
    mockedSaveSettings = jest.fn(),
    creditsIncoming = 0,
    creditsAvailable = 0,
    user,
}: {
    settings?: Partial<FuxNotificationsConfig | FuxSettingsConfig>;
    mockedSaveSettings?: jest.Mock;
    projectId?: string;
    creditsIncoming?: number;
    creditsAvailable?: number;
    user?: User;
}) => {
    jest.mocked(useParams).mockReturnValue({ projectId, organizationId: 'organizationId' });
    const userSettingsService = createInMemoryUserSettingsService();
    userSettingsService.getGlobalSettings = async () => Promise.resolve(getMockedUserGlobalSettings(settings));

    const creditsService = createInMemoryCreditsService();
    userSettingsService.saveGlobalSettings = mockedSaveSettings;
    creditsService.getOrganizationBalance = () =>
        Promise.resolve({ incoming: creditsIncoming, available: creditsAvailable, blocked: 0 });

    const usersService = createInMemoryUsersService();
    if (user) {
        usersService.getActiveUser = jest.fn(async () => user);
    }

    return render(<CreditBalanceButton isDarkMode={true} />, {
        services: { userSettingsService, creditsService, usersService },
    });
};

describe('CreditBalanceButton', () => {
    it('low credit', async () => {
        await renderApp({ creditsAvailable: CREDIT_LOW_LIMIT - 1, creditsIncoming: 100 });

        expect(await screen.findByRole('button', { name: 'credit balance status' })).toBeInTheDocument();
        expect(screen.getByLabelText('low credit indicator')).toBeVisible();
    });

    it('high credit', async () => {
        await renderApp({ creditsAvailable: 100, creditsIncoming: 100 });

        expect(await screen.findByRole('button', { name: 'credit balance status' })).toBeInTheDocument();
        expect(screen.queryByLabelText('low credit indicator')).not.toBeInTheDocument();
    });

    describe('has projectId param', () => {
        it('open/close notification', async () => {
            const mockedSaveSettings = jest.fn();
            const admin = getMockedUser({ email: 'test@mail.com', isAdmin: true });

            await renderApp({
                projectId: '321',
                settings: {
                    autoTrainingCreditNotification: { isEnabled: true },
                    firstAutotrainedProjectId: { value: 'project-id' },
                },
                mockedSaveSettings,
                user: admin,
            });

            expect(screen.getByText(/the auto-training job has been started/i)).toBeVisible();
            expect(screen.getByRole('button', { name: /credit balance stat/i })).toHaveClass('fuxOpen');
            expect(await screen.findByRole('button', { name: 'Learn more' })).toBeInTheDocument();

            fireEvent.click(screen.getByRole('button', { name: /close first user experience notification/i }));

            await waitFor(() => {
                const userSettings = 0;

                expect(mockedSaveSettings.mock.calls[userSettings]).toEqual([
                    expect.objectContaining({
                        [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION]: { isEnabled: false },
                    }),
                ]);
            });
        });

        it('will not show the notification if the users has navigated to other project that the autotrained one', async () => {
            const mockedSaveSettings = jest.fn();
            const admin = getMockedUser({ email: 'test@mail.com', isAdmin: true });

            await renderApp({
                projectId: '321',
                settings: {
                    autoTrainingCreditNotification: { isEnabled: true },
                    firstAutotrainedProjectId: { value: 'other-project-id' },
                },
                mockedSaveSettings,
                user: admin,
            });

            expect(screen.queryByText(/the auto-training job has been started/i)).not.toBeInTheDocument();
        });

        it('does not show a link to credits usage page for contributors', async () => {
            const usersService = createInMemoryUsersService();
            const contributor = getMockedUser({ email: 'test@mail.com', isAdmin: false });
            usersService.getActiveUser = jest.fn(async () => contributor);

            await renderApp({
                projectId: '321',
                settings: {
                    autoTrainingCreditNotification: { isEnabled: true },
                    firstAutotrainedProjectId: { value: 'project-id' },
                },
                user: contributor,
            });

            expect(screen.getByText(/the auto-training job has been started/i)).toBeVisible();
            expect(screen.getByRole('button', { name: /credit balance stat/i })).toHaveClass('fuxOpen');
            expect(screen.queryByRole('button', { name: 'Learn more' })).not.toBeInTheDocument();
        });

        it('fux style are hidden', async () => {
            await renderApp({
                projectId: '321',
                settings: {
                    autoTrainingCreditNotification: { isEnabled: false },
                    firstAutotrainedProjectId: { value: 'project-id' },
                },
            });

            expect(screen.queryByText(/the auto-training job has been started/i)).not.toBeInTheDocument();
            expect(screen.getByRole('button', { name: /credit balance stat/i })).not.toHaveClass('fuxOpen');
        });
    });
});

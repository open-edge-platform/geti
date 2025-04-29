// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { FUX_SETTINGS_KEYS } from '../../../../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../../../../core/user-settings/hooks/use-global-settings.hook';
import { initialConfig } from '../../../../../core/user-settings/utils';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { HelpActions } from './help-actions.component';

const mockSaveConfig = jest.fn();

jest.mock('../../../../../core/user-settings/hooks/use-global-settings.hook', () => ({
    ...jest.requireActual('../../../../../core/user-settings/hooks/use-global-settings.hook'),
    useUserGlobalSettings: jest.fn(() => ({
        isSavingConfig: false,
        saveConfig: mockSaveConfig,
    })),
}));

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: jest.fn(() => ({ organizationId: 'organization-id' })),
}));

describe('Docs actions', () => {
    jest.mocked(useUserGlobalSettings).mockReturnValue({
        isSavingConfig: false,
        saveConfig: mockSaveConfig,
        config: initialConfig,
    });

    describe('help actions', () => {
        it('Check if there are all needed actions', async () => {
            render(<HelpActions isDarkMode={false} />);

            fireEvent.click(screen.getByRole('button', { name: 'Documentation actions' }));

            expect(screen.getByText('User guide')).toBeInTheDocument();
            expect(screen.getByText('Reset help dialogs')).toBeInTheDocument();
            expect(screen.getByText('About')).toBeInTheDocument();
            expect(screen.getByText('Contact support')).toBeInTheDocument();
            expect(screen.getByText('REST API specification')).toBeInTheDocument();
        });
    });

    describe('Reset tutorial', () => {
        it('Check reset dialogs action', async () => {
            render(<HelpActions isDarkMode={false} />);

            fireEvent.click(screen.getByRole('button', { name: 'Documentation actions' }));
            fireEvent.click(screen.getByRole('menuitem', { name: 'Reset help dialogs' }));

            expect(mockSaveConfig).toHaveBeenCalledWith(
                { ...initialConfig, [FUX_SETTINGS_KEYS.USER_DISMISSED_ALL]: { value: false } },
                'Help dialogs have been reset.'
            );
        });
    });
});

// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { act, waitFor } from '@testing-library/react';

import { FUX_NOTIFICATION_KEYS } from '../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../core/user-settings/hooks/use-global-settings.hook';
import { initialFuxNotificationsConfig } from '../../core/user-settings/utils';
import { renderHookWithProviders } from '../../test-utils/render-hook-with-providers';
import { useTutorialEnablement } from './use-tutorial-enablement.hook';

const mockSaveConfig = jest.fn();

jest.mock('../../core/user-settings/hooks/use-global-settings.hook', () => ({
    ...jest.requireActual('../../core/user-settings/hooks/use-global-settings.hook'),
    useUserGlobalSettings: jest.fn(),
}));

describe('useTutorialEnablement', () => {
    it('given a config key with `isEnabled` as `false`, it returns `isOpen` as false', async () => {
        jest.mocked(useUserGlobalSettings).mockReturnValue({
            isSavingConfig: false,
            saveConfig: mockSaveConfig,
            config: {
                ...initialFuxNotificationsConfig,
                [FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY]: { isEnabled: false },
            },
        });

        const { result } = renderHookWithProviders(() =>
            useTutorialEnablement(FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY)
        );

        await waitFor(() => {
            expect(result.current.isOpen).toEqual(false);
        });
    });

    it('given a config key with `isEnabled` as `true`, it returns `isOpen` as true', async () => {
        jest.mocked(useUserGlobalSettings).mockReturnValue({
            isSavingConfig: false,
            saveConfig: mockSaveConfig,
            config: initialFuxNotificationsConfig,
        });

        const { result } = renderHookWithProviders(() =>
            useTutorialEnablement(FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY)
        );

        await waitFor(() => {
            expect(result.current.isOpen).toEqual(true);
        });
    });

    it('calling `close` should save settings and set `isOpen` to false', async () => {
        jest.mocked(useUserGlobalSettings).mockReturnValue({
            isSavingConfig: false,
            saveConfig: mockSaveConfig,
            config: initialFuxNotificationsConfig,
        });
        const { result } = renderHookWithProviders(() =>
            useTutorialEnablement(FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY)
        );

        await waitFor(() => {
            expect(result.current.isOpen).toEqual(true);
        });

        await act(async () => {
            await result.current.close();
        });

        await waitFor(() => {
            expect(mockSaveConfig).toHaveBeenCalledWith({
                ...initialFuxNotificationsConfig,
                [FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY]: {
                    isEnabled: false,
                },
            });
        });
    });
});

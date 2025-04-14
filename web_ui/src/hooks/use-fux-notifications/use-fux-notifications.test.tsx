// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { renderHook } from '@testing-library/react';

import { FUX_NOTIFICATION_KEYS, FUX_SETTINGS_KEYS } from '../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../core/user-settings/hooks/use-global-settings.hook';
import { INITIAL_GLOBAL_SETTINGS } from '../../core/user-settings/utils';
import { getMockedUserGlobalSettingsObject } from '../../test-utils/mocked-items-factory/mocked-settings';
import { useFuxNotifications } from './use-fux-notifications.hook';

const mockSaveConfig = jest.fn();
const mockSettings = getMockedUserGlobalSettingsObject({
    saveConfig: mockSaveConfig,
});

jest.mock('../../core/user-settings/hooks/use-global-settings.hook', () => ({
    ...jest.requireActual('../../core/user-settings/hooks/use-global-settings.hook'),
    useUserGlobalSettings: jest.fn(() => mockSettings),
}));

describe('useFuxNotifications', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('handleFirstAnnotation', () => {
        it('updates user settings if it was first ever annotation', () => {
            const { result } = renderHook(() => useFuxNotifications());

            result.current.handleFirstAnnotation();

            expect(mockSaveConfig).toHaveBeenCalledWith({
                ...INITIAL_GLOBAL_SETTINGS,
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_CONTINUE_ANNOTATING]: {
                    isEnabled: true,
                },
                [FUX_SETTINGS_KEYS.NEVER_ANNOTATED]: {
                    value: false,
                },
            });
        });
    });

    describe('handleFirstAutoTraining', () => {
        it('updates user settings if it was the first auto training', () => {
            const { result } = renderHook(() => useFuxNotifications());

            result.current.handleFirstAutoTraining('project-id', 'job-id');

            expect(mockSaveConfig).toHaveBeenCalledWith({
                ...INITIAL_GLOBAL_SETTINGS,
                [FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED]: { value: false },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: { value: 'project-id' },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINING_JOB_ID]: { value: 'job-id' },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: { isEnabled: true },
            });
        });
    });

    describe('handleFirstSuccessfulAutoTraining', () => {
        it('updates user settings if it was the first auto training', () => {
            const { result } = renderHook(() => useFuxNotifications());

            result.current.handleFirstSuccessfulAutoTraining('model-id');

            expect(mockSaveConfig).toHaveBeenCalledWith({
                ...INITIAL_GLOBAL_SETTINGS,
                [FUX_SETTINGS_KEYS.NEVER_SUCCESSFULLY_AUTOTRAINED]: { value: false },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_MODEL_ID]: { value: 'model-id' },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_SUCCESSFULLY_TRAINED]: { isEnabled: true },
                [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]: { isEnabled: false },
            });
        });
    });

    describe('handleFirstVisitToPredictionMode', () => {
        it('updates user settings if it was the first auto training', () => {
            const { result } = renderHook(() => useFuxNotifications());

            result.current.handleFirstVisitToPredictionMode();

            expect(mockSaveConfig).toHaveBeenCalledWith({
                ...INITIAL_GLOBAL_SETTINGS,
                [FUX_SETTINGS_KEYS.NEVER_CHECKED_PREDICTIONS]: { value: false },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_CHECK_PREDICTIONS]: { isEnabled: false },
            });
        });
    });

    describe('User dismissed all', () => {
        it('should never update settings', () => {
            jest.mocked(useUserGlobalSettings).mockImplementationOnce(() => ({
                ...mockSettings,
                config: {
                    ...mockSettings.config,
                    [FUX_SETTINGS_KEYS.USER_DISMISSED_ALL]: {
                        value: true,
                    },
                },
            }));

            const { result } = renderHook(() => useFuxNotifications());

            result.current.handleFirstAnnotation();
            result.current.handleFirstAutoTraining('project-id', 'job-id');
            result.current.handleFirstSuccessfulAutoTraining('model-id');
            result.current.handleFirstVisitToPredictionMode();

            expect(mockSaveConfig).not.toHaveBeenCalled();
        });
    });
});

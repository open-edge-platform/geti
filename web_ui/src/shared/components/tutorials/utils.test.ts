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

import {
    FUX_NOTIFICATION_KEYS,
    FUX_SETTINGS_KEYS,
    FuxNotificationsConfig,
    GENERAL_SETTINGS_KEYS,
    TUTORIAL_CARD_KEYS,
    TutorialConfig,
} from '../../../core/user-settings/dtos/user-settings.interface';
import {
    initialConfig,
    initialFuxNotificationsConfig,
    initialFuxSettingsConfig,
    initialTutorialConfig,
} from '../../../core/user-settings/utils';
import {
    dismissAllTutorials,
    dismissTutorial,
    getTutorialAndFuxNotificationsConfig,
    handleChangeTutorial,
    onPressLearnMore,
    resetAllTutorials,
} from './utils';

describe('Tutorial utils', () => {
    describe('getTutorialAndFuxNotificationsConfig', () => {
        it('returns settings for normal tutorials + first user experience', () => {
            expect(getTutorialAndFuxNotificationsConfig(initialConfig)).toEqual({
                ...initialTutorialConfig,
                ...initialFuxNotificationsConfig,
            });
        });
    });

    describe('onPressLearnMore', () => {
        it('opens new tab when provided a valid doc Url', () => {
            const spy = jest.spyOn(window, 'open').mockImplementation();

            onPressLearnMore('some-url');

            expect(spy).toHaveBeenCalledWith('some-url', '_blank', 'noopener,noreferrer');
        });

        it('returns "undefined" when provided with an "undefined" docUrl', () => {
            expect(onPressLearnMore(undefined)).toBeUndefined();
        });
    });

    describe('dismissAllTutorials', () => {
        it('should dismiss all tutorial settings (fux + tutorials + credit)', () => {
            const mockSaveConfig = jest.fn();

            dismissAllTutorials({
                config: initialConfig,
                isSavingConfig: false,
                saveConfig: mockSaveConfig,
            });

            const tutorialAndFuxNotificationKeys = [
                ...Object.values(TUTORIAL_CARD_KEYS),
                ...Object.values(FUX_NOTIFICATION_KEYS),
            ];
            const expectedConfig = {
                ...initialConfig,
                [FUX_SETTINGS_KEYS.NEVER_SUCCESSFULLY_AUTOTRAINED]: {
                    value: true,
                },
                [FUX_SETTINGS_KEYS.USER_DISMISSED_ALL]: {
                    value: true,
                },
                [FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED]: {
                    value: true,
                },
                [FUX_SETTINGS_KEYS.NEVER_ANNOTATED]: {
                    value: true,
                },
                [FUX_SETTINGS_KEYS.NEVER_CHECKED_PREDICTIONS]: {
                    value: true,
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: {
                    value: null,
                },
            };

            tutorialAndFuxNotificationKeys.forEach((key) => {
                expectedConfig[key].isEnabled = false;
            });

            expect(mockSaveConfig).toHaveBeenCalledWith(expectedConfig);
        });

        it('should dismiss all notification even when they were already dismissed', () => {
            const mockSaveConfig = jest.fn();

            const dismissedTutorialAndFuxNotificationConfig = {
                ...initialTutorialConfig,
                ...initialFuxNotificationsConfig,
            };
            for (const key in dismissedTutorialAndFuxNotificationConfig) {
                const tutorialKey = key as keyof typeof dismissedTutorialAndFuxNotificationConfig;
                const tutorial = dismissedTutorialAndFuxNotificationConfig[tutorialKey];
                if ('isEnabled' in tutorial) {
                    tutorial.isEnabled = false;
                }
            }

            dismissAllTutorials({
                config: { ...dismissedTutorialAndFuxNotificationConfig, ...initialFuxSettingsConfig },
                isSavingConfig: false,
                saveConfig: mockSaveConfig,
            });

            const tutorialAndFuxNotificationKeys = [
                ...Object.values(TUTORIAL_CARD_KEYS),
                ...Object.values(FUX_NOTIFICATION_KEYS),
            ];

            const expectedConfig = {
                ...initialTutorialConfig,
                ...initialFuxNotificationsConfig,
                [FUX_SETTINGS_KEYS.NEVER_SUCCESSFULLY_AUTOTRAINED]: {
                    value: true,
                },
                [FUX_SETTINGS_KEYS.USER_DISMISSED_ALL]: {
                    value: true,
                },
                [FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED]: {
                    value: true,
                },
                [FUX_SETTINGS_KEYS.NEVER_ANNOTATED]: {
                    value: true,
                },
                [FUX_SETTINGS_KEYS.NEVER_CHECKED_PREDICTIONS]: {
                    value: true,
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: {
                    value: null,
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINING_JOB_ID]: {
                    value: null,
                },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_MODEL_ID]: {
                    value: null,
                },
            };

            tutorialAndFuxNotificationKeys.forEach((key) => {
                expectedConfig[key].isEnabled = false;
            });

            expect(mockSaveConfig).toHaveBeenCalledWith(expectedConfig);
        });
    });

    describe('handleChangeTutorial', () => {
        it('disables current key and enables the designated key', () => {
            const mockSaveConfig = jest.fn();

            handleChangeTutorial(
                FUX_NOTIFICATION_KEYS.ANNOTATOR_ACTIVE_SET,
                FUX_NOTIFICATION_KEYS.ANNOTATOR_CHECK_PREDICTIONS,
                {
                    config: initialFuxNotificationsConfig,
                    isSavingConfig: false,
                    saveConfig: mockSaveConfig,
                }
            );

            const expectedConfig: FuxNotificationsConfig = {
                ...initialFuxNotificationsConfig,
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_ACTIVE_SET]: { isEnabled: false },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_CHECK_PREDICTIONS]: { isEnabled: true },
            };

            expect(mockSaveConfig).toHaveBeenCalledWith(expectedConfig);
        });
    });

    describe('dismissTutorial', () => {
        it('should dismiss a tutorial correctly', () => {
            const mockSaveConfig = jest.fn();

            dismissTutorial(TUTORIAL_CARD_KEYS.LIVE_PREDICTION_NOTIFICATION, {
                config: initialConfig,
                isSavingConfig: false,
                saveConfig: mockSaveConfig,
            });

            const expectedConfig: TutorialConfig = {
                ...initialConfig,
                [TUTORIAL_CARD_KEYS.LIVE_PREDICTION_NOTIFICATION]: { isEnabled: false },
            };

            expect(mockSaveConfig).toHaveBeenCalledWith(expectedConfig);
        });
    });

    describe('resetAllTutorials', () => {
        it('should enable all tutorials correctly', () => {
            const mockSaveConfig = jest.fn();

            resetAllTutorials({
                config: {
                    ...initialConfig,
                    [TUTORIAL_CARD_KEYS.PROJECT_DATASET_TUTORIAL]: { isEnabled: false },
                    [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: { value: 'project-id' },
                    [FUX_NOTIFICATION_KEYS.ANNOTATOR_TOOLS]: { isEnabled: false },
                    [FUX_NOTIFICATION_KEYS.ANNOTATOR_CONTINUE_ANNOTATING]: { isEnabled: false },
                    [FUX_NOTIFICATION_KEYS.ANNOTATOR_ACTIVE_SET]: { isEnabled: true },
                    [FUX_NOTIFICATION_KEYS.ANNOTATOR_CHECK_PREDICTIONS]: { isEnabled: false },
                    [GENERAL_SETTINGS_KEYS.MAINTENANCE_BANNER]: {
                        wasDismissed: false,
                        window: { start: 0, end: 0 },
                    },
                },
                isSavingConfig: false,
                saveConfig: mockSaveConfig,
            });

            expect(mockSaveConfig).toHaveBeenCalledWith(initialConfig, 'Help dialogs have been reset.');
        });
    });
});

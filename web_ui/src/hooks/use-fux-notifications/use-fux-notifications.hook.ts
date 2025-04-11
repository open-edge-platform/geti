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

import { useCallback } from 'react';

import { FUX_NOTIFICATION_KEYS, FUX_SETTINGS_KEYS } from '../../core/user-settings/dtos/user-settings.interface';
import { useUserGlobalSettings } from '../../core/user-settings/hooks/use-global-settings.hook';
import { getSettingsOfType } from '../../core/user-settings/utils';
import { getFuxSetting } from '../../shared/components/tutorials/utils';

export const useFuxNotifications = () => {
    const settings = useUserGlobalSettings();

    const handleFirstAnnotation = () => {
        const hasNeverAnnotated = getFuxSetting(FUX_SETTINGS_KEYS.NEVER_ANNOTATED, settings.config);

        if (hasNeverAnnotated) {
            settings.saveConfig({
                ...settings.config,
                [FUX_SETTINGS_KEYS.NEVER_ANNOTATED]: { value: false },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_CONTINUE_ANNOTATING]: { isEnabled: true },
            });
        }
    };

    const handleFirstAutoTraining = useCallback(
        async (projectId: string, jobId: string) => {
            const hasNeverAutotrained = getFuxSetting(FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED, settings.config);

            if (hasNeverAutotrained) {
                await settings.saveConfig({
                    ...settings.config,
                    [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: { isEnabled: true },
                    [FUX_NOTIFICATION_KEYS.ANNOTATOR_CONTINUE_ANNOTATING]: { isEnabled: false },
                    [FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED]: { value: false },
                    [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: { value: projectId },
                    [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINING_JOB_ID]: { value: jobId },
                });
            }
        },
        [settings]
    );

    const handleFirstSuccessfulAutoTraining = async (trainedModelId: string) => {
        const hasNeverSuccessfullyAutotrained = getFuxSetting(
            FUX_SETTINGS_KEYS.NEVER_SUCCESSFULLY_AUTOTRAINED,
            settings.config
        );

        const settingsConfig = getSettingsOfType(settings.config, FUX_NOTIFICATION_KEYS);
        const settingToDisable = settingsConfig[FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL].isEnabled
            ? FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL
            : FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION;

        if (hasNeverSuccessfullyAutotrained) {
            await settings.saveConfig({
                ...settings.config,
                [FUX_SETTINGS_KEYS.NEVER_SUCCESSFULLY_AUTOTRAINED]: { value: false },
                [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_MODEL_ID]: { value: trainedModelId },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: { isEnabled: false },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_CONTINUE_ANNOTATING]: { isEnabled: false },
                [settingToDisable]: { isEnabled: false },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_SUCCESSFULLY_TRAINED]: { isEnabled: true },
            });
        }
    };
    const handleFirstVisitToPredictionMode = () => {
        const neverCheckedPredictions = getFuxSetting(FUX_SETTINGS_KEYS.NEVER_CHECKED_PREDICTIONS, settings.config);

        if (neverCheckedPredictions) {
            settings.saveConfig({
                ...settings.config,
                [FUX_SETTINGS_KEYS.NEVER_CHECKED_PREDICTIONS]: { value: false },
                [FUX_NOTIFICATION_KEYS.ANNOTATOR_CHECK_PREDICTIONS]: { isEnabled: false },
            });
        }
    };

    return {
        handleFirstAnnotation,
        handleFirstAutoTraining,
        handleFirstSuccessfulAutoTraining,
        handleFirstVisitToPredictionMode,
    };
};

// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
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
    TUTORIAL_CARD_KEYS,
} from '../../../core/user-settings/dtos/user-settings.interface';
import { UserGlobalSettings, UseSettings } from '../../../core/user-settings/services/user-settings.interface';
import {
    getSettingsOfType,
    initialFuxNotificationsConfig,
    initialFuxSettingsConfig,
    initialGeneralSettingsConfig,
    initialTutorialConfig,
} from '../../../core/user-settings/utils';
import { openNewTab } from '../../utils';

export const getTutorialAndFuxNotificationsConfig = (config: UserGlobalSettings) =>
    getSettingsOfType(config, {
        ...TUTORIAL_CARD_KEYS,
        ...FUX_NOTIFICATION_KEYS,
    });

export const dismissTutorial = (
    tutorialKey: TUTORIAL_CARD_KEYS | FUX_NOTIFICATION_KEYS,
    settings: UseSettings<UserGlobalSettings>
) => {
    const tutorialAndFuxNotificationsSettings = getTutorialAndFuxNotificationsConfig(settings.config);

    return settings.saveConfig({
        ...settings.config,
        [tutorialKey]: {
            ...tutorialAndFuxNotificationsSettings[tutorialKey],
            isEnabled: false,
        },
    });
};

export const resetAllTutorials = async (settings: UseSettings<UserGlobalSettings>) => {
    // eslint-disable-next-line max-len
    // Note: We need to reset the FUX settings as well because some notifications are bond to the first project they were triggered on
    await settings.saveConfig(
        {
            ...settings.config,
            ...initialGeneralSettingsConfig,
            ...initialTutorialConfig,
            ...initialFuxNotificationsConfig,
            ...initialFuxSettingsConfig,
        },
        'Help dialogs have been reset.'
    );
};

export const handleChangeTutorial = async (
    currentKey: FUX_NOTIFICATION_KEYS,
    changeToKey: FUX_NOTIFICATION_KEYS,
    settings: UseSettings<UserGlobalSettings>
) => {
    const tutorialAndFuxNotificationsSettings = getTutorialAndFuxNotificationsConfig(settings.config);

    await settings.saveConfig({
        ...settings.config,
        [currentKey]: {
            ...tutorialAndFuxNotificationsSettings[currentKey],
            isEnabled: false,
        },
        [changeToKey]: {
            ...tutorialAndFuxNotificationsSettings[changeToKey],
            isEnabled: true,
        },
    });
};

export const dismissAllTutorials = async (settings: UseSettings<UserGlobalSettings>) => {
    const tutorialAndFuxNotificationsSettings = getTutorialAndFuxNotificationsConfig(settings.config);
    const allValues = [...Object.values(TUTORIAL_CARD_KEYS), ...Object.values(FUX_NOTIFICATION_KEYS)];

    allValues.forEach((cardKey) => {
        if (tutorialAndFuxNotificationsSettings[cardKey] !== undefined) {
            tutorialAndFuxNotificationsSettings[cardKey].isEnabled = false;
        }
    });

    await settings.saveConfig({
        ...settings.config,
        ...tutorialAndFuxNotificationsSettings,
        [FUX_SETTINGS_KEYS.USER_DISMISSED_ALL]: { value: true },
    });
};

export enum DocsUrl {
    LABELS_CREATION = 'guide/project-management/project-management.html#labels-creation',
    DETECTION = 'guide/project-management/project-management.html#labels-creation',
    CLASSIFICATION = 'guide/project-management/project-management.html#labels-creation',
    SEGMENTATION = 'guide/project-management/project-management.html#labels-creation',
    ANOMALY = 'guide/additional-resources/ai-fundamentals/anomaly-classification-project.html',
    REVISIT_LABELS = `
        guide/labels/labels-management.html#dealing-with-new-labels-and-concept-drift-in-the-intel-geti-platform
    `,
    DATASET = 'guide/datasets/dataset-management.html',
    MODELS = 'guide/model-training-and-optimization/model-training-and-optimization.html',
    TESTS = 'guide/tests-management/tests.html',
    DEPLOYMENT = 'guide/deployments/deployments.html',
    MAIN_PAGE = 'guide/get-started/introduction.html',
    ANNOTATIONS_VS_PREDICTIONS = 'guide/annotations/annotation-editor.html#annotations-vs-predictions',
    ACTIVE_LEARNING = 'guide/annotations/annotation-editor.html#active-learning',
    MEDIA_GALLERY = 'guide/annotations/annotation-mode.html#media-gallery',
    ANNOTATION_TOOLS = 'guide/annotations/annotation-tools.html',
    ANNOTATION_EDITOR = 'guide/annotations/annotation-editor.html',
    MODEL_TRAINING_AND_OPTIMIZATION = 'guide/model-training-and-optimization/model-training-and-optimization.html',
    CODE_DEPLOYMENT = 'guide/deployments/deployments.html#code-deployment',
}

export const onPressLearnMore = (docUrl: string | undefined) => {
    return docUrl ? openNewTab(docUrl) : undefined;
};

export const getFuxSetting = (key: FUX_SETTINGS_KEYS, settings: UserGlobalSettings): boolean | string | null => {
    const fuxSettings = getSettingsOfType(settings, FUX_SETTINGS_KEYS);
    const userDismissedAll = fuxSettings[FUX_SETTINGS_KEYS.USER_DISMISSED_ALL];

    return !userDismissedAll.value && fuxSettings[key].value;
};

// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
    LABELS_CREATION = 'docs/user-guide/geti-fundamentals/project-management#labels-creation',
    DETECTION = 'docs/user-guide/geti-fundamentals/project-management#labels-creation',
    CLASSIFICATION = 'docs/user-guide/geti-fundamentals/project-management#labels-creation',
    SEGMENTATION = 'docs/user-guide/geti-fundamentals/project-management#labels-creation',
    REVISIT_LABELS = 'docs/user-guide/geti-fundamentals/labels/labels-management' +
        '#dealing-with-new-labels-and-concept-drift-in-the-intel-geti-platform',
    DATASET = 'docs/user-guide/geti-fundamentals/datasets/dataset-management',
    MODELS = 'docs/user-guide/geti-fundamentals/model-training-and-optimization',
    TESTS = 'docs/user-guide/geti-fundamentals/tests-management/tests',
    DEPLOYMENT = 'docs/user-guide/geti-fundamentals/deployments/',
    MAIN_PAGE = 'docs/user-guide/getting-started/introduction',
    ANNOTATIONS_VS_PREDICTIONS = 'docs/user-guide/geti-fundamentals/annotations/annotation-editor' +
        '#annotations-vs-predictions',
    ACTIVE_LEARNING = 'docs/user-guide/learn-geti/active-learning',
    MEDIA_GALLERY = 'docs/user-guide/geti-fundamentals/annotations/annotation-mode#media-gallery',
    ANNOTATION_TOOLS = 'docs/user-guide/geti-fundamentals/annotations/annotation-tools',
    ANNOTATION_EDITOR = 'docs/user-guide/geti-fundamentals/annotations/annotation-editor',
    CODE_DEPLOYMENT = 'docs/user-guide/geti-fundamentals/deployments/code-deployment',
}

export const onPressLearnMore = (docUrl: string | undefined) => {
    return docUrl ? openNewTab(docUrl) : undefined;
};

export const getFuxSetting = (key: FUX_SETTINGS_KEYS, settings: UserGlobalSettings): boolean | string | null => {
    const fuxSettings = getSettingsOfType(settings, FUX_SETTINGS_KEYS);
    const userDismissedAll = fuxSettings[FUX_SETTINGS_KEYS.USER_DISMISSED_ALL];

    return !userDismissedAll.value && fuxSettings[key].value;
};

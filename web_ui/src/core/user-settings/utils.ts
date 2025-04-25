// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    AnnotatorSettingsConfig,
    CANVAS_ADJUSTMENTS_KEYS,
    CanvasSettingsConfig,
    FEATURES_KEYS,
    FUX_NOTIFICATION_KEYS,
    FUX_SETTINGS_KEYS,
    FuxNotificationsConfig,
    FuxSettingsConfig,
    GENERAL_SETTINGS_KEYS,
    GeneralSettingsConfig,
    GLOBAL_MODALS_KEYS,
    GlobalModalsConfig,
    TUTORIAL_CARD_KEYS,
    TutorialConfig,
} from './dtos/user-settings.interface';
import { UserGlobalSettings, UserProjectSettings } from './services/user-settings.interface';

export const initialAnnotatorConfig: AnnotatorSettingsConfig = {
    [FEATURES_KEYS.ANNOTATION_PANEL]: {
        title: 'Annotation',
        isEnabled: true,
        tooltipDescription: 'Show annotation/prediction list on the right sidebar',
    },
    [FEATURES_KEYS.COUNTING_PANEL]: {
        title: 'Counting',
        isEnabled: false,
        tooltipDescription: 'Show counting list on the right sidebar',
    },
    [FEATURES_KEYS.DATASET_PANEL]: {
        title: 'Dataset',
        isEnabled: true,
        tooltipDescription: 'Show dataset list on the right sidebar',
    },
    [FEATURES_KEYS.INITIAL_PREDICTION]: {
        title: 'Initial Prediction',
        isEnabled: true,
        tooltipDescription: 'Turn off to skip loading predictions when opening an image.',
    },
    [FEATURES_KEYS.INFERENCE_MODEL]: {
        title: 'Use active model as inference model',
        isEnabled: true,
        tooltipDescription: 'Turn off to use prompt learning model as inference model.',
    },
};

export const initialCanvasConfig: CanvasSettingsConfig = {
    [CANVAS_ADJUSTMENTS_KEYS.HIDE_LABELS]: {
        value: false,
        defaultValue: false,
    },
    [CANVAS_ADJUSTMENTS_KEYS.LABEL_OPACITY]: {
        value: 1,
        defaultValue: 1,
    },
    [CANVAS_ADJUSTMENTS_KEYS.ANNOTATION_BORDER_OPACITY]: {
        value: 1,
        defaultValue: 1,
    },
    [CANVAS_ADJUSTMENTS_KEYS.ANNOTATION_FILL_OPACITY]: {
        value: 0.4,
        defaultValue: 0.4,
    },
    [CANVAS_ADJUSTMENTS_KEYS.IMAGE_BRIGHTNESS]: {
        value: 0,
        defaultValue: 0,
    },
    [CANVAS_ADJUSTMENTS_KEYS.IMAGE_CONTRAST]: {
        value: 0,
        defaultValue: 0,
    },
    [CANVAS_ADJUSTMENTS_KEYS.IMAGE_SATURATION]: {
        value: 0,
        defaultValue: 0,
    },
    [CANVAS_ADJUSTMENTS_KEYS.PIXEL_VIEW]: {
        value: true,
        defaultValue: true,
    },
    [CANVAS_ADJUSTMENTS_KEYS.MARKERS_OPACITY]: {
        value: 1,
        defaultValue: 1,
    },
};

const initialGlobalModalsConfig: GlobalModalsConfig = {
    [GLOBAL_MODALS_KEYS.WELCOME_MODAL]: {
        isEnabled: true,
    },
    [GLOBAL_MODALS_KEYS.EXHAUSTED_ORGANIZATION_CREDITS_MODAL]: {
        isEnabled: true,
    },
    [GLOBAL_MODALS_KEYS.LOW_ORGANIZATION_CREDITS_MODAL]: {
        isEnabled: true,
    },
};

export const initialGeneralSettingsConfig: GeneralSettingsConfig = {
    [GENERAL_SETTINGS_KEYS.CHOSEN_ORGANIZATION]: { value: null },
    [GENERAL_SETTINGS_KEYS.MAINTENANCE_BANNER]: {
        wasDismissed: false,
        window: {
            start: 0,
            end: 0,
        },
    },
};

export const initialTutorialConfig: TutorialConfig = {
    [TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_SEGMENTATION]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_DETECTION]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_DETECTION_CHAIN]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_CLASSIFICATION_HIERARCHICAL]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_CLASSIFICATION_SINGLE_SELECTION]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_CLASSIFICATION_MULTIPLE_SELECTION]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.ANNOTATOR_DATASET_TUTORIAL]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.PROJECT_DATASET_TUTORIAL]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.PROJECT_MODEL_TUTORIAL]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.ANOMALY_TUTORIAL]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.ANNOTATIONS_COUNT_LIMIT]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.LIVE_PREDICTION_NOTIFICATION]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.PROJECT_TESTS_TUTORIAL]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.PROJECT_DEPLOYMENT_TUTORIAL]: {
        isEnabled: true,
    },
};

export const initialFuxNotificationsConfig: FuxNotificationsConfig = {
    [FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY]: {
        isEnabled: true,
    },
    [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: {
        isEnabled: false,
    },
    [FUX_NOTIFICATION_KEYS.ANNOTATOR_ACTIVE_SET]: {
        isEnabled: false,
    },
    [FUX_NOTIFICATION_KEYS.ANNOTATOR_TOOLS]: {
        isEnabled: true,
    },
    [FUX_NOTIFICATION_KEYS.ANNOTATOR_SUCCESSFULLY_TRAINED]: {
        isEnabled: false,
    },
    [FUX_NOTIFICATION_KEYS.ANNOTATOR_CHECK_PREDICTIONS]: {
        isEnabled: false,
    },
    [FUX_NOTIFICATION_KEYS.ANNOTATOR_CONTINUE_ANNOTATING]: {
        isEnabled: false,
    },
    [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_MODAL]: {
        isEnabled: true,
    },
    [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION]: {
        isEnabled: false,
    },
};

export const initialFuxSettingsConfig: FuxSettingsConfig = {
    [FUX_SETTINGS_KEYS.NEVER_SUCCESSFULLY_AUTOTRAINED]: {
        value: true,
    },
    [FUX_SETTINGS_KEYS.USER_DISMISSED_ALL]: {
        value: false,
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

export const initialConfig = {
    ...initialAnnotatorConfig,
    ...initialTutorialConfig,
    ...initialFuxNotificationsConfig,
    ...initialFuxSettingsConfig,
    ...initialCanvasConfig,
    ...initialGlobalModalsConfig,
    ...initialGeneralSettingsConfig,
};

export const INITIAL_PROJECT_SETTINGS = {
    ...initialAnnotatorConfig,
    ...initialCanvasConfig,
} satisfies UserProjectSettings;

export const INITIAL_GLOBAL_SETTINGS = {
    ...initialGlobalModalsConfig,
    ...initialGeneralSettingsConfig,
    ...initialTutorialConfig,
    ...initialFuxNotificationsConfig,
    ...initialFuxSettingsConfig,
} satisfies UserGlobalSettings;

export const getSettingsOfType = (
    settings: UserGlobalSettings | UserProjectSettings,
    enumType:
        | typeof TUTORIAL_CARD_KEYS
        | typeof FEATURES_KEYS
        | typeof CANVAS_ADJUSTMENTS_KEYS
        | typeof FUX_NOTIFICATION_KEYS
        | typeof FUX_SETTINGS_KEYS
        | typeof GLOBAL_MODALS_KEYS
        | typeof GENERAL_SETTINGS_KEYS
) => {
    return Object.fromEntries(
        Object.entries(settings).filter(([key]) => {
            return Object.values(enumType).includes(key);
        })
    );
};

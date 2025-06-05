// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
export enum FEATURES_KEYS {
    DATASET_PANEL = 'dataset',
    COUNTING_PANEL = 'counting',
    ANNOTATION_PANEL = 'annotation',
    INITIAL_PREDICTION = 'initialPredictionAsAnnotations',
    INFERENCE_MODEL = 'inferenceModel',
}

export enum CANVAS_ADJUSTMENTS_KEYS {
    LABEL_OPACITY = 'labelOpacity',
    ANNOTATION_FILL_OPACITY = 'annotationFillOpacity',
    ANNOTATION_BORDER_OPACITY = 'annotationBorderOpacity',
    IMAGE_BRIGHTNESS = 'imageBrightness',
    IMAGE_CONTRAST = 'imageContrast',
    IMAGE_SATURATION = 'imageSaturation',
    PIXEL_VIEW = 'pixelView',
    HIDE_LABELS = 'hideLabels',
    MARKERS_OPACITY = 'markersOpacity',
}

export enum TUTORIAL_CARD_KEYS {
    CREATE_PROJECT_LABELS_DETECTION = 'createProjectLabelsDetectionTutorial',
    CREATE_PROJECT_LABELS_DETECTION_CHAIN = 'createProjectLabelsDetectionChainTutorial',
    CREATE_PROJECT_LABELS_SEGMENTATION = 'createProjectLabelsSegmentationTutorial',
    CREATE_PROJECT_LABELS_CLASSIFICATION_SINGLE_SELECTION = 'createProjectLabelsClassificationSingleSelectionTutorial',
    CREATE_PROJECT_LABELS_CLASSIFICATION_MULTIPLE_SELECTION = 'createProjectLabelsClassification' +
        'MultipleSelectionTutorial',
    CREATE_PROJECT_LABELS_CLASSIFICATION_HIERARCHICAL = 'createProjectLabelsClassificationHierarchicalTutorial',
    PROJECT_MODEL_TUTORIAL = 'projectModelTutorial',
    PROJECT_DATASET_TUTORIAL = 'projectDatasetTutorial',
    PROJECT_DEPLOYMENT_TUTORIAL = 'projectDeploymentTutorial',
    PROJECT_TESTS_TUTORIAL = 'projectTestsTutorial',
    ANNOTATOR_DATASET_TUTORIAL = 'annotatorDatasetTutorial',
    ANOMALY_TUTORIAL = 'anomalyTutorial',
    ANNOTATIONS_COUNT_LIMIT = 'annotationsCountLimit',
    LIVE_PREDICTION_NOTIFICATION = 'livePredictionNotification',
}

export enum FUX_NOTIFICATION_KEYS {
    ANNOTATE_INTERACTIVELY = 'annotateInteractively',
    ANNOTATOR_AUTO_TRAINING_STARTED = 'annotatorAutoTrainingStarted',
    ANNOTATOR_TOOLS = 'annotatorTools',
    ANNOTATOR_ACTIVE_SET = 'annotatorActiveSet',
    ANNOTATOR_SUCCESSFULLY_TRAINED = 'annotatorSuccessfullyTrained',
    ANNOTATOR_CHECK_PREDICTIONS = 'annotatorCheckPredictions',
    ANNOTATOR_CONTINUE_ANNOTATING = 'annotatorContinueAnnotating',
    AUTO_TRAINING_MODAL = 'autoTrainingCreditModal',
    AUTO_TRAINING_NOTIFICATION = 'autoTrainingCreditNotification',
}

export enum FUX_SETTINGS_KEYS {
    NEVER_ANNOTATED = 'neverAnnotated',
    NEVER_AUTOTRAINED = 'neverAutotrained',
    NEVER_CHECKED_PREDICTIONS = 'neverCheckedPredictions',
    USER_DISMISSED_ALL = 'userDismissedAll',
    NEVER_SUCCESSFULLY_AUTOTRAINED = 'neverSuccessfullyAutotrained',
    FIRST_AUTOTRAINED_PROJECT_ID = 'firstAutotrainedProjectId',
    FIRST_AUTOTRAINING_JOB_ID = 'firstAutoTrainingJobId',
    FIRST_AUTOTRAINED_MODEL_ID = 'firstAutoTrainedModelId',
}

export enum GLOBAL_MODALS_KEYS {
    WELCOME_MODAL = 'welcomeModal',
    EXHAUSTED_ORGANIZATION_CREDITS_MODAL = 'exhaustedOrganizationCreditsModal',
    LOW_ORGANIZATION_CREDITS_MODAL = 'lowOrganizationCreditsModal',
}

export enum GENERAL_SETTINGS_KEYS {
    MAINTENANCE_BANNER = 'maintenanceBanner',
}

export type TutorialKeys = TUTORIAL_CARD_KEYS | FUX_NOTIFICATION_KEYS | FUX_SETTINGS_KEYS;
export type SettingsKeys = FEATURES_KEYS | TutorialKeys;

export interface SettingsFeature {
    title: string;
    isEnabled: boolean;
    tooltipDescription: string;
}

interface CanvasSettingsValues<T extends boolean | number> {
    value: T;
    defaultValue: T;
}

export type GeneralSettingsConfig = {
    [GENERAL_SETTINGS_KEYS.MAINTENANCE_BANNER]: { wasDismissed: boolean; window: { start: number; end: number } };
};

export type GlobalModalsConfig = Record<GLOBAL_MODALS_KEYS, { isEnabled: boolean }>;
export type TutorialConfig = Record<TUTORIAL_CARD_KEYS, { isEnabled: boolean }>;
export type FuxNotificationsConfig = Record<FUX_NOTIFICATION_KEYS, { isEnabled: boolean }>;
export type FuxSettingsConfig = Record<FUX_SETTINGS_KEYS, { value: boolean | null | string }>;
export type AnnotatorSettingsConfig = Record<FEATURES_KEYS, SettingsFeature>;
export type CanvasSettingsConfig = Record<
    CANVAS_ADJUSTMENTS_KEYS,
    CanvasSettingsValues<number> | CanvasSettingsValues<boolean>
>;

export type SettingsDTO = string;

export interface SettingsResponseDTO {
    settings: SettingsDTO;
}

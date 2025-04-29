// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { OpenApiResponseBody } from '../../../src/core/server/types';
import {
    FUX_NOTIFICATION_KEYS,
    FUX_SETTINGS_KEYS,
    GLOBAL_MODALS_KEYS,
    TUTORIAL_CARD_KEYS,
} from '../../../src/core/user-settings/dtos/user-settings.interface';

export const disabledFUXSettings = {
    homePageTutorial: {
        title: 'Home page tutorial',
        isEnabled: false,
        tooltipDescription: 'Toggle tutorial on the home page',
    },
    annotatorScreenTutorial: {
        title: 'Annotator tutorial',
        isEnabled: false,
        tooltipDescription: 'Toggle tutorial on annotator page',
    },
    [TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_SEGMENTATION]: {
        isEnabled: false,
    },
    [TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_DETECTION]: {
        isEnabled: false,
    },
    [TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_DETECTION_CHAIN]: {
        isEnabled: false,
    },
    [TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_CLASSIFICATION_HIERARCHICAL]: {
        isEnabled: false,
    },
    [TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_CLASSIFICATION_SINGLE_SELECTION]: {
        isEnabled: false,
    },
    [TUTORIAL_CARD_KEYS.CREATE_PROJECT_LABELS_CLASSIFICATION_MULTIPLE_SELECTION]: {
        isEnabled: false,
    },
    [TUTORIAL_CARD_KEYS.ANNOTATOR_DATASET_TUTORIAL]: {
        isEnabled: false,
    },
    [TUTORIAL_CARD_KEYS.PROJECT_DATASET_TUTORIAL]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.PROJECT_MODEL_TUTORIAL]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.PROJECT_TESTS_TUTORIAL]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.PROJECT_DEPLOYMENT_TUTORIAL]: {
        isEnabled: true,
    },
    [TUTORIAL_CARD_KEYS.ANOMALY_TUTORIAL]: {
        isEnabled: false,
    },
    [TUTORIAL_CARD_KEYS.ANNOTATIONS_COUNT_LIMIT]: {
        isEnabled: true,
    },
    [GLOBAL_MODALS_KEYS.WELCOME_MODAL]: {
        isEnabled: false,
    },
    [GLOBAL_MODALS_KEYS.EXHAUSTED_ORGANIZATION_CREDITS_MODAL]: {
        isEnabled: false,
    },
    [FUX_NOTIFICATION_KEYS.ANNOTATE_INTERACTIVELY]: {
        isEnabled: false,
    },
    [FUX_NOTIFICATION_KEYS.ANNOTATOR_AUTO_TRAINING_STARTED]: {
        isEnabled: false,
    },
    [FUX_NOTIFICATION_KEYS.ANNOTATOR_ACTIVE_SET]: {
        isEnabled: false,
    },
    [FUX_NOTIFICATION_KEYS.ANNOTATOR_TOOLS]: {
        isEnabled: false,
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
        isEnabled: false,
    },
    [FUX_NOTIFICATION_KEYS.AUTO_TRAINING_NOTIFICATION]: {
        isEnabled: false,
    },
    [FUX_SETTINGS_KEYS.NEVER_SUCCESSFULLY_AUTOTRAINED]: {
        value: false,
    },
    [FUX_SETTINGS_KEYS.USER_DISMISSED_ALL]: {
        value: false,
    },
    [FUX_SETTINGS_KEYS.NEVER_AUTOTRAINED]: {
        value: false,
    },
    [FUX_SETTINGS_KEYS.NEVER_ANNOTATED]: {
        value: false,
    },
    [FUX_SETTINGS_KEYS.NEVER_CHECKED_PREDICTIONS]: {
        value: false,
    },
    [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINED_PROJECT_ID]: {
        value: null,
    },
    [FUX_SETTINGS_KEYS.FIRST_AUTOTRAINING_JOB_ID]: {
        value: null,
    },
};

export const settings = JSON.stringify(disabledFUXSettings);

export const supportedAlgorithms: OpenApiResponseBody<'GetSupportedAlgorithms'> = {
    supported_algorithms: [
        {
            name: 'U-Net',
            gigaflops: 5.6,
            model_size: 21.1,
            model_template_id: 'U-Net',
            summary: 'This algorithm is only used for testing purposes',
            task_type: 'classification',
            default_algorithm: true,
            lifecycle_stage: 'active',
        },
        {
            name: 'U-Net',
            gigaflops: 5.6,
            model_size: 21.1,
            model_template_id: 'U-Net',
            summary: 'This algorithm is only used for testing purposes',
            task_type: 'segmentation',
            default_algorithm: true,
            lifecycle_stage: 'active',
        },
        {
            name: 'STFPM',
            gigaflops: 5.6,
            model_size: 21.1,
            model_template_id: 'ote_anomaly_classification_stfpm',
            summary: 'Use this model when the position of the objects in the image frame might differ between images.',
            task_type: 'anomaly',
            default_algorithm: true,
            lifecycle_stage: 'active',
        },
        {
            name: 'PADIM',
            gigaflops: 3.9,
            model_size: 168.4,
            model_template_id: 'ote_anomaly_classification_padim',
            summary:
                // eslint-disable-next-line max-len
                'This model is faster and in many cases more accurate, but it requires a fixed position of the objects within the image.',
            task_type: 'anomaly',
            lifecycle_stage: 'active',
        },
        {
            name: 'STFPM',
            gigaflops: 5.6,
            model_size: 21.1,
            model_template_id: 'ote_anomaly_segmentation_stfpm',
            summary: 'Use this model when the position of the objects in the image frame might differ between images.',
            task_type: 'anomaly',
            default_algorithm: true,
            lifecycle_stage: 'active',
        },
        {
            name: 'PADIM',
            gigaflops: 3.9,
            model_size: 168.4,
            model_template_id: 'ote_anomaly_segmentation_padim',
            summary:
                // eslint-disable-next-line max-len
                'This model is faster and in many cases more accurate, but it requires a fixed position of the objects within the image.',
            task_type: 'anomaly',
            lifecycle_stage: 'active',
        },
        {
            name: 'STFPM',
            gigaflops: 5.6,
            model_size: 21.1,
            model_template_id: 'ote_anomaly_detection_stfpm',
            summary: 'Use this model when the position of the objects in the image frame might differ between images.',
            task_type: 'anomaly',
            default_algorithm: true,
            lifecycle_stage: 'active',
        },
        {
            name: 'PADIM',
            gigaflops: 3.9,
            model_size: 168.4,
            model_template_id: 'ote_anomaly_detection_padim',
            summary:
                // eslint-disable-next-line max-len
                'This model is faster and in many cases more accurate, but it requires a fixed position of the objects within the image.',
            task_type: 'anomaly',
            lifecycle_stage: 'active',
        },
        {
            name: 'EfficientNet-V2-S',
            gigaflops: 5.76,
            model_size: 20.23,
            model_template_id: 'Custom_Image_Classification_EfficientNet-V2-S',
            summary: 'Class-Incremental Image Classification for EfficientNet-V2-S',
            task_type: 'classification',
            default_algorithm: true,
            lifecycle_stage: 'active',
        },
        {
            name: 'MobileNet-V3-large-1x',
            gigaflops: 0.44,
            model_size: 4.29,
            model_template_id: 'Custom_Image_Classification_MobileNet-V3-large-1x',
            summary: 'Class-Incremental Image Classification for MobileNet-V3-large-1x',
            task_type: 'classification',
            lifecycle_stage: 'active',
        },
        {
            name: 'EfficientNet-B0',
            gigaflops: 0.81,
            model_size: 4.09,
            model_template_id: 'Custom_Image_Classification_EfficinetNet-B0',
            summary: 'Class-Incremental Image Classification for EfficientNet-B0',
            task_type: 'classification',
            lifecycle_stage: 'active',
        },
        {
            name: 'Lite-HRNet-18-mod2',
            gigaflops: 3.63,
            model_size: 4.8,
            model_template_id: 'Custom_Semantic_Segmentation_Lite-HRNet-18-mod2_OCR',
            summary:
                // eslint-disable-next-line max-len
                'Class-Incremental Semantic Segmentation with middle-sized architecture which based on the Lite-HRNet backbone for the balance between the fast inference and long training.',
            task_type: 'segmentation',
            lifecycle_stage: 'active',
        },
        {
            name: 'Lite-HRNet-s-mod2',
            gigaflops: 1.82,
            model_size: 3.5,
            model_template_id: 'Custom_Semantic_Segmentation_Lite-HRNet-s-mod2_OCR',
            summary:
                // eslint-disable-next-line max-len
                'Class-Incremental Semantic Segmentation with lightweight architecture which based on the Lite-HRNet backbone for the fast inference and training on the limited amount of data.',
            task_type: 'segmentation',
            lifecycle_stage: 'active',
        },
        {
            name: 'Lite-HRNet-x-mod3',
            gigaflops: 13.97,
            model_size: 6.4,
            model_template_id: 'Custom_Semantic_Segmentation_Lite-HRNet-x-mod3_OCR',
            summary:
                // eslint-disable-next-line max-len
                'Class-Incremental Semantic Segmentation with heavy-size architecture which based on the Lite-HRNet backbone for the accurate predictions but long training.',
            task_type: 'segmentation',
            lifecycle_stage: 'active',
        },
        {
            name: 'Lite-HRNet-18',
            gigaflops: 3.45,
            model_size: 4.5,
            model_template_id: 'Custom_Semantic_Segmentation_Lite-HRNet-18_OCR',
            summary:
                // eslint-disable-next-line max-len
                'Class-Incremental Semantic Segmentation with middle-sized architecture which based on the Lite-HRNet backbone for the balance between the fast inference and long training. (deprecated in next version)',
            task_type: 'segmentation',
            lifecycle_stage: 'active',
        },
        {
            name: 'ATSS',
            gigaflops: 20.6,
            model_size: 9.1,
            model_template_id: 'Custom_Object_Detection_Gen3_ATSS',
            summary: 'Class-Incremental Object Detection for ATSS',
            task_type: 'detection',
            default_algorithm: true,
            lifecycle_stage: 'active',
        },
        {
            name: 'SSD',
            gigaflops: 9.4,
            model_size: 7.6,
            model_template_id: 'Custom_Object_Detection_Gen3_SSD',
            summary: 'Class-Incremental Object Detection for SSD',
            task_type: 'detection',
            lifecycle_stage: 'active',
        },
        {
            name: 'YOLOX',
            gigaflops: 6.5,
            model_size: 20.4,
            model_template_id: 'Custom_Object_Detection_YOLOX',
            summary: 'Class-Incremental Object Detection for YOLOX',
            task_type: 'detection',
            lifecycle_stage: 'active',
        },
        {
            name: 'MaskRCNN-ResNet50',
            gigaflops: 533.8,
            model_size: 177.9,
            model_template_id: 'Custom_Counting_Instance_Segmentation_MaskRCNN_ResNet50',
            summary: 'Class-Incremental Instance Segmentation for MaskRCNN-ResNet50',
            task_type: 'instance_segmentation',
            default_algorithm: true,
            lifecycle_stage: 'active',
        },
        {
            name: 'MaskRCNN-EfficientNetB2B',
            gigaflops: 68.48,
            model_size: 13.27,
            model_template_id: 'Custom_Counting_Instance_Segmentation_MaskRCNN_EfficientNetB2B',
            summary: 'Class-Incremental Instance Segmentation for MaskRCNN-EfficientNetB2B',
            task_type: 'instance_segmentation',
            lifecycle_stage: 'active',
        },
        {
            name: 'MaskRCNN-ResNet50',
            gigaflops: 533.8,
            model_size: 177.9,
            model_template_id: 'Custom_Rotated_Detection_via_Instance_Segmentation_MaskRCNN_ResNet50',
            summary: 'Class-Incremental Rotated object detection for MaskRCNN-ResNet50',
            task_type: 'rotated_detection',
            default_algorithm: true,
            lifecycle_stage: 'active',
        },
        {
            name: 'MaskRCNN-EfficientNetB2B',
            gigaflops: 68.48,
            model_size: 13.27,
            model_template_id: 'Custom_Rotated_Detection_via_Instance_Segmentation_MaskRCNN_EfficientNetB2B',
            summary: 'Class-Incremental Rotated object detection for MaskRCNN-EfficientNetB2B',
            task_type: 'rotated_detection',
        },
    ],
};

// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ConfigurableParametersTaskChain } from '@shared/components/configurable-parameters/configurable-parameters.interface';

import {
    ConfigurableParametersDTO,
    ConfigurableParametersTaskChainDTO,
} from '../dtos/configurable-parameters.interface';
import { getConfigParametersEntity, getModelConfigEntity } from './utils';

export const mockedConfigTaskChainDTO: ConfigurableParametersTaskChainDTO = {
    task_id: 'task-id',
    task_title: 'Detection',
    components: [
        {
            id: '60e7f85a9372f15304f88eb9',
            header: 'Configuration For A Segmentation Task',
            description: 'Configuration for a segmentation task',
            entity_identifier: {
                workspace_id: '60e7f858191ae547c0a701de',
                project_id: '60e7f858191ae547c0a701e3',
                component: 'DATASET_COUNTER',
                task_id: '60e7f858191ae547c0a701e8',
                type: 'COMPONENT_PARAMETERS',
            },
            groups: [
                {
                    header: 'Data Augmentation',
                    description: 'Data Augmentation',
                    type: 'PARAMETER_GROUP',
                    name: 'data-augmentation',
                    parameters: [
                        {
                            value: 'ImageNet',
                            default_value: 'ImageNet',
                            name: 'image-net',
                            description: 'Options for data augmentation policies.',
                            header: 'Auto augment option',
                            warning: null,
                            editable: true,
                            template_type: 'selectable',
                            data_type: 'string',
                            options: ['None', 'ImageNet', 'cifar10', 'svhn'],
                        },
                        {
                            value: 90,
                            default_value: 90,
                            description:
                                // eslint-disable-next-line max-len
                                'Degrees of rotation that the image will be rotated left and right. This is only used if automatic augmentations are disabled.',
                            header: 'Rotation range of augmented image',
                            name: 'rotation-range-of-augmented-image',
                            warning: null,
                            editable: true,
                            data_type: 'integer',
                            template_type: 'input',
                            min_value: 0,
                            max_value: 180,
                        },
                        {
                            value: 0.2,
                            default_value: 0.2,
                            description:
                                // eslint-disable-next-line max-len
                                'Amount of positive and negative scaling. Implemented as (1-amount, 1+amount). This is only used if automatic augmentations are disabled.',
                            header: 'Scaling range of augmented image',
                            warning: null,
                            editable: true,
                            data_type: 'float',
                            template_type: 'input',
                            name: 'scaling-range-of-augmented-image',
                            min_value: 0,
                            max_value: 0.99,
                        },
                    ],
                },
                {
                    header: 'Learning Architecture',
                    description: 'Learning Architecture',
                    type: 'PARAMETER_GROUP',
                    name: 'learning-architecture',
                    parameters: [
                        {
                            value: 'U-Net',
                            default_value: 'U-Net',
                            description: 'Switch between U-Net, DeepLab V3 or Fastseg network architecture',
                            header: 'Model architecture',
                            warning: null,
                            editable: true,
                            template_type: 'selectable',
                            data_type: 'string',
                            name: 'model-architecutre',
                            options: ['U-Net', 'DeepLab V3', 'Fastseg'],
                        },
                    ],
                },
                {
                    header: 'Postprocessing',
                    description: 'Postprocessing',
                    type: 'PARAMETER_GROUP',
                    name: 'postprocessing',
                    parameters: [
                        {
                            value: 5,
                            default_value: 5,
                            description:
                                'With a higher value, the segmentation output will be smoother, but less accurate.',
                            header: 'Blur strength',
                            warning: null,
                            editable: true,
                            data_type: 'integer',
                            template_type: 'input',
                            name: 'blur-strength',
                            min_value: 1,
                            max_value: 25,
                        },
                        {
                            value: true,
                            default_value: true,
                            description:
                                // eslint-disable-next-line max-len
                                'For larger images or images with many annotations, disabling this setting increases speed of generating results, at the cost of less smooth predictions.',
                            header: 'Generate full size predictions',
                            warning: null,
                            editable: true,
                            data_type: 'boolean',
                            template_type: 'selectable',
                            name: 'generate-full-size-predictions',
                        },
                        {
                            value: 0.5,
                            default_value: 0.5,
                            description:
                                // eslint-disable-next-line max-len
                                'The threshold to apply to the probability output of the model, for each pixel. A higher value means a stricter segmentation prediction.',
                            header: 'Soft threshold',
                            warning: null,
                            editable: true,
                            data_type: 'float',
                            template_type: 'input',
                            name: 'soft-threshold',
                            min_value: 0,
                            max_value: 1,
                        },
                    ],
                },
                {
                    header: 'Preprocessing',
                    description: 'Preprocessing',
                    type: 'PARAMETER_GROUP',
                    name: 'preprocessing',
                    parameters: [
                        {
                            value: false,
                            default_value: false,
                            description:
                                // eslint-disable-next-line max-len
                                'Enable this option to automatically determine the image size for the network based on the size of the images. The automatic image size is never larger than the settings for Image width and Image height.',
                            header: 'Automatic image size',
                            warning: null,
                            editable: true,
                            data_type: 'boolean',
                            name: 'automatic-image-size',
                            template_type: 'selectable',
                        },
                        {
                            value: 512,
                            default_value: 512,
                            description:
                                // eslint-disable-next-line max-len
                                'Images will be resized to this height before being propagated through the network. If automatic image size is enabled, the image will be resized up to a maximum of the width and height settings.',
                            header: 'Image height',
                            warning:
                                // eslint-disable-next-line max-len
                                'Increasing this value may cause the system to use more memory than available, potentially causing out of memory errors, please update with caution.',
                            editable: true,
                            template_type: 'selectable',
                            data_type: 'integer',
                            name: 'image-height',
                            options: [256, 320, 384, 512, 640, 768, 1024],
                        },
                        {
                            value: 512,
                            default_value: 512,
                            description:
                                // eslint-disable-next-line max-len
                                'Images will be resized to this width before being propagated through the network. If automatic image size is enabled, the image will be resized up to a maximum of the width and height settings.',
                            header: 'Image width',
                            warning:
                                // eslint-disable-next-line max-len
                                'Increasing this value may cause the system to use more memory than available, potentially causing out of memory errors, please update with caution.',
                            editable: true,
                            template_type: 'selectable',
                            data_type: 'integer',
                            name: 'image-width',
                            options: [256, 320, 385, 512, 640, 768, 1024],
                        },
                    ],
                },
            ],
        },
        {
            id: '60e7f8599372f15304f88eb7',
            header: 'Subset Splitting',
            description: 'Specify the distribution of annotated samples over the training, validation and test sets.',
            entity_identifier: {
                workspace_id: '60e7f858191ae547c0a701de1',
                project_id: '60e7f858191ae547c0a701e31',
                component: 'DATASET_COUNTER',
                task_id: '60e7f858191ae547c0a701e81',
                type: 'COMPONENT_PARAMETERS',
            },
            groups: [
                {
                    header: 'U-Net settings',
                    description: 'U-Net settings',
                    type: 'PARAMETER_GROUP',
                    name: 'u-net-settings',
                    parameters: [
                        {
                            value: 3,
                            default_value: 3,
                            description:
                                'The number of layers in the network. Increasing this value will require more memory.',
                            header: 'Network depth',
                            warning:
                                // eslint-disable-next-line max-len
                                'Increasing this value may cause the system to use more memory than available, potentially causing out of memory errors, please update with caution.',
                            editable: true,
                            data_type: 'integer',
                            template_type: 'input',
                            name: 'network-depth',
                            min_value: 2,
                            max_value: 6,
                        },
                        {
                            value: false,
                            default_value: false,
                            description:
                                // eslint-disable-next-line max-len
                                'Enable this option if the dataset contains only grayscale images. This is not necessary, but it can improve training speed.',
                            header: 'Grayscale image',
                            warning: null,
                            editable: true,
                            data_type: 'boolean',
                            template_type: 'selectable',
                            name: 'grayscale-image',
                        },
                        {
                            value: 'InstanceNorm',
                            default_value: 'InstanceNorm',
                            description: 'The normalization method used during training of the network.',
                            header: 'Normalization method',
                            warning: null,
                            editable: true,
                            template_type: 'selectable',
                            data_type: 'string',
                            name: 'normalization-method',
                            options: ['InstanceNorm', 'BatchNorm'],
                        },
                        {
                            value: 5,
                            default_value: 5,
                            description:
                                // eslint-disable-next-line max-len
                                'Increasing this value will increase the number of learnable parameters in the network, which requires more memory.',
                            header: 'Initial number of filters, 2^value',
                            warning:
                                // eslint-disable-next-line max-len
                                'Increasing this value may cause the system to use more memory than available, potentially causing out of memory errors, please update with caution.',
                            editable: true,
                            data_type: 'integer',
                            template_type: 'input',
                            name: 'initial-number-of-filters',
                            min_value: 2,
                            max_value: 6,
                        },
                    ],
                },
            ],
        },
        {
            id: '60e7f8599372f15304f88eb6',
            header: 'Dataset Management',
            description: 'Specify the configuration for dataset management in the system.',
            entity_identifier: {
                workspace_id: '60e7f858191ae547c0a701de2',
                project_id: '60e7f858191ae547c0a701e32',
                component: 'DATASET_COUNTER2',
                task_id: '60e7f858191ae547c0a701e82',
                type: 'COMPONENT_PARAMETERS',
            },
            groups: [
                {
                    header: 'DeepLab V3 settings',
                    description: 'DeepLab V3 settings',
                    name: 'deeplab-v3-settings',
                    type: 'PARAMETER_GROUP',
                    parameters: [
                        {
                            value: 'ResNet 50',
                            default_value: 'ResNet 50',
                            description:
                                // eslint-disable-next-line max-len
                                'This controls which classification model to use as backbone for the DeepLab model. ResNet 101 may lead to better segmentation performance than ResNet 50, but has higher memory requirements.',
                            header: 'Backbone',
                            warning:
                                // eslint-disable-next-line max-len
                                'ResNet 101 has higher memory requirements than ResNet 50. Switching to ResNet 101 may cause out of memory errors.',
                            editable: true,
                            template_type: 'selectable',
                            data_type: 'string',
                            name: 'backbone',
                            options: ['ResNet 101', 'ResNet 50'],
                        },
                        {
                            value: true,
                            default_value: true,
                            description:
                                // eslint-disable-next-line max-len
                                'Enable this option to initialize the network with weights that are pretrained on the COCO dataset.',
                            header: 'Use pretrained weights',
                            warning: null,
                            editable: true,
                            data_type: 'boolean',
                            template_type: 'selectable',
                            name: 'use-pretrained-weights',
                        },
                    ],
                },
            ],
        },
        {
            id: '60e7f8599372f15304f88eb8',
            entity_identifier: {
                workspace_id: '60e7f858191ae547c0a701de3',
                project_id: '60e7f858191ae547c0a701e33',
                component: 'DATASET_COUNTER',
                task_id: '60e7f858191ae547c0a701e83',
                type: 'COMPONENT_PARAMETERS',
            },
            header: 'Optimization By POT',
            description: 'Optimization by POT',
            parameters: [
                {
                    value: false,
                    default_value: false,
                    description:
                        // eslint-disable-next-line max-len
                        'If this is ON, the first training will only be triggered when each label is present in N images, while N is number of required images for the first training. Otherwise, first training will be triggered when N images have been annotated. If first training has been triggered, this parameter will not take effect.',
                    header: 'Label constraint for the first training',
                    warning: null,
                    editable: true,
                    data_type: 'boolean',
                    template_type: 'selectable',
                    name: 'label-constraint-for-the-first-training',
                },
                {
                    value: 12,
                    default_value: 12,
                    description: 'Default integer description',
                    header: 'Number of images required for the first training',
                    warning: null,
                    editable: true,
                    data_type: 'integer',
                    template_type: 'input',
                    name: 'number-of-images-required',
                    min_value: 3,
                    max_value: 10000,
                },
                {
                    value: 6,
                    default_value: 6,
                    description:
                        // eslint-disable-next-line max-len
                        'The minimum number of new annotations required before auto-train is triggered. This is applicable after one successful training round.',
                    header: 'Number of images required for retraining',
                    warning: null,
                    editable: true,
                    data_type: 'integer',
                    template_type: 'input',
                    name: 'number-of-images-required',
                    min_value: 6,
                    max_value: 10000,
                },
            ],
        },
        {
            id: '60e7f45a9372f15304f88eb2',
            header: 'Learning Parameters',
            description: 'Learning Parameters',
            entity_identifier: {
                group_name: 'learning_parameters',
                model_storage_id: '6193c24ed1f15d80895d99b2',
                type: 'HYPER_PARAMETER_GROUP',
                workspace_id: '61938a645055d2dc122f5720',
            },
            parameters: [
                {
                    value: 5,
                    default_value: 5,
                    description:
                        // eslint-disable-next-line max-len
                        'The number of training samples seen in each iteration of training. Increasing this value improves training time and may make the training more stable. A larger batch size has higher memory requirements.',
                    header: 'Batch size',
                    warning:
                        // eslint-disable-next-line max-len
                        'Increasing this value may cause the system to use more memory than available, potentially causing out of memory errors, please update with caution.',
                    editable: true,
                    data_type: 'integer',
                    template_type: 'input',
                    name: 'batch-size',
                    min_value: 2,
                    max_value: 64,
                },
                {
                    value: 30,
                    default_value: 30,
                    description:
                        'Number of epochs without improvement before the system will automatically stop training.',
                    header: 'Early stopping patience',
                    warning: null,
                    editable: true,
                    data_type: 'integer',
                    template_type: 'input',
                    name: 'early-stopping-patience',
                    min_value: 1,
                    max_value: 500,
                },
                {
                    value: 0.001,
                    default_value: 0.001,
                    description: 'Increasing this value will speed up training convergence but might make it unstable.',
                    header: 'Learning rate',
                    warning: null,
                    editable: true,
                    data_type: 'float',
                    template_type: 'input',
                    name: 'learning-rate',
                    min_value: 0.000001,
                    max_value: 0.01,
                },
                {
                    value: true,
                    default_value: true,
                    description:
                        // eslint-disable-next-line max-len
                        'If this setting is enabled and there is more than one label, the loss value in the network is a weighted average per label. Classes that are underrepresented in the dataset (by number of pixels) get a higher weight. ',
                    header: 'Use weighted loss',
                    warning: null,
                    editable: true,
                    data_type: 'boolean',
                    template_type: 'selectable',
                    name: 'use-weighted-loss',
                },
                {
                    value: 0,
                    default_value: 0,
                    description:
                        // eslint-disable-next-line max-len
                        'The number of images and/or video frames used for training for each epoch. Setting this to a lower value allows the network to train faster, but it may make the results less robust. Set to 0 to use all annotated images and/or video frames.',
                    header: 'Number of images/frames to use for training per epoch',
                    warning: null,
                    editable: true,
                    data_type: 'integer',
                    template_type: 'input',
                    name: 'number-of-images/frames',
                    min_value: 0,
                    max_value: 10000,
                },
                {
                    value: 40,
                    default_value: 40,
                    description:
                        'Increasing this value causes the results to be more robust but training time will be longer.',
                    header: 'Number of epochs',
                    warning: null,
                    editable: true,
                    data_type: 'integer',
                    template_type: 'input',
                    name: 'number-of-epochs',
                    min_value: 1,
                    max_value: 1000,
                },
                {
                    value: 0,
                    default_value: 0,
                    description:
                        // eslint-disable-next-line max-len
                        'Increasing this value might improve training speed however it might cause out of memory errors. If the number of workers is set to zero, data loading will happen in the main training thread.',
                    header: 'Number of cpu threads to use during batch generation',
                    warning: null,
                    editable: true,
                    data_type: 'integer',
                    template_type: 'input',
                    name: 'number-of-cpu',
                    min_value: 0,
                    max_value: 8,
                },
            ],
        },
    ],
};

export const mockedReadOnlyConfigTaskChainData: ConfigurableParametersTaskChain =
    getModelConfigEntity(mockedConfigTaskChainDTO);

export const mockedEditableConfigTaskChainData: ConfigurableParametersTaskChain = getModelConfigEntity(
    mockedConfigTaskChainDTO,
    true
);

export const mockedConfigParamDTO: ConfigurableParametersDTO = {
    global: [
        {
            id: '615f02ffa7318ebbed32d6e7',
            description: 'Specify the configuration for project level coordination.',
            header: 'Coordination',
            type: 'CONFIGURABLE_PARAMETERS',
            entity_identifier: {
                workspace_id: '60e7f858191ae547c0a701de',
                project_id: '60e7f858191ae547c0a701e3',
                component: 'DATASET_COUNTER',
                task_id: '60e7f858191ae547c0a701e8',
                type: 'COMPONENT_PARAMETERS',
            },
            parameters: [
                {
                    value: 'ImageNet',
                    default_value: 'ImageNet',
                    name: 'image-net',
                    description: 'Options for data augmentation policies.',
                    header: 'Auto augment option',
                    warning: null,
                    editable: true,
                    template_type: 'selectable',
                    data_type: 'string',
                    options: ['None', 'ImageNet', 'cifar10', 'svhn'],
                },
                {
                    value: 90,
                    default_value: 90,
                    description:
                        // eslint-disable-next-line max-len
                        'Degrees of rotation that the image will be rotated left and right. This is only used if automatic augmentations are disabled.',
                    header: 'Rotation range of augmented image',
                    name: 'rotation-range-of-augmented-image',
                    warning: null,
                    editable: true,
                    data_type: 'integer',
                    template_type: 'input',
                    min_value: 0,
                    max_value: 180,
                },
            ],
        },
    ],
    task_chain: [mockedConfigTaskChainDTO],
};

export const mockedConfigParamData: ConfigurableParametersTaskChain[] = getConfigParametersEntity(mockedConfigParamDTO);

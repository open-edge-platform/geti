// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.
export const segmentationConfigurationMock = {
    global: [
        {
            description: 'Specify the project-level configuration for active learning.',
            entity_identifier: {
                component: 'PROJECT_ACTIVE_LEARNING',
                project_id: '64e32726d4842bb3c2a82d0c',
                type: 'COMPONENT_PARAMETERS',
                workspace_id: '64c8a6e6d4842bb3c2a8063e',
            },
            header: 'Active Learning',
            id: '64e32727d6ddaa1a15243a41',
            parameters: [
                {
                    data_type: 'string',
                    default_value: 'mean',
                    description: 'Function to aggregate the active scores of a media across the tasks',
                    editable: true,
                    enum_name: 'ActiveScoreReductionFunction',
                    header: 'Inter-task scores reduction function',
                    name: 'inter_task_reduce_fn',
                    options: ['min', 'mean', 'max'],
                    template_type: 'selectable',
                    ui_rules: {},
                    value: 'mean',
                    warning: null,
                },
                {
                    data_type: 'integer',
                    default_value: 500,
                    description: 'Number of images analysed after training for active learning',
                    editable: true,
                    header: 'Number of images analysed after training for active learning',
                    max_value: 10000,
                    min_value: 10,
                    name: 'max_unseen_media',
                    template_type: 'input',
                    ui_rules: {},
                    value: 500,
                    warning: null,
                },
            ],
            type: 'CONFIGURABLE_PARAMETERS',
        },
        {
            description: 'Specify parameters to control how datasets are managed in the system.',
            entity_identifier: {
                component: 'PIPELINE_DATASET_MANAGER',
                project_id: '64e32726d4842bb3c2a82d0c',
                type: 'COMPONENT_PARAMETERS',
                workspace_id: '64c8a6e6d4842bb3c2a8063e',
            },
            header: 'Dataset management',
            id: '64e32727d6ddaa1a15243a45',
            parameters: [
                {
                    data_type: 'boolean',
                    default_value: false,
                    description:
                        'Enabling NDR will help to prevent annotating very similar images. Note that this does not ' +
                        'remove any data from the project,it is only used in selecting images for active learning.',
                    editable: true,
                    header: 'Use Near Duplicate Removal (NDR) for active learning',
                    name: 'use_ndr',
                    template_type: 'input',
                    ui_rules: {},
                    value: false,
                    warning: null,
                },
            ],
            type: 'CONFIGURABLE_PARAMETERS',
        },
    ],
    task_chain: [
        {
            components: [
                {
                    description: 'Learning Parameters',
                    entity_identifier: {
                        group_name: 'learning_parameters',
                        model_storage_id: '64e32726d4842bb3c2a82d11',
                        type: 'HYPER_PARAMETER_GROUP',
                        workspace_id: '64c8a6e6d4842bb3c2a8063e',
                    },
                    header: 'Learning Parameters',
                    id: '64e32727d6ddaa1a15243a46-1',
                    name: 'learning_parameters',
                    parameters: [
                        {
                            data_type: 'boolean',
                            default_value: true,
                            description:
                                'Find a proper batch size by training for an ' +
                                'iteration with various batch size a few times.',
                            editable: true,
                            header: "Decrease batch size if current batch size isn't fit to CUDA memory.",
                            name: 'auto_decrease_batch_size',
                            template_type: 'input',
                            ui_rules: {},
                            value: true,
                            warning:
                                'Enabling this option could reduce the actual batch size if the current setting ' +
                                'results in out-of-memory error. The learning rate also could be adjusted according ' +
                                'to the adapted batch size. This process might take some extra computation time ' +
                                'to try a few batch size candidates.',
                        },
                        {
                            data_type: 'integer',
                            default_value: 4,
                            description:
                                'The number of training samples seen in each iteration of training. Increasing ' +
                                'this value improves training time and may make the training more stable. ' +
                                'A larger batch size has higher memory requirements.',
                            editable: true,
                            header: 'Batch size',
                            max_value: 512,
                            min_value: 1,
                            name: 'batch_size',
                            template_type: 'input',
                            ui_rules: {},
                            value: 4,
                            warning:
                                'Increasing this value may cause the system to use more memory than available, ' +
                                'potentially causing out of memory errors, please update with caution.',
                        },
                        {
                            data_type: 'integer',
                            default_value: 0,
                            description:
                                'Training will stop if the model does not improve within the number of ' +
                                'iterations of patience. This ensures the model is trained enough with the number ' +
                                'of iterations of patience before early stopping.',
                            editable: true,
                            header: 'Iteration patience for early stopping',
                            max_value: 1000,
                            min_value: 0,
                            name: 'early_stop_iteration_patience',
                            template_type: 'input',
                            ui_rules: {},
                            value: 0,
                            warning: 'This is applied exclusively when early stopping is enabled.',
                        },
                        {
                            data_type: 'integer',
                            default_value: 10,
                            description:
                                'Training will stop if the model does not improve ' +
                                'within the number of epochs of patience.',
                            editable: true,
                            header: 'Patience for early stopping',
                            max_value: 50,
                            min_value: 0,
                            name: 'early_stop_patience',
                            template_type: 'input',
                            ui_rules: {},
                            value: 10,
                            warning: 'This is applied exclusively when early stopping is enabled.',
                        },
                        {
                            data_type: 'boolean',
                            default_value: true,
                            description:
                                "Early exit from training when validation accuracy isn't " +
                                'changed or decreased for several epochs.',
                            editable: true,
                            header: 'Enable early stopping of the training',
                            name: 'enable_early_stopping',
                            template_type: 'input',
                            ui_rules: {},
                            value: true,
                            warning: null,
                        },
                        {
                            data_type: 'float',
                            default_value: 0.001,
                            description:
                                'Increasing this value will speed up training convergence but might make it unstable.',
                            editable: true,
                            header: 'Learning rate',
                            max_value: 0.1,
                            min_value: 1e-7,
                            name: 'learning_rate',
                            template_type: 'input',
                            ui_rules: {},
                            value: 0.001,
                            warning: null,
                        },
                        {
                            data_type: 'integer',
                            default_value: 100,
                            description: '',
                            editable: true,
                            header: 'Number of iterations for learning rate warmup',
                            max_value: 10000,
                            min_value: 0,
                            name: 'learning_rate_warmup_iters',
                            template_type: 'input',
                            ui_rules: {},
                            value: 100,
                            warning: null,
                        },
                        {
                            data_type: 'integer',
                            default_value: 5,
                            description: '',
                            editable: true,
                            header: 'Number of checkpoints that is done during the single training round',
                            max_value: 100,
                            min_value: 1,
                            name: 'num_checkpoints',
                            template_type: 'input',
                            ui_rules: {},
                            value: 5,
                            warning: null,
                        },
                        {
                            data_type: 'integer',
                            default_value: 100,
                            description:
                                'Increasing this value causes the results to be more ' +
                                'robust but training time will be longer.',
                            editable: true,
                            header: 'Number of training iterations',
                            max_value: 100000,
                            min_value: 1,
                            name: 'num_iters',
                            template_type: 'input',
                            ui_rules: {},
                            value: 100,
                            warning: null,
                        },
                        {
                            data_type: 'integer',
                            default_value: 0,
                            description:
                                'Increasing this value might improve training speed however ' +
                                'it might cause out of memory errors. If the number of workers is set to zero, ' +
                                'data loading will happen in the main training thread.',
                            editable: true,
                            header: 'Number of cpu threads to use during batch generation',
                            max_value: 8,
                            min_value: 0,
                            name: 'num_workers',
                            template_type: 'input',
                            ui_rules: {},
                            value: 0,
                            warning: null,
                        },
                        {
                            data_type: 'boolean',
                            default_value: true,
                            description:
                                'Depending on the size of iteration per epoch, adaptively ' +
                                'update the validation interval and related values.',
                            editable: true,
                            header: 'Use adaptive validation interval',
                            name: 'use_adaptive_interval',
                            template_type: 'input',
                            ui_rules: {},
                            value: true,
                            warning:
                                'This will automatically control the patience and ' +
                                'interval when early stopping is enabled.',
                        },
                    ],
                    type: 'PARAMETER_GROUP',
                },
                {
                    description: 'Optimization by NNCF',
                    entity_identifier: {
                        group_name: 'nncf_optimization',
                        model_storage_id: '64e32726d4842bb3c2a82d11',
                        type: 'HYPER_PARAMETER_GROUP',
                        workspace_id: '64c8a6e6d4842bb3c2a8063e',
                    },
                    header: 'Optimization by NNCF',
                    id: '64e32727d6ddaa1a15243a46-2',
                    name: 'nncf_optimization',
                    parameters: [
                        {
                            data_type: 'float',
                            default_value: 1.0,
                            description: 'The maximal allowed accuracy metric drop in absolute values',
                            editable: true,
                            header: 'Maximum accuracy degradation',
                            max_value: 100.0,
                            min_value: 0.0,
                            name: 'maximal_accuracy_degradation',
                            template_type: 'input',
                            ui_rules: {},
                            value: 1.0,
                            warning: null,
                        },
                    ],
                    type: 'PARAMETER_GROUP',
                },
                {
                    description: 'Postprocessing',
                    entity_identifier: {
                        group_name: 'postprocessing',
                        model_storage_id: '64e32726d4842bb3c2a82d11',
                        type: 'HYPER_PARAMETER_GROUP',
                        workspace_id: '64c8a6e6d4842bb3c2a8063e',
                    },
                    header: 'Postprocessing',
                    id: '64e32727d6ddaa1a15243a46-3',
                    name: 'postprocessing',
                    parameters: [
                        {
                            data_type: 'float',
                            default_value: 0.35,
                            description:
                                'This threshold only takes effect if the threshold is not set based on the result.',
                            editable: true,
                            header: 'Confidence threshold',
                            max_value: 1,
                            min_value: 0,
                            name: 'confidence_threshold',
                            template_type: 'input',
                            ui_rules: {},
                            value: 0.35,
                            warning: null,
                        },
                        {
                            data_type: 'boolean',
                            default_value: true,
                            description: 'Confidence threshold is derived from the results',
                            editable: true,
                            header: 'Result based confidence threshold',
                            name: 'result_based_confidence_threshold',
                            template_type: 'input',
                            ui_rules: {},
                            value: true,
                            warning: null,
                        },
                        {
                            data_type: 'boolean',
                            default_value: false,
                            description: 'Use direct ellipse shape in inference instead of polygon from mask',
                            editable: true,
                            header: 'Use ellipse shapes',
                            name: 'use_ellipse_shapes',
                            template_type: 'input',
                            ui_rules: {},
                            value: false,
                            warning: null,
                        },
                    ],
                    type: 'PARAMETER_GROUP',
                },
                {
                    description: 'POT Parameters',
                    entity_identifier: {
                        group_name: 'pot_parameters',
                        model_storage_id: '64e32726d4842bb3c2a82d11',
                        type: 'HYPER_PARAMETER_GROUP',
                        workspace_id: '64c8a6e6d4842bb3c2a8063e',
                    },
                    header: 'POT Parameters',
                    id: '64e32727d6ddaa1a15243a46-4',
                    name: 'pot_parameters',
                    parameters: [
                        {
                            data_type: 'string',
                            default_value: 'Performance',
                            description: 'Quantization preset that defines quantization scheme',
                            editable: true,
                            enum_name: 'POTQuantizationPreset',
                            header: 'Preset',
                            name: 'preset',
                            options: ['Mixed', 'Performance'],
                            template_type: 'selectable',
                            ui_rules: {},
                            value: 'Performance',
                            warning: null,
                        },
                        {
                            data_type: 'integer',
                            default_value: 300,
                            description: 'Number of data samples used for post-training optimization',
                            editable: true,
                            header: 'Number of data samples',
                            max_value: 9223372036854775807,
                            min_value: 1,
                            name: 'stat_subset_size',
                            template_type: 'input',
                            ui_rules: {},
                            value: 300,
                            warning: null,
                        },
                    ],
                    type: 'PARAMETER_GROUP',
                },
                {
                    description: 'Crop dataset to tiles',
                    entity_identifier: {
                        group_name: 'tiling_parameters',
                        model_storage_id: '64e32726d4842bb3c2a82d11',
                        type: 'HYPER_PARAMETER_GROUP',
                        workspace_id: '64c8a6e6d4842bb3c2a8063e',
                    },
                    header: 'Tiling',
                    id: '64e32727d6ddaa1a15243a46-5',
                    name: 'tiling_parameters',
                    parameters: [
                        {
                            data_type: 'boolean',
                            default_value: true,
                            description:
                                'Config tile size and tile overlap adaptively based on annotated dataset statistic. ' +
                                "Manual settings well be ignored if it's turned on. Please turn off this option in " +
                                'order to tune tiling parameters manually.',
                            editable: true,
                            header: 'Enable adaptive tiling parameters',
                            name: 'enable_adaptive_params',
                            template_type: 'input',
                            ui_rules: {},
                            value: true,
                            warning: null,
                        },
                        {
                            data_type: 'boolean',
                            default_value: false,
                            description:
                                'Enabling tile classifier enhances the speed of tiling inference by incorporating a ' +
                                'tile classifier into the instance segmentation model. This feature prevents the ' +
                                'detector from making predictions on tiles that do not contain any objects, ' +
                                'thus optimizing its speed performance.',
                            editable: true,
                            header: 'Enable tile classifier',
                            name: 'enable_tile_classifier',
                            template_type: 'input',
                            ui_rules: {},
                            value: false,
                            warning:
                                'The tile classifier prioritizes inference speed over training speed, ' +
                                'it requires more training in order to achieve its optimized performance.',
                        },
                        {
                            data_type: 'boolean',
                            default_value: false,
                            description: 'Set to True to allow tiny objects to be better detected.',
                            editable: true,
                            header: 'Enable tiling',
                            name: 'enable_tiling',
                            template_type: 'input',
                            ui_rules: {},
                            value: false,
                            warning:
                                'Tiling trades off speed for accuracy as it increases the number of images to be ' +
                                "processed. In turn, it's memory efficient as smaller resolution patches are handled " +
                                'at onces so that the possibility of OOM issues could be reduced. Important: ' +
                                'In the current version, depending on the dataset size and the available ' +
                                'hardware resources, a model may not train successfully when tiling is enabled.',
                        },
                        {
                            data_type: 'float',
                            default_value: 2.0,
                            description:
                                'The purpose of the scale parameter is to optimize the performance and efficiency ' +
                                'of tiling in OpenVINO IR during inference. By controlling the increase in tile ' +
                                'size and input size, the scale parameter allows for more efficient parallelization ' +
                                'of the workload and improve the overall performance and efficiency of the ' +
                                'inference process on OpenVINO.',
                            editable: true,
                            header: 'OpenVINO IR Scale Factor',
                            max_value: 4.0,
                            min_value: 1.0,
                            name: 'tile_ir_scale_factor',
                            template_type: 'input',
                            ui_rules: {},
                            value: 2.0,
                            warning: null,
                        },
                        {
                            data_type: 'integer',
                            default_value: 1500,
                            description: 'Maximum number of objects per tile',
                            editable: true,
                            header: 'Max object per tile',
                            max_value: 5000,
                            min_value: 1,
                            name: 'tile_max_number',
                            template_type: 'input',
                            ui_rules: {},
                            value: 1500,
                            warning: null,
                        },
                        {
                            data_type: 'float',
                            default_value: 0.2,
                            description:
                                'Overlap ratio between each two neighboring tiles. Recommend to set as ' +
                                'large_object_size / tile_size.',
                            editable: true,
                            header: 'Tile Overlap',
                            max_value: 0.9,
                            min_value: 0.0,
                            name: 'tile_overlap',
                            template_type: 'input',
                            ui_rules: {},
                            value: 0.2,
                            warning: null,
                        },
                        {
                            data_type: 'float',
                            default_value: 1.0,
                            description:
                                'Since tiling train and validation to all tile from large image, usually it takes ' +
                                'lots of time than normal training. The tile_sampling_ratio is ratio for sampling ' +
                                'entire tile dataset. Sampling tile dataset would save lots of time for training ' +
                                'and validation time. Note that sampling will be applied to training and ' +
                                'validation dataset, not test dataset.',
                            editable: true,
                            header: 'Sampling Ratio for entire tiling',
                            max_value: 1.0,
                            min_value: 1e-6,
                            name: 'tile_sampling_ratio',
                            template_type: 'input',
                            ui_rules: {},
                            value: 1.0,
                            warning: null,
                        },
                        {
                            data_type: 'integer',
                            default_value: 400,
                            description:
                                'Tile image size. (tile_size x tile_size) sub images will be the unit of computation.',
                            editable: true,
                            header: 'Tile Image Size',
                            max_value: 4096,
                            min_value: 100,
                            name: 'tile_size',
                            template_type: 'input',
                            ui_rules: {},
                            value: 400,
                            warning: null,
                        },
                    ],
                    type: 'PARAMETER_GROUP',
                },
                {
                    description:
                        'Specify the distribution of annotated samples over the training, validation and test sets. ' +
                        'Note: items that have already been trained will stay in the same subset even if ' +
                        'these parameters are changed.',
                    entity_identifier: {
                        component: 'SUBSET_MANAGER',
                        project_id: '64e32726d4842bb3c2a82d0c',
                        task_id: '64e32726d4842bb3c2a82d10',
                        type: 'COMPONENT_PARAMETERS',
                        workspace_id: '64c8a6e6d4842bb3c2a8063e',
                    },
                    groups: [
                        {
                            description:
                                'Specify the distributions of annotated samples over training, validation and test ' +
                                'set. These values must add up to 1, and will be rescaled if they ' +
                                'do not add up correctly.',
                            header: 'Subset distribution',
                            name: 'subset_parameters',
                            parameters: [
                                {
                                    data_type: 'float',
                                    default_value: 0.3,
                                    description: 'Fraction of annotated data that will be assigned to the test set',
                                    editable: true,
                                    header: 'Test set proportion',
                                    max_value: 1.0,
                                    min_value: 0.1,
                                    name: 'test_proportion',
                                    template_type: 'input',
                                    ui_rules: {
                                        action: 'SHOW',
                                        operator: 'AND',
                                        rules: [
                                            {
                                                operator: 'EQUAL_TO',
                                                parameter: ['auto_subset_fractions'],
                                                type: 'RULE',
                                                value: false,
                                            },
                                        ],
                                        type: 'UI_RULES',
                                    },
                                    value: 0.3,
                                    warning:
                                        'When the proportions do not add up to 1, ' +
                                        'they will be rescaled to add up to 1.',
                                },
                                {
                                    data_type: 'float',
                                    default_value: 0.5,
                                    description: 'Fraction of annotated data that will be assigned to the training set',
                                    editable: true,
                                    header: 'Training set proportion',
                                    max_value: 1.0,
                                    min_value: 0.1,
                                    name: 'train_proportion',
                                    template_type: 'input',
                                    ui_rules: {
                                        action: 'SHOW',
                                        operator: 'AND',
                                        rules: [
                                            {
                                                operator: 'EQUAL_TO',
                                                parameter: ['auto_subset_fractions'],
                                                type: 'RULE',
                                                value: false,
                                            },
                                        ],
                                        type: 'UI_RULES',
                                    },
                                    value: 0.5,
                                    warning:
                                        'When the proportions do not add up to 1, ' +
                                        'they will be rescaled to add up to 1.',
                                },
                                {
                                    data_type: 'float',
                                    default_value: 0.2,
                                    description:
                                        'Fraction of annotated data that will be assigned to the validation set',
                                    editable: true,
                                    header: 'Validation set proportion',
                                    max_value: 1.0,
                                    min_value: 0.1,
                                    name: 'validation_proportion',
                                    template_type: 'input',
                                    ui_rules: {
                                        action: 'SHOW',
                                        operator: 'AND',
                                        rules: [
                                            {
                                                operator: 'EQUAL_TO',
                                                parameter: ['auto_subset_fractions'],
                                                type: 'RULE',
                                                value: false,
                                            },
                                        ],
                                        type: 'UI_RULES',
                                    },
                                    value: 0.2,
                                    warning:
                                        'When the proportions do not add up to 1, ' +
                                        'they will be rescaled to add up to 1.',
                                },
                            ],
                            type: 'PARAMETER_GROUP',
                        },
                    ],
                    header: 'Subset splitting',
                    id: '64e32727d6ddaa1a15243a3f',
                    parameters: [
                        {
                            data_type: 'boolean',
                            default_value: true,
                            description:
                                'If this setting is enabled, the system will automatically determine the most ' +
                                'optimal distribution of the annotated samples over training, validation and ' +
                                'test set. Disable this setting to manually specify the proportions.',
                            editable: true,
                            header: 'Automatically determine subset proportions',
                            name: 'auto_subset_fractions',
                            template_type: 'input',
                            ui_rules: {},
                            value: true,
                            warning: null,
                        },
                    ],
                    type: 'CONFIGURABLE_PARAMETERS',
                },
                {
                    description: 'Specify the number of required annotations for a task',
                    entity_identifier: {
                        component: 'DATASET_COUNTER',
                        project_id: '64e32726d4842bb3c2a82d0c',
                        task_id: '64e32726d4842bb3c2a82d10',
                        type: 'COMPONENT_PARAMETERS',
                        workspace_id: '64c8a6e6d4842bb3c2a8063e',
                    },
                    header: 'Annotation requirements',
                    id: '64e32727d6ddaa1a15243a40',
                    parameters: [
                        {
                            data_type: 'boolean',
                            default_value: false,
                            description:
                                'If this is ON, the first training will only be triggered when each label is ' +
                                'present in N images, while N is number of required images for the first ' +
                                'training. Otherwise, first training will be triggered when N images have ' +
                                'been annotated. If first training has been triggered, this parameter will ' +
                                'not take effect.',
                            editable: true,
                            header: 'Label constraint for the first training',
                            name: 'label_constraint_first_training',
                            template_type: 'input',
                            ui_rules: {},
                            value: false,
                            warning: null,
                        },
                        {
                            data_type: 'integer',
                            default_value: 12,
                            description:
                                'The minimum number of new annotations required before auto-train is triggered. ' +
                                'Auto-training will start every time that this number of annotations is created.',
                            editable: true,
                            header: 'Number of images required for auto-training',
                            max_value: 10000,
                            min_value: 3,
                            name: 'required_images_auto_training',
                            template_type: 'input',
                            ui_rules: {},
                            value: 12,
                            warning: null,
                        },
                    ],
                    type: 'CONFIGURABLE_PARAMETERS',
                },
                {
                    description: 'Specify the task-level configuration for active learning.',
                    entity_identifier: {
                        component: 'TASK_ACTIVE_LEARNING',
                        project_id: '64e32726d4842bb3c2a82d0c',
                        task_id: '64e32726d4842bb3c2a82d10',
                        type: 'COMPONENT_PARAMETERS',
                        workspace_id: '64c8a6e6d4842bb3c2a8063e',
                    },
                    header: 'Active Learning',
                    id: '64e32727d6ddaa1a15243a42',
                    parameters: [
                        {
                            data_type: 'string',
                            default_value: 'mean',
                            description: 'Function to aggregate the active scores of a media within a task',
                            editable: true,
                            enum_name: 'ActiveScoreReductionFunction',
                            header: 'Intra-task scores reduction function',
                            name: 'intra_task_reduce_fn',
                            options: ['min', 'mean', 'max'],
                            template_type: 'selectable',
                            ui_rules: {},
                            value: 'mean',
                            warning: null,
                        },
                    ],
                    type: 'CONFIGURABLE_PARAMETERS',
                },
                {
                    description: 'General settings for a task.',
                    entity_identifier: {
                        component: 'TASK_NODE',
                        project_id: '64e32726d4842bb3c2a82d0c',
                        task_id: '64e32726d4842bb3c2a82d10',
                        type: 'COMPONENT_PARAMETERS',
                        workspace_id: '64c8a6e6d4842bb3c2a8063e',
                    },
                    header: 'General',
                    id: '64e32727d6ddaa1a15243a44',
                    parameters: [
                        {
                            data_type: 'boolean',
                            default_value: true,
                            description:
                                'Enable to allow the task to start training automatically when it is ready to train.',
                            editable: true,
                            header: 'Auto-training',
                            name: 'auto_training',
                            template_type: 'input',
                            ui_rules: {},
                            value: true,
                            warning: null,
                        },
                    ],
                    type: 'CONFIGURABLE_PARAMETERS',
                },
            ],
            task_id: '64e32726d4842bb3c2a82d10',
            task_title: 'Instance segmentation',
        },
    ],
};

export const yoloAlgorithm = {
    name: 'Yolo',
    task_type: 'detection',
    model_size: 200,
    model_template_id: 'detection_yolo',
    gigaflops: 5,
    summary: 'YOLO architecture for detection',
    default_algorithm: true,
    performance_category: 'speed',
    lifecycle_stage: 'active',
};

export const supportedAlgorithms = {
    supported_algorithms: [
        yoloAlgorithm,
        {
            name: 'SSD',
            task_type: 'detection',
            model_size: 200,
            model_template_id: 'detection_ssd',
            gigaflops: 5,
            summary: 'SSD architecture for detection',
            default_algorithm: false,
            performance_category: 'balance',
            lifecycle_stage: 'active',
        },
    ],
};

export const modelGroups = {
    model_groups: [
        {
            id: '60dc3b8b3fc7834f46ea90d5',
            name: yoloAlgorithm.name,
            task_id: '60db493fd20945a0046f56d2',
            model_template_id: yoloAlgorithm.model_template_id,
            models: [
                {
                    name: 'Model of Yolo',
                    creation_date: '2021-06-30T09:38:19.677000+00:00',
                    id: '60dc3b8b3fc7834f46ea90ag',
                    size: 12813101,
                    version: 1,
                    performance: {
                        score: 0.28953322601318,
                    },
                    label_schema_in_sync: false,
                    score_up_to_date: true,
                    active_model: false,
                },
                {
                    name: 'Model of Yolo',
                    creation_date: '2021-06-30T09:38:19.677000+00:00',
                    id: '60dc3b8b3fc7834f46ea90af',
                    size: 12813101,
                    version: 2,
                    performance: {
                        score: 0.28953322601318,
                    },
                    label_schema_in_sync: true,
                    score_up_to_date: true,
                    active_model: true,
                },
            ],
        },
    ],
};

export const modelGroupResponse = {
    id: '59e94836734b717fbbfe0b79',
    name: 'MobileNetV2-ATSS',
    model_template_id: 'Custom_Object_Detection_Gen3_ATSS',
    task_id: '59e94836734b717fbbfe0b78',
    models: [
        {
            id: '59e96bd31b6b242caaf77a1c',
            name: 'MobileNetV2-ATSS',
            creation_date: '2025-02-25T10:39:22.502000+00:00',
            score_up_to_date: true,
            active_model: true,
            size: 18953637,
            performance: {
                score: 0.7499999999999998,
            },
            label_schema_in_sync: true,
            version: 2,
            purge_info: {
                is_purged: false,
                purge_time: null,
                user_uid: null,
            },
        },
        {
            id: '59e94a8a144cc52ba1424465',
            name: 'MobileNetV2-ATSS',
            creation_date: '2025-02-25T10:39:22.502000+00:00',
            score_up_to_date: true,
            active_model: false,
            size: 28314695,
            performance: {
                score: 0.7499999999999998,
            },
            label_schema_in_sync: true,
            version: 1,
            purge_info: {
                is_purged: false,
                purge_time: null,
                user_uid: null,
            },
        },
    ],
    learning_approach: 'fully_supervised',
    lifecycle_stage: 'active',
};

export const modelDetailsResponse = {
    id: '59e96bd31b6b242caaf77a1c',
    name: 'MobileNetV2-ATSS',
    architecture: 'MobileNetV2-ATSS',
    version: 2,
    creation_date: '2025-02-25T10:39:22.502000+00:00',
    size: 18953637,
    score_up_to_date: true,
    fps_throughput: 0,
    latency: 0,
    performance: {
        score: 0.7499999999999998,
    },
    label_schema_in_sync: true,
    precision: ['FP32'],
    target_device: 'CPU',
    target_device_type: null,
    optimized_models: [
        {
            id: '59e96bd31b6b242caaf77a20',
            name: 'MobileNetV2-ATSS ONNX FP32',
            version: 2,
            creation_date: '2025-02-25T10:39:22.502000+00:00',
            model_format: 'ONNX',
            precision: ['FP32'],
            has_xai_head: false,
            target_device: 'CPU',
            target_device_type: null,
            performance: {
                score: 0.7499999999999998,
            },
            size: 9727970,
            latency: 0,
            fps_throughput: 0,
            optimization_type: 'ONNX',
            optimization_objectives: {},
            model_status: 'SUCCESS',
            configurations: [],
            previous_revision_id: '59e96bd31b6b242caaf77a1c',
            previous_trained_revision_id: '59e96bd31b6b242caaf77a1c',
            optimization_methods: [],
        },
        {
            id: '59e96bd31b6b242caaf77a1f',
            name: 'MobileNetV2-ATSS OpenVINO FP16',
            version: 2,
            creation_date: '2025-02-25T10:39:22.502000+00:00',
            model_format: 'OpenVINO',
            precision: ['FP16'],
            has_xai_head: false,
            target_device: 'CPU',
            target_device_type: null,
            performance: {
                score: 0.7499999999999998,
            },
            size: 5863165,
            latency: 0,
            fps_throughput: 0,
            optimization_type: 'MO',
            optimization_objectives: {},
            model_status: 'SUCCESS',
            configurations: [],
            previous_revision_id: '59e96bd31b6b242caaf77a1c',
            previous_trained_revision_id: '59e96bd31b6b242caaf77a1c',
            optimization_methods: [],
        },
        {
            id: '59e96bd31b6b242caaf77a1e',
            name: 'MobileNetV2-ATSS OpenVINO FP32',
            version: 2,
            creation_date: '2025-02-25T10:39:22.502000+00:00',
            model_format: 'OpenVINO',
            precision: ['FP32'],
            has_xai_head: false,
            target_device: 'CPU',
            target_device_type: null,
            performance: {
                score: 0.7499999999999998,
            },
            size: 10330722,
            latency: 0,
            fps_throughput: 0,
            optimization_type: 'MO',
            optimization_objectives: {},
            model_status: 'SUCCESS',
            configurations: [],
            previous_revision_id: '59e96bd31b6b242caaf77a1c',
            previous_trained_revision_id: '59e96bd31b6b242caaf77a1c',
            optimization_methods: [],
        },
        {
            id: '59e96bd31b6b242caaf77a1d',
            name: 'MobileNetV2-ATSS OpenVINO FP32 with XAI head',
            version: 2,
            creation_date: '2025-02-25T10:39:22.502000+00:00',
            model_format: 'OpenVINO',
            precision: ['FP32'],
            has_xai_head: true,
            target_device: 'CPU',
            target_device_type: null,
            performance: {
                score: 0.7499999999999998,
            },
            size: 10417632,
            latency: 0,
            fps_throughput: 0,
            optimization_type: 'MO',
            optimization_objectives: {},
            model_status: 'SUCCESS',
            configurations: [],
            previous_revision_id: '59e96bd31b6b242caaf77a1c',
            previous_trained_revision_id: '59e96bd31b6b242caaf77a1c',
            optimization_methods: [],
        },
    ],
    labels: [
        {
            id: '59e94836734b717fbbfe0b7a',
            name: 'Candy',
            is_anomalous: false,
            color: '#e96115ff',
            hotkey: '',
            is_empty: false,
            group: 'Detection labels',
            parent_id: null,
        },
        {
            id: '59e94836734b717fbbfe0b84',
            name: 'No object',
            is_anomalous: false,
            color: '#000000ff',
            hotkey: '',
            is_empty: true,
            group: 'No object',
            parent_id: null,
        },
    ],
    training_dataset_info: {
        dataset_storage_id: '59e94836734b717fbbfe0b81',
        dataset_revision_id: '59e96b99cab175378e6dce03',
        n_samples: 4,
        n_images: 4,
        n_videos: 0,
        n_frames: 0,
    },
    training_framework: {
        type: 'otx',
        version: '1.6.2',
    },
    purge_info: {
        is_purged: false,
        purge_time: null,
        user_uid: null,
    },
    total_disk_size: 78402806,
    learning_approach: 'fully_supervised',
    previous_revision_id: '59e94a8a144cc52ba1424465',
    previous_trained_revision_id: '59e94a8a144cc52ba1424465',
};

export const modelMetricsResponse = {
    model_statistics: [
        {
            header: 'Training date',
            type: 'text',
            key: 'Training date',
            value: '2025-02-25T10:39:22.502000+00:00',
        },
        {
            header: 'Training job duration',
            type: 'text',
            key: 'Training job duration',
            value: '0:08:22',
        },
        {
            header: 'Training duration',
            type: 'text',
            key: 'Training duration',
            value: '0:04:26',
        },
        {
            header: 'Dataset split',
            type: 'bar',
            key: 'Dataset split',
            value: [
                {
                    header: 'Training',
                    key: 'Training',
                    value: 2,
                    color: null,
                },
                {
                    header: 'Validation',
                    key: 'Validation',
                    value: 1,
                    color: null,
                },
                {
                    header: 'Test',
                    key: 'Test',
                    value: 1,
                    color: null,
                },
            ],
        },
        {
            header: 'F-measure',
            type: 'bar',
            key: 'F-measure',
            value: [
                {
                    header: 'validation',
                    key: 'validation',
                    value: 0.91,
                    color: null,
                },
                {
                    header: 'test',
                    key: 'test',
                    value: 0.75,
                    color: null,
                },
            ],
        },
        {
            header: 'F-measure per label (test)',
            type: 'radial_bar',
            key: 'F-measure per label (test)',
            value: [
                {
                    header: 'Candy',
                    key: 'Candy',
                    value: 0.75,
                    color: '#e96115ff',
                },
            ],
        },
        {
            header: 'F-measure per label',
            type: 'radial_bar',
            key: 'F-measure per label',
            value: [
                {
                    header: 'Candy',
                    key: 'Candy',
                    value: 0.91,
                    color: '#e96115ff',
                },
            ],
        },
        {
            header: 'Optimal confidence threshold',
            type: 'text',
            key: 'Optimal confidence threshold',
            value: 0.4,
        },
        {
            header: 'train/data_time (sec/iter)',
            type: 'line',
            key: 'train/data_time (sec/iter)',
            value: {
                x_axis_label: 'Epoch',
                y_axis_label: 'train/data_time (sec/iter)',
                line_data: [
                    {
                        header: 'train/data_time (sec/iter)',
                        key: 'train/data_time (sec/iter)',
                        points: [
                            {
                                x: 1,
                                y: 1.3855485916137695,
                                type: 'point',
                            },
                            {
                                x: 2,
                                y: 0.05380892753601074,
                                type: 'point',
                            },
                            {
                                x: 3,
                                y: 0.0403745174407959,
                                type: 'point',
                            },
                            {
                                x: 4,
                                y: 0.059762001037597656,
                                type: 'point',
                            },
                            {
                                x: 5,
                                y: 0.0563814640045166,
                                type: 'point',
                            },
                            {
                                x: 6,
                                y: 0.07759952545166016,
                                type: 'point',
                            },
                            {
                                x: 7.000000000000001,
                                y: 0.044027090072631836,
                                type: 'point',
                            },
                            {
                                x: 8,
                                y: 0.05509305000305176,
                                type: 'point',
                            },
                            {
                                x: 9,
                                y: 0.05472540855407715,
                                type: 'point',
                            },
                            {
                                x: 10,
                                y: 0.06683731079101562,
                                type: 'point',
                            },
                            {
                                x: 11,
                                y: 0.03763079643249512,
                                type: 'point',
                            },
                            {
                                x: 12,
                                y: 0.0443727970123291,
                                type: 'point',
                            },
                            {
                                x: 13,
                                y: 0.04838967323303223,
                                type: 'point',
                            },
                            {
                                x: 14.000000000000002,
                                y: 0.047128915786743164,
                                type: 'point',
                            },
                            {
                                x: 15,
                                y: 0.046391963958740234,
                                type: 'point',
                            },
                            {
                                x: 16,
                                y: 0.0655984878540039,
                                type: 'point',
                            },
                            {
                                x: 17,
                                y: 0.03894686698913574,
                                type: 'point',
                            },
                            {
                                x: 18,
                                y: 0.06224226951599121,
                                type: 'point',
                            },
                            {
                                x: 19,
                                y: 0.051203012466430664,
                                type: 'point',
                            },
                            {
                                x: 20,
                                y: 0.03756093978881836,
                                type: 'point',
                            },
                        ],
                        color: null,
                    },
                ],
            },
        },
        {
            header: 'train/loss_cls',
            type: 'line',
            key: 'train/loss_cls',
            value: {
                x_axis_label: 'Epoch',
                y_axis_label: 'train/loss_cls',
                line_data: [
                    {
                        header: 'train/loss_cls',
                        key: 'train/loss_cls',
                        points: [
                            {
                                x: 1,
                                y: 0.08783111721277237,
                                type: 'point',
                            },
                            {
                                x: 2,
                                y: 0.1099652573466301,
                                type: 'point',
                            },
                            {
                                x: 3,
                                y: 0.07923795282840729,
                                type: 'point',
                            },
                            {
                                x: 4,
                                y: 0.16337206959724426,
                                type: 'point',
                            },
                            {
                                x: 5,
                                y: 0.1270955353975296,
                                type: 'point',
                            },
                            {
                                x: 6,
                                y: 0.06735876202583313,
                                type: 'point',
                            },
                            {
                                x: 7.000000000000001,
                                y: 0.09165109694004059,
                                type: 'point',
                            },
                            {
                                x: 8,
                                y: 0.15494771301746368,
                                type: 'point',
                            },
                            {
                                x: 9,
                                y: 0.12364315241575241,
                                type: 'point',
                            },
                            {
                                x: 10,
                                y: 0.09324128180742264,
                                type: 'point',
                            },
                            {
                                x: 11,
                                y: 0.24960872530937195,
                                type: 'point',
                            },
                            {
                                x: 12,
                                y: 0.08232278376817703,
                                type: 'point',
                            },
                            {
                                x: 13,
                                y: 0.10751137137413025,
                                type: 'point',
                            },
                            {
                                x: 14.000000000000002,
                                y: 0.10755514353513718,
                                type: 'point',
                            },
                            {
                                x: 15,
                                y: 0.20943421125411987,
                                type: 'point',
                            },
                            {
                                x: 16,
                                y: 0.1420864760875702,
                                type: 'point',
                            },
                            {
                                x: 17,
                                y: 0.1381174772977829,
                                type: 'point',
                            },
                            {
                                x: 18,
                                y: 0.04996005445718765,
                                type: 'point',
                            },
                            {
                                x: 19,
                                y: 0.08291900902986526,
                                type: 'point',
                            },
                            {
                                x: 20,
                                y: 0.08408372104167938,
                                type: 'point',
                            },
                        ],
                        color: null,
                    },
                ],
            },
        },
        {
            header: 'train/loss_bbox',
            type: 'line',
            key: 'train/loss_bbox',
            value: {
                x_axis_label: 'Epoch',
                y_axis_label: 'train/loss_bbox',
                line_data: [
                    {
                        header: 'train/loss_bbox',
                        key: 'train/loss_bbox',
                        points: [
                            {
                                x: 1,
                                y: 0.17143402993679047,
                                type: 'point',
                            },
                            {
                                x: 2,
                                y: 0.12210748344659805,
                                type: 'point',
                            },
                            {
                                x: 3,
                                y: 0.15211455523967743,
                                type: 'point',
                            },
                            {
                                x: 4,
                                y: 0.16336214542388916,
                                type: 'point',
                            },
                            {
                                x: 5,
                                y: 0.1895395815372467,
                                type: 'point',
                            },
                            {
                                x: 6,
                                y: 0.14721304178237915,
                                type: 'point',
                            },
                            {
                                x: 7.000000000000001,
                                y: 0.1599736511707306,
                                type: 'point',
                            },
                            {
                                x: 8,
                                y: 0.19101332128047943,
                                type: 'point',
                            },
                            {
                                x: 9,
                                y: 0.23716507852077484,
                                type: 'point',
                            },
                            {
                                x: 10,
                                y: 0.16114389896392822,
                                type: 'point',
                            },
                            {
                                x: 11,
                                y: 0.21759366989135742,
                                type: 'point',
                            },
                            {
                                x: 12,
                                y: 0.17304562032222748,
                                type: 'point',
                            },
                            {
                                x: 13,
                                y: 0.16944816708564758,
                                type: 'point',
                            },
                            {
                                x: 14.000000000000002,
                                y: 0.16832999885082245,
                                type: 'point',
                            },
                            {
                                x: 15,
                                y: 0.17087368667125702,
                                type: 'point',
                            },
                            {
                                x: 16,
                                y: 0.15223465859889984,
                                type: 'point',
                            },
                            {
                                x: 17,
                                y: 0.19350826740264893,
                                type: 'point',
                            },
                            {
                                x: 18,
                                y: 0.15699045360088348,
                                type: 'point',
                            },
                            {
                                x: 19,
                                y: 0.20858249068260193,
                                type: 'point',
                            },
                            {
                                x: 20,
                                y: 0.16366027295589447,
                                type: 'point',
                            },
                        ],
                        color: null,
                    },
                ],
            },
        },
        {
            header: 'train/loss_centerness',
            type: 'line',
            key: 'train/loss_centerness',
            value: {
                x_axis_label: 'Epoch',
                y_axis_label: 'train/loss_centerness',
                line_data: [
                    {
                        header: 'train/loss_centerness',
                        key: 'train/loss_centerness',
                        points: [
                            {
                                x: 1,
                                y: 0.612163245677948,
                                type: 'point',
                            },
                            {
                                x: 2,
                                y: 0.6004361510276794,
                                type: 'point',
                            },
                            {
                                x: 3,
                                y: 0.6268562078475952,
                                type: 'point',
                            },
                            {
                                x: 4,
                                y: 0.5893694758415222,
                                type: 'point',
                            },
                            {
                                x: 5,
                                y: 0.6306703090667725,
                                type: 'point',
                            },
                            {
                                x: 6,
                                y: 0.6045227646827698,
                                type: 'point',
                            },
                            {
                                x: 7.000000000000001,
                                y: 0.6259795427322388,
                                type: 'point',
                            },
                            {
                                x: 8,
                                y: 0.5965809226036072,
                                type: 'point',
                            },
                            {
                                x: 9,
                                y: 0.5730409622192383,
                                type: 'point',
                            },
                            {
                                x: 10,
                                y: 0.6032168865203857,
                                type: 'point',
                            },
                            {
                                x: 11,
                                y: 0.6052239537239075,
                                type: 'point',
                            },
                            {
                                x: 12,
                                y: 0.6311246752738953,
                                type: 'point',
                            },
                            {
                                x: 13,
                                y: 0.5573719143867493,
                                type: 'point',
                            },
                            {
                                x: 14.000000000000002,
                                y: 0.623321533203125,
                                type: 'point',
                            },
                            {
                                x: 15,
                                y: 0.6025677919387817,
                                type: 'point',
                            },
                            {
                                x: 16,
                                y: 0.6152403950691223,
                                type: 'point',
                            },
                            {
                                x: 17,
                                y: 0.6039316654205322,
                                type: 'point',
                            },
                            {
                                x: 18,
                                y: 0.6278438568115234,
                                type: 'point',
                            },
                            {
                                x: 19,
                                y: 0.5934855937957764,
                                type: 'point',
                            },
                            {
                                x: 20,
                                y: 0.6154295206069946,
                                type: 'point',
                            },
                        ],
                        color: null,
                    },
                ],
            },
        },
        {
            header: 'train/loss',
            type: 'line',
            key: 'train/loss',
            value: {
                x_axis_label: 'Epoch',
                y_axis_label: 'train/loss',
                line_data: [
                    {
                        header: 'train/loss',
                        key: 'train/loss',
                        points: [
                            {
                                x: 1,
                                y: 0.871428370475769,
                                type: 'point',
                            },
                            {
                                x: 2,
                                y: 0.83250892162323,
                                type: 'point',
                            },
                            {
                                x: 3,
                                y: 0.8582087159156799,
                                type: 'point',
                            },
                            {
                                x: 4,
                                y: 0.916103720664978,
                                type: 'point',
                            },
                            {
                                x: 5,
                                y: 0.94730544090271,
                                type: 'point',
                            },
                            {
                                x: 6,
                                y: 0.8190945386886597,
                                type: 'point',
                            },
                            {
                                x: 7.000000000000001,
                                y: 0.8776043057441711,
                                type: 'point',
                            },
                            {
                                x: 8,
                                y: 0.9425419569015503,
                                type: 'point',
                            },
                            {
                                x: 9,
                                y: 0.9338492155075073,
                                type: 'point',
                            },
                            {
                                x: 10,
                                y: 0.857602059841156,
                                type: 'point',
                            },
                            {
                                x: 11,
                                y: 1.0724263191223145,
                                type: 'point',
                            },
                            {
                                x: 12,
                                y: 0.8864930868148804,
                                type: 'point',
                            },
                            {
                                x: 13,
                                y: 0.8343314528465271,
                                type: 'point',
                            },
                            {
                                x: 14.000000000000002,
                                y: 0.8992066383361816,
                                type: 'point',
                            },
                            {
                                x: 15,
                                y: 0.9828757047653198,
                                type: 'point',
                            },
                            {
                                x: 16,
                                y: 0.9095615148544312,
                                type: 'point',
                            },
                            {
                                x: 17,
                                y: 0.9355574250221252,
                                type: 'point',
                            },
                            {
                                x: 18,
                                y: 0.8347944021224976,
                                type: 'point',
                            },
                            {
                                x: 19,
                                y: 0.8849871158599854,
                                type: 'point',
                            },
                            {
                                x: 20,
                                y: 0.8631734848022461,
                                type: 'point',
                            },
                        ],
                        color: null,
                    },
                ],
            },
        },
        {
            header: 'train/grad_norm',
            type: 'line',
            key: 'train/grad_norm',
            value: {
                x_axis_label: 'Epoch',
                y_axis_label: 'train/grad_norm',
                line_data: [
                    {
                        header: 'train/grad_norm',
                        key: 'train/grad_norm',
                        points: [
                            {
                                x: 1,
                                y: 2.72811222076416,
                                type: 'point',
                            },
                            {
                                x: 2,
                                y: 4.076419830322266,
                                type: 'point',
                            },
                            {
                                x: 3,
                                y: 2.465280532836914,
                                type: 'point',
                            },
                            {
                                x: 4,
                                y: 7.131985187530518,
                                type: 'point',
                            },
                            {
                                x: 5,
                                y: 5.987826824188232,
                                type: 'point',
                            },
                            {
                                x: 6,
                                y: 2.7370643615722656,
                                type: 'point',
                            },
                            {
                                x: 7.000000000000001,
                                y: 3.65371036529541,
                                type: 'point',
                            },
                            {
                                x: 8,
                                y: 5.712488174438477,
                                type: 'point',
                            },
                            {
                                x: 9,
                                y: 4.401169300079346,
                                type: 'point',
                            },
                            {
                                x: 10,
                                y: 3.541700601577759,
                                type: 'point',
                            },
                            {
                                x: 11,
                                y: 8.909773826599121,
                                type: 'point',
                            },
                            {
                                x: 12,
                                y: 5.391369342803955,
                                type: 'point',
                            },
                            {
                                x: 13,
                                y: 5.6188507080078125,
                                type: 'point',
                            },
                            {
                                x: 14.000000000000002,
                                y: 5.171286106109619,
                                type: 'point',
                            },
                            {
                                x: 15,
                                y: 5.242117881774902,
                                type: 'point',
                            },
                            {
                                x: 16,
                                y: 4.558900833129883,
                                type: 'point',
                            },
                            {
                                x: 17,
                                y: 5.109803676605225,
                                type: 'point',
                            },
                            {
                                x: 18,
                                y: 3.8619112968444824,
                                type: 'point',
                            },
                            {
                                x: 19,
                                y: 3.616936683654785,
                                type: 'point',
                            },
                            {
                                x: 20,
                                y: 4.989160060882568,
                                type: 'point',
                            },
                        ],
                        color: null,
                    },
                ],
            },
        },
        {
            header: 'train/time (sec/iter)',
            type: 'line',
            key: 'train/time (sec/iter)',
            value: {
                x_axis_label: 'Epoch',
                y_axis_label: 'train/time (sec/iter)',
                line_data: [
                    {
                        header: 'train/time (sec/iter)',
                        key: 'train/time (sec/iter)',
                        points: [
                            {
                                x: 1,
                                y: 3.577383279800415,
                                type: 'point',
                            },
                            {
                                x: 2,
                                y: 1.9800798892974854,
                                type: 'point',
                            },
                            {
                                x: 3,
                                y: 2.142547607421875,
                                type: 'point',
                            },
                            {
                                x: 4,
                                y: 1.9639105796813965,
                                type: 'point',
                            },
                            {
                                x: 5,
                                y: 2.170027256011963,
                                type: 'point',
                            },
                            {
                                x: 6,
                                y: 2.429165840148926,
                                type: 'point',
                            },
                            {
                                x: 7.000000000000001,
                                y: 1.961132287979126,
                                type: 'point',
                            },
                            {
                                x: 8,
                                y: 2.040463924407959,
                                type: 'point',
                            },
                            {
                                x: 9,
                                y: 1.9603767395019531,
                                type: 'point',
                            },
                            {
                                x: 10,
                                y: 2.2590980529785156,
                                type: 'point',
                            },
                            {
                                x: 11,
                                y: 1.8964004516601562,
                                type: 'point',
                            },
                            {
                                x: 12,
                                y: 2.0933594703674316,
                                type: 'point',
                            },
                            {
                                x: 13,
                                y: 2.328886032104492,
                                type: 'point',
                            },
                            {
                                x: 14.000000000000002,
                                y: 2.2258009910583496,
                                type: 'point',
                            },
                            {
                                x: 15,
                                y: 2.2563159465789795,
                                type: 'point',
                            },
                            {
                                x: 16,
                                y: 2.5638794898986816,
                                type: 'point',
                            },
                            {
                                x: 17,
                                y: 2.2868103981018066,
                                type: 'point',
                            },
                            {
                                x: 18,
                                y: 1.9019696712493896,
                                type: 'point',
                            },
                            {
                                x: 19,
                                y: 2.1366524696350098,
                                type: 'point',
                            },
                            {
                                x: 20,
                                y: 2.0825493335723877,
                                type: 'point',
                            },
                        ],
                        color: null,
                    },
                ],
            },
        },
        {
            header: 'learning_rate',
            type: 'line',
            key: 'learning_rate',
            value: {
                x_axis_label: 'Epoch',
                y_axis_label: 'learning_rate',
                line_data: [
                    {
                        header: 'learning_rate',
                        key: 'learning_rate',
                        points: [
                            {
                                x: 1,
                                y: 0.001333333333333333,
                                type: 'point',
                            },
                            {
                                x: 2,
                                y: 0.002222222222222222,
                                type: 'point',
                            },
                            {
                                x: 3,
                                y: 0.003111111111111111,
                                type: 'point',
                            },
                            {
                                x: 4,
                                y: 0.004,
                                type: 'point',
                            },
                            {
                                x: 5,
                                y: 0.004,
                                type: 'point',
                            },
                            {
                                x: 6,
                                y: 0.004,
                                type: 'point',
                            },
                            {
                                x: 7.000000000000001,
                                y: 0.004,
                                type: 'point',
                            },
                            {
                                x: 8,
                                y: 0.004,
                                type: 'point',
                            },
                            {
                                x: 9,
                                y: 0.004,
                                type: 'point',
                            },
                            {
                                x: 10,
                                y: 0.004,
                                type: 'point',
                            },
                            {
                                x: 11,
                                y: 0.004,
                                type: 'point',
                            },
                            {
                                x: 12,
                                y: 0.004,
                                type: 'point',
                            },
                            {
                                x: 13,
                                y: 0.004,
                                type: 'point',
                            },
                            {
                                x: 14.000000000000002,
                                y: 0.004,
                                type: 'point',
                            },
                            {
                                x: 15,
                                y: 0.004,
                                type: 'point',
                            },
                            {
                                x: 16,
                                y: 0.004,
                                type: 'point',
                            },
                            {
                                x: 17,
                                y: 0.004,
                                type: 'point',
                            },
                            {
                                x: 18,
                                y: 0.004,
                                type: 'point',
                            },
                            {
                                x: 19,
                                y: 0.004,
                                type: 'point',
                            },
                            {
                                x: 20,
                                y: 0.004,
                                type: 'point',
                            },
                        ],
                        color: null,
                    },
                ],
            },
        },
        {
            header: 'momentum',
            type: 'line',
            key: 'momentum',
            value: {
                x_axis_label: 'Epoch',
                y_axis_label: 'momentum',
                line_data: [
                    {
                        header: 'momentum',
                        key: 'momentum',
                        points: [
                            {
                                x: 1,
                                y: 0.1,
                                type: 'point',
                            },
                            {
                                x: 2,
                                y: 0.9,
                                type: 'point',
                            },
                            {
                                x: 3,
                                y: 5,
                                type: 'point',
                            },
                            {
                                x: 4,
                                y: 9,
                                type: 'point',
                            },
                            {
                                x: 5,
                                y: 11,
                                type: 'point',
                            },
                            {
                                x: 6,
                                y: 5,
                                type: 'point',
                            },
                            {
                                x: 7.000000000000001,
                                y: 4,
                                type: 'point',
                            },
                            {
                                x: 8,
                                y: 20,
                                type: 'point',
                            },
                            {
                                x: 9,
                                y: 17,
                                type: 'point',
                            },
                            {
                                x: 10,
                                y: 2,
                                type: 'point',
                            },
                        ],
                        color: null,
                    },
                ],
            },
        },
        {
            header: 'val/AP50',
            type: 'line',
            key: 'val/AP50',
            value: {
                x_axis_label: 'Epoch',
                y_axis_label: 'val/AP50',
                line_data: [
                    {
                        header: 'val/AP50',
                        key: 'val/AP50',
                        points: [
                            {
                                x: 5,
                                y: 1,
                                type: 'point',
                            },
                            {
                                x: 10,
                                y: 4.5,
                                type: 'point',
                            },
                            {
                                x: 15,
                                y: 8,
                                type: 'point',
                            },
                            {
                                x: 20,
                                y: 10,
                                type: 'point',
                            },
                        ],
                        color: null,
                    },
                ],
            },
        },
        {
            header: 'val/mAP',
            type: 'line',
            key: 'val/mAP',
            value: {
                x_axis_label: 'Epoch',
                y_axis_label: 'val/mAP',
                line_data: [
                    {
                        header: 'val/mAP',
                        key: 'val/mAP',
                        points: [
                            {
                                x: 5,
                                y: 1,
                                type: 'point',
                            },
                            {
                                x: 10,
                                y: 6,
                                type: 'point',
                            },
                            {
                                x: 15,
                                y: 11,
                                type: 'point',
                            },
                            {
                                x: 20,
                                y: 20,
                                type: 'point',
                            },
                        ],
                        color: null,
                    },
                ],
            },
        },
        {
            header: 'Validation score',
            type: 'radial_bar',
            key: 'Validation score',
            value: [
                {
                    header: 'mAP',
                    key: 'mAP',
                    value: 0.97,
                    color: null,
                },
            ],
        },
    ],
} as const;

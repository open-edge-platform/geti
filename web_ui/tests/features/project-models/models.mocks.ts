// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { OpenApiResponseBody } from '../../../src/core/server/types';
import { LifecycleStage } from '../../../src/core/supported-algorithms/dtos/supported-algorithms.interface';

export const getObsoleteModelGroups: OpenApiResponseBody<'GetModelGroups'> = {
    model_groups: [
        {
            id: '633aa0e210ccb847ccccc42b',
            model_template_id: 'Custom_Image_Classification_EfficinetNet-B0',
            models: [
                {
                    active_model: true,
                    creation_date: '2022-10-10T08:20:52.540000+00:00',
                    id: '6343d5e4aba8c6d87d17ab6a',
                    name: 'EfficientNet-B0',
                    performance: { score: 0.85 },
                    size: 16330443,
                    version: 2,
                },
                {
                    active_model: false,
                    creation_date: '2022-10-03T08:44:35.074000+00:00',
                    id: '633aa0f397e2d10e57eccdb7',
                    name: 'EfficientNet-B0',
                    performance: { score: 0.75 },
                    size: 16330444,
                    version: 1,
                },
            ],
            name: 'EfficientNet-B0',
            task_id: '6101254defba22ca453f11d1',
            lifecycle_stage: LifecycleStage.OBSOLETE,
        },
    ],
};

export const getDeprecatedModelGroups: OpenApiResponseBody<'GetModelGroups'> = {
    model_groups: [
        {
            id: '633aa0e210ccb847ccccc42b',
            model_template_id: 'Custom_Image_Classification_EfficinetNet-B0',
            models: [
                {
                    active_model: true,
                    creation_date: '2022-10-10T08:20:52.540000+00:00',
                    id: '6343d5e4aba8c6d87d17ab6a',
                    name: 'EfficientNet-B0',
                    performance: { score: 0.85 },
                    size: 16330443,
                    version: 2,
                },
                {
                    active_model: false,
                    creation_date: '2022-10-03T08:44:35.074000+00:00',
                    id: '633aa0f397e2d10e57eccdb7',
                    name: 'EfficientNet-B0',
                    performance: { score: 0.75 },
                    size: 16330444,
                    version: 1,
                },
            ],
            name: 'EfficientNet-B0',
            task_id: '6101254defba22ca453f11d1',
            lifecycle_stage: LifecycleStage.DEPRECATED,
        },
    ],
};

export const getModelGroups: OpenApiResponseBody<'GetModelGroups'> = {
    model_groups: [
        {
            id: '633aa0e210ccb847ccccc42b',
            model_template_id: 'Custom_Image_Classification_EfficinetNet-B0',
            models: [
                {
                    active_model: true,
                    creation_date: '2022-10-10T08:20:52.540000+00:00',
                    id: '6343d5e4aba8c6d87d17ab6a',
                    name: 'EfficientNet-B0',
                    performance: { score: 0.85 },
                    size: 16330443,
                    version: 2,
                },
                {
                    active_model: false,
                    creation_date: '2022-10-03T08:44:35.074000+00:00',
                    id: '633aa0f397e2d10e57eccdb7',
                    name: 'EfficientNet-B0',
                    performance: { score: 0.75 },
                    size: 16330444,
                    version: 1,
                },
            ],
            name: 'EfficientNet-B0',
            task_id: '6101254defba22ca453f11d1',
            lifecycle_stage: LifecycleStage.ACTIVE,
        },
    ],
};

export const getModelGroup: OpenApiResponseBody<'GetModelGroup'> = {
    id: '633aa0e210ccb847ccccc42b',
    model_template_id: 'Custom_Image_Classification_EfficinetNet-B0',
    models: [
        {
            active_model: true,
            creation_date: '2022-10-10T08:20:52.540000+00:00',
            id: '6343d5e4aba8c6d87d17ab6a',
            name: 'EfficientNet-B0',
            performance: { score: 0.85 },
            size: 16330443,
            version: 2,
        },
        {
            active_model: false,
            creation_date: '2022-10-03T08:44:35.074000+00:00',
            id: '633aa0f397e2d10e57eccdb7',
            name: 'EfficientNet-B0',
            performance: { score: 0.75 },
            size: 16330444,
            version: 1,
        },
    ],
    name: 'EfficientNet-B0',
    task_id: '6101254defba22ca453f11d1',
    lifecycle_stage: LifecycleStage.ACTIVE,
};

export const getModelDetail: OpenApiResponseBody<'GetModelDetail'> = {
    architecture: 'EfficientNet-B0',
    creation_date: '2022-10-03T09:44:35.074000+00:00',
    fps_throughput: 0,
    id: '6343d5e4aba8c6d87d17ab6a',
    labels: [
        {
            color: '#00f5d4ff',
            group: 'Classification labels',
            hotkey: '',
            id: '633aa0e210ccb847ccccc42e',
            is_anomalous: false,
            is_empty: false,
            name: 'Cat',
            parent_id: null,
        },
        {
            color: '#cc94daff',
            group: 'Classification labels',
            hotkey: '',
            id: '633aa0e210ccb847ccccc430',
            is_anomalous: false,
            is_empty: false,
            name: 'Dog',
            parent_id: null,
        },
    ],
    latency: 0,
    name: 'EfficientNet-B0',
    optimization_capabilities: {
        is_filter_pruning_enabled: false,
        is_filter_pruning_supported: true,
        is_nncf_supported: true,
    },
    optimized_models: [
        {
            // @ts-expect-error this field isn't documented in the rest api
            creation_date: '2022-10-03T08:44:35.105000+00:00',
            fps_throughput: 0,
            id: '633aa0f397e2d10e57eccdb8',
            latency: 0,
            model_status: 'SUCCESS',
            name: 'EfficientNet-B0 OpenVINO',
            optimization_methods: [],
            optimization_objectives: {},
            optimization_type: 'MO',
            performance: { score: 0.75 },
            precision: ['FP32'],
            previous_revision_id: '633aa0f397e2d10e57eccdb7',
            previous_trained_revision_id: '633aa0f397e2d10e57eccdb7',
            size: 16246582,
            target_device: 'CPU',
            target_device_type: undefined,
            version: 1,
            configurations: [],
        },
    ],
    performance: { score: 0.75 },
    precision: ['FP32'],
    previous_revision_id: '',
    previous_trained_revision_id: '',
    score_up_to_date: true,
    size: 16330444,
    target_device: 'CPU',
    target_device_type: undefined,
    training_dataset_info: {
        dataset_revision_id: '633aa0f297e2d10e57eccda6',
        dataset_storage_id: '633aa0e210ccb847ccccc428',
        n_frames: 0,
        n_images: 18,
        n_samples: 18,
    },
    version: 2,
};

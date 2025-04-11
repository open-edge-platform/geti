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

import { expect } from '@playwright/test';

import { LifecycleStage } from '../../../src/core/supported-algorithms/dtos/supported-algorithms.interface';
import { test } from '../../fixtures/base-test';
import {
    acceptFilter,
    checkChipsValue,
    checkMediaNameFilter,
    closeSearchByNameFilterPopover,
    openAndTypeIntoSearchField,
    triggerFilterModal,
} from '../../fixtures/search-by-name';
import { switchCallsAfter } from '../../utils/api';
import { Subset } from './../../../src/pages/project-details/components/project-model/training-dataset/utils';
import { testWithModelsApiExamples } from './fixtures';

const MODEL_DETAILS_URL =
    // eslint-disable-next-line max-len
    'organizations/5b1f89f3-aba5-4a5f-84ab-de9abb8e0633/workspaces/61011e42d891c82e13ec92da/projects/60db493ed20945a0046f56ce/models/60dc3b8b3fc7834f46ea90d5/60dc3b8b3fc7834f46ea90af/model-variants/openvino';

const testingPrefix = 'testing-';

const modelDetailsWithoutOptimizedPOTModel = {
    id: '6728a04d2a8677f073453e76',
    name: 'EfficientNet-B0',
    architecture: 'EfficientNet-B0',
    version: 1,
    creation_date: '2024-11-04T10:22:05.049000+00:00',
    size: 40610840,
    performance: {
        score: 0.7,
    },
    label_schema_in_sync: false,
    precision: ['FP32'],
    optimized_models: [
        {
            id: '6728a04d2a8677f073453e7a',
            name: 'EfficientNet-B0 ONNX FP32',
            version: 1,
            creation_date: '2024-11-04T10:22:05.062000+00:00',
            model_format: 'ONNX',
            precision: ['FP32'],
            has_xai_head: false,
            performance: {
                score: 0.7,
            },
            size: 20108608,
            optimization_type: 'ONNX',
            optimization_objectives: {},
            model_status: 'SUCCESS',
            configurations: [],
            previous_revision_id: '6728a04d2a8677f073453e76',
            previous_trained_revision_id: '6728a04d2a8677f073453e76',
            optimization_methods: [],
        },
        {
            id: '6728a04d2a8677f073453e79',
            name: 'EfficientNet-B0 OpenVINO FP16',
            version: 1,
            creation_date: '2024-11-04T10:22:05.060000+00:00',
            model_format: 'OpenVINO',
            precision: ['FP16'],
            has_xai_head: false,
            performance: {
                score: 0.7,
            },
            size: 10410305,
            optimization_type: 'MO',
            optimization_objectives: {},
            model_status: 'SUCCESS',
            configurations: [],
            previous_revision_id: '6728a04d2a8677f073453e76',
            previous_trained_revision_id: '6728a04d2a8677f073453e76',
            optimization_methods: [],
        },
        {
            id: '6728a04d2a8677f073453e78',
            name: 'EfficientNet-B0 OpenVINO FP32',
            version: 1,
            creation_date: '2024-11-04T10:22:05.057000+00:00',
            model_format: 'OpenVINO',
            precision: ['FP32'],
            has_xai_head: false,
            performance: {
                score: 0.7,
            },
            size: 20321739,
            optimization_type: 'MO',
            optimization_objectives: {},
            model_status: 'SUCCESS',
            configurations: [],
            previous_revision_id: '6728a04d2a8677f073453e76',
            previous_trained_revision_id: '6728a04d2a8677f073453e76',
            optimization_methods: [],
        },
        {
            id: '6728a04d2a8677f073453e77',
            name: 'EfficientNet-B0 OpenVINO FP32 with XAI head',
            version: 1,
            creation_date: '2024-11-04T10:22:05.055000+00:00',
            model_format: 'OpenVINO',
            precision: ['FP32'],
            has_xai_head: true,
            performance: {
                score: 0.7,
            },
            size: 33063832,
            optimization_type: 'MO',
            optimization_objectives: {},
            model_status: 'SUCCESS',
            configurations: [],
            previous_revision_id: '6728a04d2a8677f073453e76',
            previous_trained_revision_id: '6728a04d2a8677f073453e76',
            optimization_methods: [],
        },
    ],
    labels: [
        {
            id: '6728a02a0daf05467155ac7e',
            name: 'support animal',
            is_anomalous: false,
            color: '#ff7d00ff',
            hotkey: '',
            is_empty: false,
            group: 'animal',
            parent_id: null,
        },
        {
            id: '6728a02a0daf05467155ac7f',
            name: 'man',
            is_anomalous: false,
            color: '#d7bc5eff',
            hotkey: '',
            is_empty: false,
            group: 'animal___gender',
            parent_id: '6728a02a0daf05467155ac82',
        },
        {
            id: '6728a02a0daf05467155ac80',
            name: 'woman_DELETED_6728a02a0daf05467155ac80',
            is_anomalous: false,
            color: '#d7bc5eff',
            hotkey: '',
            is_empty: false,
            group: 'animal___gender',
            parent_id: '6728a02a0daf05467155ac82',
        },
        {
            id: '6728a02a0daf05467155ac81',
            name: 'dog',
            is_anomalous: false,
            color: '#c9e649ff',
            hotkey: '',
            is_empty: false,
            group: 'animal___pet',
            parent_id: '6728a02a0daf05467155ac7e',
        },
        {
            id: '6728a02a0daf05467155ac82',
            name: 'person',
            is_anomalous: false,
            color: '#c9e649ff',
            hotkey: '',
            is_empty: false,
            group: 'animal',
            parent_id: null,
        },
        {
            id: '6728a02a0daf05467155ac83',
            name: 'cat',
            is_anomalous: false,
            color: '#81407bff',
            hotkey: '',
            is_empty: false,
            group: 'animal___pet',
            parent_id: '6728a02a0daf05467155ac7e',
        },
    ],
    training_dataset_info: {
        dataset_storage_id: '6728a02a0daf05467155ac84',
        dataset_revision_id: '6728a04c2a8677f073453e71',
        n_samples: 19,
        n_images: 19,
        n_videos: 0,
        n_frames: 0,
    },
    training_framework: {
        type: 'otx',
        version: '2.2.0',
    },
    purge_info: {
        is_purged: false,
        purge_time: null,
        user_uid: null,
    },
    total_disk_size: 187083699,
    learning_approach: 'fully_supervised',
    previous_revision_id: '',
    previous_trained_revision_id: '',
};
const modelDetailsWithOptimizedPOTModel = {
    ...modelDetailsWithoutOptimizedPOTModel,
    optimized_models: [
        ...modelDetailsWithoutOptimizedPOTModel.optimized_models,
        {
            id: '6728a04d2a8677f073453e78',
            name: 'EfficientNet-B0 OpenVINO INT8',
            version: 1,
            creation_date: '2024-11-04T10:22:05.057000+00:00',
            model_format: 'OpenVINO',
            precision: ['INT8'],
            has_xai_head: false,
            performance: {
                score: 0.7,
            },
            size: 20321739,
            optimization_type: 'POT',
            optimization_objectives: {},
            model_status: 'SUCCESS',
            configurations: [],
            previous_revision_id: '6728a04d2a8677f073453e76',
            previous_trained_revision_id: '6728a04d2a8677f073453e76',
            optimization_methods: [],
        },
    ],
};

testWithModelsApiExamples.describe('project model details', () => {
    testWithModelsApiExamples.beforeEach(async ({ page, registerApiResponse }) => {
        const switchCallsAfterTwo = switchCallsAfter(2);

        registerApiResponse(
            'GetModelDetail',
            switchCallsAfterTwo([
                (_, res, ctx) => {
                    return res(ctx.json(modelDetailsWithoutOptimizedPOTModel));
                },
                (_, res, ctx) => {
                    return res(ctx.json(modelDetailsWithOptimizedPOTModel));
                },
            ])
        );

        await page.goto(MODEL_DETAILS_URL, { timeout: 15000 });
    });

    testWithModelsApiExamples.describe('Training datasets', () => {
        testWithModelsApiExamples.beforeEach(async ({ page }) => {
            await page.getByText('Training datasets').click();
        });

        testWithModelsApiExamples(
            'Check if typing filter will set chip with the filter and after removing it filter is removed',
            async ({ page }) => {
                /** Implementation of test cases:
                 * test_annotator_dataset_searchbar_auto_label[modelPage]
                 * test_annotator_dataset_searchbar_remove_label[modelPage]
                 */

                await openAndTypeIntoSearchField(page, 'cat', testingPrefix);

                await closeSearchByNameFilterPopover(page, testingPrefix);
                await expect(page.getByTestId(`${testingPrefix}chip-search-rule-id`)).toHaveText(
                    'Media name contains cat'
                );

                await page.getByRole('button', { name: `${testingPrefix}remove-rule-search-rule-id` }).click();
                await expect(page.getByTestId(`${testingPrefix}chip-search-rule-id`)).toBeHidden();

                await triggerFilterModal(page, testingPrefix);
                expect(await page.locator('#media-filter-delete-row').count()).toBe(0);
                await page.keyboard.press('Escape');
            }
        );

        testWithModelsApiExamples(
            'Check if submitting filter shorter than 3 chars will add chip with filter',
            async ({ page }) => {
                /** test_annotator_dataset_searchbar_manual_label[modelPage] */

                await openAndTypeIntoSearchField(page, 'im', testingPrefix);
                await acceptFilter(page, testingPrefix);

                await closeSearchByNameFilterPopover(page, testingPrefix);
                await checkChipsValue(page, 'Media name contains im', testingPrefix);
            }
        );

        testWithModelsApiExamples('Check if changing search will update filter rule', async ({ page }) => {
            /** test_annotator_dataset_searchbar_overwrite_label[modelPage] */

            await openAndTypeIntoSearchField(page, 'cat', testingPrefix);
            await openAndTypeIntoSearchField(page, 'dog', testingPrefix);

            await closeSearchByNameFilterPopover(page, testingPrefix);

            await triggerFilterModal(page, testingPrefix);

            await checkMediaNameFilter(page, 'dog');
        });

        testWithModelsApiExamples(
            'Opening image and video previews',
            async ({ page, registerApiResponse, openApi }) => {
                registerApiResponse('FilterVideoFramesInTrainingRevision', (_, res, ctx) => {
                    const { mock } = openApi.mockResponseForOperation('FilterVideoFramesInTrainingRevision');
                    return res(
                        ctx.json({
                            media: mock.video_frames,
                            total_images: 0,
                            total_matched_images: 0,
                            total_matched_video_frames: 2,
                            total_matched_videos: 1,
                            total_videos: 2,
                        })
                    );
                });

                //
                const trainingBucket = page.getByTestId(`${Subset.TRAINING}-subset`);

                // Test that we can open an image preview
                const images = trainingBucket.getByRole('img', { name: /dummy_images/ });
                await images.click();
                const dialog = page.getByRole('dialog');
                await expect(dialog).toBeVisible();
                await expect(page.getByText(/training subset/i)).toBeVisible();
                await page.getByRole('button', { name: /close preview modal/ }).click();
                await expect(dialog).toBeHidden();

                // Test that we can open an video preview
                const video = trainingBucket.getByRole('img', { name: /dummy_video/ });
                await video.click();

                await expect(dialog).toBeVisible();
                await expect(page.getByText(/training subset/i)).toBeVisible();

                // Navigate within video
                const next = page.getByRole('button', { name: /go to next frame/i });
                await expect(next).toBeEnabled();
                await next.click();

                const previous = page.getByRole('button', { name: /go to previous frame/i });
                await expect(previous).toBeEnabled();
                await previous.click();

                // Close dialog
                await page.getByRole('button', { name: /close preview modal/ }).click();
                await expect(dialog).toBeHidden();
            }
        );

        testWithModelsApiExamples(
            'Edit an image from the model testing set',
            async ({ page, registerApiResponse, openApi }) => {
                registerApiResponse('FilterVideoFramesInTrainingRevision', (_, res, ctx) => {
                    const { mock } = openApi.mockResponseForOperation('FilterVideoFramesInTrainingRevision');
                    return res(
                        ctx.json({
                            media: mock.video_frames,
                            total_images: 0,
                            total_matched_images: 0,
                            total_matched_video_frames: 2,
                            total_matched_videos: 1,
                            total_videos: 2,
                        })
                    );
                });

                //
                const testingBucket = page.getByTestId(`${Subset.TESTING}-subset`);

                // Test that we can open an image preview
                const images = testingBucket.getByRole('img', { name: /dummy_images/ });
                await images.click();
                const dialog = page.getByRole('dialog');
                await expect(dialog).toBeVisible();
                await expect(page.getByText(/testing subset/i)).toBeVisible();

                await page.getByRole('button', { name: /edit annotations/i }).click();
                await expect(dialog).toBeHidden();

                expect(page.url()).toContain('annotator');
            }
        );
    });

    testWithModelsApiExamples(
        'Shows progress when model is being optimized, when is optimized shows that model in a table',
        async ({ page, registerApiResponse }) => {
            const runningJobs = {
                jobs: [
                    {
                        id: '6728b85b7f17fba4f71cac99',
                        type: 'optimize_pot',
                        creation_time: '2024-11-04T12:04:43.749000+00:00',
                        start_time: '2024-11-04T12:04:49.735000+00:00',
                        end_time: null,
                        name: 'Optimization',
                        author: '660db1b9-d91e-4671-b04e-8ed03a23312b',
                        state: 'running',
                        steps: [
                            {
                                message: 'Dataset sharding is done and model is prepared',
                                index: 1,
                                progress: 100,
                                state: 'running',
                                step_name: 'Shard dataset',
                            },
                            {
                                message: null,
                                index: 2,
                                progress: -1,
                                state: 'waiting',
                                step_name: 'Optimizing model',
                            },
                            {
                                message: null,
                                index: 3,
                                progress: -1,
                                state: 'waiting',
                                step_name: 'Evaluating optimized model',
                            },
                        ],
                        cancellation_info: {
                            cancellable: true,
                            is_cancelled: false,
                            user_uid: null,
                            cancel_time: null,
                        },
                        metadata: {
                            project: {
                                id: '5d10b5fb212b36bd37c48bc6',
                                name: 'Candy',
                            },
                            task: {
                                task_id: '5d10b5fb212b36bd37c48bc9',
                                model_template_id: 'Custom_Object_Detection_Gen3_ATSS',
                                model_architecture: 'MobileNetV2-ATSS',
                            },
                            model_storage_id: '60dc3b8b3fc7834f46ea90d5',
                            base_model_id: '60dc3b8b3fc7834f46ea90af',
                            optimization_type: 'POT',
                            optimized_model_id: null,
                        },
                    },
                ],
                jobs_count: {
                    n_scheduled_jobs: 0,
                    n_running_jobs: 1,
                    n_finished_jobs: 0,
                    n_failed_jobs: 0,
                    n_cancelled_jobs: 0,
                },
            };
            const finishedJobs = {
                jobs: [
                    {
                        id: '6728b85b7f17fba4f71cac99',
                        type: 'optimize_pot',
                        creation_time: '2024-11-04T12:04:43.749000+00:00',
                        start_time: '2024-11-04T12:04:49.735000+00:00',
                        end_time: '2024-11-04T12:07:29.459000+00:00',
                        name: 'Optimization',
                        author: '660db1b9-d91e-4671-b04e-8ed03a23312b',
                        state: 'finished',
                        steps: [
                            {
                                message: 'Dataset sharding is done and model is prepared',
                                index: 1,
                                progress: 100,
                                state: 'finished',
                                step_name: 'Shard dataset',
                                duration: 10.208,
                            },
                            {
                                message: 'Model optimized',
                                index: 2,
                                progress: 100.0,
                                state: 'finished',
                                step_name: 'Optimizing model',
                                duration: 14.012,
                            },
                            {
                                message: 'Model evaluated',
                                index: 3,
                                progress: 100,
                                state: 'finished',
                                step_name: 'Evaluating optimized model',
                                duration: 16.011,
                            },
                        ],
                        cancellation_info: {
                            cancellable: true,
                            is_cancelled: false,
                            user_uid: null,
                            cancel_time: null,
                        },
                        metadata: {
                            project: {
                                id: '5d10b5fb212b36bd37c48bc6',
                                name: 'Candy',
                            },
                            task: {
                                task_id: '5d10b5fb212b36bd37c48bc9',
                                model_template_id: 'Custom_Object_Detection_Gen3_ATSS',
                                model_architecture: 'MobileNetV2-ATSS',
                            },
                            model_storage_id: '60dc3b8b3fc7834f46ea90d5',
                            base_model_id: '60dc3b8b3fc7834f46ea90af',
                            optimization_type: 'POT',
                            optimized_model_id: '6728b87dacb382cc9d1149c7',
                        },
                    },
                ],
                jobs_count: {
                    n_scheduled_jobs: 0,
                    n_running_jobs: 0,
                    n_finished_jobs: 1,
                    n_failed_jobs: 0,
                    n_cancelled_jobs: 0,
                },
            };

            registerApiResponse('GetJobs', (_, res, ctx) =>
                res(
                    ctx.json({
                        jobs: [],
                        jobs_count: {
                            n_scheduled_jobs: 0,
                            n_running_jobs: 0,
                            n_finished_jobs: 0,
                            n_failed_jobs: 0,
                            n_cancelled_jobs: 0,
                        },
                    })
                )
            );

            await page.getByRole('button', { name: 'Start optimization' }).click();

            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(runningJobs)));

            await expect(page.getByRole('button', { name: 'Optimization in progress' })).toBeVisible();

            registerApiResponse('GetJobs', (_, res, ctx) => res(ctx.json(finishedJobs)));

            await expect(page.getByRole('button', { name: 'Optimization in progress' })).toBeHidden();
            await expect(page.getByRole('button', { name: 'Start optimization' })).toBeHidden();

            await expect(
                page.getByRole('row', {
                    name: /EfficientNet\-B0 OpenVINO INT8 post\-training optimization/i,
                })
            ).toBeVisible();
        }
    );

    test('When model variant is obsolete, start optimization button should be disabled', async ({
        page,
        registerApiResponse,
    }) => {
        const modelDetailsObsolete = {
            ...modelDetailsWithoutOptimizedPOTModel,

            optimized_models: [
                {
                    id: '6728a04d2a8677f073453e7a',
                    name: 'EfficientNet-B0 ONNX FP32',
                    version: 1,
                    creation_date: '2024-11-04T10:22:05.062000+00:00',
                    model_format: 'ONNX',
                    precision: ['FP32'],
                    has_xai_head: false,
                    performance: {
                        score: 0.7,
                    },
                    size: 20108608,
                    optimization_type: 'ONNX',
                    optimization_objectives: {},
                    model_status: 'SUCCESS',
                    configurations: [],
                    previous_revision_id: '6728a04d2a8677f073453e76',
                    previous_trained_revision_id: '6728a04d2a8677f073453e76',
                    optimization_methods: [],
                },
                {
                    id: '6728a04d2a8677f073453e79',
                    name: 'EfficientNet-B0 OpenVINO FP16',
                    version: 1,
                    creation_date: '2024-11-04T10:22:05.060000+00:00',
                    model_format: 'OpenVINO',
                    precision: ['FP16'],
                    has_xai_head: false,
                    performance: {
                        score: 0.7,
                    },
                    size: 10410305,
                    optimization_type: 'MO',
                    optimization_objectives: {},
                    model_status: 'SUCCESS',
                    configurations: [],
                    previous_revision_id: '6728a04d2a8677f073453e76',
                    previous_trained_revision_id: '6728a04d2a8677f073453e76',
                    optimization_methods: [],
                    lifecycle_stage: LifecycleStage.OBSOLETE,
                },
                {
                    id: '6728a04d2a8677f073453e78',
                    name: 'EfficientNet-B0 OpenVINO FP32',
                    version: 1,
                    creation_date: '2024-11-04T10:22:05.057000+00:00',
                    model_format: 'OpenVINO',
                    precision: ['FP32'],
                    has_xai_head: false,
                    performance: {
                        score: 0.7,
                    },
                    size: 20321739,
                    optimization_type: 'MO',
                    optimization_objectives: {},
                    model_status: 'SUCCESS',
                    configurations: [],
                    previous_revision_id: '6728a04d2a8677f073453e76',
                    previous_trained_revision_id: '6728a04d2a8677f073453e76',
                    optimization_methods: [],
                },
                {
                    id: '6728a04d2a8677f073453e77',
                    name: 'EfficientNet-B0 OpenVINO FP32 with XAI head',
                    version: 1,
                    creation_date: '2024-11-04T10:22:05.055000+00:00',
                    model_format: 'OpenVINO',
                    precision: ['FP32'],
                    has_xai_head: true,
                    performance: {
                        score: 0.7,
                    },
                    size: 33063832,
                    optimization_type: 'MO',
                    optimization_objectives: {},
                    model_status: 'SUCCESS',
                    configurations: [],
                    previous_revision_id: '6728a04d2a8677f073453e76',
                    previous_trained_revision_id: '6728a04d2a8677f073453e76',
                    optimization_methods: [],
                },
            ],
        };
        registerApiResponse('GetModelDetail', (_, res, ctx) => res(ctx.json(modelDetailsObsolete)));

        await page.goto(MODEL_DETAILS_URL);

        const startOptimizationButton = page.getByRole('button', { name: 'Start optimization' });

        await expect(startOptimizationButton).toBeVisible();
        await expect(startOptimizationButton).toBeDisabled();
    });
});

// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { PredictionDTO } from '@/api/types';
import { expect } from '@playwright/test';
import { getMockedMediaImage } from 'mocks/mock-media';
import { getMockedModel } from 'mocks/mock-model';
import { getMockedVariant } from 'mocks/mock-model-variant';
import { HttpResponse } from 'msw';

import { http, test } from '../fixtures';
import { blueLabel, mockedDetectionProject, redLabel, useDetectionProjectFixtures } from './annotator-fixtures';

test.describe('Annotator - predictions', () => {
    useDetectionProjectFixtures();

    test.describe('Annotation and prediction modes', () => {
        const predictions = [
            {
                shape: {
                    type: 'rectangle',
                    x: 3,
                    y: 0,
                    width: 780,
                    height: 421,
                },
                labels: [{ id: blueLabel.id }],
                confidences: [0.9619140625],
            },
            {
                shape: {
                    type: 'rectangle',
                    x: 1007,
                    y: 624,
                    width: 909,
                    height: 456,
                },
                labels: [{ id: blueLabel.id }],
                confidences: [0.9599609375],
            },
            {
                shape: {
                    type: 'rectangle',
                    x: 291,
                    y: 0,
                    width: 1553,
                    height: 889,
                },
                labels: [{ id: blueLabel.id }],
                confidences: [0.904296875],
            },
        ] satisfies PredictionDTO[];

        test('Annotation vs Prediction', async ({ page, annotatorPage, boundingBoxTool, network }) => {
            network.use(
                http.get('/api/projects/{project_id}/models', async () => {
                    return HttpResponse.json([
                        getMockedModel({
                            variants: [getMockedVariant({})],
                        }),
                    ]);
                }),
                http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', async () => {
                    return HttpResponse.json({
                        annotations: [],
                        user_reviewed: true,
                        subset: 'training',
                    });
                }),
                http.post('/api/projects/{project_id}/dataset/media:predict', async () => {
                    return HttpResponse.json({
                        predictions: [
                            {
                                media: {
                                    id: '123',
                                },
                                prediction: predictions,
                            },
                        ],
                    });
                })
            );

            await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

            await test.step('Draws an annotation in annotation mode', async () => {
                await expect(annotatorPage.getAnnotatorMode('annotation')).toHaveAttribute('aria-pressed', 'true');
                await expect(annotatorPage.getAnnotatorMode('prediction')).toHaveAttribute('aria-pressed', 'false');

                const annotation = { x: 100, y: 100, width: 150, height: 150 };

                await boundingBoxTool.selectTool();
                await boundingBoxTool.drawBoundingBox(annotation);

                expect(await annotatorPage.getAnnotationsListItems('annotation rect')).toHaveLength(1);

                await expect(page.getByLabel(`label ${redLabel.name} background`)).toHaveCount(1);

                expect(await annotatorPage.getAnnotationsListItems('prediction rect')).toHaveLength(0);
            });

            await test.step('Displays server prediction in prediction mode', async () => {
                await annotatorPage.openPredictionMode();

                await expect(annotatorPage.getAnnotatorMode('prediction')).toHaveAttribute('aria-pressed', 'true');
                await expect(annotatorPage.getAnnotatorMode('annotation')).toHaveAttribute('aria-pressed', 'false');

                await expect(annotatorPage.getPrimaryToolbar()).toBeHidden();
                await expect(page.getByLabel('Labels', { exact: true })).toBeHidden();

                await expect(page.getByLabel(`label ${blueLabel.name} background`)).toHaveCount(predictions.length);
                expect(await annotatorPage.getAnnotationsListItems('prediction rect')).toHaveLength(predictions.length);

                expect(await annotatorPage.getAnnotationsListItems('annotation rect')).toHaveLength(0);
                await expect(page.getByLabel(`label ${redLabel.name} background`)).toHaveCount(0);
            });

            await test.step('Hides predictions in annotation mode, restores annotation', async () => {
                await annotatorPage.openAnnotationMode();

                expect(await annotatorPage.getAnnotationsListItems('prediction rect')).toHaveLength(0);
                expect(await annotatorPage.getAnnotationsListItems('annotation rect')).toHaveLength(1);
            });

            await test.step('Edits prediction by overwriting existing annotations with prediction in annotation mode', async () => {
                await annotatorPage.openPredictionMode();
                await annotatorPage.editPrediction();

                await expect(annotatorPage.getAnnotatorMode('annotation')).toHaveAttribute('aria-pressed', 'true');
                await expect(annotatorPage.getAnnotatorMode('prediction')).toHaveAttribute('aria-pressed', 'false');

                await expect(page.getByLabel(`label ${blueLabel.name} background`)).toHaveCount(predictions.length);
                await expect(page.getByLabel(`label ${redLabel.name} background`)).toBeHidden();
            });
        });

        test('Displays cues for annotator modes only for the first time for one media, resets for next media', async ({
            annotatorPage,
            page,
            network,
        }) => {
            // item-1: no annotations (404), has predictions
            // item-2: has 1 annotation, has predictions
            const mediaItems = [
                getMockedMediaImage({ id: 'item-1', name: 'item-1', width: 1920, height: 1080 }),
                getMockedMediaImage({ id: 'item-2', name: 'item-2', width: 1920, height: 1080 }),
            ];

            network.use(
                http.get('/api/projects/{project_id}/dataset/media', () => {
                    return HttpResponse.json({
                        items: mediaItems,
                        pagination: {
                            offset: 0,
                            limit: 10,
                            count: mediaItems.length,
                            total: mediaItems.length,
                        },
                    });
                }),
                http.get('/api/projects/{project_id}/models', async () => {
                    return HttpResponse.json([
                        getMockedModel({
                            variants: [getMockedVariant({})],
                        }),
                    ]);
                }),
                http.post('/api/projects/{project_id}/dataset/media:predict', async () => {
                    return HttpResponse.json({
                        predictions: [
                            {
                                media: {
                                    id: '123',
                                },
                                prediction: predictions,
                            },
                        ],
                    });
                }),
                http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', async ({ params }) => {
                    if (params.media_id === mediaItems[0].id) {
                        return HttpResponse.json(
                            {
                                // @ts-expect-error We care only about mocking detail
                                detail: 'Media has not been annotated yet',
                            },
                            { status: 404 }
                        );
                    }

                    return HttpResponse.json({
                        annotations: [
                            {
                                shape: {
                                    type: 'rectangle',
                                    x: 1007,
                                    y: 624,
                                    width: 909,
                                    height: 456,
                                },
                                labels: [{ id: redLabel.id }],
                            },
                        ],
                        user_reviewed: true,
                        subset: 'training',
                    });
                })
            );

            await test.step('item-1 (annotation mode): prediction cue visible because there are no annotations but predictions exist', async () => {
                const predictResponsePromise = page.waitForResponse((res) => res.url().includes('media:predict'));

                await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

                await expect(annotatorPage.getAnnotationsList()).toBeVisible();
                await predictResponsePromise;

                await expect(page.getByLabel('Prediction available')).toBeVisible();
            });

            await test.step('item-1: switching annotation -> prediction dismisses prediction cue; switching back keeps it dismissed', async () => {
                await annotatorPage.openPredictionMode();

                await annotatorPage.openAnnotationMode();

                await expect(page.getByLabel('Prediction available')).toBeHidden();
            });

            await test.step('navigate to item-2 (in prediction mode): no annotation cue is shown', async () => {
                await annotatorPage.openPredictionMode();
                await annotatorPage.selectMediaItem('item-2');

                await expect(page.getByLabel('Annotation available')).toBeHidden();
            });

            await test.step('item-2: switching prediction -> annotation hides prediction cue', async () => {
                await annotatorPage.openAnnotationMode();

                await expect(page.getByLabel('Prediction available')).toBeHidden();
            });
        });

        test('Displays "No object" when media:predict returns empty predictions', async ({
            page,
            annotatorPage,
            network,
        }) => {
            network.use(
                http.get('/api/projects/{project_id}/models', async () => {
                    return HttpResponse.json([
                        getMockedModel({
                            variants: [getMockedVariant({})],
                        }),
                    ]);
                }),
                http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', async () => {
                    return HttpResponse.json(
                        {
                            // @ts-expect-error We care only about mocking detail
                            detail: 'Media has not been annotated yet',
                        },
                        { status: 404 }
                    );
                }),
                http.post('/api/projects/{project_id}/dataset/media:predict', async () => {
                    return HttpResponse.json({
                        predictions: [
                            {
                                media: { id: '123' },
                                prediction: [],
                            },
                        ],
                    });
                })
            );

            await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

            await annotatorPage.openPredictionMode();

            await expect(annotatorPage.getAnnotatorMode('prediction')).toHaveAttribute('aria-pressed', 'true');
            await expect(page.getByLabel('label No object background')).toHaveCount(1);
        });
    });

    test.describe('Prediction mode model', () => {
        const olderModel = getMockedModel({
            id: 'older-model-id',
            name: 'Older_Model (older)',
            variants: [
                getMockedVariant({
                    id: 'older-variant-id',
                    format: 'openvino',
                    precision: 'fp32',
                    optimal_confidence_threshold: 0.2,
                }),
            ],
            training_info: {
                status: 'successful',
                label_schema_revision: { labels: [{ id: 'label-1', name: 'cat' }] },
                start_time: '2025-01-01T10:00:00.000000+00:00',
                end_time: '2025-01-01T12:00:00.000000+00:00',
                dataset_revision_id: 'dataset-1',
            },
        });

        const newerModel = getMockedModel({
            id: 'newer-model-id',
            name: 'Newer_Model (newer)',
            variants: [
                getMockedVariant({
                    id: 'newer-variant-id',
                    format: 'openvino',
                    precision: 'fp16',
                    optimal_confidence_threshold: 0.65,
                }),
            ],
            training_info: {
                status: 'successful',
                label_schema_revision: { labels: [{ id: 'label-1', name: 'cat' }] },
                start_time: '2025-02-01T10:00:00.000000+00:00',
                end_time: '2025-02-01T12:00:00.000000+00:00',
                dataset_revision_id: 'dataset-2',
            },
        });

        const emptyPredictHandler = http.post('/api/projects/{project_id}/dataset/media:predict', async () => {
            return HttpResponse.json({ predictions: [{ media: { id: 'item-1' }, prediction: [] }] });
        });

        test('shows no model selector when no models are available', async ({ page, annotatorPage, network }) => {
            network.use(
                http.get('/api/projects/{project_id}/models', async () => {
                    return HttpResponse.json([]);
                }),
                emptyPredictHandler
            );

            await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

            await test.step('open prediction mode', async () => {
                await annotatorPage.openPredictionMode();
            });

            await test.step('prediction settings are not available when no models available', async () => {
                await expect(annotatorPage.getPredictionSettingsButton()).toBeHidden();
                await expect(page.getByRole('button', { name: 'Select prediction model' })).toBeHidden();
            });
        });

        test('shows no model selector when models have no OpenVINO variants', async ({
            page,
            annotatorPage,
            network,
        }) => {
            network.use(
                http.get('/api/projects/{project_id}/models', async () => {
                    return HttpResponse.json([
                        getMockedModel({
                            id: 'pytorch-only-model',
                            variants: [getMockedVariant({ id: 'pytorch-variant', format: 'pytorch' })],
                        }),
                    ]);
                }),
                emptyPredictHandler
            );

            await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

            await test.step('open prediction mode', async () => {
                await annotatorPage.openPredictionMode();
            });

            await test.step('prediction settings are not available when no OpenVINO models available', async () => {
                await expect(annotatorPage.getPredictionSettingsButton()).toBeHidden();
                await expect(page.getByRole('button', { name: 'Select prediction model' })).toBeHidden();
            });
        });

        test('selects latest model by training end time when no active model is set', async ({
            page,
            annotatorPage,
            network,
        }) => {
            network.use(
                http.get('/api/projects/{project_id}/models', async () => {
                    return HttpResponse.json([olderModel, newerModel]);
                }),
                emptyPredictHandler
            );

            await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

            await test.step('open prediction mode', async () => {
                await annotatorPage.openPredictionMode();
                await annotatorPage.openPredictionSettings();
            });

            await test.step('the newer model is pre-selected in the picker', async () => {
                await expect(page.getByRole('button', { name: 'Select prediction model' })).toContainText(
                    'Newer_Model'
                );
            });
        });

        test('active model takes priority over default latest model selection', async ({
            page,
            annotatorPage,
            network,
        }) => {
            network.use(
                http.get('/api/projects/{project_id}/models', async () => {
                    return HttpResponse.json([olderModel, newerModel]);
                }),
                http.get('/api/projects/{project_id}/pipeline', ({ response }) => {
                    return response(200).json({
                        project_id: mockedDetectionProject.id,
                        status: 'idle',
                        source: null,
                        sink: null,
                        // @ts-expect-error We care only about mocking the active model resolution behavior
                        model: olderModel,
                        // @ts-expect-error model_revision_id is not included in getMockedVariant
                        model_variant: getMockedVariant({ id: olderModel.variants[0].id }),
                        device: 'cpu',
                    });
                }),
                emptyPredictHandler
            );

            await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

            await test.step('open prediction mode', async () => {
                await annotatorPage.openPredictionMode();
                await annotatorPage.openPredictionSettings();
            });

            await test.step('the active model is pre-selected instead of the latest model', async () => {
                await expect(page.getByRole('button', { name: 'Select prediction model' })).toContainText(
                    'Older_Model'
                );
            });
        });

        test('changing model selection uses the newly selected model for predictions', async ({
            page,
            annotatorPage,
            network,
        }) => {
            let capturedModelVariantId: string | undefined;
            let capturedConfidenceThreshold: number | undefined;

            network.use(
                http.get('/api/projects/{project_id}/models', async () => {
                    return HttpResponse.json([olderModel, newerModel]);
                }),
                http.post('/api/projects/{project_id}/dataset/media:predict', async ({ request }) => {
                    const body = (await request.json()) as unknown as {
                        model_variant_id?: string;
                        confidence_threshold?: number;
                    };
                    capturedModelVariantId = body.model_variant_id;
                    capturedConfidenceThreshold = body.confidence_threshold;

                    return HttpResponse.json({ predictions: [{ media: { id: 'item-1' }, prediction: [] }] });
                })
            );

            await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

            await test.step('open prediction mode — newer model should be selected by default', async () => {
                await annotatorPage.openPredictionMode();
                await annotatorPage.openPredictionSettings();

                await expect(page.getByRole('button', { name: 'Select prediction model' })).toContainText(
                    'Newer_Model'
                );
            });

            await test.step('select the older model from the picker', async () => {
                const predictResponsePromise = page.waitForResponse((res) => res.url().includes('media:predict'));

                await page.getByRole('button', { name: 'Select prediction model' }).click();
                await page.getByRole('option', { name: /Older_Model/ }).click();

                await expect(page.getByRole('button', { name: 'Select prediction model' })).toContainText(
                    'Older_Model'
                );

                await predictResponsePromise;
            });

            await test.step('predictions are requested with the newly selected model variant', async () => {
                expect(capturedModelVariantId).toBe(olderModel.variants[0].id);
            });

            await test.step('the confidence threshold follows the selected model', async () => {
                await expect(page.getByRole('textbox', { name: 'Change Confidence threshold' })).toHaveValue('0.2');
                expect(capturedConfidenceThreshold).toBe(0.2);
            });
        });

        test('changing device selection uses the new device for predictions', async ({
            page,
            annotatorPage,
            network,
        }) => {
            let capturedDevice: string | undefined;

            network.use(
                http.get('/api/projects/{project_id}/models', async () => {
                    return HttpResponse.json([newerModel]);
                }),
                http.get('/api/system/devices/inference', async () => {
                    return HttpResponse.json([
                        { type: 'cpu', name: 'CPU' },
                        { type: 'xpu', name: 'XPU' },
                    ]);
                }),
                http.get('/api/projects/{project_id}/pipeline', ({ response }) => {
                    return response(200).json({
                        project_id: mockedDetectionProject.id,
                        status: 'idle',
                        source: null,
                        sink: null,
                        device: 'cpu',
                    });
                }),
                http.post('/api/projects/{project_id}/dataset/media:predict', async ({ request }) => {
                    const body = await request.json();
                    capturedDevice = body.device;

                    return HttpResponse.json({ predictions: [{ media: { id: 'item-1' }, prediction: [] }] });
                })
            );

            await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

            await test.step('open prediction mode and wait for initial predict request', async () => {
                const predictResponsePromise = page.waitForResponse((res) => res.url().includes('media:predict'));

                await annotatorPage.openPredictionMode();

                await predictResponsePromise;
            });

            await test.step('initial predict request used cpu device', async () => {
                expect(capturedDevice).toBe('cpu');
            });

            await test.step('change device selection to XPU', async () => {
                const predictResponsePromise = page.waitForResponse((res) => res.url().includes('media:predict'));

                await annotatorPage.openPredictionSettings();
                await page.getByRole('button', { name: /inference device/i }).click();
                await page.getByRole('option', { name: /XPU/i }).click();

                await expect(page.getByRole('button', { name: /XPU/i })).toBeVisible();

                await predictResponsePromise;
            });

            await test.step('new predict request used xpu device', async () => {
                expect(capturedDevice).toBe('xpu');
            });
        });

        test('last used model is used by default', async ({ page, annotatorPage, network }) => {
            network.use(
                http.get('/api/projects/{project_id}/models', async () => {
                    return HttpResponse.json([olderModel, newerModel]);
                }),
                emptyPredictHandler
            );

            await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

            await test.step('open prediction mode — newer model is auto-selected by default', async () => {
                await annotatorPage.openPredictionMode();
                await annotatorPage.openPredictionSettings();

                await expect(page.getByRole('button', { name: 'Select prediction model' })).toContainText(
                    'Newer_Model'
                );
            });

            await test.step('change selection to the older model', async () => {
                const predictResponsePromise = page.waitForResponse((res) => res.url().includes('media:predict'));

                await page.getByRole('button', { name: 'Select prediction model' }).click();
                await page.getByRole('option', { name: /Older_Model/ }).click();

                await expect(page.getByRole('button', { name: 'Select prediction model' })).toContainText(
                    'Older_Model'
                );

                await predictResponsePromise;
            });

            await test.step('reload the page', async () => {
                await page.reload();
            });

            await test.step('open prediction mode after reload — older model is still selected', async () => {
                await annotatorPage.openPredictionMode();
                await annotatorPage.openPredictionSettings();

                await expect(page.getByRole('button', { name: 'Select prediction model' })).toContainText(
                    'Older_Model'
                );
            });
        });
    });
});

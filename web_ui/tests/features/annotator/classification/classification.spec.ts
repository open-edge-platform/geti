// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

import { LabelDTO } from '../../../../src/core/labels/dtos/label.interface';
import { DOMAIN } from '../../../../src/core/projects/core.interface';
import { delay } from '../../../../src/shared/utils';
import { checkCommonElements, annotatorTest as test } from '../../../fixtures/annotator-test';
import { registerFullImage, registerStoreSettings, switchCallsAfter } from '../../../utils/api';
import { waitForLoadingToBeFinished } from '../../../utils/assertions';
import { resolveTestAssetPath } from '../../../utils/dataset';
import {
    expectAGlobalAnnotationToExist,
    expectAnnotationNotToHaveLabels,
    expectAnnotationToHaveLabels,
    getGlobalAnnotation,
} from '../../project-tests/expect';
import { toggleShowPredictions } from '../utils';
import {
    globalAnnotationDTO,
    media,
    modelSource,
    project,
    labels as projectLabels,
    userAnnotationsResponse,
    userSource,
} from './../../../mocks/classification/card-classification-projects';
import { annotatorUrl, predictionAnnotationsResponse } from './../../../mocks/classification/mocks';

const suits = projectLabels.filter(({ group }) => group === 'Suit');
const values = projectLabels.filter(({ group }) => group === 'Value');

const toPredictionLabel = (label: LabelDTO) => ({
    ...label,
    source: modelSource,
    probability: 0.33,
});

const toUserLabel = (label: LabelDTO) => {
    return { ...label, source: userSource, probability: 1.0 };
};

const selectAnnotationMode = async (page: Page) =>
    await page.getByRole('button', { name: 'Select annotation mode' }).click();

const selectPredictionMode = async (page: Page) =>
    await page.getByRole('button', { name: 'Select prediction mode' }).click();

const getSubmitAnnotations = (page: Page) => page.getByRole('button', { name: 'Submit annotations' });

test.describe(`Classification`, () => {
    // Create default annotations and predictions where the values differ but suit is the same
    const annotations = [{ ...globalAnnotationDTO, labels: [suits[0], values[0]].map(toUserLabel) }];
    const predictions = [{ ...globalAnnotationDTO, labels: [suits[0], values[7]].map(toPredictionLabel) }];
    predictionAnnotationsResponse.maps = predictions[0].labels.map((label) => {
        return {
            id: label.id,
            label_id: label.id,
            name: label.name,
            roi: {
                id: label.id,
                shape: { type: 'RECTANGLE', x: 0, y: 0, height: 960, width: 720 },
            },
            // eslint-disable-next-line max-len
            url: '/api/v1/organizations/000000000000000000000001/workspaces/workspace_id/projects/project_id/datasets/dataset_id/media/images/image_id/predictions/maps/map_id',
        };
    });

    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
        registerFullImage(registerApiResponse, resolveTestAssetPath('ace-of-spades.webp'));

        registerApiResponse('GetImageAnnotation', (_, res, ctx) => {
            return res(ctx.json({ ...userAnnotationsResponse, annotations }));
        });

        registerApiResponse('GetSinglePrediction', async (_req, res, ctx) => {
            return res(ctx.status(200), ctx.json({ predictions }));
        });

        registerApiResponse('GetSingleExplanation', async (_req, res, ctx) => {
            return res(
                ctx.json({
                    maps: predictions[0].labels.map((label) => {
                        return {
                            // eslint-disable-next-line max-len
                            data: '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAIBAQEBAQIBAQECAgICAgQDAgICAgUEBAMEBgUGBgYFBgYGBwkIBgcJBwYGCAsICQoKCgoKBggLDAsKDAkKCgr/wAALCAAGAAgBAREA/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/9oACAEBAAA/APyq+Ov7Tf7GuqfDH4u/Cz4G6X8XYrXxBN4Ot/h2fFHiScxR2ekxTxXX9p28eoPBK5DxfZ18uZIPnEQt1OD/AP/Z',
                            label_id: label.id,
                            label_name: label.name,
                        };
                    }),
                    created: '2023-11-07 14:57:03.371633532 +0000',
                    media_identifier: {
                        image_id: '6548cac2e645c2fbcd20b7b2',
                        type: 'image',
                    },
                })
            );
        });
    });

    test('Annotations and predictions', async ({ page }) => {
        await page.goto(annotatorUrl);

        await expectAnnotationToHaveLabels(await getGlobalAnnotation(page), annotations[0].labels);

        await expectAGlobalAnnotationToExist(page);

        await selectAnnotationMode(page);
        await selectPredictionMode(page);

        await expect(getSubmitAnnotations(page)).toBeEnabled();

        await Promise.all([
            page.waitForRequest((request) => {
                if (request.method() !== 'POST' || !request.url().endsWith('/annotations')) {
                    return false;
                }

                // Verify that predictions were submitted
                const [annotation] = request.postDataJSON()?.annotations ?? [];
                return predictions[0].labels.every(({ id }) => {
                    return annotation.labels.some((label: LabelDTO) => label.id === id);
                });
            }),
            getSubmitAnnotations(page).click(),
        ]);
    });

    test('No annotations, no predictions', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
            res(ctx.json({ ...userAnnotationsResponse, annotations: [] }))
        );
        registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.json({ predictions: [] })));

        await page.goto(annotatorUrl);

        await expectAnnotationToHaveLabels(await getGlobalAnnotation(page), []);
    });

    test('No annotations, predicted annotation', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
            res(ctx.json({ ...userAnnotationsResponse, annotations: [] }))
        );

        await page.goto(annotatorUrl);
        await expectAGlobalAnnotationToExist(page);

        await expectAnnotationToHaveLabels(await getGlobalAnnotation(page), predictions[0].labels);
    });

    test('No annotations, predicted annotation with slow request', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetImageAnnotation', async (_, res, ctx) => {
            await delay(2000);
            return res(ctx.json({ ...userAnnotationsResponse, annotations: [] }));
        });
        registerApiResponse('GetSinglePrediction', async (_req, res, ctx) => {
            await delay(2020);
            return res(ctx.status(200), ctx.json({ predictions }));
        });

        await page.goto(annotatorUrl);

        await page.waitForTimeout(2 * 1000);

        await expectAGlobalAnnotationToExist(page);

        await expectAnnotationToHaveLabels(await getGlobalAnnotation(page), predictions[0].labels);
    });

    test('Annotations, no predicted annotation', async ({ page, registerApiResponse }) => {
        await page.goto(annotatorUrl);
        await expectAGlobalAnnotationToExist(page);
        registerApiResponse('GetSinglePrediction', async (_req, res, ctx) => {
            return res(ctx.status(204), ctx.json({ predictions: [] }));
        });

        await expectAnnotationToHaveLabels(await getGlobalAnnotation(page), annotations[0].labels);
    });

    test('It allows opening prediction mode after the first model was trained', async ({
        page,
        registerApiResponse,
        featureFlags,
    }) => {
        const modelGroups = [
            {
                id: '6630ee6acca0ded16d798213',
                name: 'EfficientNet-B0',
                model_template_id: 'Custom_Image_Classification_EfficinetNet-B0',
                task_id: '6630ee6acca0ded16d798212',
                models: [
                    {
                        id: '6630efdf61c12b94423306f4',
                        name: 'EfficientNet-B0',
                        creation_date: '2024-04-30T13:19:27.350000+00:00',
                        score_up_to_date: true,
                        active_model: true,
                        size: 32484626,
                        performance: {
                            score: 0.875,
                        },
                        label_schema_in_sync: true,
                        version: 1,
                    },
                ],
            },
        ];

        const switchAfter = switchCallsAfter(1);
        const getModelGroups = switchAfter([
            async (_, res, ctx) => {
                // Assume no model has been trained when we open up the annotator
                return res(ctx.json({ model_groups: [] }));
            },
            async (_, res, ctx) => {
                // After a little while we will have an active model, at which time we can fetch predictions
                return res(ctx.json({ model_groups: modelGroups }));
            },
        ]);

        registerApiResponse('GetModelGroups', getModelGroups);
        registerApiResponse('GetImageAnnotation', async (_, res, ctx) => {
            return res(ctx.status(200), ctx.json({ ...userAnnotationsResponse, annotations: [] }));
        });
        registerApiResponse('GetSinglePrediction', async (_, res, ctx) => {
            return res(ctx.status(200), ctx.json({ predictions: [] }));
        });

        await page.goto(annotatorUrl);

        await expectAnnotationToHaveLabels(await getGlobalAnnotation(page), []);

        if (featureFlags.FEATURE_FLAG_VISUAL_PROMPT_SERVICE === false) {
            await expect(page.getByRole('button', { name: 'Select prediction mode' })).toBeDisabled();
        }

        // It takes about 60 seconds for us to refetch the models, we wait for a bit more
        // to make sure that the test doesn't become flaky when loading is slow
        registerApiResponse('GetSinglePrediction', async (_, res, ctx) => {
            return res(ctx.status(200), ctx.json({ predictions }));
        });
        await expect(page.getByRole('button', { name: 'Select prediction mode' })).toBeEnabled({ timeout: 90_000 });

        await selectPredictionMode(page);
        await expectAnnotationToHaveLabels(await getGlobalAnnotation(page), predictions[0].labels);

        await selectAnnotationMode(page);
        await expectAnnotationToHaveLabels(await getGlobalAnnotation(page), predictions[0].labels);
    });

    test('It shows predicted annotations after a timeout', async ({ page, registerApiResponse }) => {
        registerApiResponse('GetImageAnnotation', async (_, res, ctx) => {
            await delay(1_000);

            return res(ctx.status(200), ctx.json({ ...userAnnotationsResponse, annotations: [] }));
        });

        registerApiResponse('GetSinglePrediction', async (_req, res, ctx) => {
            await delay(4_000);
            return res(ctx.status(200), ctx.json({ predictions }));
        });

        await page.goto(annotatorUrl);

        await page.waitForTimeout(5 * 1000);

        await expectAnnotationToHaveLabels(await getGlobalAnnotation(page), predictions[0].labels);
    });

    test('Anotator page elements', async ({ page }) => {
        await page.goto(annotatorUrl);

        await waitForLoadingToBeFinished(page);
        await expect(page.getByText('Card classification')).toBeVisible({
            timeout: 5000,
        });

        await checkCommonElements(page, DOMAIN.CLASSIFICATION);
    });

    test.describe('Explanation', () => {
        test('empty explanations', async ({ page, registerApiResponse, explanation }) => {
            registerApiResponse('GetSingleExplanation', async (_, res, ctx) => {
                return res(ctx.status(200), ctx.json({ maps: [] }));
            });

            await page.goto(`${annotatorUrl}?mode=predictions`);

            const explanationButton = await explanation.getExplanationButton();

            await expect(explanationButton).toBeDisabled();
        });

        test('replace user annotations with predictions', async ({ page, explanation }) => {
            await page.goto(`${annotatorUrl}?mode=predictions`);

            await explanation.activateTool();

            const globalAnnotation = await getGlobalAnnotation(page);

            await explanation.selectExplanationOption('Spades');

            await expectAnnotationToHaveLabels(globalAnnotation, [predictions[0].labels[0]]);
            await expectAnnotationNotToHaveLabels(globalAnnotation, [predictions[0].labels[1]]);

            await explanation.selectExplanationOption('A');

            await expectAnnotationToHaveLabels(globalAnnotation, [predictions[0].labels[1]]);
            await expectAnnotationNotToHaveLabels(globalAnnotation, [predictions[0].labels[0]]);
        });
    });

    // TODO: there's some weird visual bug when model mesh is enabled
    // Add a check that no annotation has a shape
    test('overlap annotations', async ({ page }) => {
        await page.goto(annotatorUrl);

        await selectPredictionMode(page);

        const globalAnnotation = await getGlobalAnnotation(page);
        await expectAnnotationToHaveLabels(globalAnnotation, predictions[0].labels);
        await expectAnnotationNotToHaveLabels(globalAnnotation, [annotations[0].labels[1]]);

        await page.getByRole('switch', { name: 'overlap annotations' }).click();

        // 7 is shown, but A from prediction is hidden
        await expectAnnotationToHaveLabels(globalAnnotation, [annotations[0].labels[1]]);
        await expectAnnotationNotToHaveLabels(globalAnnotation, [predictions[0].labels[1]]);
    });

    test('render submit/accept annotation', async ({ page }) => {
        await page.goto(annotatorUrl);

        await expect(getSubmitAnnotations(page)).toBeVisible();
        await expect(getSubmitAnnotations(page)).toHaveText('Submit »');

        await selectPredictionMode(page);

        await expect(getSubmitAnnotations(page)).toBeVisible();
        await expect(getSubmitAnnotations(page)).toHaveText('Accept »');
    });

    test.describe('prediction as annotations config', () => {
        test.beforeEach(({ registerApiResponse }) => {
            registerStoreSettings(registerApiResponse);
        });

        test.describe('disabled', () => {
            test('shows discard/submit confirmation with changes', async ({ registerApiResponse, page }) => {
                registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
                    res(ctx.json({ ...userAnnotationsResponse, annotations: [] }))
                );

                await page.goto(annotatorUrl);

                await toggleShowPredictions(page, false);

                await page.getByRole('button', { name: 'Spades' }).click();
                await page.getByRole('button', { name: 'Next media item' }).click();

                // Go to the next image/video while discarding changes
                await expect(page.getByRole('heading', { name: 'Discard or submit annotations' })).toBeVisible();
                await page.getByRole('button', { name: 'Discard' }).click();

                // Go back and verify that we don't load predictions
                await page.getByRole('img', { name: /dummy_image/ }).click();
                await expectAnnotationToHaveLabels(await getGlobalAnnotation(page), []);
            });
        });

        test.describe('enable', () => {
            test('do not show discard/submit confirmation', async ({ registerApiResponse, page }) => {
                registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
                    res(ctx.json({ ...userAnnotationsResponse, annotations: [] }))
                );

                await page.goto(annotatorUrl);

                await toggleShowPredictions(page, true);

                await expectAnnotationToHaveLabels(await getGlobalAnnotation(page), predictions[0].labels);

                await page.getByRole('button', { name: 'Next media item' }).click();
                await expect(page.getByRole('heading', { name: 'Discard or submit annotations' })).toBeHidden();
            });

            test('shows discard/submit confirmation with changes', async ({ registerApiResponse, page }) => {
                registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
                    res(ctx.json({ ...userAnnotationsResponse, annotations: [] }))
                );

                await page.goto(annotatorUrl);
                await waitForLoadingToBeFinished(page);

                await toggleShowPredictions(page, true);

                await expectAnnotationToHaveLabels(await getGlobalAnnotation(page), predictions[0].labels);

                await page.getByRole('button', { name: 'Clubs' }).click();
                await page.getByRole('button', { name: 'Next media item' }).click();

                await expect(page.getByRole('heading', { name: 'Discard or submit annotations' })).toBeVisible();
            });
        });
    });
});

// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { expect, Page } from '@playwright/test';

import { AnnotationLabelDTO } from '../../../../src/core/annotations/dtos/annotation.interface';
import { LabelDTO } from '../../../../src/core/labels/dtos/label.interface';
import { DOMAIN } from '../../../../src/core/projects/core.interface';
import { OpenApiResponseBody } from '../../../../src/core/server/types';
import { delay } from '../../../../src/shared/utils';
import {
    checkCommonElements,
    checkNumberOfTools,
    checkSegmentationTools,
    annotatorTest as test,
} from '../../../fixtures/annotator-test';
import {
    annotatorUrl,
    cardLabelId,
    cards,
    media,
    modelSource,
    project,
} from '../../../mocks/segmentation/card-segmentation-project';
import { registerFullImage } from '../../../utils/api';
import { waitForLoadingToBeFinished } from '../../../utils/assertions';
import { resolveTestAssetPath } from '../../../utils/dataset';
import { userAnnotationsResponse } from './../../../mocks/segmentation/mocks';

// @ts-expect-error ignore for now
const toPredictionLabel = (label: Partial<LabelDTO>): AnnotationLabelDTO => ({
    ...label,
    source: modelSource,
    probability: 0.33,
});

const selectPredictionMode = async (page: Page) =>
    await page.getByRole('button', { name: 'Select prediction mode' }).click();
const usePredictions = async (page: Page) => await page.getByRole('button', { name: 'Use predictions' }).click();

test.describe(`Segmentation`, () => {
    const annotations = [cards[0], cards[1], cards[2], cards[3]];

    const predictions = [cards[4], cards[5], cards[6], cards[7], cards[8], cards[9]].map((annotation) => {
        return { ...annotation, labels: annotation.labels.map(toPredictionLabel) };
    });

    test.beforeEach(({ registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
        registerFullImage(registerApiResponse, resolveTestAssetPath('multiple-cards.webp'));

        registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
            res(
                ctx.json({
                    ...userAnnotationsResponse,
                    annotations,
                })
            )
        );
        registerApiResponse('GetSinglePrediction', async (_, res, ctx) => {
            return res(ctx.json({ predictions }));
        });
        registerApiResponse('GetSingleExplanation', async (_, res, ctx) => {
            return res(ctx.json({ maps: [{ label_id: cardLabelId, label_name: 'Card', data: '' }] }));
        });
    });

    test('Annotations and predictions', async ({ page, registerApiResponse, annotationListPage }) => {
        registerApiResponse('CreateImageAnnotation', (req, res, ctx) => {
            return res(ctx.status(200), ctx.json({ annotation_state_per_task: [], ...req.body }));
        });

        await page.goto(annotatorUrl);

        await annotationListPage.expectTotalAnnotationsToBe(annotations.length);

        await selectPredictionMode(page);

        await usePredictions(page);
        await page.getByRole('button', { name: 'Merge' }).click();

        await annotationListPage.expectTotalAnnotationsToBe(annotations.length + predictions.length);
    });

    test('No annotations, no predictions', async ({ page, registerApiResponse, annotationListPage }) => {
        registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
            res(ctx.json({ ...userAnnotationsResponse, annotations: [] }))
        );
        registerApiResponse('GetSinglePrediction', async (_, res, ctx) => {
            return res(ctx.json({ predictions: [] }));
        });

        await page.goto(annotatorUrl);

        await annotationListPage.expectTotalAnnotationsToBe(0);
    });

    test('No annotations, predicted annotation', async ({ page, registerApiResponse, annotationListPage }) => {
        registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
            res(ctx.json({ ...userAnnotationsResponse, annotations: [] }))
        );

        await page.goto(annotatorUrl);
        await annotationListPage.expectTotalAnnotationsToBe(predictions.length);
    });

    test('Annotations, no predicted annotation', async ({ page, registerApiResponse, annotationListPage }) => {
        registerApiResponse('GetSinglePrediction', async (_, res, ctx) => {
            return res(ctx.json({ predictions: [] }));
        });

        await page.goto(annotatorUrl);
        await annotationListPage.expectTotalAnnotationsToBe(annotations.length);
    });

    test('Slowly loading predictions', async ({ page, registerApiResponse, annotationListPage }) => {
        registerApiResponse('GetImageAnnotation', async (_, res, ctx) => {
            await delay(2_000);

            return res(ctx.status(200), ctx.json({ ...userAnnotationsResponse, annotations: [] }));
        });

        registerApiResponse('GetSinglePrediction', async (_, res, ctx) => {
            await delay(60_000);

            return res(ctx.json({ predictions }));
        });

        await page.goto(annotatorUrl);

        await page.waitForTimeout(60_000);

        await annotationListPage.expectTotalAnnotationsToBe(0);
    });

    test('Annotations and predictions slow', async ({ page, registerApiResponse, annotationListPage }) => {
        registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
            res(ctx.json({ ...userAnnotationsResponse, annotations }))
        );
        registerApiResponse('GetSinglePrediction', async (_, res, ctx) => {
            await delay(4_000);
            return res(ctx.json({ predictions }));
        });

        registerApiResponse('CreateImageAnnotation', (req, res, ctx) => {
            return res(ctx.status(200), ctx.json({ annotation_state_per_task: [], ...req.body }));
        });

        await page.goto(annotatorUrl);

        await annotationListPage.expectTotalAnnotationsToBe(4);

        await selectPredictionMode(page);
        await usePredictions(page);
        await page.getByRole('button', { name: 'Replace' }).click();

        await annotationListPage.expectTotalAnnotationsToBe(6);
    });

    // Issue: UI assumes user has made changes to predictions when switching between Active Learning and AI mode
    test.fixme(
        'It does not cache predictions from a previous model',
        async ({ page, registerApiResponse, openApi }) => {
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.status(204)));
            registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.json({ predictions })));
            registerApiResponse('FilterMedia', (_, res, ctx) => {
                const { mock, status } = openApi.mockResponseForOperation('FilterMedia') as {
                    status: number;
                    mock: OpenApiResponseBody<'FilterMedia'>;
                };

                // @ts-expect-error this field is not yet set to be required
                mock.media[0].name = 'Test image';

                return res(ctx.status(status), ctx.json({ ...mock, next_page: '' }));
            });

            await page.goto(annotatorUrl);

            await selectPredictionMode(page);

            const labels = page.getByLabel('annotations').getByLabel('labels');
            await expect(labels).toHaveCount(predictions.length);

            await page.getByRole('button', { name: /back/i }).click();

            // Reopen the same image with new predictions
            const newPredictions = [
                ...predictions,
                ...annotations.map((annotation) => ({
                    ...annotation,
                    labels: annotation.labels.map(toPredictionLabel),
                })),
            ];
            registerApiResponse('GetSinglePrediction', (_, res, ctx) => {
                return res(ctx.json({ predictions: newPredictions }));
            });

            registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.json({ predictions: newPredictions })));

            await page.getByRole('img', { name: /test image/i }).dblclick();

            await selectPredictionMode(page);

            const newlabels = page.getByLabel('annotations').getByLabel('labels');
            await expect(newlabels).toHaveCount(newPredictions.length);
        }
    );

    test('annotator page elements', async ({ page, registerApiExample }) => {
        registerApiExample('GetProjectStatus', 'Waiting for classification annotations');

        await page.goto(annotatorUrl);
        await waitForLoadingToBeFinished(page);

        await expect(page.getByTestId('project-name-domain-id')).toHaveText(
            'Example Segmentation project@ Segmentation'
        );

        await checkNumberOfTools(page, 8);

        await checkSegmentationTools(page);

        await checkCommonElements(page, DOMAIN.SEGMENTATION);
    });

    test.describe('Explanation', () => {
        test('empty explanation', async ({ page, registerApiResponse, explanation }) => {
            registerApiResponse('GetSingleExplanation', (_, res, ctx) => res(ctx.json({ maps: [] })));

            await page.goto(`${annotatorUrl}?mode=predictions`);

            const explanationButton = await explanation.getExplanationButton();

            await expect(explanationButton).toBeDisabled();
        });

        test('replace user annotations with predictions', async ({ page, registerApiResponse, explanation }) => {
            registerApiResponse('CreateImageAnnotation', (req, res, ctx) =>
                res(ctx.status(200), ctx.json({ annotation_state_per_task: [], ...req.body }))
            );

            await page.goto(`${annotatorUrl}?mode=predictions`);

            await explanation.activateTool();

            const newlabels = page.getByLabel('Annotator canvas').getByLabel('annotations').getByLabel('labels');
            await expect(newlabels).toHaveCount(predictions.length);
        });
    });
});

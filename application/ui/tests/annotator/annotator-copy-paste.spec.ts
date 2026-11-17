// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { expect } from '@playwright/test';
import { getMockedMediaImage } from 'mocks/mock-media';
import { getMockedModel } from 'mocks/mock-model';
import { getMockedVariant } from 'mocks/mock-model-variant';
import { HttpResponse } from 'msw';

import type { AnnotatorPage } from '../datasets/annotator-page';
import { http, test } from '../fixtures';
import { mockedDetectionProject, useDetectionProjectFixtures } from './annotator-fixtures';

const mediaItems = [
    getMockedMediaImage({ id: 'item-1', name: 'item-1.jpg', width: 1920, height: 1080 }),
    getMockedMediaImage({ id: 'item-2', name: 'item-2.jpg', width: 1920, height: 1080 }),
];

const expectAnnotationsCount = (
    annotatorPage: AnnotatorPage,
    label: Parameters<AnnotatorPage['getAnnotationsListItems']>[0],
    count: number
) => expect(annotatorPage.getAnnotationsList().getByLabel(label)).toHaveCount(count);

const box = { x: 100, y: 100, width: 150, height: 150 };

test.describe('Annotator - copy and paste annotations', () => {
    useDetectionProjectFixtures();

    test.beforeEach(async ({ network }) => {
        network.use(
            http.get('/api/projects/{project_id}/dataset/media', () => {
                return HttpResponse.json({
                    items: mediaItems,
                    pagination: { offset: 0, limit: 10, count: mediaItems.length, total: mediaItems.length },
                });
            })
        );
    });

    test('cascades pasted copies on the same media and pastes at original coordinates on another', async ({
        page,
        annotatorPage,
        boundingBoxTool,
    }) => {
        await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

        await test.step('Draw a box and copy it', async () => {
            await boundingBoxTool.selectTool();
            await boundingBoxTool.drawBoundingBox(box);
            await expectAnnotationsCount(annotatorPage, 'annotation rect', 1);

            await page.keyboard.press('Control+c');

            await expect(page.getByText('1 annotation copied')).toBeVisible();
        });

        const [original] = await annotatorPage.getAnnotationRectBoxes();

        await test.step('Pasted copies on the same media cascade down-right', async () => {
            await page.keyboard.press('Control+v');
            await expectAnnotationsCount(annotatorPage, 'annotation rect', 2);

            await page.keyboard.press('Control+v');
            await expectAnnotationsCount(annotatorPage, 'annotation rect', 3);

            const [, first, second] = await annotatorPage.getAnnotationRectBoxes();

            expect(first.x).toBeGreaterThan(original.x);
            expect(first.y).toBeGreaterThan(original.y);
            expect(second.x).toBeGreaterThan(first.x);
            expect(second.y).toBeGreaterThan(first.y);
        });

        await test.step('Paste on another media lands at the original coordinates', async () => {
            await annotatorPage.selectMediaItem('item-2.jpg');
            await expect(annotatorPage.getSelectedMediaItem()).toHaveAttribute('alt', 'item-2.jpg');
            await annotatorPage.waitForMediaLoaded();
            await expectAnnotationsCount(annotatorPage, 'annotation rect', 0);

            await page.keyboard.press('Control+v');
            await expectAnnotationsCount(annotatorPage, 'annotation rect', 1);

            const [pasted] = await annotatorPage.getAnnotationRectBoxes();

            expect(pasted.x).toBeCloseTo(original.x, 0);
            expect(pasted.y).toBeCloseTo(original.y, 0);
        });
    });

    test('undo removes the whole pasted batch in one step', async ({ page, annotatorPage, boundingBoxTool }) => {
        await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

        await boundingBoxTool.selectTool();
        await boundingBoxTool.drawBoundingBox(box);
        await boundingBoxTool.drawBoundingBox({ x: 400, y: 300, width: 100, height: 100 });
        await expectAnnotationsCount(annotatorPage, 'annotation rect', 2);

        await test.step('Copy both annotations and paste them as one batch', async () => {
            await page.keyboard.press('Control+a');
            await page.keyboard.press('Control+c');
            await expect(page.getByText('2 annotations copied')).toBeVisible();

            await page.keyboard.press('Control+v');
            await expectAnnotationsCount(annotatorPage, 'annotation rect', 4);
        });

        await test.step('A single undo removes both pasted annotations', async () => {
            await annotatorPage.undo();

            await expectAnnotationsCount(annotatorPage, 'annotation rect', 2);
        });
    });

    test('paste does nothing in prediction mode', async ({ page, annotatorPage, boundingBoxTool, network }) => {
        network.use(
            http.get('/api/projects/{project_id}/models', async () => {
                return HttpResponse.json([getMockedModel({ variants: [getMockedVariant({})] })]);
            }),
            http.post('/api/projects/{project_id}/dataset/media:predict', async () => {
                return HttpResponse.json({ predictions: [{ media: { id: 'item-1' }, prediction: [] }] });
            })
        );

        await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

        await boundingBoxTool.selectTool();
        await boundingBoxTool.drawBoundingBox(box);
        await expectAnnotationsCount(annotatorPage, 'annotation rect', 1);

        await page.keyboard.press('Control+c');
        await expect(page.getByText('1 annotation copied')).toBeVisible();

        await annotatorPage.openPredictionMode();
        await expect(annotatorPage.getAnnotatorMode('prediction')).toHaveAttribute('aria-pressed', 'true');

        await page.keyboard.press('Control+v');

        await expectAnnotationsCount(annotatorPage, 'annotation rect', 0);
        await expectAnnotationsCount(annotatorPage, 'prediction rect', 0);

        await annotatorPage.openAnnotationMode();

        await expectAnnotationsCount(annotatorPage, 'annotation rect', 1);
    });

    test('hotkeys list shows the copy and paste rows', async ({ page, annotatorPage }) => {
        await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

        await annotatorPage.openHotkeys();

        const dialog = page.getByRole('dialog');

        await expect(dialog.getByText('Copy selected annotations')).toBeVisible();
        await expect(dialog.getByText('Paste annotations')).toBeVisible();
    });
});

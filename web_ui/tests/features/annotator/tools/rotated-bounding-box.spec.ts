// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect } from '@playwright/test';

import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { annotatorUrl, media, project } from '../../../mocks/detection-oriented/mocks';

test.describe('Rotated bounding box', () => {
    const startingPoint = { x: 150, y: 350 };
    const endPoint = { x: 300, y: 300 };

    test.beforeEach(async ({ registerApiResponse, page, annotatorPage }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));

        await page.goto(annotatorUrl, { timeout: 15000 });
        await annotatorPage.deleteAllAnnotations();
    });

    test('Draw rotated bounding box', async ({ page, rotatedBoundingBoxTool }) => {
        await rotatedBoundingBoxTool.drawRotatedBoundingBox(startingPoint, endPoint);
        await rotatedBoundingBoxTool.checkRotationIndicatorAtDefaultPosition(startingPoint);

        expect(await page.getByLabel(/Labels of annotation with id/).count()).toBe(1);
    });

    test('Undo and redo rotated bounding box', async ({ rotatedBoundingBoxTool, undoRedo, annotationListPage }) => {
        await rotatedBoundingBoxTool.drawRotatedBoundingBox(startingPoint, endPoint);

        await annotationListPage.expectTotalAnnotationsToBe(1);

        await undoRedo.undoUsingButton();

        await annotationListPage.expectTotalAnnotationsToBe(0);

        await undoRedo.redoUsingButton();

        await annotationListPage.expectTotalAnnotationsToBe(1);

        await undoRedo.undoUsingShortcut();

        await annotationListPage.expectTotalAnnotationsToBe(0);

        await undoRedo.redoUsingShortcut();

        await annotationListPage.expectTotalAnnotationsToBe(1);
    });

    test('Draw rotated bounding box and check if rotating indicator is visible', async ({ rotatedBoundingBoxTool }) => {
        const newStartingPoint = { x: 250, y: 350 };
        const newEndPoint = { x: 300, y: 350 };

        await rotatedBoundingBoxTool.drawRotatedBoundingBox(newStartingPoint, newEndPoint);
        await rotatedBoundingBoxTool.checkIfRotationIndicatorIsVisible();

        await rotatedBoundingBoxTool.moveResizeAnchor({ x: -250, y: 0 }, 'North resize anchor');
        await rotatedBoundingBoxTool.checkIfRotationIndicatorIsVisible();

        await rotatedBoundingBoxTool.moveResizeAnchor({ x: 0, y: 300 }, 'West resize anchor');
        await rotatedBoundingBoxTool.checkIfRotationIndicatorIsVisible();

        await rotatedBoundingBoxTool.moveResizeAnchor({ x: 650, y: 0 }, 'South resize anchor');
        await rotatedBoundingBoxTool.checkIfRotationIndicatorIsVisible();

        await rotatedBoundingBoxTool.moveResizeAnchor({ x: 0, y: -450 }, 'East resize anchor');
        await rotatedBoundingBoxTool.checkIfRotationIndicatorIsVisible();
    });

    test('Selects rotated bounding box tool using hotkey', async ({ page }) => {
        // Change to bounding tool first
        await page.keyboard.press('b');

        await expect(page.locator('role=button[name="Bounding Box"]')).toHaveAttribute('aria-pressed', 'true');

        await page.keyboard.press('r');

        await expect(page.getByRole('button', { name: 'Rotated Bounding Box' })).toHaveAttribute(
            'aria-pressed',
            'true'
        );

        // Check correct mouse cursor
        await page.mouse.move(100, 100);
        await expect(page.locator('[role=editor]')).not.toHaveAttribute('style');
    });
});

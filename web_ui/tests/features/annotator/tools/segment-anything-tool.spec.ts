// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Locator } from '@playwright/test';

import { pointInRectangle } from '../../../../src/core/annotations/math';
import { Rect, RotatedRect } from '../../../../src/core/annotations/shapes.interface';
import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { annotatorUrl, userAnnotationsResponse } from '../../../mocks/classification/mocks';
import * as detectionClassificationMocks from '../../../mocks/detection-classification/mocks';
import * as detectionOrientedMocks from '../../../mocks/detection-oriented/mocks';
import * as detectionSegmentationMocks from '../../../mocks/detection-segmentation/mocks';
import * as detectionMocks from '../../../mocks/detection/mocks';
import { media, project } from '../../../mocks/segmentation/mocks';
import { registerFullImage } from '../../../utils/api';
import { resolveTestAssetPath } from '../../../utils/dataset';
import { withRelative } from '../../../utils/mouse';
import { getPolylineArea, getPolylinePoints } from '../utils';

const expectBoundingBox = async (boundingBox: Locator, { x, y, width, height }: Omit<Rect, 'shapeType'>) => {
    const actualX = Math.round(Number(await boundingBox.getAttribute('x')));
    const actualY = Math.round(Number(await boundingBox.getAttribute('y')));
    const actualWidth = Math.round(Number(await boundingBox.getAttribute('width')));
    const actualHeight = Math.round(Number(await boundingBox.getAttribute('height')));

    expect.soft(actualX).toBeCloseTo(x, 0);
    expect.soft(actualY).toBeCloseTo(y, 0);
    expect.soft(actualWidth).toBeCloseTo(width, -1);
    expect.soft(actualHeight).toBeCloseTo(height, -1);
};
const expectRotatedBoundingBox = async (
    rotatedBoundingBox: Locator,
    { angle, ...boundingBox }: Omit<RotatedRect, 'shapeType'>
) => {
    await expectBoundingBox(rotatedBoundingBox, boundingBox);

    const transform = await rotatedBoundingBox.getAttribute('transform');
    const actualAngle = Math.round(Number(transform?.match(/\d+.\d+/)?.at(0)));
    expect.soft(actualAngle).toBeCloseTo(angle, 0);
};

test.beforeEach(({ registerApiResponse }) => {
    registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
    registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
    registerFullImage(registerApiResponse, resolveTestAssetPath('multiple-cards.webp'));
    registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
        res(ctx.json({ ...userAnnotationsResponse, annotations: [] }))
    );
    registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.json({ predictions: [] })));
});

test.describe('Segment anything', () => {
    // TODO: Unskip that test once root cause issue of flakiness is fixed
    test.skip('It segments all cards with a single click', async ({
        page,
        segmentAnythingTool,
        annotationListPage,
    }) => {
        await page.goto(annotatorUrl, { timeout: 10000 });

        await segmentAnythingTool.selectTool();

        const relative = await withRelative(page);

        const successivePoints = [
            { x: 637, y: 428 },
            { x: 593, y: 402 },
            { x: 472, y: 138 },
            { x: 107, y: 271 },
            { x: 119, y: 567 },
            { x: 327, y: 243 },
            { x: 346, y: 472 },
            { x: 326, y: 721 },
            { x: 301, y: 821 },
            { x: 525, y: 782 },
        ];

        for (const p of successivePoints) {
            const { x, y } = relative(p.x, p.y);
            await page.mouse.click(x, y);
            await segmentAnythingTool.waitForResultShape();
        }

        await annotationListPage.expectTotalAnnotationsToBe(10);
    });

    test('It segments an object by clicking on it', async ({ page, segmentAnythingTool }) => {
        await page.goto(annotatorUrl);

        await segmentAnythingTool.selectTool();
        await segmentAnythingTool.enableInteractiveMode();
        const relative = await withRelative(page);

        const [pointOncard, pointOnOtherCard] = [relative(675, 419), relative(594, 406)];
        // Add 2 positive points with left click
        await page.mouse.click(pointOncard.x, pointOncard.y);

        await expect(page.getByLabel(/positive interactive segmentation point/i)).toHaveCount(1);
        await expect(page.getByLabel('Segment anything result')).toBeVisible();

        // Get polyline and calculate its area
        const initialPolyline = await segmentAnythingTool.getResultShape();
        const initialPolylineArea = await getPolylineArea(initialPolyline);

        // Add a negative point so that only 1 card is selected
        await page.mouse.click(pointOnOtherCard.x, pointOnOtherCard.y);
        await expect(page.getByLabel(/negative interactive segmentation point/i)).toHaveCount(1);

        await expect(async () => {
            const finalPolyline = await segmentAnythingTool.getResultShape();
            const finalPolylineArea = await getPolylineArea(finalPolyline);

            expect(finalPolylineArea).toBeLessThan(initialPolylineArea);
        }).toPass({ timeout: 1500 });

        // Check that the resulting annotation touches the image's right side
        const polylinePoints = await getPolylinePoints(await segmentAnythingTool.getResultShape());
        const rightMostPoint = Math.max(...polylinePoints.map((point) => point.x));
        expect(rightMostPoint).toEqual(719);
    });

    test('Does not segment the background', async ({ page, segmentAnythingTool }) => {
        await page.goto(annotatorUrl);

        await segmentAnythingTool.selectTool();
        await segmentAnythingTool.enableInteractiveMode();

        const relative = await withRelative(page);

        const backgroundPoint = relative(100, 100);
        await page.mouse.click(backgroundPoint.x, backgroundPoint.y);

        await expect(page.getByLabel(/positive interactive segmentation point/i)).toHaveCount(1);
        await expect(page.getByLabel('Segment anything result')).toBeHidden();
        await expect(page.getByRole('button', { name: 'accept segment-anything annotation' })).toBeDisabled();
    });

    test('Should use the correct cursor', async ({ page, segmentAnythingTool }) => {
        await page.goto(annotatorUrl);

        await segmentAnythingTool.selectTool();
        await page.mouse.move(100, 100);

        expect(await page.locator('[role=editor]').getAttribute('style')).toContain('selection');

        await segmentAnythingTool.enableInteractiveMode();

        expect(await page.locator('[role=editor]').getAttribute('style')).toContain('pencil-plus');
    });

    test('Should display the correct tooltips', async ({ page, segmentAnythingTool }) => {
        await page.goto(annotatorUrl);

        await segmentAnythingTool.selectTool();

        const autoAcceptModeButton = page.getByRole('switch', { name: 'Interactive mode' });
        await autoAcceptModeButton.hover();

        await expect(
            page.getByText('With this mode ON, edit preview by placing new positive or negative points. - SHIFT')
        ).toBeVisible();

        await autoAcceptModeButton.click();
        const rightClickModeButtonSAM = page.getByRole('switch', { name: 'Right-click mode' });
        await rightClickModeButtonSAM.hover();

        await expect(
            page.getByText(
                'With this mode ON, press left-click to place positive points and right-click to place negative points.'
            )
        ).toBeVisible();
    });

    test.describe('Using auto segmentation in other project types', () => {
        test('Rotated bounding boxes can be created with segment anything', async ({
            page,
            annotationListPage,
            segmentAnythingTool,
            registerApiResponse,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionOrientedMocks.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(detectionOrientedMocks.media)));

            await page.goto(detectionOrientedMocks.annotatorUrl, { timeout: 15000 });

            await segmentAnythingTool.selectTool();
            await segmentAnythingTool.enableInteractiveMode();

            const relative = await withRelative(page);

            const { x, y } = relative(119, 567);
            await page.mouse.click(x, y);
            const rotatedBoundingBox = await segmentAnythingTool.getResultShape();

            await expect(rotatedBoundingBox).toBeVisible();

            const expectedRotatedBoundingBox = { x: 1.4, y: 452, width: 137, height: 216, angle: 22 };
            await expectRotatedBoundingBox(rotatedBoundingBox, expectedRotatedBoundingBox);

            await segmentAnythingTool.acceptAnnotation();
            await annotationListPage.expectTotalAnnotationsToBe(1);
        });

        test('Bounding boxes can be created with segment anything', async ({
            page,
            annotationListPage,
            segmentAnythingTool,
            registerApiResponse,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionMocks.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(detectionMocks.media)));

            await page.goto(detectionMocks.annotatorUrl, { timeout: 15000 });

            await segmentAnythingTool.selectTool();
            await segmentAnythingTool.enableInteractiveMode();

            const relative = await withRelative(page);

            const { x, y } = relative(119, 567);
            await page.mouse.click(x, y);
            const boundingBox = await segmentAnythingTool.getResultShape();

            await expect(boundingBox).toBeVisible();

            const expectedBoundingBox = { x: 0, y: 441, width: 172, height: 241 };
            await expectBoundingBox(boundingBox, expectedBoundingBox);

            await segmentAnythingTool.acceptAnnotation();
            await annotationListPage.expectTotalAnnotationsToBe(1);
        });

        test('Bounding boxes can be created with segment anything in a detection classification project', async ({
            page,
            annotationListPage,
            segmentAnythingTool,
            registerApiResponse,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionClassificationMocks.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(detectionClassificationMocks.media)));

            await page.goto(detectionClassificationMocks.annotatorUrl, { timeout: 15000 });

            await segmentAnythingTool.selectTool();
            await segmentAnythingTool.enableInteractiveMode();

            const relative = await withRelative(page);

            const { x, y } = relative(119, 567);
            await page.mouse.click(x, y);
            const boundingBox = await segmentAnythingTool.getResultShape();

            await expect(boundingBox).toBeVisible();

            const expectedBoundingBox = { x: 0, y: 441, width: 172, height: 241 };
            await expectBoundingBox(boundingBox, expectedBoundingBox);

            await segmentAnythingTool.acceptAnnotation();
            await annotationListPage.expectTotalAnnotationsToBe(1);
        });

        test(`Polygons can be created with segment anything in a detection segmentation project`, async ({
            page,
            annotationListPage,
            segmentAnythingTool,
            registerApiResponse,
        }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(detectionSegmentationMocks.project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(detectionSegmentationMocks.media)));

            const selectedInput = { x: 562, y: 391, width: 157, height: 244 };
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => {
                const response = detectionSegmentationMocks.userAnnotationsResponse;
                const annotations = [
                    {
                        ...response.annotations[0],
                        shape: { type: 'RECTANGLE', ...selectedInput },
                    },
                ];
                return res(ctx.json({ ...response, annotations }));
            });

            await page.goto(`${detectionSegmentationMocks.annotatorUrl}?task-id=635fce72fc03e87df9becd12`, {
                timeout: 15000,
            });

            await segmentAnythingTool.selectTool();
            await segmentAnythingTool.enableInteractiveMode();

            const relative = await withRelative(page);

            const { x, y } = relative(675, 419);
            await page.mouse.click(x, y);

            await segmentAnythingTool.waitForResultShape();
            const polygon = await segmentAnythingTool.getResultShape();
            const points = await getPolylinePoints(polygon);
            points.forEach((point) => expect(pointInRectangle(selectedInput, point)).toBeTruthy());

            await segmentAnythingTool.acceptAnnotation();
            await annotationListPage.expectTotalAnnotationsToBe(1);
        });
    });
});

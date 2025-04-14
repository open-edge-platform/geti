// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Locator, Page } from '@playwright/test';

import { Point } from '../../../src/core/annotations/shapes.interface';
import { EMPTY_LABEL_MESSAGE, MIN_POINTS_MESSAGE } from '../../../src/pages/create-project/utils';
import { delay } from '../../../src/shared/utils';
import { expect } from '../../fixtures/base-test';
import { TemplateManagerPage } from '../../fixtures/page-objects/template-manager';
import { expectProjectToHaveType } from './expect';
import { testWithOpenApi as test } from './fixtures';

test.use({ featureFlags: { FEATURE_FLAG_KEYPOINT_DETECTION: true } });

const addAndVerifyPointPosition = async ({
    templateManagerPage,
    selector,
    position,
}: {
    templateManagerPage: TemplateManagerPage;
    selector: Locator;
    position: Point;
}) => {
    await templateManagerPage.addPoint(position);

    const pointPosition = await templateManagerPage.getPointPosition(selector);
    expect(pointPosition.cx).toBeCloseTo(position.x, 10);
    expect(pointPosition.cy).toBeCloseTo(position.y, 10);
};

const renameAndVerifyPoint = async ({
    page,
    oldValue,
    newValue,
}: {
    page: Page;
    oldValue: string;
    newValue: string;
}) => {
    await page.getByLabel(`keypoint ${oldValue} anchor`).click();
    await expect(page.getByTestId(`pose label - ${oldValue}`)).toBeVisible();
    await page.getByLabel('label name input').fill(newValue);

    await expect(page.getByLabel(`pose label - ${oldValue}`)).not.toBeInViewport();
    await expect(page.getByTestId(`pose label - ${newValue}`)).toBeVisible();
};

test.describe('Keypoint detection', () => {
    test('Create project', async ({ createProjectPage }) => {
        const projectPage = await createProjectPage.keypointDetection('Playwright keypoint detection');

        await expectProjectToHaveType(projectPage, 'Keypoint detection');
    });

    test('validate keypoints and enable creation of other projects', async ({ page, createProjectPage }) => {
        await createProjectPage.keypointDetectionTemplate('Playwright keypoint detection');

        const createButton = page.getByRole('button', { name: 'Create' });
        await expect(createButton).toBeDisabled();
        // eslint-disable-next-line playwright/no-force-option
        await createButton.hover({ force: true });
        await expect(page.getByText(MIN_POINTS_MESSAGE)).toBeVisible();

        await page.getByRole('button', { name: 'Back' }).click();
        await page.getByRole('button', { name: 'Back' }).click();

        await createProjectPage.detection('detection project', ['Fish']);
    });

    test.describe('pose template', () => {
        test('adds multiple points and connects them', async ({ page, createProjectPage, templateManagerPage }) => {
            await createProjectPage.keypointDetectionTemplate('Playwright keypoint detection');

            await page.getByRole('button', { name: 'Back' }).click();
            await page.getByRole('button', { name: 'Next' }).click();

            await addAndVerifyPointPosition({
                templateManagerPage,
                position: { x: 100, y: 100 },
                selector: page.getByLabel('keypoint 1 anchor'),
            });

            await addAndVerifyPointPosition({
                templateManagerPage,
                position: { x: 200, y: 200 },
                selector: page.getByLabel('keypoint 2 anchor'),
            });

            await addAndVerifyPointPosition({
                templateManagerPage,
                position: { x: 300, y: 300 },
                selector: page.getByLabel('keypoint 3 anchor'),
            });

            await templateManagerPage.connectPoints(page, '3', '2');
            await templateManagerPage.connectPoints(page, '1', '2');
        });

        test('disables project creation when no points are present', async ({
            page,
            createProjectPage,
            templateManagerPage,
        }) => {
            await createProjectPage.keypointDetectionTemplate('Playwright keypoint detection');

            await expect(page.getByRole('button', { name: 'Create' })).toBeDisabled();

            await templateManagerPage.addPoint({ x: 100, y: 100 });

            await expect(page.getByRole('button', { name: 'Create' })).toBeEnabled();
        });

        test('adds new connected points while holding shift key', async ({
            page,
            createProjectPage,
            templateManagerPage,
        }) => {
            await createProjectPage.keypointDetectionTemplate('Playwright keypoint detection');

            await templateManagerPage.addPoint({ x: 100, y: 100 });
            await page.keyboard.down('Shift');
            await templateManagerPage.addPoint({ x: 200, y: 200 });
            await templateManagerPage.addPoint({ x: 300, y: 300 });
            await page.keyboard.up('Shift');

            await expect(page.getByLabel(`hidden padded edge 1 - 2`)).toBeInViewport();
            await expect(page.getByLabel(`hidden padded edge 2 - 3`)).toBeInViewport();

            await templateManagerPage.addPoint({ x: 200, y: 300 });
            await expect(page.getByLabel(`hidden padded edge 3 - 4`)).not.toBeInViewport();
        });

        test('adds new points connected to an existing one while holding shift', async ({
            page,
            createProjectPage,
            templateManagerPage,
        }) => {
            await createProjectPage.keypointDetectionTemplate('Playwright keypoint detection');

            await templateManagerPage.addPoint({ x: 100, y: 100 });
            await templateManagerPage.addPoint({ x: 200, y: 200 });
            await templateManagerPage.addPoint({ x: 300, y: 300 });

            await page.getByLabel('keypoint 2 anchor').click();
            await page.keyboard.down('Shift');
            await templateManagerPage.addPoint({ x: 400, y: 200 });
            await page.keyboard.up('Shift');

            await expect(page.getByLabel(`hidden padded edge 1 - 2`)).not.toBeInViewport();
            await expect(page.getByLabel(`hidden padded edge 2 - 3`)).not.toBeInViewport();
            await expect(page.getByLabel(`hidden padded edge 2 - 4`)).toBeInViewport();
        });

        test.describe('edges', () => {
            test('prevents duplicates', async ({ page, createProjectPage, templateManagerPage }) => {
                await createProjectPage.keypointDetectionTemplate('Playwright keypoint detection');

                await templateManagerPage.addMultipleConnectedPoints([
                    { x: 100, y: 100 },
                    { x: 200, y: 200 },
                    { x: 300, y: 300 },
                ]);

                await expect(page.getByLabel(`hidden padded edge 1 - 2`)).toBeInViewport();

                await page.getByLabel('keypoint 1 anchor').click();
                await page.getByLabel(`link keypoint 1`).click();
                await page.getByLabel('keypoint 2 anchor').click();

                await expect(page.getByLabel(`hidden padded edge 1 - 2`)).toHaveCount(1);
            });

            test('moving one point reposition connected edges', async ({
                page,
                createProjectPage,
                templateManagerPage,
            }) => {
                await createProjectPage.keypointDetectionTemplate('Playwright keypoint detection');

                await templateManagerPage.addMultipleConnectedPoints([
                    { x: 100, y: 100 },
                    { x: 200, y: 200 },
                    { x: 300, y: 300 },
                ]);

                const point = page.getByLabel('keypoint 2 anchor');
                const initialPosition = await templateManagerPage.getPosition(point);
                const newPosition = { x: initialPosition.x + 100, y: initialPosition.y };

                const edgeOne = page.getByLabel(`hidden padded edge 1 - 2`);
                const edgeTwo = page.getByLabel(`hidden padded edge 2 - 3`);

                expect(await templateManagerPage.isLineInContactWithPoint(edgeOne, point)).toBe(true);
                expect(await templateManagerPage.isLineInContactWithPoint(edgeTwo, point)).toBe(true);

                await templateManagerPage.movePointTo(page, point, newPosition);

                expect(await templateManagerPage.getPosition(point)).toEqual(newPosition);
                expect(await templateManagerPage.isLineInContactWithPoint(edgeOne, point)).toBe(true);
                expect(await templateManagerPage.isLineInContactWithPoint(edgeTwo, point)).toBe(true);
            });

            test('removes a point and deletes all connected edges', async ({
                page,
                createProjectPage,
                templateManagerPage,
            }) => {
                await createProjectPage.keypointDetectionTemplate('Playwright keypoint detection');

                await templateManagerPage.addMultipleConnectedPoints([
                    { x: 100, y: 100 },
                    { x: 200, y: 100 },
                    { x: 300, y: 100 },
                ]);

                await expect(page.getByLabel(`hidden padded edge 1 - 2`)).toBeInViewport();
                await expect(page.getByLabel(`hidden padded edge 2 - 3`)).toBeInViewport();

                await templateManagerPage.deletePoint('2');

                await expect(page.getByLabel(`keypoint 2 anchor`)).not.toBeInViewport();
                await expect(page.getByLabel(`hidden padded edge 1 - 2`)).not.toBeInViewport();
                await expect(page.getByLabel(`hidden padded edge 2 - 3`)).not.toBeInViewport();

                await renameAndVerifyPoint({ page, oldValue: '1', newValue: 'test 111' });
            });

            test('deletes edges using the context menu', async ({ page, createProjectPage, templateManagerPage }) => {
                await createProjectPage.keypointDetectionTemplate('Playwright keypoint detection');

                await templateManagerPage.addPoint({ x: 100, y: 100 });
                await page.getByLabel(`link keypoint 1`).click();

                await templateManagerPage.addPoint({ x: 200, y: 100 });

                await expect(page.getByLabel(`hidden padded edge 1 - 2`)).toBeInViewport();

                await templateManagerPage.openEdgeMenu('hidden padded edge 1 - 2');
                await page.getByLabel('delete edge 1 - 2').click();

                await expect(page.getByLabel(`hidden padded edge 1 - 2`)).not.toBeInViewport();
            });

            test('insert intermediate points along an edge', async ({
                page,
                createProjectPage,
                templateManagerPage,
            }) => {
                await createProjectPage.keypointDetectionTemplate('Playwright keypoint detection');

                await templateManagerPage.addMultipleConnectedPoints([
                    { x: 100, y: 100 },
                    { x: 600, y: 100 },
                ]);

                const originalLine = page.getByLabel('hidden padded edge 1 - 2');
                const position = await templateManagerPage.getPosition(originalLine);

                await page.mouse.move(position.x, position.y, { steps: 20 });
                await page.mouse.click(position.x, position.y);

                const newPoint = page.getByLabel('keypoint 3 anchor');
                await templateManagerPage.movePointTo(page, newPoint, { ...position, y: position.y + 100 });

                await expect(page.getByLabel('hidden padded edge 1 - 3')).toBeInViewport();
                await expect(page.getByLabel('hidden padded edge 2 - 3')).toBeInViewport();
                await expect(page.getByLabel('hidden padded edge 1 - 2')).not.toBeInViewport();
            });
        });

        test.describe('undo/redo', () => {
            test('move point position', async ({ page, createProjectPage, templateManagerPage }) => {
                await createProjectPage.keypointDetectionTemplate('Playwright keypoint detection');

                await expect(page.getByRole('button', { name: 'Create' })).toBeDisabled();

                await templateManagerPage.addMultipleConnectedPoints([
                    { x: 100, y: 100 },
                    { x: 100, y: 200 },
                    { x: 100, y: 300 },
                ]);

                const initialPosition = await templateManagerPage.getPosition(page.getByLabel('keypoint 2 anchor'));
                const newPosition = { x: initialPosition.x + 100, y: initialPosition.y };

                await templateManagerPage.movePointTo(page, page.getByLabel('keypoint 2 anchor'), newPosition);

                expect(await templateManagerPage.getPosition(page.getByLabel('keypoint 2 anchor'))).toEqual(
                    newPosition
                );

                await page.getByLabel('undo').click();
                expect(await templateManagerPage.getPosition(page.getByLabel('keypoint 2 anchor'))).toEqual(
                    initialPosition
                );

                await page.getByLabel('redo').click();
                expect(await templateManagerPage.getPosition(page.getByLabel('keypoint 2 anchor'))).toEqual(
                    newPosition
                );
            });

            test('remove point and associated edges, then undo the action', async ({
                page,
                createProjectPage,
                templateManagerPage,
            }) => {
                await createProjectPage.keypointDetectionTemplate('Playwright keypoint detection');

                await expect(page.getByRole('button', { name: 'Create' })).toBeDisabled();

                await templateManagerPage.addMultipleConnectedPoints([
                    { x: 100, y: 100 },
                    { x: 100, y: 200 },
                    { x: 100, y: 300 },
                ]);

                await templateManagerPage.deletePoint('2');

                await expect(page.getByLabel('keypoint 2')).not.toBeInViewport();
                await expect(page.getByLabel('hidden padded edge 1 - 2')).not.toBeInViewport();
                await expect(page.getByLabel('hidden padded edge 2 - 3')).not.toBeInViewport();

                await page.getByLabel('undo').click();

                await expect(page.getByLabel('keypoint 2 anchor')).toBeVisible();
                await expect(page.getByLabel('hidden padded edge 1 - 2')).toBeInViewport();
                await expect(page.getByLabel('hidden padded edge 2 - 3')).toBeInViewport();
            });
        });

        test.describe('label editing', () => {
            test('change color', async ({ page, createProjectPage, templateManagerPage }) => {
                await createProjectPage.keypointDetectionTemplate('Playwright keypoint detection');

                await expect(page.getByRole('button', { name: 'Create' })).toBeDisabled();

                await templateManagerPage.addMultipleConnectedPoints([
                    { x: 400, y: 100 },
                    { x: 400, y: 200 },
                    { x: 400, y: 300 },
                ]);

                const point = page.getByLabel('keypoint 3 anchor');

                await point.click();

                const initialPosition = await templateManagerPage.getPosition(point);
                const newPosition = { x: initialPosition.x + 100, y: initialPosition.y };
                await templateManagerPage.movePointTo(page, point, newPosition);

                await templateManagerPage.changeLabelColor(point, '#ffffff');

                await expect(page.getByRole('button', { name: 'white, color selector' })).toBeVisible();
                await expect(page.getByLabel('keypoint 3 circle')).toHaveAttribute('stroke', '#ffffff');

                expect(await templateManagerPage.getPosition(point)).toEqual(newPosition);
            });

            test('update name', async ({ page, createProjectPage, templateManagerPage }) => {
                await createProjectPage.keypointDetectionTemplate('Playwright keypoint detection');

                await expect(page.getByRole('button', { name: 'Create' })).toBeDisabled();

                await templateManagerPage.addMultipleConnectedPoints([
                    { x: 400, y: 100 },
                    { x: 400, y: 200 },
                    { x: 400, y: 300 },
                ]);

                await renameAndVerifyPoint({ page, oldValue: '1', newValue: 'test 111' });
                await renameAndVerifyPoint({ page, oldValue: '3', newValue: 'test 333' });
            });

            test('disables project creation when label names are empty', async ({
                page,
                createProjectPage,
                templateManagerPage,
            }) => {
                await createProjectPage.keypointDetectionTemplate('Playwright keypoint detection');

                await expect(page.getByRole('button', { name: 'Create' })).toBeDisabled();

                await templateManagerPage.addMultipleConnectedPoints([
                    { x: 400, y: 100 },
                    { x: 400, y: 200 },
                ]);

                await page.getByLabel('keypoint 1 anchor').click();
                await expect(page.getByRole('button', { name: 'Create' })).toBeEnabled();

                await page.getByLabel('label name input').clear();

                await expect(page.getByRole('button', { name: 'Create' })).toBeDisabled();
                await expect(page.getByText(EMPTY_LABEL_MESSAGE)).toBeVisible();
            });

            test('undo/redo does not update label name one letter at a time', async ({
                page,
                createProjectPage,
                templateManagerPage,
            }) => {
                await createProjectPage.keypointDetectionTemplate('Playwright keypoint detection');

                await expect(page.getByRole('button', { name: 'Create' })).toBeDisabled();

                await templateManagerPage.addPoint({ x: 400, y: 100 });

                const newLabelName = 'test 111';

                await renameAndVerifyPoint({ page, oldValue: '1', newValue: newLabelName });
                //keypress debounce delay
                await delay(200);

                await page.getByLabel('undo').click();
                await expect(page.getByLabel('label name input')).toHaveValue('1');

                await page.getByLabel('redo').click();
                await expect(page.getByLabel('label name input')).toHaveValue(newLabelName);
            });
        });
    });
});

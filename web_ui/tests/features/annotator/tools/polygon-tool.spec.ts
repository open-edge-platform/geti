// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { project } from '../../../mocks/segmentation/mocks';
import { clickAndMove, withRelative } from '../../../utils/mouse';
import { expectPolygonShape } from '../expect';
import { getAnnotationsCount, getPolylineArea } from '../utils';

const getPolygonShape = (page: Page) =>
    page.getByLabel('edit-annotations').getByLabel('Drag to move shape').locator('polygon');

const getNumberOfPoints = async (page: Page) => {
    return page.getByLabel(/Click to select point/).count();
};

const shape = {
    points: [
        { x: 300 + 33, y: 33 },
        { x: 300 + 33, y: 330 },
        { x: 300 + 330, y: 330 },
    ],
};

const shapeWithFivePoints = {
    points: [
        { x: 300 + 33, y: 33 },
        { x: 300 + 33, y: 330 },
        { x: 300 + 130, y: 450 },
        { x: 300 + 330, y: 330 },
        { x: 300 + 330, y: 33 },
    ],
};

test.describe('Polygon', () => {
    test.beforeEach(async ({ page, annotatorPath, polygonTool, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.status(200), ctx.json(project)));
        registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.status(204)));
        registerApiResponse('GetSinglePrediction', (_, res, ctx) => res(ctx.status(204)));

        await page.goto(annotatorPath);
        await polygonTool.selectTool();
    });

    test('Using default polygon tool', async ({ page, polygonTool }) => {
        await polygonTool.drawPolygon(shape);

        const shapeLocator = getPolygonShape(page);

        await expectPolygonShape(shapeLocator, shape);
    });

    test('Drawing a polygon partially outside of the image', async ({ page, polygonTool }) => {
        const imageWidth = 940;
        const shapeOutsideImage = {
            points: [
                { x: 800, y: 30 },
                { x: 800, y: 300 },
                { x: 800 + 300, y: 300 },
                { x: 800 + 300, y: 30 },
            ],
        };
        await polygonTool.drawPolygon(shapeOutsideImage, { asLasso: true, finishShape: true });

        const shapeLocator = getPolygonShape(page);

        // The algorithm that we use to optimize polygons shuffles the polygon's points, which
        // isn't handled by our expect call
        await expectPolygonShape(shapeLocator, {
            points: [
                { x: imageWidth, y: 300 },
                { x: 800, y: 300 },
                { x: 800, y: 30 },
                { x: imageWidth, y: 30 },
            ],
        });
    });

    test('Undo redo polygon', async ({ page, polygonTool, undoRedo, annotationListPage }) => {
        await polygonTool.drawPolygon(shape);

        await undoRedo.undoUsingButton();

        await annotationListPage.expectTotalAnnotationsToBe(0);

        await undoRedo.redoUsingButton();

        await annotationListPage.expectTotalAnnotationsToBe(1);

        await undoRedo.undoUsingShortcut();

        await annotationListPage.expectTotalAnnotationsToBe(0);

        await undoRedo.redoUsingShortcut();

        await annotationListPage.expectTotalAnnotationsToBe(1);

        const shapeLocator = getPolygonShape(page);

        await expectPolygonShape(shapeLocator, {
            ...shape,
            points: [...shape.points].reverse(),
        });
    });

    test('Snapping mode and free drawing', async ({ page, polygonTool }) => {
        //test_annotation_polygon_snapping_mode_and_free_drawing

        await expect(page.getByRole('switch', { name: 'Snapping mode' })).not.toBeChecked();
        await polygonTool.toggleSnappingMode({ hotkey: true });
        await expect(page.getByRole('switch', { name: 'Snapping mode' })).toBeChecked();

        const antelopePoints = [
            { x: 331.5384628426315, y: 261.08119345118854 },
            { x: 652.9059842101528, y: 233.7307661007612 },
            { x: 644.3589756631443, y: 113.21794558794069 },
            { x: 688.8034201075887, y: 190.99572336571845 },
            { x: 746.068377372546, y: 163.6452960152911 },
            { x: 579.4017107058793, y: 502.9615353315304 },
            { x: 559.7435910477597, y: 528.602560972556 },
            { x: 337.5213688255375, y: 505.52563789563294 },
        ];

        const antelopeShape = {
            points: antelopePoints,
        };

        await polygonTool.drawPolygon(antelopeShape, { asLasso: false, finishShape: false });

        const relative = await withRelative(page);

        const startPoint = relative(
            antelopePoints[antelopePoints.length - 1].x,
            antelopePoints[antelopePoints.length - 1].y
        );

        const relativeEndPoint = relative(antelopePoints[0].x, antelopePoints[0].y);

        await page.mouse.move(startPoint.x, startPoint.y);
        await page.mouse.down();
        await page.mouse.move(relativeEndPoint.x, relativeEndPoint.y);
        await page.mouse.up();
        await expect(page.getByRole('switch', { name: 'Snapping mode' })).toBeChecked();
    });

    test('Using smart polygon tool', async ({ page, polygonTool }) => {
        await page.getByRole('switch', { name: 'Snapping mode' }).check();

        // These points were recorded manually so that when used the polygon's
        // snapping mode will correctly annotate the antelope
        const antelopePoints = [
            { x: 331.5384628426315, y: 261.08119345118854 },
            { x: 476.8376081417768, y: 238.00427037426547 },
            { x: 607.6068389110076, y: 257.66239003238513 },
            { x: 652.9059842101528, y: 233.7307661007612 },
            { x: 600.7692320734006, y: 172.19230456229965 },
            { x: 661.4529927571614, y: 207.2350396050347 },
            { x: 644.3589756631443, y: 113.21794558794069 },
            { x: 671.7094030135717, y: 120.05555242554753 },
            { x: 644.3589756631443, y: 137.1495695195646 },
            { x: 688.8034201075887, y: 190.99572336571845 },
            { x: 717.8632491674177, y: 138.00427037426547 },
            { x: 700.7692320734006, y: 118.34615071614581 },
            { x: 689.6581209622896, y: 120.91025328024838 },
            { x: 707.6068389110076, y: 112.36324473323984 },
            { x: 709.3162406204092, y: 201.25213362212872 },
            { x: 746.068377372546, y: 163.6452960152911 },
            { x: 713.5897448939135, y: 236.29486866486374 },
            { x: 703.3333346375033, y: 283.30341567341077 },
            { x: 599.9145312186998, y: 389.2863216563167 },
            { x: 592.2222235263921, y: 447.40597977597486 },
            { x: 587.094018398187, y: 508.08974045973554 },
            { x: 579.4017107058793, y: 502.9615353315304 },
            { x: 576.8376081417767, y: 413.2179455879407 },
            { x: 574.2735055776742, y: 526.8931592631543 },
            { x: 559.7435910477597, y: 528.602560972556 },
            { x: 546.068377372546, y: 387.57691994691504 },
            { x: 417.008548312717, y: 361.08119345118854 },
            { x: 368.29059959476825, y: 510.6538430238381 },
            { x: 351.19658250075116, y: 515.7820481520432 },
            { x: 334.95726626143494, y: 453.3888857588808 },
            { x: 337.5213688255375, y: 505.52563789563294 },
            { x: 321.28205258622125, y: 473.0470054170005 },
            { x: 323.8461551503238, y: 417.49144986144495 },
            { x: 340.08547138964, y: 338.8589712289663 },
            { x: 325.5555568597255, y: 279.0299113999065 },
            { x: 312.29034488347315, y: 300.1691349129008 },
            { x: 277.7589847707177, y: 336.10993829556463 },
            { x: 317.92811796310673, y: 279.02748586427504 },
            { x: 335.5461588369615, y: 261.4094449904202 },
            { x: 332.7272722971448, y: 259.2952800855576 },
        ];

        // This test is slow due to each individual point the user needs to draw, so
        // we increase the timeout to be depending on the amount of points to be drawn
        test.setTimeout(antelopePoints.length * 4000);

        const antelopeShape = {
            points: antelopePoints,
        };

        await polygonTool.selectTool();
        await polygonTool.drawPolygon(antelopeShape);

        const shapeLocator = getPolygonShape(page);

        // Checking the exact points tends to give flaky results as the points
        // might differ per browser, instead let's try to make sure that the area
        // that the user selects is roughly equal to the expected area
        expect(await getPolylineArea(shapeLocator)).toBeCloseTo(62029, -2);
    });

    test('Selects polygon tool using hotkey', async ({ page }) => {
        // Change to circle tool first
        await page.keyboard.press('c');

        await expect(page.getByRole('button', { name: 'Circle' })).toHaveAttribute('aria-pressed', 'true');

        await page.keyboard.press('p');

        await expect(page.getByRole('button', { name: 'Polygon' })).toHaveAttribute('aria-pressed', 'true');
    });

    test('Eraser mode cursor is visible only when there are polygon points', async ({ page }) => {
        const relative = await withRelative(page);
        const editor = page.locator('svg[role=editor]');

        await expect(editor).not.toHaveCSS('cursor', /eraser-tool/);

        const relativeStartPoint = relative(shape.points[0].x, shape.points[0].y);
        const relativeSecondPoint = relative(shape.points[1].x, shape.points[1].y);

        await page.mouse.move(relativeStartPoint.x, relativeStartPoint.y);
        await page.mouse.down();
        await page.mouse.up();
        await page.mouse.move(relativeSecondPoint.x, relativeSecondPoint.y);
        await page.mouse.down();
        await page.mouse.up();

        await page.mouse.down({ button: 'right' });
        await page.mouse.move(relativeSecondPoint.x + 10, relativeSecondPoint.y + 10);

        await expect(editor).toHaveCSS('cursor', /eraser-tool/);
    });

    // test_annotations_polygon_erase
    test('Polygon annotation can be erased with different methods: right mouse click + undo', async ({
        page,
        polygonTool,
    }) => {
        const shapeWithFourPoints = {
            points: [
                { x: 300 + 33, y: 33 },
                { x: 300 + 33, y: 330 },
                { x: 300 + 330, y: 330 },
                { x: 300 + 330, y: 33 },
            ],
        };

        await polygonTool.drawPolygon(shapeWithFourPoints, { finishShape: true, asLasso: false });

        const points = await page.locator('polygon').getAttribute('points');

        // Shape initially has 4 points
        expect(points?.split(' ')).toHaveLength(4);

        // Manually delete
        const relative = await withRelative(page);
        const relativeSecondPoint = relative(shape.points[1].x, shape.points[1].y);

        await page.mouse.click(relativeSecondPoint.x, relativeSecondPoint.y, { button: 'right' });

        await page.getByText('Delete').click();

        expect((await page.locator('polygon').getAttribute('points'))?.split(' ')).toHaveLength(3);

        // Undo
        await page.getByLabel('undo').click();

        expect((await page.locator('polygon').getAttribute('points'))?.split(' ')).toHaveLength(4);

        // Undo again to remove annotation
        await page.getByLabel('undo').click();

        expect(await getAnnotationsCount(page)).toBe(0);
    });

    test('Delete on and multiple points, by using hotkey or mouse', async ({ page, polygonTool }) => {
        await polygonTool.drawPolygon(shapeWithFivePoints);

        const points = await page.locator('polygon').getAttribute('points');

        // Shape initially has 5 points
        expect(points?.split(' ')).toHaveLength(5);

        const relative = await withRelative(page);
        const relativeThirdPoint = relative(shapeWithFivePoints.points[2].x, shapeWithFivePoints.points[2].y);
        const relativeFourthPoint = relative(shapeWithFivePoints.points[3].x, shapeWithFivePoints.points[3].y);

        await polygonTool.deletePointByRightClick(relativeThirdPoint);

        expect((await page.locator('polygon').getAttribute('points'))?.split(' ')).toHaveLength(4);

        // Undo
        await page.getByLabel('undo').click();

        expect((await page.locator('polygon').getAttribute('points'))?.split(' ')).toHaveLength(5);

        // Select multiple points
        await page.mouse.click(relativeThirdPoint.x, relativeThirdPoint.y);
        await page.keyboard.down('Shift');
        await page.mouse.click(relativeFourthPoint.x, relativeFourthPoint.y);
        await page.keyboard.up('Shift');

        // Delete them by using hotkey
        await page.keyboard.press('Delete');

        expect((await page.locator('polygon').getAttribute('points'))?.split(' ')).toHaveLength(3);
    });

    test('Translate polygon', async ({ page, polygonTool, selectionTool }) => {
        const origin = shape.points[0];
        const destination = { x: origin.x + 400, y: origin.y + 30 };

        await polygonTool.drawPolygon(shape);

        const relative = await withRelative(page);

        const startPoint = relative(origin.x + 10, origin.y + 50);
        const endPoint = relative(destination.x + 10, destination.y + 50);

        await selectionTool.selectTool();
        await page.mouse.click(startPoint.x, startPoint.y);

        await clickAndMove(page, startPoint, endPoint);

        const shapeLocator = getPolygonShape(page);

        // image is 940x629, translating the polygon to outside the image results in two new points
        // at the edge of the image
        await expectPolygonShape(shapeLocator, {
            ...shape,
            points: [
                { x: 940, y: 270 },
                { x: 940, y: 360 },
                { x: 733, y: 360 },
                { x: 733, y: 63 },
            ],
        });
    });

    test('Resize polygon', async ({ page, polygonTool }) => {
        const secondPoint = { x: shape.points[1].x, y: shape.points[1].y };
        const newPoint = { x: secondPoint.x + 30, y: secondPoint.y + 30 };

        await polygonTool.drawPolygon(shape);

        const relative = await withRelative(page);

        const startPoint = relative(secondPoint.x, secondPoint.y);
        const endPoint = relative(newPoint.x, newPoint.y);

        await clickAndMove(page, startPoint, endPoint);

        const shapeLocator = getPolygonShape(page);

        await expectPolygonShape(shapeLocator, {
            points: [shape.points[2], newPoint, shape.points[0]],
        });
    });

    test('Resize polygon outside of the image', async ({ page, polygonTool }) => {
        const topPoint = shape.points[0];
        const newPoint = { x: topPoint.x, y: topPoint.y - 100 };

        await polygonTool.drawPolygon(shape);

        const relative = await withRelative(page);

        const startPoint = relative(topPoint.x, topPoint.y);
        const endPoint = relative(newPoint.x, newPoint.y);

        await clickAndMove(page, startPoint, endPoint);

        const shapeLocator = getPolygonShape(page);

        await expectPolygonShape(shapeLocator, {
            points: [shape.points[2], shape.points[1], { x: newPoint.x, y: 0 }, { x: 383, y: 0 }],
        });
    });

    test('Adding a new point to a polygon outside of the image', async ({ page, polygonTool }) => {
        const topPoint = shape.points[0];
        const bottomRightPoint = shape.points[2];
        const middlePoint = {
            x: bottomRightPoint.x + (topPoint.x - bottomRightPoint.x) / 2,
            y: bottomRightPoint.y + (topPoint.y - bottomRightPoint.y) / 2,
        };
        const newPoint = { x: middlePoint.x, y: middlePoint.y - 300 };

        await polygonTool.drawPolygon(shape);

        const relative = await withRelative(page);

        const startPoint = relative(middlePoint.x, middlePoint.y);
        const endPoint = relative(newPoint.x, newPoint.y);

        await clickAndMove(page, startPoint, endPoint);

        const shapeLocator = getPolygonShape(page);

        await expectPolygonShape(shapeLocator, {
            points: [shape.points[2], shape.points[1], shape.points[0], { x: 365, y: 0 }, { x: 521, y: 0 }],
        });
    });

    test('Add label to polygon', async ({ page, polygonTool }) => {
        await polygonTool.drawPolygon(shape);

        await expect(page.getByLabel('edit-annotations').getByLabel('labels')).toHaveText('Select label');
    });

    test('Adds points by clicking on the segments', async ({ polygonTool, page }) => {
        await polygonTool.drawPolygon(shape);

        const relative = await withRelative(page);

        const randomMiddlePoint = relative(shape.points[0].x, shape.points[0].y + 30);
        const randomMiddlePointTwo = relative(shape.points[0].x, shape.points[0].y + 60);

        // Number of points should be 3
        expect(await getNumberOfPoints(page)).toBe(3);
        await expect(page.getByLabel(/Click to select point/)).toHaveCount(3);

        await page.mouse.click(randomMiddlePoint.x, randomMiddlePoint.y);

        // Number of points should be 4
        await expect(page.getByLabel(/Click to select point/)).toHaveCount(4);
        expect(await getNumberOfPoints(page)).toBe(4);

        await page.mouse.click(randomMiddlePointTwo.x, randomMiddlePointTwo.y);

        // Number of points should be 5
        expect(await getNumberOfPoints(page)).toBe(5);
        await expect(page.getByLabel(/Click to select point/)).toHaveCount(5);
    });

    test('Dragging a point can increase or decrease the area of the polygon', async ({ polygonTool, page }) => {
        await polygonTool.drawPolygon(shape);

        const relative = await withRelative(page);

        const randomMiddlePoint = relative(shape.points[0].x, shape.points[0].y + 30);

        const initialPolygon = page.locator('polygon');
        const initialPolygonArea = await getPolylineArea(initialPolygon);

        await clickAndMove(page, randomMiddlePoint, { x: randomMiddlePoint.x - 40, y: randomMiddlePoint.y });

        const biggerPolygon = page.locator('polygon');
        const biggerPolygonArea = await getPolylineArea(biggerPolygon);

        expect(biggerPolygonArea).toBeGreaterThan(initialPolygonArea);

        await clickAndMove(page, { x: randomMiddlePoint.x - 40, y: randomMiddlePoint.y }, randomMiddlePoint);

        const finalPolygon = page.locator('polygon');
        const finalPolygonArea = await getPolylineArea(finalPolygon);

        expect(finalPolygonArea).toBe(initialPolygonArea);
    });

    test('Translating the polygon out of bounds will crop the ROI', async ({ polygonTool, selectionTool, page }) => {
        const origin = shape.points[0];
        const destination = { x: origin.x + 400, y: origin.y + 30 };

        await polygonTool.drawPolygon(shape);

        const initialPolygon = page.locator('polygon');
        const initialPolygonArea = await getPolylineArea(initialPolygon);

        const relative = await withRelative(page);

        const startPoint = relative(origin.x + 10, origin.y + 50);
        const endPoint = relative(destination.x, destination.y);

        await selectionTool.selectTool();
        await page.mouse.click(startPoint.x, startPoint.y);

        // Move polygon slightly out of the canvas
        await clickAndMove(page, startPoint, endPoint);

        // Move back to the initial position
        await clickAndMove(page, endPoint, startPoint);

        const finalPolygon = page.locator('polygon');
        const finalPolygonArea = await getPolylineArea(finalPolygon);

        expect(finalPolygonArea).toBeLessThan(initialPolygonArea);
    });

    test('Undo point and shape removal - point deleted by right click', async ({ page, polygonTool }) => {
        await polygonTool.drawPolygon(shapeWithFivePoints);

        const relative = await withRelative(page);
        const relativeThirdPoint = relative(shapeWithFivePoints.points[2].x, shapeWithFivePoints.points[2].y);

        await polygonTool.deletePointByRightClick(relativeThirdPoint);
        expect((await page.locator('polygon').getAttribute('points'))?.split(' ')).toHaveLength(4);

        await page.getByLabel('undo').click();
        expect((await page.locator('polygon').getAttribute('points'))?.split(' ')).toHaveLength(5);

        await page.getByLabel('undo').click();
        expect(await page.getByRole('list', { name: 'Annotations list' }).getByRole('listitem').count()).toBe(0);
    });

    test('Right click couple of points - it should delete only last one', async ({ page, polygonTool }) => {
        await polygonTool.drawPolygon(shapeWithFivePoints);

        const relative = await withRelative(page);
        const relativeSecondPoint = relative(shapeWithFivePoints.points[1].x, shapeWithFivePoints.points[1].y);
        const relativeThirdPoint = relative(shapeWithFivePoints.points[2].x, shapeWithFivePoints.points[2].y);

        await polygonTool.openPointContextMenu(relativeSecondPoint);
        await polygonTool.deletePointByRightClick(relativeThirdPoint);
        expect((await page.locator('polygon').getAttribute('points'))?.split(' ')).toHaveLength(4);
    });

    test('Should use the correct cursor', async ({ page, polygonTool }) => {
        await polygonTool.selectTool();
        await page.mouse.move(500, 500);

        expect(await page.locator('[role=editor]').getAttribute('style')).toContain('polygon-drawing');

        await page.mouse.down();
        await page.mouse.move(510, 510);

        expect(await page.locator('[role=editor]').getAttribute('style')).toContain('lasso-drawing');
        await page.mouse.up();
    });

    test('Should display the correct tooltips', async ({ page, polygonTool }) => {
        await polygonTool.selectTool();

        const snappingModeButton = page.getByRole('switch', {
            name: 'Snapping mode',
        });

        await snappingModeButton.hover();
        expect(page.getByText('SHIFT+S')).toBeTruthy();
    });
});

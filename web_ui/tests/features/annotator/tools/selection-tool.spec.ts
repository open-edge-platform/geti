// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

import { AnnotationDTO, RectDTO } from '../../../../src/core/annotations/dtos/annotation.interface';
import { Point } from '../../../../src/core/annotations/shapes.interface';
import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { expect } from '../../../fixtures/base-test';
import {
    annotatorUrl,
    media,
    project,
    userAnnotationsDetectionSegmentationResponse,
} from '../../../mocks/detection-segmentation/mocks';
import { withRelative } from '../../../utils/mouse';

const expectAnnotationToBeSelected = async (page: Page, annotationId: string) => {
    await expect(page.getByRole('checkbox', { name: `Select annotation ${annotationId}` })).toBeChecked();
};

const expectAnnotationNotToBeSelected = async (page: Page, annotationId: string) => {
    await expect(page.getByRole('checkbox', { name: `Select annotation ${annotationId}` })).not.toBeChecked();
};

const expectAnnotationToBeSelectedLocally = async (page: Page, annotationId: string) => {
    await expect(page.getByLabel(`Selected shape ${annotationId}`, { exact: true })).toBeVisible();
};

const expectAnnotationNotToBeSelectedLocally = async (page: Page, annotationId: string) => {
    await expect(page.getByLabel(`Not selected shape ${annotationId}`)).toBeVisible();
};

const expectAnnotationEditPointsToBeVisible = async (page: Page, annotationId: string) => {
    const boundingBox = page.getByLabel(`Edit bounding box points ${annotationId}`);
    const resizeAnchors = boundingBox.getByLabel(/resize anchor/);

    await expect(resizeAnchors).toHaveCount(8);
};

const expectAnnotationEditPointsToBeHidden = async (page: Page, annotationId: string) => {
    const boundingBox = page.getByLabel(`Edit bounding box points ${annotationId}`);
    const resizeAnchors = boundingBox.getByLabel(/resize anchor/);

    await expect(resizeAnchors).toHaveCount(0);
};

test.describe('Selection', () => {
    const [
        firstDetectionAnnotation,
        secondDetectionAnnotation,
        firstSegmentationAnnotation,
        secondSegmentationAnnotation,
    ] = userAnnotationsDetectionSegmentationResponse.annotations as AnnotationDTO[];
    const firstDetectionShape = firstDetectionAnnotation.shape as RectDTO;
    const secondDetectionShape = secondDetectionAnnotation.shape as RectDTO;
    const firstSegmentationShape = firstSegmentationAnnotation.shape as RectDTO;
    const secondSegmentationShape = secondSegmentationAnnotation.shape as RectDTO;

    test.beforeEach(async ({ page, selectionTool, registerApiResponse }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
        registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
            res(ctx.json(userAnnotationsDetectionSegmentationResponse))
        );

        await page.goto(annotatorUrl);

        await selectionTool.selectTool();
    });

    test('Should select annotation by click', async ({ page, selectionTool }) => {
        await expectAnnotationNotToBeSelected(page, secondDetectionAnnotation.id);

        await selectionTool.selectUsingClick(secondDetectionAnnotation.shape);

        await expectAnnotationToBeSelected(page, secondDetectionAnnotation.id);
    });

    test('Edit points should be visible when annotation is selected by click', async ({ page, selectionTool }) => {
        await expectAnnotationNotToBeSelected(page, secondDetectionAnnotation.id);
        await expectAnnotationEditPointsToBeHidden(page, secondDetectionAnnotation.id);

        await selectionTool.selectUsingClick(secondDetectionAnnotation.shape);

        await expectAnnotationEditPointsToBeVisible(page, secondDetectionAnnotation.id);
    });

    test('Edit points should be visible when annotation is selected in the annotations list', async ({
        page,
        annotationListPage,
    }) => {
        await expectAnnotationNotToBeSelected(page, secondDetectionAnnotation.id);
        await expectAnnotationEditPointsToBeHidden(page, secondDetectionAnnotation.id);

        const annotationInTheList = await annotationListPage.getAnnotationListItem(
            page.getByRole('listitem', { name: new RegExp(`Annotation with id ${secondDetectionAnnotation.id}`) })
        );

        await annotationInTheList.select();

        await expectAnnotationEditPointsToBeVisible(page, secondDetectionAnnotation.id);
    });

    test('Should keep selection and select new annotation by click and shift key', async ({ page, selectionTool }) => {
        await expectAnnotationNotToBeSelected(page, firstDetectionAnnotation.id);
        await expectAnnotationNotToBeSelected(page, secondDetectionAnnotation.id);

        await selectionTool.selectUsingClick(firstDetectionAnnotation.shape);

        await expectAnnotationToBeSelected(page, firstDetectionAnnotation.id);
        await expectAnnotationNotToBeSelected(page, secondDetectionAnnotation.id);

        await selectionTool.selectUsingClickAndShiftKey(secondDetectionAnnotation.shape);

        await expectAnnotationToBeSelected(page, firstDetectionAnnotation.id);
        await expectAnnotationToBeSelected(page, secondDetectionAnnotation.id);
    });

    test('Should unselect annotation by click and shift key', async ({ page, selectionTool }) => {
        await selectionTool.selectUsingClick(firstDetectionAnnotation.shape);
        await selectionTool.selectUsingClickAndShiftKey(secondDetectionAnnotation.shape);

        await expectAnnotationToBeSelected(page, firstDetectionAnnotation.id);
        await expectAnnotationToBeSelected(page, secondDetectionAnnotation.id);

        await selectionTool.selectUsingClickAndShiftKey(secondDetectionAnnotation.shape);
        await expectAnnotationToBeSelected(page, firstDetectionAnnotation.id);
        await expectAnnotationNotToBeSelected(page, secondDetectionAnnotation.id);
    });

    test('Should unselect annotation when click event is outside the annotations', async ({ page, selectionTool }) => {
        await selectionTool.selectUsingClick(firstDetectionAnnotation.shape);

        await expectAnnotationToBeSelected(page, firstDetectionAnnotation.id);

        const outsideAnnotationX = firstDetectionShape.x + firstDetectionShape.width + 50;
        const relative = await withRelative(page);
        const { x, y } = relative(outsideAnnotationX, firstDetectionShape.y);

        await page.mouse.click(x, y);

        await expectAnnotationNotToBeSelected(page, firstDetectionAnnotation.id);
    });

    test('Should select multiple annotations using box selection', async ({ page, selectionTool }) => {
        await expectAnnotationNotToBeSelected(page, firstDetectionAnnotation.id);
        await expectAnnotationNotToBeSelected(page, secondDetectionAnnotation.id);

        const startPoint = {
            x: secondDetectionShape.x - 10,
            y: secondDetectionShape.y - 10,
        };

        const endPoint = {
            x: firstDetectionShape.x + 10,
            y: firstDetectionShape.y + 10,
        };

        await selectionTool.selectUsingBox(startPoint, endPoint);

        await expectAnnotationToBeSelected(page, firstDetectionAnnotation.id);
        await expectAnnotationToBeSelected(page, secondDetectionAnnotation.id);

        // Check that annotations are not editable
        await expectAnnotationEditPointsToBeHidden(page, firstDetectionAnnotation.id);
        await expectAnnotationEditPointsToBeHidden(page, secondDetectionAnnotation.id);
    });

    // eslint-disable-next-line max-len
    test('Should mark annotations as selected on pointer move event, annotation list is updated on pointer up event', async ({
        page,
    }) => {
        const relative = await withRelative(page);
        const startPoint = {
            x: secondDetectionShape.x - 10,
            y: secondDetectionShape.y - 10,
        };

        const endPoint = {
            x: firstDetectionShape.x + 10,
            y: firstDetectionShape.y + 10,
        };

        await expectAnnotationNotToBeSelectedLocally(page, firstDetectionAnnotation.id);
        await expectAnnotationNotToBeSelectedLocally(page, secondDetectionAnnotation.id);

        const relativeStartPoint = relative(startPoint.x, startPoint.y);
        const relativeEndPoint = relative(endPoint.x, endPoint.y);

        await page.mouse.move(relativeStartPoint.x, relativeStartPoint.y);
        await page.mouse.down();
        await page.mouse.move(relativeEndPoint.x, relativeEndPoint.y);

        await expectAnnotationToBeSelectedLocally(page, firstDetectionAnnotation.id);
        await expectAnnotationToBeSelectedLocally(page, secondDetectionAnnotation.id);

        await expectAnnotationNotToBeSelected(page, firstDetectionAnnotation.id);
        await expectAnnotationNotToBeSelected(page, secondDetectionAnnotation.id);

        await page.mouse.up();

        await expectAnnotationToBeSelected(page, firstDetectionAnnotation.id);
        await expectAnnotationToBeSelected(page, secondDetectionAnnotation.id);
    });

    test('Should unselect annotations using box selection outside the annotation', async ({ page, selectionTool }) => {
        const startPoint = {
            x: secondDetectionShape.x - 10,
            y: secondDetectionShape.y - 10,
        };

        const endPoint = {
            x: firstDetectionShape.x + 10,
            y: firstDetectionShape.y + 10,
        };

        await selectionTool.selectUsingBox(startPoint, endPoint);

        await expectAnnotationToBeSelected(page, firstDetectionAnnotation.id);
        await expectAnnotationToBeSelected(page, secondDetectionAnnotation.id);

        await selectionTool.selectUsingBox(
            { x: 10, y: 10 },
            { x: secondDetectionShape.x - 10, y: secondDetectionShape.y }
        );

        await expectAnnotationNotToBeSelected(page, firstDetectionAnnotation.id);
        await expectAnnotationNotToBeSelected(page, secondDetectionAnnotation.id);
    });

    test('Should keep selection and select new annotation using box selection and shift key', async ({
        page,
        selectionTool,
    }) => {
        const startPoint = {
            x: secondDetectionShape.x - 10,
            y: secondDetectionShape.y - 10,
        };

        const endPoint = {
            x: firstSegmentationShape.x + 10,
            y: firstSegmentationShape.y + 10,
        };

        await selectionTool.selectUsingBox(startPoint, endPoint);

        await expectAnnotationToBeSelected(page, firstSegmentationAnnotation.id);
        await expectAnnotationToBeSelected(page, secondDetectionAnnotation.id);

        await selectionTool.selectUsingBoxAndShiftKey(
            { x: firstDetectionShape.x + firstDetectionShape.width / 2, y: firstDetectionShape.y },
            {
                x: firstDetectionShape.x + firstDetectionShape.width,
                y: firstDetectionShape.y + firstDetectionShape.height / 2,
            }
        );

        await expectAnnotationToBeSelected(page, firstSegmentationAnnotation.id);
        await expectAnnotationToBeSelected(page, secondDetectionAnnotation.id);
        await expectAnnotationToBeSelected(page, firstDetectionAnnotation.id);
    });

    test('Should unselect annotation when using box selection and shift key', async ({ page, selectionTool }) => {
        const startPoint = {
            x: secondDetectionShape.x - 10,
            y: secondDetectionShape.y - 10,
        };

        const endPoint = {
            x: firstDetectionShape.x + 10,
            y: firstDetectionShape.y + 10,
        };

        await selectionTool.selectUsingBox(startPoint, endPoint);

        await expectAnnotationToBeSelected(page, firstDetectionAnnotation.id);
        await expectAnnotationToBeSelected(page, secondDetectionAnnotation.id);

        await selectionTool.selectUsingBoxAndShiftKey(
            { x: secondDetectionShape.x - 10, y: secondDetectionShape.y },
            {
                x: secondDetectionShape.x + secondDetectionShape.width / 2,
                y: secondDetectionShape.y + secondDetectionShape.height / 2,
            }
        );

        await expectAnnotationToBeSelected(page, firstDetectionAnnotation.id);
        await expectAnnotationNotToBeSelected(page, secondDetectionAnnotation.id);
    });

    // eslint-disable-next-line max-len
    test('Should select annotation locally again when using box selection, shift key and moving box inside annotation outside and inside again', async ({
        page,
        selectionTool,
    }) => {
        const relative = await withRelative(page);

        const startPoint = {
            x: secondDetectionShape.x - 10,
            y: secondDetectionShape.y - 10,
        };

        const endPoint = {
            x: firstDetectionShape.x + 10,
            y: firstDetectionShape.y + 10,
        };

        await selectionTool.selectUsingBox(startPoint, endPoint);

        await expectAnnotationToBeSelected(page, secondDetectionAnnotation.id);

        const startSelectUnselectPoint = { x: secondDetectionShape.x - 10, y: secondDetectionShape.y };

        const endSelectUnselectPoint = {
            x: secondDetectionShape.x + secondDetectionShape.width / 2,
            y: secondDetectionShape.y + secondDetectionShape.height / 2,
        };

        const relativeStartPoint = relative(startSelectUnselectPoint.x, startSelectUnselectPoint.y);
        const relativeEndPoint = relative(endSelectUnselectPoint.x, endSelectUnselectPoint.y);

        await page.keyboard.down('Shift');

        await page.mouse.move(relativeStartPoint.x, relativeStartPoint.y);
        await page.mouse.down();
        await page.mouse.move(relativeEndPoint.x, relativeEndPoint.y);

        await expectAnnotationNotToBeSelectedLocally(page, secondDetectionAnnotation.id);

        await page.mouse.move(relativeStartPoint.x, relativeStartPoint.y);
        await page.mouse.move(relativeEndPoint.x, relativeEndPoint.y);

        await expectAnnotationToBeSelectedLocally(page, secondDetectionAnnotation.id);

        await page.mouse.up();
        await page.keyboard.up('Shift');
    });

    test(
        'Selected annotations should stay selected in task context, i.e. changing annotations in the segmentation ' +
            'should not change annotations state in the detection',
        async ({ page, selectionTool, taskNavigation }) => {
            await selectionTool.selectUsingClick(firstDetectionShape);

            await expectAnnotationNotToBeSelected(page, secondSegmentationAnnotation.id);

            await taskNavigation.selectTaskMode('Segmentation');
            await selectionTool.selectTool();

            await selectionTool.selectUsingClick(secondSegmentationShape);

            await expectAnnotationToBeSelected(page, secondSegmentationAnnotation.id);

            await taskNavigation.selectTaskMode('All Tasks');

            await expectAnnotationToBeSelected(page, firstDetectionAnnotation.id);
            await expectAnnotationToBeSelected(page, secondSegmentationAnnotation.id);
        }
    );

    test('Should select annotation from the current task', async ({ page, selectionTool, taskNavigation }) => {
        await taskNavigation.selectTaskMode('Detection');
        await selectionTool.selectTool();

        const startPoint = {
            x: secondDetectionShape.x - 10,
            y: secondDetectionShape.y - 10,
        };

        const endPoint = {
            x: firstDetectionShape.x + firstDetectionShape.width + 10,
            y: firstDetectionShape.y + firstDetectionShape.height + 10,
        };

        await selectionTool.selectUsingBox(startPoint, endPoint);

        await expectAnnotationToBeSelected(page, firstDetectionAnnotation.id);
        await expectAnnotationToBeSelected(page, secondDetectionAnnotation.id);

        await taskNavigation.selectTaskMode('All Tasks');

        await expectAnnotationToBeSelected(page, firstDetectionAnnotation.id);
        await expectAnnotationToBeSelected(page, secondDetectionAnnotation.id);
        await expectAnnotationNotToBeSelected(page, firstSegmentationAnnotation.id);
        await expectAnnotationNotToBeSelected(page, secondSegmentationAnnotation.id);
    });

    test('Should use the correct cursor and tooltips', async ({ page, selectionTool }) => {
        await selectionTool.selectTool();

        await page.mouse.move(100, 100);

        const editByPointButton = page.getByLabel('Edit by point');
        await expect(editByPointButton).toBeVisible();
        await editByPointButton.hover();

        await expect(page.getByText('Edit by point')).toBeVisible();
        await expect(page.getByText('Edit by point')).toBeVisible();
    });

    test.describe('Not selecting global annotations', () => {
        const dragAndStop = async (page: Page, startPoint: Point, endPoint: Point) => {
            const relative = await withRelative(page);
            const relativeStartPoint = relative(startPoint.x, startPoint.y);
            const relativeEndPoint = relative(endPoint.x, endPoint.y);

            await page.mouse.move(relativeStartPoint.x, relativeStartPoint.y);
            await page.mouse.down();
            await page.mouse.move(relativeEndPoint.x, relativeEndPoint.y);
        };

        test('segmentation: Should not highlight a global annotation', async ({
            page,
            selectionTool,
            taskNavigation,
            labelShortcutsPage,
        }) => {
            const inputAnnotation = userAnnotationsDetectionSegmentationResponse.annotations[1];

            await taskNavigation.selectTaskMode('Segmentation');
            await (await labelShortcutsPage.getPinnedLabelLocator('Empty')).click();

            await selectionTool.selectTool();

            const startPoint = { x: inputAnnotation.shape.x + 10, y: inputAnnotation.shape.y + 10 };
            const endPoint = { x: inputAnnotation.shape.x + 50, y: inputAnnotation.shape.y + 50 };
            await dragAndStop(page, startPoint, endPoint);

            const editor = page.locator('[role="application"]');
            const selectedAnnotations = editor.getByLabel(/Selected shape/, { exact: true });

            await expect(selectedAnnotations).toHaveCount(0);
        });

        test('All tasks: Should not highlight a global annotation', async ({
            page,
            selectionTool,
            labelShortcutsPage,
        }) => {
            await (await labelShortcutsPage.getPinnedLabelLocator('No object')).click();
            await selectionTool.selectTool();

            const startPoint = { x: 100, y: 100 };
            const endPoint = { x: 200, y: 200 };
            await dragAndStop(page, startPoint, endPoint);

            const editor = page.locator('[role="editor"]');
            const selectedAnnotations = editor.getByLabel(/Selected shape/, { exact: true });

            await expect(selectedAnnotations).toHaveCount(0);
        });
    });
});

// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

import { AnnotationDTO, RectDTO } from '../../../../src/core/annotations/dtos/annotation.interface';
import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { expect } from '../../../fixtures/base-test';
import * as classification from '../../../mocks/classification/mocks';
import * as detectionClassification from '../../../mocks/detection-classification/mocks';
import * as nonClassification from '../../../mocks/detection-segmentation/mocks';
import { withRelative } from '../../../utils/mouse';
import { selectShape } from '../utils';

const [firstAnnotation, secondAnnotation] = nonClassification.userAnnotationsResponse.annotations as AnnotationDTO[];

const getCreateStamp = async (page: Page) => {
    return page.getByRole('button', { name: 'Create stamp' });
};

const getCancelStamp = async (page: Page) => {
    return page.getByRole('button', { name: 'Cancel stamp' });
};

const selectMultipleAnnotations = async (page: Page) => {
    await selectShape(page, firstAnnotation.shape);
    await page.keyboard.down('Shift');

    await selectShape(page, secondAnnotation.shape);
    await page.keyboard.up('Shift');
};

const expectStampToolIsActive = async (page: Page) => {
    await expect(page.getByLabel('Stamp tool')).toBeVisible();
};

const expectStampToolIsInactive = async (page: Page) => {
    await expect(page.getByLabel('Stamp tool')).toBeHidden();
};

const expectCreateStampIsVisible = async (page: Page) => {
    await expect(await getCreateStamp(page)).toBeVisible();
};

const expectCreateStampIsInvisible = async (page: Page) => {
    await expect(page.getByRole('button', { name: 'Create stamp' })).toBeHidden();
};

const expectCancelStampIsVisible = async (page: Page) => {
    await expect(await getCancelStamp(page)).toBeVisible();
};

const expectCancelStampIsInvisible = async (page: Page) => {
    await expect(page.getByRole('button', { name: 'Cancel stamp' })).toBeHidden();
};

const expectClassificationHasOneAnnotation = async (page: Page) => {
    await expect(page.getByLabel('annotations', { exact: true })).toHaveCount(1);
};

test.describe('Stamp tool', () => {
    test.describe('Stamp tool - non classification task', () => {
        test.beforeEach(async ({ registerApiResponse, page, stampTool }) => {
            const { annotatorUrl, media, userAnnotationsResponse, project } = nonClassification;

            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.json(userAnnotationsResponse)));

            await page.goto(annotatorUrl);

            await stampTool.selectSelectionTool();
        });

        // test_annotation_template
        test('Create and cancel stamp buttons are not visible when annotation is not selected', async ({ page }) => {
            await expect(page.getByLabel(`Not selected shape ${firstAnnotation.id}`)).toBeVisible();

            await expectCreateStampIsInvisible(page);
            await expectCancelStampIsInvisible(page);
        });

        // test_annotation_template
        test('Create stamp button is visible and enabled when only one annotation is selected', async ({ page }) => {
            await selectShape(page, firstAnnotation.shape);

            await expectCreateStampIsVisible(page);
            await expectCancelStampIsInvisible(page);
        });

        // test_annotation_template_multiple_annotation
        test('Create stamp button is visible and disabled when only more than one annotation is selected', async ({
            page,
        }) => {
            await selectMultipleAnnotations(page);

            await expectCreateStampIsVisible(page);
            await expect(await getCreateStamp(page)).toBeDisabled();
        });

        // test_annotation_template
        test('Stamp tool can be activated using shortcut when only one annotation selected', async ({
            page,

            stampTool,
        }) => {
            await selectShape(page, firstAnnotation.shape);
            await stampTool.selectStampToolUsingHotkey();

            await expectStampToolIsActive(page);
        });

        // test_annotation_template_multiple_annotation
        test('Stamp tool cannot be activated using shortcut when more than one annotation selected', async ({
            page,

            stampTool,
        }) => {
            await selectMultipleAnnotations(page);

            await stampTool.selectStampToolUsingHotkey();

            await expectStampToolIsInactive(page);
        });

        // test_annotation_template
        test('Stamp tool can be activated using context menu only when one annotation selected', async ({
            page,

            stampTool,
        }) => {
            const { x, y, width, height } = firstAnnotation.shape as RectDTO;
            const relative = await withRelative(page);
            const centerOfTheAnnotation = relative(x + width / 2, y + height / 2);

            await stampTool.selectStampToolUsingContextMenu(centerOfTheAnnotation.x, centerOfTheAnnotation.y);

            await expectStampToolIsActive(page);
        });

        // test_annotation_template
        test('Cancel stamp button is visible when stamp tool is active', async ({ page, stampTool }) => {
            await selectShape(page, firstAnnotation.shape);

            await stampTool.selectStampToolUsingButton();

            await expectCreateStampIsInvisible(page);
            await expectCancelStampIsVisible(page);
        });

        // test_annotation_template
        test('Stamp can be closed using cancel button', async ({ page, stampTool }) => {
            await selectShape(page, firstAnnotation.shape);

            await stampTool.selectStampToolUsingButton();

            await expectStampToolIsActive(page);

            await stampTool.cancelStampToolUsingButton();

            await expectStampToolIsInactive(page);
        });

        // test_annotation_template
        test('Stamp can be closed using ESC key', async ({ page, stampTool }) => {
            await selectShape(page, firstAnnotation.shape);

            await stampTool.selectStampToolUsingButton();

            await expectStampToolIsActive(page);

            await stampTool.cancelStampToolUsingHotkey();

            await expectStampToolIsInactive(page);
        });

        // test_annotation_template
        test('Stamp can be closed using tool context menu', async ({ page, stampTool }) => {
            const { x, y, width, height } = firstAnnotation.shape as RectDTO;
            const relative = await withRelative(page);
            const centerOfTheAnnotation = relative(x + width / 2, y + height / 2);

            await selectShape(page, firstAnnotation.shape);

            await stampTool.selectStampToolUsingButton();
            await expectStampToolIsActive(page);

            await stampTool.cancelStampToolUsingContextMenu(centerOfTheAnnotation.x, centerOfTheAnnotation.y);

            await expectStampToolIsInactive(page);
        });

        test('Stamp should be closed when other selection tool type is used', async ({ page, stampTool }) => {
            await selectShape(page, firstAnnotation.shape);

            await stampTool.selectStampToolUsingButton();

            await page.getByRole('button', { name: /Edit by point/ }).click();

            await expectStampToolIsInactive(page);
            await expectCreateStampIsInvisible(page);
        });

        test('Stamp should be closed when other tool type is used', async ({ page, stampTool, boundingBoxTool }) => {
            await selectShape(page, firstAnnotation.shape);

            await stampTool.selectStampToolUsingButton();

            await boundingBoxTool.selectTool();
            await expectStampToolIsInactive(page);
            await expectCreateStampIsInvisible(page);
        });

        // test_annotation_template
        test('Stamped annotation should be added to the media and annotations list', async ({
            page,

            annotationListPage,
            stampTool,
        }) => {
            const { x, y, width, height } = secondAnnotation.shape as RectDTO;
            const relative = await withRelative(page);
            const centerOfTheAnnotation = relative(x + width / 2, y + height / 2);

            const countBeforeStamping = await annotationListPage.getTotalAnnotations();

            const coordinatesToStamp = new Array(4).fill(0).map((_, idx) => ({
                x: centerOfTheAnnotation.x + 10 * idx,
                y: centerOfTheAnnotation.y + 10 * idx,
            }));

            await selectShape(page, secondAnnotation.shape);

            await stampTool.selectStampToolUsingButton();

            for (const coordinate of coordinatesToStamp) {
                await page.mouse.click(coordinate.x, coordinate.y);
            }

            await annotationListPage.expectTotalAnnotationsToBe(countBeforeStamping + coordinatesToStamp.length);
        });

        // test_annotation_template_multiple_images
        test('Stamp tool should persist while switching between media items', async ({
            page,
            stampTool,
            annotationListPage,
        }) => {
            await selectShape(page, secondAnnotation.shape);

            await stampTool.selectStampToolUsingButton();

            await expectStampToolIsActive(page);

            await page.getByRole('button', { name: 'Submit annotations' }).click();

            await expect(page.getByTestId('main-content-loader-id')).toBeHidden();

            await expectStampToolIsActive(page);

            const relative = await withRelative(page);
            const { x, y } = relative(0, 0);

            const countBeforeStamping = await annotationListPage.getTotalAnnotations();

            await page.mouse.click(x + 100, y + 100);

            await annotationListPage.expectTotalAnnotationsToBe(countBeforeStamping + 1);
        });

        test('Stamped annotation should be in the selected state', async ({ page, stampTool }) => {
            await selectShape(page, firstAnnotation.shape);

            await stampTool.selectStampToolUsingButton();

            const relative = await withRelative(page);

            const newPoint = relative(0, 0);

            await page.mouse.click(newPoint.x + 100, newPoint.y + 100);

            await stampTool.selectSelectionTool();
            await expect(page.getByLabel(/^Selected shape \w+/)).toHaveCount(1);
            await expect(page.getByLabel(`Not selected shape ${firstAnnotation.id}`)).toHaveCount(1);
        });

        test('Annotation should not be editable when stamp tool is active', async ({
            annotationListPage,
            stampTool,
            page,
        }) => {
            await selectShape(page, firstAnnotation.shape);

            await stampTool.selectStampToolUsingButton();

            const annotation = await annotationListPage.getAnnotationListItem(
                page.getByRole('listitem', { name: new RegExp(`Annotation with id ${firstAnnotation.id}`) })
            );

            await annotation.select();

            await expect(page.getByLabel('edit-annotations')).toBeHidden();
        });

        test('Should display the correct tooltips', async ({ page }) => {
            await selectShape(page, firstAnnotation.shape);

            const stampToolButton = page.getByRole('button', { name: 'Create stamp' });
            await expect(stampToolButton).toBeVisible();
            await stampToolButton.hover();

            await expect(page.getByText('Create stamp: S')).toBeVisible();
        });
    });

    test.describe('Stamp tool - classification task', () => {
        test.beforeEach(async ({ registerApiResponse, page, stampTool }) => {
            const { annotatorUrl, media, userAnnotationsResponse, project } = classification;

            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.json(userAnnotationsResponse)));

            await page.goto(annotatorUrl);

            await stampTool.selectSelectionTool();
        });

        test('Create and cancel stamp buttons are not visible', async ({ page }) => {
            await expectClassificationHasOneAnnotation(page);

            await expectCreateStampIsInvisible(page);
            await expectCancelStampIsInvisible(page);

            await expectStampToolIsInactive(page);
        });

        test('Shortcut does not active the stamp tool', async ({ stampTool, page }) => {
            await expectClassificationHasOneAnnotation(page);

            await stampTool.selectStampToolUsingHotkey();

            await expectStampToolIsInactive(page);
        });
    });

    test.describe('Stamp tool - detection -> classification', () => {
        test.beforeEach(async ({ registerApiResponse, page, stampTool }) => {
            const { annotatorUrl, media, userDetectionAnnotationsResponse, project } = detectionClassification;

            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.json(userDetectionAnnotationsResponse)));

            await page.goto(annotatorUrl);

            await stampTool.selectSelectionTool();
        });

        test('Pasted stamped annotation should have the same labels like stamped annotation', async ({
            page,

            stampTool,
            annotatorPage,
        }) => {
            const annotation = detectionClassification.userDetectionAnnotationsResponse.annotations[0] as AnnotationDTO;
            const shape = annotation.shape as RectDTO;

            await selectShape(page, shape);

            await page.getByRole('button', { name: /Clubs/ }).click();

            await stampTool.selectStampToolUsingButton();

            await annotatorPage.deleteAllAnnotations();

            const relative = await withRelative(page);

            const newPoint = relative(50, 50);

            await page.mouse.click(newPoint.x + shape.width, newPoint.y + shape.height);

            const labels = page.getByLabel(/Labels of annotation with id/);

            await expect(labels.getByText('Clubs')).toHaveCount(1);
            await expect(labels.getByText('Card')).toHaveCount(1);
        });
    });
});

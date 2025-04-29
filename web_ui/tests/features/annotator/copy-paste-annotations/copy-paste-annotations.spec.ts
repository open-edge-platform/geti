// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

import { AnnotationDTO, RectDTO, ShapeDTO } from '../../../../src/core/annotations/dtos/annotation.interface';
import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { expect } from '../../../fixtures/base-test';
import * as singleClassification from '../../../mocks/classification/mocks';
import * as taskChainDetectionClassification from '../../../mocks/detection-classification/mocks';
import * as nonClassification from '../../../mocks/detection-segmentation/mocks';
import { expectRectShape } from '../expect';
import { selectShape } from '../utils';

const getAnnotationsList = (page: Page) => {
    const annotationsList = page.getByLabel('Annotations list').getByRole('listitem', { name: /Annotation with id/ });

    return annotationsList;
};

const copyAnnotations = async (page: Page) => {
    await page.keyboard.press(`Control+C`);
};

const pasteAnnotations = async (page: Page) => {
    await page.keyboard.press(`Control+V`);
};

const getPastedAnnotation = async (page: Page) => {
    const pastedAnnotationInTheList = page
        .getByLabel('Annotations list')
        .getByRole('listitem', { name: /Annotation with id/ })
        .first();

    const pastedAnnotationId = (await pastedAnnotationInTheList.getAttribute('aria-label'))?.split('id')[1].trim();

    return page.getByLabel(`Selected shape ${pastedAnnotationId}`);
};

test.describe('Copy paste annotations', () => {
    test.describe('Non classification task', () => {
        const { annotatorUrl, media, project, userAnnotationsDetectionSegmentationResponse } = nonClassification;

        const [
            firstDetectionAnnotation,
            secondDetectionAnnotation,
            firstSegmentationAnnotation,
            secondSegmentationAnnotation,
        ] = userAnnotationsDetectionSegmentationResponse.annotations as AnnotationDTO[];
        const secondShape = secondDetectionAnnotation.shape as RectDTO;

        test.beforeEach(async ({ registerApiResponse, page, selectionTool, taskNavigation }) => {
            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
            registerApiResponse('GetImageAnnotation', (_, res, ctx) =>
                res(ctx.json(userAnnotationsDetectionSegmentationResponse))
            );

            await page.goto(annotatorUrl);

            await taskNavigation.selectTaskMode('Detection');
            await selectionTool.selectTool();
        });

        test('Should not copy an annotation when annotation is not selected', async ({ page }) => {
            const annotationsCount = await getAnnotationsList(page).count();

            await expect(
                page.getByLabel('Annotations list').getByRole('checkbox', { name: /Select annotation/, checked: true })
            ).toHaveCount(0);

            await copyAnnotations(page);
            await pasteAnnotations(page);

            await expect(getAnnotationsList(page)).toHaveCount(annotationsCount);
        });

        test('Should copy an annotation when annotation is selected', async ({ page }) => {
            const annotationsCount = await getAnnotationsList(page).count();

            // Detection's annotations
            expect(annotationsCount).toBe(2);

            await selectShape(page, secondShape);

            await copyAnnotations(page);
            await pasteAnnotations(page);

            await expect(getAnnotationsList(page)).toHaveCount(annotationsCount + 1);
        });

        test('Should copy multiple annotations', async ({ page }) => {
            const annotationsCount = await getAnnotationsList(page).count();

            await selectShape(page, firstDetectionAnnotation.shape);
            await page.keyboard.down('Shift');
            await selectShape(page, secondDetectionAnnotation.shape);
            await page.keyboard.up('Shift');

            await copyAnnotations(page);
            await pasteAnnotations(page);

            await expect(getAnnotationsList(page)).toHaveCount(annotationsCount + 2);
        });

        test('Pasted annotations should be in the selected state', async ({ page }) => {
            await selectShape(page, firstDetectionAnnotation.shape);
            await page.keyboard.down('Shift');
            await selectShape(page, secondDetectionAnnotation.shape);
            await page.keyboard.up('Shift');

            await copyAnnotations(page);

            // Annotations list is virtualized, we want to avoid need for expanding that list to get all annotations
            await page.getByRole('button', { name: 'Delete selected annotations' }).click();

            await pasteAnnotations(page);

            await expect(getAnnotationsList(page)).toHaveCount(2);

            await expect(
                page.getByLabel('Annotations list').getByRole('checkbox', { name: /Select annotation/, checked: true })
            ).toHaveCount(2);
        });

        test(
            'Should copy and paste annotations relatively to the original annotations when pasted to the same' +
                'media item',
            async ({ page }) => {
                await selectShape(page, secondDetectionAnnotation.shape);
                const zoom = Number(await page.getByLabel('Zoom level').getAttribute('data-value'));
                const OFFSET = 10 / zoom;

                await copyAnnotations(page);
                await pasteAnnotations(page);

                const pastedAnnotation = await getPastedAnnotation(page);

                const { x, y, height, width } = secondShape;
                await expectRectShape(pastedAnnotation, { x: x + OFFSET, y: y + OFFSET, width, height });
            }
        );

        test(
            'Should copy and paste annotations relatively to the original annotations when pasted to another media' +
                'item',
            async ({ page }) => {
                await selectShape(page, secondDetectionAnnotation.shape);

                await copyAnnotations(page);

                await page.getByRole('button', { name: /Submit/ }).click();

                await expect(page.getByTestId('main-content-loader-id')).toBeHidden();

                await pasteAnnotations(page);

                const pastedAnnotation = await getPastedAnnotation(page);

                const { x, y, height, width } = secondShape;
                await expectRectShape(pastedAnnotation, { x, y, width, height });
            }
        );

        test(
            'Annotations copied from the detection should not be pasted in the segmentation, notification warning' +
                ' should be displayed',
            async ({ page, taskNavigation }) => {
                await selectShape(page, secondDetectionAnnotation.shape);

                await copyAnnotations(page);

                await taskNavigation.selectTaskMode('Segmentation');

                await expect(getAnnotationsList(page)).toHaveCount(0);

                await pasteAnnotations(page);

                await expect(getAnnotationsList(page)).toHaveCount(0);

                await expect(page.getByText('You can only paste annotations in the same task context.')).toBeVisible();
            }
        );

        test('Annotation should be pasted when partially fits to the ROI', async ({
            page,
            selectionTool,
            taskNavigation,
        }) => {
            await taskNavigation.selectTaskMode('All Tasks');

            await selectionTool.selectTool();
            await selectShape(page, firstSegmentationAnnotation.shape);

            await copyAnnotations(page);

            await selectShape(page, secondShape);

            await taskNavigation.selectTaskMode('Segmentation');

            const annotationsCount = await getAnnotationsList(page).count();

            await pasteAnnotations(page);

            await expect(getAnnotationsList(page)).toHaveCount(annotationsCount + 1);
        });

        test('Annotation should not be pasted when does not fit to the ROI', async ({
            page,
            selectionTool,
            taskNavigation,
        }) => {
            await taskNavigation.selectTaskMode('All Tasks');

            await selectionTool.selectTool();
            await selectShape(page, secondSegmentationAnnotation.shape);

            await copyAnnotations(page);

            await selectShape(page, secondShape);

            await taskNavigation.selectTaskMode('Segmentation');

            const annotationsCount = await getAnnotationsList(page).count();

            await pasteAnnotations(page);

            await expect(
                page.getByText("One ore more annotations were outside the region of the interest haven't been pasted.")
            ).toBeVisible();
            await expect(getAnnotationsList(page)).toHaveCount(annotationsCount);
        });
    });

    test.describe('Classification task', () => {
        test('Copy paste feature should not work in the classification task', async ({ page, registerApiResponse }) => {
            const { annotatorUrl, media, userAnnotationsResponse, project } = singleClassification;

            const classificationTask = project.pipeline.tasks[1];
            const label = classificationTask.labels?.find(
                ({ id }) => id === userAnnotationsResponse.annotations[0].labels[0].id
            );

            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.json(userAnnotationsResponse)));

            await page.goto(annotatorUrl);

            await expect(page.getByLabel('annotations').getByLabel(`annotation-${label?.name}`)).toHaveCount(1);

            await copyAnnotations(page);
            await pasteAnnotations(page);

            await expect(page.getByLabel('annotations').getByLabel(`annotation-${label?.name}`)).toHaveCount(1);
        });

        test('Annotations copied from the detection should not be applied to the classification', async ({
            page,
            selectionTool,
            taskNavigation,
            registerApiResponse,
        }) => {
            const { annotatorUrl, media, userDetectionAnnotationsResponse, project } = taskChainDetectionClassification;

            registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
            registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
            registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.json(userDetectionAnnotationsResponse)));

            await page.goto(annotatorUrl);

            const copiedAnnotation = userDetectionAnnotationsResponse.annotations[0];

            await selectionTool.selectTool();
            await selectShape(page, copiedAnnotation.shape as ShapeDTO);

            await copyAnnotations(page);

            await taskNavigation.selectTaskMode('Classification');

            await pasteAnnotations(page);

            await expect(
                page.getByLabel('annotations').getByLabel(`annotation-${copiedAnnotation.labels[0].name}`)
            ).toBeHidden();
        });
    });
});

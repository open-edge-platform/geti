// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

import { Point, Rect } from '../../../../src/core/annotations/shapes.interface';
import { AnnotationContextMenuItemsKeys } from '../../../../src/pages/annotator/providers/annotator-context-menu-provider/utils';
import { annotatorTest as test } from '../../../fixtures/annotator-test';
import { expect } from '../../../fixtures/base-test';
import { annotatorUrl, media, project, userAnnotationsResponse } from '../../../mocks/detection-segmentation/mocks';
import { withRelative } from '../../../utils/mouse';
import { expectRectShape } from '../expect';

const expectContextMenuToBeInvisible = async (page: Page) => {
    await expect(page.getByLabel('Annotation context menu')).toBeHidden();
};

const expectContextMenuToBeVisible = async (page: Page) => {
    await expect(page.getByLabel('Annotation context menu')).toBeVisible();
};

const openContextMenu = async (page: Page, { x, y }: Point) => {
    const relative = await withRelative(page);
    const relativePoint = relative(x, y);

    await page.mouse.click(relativePoint.x, relativePoint.y, { button: 'right' });
};

const openContextMenuAtTheCenterOfTheAnnotation = async (
    page: Page,
    { x, y, width, height }: Omit<Rect, 'shapeType'>
) => {
    const point = {
        x: x + width / 2,
        y: y + height / 2,
    };

    await openContextMenu(page, point);
};

const selectAction = async (page: Page, name: AnnotationContextMenuItemsKeys) => {
    await page.getByRole('menuitem', { name }).click();
};

const expectAnnotationToBeVisible = async (page: Page, id: string) => {
    await expect(page.getByLabel(`Selected shape ${id}`)).toBeVisible();
};

const expectAnnotationToBeInvisible = async (page: Page, id: string) => {
    await expect(page.getByLabel(`Selected shape ${id}`)).toBeHidden();
    await expect(page.getByLabel(`Not selected shape ${id}`)).toBeHidden();
};

test.describe('Annotations context menu', () => {
    const [firstAnnotation, secondAnnotation] = userAnnotationsResponse.annotations;

    test.beforeEach(async ({ page, registerApiResponse, selectionTool }) => {
        registerApiResponse('GetProjectInfo', (_, res, ctx) => res(ctx.json(project)));
        registerApiResponse('GetImageDetail', (_, res, ctx) => res(ctx.json(media)));
        registerApiResponse('GetImageAnnotation', (_, res, ctx) => res(ctx.json(userAnnotationsResponse)));

        await page.goto(annotatorUrl);

        await selectionTool.selectTool();
    });

    // eslint-disable-next-line max-len
    test('Context menu should appear when SELECTION TOOL is selected and the right click happens on the annotation', async ({
        page,
        boundingBoxTool,
        selectionTool,
    }) => {
        await boundingBoxTool.selectTool();

        await openContextMenuAtTheCenterOfTheAnnotation(page, firstAnnotation.shape);

        await expectContextMenuToBeInvisible(page);

        await selectionTool.selectTool();

        await openContextMenuAtTheCenterOfTheAnnotation(page, firstAnnotation.shape);

        await expectContextMenuToBeVisible(page);
    });

    test('Context menu should close right-click is outside the annotation', async ({ page }) => {
        const { x, y } = firstAnnotation.shape;

        await openContextMenuAtTheCenterOfTheAnnotation(page, firstAnnotation.shape);

        await expectContextMenuToBeVisible(page);

        await openContextMenu(page, { x: x - 10, y: y - 10 });
        await expectContextMenuToBeInvisible(page);
    });

    test('Context menu should close when left-click is outside the context', async ({ page }) => {
        await openContextMenuAtTheCenterOfTheAnnotation(page, firstAnnotation.shape);

        await expectContextMenuToBeVisible(page);

        const pointOutsideContext = {
            x: firstAnnotation.shape.x - 10,
            y: firstAnnotation.shape.y - 10,
        };

        const relative = await withRelative(page);
        const { x, y } = relative(pointOutsideContext.x, pointOutsideContext.y);

        await page.mouse.click(x, y);

        await expectContextMenuToBeInvisible(page);
    });

    test('Annotation which has context menu should be selected', async ({ page }) => {
        await openContextMenuAtTheCenterOfTheAnnotation(page, firstAnnotation.shape);

        const selectedAnnotation = page.getByLabel(`Selected shape ${firstAnnotation.id}`);

        await expectRectShape(selectedAnnotation, firstAnnotation.shape);
    });

    test('Only one context menu should be visible at a time, even when opened on the another annotation', async ({
        page,
    }) => {
        await openContextMenuAtTheCenterOfTheAnnotation(page, firstAnnotation.shape);

        await openContextMenuAtTheCenterOfTheAnnotation(page, secondAnnotation.shape);

        const contextMenu = page.getByLabel('Annotation context menu');
        await expect(contextMenu).toBeVisible();

        expect(await contextMenu.all()).toHaveLength(1);
    });

    test.describe('Context menu actions', () => {
        test('Should remove annotation and close menu', async ({ page }) => {
            await openContextMenuAtTheCenterOfTheAnnotation(page, firstAnnotation.shape);

            await expectAnnotationToBeVisible(page, firstAnnotation.id);

            await selectAction(page, AnnotationContextMenuItemsKeys.REMOVE);

            await expectAnnotationToBeInvisible(page, firstAnnotation.id);
            await expectContextMenuToBeInvisible(page);
        });

        test('Should lock and lock annotation, after each action should close menu', async ({ page }) => {
            await openContextMenuAtTheCenterOfTheAnnotation(page, firstAnnotation.shape);

            await expect(page.locator(`[id="annotation-${firstAnnotation.id}-toggle-lock"]`)).toBeHidden();

            await selectAction(page, AnnotationContextMenuItemsKeys.LOCK);

            await expect(page.locator(`[id="annotation-${firstAnnotation.id}-toggle-lock"]`)).toBeVisible();

            await expectContextMenuToBeInvisible(page);

            await openContextMenuAtTheCenterOfTheAnnotation(page, firstAnnotation.shape);

            await selectAction(page, AnnotationContextMenuItemsKeys.UNLOCK);

            await expect(page.locator(`[id="annotation-${firstAnnotation.id}-toggle-lock"]`)).toBeHidden();

            await expectContextMenuToBeInvisible(page);
        });

        test('Should hide annotation', async ({ page }) => {
            await openContextMenuAtTheCenterOfTheAnnotation(page, firstAnnotation.shape);

            await expect(page.locator(`[id="annotation-list-item-${firstAnnotation.id}-visibility-off"]`)).toBeHidden();

            await selectAction(page, AnnotationContextMenuItemsKeys.HIDE);

            await expect(
                page.locator(`[id="annotation-list-item-${firstAnnotation.id}-visibility-off"]`)
            ).toBeVisible();
        });

        test('Should open label search', async ({ page }) => {
            await openContextMenuAtTheCenterOfTheAnnotation(page, firstAnnotation.shape);

            await selectAction(page, AnnotationContextMenuItemsKeys.EDIT_LABELS);

            await expect(page.getByLabel('annotation-deer')).toBeHidden();

            await expect(page.getByRole('textbox', { name: 'Select label' })).toBeVisible();

            await page.getByRole('listitem', { name: 'label item deer' }).click();

            await expect(page.getByLabel('annotation-deer')).toBeVisible();
        });
    });
});

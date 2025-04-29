// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import range from 'lodash/range';

import { OpenApiResponseBody } from '../../../src/core/server/types';
import { expect } from '../../fixtures/base-test';
import { annotatorTest as test } from './../../fixtures/annotator-test';
import { annotatorUrl } from './../../mocks/detection-classification/mocks';
import { dragAndDrop } from './utils';

test.describe('Annotation list', () => {
    test.beforeEach(async ({ registerApiExample, registerApiResponse, openApi, page }) => {
        registerApiExample('GetProjectInfo', 'Detection classification response');

        registerApiResponse('GetImageAnnotation', (_req, res, ctx) => {
            const { mock } = openApi.mockResponseForOperation('GetImageAnnotation') as {
                mock: OpenApiResponseBody<'GetImageAnnotation'>;
            };

            const labels = mock.annotations
                ?.at(0)
                ?.labels?.map((label) => ({ ...label, id: '62946c62003ddb3967f1475b' }));

            const annotations = [
                {
                    id: 'annotation-1',
                    labels,
                    labels_to_revisit: [],
                    modified: '2021-09-08T12:43:22.265000+00:00',
                    shape: { height: 20, type: 'RECTANGLE', width: 20, x: 100, y: 100 },
                },
                {
                    id: 'annotation-2',
                    labels,
                    labels_to_revisit: [],
                    modified: '2021-09-08T12:43:22.265000+00:00',
                    shape: { height: 20, type: 'RECTANGLE', width: 20, x: 200, y: 100 },
                },
                {
                    id: 'annotation-3',
                    labels,
                    labels_to_revisit: [],
                    modified: '2021-09-08T12:43:22.265000+00:00',
                    shape: { height: 20, type: 'RECTANGLE', width: 20, x: 300, y: 100 },
                },
                {
                    id: 'annotation-4',
                    labels,
                    labels_to_revisit: [],
                    modified: '2021-09-08T12:43:22.265000+00:00',
                    shape: { height: 20, type: 'RECTANGLE', width: 20, x: 400, y: 100 },
                },
            ];

            return res(ctx.json({ ...mock, annotations }));
        });

        await page.goto(annotatorUrl);

        await expect(
            page.getByRole('checkbox', {
                name: new RegExp(`0 out of ${TOTAL_ANNOTATIONS} annotations selected`),
            })
        ).toBeVisible();
    });

    const TOTAL_ANNOTATIONS = 4;
    test('Select annotations', async ({ page, annotationListPage }) => {
        for (let idx = 0; idx < TOTAL_ANNOTATIONS; idx++) {
            const listItem = await annotationListPage.getAnnotationListItem(
                page.getByRole('listitem', { name: new RegExp(`annotation-${idx + 1}`) })
            );
            await listItem.select();
        }

        expect(await annotationListPage.getTotalSelectedAnnotations()).toEqual(TOTAL_ANNOTATIONS);
        await annotationListPage.deselectAll();
        expect(await annotationListPage.getTotalSelectedAnnotations()).toEqual(0);
    });

    test('Drag & drop annotation', async ({ page, annotationListPage }) => {
        const [firstAnnotation, secondAnnotation] = await annotationListPage.getVisibleAnnotations();

        await expect(firstAnnotation).toHaveAttribute('aria-label', /annotation-4/);
        await expect(secondAnnotation).toHaveAttribute('aria-label', /annotation-3/);

        await dragAndDrop(
            page,
            '[aria-label="Annotation with id annotation-4"]',
            '[aria-label="Annotation with id annotation-3"]'
        );

        const [secondAnnotationAfterDrag, firstAnnotationAfterDrag] = await annotationListPage.getVisibleAnnotations();
        await expect(secondAnnotationAfterDrag).toHaveAttribute('aria-label', /annotation-3/);
        await expect(firstAnnotationAfterDrag).toHaveAttribute('aria-label', /annotation-4/);
    });

    test.describe('Annotation list bulk actions', () => {
        test.beforeEach(async ({ page, annotationListPage }) => {
            const listItem1 = await annotationListPage.getAnnotationListItem(
                page.getByRole('listitem', { name: /annotation-1/ })
            );
            const listItem3 = await annotationListPage.getAnnotationListItem(
                page.getByRole('listitem', { name: /annotation-3/ })
            );

            await listItem1.select();
            await listItem3.select();
        });
        test('Hide selected annotations', async ({ page, annotationListPage }) => {
            const listItem1 = await annotationListPage.getAnnotationListItem(
                page.getByRole('listitem', { name: /annotation-1/ })
            );
            const listItem3 = await annotationListPage.getAnnotationListItem(
                page.getByRole('listitem', { name: /annotation-3/ })
            );

            await annotationListPage.hideSelected();

            expect(await listItem1.annotationIsVisible()).toEqual(true);
            expect(await listItem3.annotationIsVisible()).toEqual(true);
        });

        test('Lock selected annotations', async ({ page, annotationListPage }) => {
            const listItem1 = await annotationListPage.getAnnotationListItem(
                page.getByRole('listitem', { name: /annotation-1/ })
            );
            const listItem3 = await annotationListPage.getAnnotationListItem(
                page.getByRole('listitem', { name: /annotation-3/ })
            );

            await annotationListPage.lockSelected();

            expect(await listItem1.isLocked()).toEqual(true);
            expect(await listItem3.isLocked()).toEqual(true);
        });

        test('Change labels of selected', async ({ page, annotationListPage }) => {
            const listItem1 = await annotationListPage.getAnnotationListItem(
                page.getByRole('listitem', { name: /annotation-1/ })
            );
            const listItem3 = await annotationListPage.getAnnotationListItem(
                page.getByRole('listitem', { name: /annotation-3/ })
            );

            await annotationListPage.assignLabelsOfSelected();
            await page.getByRole('listitem', { name: /card/i }).click();

            expect(await listItem1.labels()).toEqual([]);
            expect(await listItem3.labels()).toEqual([]);
        });

        test('Remove selected annotations', async ({ annotationListPage }) => {
            await annotationListPage.removeSelected();
            await annotationListPage.expectTotalAnnotationsToBe(TOTAL_ANNOTATIONS - 2);
        });
    });

    test.describe('List item', () => {
        test('Change labels', async ({ page, annotationListPage }) => {
            const firstAnnotation = page.getByRole('listitem', { name: /annotation-1/ });
            const listItemPage = await annotationListPage.getAnnotationListItem(firstAnnotation);

            expect(await listItemPage.labels()).toEqual(['Card']);

            await listItemPage.showActions((menu) => menu.getByRole('menuitem', { name: 'edit label' }).click());

            await expect(page.getByLabel('Label search results')).toBeVisible();
            await page.getByRole('listitem', { name: /hearts/i }).click();

            expect(await listItemPage.labels()).toEqual(['Card', 'Hearts']);
        });

        test('Toggle annotation lock', async ({ page, annotationListPage }) => {
            const firstAnnotation = page.getByRole('listitem', { name: /annotation-1/ });
            const listItemPage = await annotationListPage.getAnnotationListItem(firstAnnotation);

            // Lock
            await listItemPage.showActions((menu) => menu.getByRole('menuitem', { name: 'lock' }).click());
            expect(await listItemPage.isLocked()).toEqual(true);

            await listItemPage.showActions(async (menu) => {
                await expect(menu.getByRole('menuitem', { name: /remove/i })).toBeDisabled();
                await menu.getByRole('menuitem', { name: 'unlock' }).click();
            });
            expect(await listItemPage.isLocked()).toEqual(false);

            await listItemPage.showActions((menu) => menu.getByRole('menuitem', { name: 'lock' }).click());
            await listItemPage.unlock();
            expect(await listItemPage.isLocked()).toEqual(false);
        });

        test('Toggle annotation visibility', async ({ page, annotationListPage }) => {
            const firstAnnotation = page.getByRole('listitem', { name: /annotation-1/ });
            const listItemPage = await annotationListPage.getAnnotationListItem(firstAnnotation);

            // Lock
            await listItemPage.showActions((menu) => menu.getByRole('menuitem', { name: 'hide' }).click());
            expect(await listItemPage.annotationIsVisible()).toEqual(true);

            await listItemPage.showActions(async (menu) => {
                await menu.getByRole('menuitem', { name: 'show' }).click();
            });
            expect(await listItemPage.annotationIsVisible()).toEqual(false);

            await listItemPage.showActions((menu) => menu.getByRole('menuitem', { name: 'hide' }).click());
            await listItemPage.show();
            expect(await listItemPage.annotationIsVisible()).toEqual(false);
        });

        test('Remove annotation', async ({ page, annotationListPage }) => {
            const firstAnnotation = page.getByRole('listitem', { name: /annotation-1/ });
            const listItemPage = await annotationListPage.getAnnotationListItem(firstAnnotation);

            // Remove
            await listItemPage.showActions((menu) => menu.getByRole('menuitem', { name: 'remove' }).click());
            await expect(firstAnnotation).toBeHidden();

            await expect(
                page.getByRole('checkbox', {
                    name: new RegExp(`0 out of ${TOTAL_ANNOTATIONS - 1} annotations selected`),
                })
            ).toBeVisible();
        });

        test('Selecting with keyboard shortcuts', async ({ page }) => {
            await page.keyboard.press('Control+a');
            await expect(
                page.getByRole('checkbox', {
                    name: new RegExp(`${TOTAL_ANNOTATIONS} out of ${TOTAL_ANNOTATIONS} annotations selected`),
                })
            ).toBeVisible();

            await page.keyboard.press('Control+d');
            await expect(
                page.getByRole('checkbox', {
                    name: new RegExp(`0 out of ${TOTAL_ANNOTATIONS} annotations selected`),
                })
            ).toBeVisible();
        });
    });
});

test('Many annotations (all should be visible)', async ({ page, registerApiResponse, registerApiExample, openApi }) => {
    registerApiExample('GetProjectInfo', 'Detection classification response');
    registerApiResponse('GetImageAnnotation', (_req, res, ctx) => {
        const { mock } = openApi.mockResponseForOperation('GetImageAnnotation') as {
            mock: OpenApiResponseBody<'GetImageAnnotation'>;
        };

        const labels = mock.annotations?.at(0)?.labels?.map((label) => ({ ...label, id: '62946c62003ddb3967f1475b' }));
        const annotations = range(0, 100).map((id) => ({
            id: `annotation-${id}`,
            labels,
            labels_to_revisit: [],
            modified: '2021-09-08T12:43:22.265000+00:00',
            shape: {
                height: 20,
                type: 'RECTANGLE',
                width: 20,
                x: Math.round(Math.random() * 600) + 10,
                y: Math.round(Math.random() * 400) + 10,
            },
        }));

        return res(ctx.json({ ...mock, annotations }));
    });

    await page.goto(annotatorUrl);

    await expect(page.getByRole('checkbox', { name: new RegExp(`0 out of 100 annotations selected`) })).toBeVisible();
});

// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { expect, type Locator } from '@playwright/test';
import { getMockedProject } from 'mocks/mock-project';
import { HttpResponse } from 'msw';

import { http, test } from '../fixtures';
import { blueLabel, mockedDetectionProject, redLabel, useDetectionProjectFixtures } from './annotator-fixtures';

test.describe('Annotator - edit mode', () => {
    useDetectionProjectFixtures();

    test.describe('Edit mode', () => {
        const mockedSegmentationProject = getMockedProject({
            id: '123e4567-e89b-12d3-a456-426614174000',
            task: {
                exclusive_labels: true,
                task_type: 'instance_segmentation',
                labels: [redLabel, blueLabel],
            },
        });

        const smallPolygon = {
            type: 'polygon' as const,
            points: [
                { x: 100, y: 100 },
                { x: 250, y: 100 },
                { x: 250, y: 250 },
                { x: 100, y: 250 },
            ],
        };

        const secondPolygon = {
            type: 'polygon' as const,
            points: [
                { x: 400, y: 300 },
                { x: 550, y: 300 },
                { x: 550, y: 450 },
                { x: 400, y: 450 },
            ],
        };

        test('detection task — edits bounding box while bounding box tool stays active', async ({
            page,
            boundingBoxTool,
            annotatorPage,
        }) => {
            await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

            const selectedAnnotationRect = page.getByLabel('selected annotation').getByLabel('annotation rect').first();
            const getRectGeometry = async (rect: Locator) => {
                const [x, y, width, height] = await Promise.all([
                    rect.getAttribute('x'),
                    rect.getAttribute('y'),
                    rect.getAttribute('width'),
                    rect.getAttribute('height'),
                ]);

                return {
                    x,
                    y,
                    width,
                    height,
                };
            };

            await test.step('Draw a bounding box and keep drawing tool active', async () => {
                await boundingBoxTool.selectTool();
                await boundingBoxTool.drawBoundingBox({ x: 100, y: 100, width: 150, height: 150 });

                await expect(boundingBoxTool.getTool()).toHaveAttribute('aria-pressed', 'true');
                await expect(page.getByLabel(/^Edit bounding box points/)).toHaveCount(1);
            });

            const initialGeometry = await getRectGeometry(selectedAnnotationRect);

            await test.step('Resize the bounding box from south-east resize anchor', async () => {
                const southEastAnchor = page
                    .getByLabel('selected annotation')
                    .getByLabel('South east resize anchor')
                    .first();
                const anchorBox = await southEastAnchor.boundingBox();

                expect(anchorBox).not.toBeNull();

                if (anchorBox === null) {
                    return;
                }

                await page.mouse.move(anchorBox.x + anchorBox.width / 2, anchorBox.y + anchorBox.height / 2);
                await page.mouse.down();
                await page.mouse.move(anchorBox.x + anchorBox.width / 2 + 50, anchorBox.y + anchorBox.height / 2 + 40);
                await page.mouse.up();
            });

            await test.step('Bounding box geometry changes without switching tools', async () => {
                await expect
                    .poll(async () => {
                        return getRectGeometry(selectedAnnotationRect);
                    })
                    .not.toEqual(initialGeometry);

                await expect(page.getByLabel(/^Edit bounding box points/)).toHaveCount(1);
            });

            await test.step('Can draw another bounding box without switching to selection tool', async () => {
                await boundingBoxTool.drawBoundingBox({ x: 350, y: 250, width: 120, height: 120 });

                expect(await annotatorPage.getAnnotationsListItems('annotation rect')).toHaveLength(2);
            });
        });

        test('instance segmentation task — edits polygon point while polygon tool stays active', async ({
            page,
            polygonTool,
            annotatorPage,
            network,
        }) => {
            network.use(
                http.get('/api/projects/{project_id}', () => {
                    return HttpResponse.json(mockedSegmentationProject);
                })
            );

            await annotatorPage.goto(mockedSegmentationProject.id, 'item-1');

            await test.step('Draw a polygon and keep drawing tool active', async () => {
                await polygonTool.selectPolygonTool();
                await polygonTool.drawPolygon(smallPolygon);

                await expect(polygonTool.getTool()).toHaveAttribute('aria-pressed', 'true');
                await expect(page.locator('[id^="edit-polygon-points-"]')).toHaveCount(1);
            });

            const polygonAnnotation = page.getByLabel('selected annotation').getByLabel('annotation polygon').first();
            const initialPoints = (await polygonAnnotation.getAttribute('points')) ?? '';

            await test.step('Move polygon anchor while polygon tool is still selected', async () => {
                const polygonAnchor = page
                    .getByLabel('selected annotation')
                    .getByLabel('Resize polygon (250, 100) anchor')
                    .first();
                const anchorBox = await polygonAnchor.boundingBox();

                expect(anchorBox).not.toBeNull();

                if (anchorBox === null) {
                    return;
                }

                await page.mouse.move(anchorBox.x + anchorBox.width / 2, anchorBox.y + anchorBox.height / 2);
                await page.mouse.down();
                await page.mouse.move(anchorBox.x + anchorBox.width / 2 + 30, anchorBox.y + anchorBox.height / 2 + 20);
                await page.mouse.up();
            });

            await test.step('Polygon geometry changes without switching tools', async () => {
                await expect
                    .poll(async () => (await polygonAnnotation.getAttribute('points')) ?? '')
                    .not.toBe(initialPoints);
                await expect(page.locator('[id^="edit-polygon-points-"]')).toHaveCount(1);
            });

            await test.step('Can draw another polygon without switching to selection tool', async () => {
                await polygonTool.drawPolygon(secondPolygon);

                expect(await annotatorPage.getAnnotationsListItems('annotation polygon')).toHaveLength(2);
            });
        });

        test.describe('Edit mode deselection', () => {
            test('detection task — new shape enters edit mode and next shape replaces active edit selection', async ({
                page,
                boundingBoxTool,
                annotatorPage,
            }) => {
                await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

                await test.step('Draw first bounding box and verify it enters edit mode immediately', async () => {
                    await boundingBoxTool.selectTool();
                    await boundingBoxTool.drawBoundingBox({ x: 100, y: 100, width: 150, height: 150 });

                    await expect(page.getByLabel(/^Edit bounding box points/)).toHaveCount(1);
                    await expect(annotatorPage.getAnnotationsList().getByLabel('selected annotation')).toHaveCount(1);
                });

                await test.step('Draw second bounding box with the same tool', async () => {
                    await boundingBoxTool.selectTool();
                    await boundingBoxTool.drawBoundingBox({ x: 350, y: 250, width: 150, height: 150 });
                });

                await test.step('Only the newly created annotation remains in edit mode', async () => {
                    await expect(page.getByLabel(/^Edit bounding box points/)).toHaveCount(1);
                    await expect(annotatorPage.getAnnotationsList().getByLabel('selected annotation')).toHaveCount(1);
                    expect(await annotatorPage.getAnnotationsListItems('annotation rect')).toHaveLength(2);
                });
            });

            test('detection task — selection tool edit mode is replaced by newly drawn shape', async ({
                page,
                boundingBoxTool,
                annotatorPage,
            }) => {
                await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

                await test.step('Draw first bounding box', async () => {
                    await boundingBoxTool.selectTool();
                    await boundingBoxTool.drawBoundingBox({ x: 100, y: 100, width: 150, height: 150 });
                });

                await test.step('Enter edit mode via selection tool', async () => {
                    await page.getByRole('button', { name: 'Selection' }).click();
                    await page.getByLabel('annotation rect').first().click();

                    await expect(page.getByLabel(/^Edit bounding box points/)).toHaveCount(1);
                    await expect(annotatorPage.getAnnotationsList().getByLabel('selected annotation')).toHaveCount(1);
                });

                await test.step('Draw second bounding box', async () => {
                    await boundingBoxTool.selectTool();
                    await boundingBoxTool.drawBoundingBox({ x: 350, y: 250, width: 150, height: 150 });
                });

                await test.step('Previously selected annotation is deselected and new one is in edit mode', async () => {
                    await expect(page.getByLabel(/^Edit bounding box points/)).toHaveCount(1);
                    await expect(annotatorPage.getAnnotationsList().getByLabel('selected annotation')).toHaveCount(1);
                    expect(await annotatorPage.getAnnotationsListItems('annotation rect')).toHaveLength(2);
                });
            });

            test('instance segmentation task — new shape enters edit mode and next shape replaces active edit selection', async ({
                page,
                polygonTool,
                annotatorPage,
                network,
            }) => {
                network.use(
                    http.get('/api/projects/{project_id}', () => {
                        return HttpResponse.json(mockedSegmentationProject);
                    })
                );

                await annotatorPage.goto(mockedSegmentationProject.id, 'item-1');

                await test.step('Draw first polygon and verify it enters edit mode immediately', async () => {
                    await polygonTool.selectPolygonTool();
                    await polygonTool.drawPolygon(smallPolygon);

                    await expect(page.locator('[id^="edit-polygon-points-"]')).toHaveCount(1);
                    await expect(annotatorPage.getAnnotationsList().getByLabel('selected annotation')).toHaveCount(1);
                });

                await test.step('Draw second polygon with the same tool', async () => {
                    await polygonTool.selectPolygonTool();
                    await polygonTool.drawPolygon(secondPolygon);
                });

                await test.step('Only the newly created annotation remains in edit mode', async () => {
                    await expect(page.locator('[id^="edit-polygon-points-"]')).toHaveCount(1);
                    await expect(annotatorPage.getAnnotationsList().getByLabel('selected annotation')).toHaveCount(1);
                    expect(await annotatorPage.getAnnotationsListItems('annotation polygon')).toHaveLength(2);
                });
            });

            test('instance segmentation task — selection tool edit mode is replaced by newly drawn shape', async ({
                page,
                polygonTool,
                annotatorPage,
                network,
            }) => {
                network.use(
                    http.get('/api/projects/{project_id}', () => {
                        return HttpResponse.json(mockedSegmentationProject);
                    })
                );

                await annotatorPage.goto(mockedSegmentationProject.id, 'item-1');

                await test.step('Draw first polygon', async () => {
                    await polygonTool.selectPolygonTool();
                    await polygonTool.drawPolygon(smallPolygon);
                });

                await test.step('Enter edit mode via selection tool', async () => {
                    await page.getByRole('button', { name: 'Selection' }).click();
                    await page.getByLabel('annotation polygon').first().click();

                    await expect(page.locator('[id^="edit-polygon-points-"]')).toHaveCount(1);
                    await expect(annotatorPage.getAnnotationsList().getByLabel('selected annotation')).toHaveCount(1);
                });

                await test.step('Draw second polygon', async () => {
                    await polygonTool.selectPolygonTool();
                    await polygonTool.drawPolygon(secondPolygon);
                });

                await test.step('Previously selected annotation is deselected and new one is in edit mode', async () => {
                    await expect(page.locator('[id^="edit-polygon-points-"]')).toHaveCount(1);
                    await expect(annotatorPage.getAnnotationsList().getByLabel('selected annotation')).toHaveCount(1);
                    expect(await annotatorPage.getAnnotationsListItems('annotation polygon')).toHaveLength(2);
                });
            });
        });
    });
});

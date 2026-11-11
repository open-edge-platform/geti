// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { AnnotationDTO } from '@/api/types';
import { expect } from '@playwright/test';
import { getMockedProject } from 'mocks/mock-project';
import { HttpResponse } from 'msw';

import { http, test } from '../../fixtures';
import { candyBinaryHandler, redLabel } from '../annotator-fixtures';

const mockedProject = getMockedProject({
    id: 'magnetic-lasso-project',
    task: { exclusive_labels: true, task_type: 'instance_segmentation', labels: [redLabel] },
});

// Roughly the outline of the computer mouse in `candy.png`.
const OUTLINE = [
    { x: 330, y: 215 },
    { x: 490, y: 400 },
    { x: 400, y: 495 },
    { x: 245, y: 285 },
];

test.describe('Magnetic lasso tool', () => {
    test.beforeEach(async ({ network }) => {
        network.use(
            http.get('/api/projects/{project_id}', () => HttpResponse.json(mockedProject)),
            candyBinaryHandler,
            http.post('/api/projects/{project_id}/dataset/media/{media_id}/annotations', async ({ request }) => {
                const body = (await request.json()) as { annotations: AnnotationDTO[] };

                return HttpResponse.json(
                    { annotations: body.annotations, user_reviewed: true, subset: 'training' },
                    { status: 201 }
                );
            })
        );
    });

    test('snaps the outline to the object edges', async ({ page, annotatorPage, magneticLassoTool }) => {
        await annotatorPage.goto(mockedProject.id, 'item-1');

        let points: { x: number; y: number }[] = [];

        await test.step('Place the first point once the worker is ready', async () => {
            points = await magneticLassoTool.startOutline(OUTLINE);
        });

        await test.step('Click along the edges and close the outline', async () => {
            for (const point of [...points.slice(2), points[0]]) {
                await magneticLassoTool.click();
                await magneticLassoTool.hoverUntilSnapped(point);
            }

            await magneticLassoTool.click();

            await expect(async () => {
                expect(await annotatorPage.getAnnotationsListItems('annotation polygon')).toHaveLength(1);
            }).toPass();
            await expect(page.getByLabel('new polygon')).toBeHidden();
        });

        await test.step('Submit a polygon that follows the edges', async () => {
            const response = await annotatorPage.submitAndWaitForSave();
            const { annotations } = response.request().postDataJSON() as { annotations: AnnotationDTO[] };

            expect(annotations).toHaveLength(1);
            expect(annotations[0].labels).toEqual([{ id: redLabel.id }]);

            const { shape } = annotations[0];
            expect(shape.type).toBe('polygon');

            if (shape.type === 'polygon') {
                // A plain polygon would only contain the clicked points.
                expect(shape.points.length).toBeGreaterThan(OUTLINE.length);

                const xs = OUTLINE.map(({ x }) => x);
                const ys = OUTLINE.map(({ y }) => y);
                const tolerance = 50;

                for (const { x, y } of shape.points) {
                    expect(x).toBeGreaterThanOrEqual(Math.min(...xs) - tolerance);
                    expect(x).toBeLessThanOrEqual(Math.max(...xs) + tolerance);
                    expect(y).toBeGreaterThanOrEqual(Math.min(...ys) - tolerance);
                    expect(y).toBeLessThanOrEqual(Math.max(...ys) + tolerance);
                }
            }
        });
    });

    test('right-clicking does not close the outline', async ({ page, annotatorPage, magneticLassoTool }) => {
        await annotatorPage.goto(mockedProject.id, 'item-1');

        let points: { x: number; y: number }[] = [];

        await test.step('Outline the object up to the starting point', async () => {
            points = await magneticLassoTool.startOutline(OUTLINE);

            for (const point of [...points.slice(2), points[0]]) {
                await magneticLassoTool.click();
                await magneticLassoTool.hoverUntilSnapped(point);
            }
        });

        await test.step('Right-click on the starting point', async () => {
            await page.mouse.click(points[0].x, points[0].y, { button: 'right' });

            await expect(page.getByLabel('new polygon')).toBeVisible();
            expect(await annotatorPage.getAnnotationsListItems('annotation polygon')).toHaveLength(0);
        });

        await test.step('Left-click on the starting point closes the outline', async () => {
            await magneticLassoTool.click();

            await expect(async () => {
                expect(await annotatorPage.getAnnotationsListItems('annotation polygon')).toHaveLength(1);
            }).toPass();
            await expect(page.getByLabel('new polygon')).toBeHidden();
        });
    });
});

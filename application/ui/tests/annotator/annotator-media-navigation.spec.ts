// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { AnnotationDTO, DatasetSubset } from '@/api/types';
import { expect } from '@playwright/test';
import { getMockedMediaImage } from 'mocks/mock-media';
import { getMockedProject } from 'mocks/mock-project';
import { HttpResponse } from 'msw';

import { Polygon } from '../../src/shared/types';
import { http, test } from '../fixtures';
import { blueLabel, mockedDetectionProject, redLabel, useDetectionProjectFixtures } from './annotator-fixtures';

test.describe('Annotator - media navigation', () => {
    useDetectionProjectFixtures();

    test('Tool selection persists across media items', async ({ polygonTool, annotatorPage, network }) => {
        const smallPolygon: Polygon = {
            type: 'polygon',
            points: [
                { x: 100, y: 100 },
                { x: 150, y: 100 },
                { x: 150, y: 150 },
                { x: 100, y: 150 },
            ],
        };

        const mediaItems = [
            getMockedMediaImage({ id: 'media-1', name: 'item-1.jpg', width: 1920, height: 1080 }),
            getMockedMediaImage({ id: 'media-2', name: 'item-2.jpg', width: 1920, height: 1080 }),
        ];
        const mockedSegmentationProject = getMockedProject({
            id: '123e4567-e89b-12d3-a456-426614174000',
            task: {
                exclusive_labels: true,
                task_type: 'instance_segmentation',
                labels: [redLabel, blueLabel],
            },
        });

        network.use(
            http.get('/api/projects/{project_id}', () => {
                return HttpResponse.json(mockedSegmentationProject);
            }),
            http.get('/api/projects/{project_id}/dataset/media', () => {
                return HttpResponse.json({
                    items: mediaItems,
                    pagination: {
                        offset: 0,
                        limit: 10,
                        count: mediaItems.length,
                        total: mediaItems.length,
                    },
                });
            }),
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', () => {
                return HttpResponse.json({
                    annotations: [],
                    user_reviewed: true,
                    subset: 'training',
                });
            })
        );

        await annotatorPage.goto(mockedSegmentationProject.id, 'media-1');

        await test.step('Select polygon tool on first media item', async () => {
            await polygonTool.selectPolygonTool();
        });

        await test.step('Navigate to second media item by clicking in sidebar', async () => {
            await annotatorPage.selectMediaItem('item-2.jpg');

            await expect(annotatorPage.getAnnotationsList()).toBeVisible();
        });

        await test.step('Verify polygon tool persisted by drawing a polygon', async () => {
            // If polygon tool persisted, we should be able to draw immediately without reselecting
            await polygonTool.drawPolygon(smallPolygon);

            expect(await annotatorPage.getAnnotationsListItems('annotation polygon')).toHaveLength(1);
        });

        await test.step('Navigate back to first media item', async () => {
            await annotatorPage.selectMediaItem('item-1.jpg');

            await expect(annotatorPage.getAnnotationsList()).toBeVisible();
        });

        await test.step('Verify polygon tool still works after navigating back', async () => {
            // Draw another polygon to verify tool is still active
            await polygonTool.drawPolygon(smallPolygon);

            expect(await annotatorPage.getAnnotationsListItems('annotation polygon')).toHaveLength(1);
        });
    });

    test('Annotations reset correctly when switching media items', async ({ annotatorPage, network }) => {
        const mediaItems = [
            getMockedMediaImage({ id: 'media-reset-1', name: 'item-1.jpg', width: 1920, height: 1080 }),
            getMockedMediaImage({ id: 'media-reset-2', name: 'item-2.jpg', width: 1920, height: 1080 }),
        ];

        const mediaAnnotations: Record<string, AnnotationDTO[]> = {
            'media-reset-1': [
                {
                    shape: {
                        type: 'rectangle',
                        x: 80,
                        y: 120,
                        width: 140,
                        height: 120,
                    },
                    labels: [{ id: redLabel.id }],
                },
            ],
            'media-reset-2': [],
        };

        network.use(
            http.get('/api/projects/{project_id}/dataset/media', () => {
                return HttpResponse.json({
                    items: mediaItems,
                    pagination: {
                        offset: 0,
                        limit: 10,
                        count: mediaItems.length,
                        total: mediaItems.length,
                    },
                });
            }),
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', ({ params }) => {
                return HttpResponse.json({
                    annotations: mediaAnnotations[params.media_id] ?? [],
                    user_reviewed: true,
                    subset: 'training',
                });
            })
        );

        await annotatorPage.goto(mockedDetectionProject.id, 'media-reset-1');

        await test.step('Check first media annotations', async () => {
            await expect(annotatorPage.getAnnotationsList()).toBeVisible();

            expect(await annotatorPage.getAnnotationsListItems('annotation rect')).toHaveLength(1);
        });

        await test.step('Switching to media 2 clears media 1 annotations', async () => {
            await annotatorPage.selectMediaItem('item-2.jpg');

            await expect(annotatorPage.getAnnotationsList()).toBeVisible();
            expect(await annotatorPage.getAnnotationsListItems('annotation rect')).toHaveLength(0);
        });

        await test.step('Switching back restores media 1 annotations', async () => {
            await annotatorPage.selectMediaItem('item-1.jpg');

            await expect(annotatorPage.getAnnotationsList()).toBeVisible();
            expect(await annotatorPage.getAnnotationsListItems('annotation rect')).toHaveLength(1);
        });
    });

    test('Selected annotations reset when switching media items', async ({ page, annotatorPage, network }) => {
        const mediaItems = [
            getMockedMediaImage({ id: 'media-selection-reset-1', name: 'item-1.jpg', width: 1920, height: 1080 }),
            getMockedMediaImage({ id: 'media-selection-reset-2', name: 'item-2.jpg', width: 1920, height: 1080 }),
        ];

        const mediaAnnotations: Record<string, AnnotationDTO[]> = {
            'media-selection-reset-1': [
                {
                    shape: {
                        type: 'rectangle',
                        x: 80,
                        y: 120,
                        width: 140,
                        height: 120,
                    },
                    labels: [{ id: redLabel.id }],
                },
            ],
            'media-selection-reset-2': [],
        };

        network.use(
            http.get('/api/projects/{project_id}/dataset/media', () => {
                return HttpResponse.json({
                    items: mediaItems,
                    pagination: {
                        offset: 0,
                        limit: 10,
                        count: mediaItems.length,
                        total: mediaItems.length,
                    },
                });
            }),
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', ({ params }) => {
                return HttpResponse.json({
                    annotations: mediaAnnotations[params.media_id] ?? [],
                    user_reviewed: true,
                    subset: 'training',
                });
            })
        );

        await annotatorPage.goto(mockedDetectionProject.id, 'media-selection-reset-1');

        await test.step('Select annotation on media 1', async () => {
            await page.getByRole('button', { name: 'Selection' }).click();
            await page.getByLabel('annotation rect').first().click();

            const selectedAnnotations = annotatorPage.getAnnotationsList().getByLabel('selected annotation');
            await expect(selectedAnnotations).toHaveCount(1);
        });

        await test.step('Switch to media 2 and back to media 1 resets selection', async () => {
            await annotatorPage.selectMediaItem('item-2.jpg');
            await expect(annotatorPage.getAnnotationsList()).toBeVisible();
            expect(await annotatorPage.getAnnotationsListItems('annotation rect')).toHaveLength(0);

            await annotatorPage.selectMediaItem('item-1.jpg');
            await expect(annotatorPage.getAnnotationsList()).toBeVisible();

            expect(await annotatorPage.getAnnotationsListItems('annotation rect')).toHaveLength(1);

            const selectedAnnotations = annotatorPage.getAnnotationsList().getByLabel('selected annotation');
            await expect(selectedAnnotations).toHaveCount(0);
        });
    });

    test('Assigns subset to media', async ({ annotatorPage, boundingBoxTool, network }) => {
        const mediaItems = [
            getMockedMediaImage({ id: 'media-1', name: 'item-1.jpg', width: 1920, height: 1080 }),
            getMockedMediaImage({ id: 'media-2', name: 'item-2.jpg', width: 1920, height: 1080 }),
        ];
        let subsetPayload: DatasetSubset | null = 'unassigned';

        const annotationsResponsePerMedia: Record<
            string,
            { annotations: AnnotationDTO[]; user_reviewed: boolean; subset: DatasetSubset }
        > = {
            [mediaItems[0].id]: {
                annotations: [],
                user_reviewed: false,
                subset: 'unassigned',
            },
            [mediaItems[1].id]: {
                annotations: [],
                user_reviewed: false,
                subset: 'validation',
            },
        };

        network.use(
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', async ({ params }) => {
                return HttpResponse.json(annotationsResponsePerMedia[params.media_id]);
            }),
            http.get('/api/projects/{project_id}/dataset/media', () => {
                return HttpResponse.json({
                    items: mediaItems,
                    pagination: {
                        offset: 0,
                        limit: 10,
                        count: mediaItems.length,
                        total: mediaItems.length,
                    },
                });
            }),
            http.post(
                '/api/projects/{project_id}/dataset/media/{media_id}/annotations',
                async ({ request, params }) => {
                    const payload = await request.json();
                    subsetPayload = payload.subset ?? null;
                    annotationsResponsePerMedia[params.media_id].subset = payload.subset ?? 'unassigned';
                    annotationsResponsePerMedia[params.media_id].annotations = payload.annotations;

                    return HttpResponse.json({});
                }
            )
        );

        await annotatorPage.goto(mockedDetectionProject.id, mediaItems[0].id);

        await test.step('Draw an annotation', async () => {
            await boundingBoxTool.selectTool();
            await boundingBoxTool.drawBoundingBox({ x: 100, y: 100, width: 150, height: 150 });
        });

        await test.step('Select subset', async () => {
            await annotatorPage.selectSubset('training');
        });

        await test.step('Submit annotations and subset', async () => {
            await annotatorPage.submit();

            expect(subsetPayload).toBe('training');
        });

        await test.step('Navigate to the next media item by clicking in sidebar', async () => {
            await annotatorPage.selectMediaItem(mediaItems[1].name);

            await expect(annotatorPage.getSelectedSubset()).toHaveText('Validation');
        });

        await test.step('Navigate to the previous media item by clicking in sidebar', async () => {
            await annotatorPage.selectMediaItem(mediaItems[0].name);

            await expect(annotatorPage.getSelectedSubset()).toHaveText('Training');
        });
    });
});

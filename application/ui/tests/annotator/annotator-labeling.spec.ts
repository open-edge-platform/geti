// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { expect } from '@playwright/test';
import { getMockedMediaImage } from 'mocks/mock-media';
import { HttpResponse } from 'msw';

import { http, test } from '../fixtures';
import { blueLabel, mockedDetectionProject, redLabel, useDetectionProjectFixtures } from './annotator-fixtures';

test.describe('Annotator - labeling', () => {
    useDetectionProjectFixtures();

    test('Add and change annotations labels', async ({ page, boundingBoxTool, annotatorPage }) => {
        await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

        await test.step('Draw an annotation', async () => {
            await boundingBoxTool.selectTool();
            await boundingBoxTool.drawBoundingBox({ x: 100, y: 100, width: 150, height: 150 });

            await expect(page.getByLabel(`label ${redLabel.name} background`)).toHaveCount(1);
        });

        await test.step('Change annotation label by clicking label badge', async () => {
            await page.getByRole('button', { name: 'Selection' }).click();
            await page.getByLabel('annotation rect').first().click();

            await expect(page.getByRole('button', { name: `Label ${redLabel.name}` })).toHaveAttribute(
                'aria-pressed',
                'true'
            );

            await page.getByRole('button', { name: `Label ${blueLabel.name}` }).click();

            await expect(page.getByLabel(`label ${blueLabel.name} background`)).toHaveCount(1);
            await expect(page.getByRole('button', { name: `Label ${blueLabel.name}` })).toHaveAttribute(
                'aria-pressed',
                'true'
            );
        });

        await test.step('Draw a second annotation', async () => {
            await boundingBoxTool.selectTool();
            await boundingBoxTool.drawBoundingBox({ x: 300, y: 200, width: 150, height: 150 });

            await expect(page.getByLabel(`label ${blueLabel.name} background`)).toHaveCount(2);
        });

        await test.step('Change second annotation to red label', async () => {
            await page.getByRole('button', { name: 'Selection' }).click();
            await page.getByLabel('annotation rect').nth(0).click();
            await page.getByRole('button', { name: `Label ${redLabel.name}` }).click();

            await expect(page.getByLabel(`label ${redLabel.name} background`)).toHaveCount(1);
        });

        await test.step('Verify both annotations have correct labels', async () => {
            await expect(page.getByLabel(`label ${blueLabel.name} background`)).toHaveCount(1);
            await expect(page.getByLabel(`label ${redLabel.name} background`)).toHaveCount(1);
        });
    });

    test('change multiple labels at once', async ({ page, boundingBoxTool, annotatorPage }) => {
        await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

        const annotations = [
            { x: 100, y: 100, width: 150, height: 150 },
            { x: 300, y: 200, width: 150, height: 150 },
            { x: 600, y: 300, width: 150, height: 150 },
        ];

        await test.step('Draw annotations', async () => {
            await boundingBoxTool.selectTool();

            for await (const annotation of annotations) {
                await boundingBoxTool.drawBoundingBox(annotation);
            }

            await expect(page.getByLabel(`label ${redLabel.name} background`)).toHaveCount(annotations.length);
        });

        await test.step('Remove labels', async () => {
            await page.getByRole('button', { name: 'Selection' }).click();
            const labels = page.getByLabel('Remove red-label');

            await labels.nth(0).click();
            await labels.nth(1).click();
        });

        await test.step('Change selected annotations label using label badge', async () => {
            const container = page.getByLabel('annotation rect');

            // Selecting moves an annotation to the back of the DOM (selected shapes render on top),
            // so the next still-unselected annotation is always at index 0.
            await container.nth(0).click();
            await container.nth(0).click({ modifiers: ['Shift'] });
            await container.nth(0).click({ modifiers: ['Shift'] });

            await page.getByRole('button', { name: `Label ${blueLabel.name}` }).click();

            await expect(page.getByLabel(`label ${blueLabel.name} background`)).toHaveCount(annotations.length);
        });
    });

    test.describe('Handles empty label', () => {
        test('label assignment', async ({ page, boundingBoxTool, annotatorPage }) => {
            await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

            const annotations = [
                { x: 100, y: 100, width: 150, height: 150 },
                { x: 300, y: 200, width: 150, height: 150 },
                { x: 600, y: 300, width: 150, height: 150 },
            ];

            await test.step('Draw annotations', async () => {
                await boundingBoxTool.selectTool();

                for await (const annotation of annotations) {
                    await boundingBoxTool.drawBoundingBox(annotation);
                }

                await expect(page.getByLabel(`label ${redLabel.name} background`)).toHaveCount(annotations.length);
            });

            await test.step('Assigning "No object" removes other annotations', async () => {
                await page.getByLabel('Label No object').click();

                await expect(page.getByLabel(`label ${redLabel.name} background`)).toHaveCount(0);
                await expect(page.getByLabel(`label No object background`)).toHaveCount(1);
            });

            await test.step('Drawing new annotation removes "No object" annotation', async () => {
                await boundingBoxTool.selectTool();

                await boundingBoxTool.drawBoundingBox({ x: 100, y: 100, width: 150, height: 150 });

                await expect(page.getByLabel(`label ${redLabel.name} background`)).toHaveCount(1);
                await expect(page.getByLabel(`label No object background`)).toHaveCount(0);
            });
        });

        test('renders "No object" when server returns empty annotations list', async ({ page, annotatorPage }) => {
            await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

            await expect(annotatorPage.getAnnotationsList()).toBeVisible();
            await expect(page.getByLabel(`label No object background`)).toHaveCount(1);
        });

        test('drawing a new annotation removes global annotation', async ({ page, boundingBoxTool, annotatorPage }) => {
            await annotatorPage.goto(mockedDetectionProject.id, 'item-1');

            await test.step('Verify global "No object" annotation is visible initially', async () => {
                await expect(annotatorPage.getAnnotationsList()).toBeVisible();
                await expect(page.getByLabel('label No object background')).toHaveCount(1);
            });

            await test.step('Remove the label, annotation still exists', async () => {
                await page.getByRole('button', { name: 'Remove No object' }).click();
                await expect(page.getByLabel('label No label background')).toHaveCount(1);
            });

            await test.step('Draw a new annotation', async () => {
                await boundingBoxTool.selectTool();
                await boundingBoxTool.drawBoundingBox({ x: 220, y: 180, width: 180, height: 160 });
            });

            await test.step('Global annotation without the label is removed and new annotation is visible', async () => {
                await expect(page.getByLabel('label No label background')).toHaveCount(0);
                await expect(page.getByLabel(`label ${redLabel.name} background`)).toHaveCount(1);
                await expect(page.getByLabel(`label ${redLabel.name} background`).first()).toBeVisible();
            });
        });
    });

    test('Selected label persists when switching media items', async ({ page, network, annotatorPage }) => {
        const mediaItems = [
            getMockedMediaImage({ id: 'media-1', name: 'item-1.jpg', width: 1920, height: 1080 }),
            getMockedMediaImage({ id: 'media-2', name: 'item-2.jpg', width: 1920, height: 1080 }),
        ];

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
            http.get('/api/projects/{project_id}/dataset/media/{media_id}/annotations', () => {
                return HttpResponse.json({
                    annotations: [],
                    user_reviewed: true,
                    subset: 'training',
                });
            })
        );

        await annotatorPage.goto(mockedDetectionProject.id, 'media-1');

        await test.step('Select non-default label on first media item', async () => {
            const blueLabelButton = page.getByRole('button', { name: `Label ${blueLabel.name}` });
            await blueLabelButton.click();

            await expect(blueLabelButton).toHaveAttribute('aria-pressed', 'true');
        });

        await test.step('Switching media keeps selected label active', async () => {
            await annotatorPage.selectMediaItem('item-2.jpg');

            await expect(page.getByRole('button', { name: `Label ${blueLabel.name}` })).toHaveAttribute(
                'aria-pressed',
                'true'
            );
        });
    });
});

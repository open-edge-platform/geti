// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { expect, type Page } from '@playwright/test';

import { withRelative } from '../utils/mouse';

export class SegmentAnythingToolPage {
    constructor(private readonly page: Page) {}

    getTool() {
        return this.page.getByRole('button', { name: 'Auto segmentation' });
    }

    // The canvas only renders once the SAM model is loaded, and the image embedding is processed afterwards.
    async selectTool() {
        await this.getTool().click();

        await expect(this.getCanvas()).toBeVisible({ timeout: 60_000 });
        await expect(this.getProcessingImage()).toBeHidden();
    }

    getCanvas() {
        return this.page.getByLabel('SAM tool canvas');
    }

    getProcessingImage() {
        return this.page.getByText('Processing image, please wait...');
    }

    getPreview() {
        return this.page.getByLabel('Segment anything preview');
    }

    getPositivePoints() {
        return this.page.getByLabel('Positive point');
    }

    getNegativePoints() {
        return this.page.getByLabel('Negative point');
    }

    // Hovers an image point, waits for the preview and clicks to accept it.
    async hoverAndAccept(x: number, y: number) {
        const relative = await withRelative(this.page);
        const point = relative(x, y);

        await this.page.mouse.move(point.x, point.y);
        await expect(this.getPreview()).toBeVisible({ timeout: 15_000 });

        await this.page.mouse.down();
        await this.page.mouse.up();
    }

    // Shift + click places a positive point, Alt + click a negative one.
    async addPoint(x: number, y: number, modifier: 'Shift' | 'Alt') {
        const relative = await withRelative(this.page);
        const point = relative(x, y);

        await this.page.mouse.move(point.x, point.y);
        await this.page.keyboard.down(modifier);
        await this.page.mouse.down();
        await this.page.mouse.up();
        await this.page.keyboard.up(modifier);
    }
}

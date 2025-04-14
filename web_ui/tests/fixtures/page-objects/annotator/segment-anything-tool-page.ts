// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

export class SegmentAnythingToolPage {
    constructor(private page: Page) {}

    async getTool() {
        return this.page.getByRole('button', { name: 'Auto segmentation' });
    }

    async selectTool() {
        await (await this.getTool()).click();

        await expect(this.page.getByRole('progressbar', { name: 'Extracting image features' })).toBeHidden({
            timeout: 30000,
        });
    }

    async acceptAnnotation() {
        await this.page.getByRole('button', { name: 'accept segment-anything annotation' }).click();
    }

    async enableInteractiveMode() {
        await this.page.getByRole('switch', { name: 'Interactive mode' }).click();
    }

    async getResultShape() {
        return this.page
            .getByLabel('Segment anything result')
            .locator('polygon')
            .or(this.page.getByLabel('Segment anything result').locator('rect'));
    }

    async waitForResultShape() {
        await expect(this.page.getByLabel('Processing input')).toBeHidden();
    }
}

// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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

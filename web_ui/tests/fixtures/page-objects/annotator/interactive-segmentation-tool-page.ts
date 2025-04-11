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

import { Rect } from '../../../../src/core/annotations/shapes.interface';
import { BoundingBoxToolPage } from './bounding-box-tool-page';

export class InteractiveSegmentationToolPage {
    constructor(
        private page: Page,
        private boundingBoxTool: BoundingBoxToolPage
    ) {}

    async drawBoundingBox(shape: Omit<Rect, 'shapeType'>) {
        await this.boundingBoxTool.drawBoundingBox(shape);
    }

    async getTool() {
        return this.page.getByRole('button', { name: 'Interactive segmentation' });
    }

    async selectTool() {
        await (await this.getTool()).click();

        await expect(this.page.getByText('Loading...')).toBeHidden({ timeout: 10000 });
    }

    async getRightClickMode() {
        return this.page.getByRole('switch', {
            name: 'Right-click mode',
        });
    }

    async getDynamicSelectionMode() {
        return this.page.getByRole('switch', {
            name: 'Dynamic selection mode',
        });
    }

    async toggleRightClickMode() {
        await (await this.getRightClickMode()).click();
    }

    async toggleDynamicSelectionMode() {
        await (await this.getDynamicSelectionMode()).click();
    }

    async acceptAnnotation(hotkeys = false) {
        hotkeys
            ? await this.page.keyboard.press('Enter')
            : await this.page.getByRole('button', { name: 'accept ritm annotation' }).click();
    }

    async cancelAnnotation(hotkeys = false) {
        hotkeys
            ? await this.page.keyboard.press('Escape')
            : await this.page.getByRole('button', { name: 'reject ritm annotation' }).click();
    }
}

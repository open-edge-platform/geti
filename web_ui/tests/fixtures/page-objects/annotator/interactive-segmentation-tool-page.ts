// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

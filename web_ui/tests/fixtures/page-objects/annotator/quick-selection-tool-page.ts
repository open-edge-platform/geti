// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

import { Rect } from '../../../../src/core/annotations/shapes.interface';
import { clickAndMove } from '../../../utils/mouse';
import { BoundingBoxToolPage } from './bounding-box-tool-page';

export class QuickSelectionToolPage {
    constructor(
        private page: Page,
        private boundingBoxTool: BoundingBoxToolPage
    ) {}

    async drawBoundingBox(shape: Omit<Rect, 'shapeType'>) {
        await this.boundingBoxTool.drawBoundingBox(shape);
    }

    async getTool() {
        return this.page.getByRole('button', { name: 'Quick Selection', exact: true });
    }

    async selectTool() {
        await (await this.getTool()).click();

        // Wait for OpenCV to be loaded
        await expect(this.page.locator('role=button[name="New selection"]')).toBeEnabled();
    }

    async getSensitivitySlider() {
        return this.page.getByLabel('Sensitivity slider').locator('input[type=range]');
    }

    async getSensitivitySliderValue() {
        return (await this.getSensitivitySlider()).inputValue();
    }

    async getSensitivityButton() {
        return this.page.getByRole('button', {
            name: 'Sensitivity button',
        });
    }

    async openSensitivityButton() {
        await (await this.getSensitivityButton()).click();
    }

    async changeSensitivity(xOffset: number) {
        await this.openSensitivityButton();

        const sensitivitySlider = await this.getSensitivitySlider();

        const sensitivitySliderBoundingBox = await sensitivitySlider.boundingBox();

        if (!sensitivitySliderBoundingBox) {
            throw new Error('Bounding box not found');
        }

        const { x, y, width, height } = sensitivitySliderBoundingBox;

        const startPoint = { x: x + width / 2, y: y + height / 2 };
        const endPosition = { x: startPoint.x + xOffset, y: startPoint.y / 2 };

        await clickAndMove(this.page, startPoint, endPosition);
    }

    async acceptAnnotation() {
        await this.page.getByRole('button', { name: 'accept grabcut annotation' }).click();
    }

    async rejectAnnotation() {
        await this.page.getByRole('button', { name: 'reject grabcut annotation' }).click();
    }
}

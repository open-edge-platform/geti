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

import { clickAndMove } from '../../../utils/mouse';

export class ExplanationPage {
    constructor(private page: Page) {}

    async getExplanationButton() {
        return this.page.getByLabel('explanation-switcher');
    }

    async activateTool() {
        const explanationSwitcher = await this.getExplanationButton();
        await explanationSwitcher.click();
    }

    async getOpacitySliderButton() {
        return this.page.getByLabel('opacity button');
    }

    async getOpacitySlider() {
        return this.page.getByLabel('opacity slider').locator('input[type=range]');
    }

    async selectExplanationOption(name: string) {
        const dropdown = this.page.getByRole('button', { name: /show explanations dropdown/ });
        await dropdown.click();

        const labelOption = this.page.getByRole('option', { name, exact: true });
        await labelOption.click();
    }

    async getCanvas() {
        return this.page.getByLabel('explanation image');
    }

    async getCanvasProperties() {
        const canvas = await this.getCanvas();
        return canvas.evaluate((element) => ({
            top: window.getComputedStyle(element).getPropertyValue('margin-top'),
            left: window.getComputedStyle(element).getPropertyValue('margin-left'),
            opacity: window.getComputedStyle(element).getPropertyValue('opacity'),
        }));
    }

    async expectToHaveExplanation(position = { top: '0px', left: '0px' }) {
        await this.activateTool();

        const canvas = await this.getCanvas();
        const { top, left } = await this.getCanvasProperties();

        await expect(canvas).toBeVisible();
        expect({ top, left }).toEqual(position);
    }

    async moveOpacitySlider(number: number) {
        const range = await this.getOpacitySlider();

        const sensitivitySliderBoundingBox = await range.boundingBox();

        if (!sensitivitySliderBoundingBox) {
            throw new Error('Bounding box not found');
        }

        const { x, y, width, height } = sensitivitySliderBoundingBox;

        const startPoint = { x: x + width / 2, y: y + height / 2 };
        const endPosition = { x: startPoint.x + number, y: startPoint.y };

        await clickAndMove(this.page, startPoint, endPosition);
        return range.inputValue();
    }

    async expectCanvasHasOpacityOf(newOpacity: number) {
        const canvasProperties = await this.getCanvasProperties();
        expect(Number(canvasProperties.opacity)).toBe(newOpacity);
    }
}

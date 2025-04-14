// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

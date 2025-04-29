// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

import { Circle } from '../../../../src/core/annotations/shapes.interface';
import { clickAndMove, withRelative } from '../../../utils/mouse';

type DrawCircleArgs = Omit<Circle, 'shapeType'> & { options?: Parameters<Page['mouse']['down']>[0] };

export class CircleToolPage {
    constructor(private page: Page) {}

    async drawCircle({ x, y, r, options }: DrawCircleArgs) {
        const relative = await withRelative(this.page);
        const startPoint = relative(x, y);
        const endPoint = relative(x + r, y);

        await clickAndMove(this.page, startPoint, endPoint, options);
    }

    async getRadiusSlider() {
        return this.page.getByLabel('Circle radius').locator('input[type=range]');
    }

    async getRadiusSliderValue() {
        return (await this.getRadiusSlider()).inputValue();
    }

    async changeRadius(xOffset: number) {
        const radiusSlider = await this.getRadiusSlider();

        const radiusSliderBoundingBox = await radiusSlider.boundingBox();

        if (!radiusSliderBoundingBox) {
            throw new Error('Bounding box not found');
        }

        const { x, y, width, height } = radiusSliderBoundingBox;

        const startPoint = { x: x + width / 2, y: y + height / 2 };
        const endPosition = { x: startPoint.x + xOffset, y: startPoint.y / 2 };

        await clickAndMove(this.page, startPoint, endPosition);
    }

    async getTool() {
        return this.page.getByRole('button', { name: 'Circle' });
    }

    async selectTool() {
        await (await this.getTool()).click();
    }
}

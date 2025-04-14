// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

import { Polygon } from '../../../../src/core/annotations/shapes.interface';
import { withRelative } from '../../../utils/mouse';

export class ObjectColoringToolPage {
    BRUSH_SIZE_SLIDER_Y = 125;

    constructor(private page: Page) {}

    async drawPolyline(polyline: Omit<Polygon, 'shapeType'>) {
        const relative = await withRelative(this.page);

        const startPoint = relative(polyline.points[0].x, polyline.points[0].y);
        await this.page.mouse.move(startPoint.x, startPoint.y);
        await this.page.mouse.down();

        for (const point of polyline.points) {
            const relativePoint = relative(point.x, point.y);
            await this.page.mouse.move(relativePoint.x, relativePoint.y);
        }

        await this.page.mouse.up();
    }

    async getTool() {
        return this.page.getByRole('button', { name: 'Object coloring' });
    }

    async selectTool() {
        await (await this.getTool()).click();
    }

    async acceptAnnotation() {
        await this.page.getByRole('button', { name: 'accept watershed annotation' }).click();
    }

    async rejectAnnotation() {
        await this.page.getByRole('button', { name: 'reject watershed annotation' }).click();
        await this.page.getByRole('button', { name: 'Object coloring' }).click();
    }

    async openBrushSlider() {
        await this.page.getByRole('button', { name: 'Brush size button' }).click();
    }

    async getBrushSliderValue() {
        return this.page.getByLabel('Brush size slider').locator('input[type=range]').inputValue();
    }

    async changeBrushSize(from: number, to: number) {
        await this.openBrushSlider();

        await this.page.mouse.move(from, this.BRUSH_SIZE_SLIDER_Y);
        await this.page.mouse.down();
        await this.page.mouse.move(to, this.BRUSH_SIZE_SLIDER_Y);
        await this.page.mouse.up();

        // eslint-disable-next-line playwright/no-force-option
        await this.page.getByText('Object coloring').click({ force: true });
    }
}

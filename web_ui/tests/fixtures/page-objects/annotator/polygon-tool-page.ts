// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

import { Polygon } from '../../../../src/core/annotations/shapes.interface';
import { withRelative } from '../../../utils/mouse';

export class PolygonToolPage {
    constructor(private page: Page) {}

    async drawPolygon(
        polygon: Omit<Polygon, 'shapeType'>,
        config: { asLasso: boolean; finishShape: boolean } = { asLasso: false, finishShape: true }
    ) {
        const relative = await withRelative(this.page);

        const startPoint = relative(polygon.points[0].x, polygon.points[0].y);

        await this.page.mouse.move(startPoint.x, startPoint.y);
        await this.page.mouse.down();

        if (!config.asLasso) {
            await this.page.mouse.up();
        }

        for (const point of polygon.points) {
            const relativePoint = relative(point.x, point.y);

            await this.page.mouse.move(relativePoint.x, relativePoint.y);
            if (!config.asLasso) {
                await this.page.mouse.down();
                await this.page.mouse.up();
            }
        }

        if (config.finishShape) {
            // Finish the polygon by moving to its start position
            await this.page.mouse.move(startPoint.x, startPoint.y);
            await this.page.mouse.down();
            await this.page.mouse.up();
        }
    }

    async getSnappingMode() {
        return this.page.getByRole('switch', {
            name: 'Snapping mode',
        });
    }

    async toggleSnappingMode(params?: { hotkey: boolean }) {
        if (!params?.hotkey) {
            await (await this.getSnappingMode()).click();
        } else {
            await this.page.keyboard.down('Shift');
            await this.page.keyboard.press('S');
            await this.page.keyboard.up('Shift');
        }
    }

    async getTool() {
        return this.page.getByRole('button', { name: 'Polygon' });
    }

    async selectTool() {
        await (await this.getTool()).click();
    }

    async openPointContextMenu(point: { x: number; y: number }) {
        await this.page.mouse.click(point.x, point.y, { button: 'right' });
    }

    async deletePointByRightClick(point: { x: number; y: number }) {
        await this.openPointContextMenu(point);
        await this.page.getByText('Delete').click();
    }
}

// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

import { degreesToRadians } from '../../../../src/core/annotations/math';
import { withRelative } from '../../../utils/mouse';

interface Point {
    x: number;
    y: number;
}

export class RotatedBoundingBoxToolPage {
    constructor(private page: Page) {}

    async getEndPoint(startPoint: Point, width: number, angle: number) {
        const deltaY = Math.tan(degreesToRadians(angle)) * width;
        return { x: startPoint.x + width, y: startPoint.y + deltaY };
    }

    async getTool() {
        return this.page.getByRole('button', { name: 'Rotated Bounding Box', exact: true });
    }

    async drawRotatedBoundingBox(startingPoint: Point, endPoint: Point) {
        const relative = await withRelative(this.page);
        const startPointRelative = relative(startingPoint.x, startingPoint.y);
        const endPointRelative = relative(endPoint.x, endPoint.y);

        await this.page.mouse.move(startPointRelative.x, startPointRelative.y);
        await this.page.mouse.down();

        await this.page.mouse.move(endPointRelative.x, endPointRelative.y);
        await this.page.mouse.up();
    }

    async moveResizeAnchor(deltaPoint: Point, anchorLabel: string) {
        const anchor = this.page.getByLabel(anchorLabel, { exact: true });
        const anchorX = Number(await anchor.getAttribute('x'));
        const anchorY = Number(await anchor.getAttribute('y'));
        const anchorCoordinatesShift = 3;

        const relative = await withRelative(this.page);
        const endPointRelative = relative(anchorX + deltaPoint.x, anchorY + deltaPoint.y);
        const startPointRelative = relative(anchorX + anchorCoordinatesShift, anchorY + anchorCoordinatesShift);

        await this.page.mouse.move(startPointRelative.x, startPointRelative.y);
        await this.page.mouse.down();

        await this.page.mouse.move(endPointRelative.x, endPointRelative.y);
        await this.page.mouse.up();
    }

    async checkRotationIndicatorAtDefaultPosition(startingPoint: Point) {
        const rotationIndicatorX = Number(await this.page.getByLabel('Rotate anchor').getAttribute('x'));

        expect(rotationIndicatorX < startingPoint.x).toBeTruthy();
    }

    async checkIfRotationIndicatorIsVisible() {
        await expect(this.page.getByLabel('Rotate anchor')).toBeVisible();
    }
}

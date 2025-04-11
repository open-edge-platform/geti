// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { expect, Locator, Page } from '@playwright/test';

import { Point } from '../../../src/core/annotations/shapes.interface';

export class TemplateManagerPage {
    constructor(private page: Page) {}

    async addPoint(point: Point) {
        await this.page.getByLabel('drawing box').click({ position: point });
    }

    async addMultipleConnectedPoints(points: Point[]) {
        for (let i = 0; i < points.length; i++) {
            await this.page.getByLabel('drawing box').click({ position: points[i] });

            if (i !== points.length - 1) {
                await this.page.getByLabel(`link keypoint ${i + 1}`).click();
            }
        }
    }

    async getPosition(selector: Locator) {
        const box = await selector.boundingBox();
        if (!box) {
            throw Error('Element not found or not visible.');
        }

        return { x: box.x + box.width / 2, y: box.y + box.height / 2 };
    }

    async movePointTo(page: Page, selector: Locator, newPosition: Point) {
        const elementPosition = await this.getPosition(selector);

        await page.mouse.move(elementPosition.x, elementPosition.y);
        await page.mouse.down();

        await page.mouse.move(newPosition.x, newPosition.y, { steps: 10 });
        await page.mouse.up();
    }

    async connectPoints(page: Page, pointOneName: string, pointTwoName: string) {
        const deleteSelector = new RegExp(`^delete keypoint ${pointOneName}$`);

        await page.getByLabel(`keypoint ${pointOneName} anchor`).click();
        await page.getByLabel(`link keypoint ${pointOneName}`).click();
        await expect(page.getByLabel(deleteSelector)).toBeDisabled();

        await page.getByLabel(`keypoint ${pointTwoName} anchor`).click();

        await expect(page.getByLabel(`hidden padded edge ${pointOneName} - ${pointTwoName}`)).toBeInViewport();
    }

    async openEdgeMenu(selector: string) {
        // eslint-disable-next-line playwright/no-force-option
        await this.page.getByLabel(selector).click({ force: true, button: 'right' });
    }

    async changeLabelColor(point: Locator, color: string) {
        await this.page.getByRole('button', { name: /color selector$/ }).click();
        await this.page.getByRole('textbox', { name: 'Hex' }).fill(color);
        await this.page.getByRole('textbox', { name: 'Hex' }).press('Tab');

        await point.click();
    }

    async deletePoint(name: string) {
        const selector = new RegExp(`^delete keypoint ${name}$`);

        await this.page.getByLabel(`keypoint ${name} anchor`).click();
        await this.page.getByLabel(selector).click();
    }

    async getLinePositions(selector: Locator) {
        const x1 = Number(await selector.getAttribute('x1'));
        const y1 = Number(await selector.getAttribute('y1'));
        const x2 = Number(await selector.getAttribute('x2'));
        const y2 = Number(await selector.getAttribute('y2'));

        return { x1, x2, y1, y2 };
    }

    async getPointPosition(selector: Locator) {
        const cx = Number(await selector.getAttribute('cx'));
        const cy = Number(await selector.getAttribute('cy'));

        return { cx, cy };
    }

    async isLineInContactWithPoint(line: Locator, point: Locator) {
        const linePositions = await this.getLinePositions(line);
        const pointPositions = await this.getPointPosition(point);

        return (
            (linePositions.x1 === pointPositions.cx && linePositions.y1 === pointPositions.cy) ||
            (linePositions.x2 === pointPositions.cx && linePositions.y2 === pointPositions.cy)
        );
    }
}

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

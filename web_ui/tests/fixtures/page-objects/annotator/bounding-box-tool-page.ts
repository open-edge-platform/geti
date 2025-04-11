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

import { Rect } from '../../../../src/core/annotations/shapes.interface';
import { clickAndMove, withRelative } from '../../../utils/mouse';

export class BoundingBoxToolPage {
    constructor(private page: Page) {}

    async drawBoundingBox({ x, y, width, height }: Omit<Rect, 'shapeType'>) {
        const relative = await withRelative(this.page);
        const startPoint = relative(x, y);
        const endPoint = relative(x + width, y + height);

        await clickAndMove(this.page, startPoint, endPoint);
    }

    async getTool() {
        return this.page.getByRole('button', { name: 'Bounding Box', exact: true });
    }

    async selectTool() {
        await (await this.getTool()).click();
    }
}

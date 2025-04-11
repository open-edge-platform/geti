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

import { ShapeDTO } from '../../../../src/core/annotations/dtos/annotation.interface';
import { Point } from '../../../../src/core/annotations/shapes.interface';
import { selectShape } from '../../../features/annotator/utils';
import { clickAndMove, withRelative } from '../../../utils/mouse';

export class SelectionToolPage {
    constructor(private page: Page) {}

    async getTool() {
        return this.page.getByRole('button', { name: 'Selection', exact: true });
    }

    async selectTool() {
        await (await this.getTool()).click();
    }

    async selectUsingClick(shape: ShapeDTO) {
        await selectShape(this.page, shape);
    }

    async selectUsingClickAndShiftKey(shape: ShapeDTO) {
        await this.page.keyboard.down('Shift');
        await this.selectUsingClick(shape);
        await this.page.keyboard.up('Shift');
    }

    async selectUsingBox(startPoint: Point, endPoint: Point) {
        const relative = await withRelative(this.page);
        const relativeStartPoint = relative(startPoint.x, startPoint.y);
        const relativeEndPoint = relative(endPoint.x, endPoint.y);

        await clickAndMove(this.page, relativeStartPoint, relativeEndPoint);
    }

    async selectUsingBoxAndShiftKey(startPoint: Point, endPoint: Point) {
        await this.page.keyboard.down('Shift');
        await this.selectUsingBox(startPoint, endPoint);
        await this.page.keyboard.up('Shift');
    }
}

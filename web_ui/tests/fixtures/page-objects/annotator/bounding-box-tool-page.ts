// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

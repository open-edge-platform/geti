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

import { Circle, Rect } from '../../../../src/core/annotations/shapes.interface';
import { BoundingBoxToolPage } from './bounding-box-tool-page';
import { CircleToolPage } from './circle-tool-page';

export class DetectionAssistantToolPage {
    constructor(
        private page: Page,
        private boundingBoxTool: BoundingBoxToolPage,
        private circleTool: CircleToolPage
    ) {}

    numberOfMatchesFieldLocator() {
        return this.page.getByLabel('Detection tool threshold slider field');
    }

    async changeNumberOfAnnotations(newNumber: number) {
        const numberOfItemSliderCounter = this.numberOfMatchesFieldLocator();

        await numberOfItemSliderCounter.clear();
        await numberOfItemSliderCounter.type(newNumber.toString());
    }

    async drawBoundingBox(shape: Omit<Rect, 'shapeType'>) {
        await this.boundingBoxTool.drawBoundingBox(shape);
    }

    async drawCircle(shape: Omit<Circle, 'shapeType'>) {
        await this.circleTool.drawCircle(shape);
    }

    async getTool() {
        return this.page.getByRole('button', { name: 'Detection assistant' });
    }

    async getCircleMode() {
        return this.page.getByRole('button', { name: 'Circle mode' });
    }

    async getAutoMergeDuplicatesToggle() {
        return this.page.getByRole('switch', {
            name: 'Auto merge duplicates',
        });
    }

    async toggleAutoMergeDuplicates() {
        await (await this.getAutoMergeDuplicatesToggle()).click();
    }

    async selectTool() {
        await (await this.getTool()).click();
    }

    async selectBoxMode() {
        await this.page.getByRole('button', { name: 'Bounding box mode' }).click();
    }

    async selectCircleMode() {
        await (await this.getCircleMode()).click();
    }

    async getAcceptAnnotationButton() {
        return this.page.getByRole('button', { name: 'accept ssim annotation' });
    }

    async acceptAnnotation() {
        await (await this.getAcceptAnnotationButton()).click();
    }

    async rejectAnnotation() {
        await this.page.getByRole('button', { name: 'reject ssim annotation' }).click();
    }
}

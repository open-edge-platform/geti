// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { expect, Locator, Page } from '@playwright/test';

import { Circle, Polygon, Rect } from '../../../src/core/annotations/shapes.interface';
import { expectToBeEqualToPixelAccuracy } from '../../utils/assertions';

export const expectRectShape = async (shapeLocator: Locator, { x, y, width, height }: Omit<Rect, 'shapeType'>) => {
    await expectToBeEqualToPixelAccuracy(Number(await shapeLocator.getAttribute('x')), x);
    await expectToBeEqualToPixelAccuracy(Number(await shapeLocator.getAttribute('y')), y);
    await expectToBeEqualToPixelAccuracy(Number(await shapeLocator.getAttribute('width')), width);
    await expectToBeEqualToPixelAccuracy(Number(await shapeLocator.getAttribute('height')), height);
};

export const expectCircleShape = async (shapeLocator: Locator, { x, y, r }: Omit<Circle, 'shapeType'>) => {
    await expectToBeEqualToPixelAccuracy(Number(await shapeLocator.getAttribute('cx')), x);
    await expectToBeEqualToPixelAccuracy(Number(await shapeLocator.getAttribute('cy')), y);
    await expectToBeEqualToPixelAccuracy(Number(await shapeLocator.getAttribute('r')), r);
};

const getPointsFromPolygon = async (shapeLocator: Locator) => {
    const points = (await shapeLocator.getAttribute('points')) ?? '';

    return points.split(' ').map((point) => {
        return { x: Number(point.split(',')[0]), y: Number(point.split(',')[1]) };
    });
};

export const expectPolygonShape = async (shapeLocator: Locator, polygon: Omit<Polygon, 'shapeType'>) => {
    const points = await getPointsFromPolygon(shapeLocator);

    expect(points).toHaveLength(polygon.points.length);
    points.forEach(({ x, y }, idx) => {
        expectToBeEqualToPixelAccuracy(x, polygon.points[idx].x);
        expectToBeEqualToPixelAccuracy(y, polygon.points[idx].y);
    });
};

export const clearDefaultLabel = async (page: Page) => {
    const clearDefaultLabelLocator = page.getByLabel('Close hierarchical label view');

    if (await clearDefaultLabelLocator.isVisible()) {
        await clearDefaultLabelLocator.click();
    }
};

export const expectLabelIsAssignedToDrawnShape = async (page: Page, labelName: string) => {
    const editCanvas = page.getByLabel('edit-annotations');

    await editCanvas.getByText('Select label').click();
    const resultsContainer = page.getByLabel('Label search results');
    await resultsContainer.getByText(labelName).click();

    await expect(editCanvas.getByLabel('labels')).toHaveText(labelName);
};

export const expectPreselectedLabelIsAssignedToDrawnShape = async (
    page: Page,
    labelName: string,
    drawShape: () => Promise<void>
) => {
    await clearDefaultLabel(page);

    const annotatorHeader = page.locator('#annotator-header');
    await annotatorHeader.getByLabel('Select default label').click();

    const resultsContainer = page.getByLabel('Label search results');
    await resultsContainer.getByText(labelName).click();

    await drawShape();

    await expect(page.getByLabel('edit-annotations').getByLabel('labels')).toHaveText(labelName);
};

export const expectAnnotationVisible = async (page: Page, name: string | RegExp) => {
    const labels = page.getByLabel('annotations', { exact: true }).getByRole('list', { name: 'labels' });
    await expect(labels).toHaveCount(1);
    await expect(labels).toContainText(name);
};

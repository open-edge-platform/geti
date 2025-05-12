// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
    const actualPoints = await getPointsFromPolygon(shapeLocator);
    const expectedPoints = polygon.points;
    const tolerance = 2;

    expect(actualPoints).toHaveLength(expectedPoints.length);

    const arePointsClose = (a: { x: number; y: number }, b: { x: number; y: number }) =>
        Math.abs(a.x - b.x) <= tolerance && Math.abs(a.y - b.y) <= tolerance;

    expectedPoints.forEach((exp) => {
        const match = actualPoints.some((act) => arePointsClose(exp, act));

        expect(match).toBeTruthy();
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

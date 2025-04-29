// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Locator, Page } from '@playwright/test';

export const expectShapeColor = async (shapeLocator: Locator, color: string) => {
    const polygonStrokeColor = await shapeLocator.getAttribute('stroke');
    const polygonFillColor = await shapeLocator.getAttribute('fill');

    expect([polygonStrokeColor, polygonFillColor]).toEqual([color, color]);
};

export const expectToBeEqualToPixelAccuracy = (a: number, b: number) => {
    // While most times expect(a).toBeCloseTo(b) works in Chrome,
    // Firefox has some issues where its events seem to be less accurate,
    // so instead we allow the values to be 1 pixel off
    expect(a).toBeCloseTo(b, -1);
};

export const waitForLoadingToBeFinished = async (page: Page) => {
    await expect(page.getByText('Loading...').first()).toBeHidden({ timeout: 10000 });
};

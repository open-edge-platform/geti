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

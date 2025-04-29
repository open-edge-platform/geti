// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Locator, Page } from '@playwright/test';

import { getZoomLevel } from './zoom';

type Relative = (x: number, y: number) => { x: number; y: number };

export const withRelative = async (page: Page): Promise<Relative> => {
    const zoom = await getZoomLevel(page);
    const rect = (await page.locator('id=annotations-canvas-tools').boundingBox()) ?? { x: 0, y: 0 };

    const relative = (x: number, y: number): ReturnType<Relative> => {
        return { x: x * zoom + rect.x, y: y * zoom + rect.y };
    };

    return relative;
};

export const clickAndMove = async (
    page: Page,
    startPoint: { x: number; y: number },
    endPoint: { x: number; y: number },
    options?: Parameters<Page['mouse']['down']>[0]
) => {
    await page.mouse.move(startPoint.x, startPoint.y);
    await page.mouse.down(options);
    await page.mouse.move(endPoint.x, endPoint.y);
    await page.mouse.up(options);
};

export const changeSlider = async (
    page: Page,
    thumbLocator: Locator,
    sliderLocator: Locator,
    targetPercentage: number
) => {
    const thumbBoundingBox = await thumbLocator.boundingBox();
    const sliderBoundingBox = await sliderLocator.boundingBox();

    if (thumbBoundingBox === null || sliderBoundingBox === null) {
        return;
    }

    await clickAndMove(
        page,
        {
            x: thumbBoundingBox.x + thumbBoundingBox.width / 2,
            y: thumbBoundingBox.y + thumbBoundingBox.height / 2,
        },
        {
            x: sliderBoundingBox.x + sliderBoundingBox.width * targetPercentage,
            y: thumbBoundingBox.y + thumbBoundingBox.height / 2,
        }
    );
};

export const zoomInImage = async (page: Page, point: { x: number; y: number }, zoomShift: number) => {
    const relative = await withRelative(page);
    const relativePoint = relative(point.x, point.y);

    await page.mouse.move(relativePoint.x, relativePoint.y);
    await page.mouse.wheel(0, zoomShift);
};

export const clickOutsidePopover = async (page: Page) => {
    const popoverBox = await page.getByTestId('popover').boundingBox();

    if (popoverBox) {
        // click outside the popover
        await page.mouse.click(popoverBox.x - 100, popoverBox.y);
    }
};

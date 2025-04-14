// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { expect, Page } from '@playwright/test';

export const getImagesNumber = async (page: Page) => {
    const images = page.locator('img');

    await expect(images.first()).toBeVisible({ timeout: 10000 });
    return await images.count();
};

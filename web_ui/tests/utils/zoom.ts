// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Page } from '@playwright/test';

export const getZoomLevel = async (page: Page): Promise<number> => {
    return Number(await page.getByLabel('Zoom level').getAttribute('data-value'));
};

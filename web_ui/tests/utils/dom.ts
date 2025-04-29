// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Locator, Page } from '@playwright/test';

import { ImportFile } from '../fixtures/open-api';

export const getBackgroundColor = (locator: Locator) =>
    locator.evaluate((element) => {
        return window.getComputedStyle(element).getPropertyValue('background-color');
    });

export const getFillColor = (locator: Locator) =>
    locator.evaluate((element) => window.getComputedStyle(element).getPropertyValue('fill'));

export const loadFile = async (page: Page, action: Promise<void>, file: ImportFile): Promise<ImportFile> => {
    const [uploadFiles] = await Promise.all([page.waitForEvent('filechooser'), action]);
    const buffer = file.buffer ?? Buffer.alloc(file.size);

    await uploadFiles.setFiles([{ name: file.name, mimeType: '', buffer }]);

    return { ...file, buffer };
};

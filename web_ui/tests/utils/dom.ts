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

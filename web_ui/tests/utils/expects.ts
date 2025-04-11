// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { expect, Page } from '@playwright/test';

export const expectCSVToBeEqual = (expected: string[][], actual: string[][]) => {
    if (expected.length !== actual.length) {
        throw new Error('Lengths of expected and actual CSVs are different');
    }

    for (let i = 0; i < expected.length; i++) {
        if (expected[i].length !== actual[i].length) {
            throw new Error(`Lengths of expected and actual rows are different on row ${i}`);
        }

        for (let j = 0; j < expected[i].length; j++) {
            expect(expected[i][j]).toBe(actual[i][j]);
        }
    }
};

export const expectToBeDownloaded = async (page: Page, download: () => Promise<void>) => {
    const downloadPromise = page.waitForEvent('download');
    await download();

    const downloadResolved = await downloadPromise;
    expect(await downloadResolved.failure()).toBeNull();

    return downloadResolved;
};

// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

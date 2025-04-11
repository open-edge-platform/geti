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

export class ImportProjectDatasetPage {
    constructor(private page: Page) {}

    async uploadDataset(datasetPath: string) {
        const [, fileChooser] = await Promise.all([
            this.page.getByRole('button', { name: /upload/i }).click(),
            this.page.waitForEvent('filechooser'),
        ]);
        await fileChooser.setFiles([datasetPath]);

        await expect(this.page.getByRole('dialog').getByText('Dataset is parsed successfully')).toBeVisible();
    }
}

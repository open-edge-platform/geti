// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

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

import { Page } from '@playwright/test';

export class QuickInferencePage {
    constructor(private page: Page) {}

    async uploadImage(file: string) {
        const [fileChooser] = await Promise.all([
            // It is important to call waitForEvent before click to set up waiting.
            this.page.waitForEvent('filechooser'),
            this.page
                .getByRole('button', { name: /upload/i })
                .nth(0)
                .click(),
            this.page.getByTestId('menu-wrapper').getByLabel('File').click(),
        ]);

        await fileChooser.setFiles([file]);
    }

    async getAlertMessage(): Promise<string> {
        return (await this.page.getByRole('alert').textContent()) ?? '';
    }

    async openFullscreen() {
        await this.page.getByRole('button', { name: /open in fullscreen/i }).click();
    }

    async closeFullscreen() {
        await this.page.getByRole('button', { name: /close fullscreen/i }).click();
    }

    async toggleExplanation() {
        await this.page.getByRole('switch').click();
    }
}

// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
